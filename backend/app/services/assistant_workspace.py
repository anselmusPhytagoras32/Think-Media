"""FR02/03/04/10: bounded model planning and locally authorized actions."""

from datetime import timedelta
from hashlib import sha256
import json
from typing import Literal
from uuid import UUID

from pydantic import Field
from sqlalchemy import func, select

from app.errors import ApiError
from app.models import AssistantAction, CompanyProfile
from app.schemas import ProfileUpdateRequest
from app.schemas.models import ApiModel
from app.schemas.learning_submission import LessonDraft, SkillDraft
from app.schemas.marketplace import ListingInput
from app.services.assistant import AssistantService
from app.services.guidance_retrieval import retrieve_sources
from app.services.learning import LearningService
from app.services.learning_submissions import SubmissionService
from app.services.marketplace import MarketplaceService
from app.services.profiles import ProfileService
from app.services.recommendations import RecommendationService
from app.time_utils import utcnow, iso_manila

PAGES = {
    "student": ["overview", "profile", "learning", "opportunities", "applications", "suggestions", "assistant"],
    "instructor": ["overview", "profile", "learning", "opportunities", "authoring", "assistant"],
    "company": ["overview", "profile", "opportunities", "review", "assistant"],
    "administrator": ["overview", "profile", "verification", "content", "learning-review", "reports", "audit", "assistant"],
}
PROFILE_FIELDS = {
    "student": {"skills", "interests", "program", "institution", "location"},
    "instructor": {"institution"},
    "company": {"description", "location", "website"},
}
PAGE_PURPOSES = {
    "overview": "home dashboard", "profile": "my profile", "learning": "published learning library",
    "opportunities": "opportunities or my company listings", "applications": "my student applications",
    "suggestions": "my personalized suggestions", "authoring": "my instructor teaching materials",
    "review": "company applicant review", "verification": "administrator company verification",
    "content": "administrator learning content", "learning-review": "administrator instructor submission review",
    "reports": "administrator content reports", "audit": "administrator audit history", "assistant": "assistant conversation",
}
WRITE_TOOLS = {"save_resource", "update_profile", "draft_lesson", "draft_skill", "draft_listing"}


class LessonSearch(ApiModel):
    q: str = Field(default="", max_length=200)
    tag: str = Field(default="", max_length=80)


class OpportunitySearch(ApiModel):
    q: str = Field(default="", max_length=200)
    location: str = Field(default="", max_length=200)
    skill: str = Field(default="", max_length=80)
    type: Literal["ojt", "job"] = "ojt"


class SaveResource(ApiModel):
    content_id: UUID
    saved: bool


class GroundedAnswer(ApiModel):
    answer: str = Field(min_length=1, max_length=8000)
    source_ids: list[str] = Field(max_length=3)
    uncertainty: bool


class NoArguments(ApiModel):
    pass


def function(name, description, schema):
    # Keep nested field contracts directly visible to tool-calling models.
    # These are server-owned, non-recursive Pydantic schemas, never user input.
    definitions = schema.get("$defs", {})
    def inline(value):
        if isinstance(value, list):
            return [inline(item) for item in value]
        if isinstance(value, dict):
            if "$ref" in value:
                reference = value["$ref"]
                if not reference.startswith("#/$defs/"):
                    raise ValueError("Unsupported tool schema reference")
                return inline({**definitions[reference.removeprefix("#/$defs/")], **{key: item for key, item in value.items() if key != "$ref"}})
            return {key: inline(item) for key, item in value.items() if key != "$defs"}
        return value
    return {"type": "function", "function": {"name": name, "description": description, "parameters": inline(schema)}}


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


class WorkspaceAssistant:
    def __init__(self, db, user, session, provider, throttle, settings):
        self.db, self.user, self.session = db, user, session
        self.provider, self.throttle, self.settings = provider, throttle, settings

    def tools(self):
        definitions = [
            function("answer_guidance", "Answer from approved excerpts with supporting source_ids; admit uncertainty when unsupported.", GroundedAnswer.model_json_schema()),
            function("navigate", "Open the destination requested in the question. Use existing screens for applications, verification, publication, and decisions.", {"type": "object", "additionalProperties": False, "properties": {"page": {"type": "string", "enum": PAGES[self.user.role], "description": "Requested destination, not the current location. " + "; ".join(f"{page}: {PAGE_PURPOSES[page]}" for page in PAGES[self.user.role])}}, "required": ["page"]}),
            function("find_lessons", "Find published learning resources by keyword or exact tag.", LessonSearch.model_json_schema()),
            function("find_opportunities", "Search published opportunities from verified companies.", OpportunitySearch.model_json_schema()),
        ]
        if self.user.role == "student":
            definitions += [
                function("show_suggestions", "Show locally personalized suggestions. Private profile fields are not sent to the model.", NoArguments.model_json_schema()),
                function("save_resource", "Propose saving or unsaving an existing published resource; needs explicit confirmation and an actual source UUID.", SaveResource.model_json_schema()),
            ]
        if self.user.role in PROFILE_FIELDS:
            schema = ProfileUpdateRequest.model_json_schema()
            fields = PROFILE_FIELDS[self.user.role]
            schema["properties"] = {k: v for k, v in schema["properties"].items() if k in fields}
            schema["minProperties"] = 1
            definitions.append(function("update_profile", "Propose changes explicitly requested by the user to their own profile. Never infer qualifications or skills from quiz completion.", schema))
        if self.user.role == "instructor":
            lesson = LessonDraft.model_json_schema()
            lesson["properties"].pop("kind")
            lesson["required"].remove("kind")
            lesson["$defs"]["QuestionInput"]["properties"]["correct_index"]["description"] = (
                "Required zero-based integer index into options: 0 is the first option, 1 the second. "
                "Use correct_index, never an answer letter or an answer property."
            )
            definitions += [
                function("draft_lesson", "Draft a lesson with optional quiz questions for the instructor to review. Creates only an unpublished draft after confirmation.", lesson),
                function("draft_skill", "Propose an unpublished skill category for the instructor to review.", {"type": "object", "additionalProperties": False, "properties": {"title": {"type": "string", "maxLength": 80}, "summary": {"type": "string", "maxLength": 500}}, "required": ["title", "summary"]}),
            ]
        if self.user.role == "company":
            company = self.db.scalar(select(CompanyProfile).where(CompanyProfile.user_id == self.user.id))
            if company and company.verification_status == "verified":
                definitions.append(function("draft_listing", "Draft a fictional or user-specified listing for the owning company; it stays unpublished until reviewed in the company portal.", ListingInput.model_json_schema()))
        return definitions

    def validate(self, name, arguments):
        if name not in {tool["function"]["name"] for tool in self.tools()} or not isinstance(arguments, dict):
            raise ValueError("Unsupported action")
        if name == "navigate":
            if set(arguments) != {"page"} or arguments["page"] not in PAGES[self.user.role]:
                raise ValueError("Unsupported page")
            return arguments
        if name == "update_profile":
            if not arguments or set(arguments) - PROFILE_FIELDS.get(self.user.role, set()) or any(v is None for v in arguments.values()):
                raise ValueError("Unsupported profile fields")
            return ProfileUpdateRequest.model_validate(arguments).model_dump(mode="json", exclude_unset=True)
        if name in {"draft_lesson", "draft_skill"}:
            if "kind" in arguments:
                raise ValueError("Unexpected kind")
            model = LessonDraft if name == "draft_lesson" else SkillDraft
            return model.model_validate({"kind": "lesson" if name == "draft_lesson" else "skill", **arguments}).model_dump(mode="json")
        model = {"answer_guidance": GroundedAnswer, "find_lessons": LessonSearch, "find_opportunities": OpportunitySearch, "save_resource": SaveResource, "show_suggestions": NoArguments, "draft_listing": ListingInput}[name]
        return model.model_validate(arguments).model_dump(mode="json")

    def answer(self, question, page, history, resource_id=None):
        if not self.settings.assistant_tools_enabled or not hasattr(self.provider, "plan"):
            return AssistantService(self.db, self.provider, self.throttle).answer(question, self.user.id, history)
        retry = self.throttle.retry_after(str(self.user.id))
        if retry is not None:
            raise ApiError(429, "RATE_LIMITED", "Too many assistant requests. Try again later.", headers={"Retry-After": str(retry)})
        self.throttle.record_attempt(str(self.user.id))
        if not question.strip():
            raise ApiError(422, "VALIDATION_ERROR", "Enter a question.")
        sources = retrieve_sources(self.db, question, history)
        if page == "learning" and resource_id is not None:
            resource = LearningService(self.db, self.user).content(resource_id, public_only=True)
            current = dict(id=str(resource.id), title=resource.title, excerpt=resource.body[:1600])
            sources = [current, *[source for source in sources if source["id"] != current["id"]]][:3]
        try:
            plan = self.provider.plan(question, sources, self.tools(), page=page if page in PAGES[self.user.role] else "overview", previous_questions=history)
            if set(plan) != {"name", "arguments"}:
                raise ValueError("Invalid plan")
            name = plan["name"]
            args = self.validate(name, plan["arguments"])
        except Exception:
            raise ApiError(503, "ASSISTANT_UNAVAILABLE", "The assistant could not prepare a supported action. Try again or use the page controls.") from None
        output = dict(answer="", sources=[], uncertainty=False, mode="external", results=[])
        if name == "answer_guidance":
            approved = {source["id"]: source["title"] for source in sources}
            if any(id not in approved for id in args["source_ids"]) or len(set(args["source_ids"])) != len(args["source_ids"]):
                raise ApiError(503, "ASSISTANT_UNAVAILABLE", "The answer could not be verified against approved resources.")
            return {**output, "answer": args["answer"], "sources": [{"id": id, "title": approved[id]} for id in args["source_ids"]], "uncertainty": args["uncertainty"] or not args["source_ids"]}
        if name == "navigate":
            return {**output, "answer": "Open the requested workspace using the link below.", "navigation": {"label": "Open " + args["page"].replace("-", " "), "href": "#/" + args["page"]}}
        if name == "find_lessons":
            rows = LearningService(self.db, self.user).feed(5, 0, **args)["items"]
            results = [dict(id=row["id"], title=row["title"], summary=row["summary"], href="#/learning/" + row["id"], kind="lesson") for row in rows]
        elif name == "find_opportunities":
            rows = MarketplaceService(self.db, self.user).list_listings(5, 0, **args)["items"]
            results = [dict(id=row["id"], title=row["title"], summary=row["company_name"] + " · " + row["location"], href="#/opportunities/" + row["id"], kind="opportunity") for row in rows]
        elif name == "show_suggestions":
            suggested = RecommendationService(self.db, self.user, self.settings.recommender_alpha).recommend(5)
            return {**output, "answer": "Your suggestions are based on your current profile and eligible content.", "navigation": {"label": "View my suggestions", "href": "#/suggestions"}}
        else:
            return {**output, "answer": "Review the proposed change. Nothing has been saved yet.", "proposal": self.propose(name, args)}
        return {**output, "answer": "Here are matching published results." if results else "No published results match yet. Try a broader search.", "results": results}

    def profile_fingerprint(self, arguments):
        from app.repositories import ProfileRepository
        profiles = ProfileRepository(self.db)
        row = {"student": profiles.get_student, "instructor": profiles.get_instructor, "company": profiles.get_company_by_user_id}[self.user.role](self.user.id)
        self.db.refresh(row, with_for_update=True)
        return fingerprint({key: getattr(row, key) for key in arguments})

    def propose(self, name, arguments):
        if self.db.scalar(select(func.count()).select_from(AssistantAction).where(AssistantAction.actor_id == self.user.id, AssistantAction.status == "pending", AssistantAction.expires_at > utcnow())) >= 20:
            raise ApiError(429, "RATE_LIMITED", "Review or cancel an existing change before preparing another.")
        label = {"save_resource": "Change saved resource", "update_profile": "Update my profile", "draft_lesson": "Create lesson draft", "draft_skill": "Create skill draft", "draft_listing": "Create listing draft"}[name]
        if name == "save_resource":
            resource = LearningService(self.db, self.user).content(UUID(arguments["content_id"]), public_only=True)
            changes = {"Resource": resource.title, "Saved": arguments["saved"]}
        else:
            changes = {key.replace("_", " ").capitalize(): value for key, value in arguments.items() if key != "kind"}
        if name == "draft_lesson":
            SubmissionService(self.db, self.user).selected_skills(arguments.get("skill_ids", []))
        row = AssistantAction(actor_id=self.user.id, session_id=self.session.id, name=name, arguments=arguments,
                              precondition=self.profile_fingerprint(arguments) if name == "update_profile" else None,
                              expires_at=utcnow() + timedelta(minutes=10))
        self.db.add(row)
        self.db.commit()
        return dict(id=str(row.id), label=label, changes=changes, expires_at=iso_manila(row.expires_at))

    def consume(self, id, *, cancel=False):
        if not self.settings.assistant_tools_enabled:
            raise ApiError(403, "FORBIDDEN", "Assistant actions are disabled.")
        row = self.db.scalar(select(AssistantAction).where(AssistantAction.id == id, AssistantAction.actor_id == self.user.id, AssistantAction.session_id == self.session.id).with_for_update())
        if row is None:
            raise ApiError(404, "NOT_FOUND", "Proposed change not found in this session.")
        if row.status != "pending" or row.expires_at <= utcnow():
            raise ApiError(409, "ACTION_UNAVAILABLE", "This change expired or was already handled. Prepare it again if needed.")
        if cancel:
            row.status = "cancelled"
            self.db.commit()
            return dict(answer="Proposed change cancelled.")
        try:
            arguments = row.arguments
            # Revalidate role, verification and input at execution time.
            validated = self.validate(row.name, {k: v for k, v in arguments.items() if not (k == "kind" and row.name in {"draft_lesson", "draft_skill"})})
            if row.name == "update_profile":
                if self.profile_fingerprint(validated) != row.precondition:
                    raise ApiError(409, "PROFILE_CHANGED", "Your profile changed after this preview. Prepare the change again.")
                ProfileService(self.db).update_me(self.user, ProfileUpdateRequest.model_validate(validated), commit=False)
                result = dict(answer="Your profile was updated.", href="#/profile")
            elif row.name == "save_resource":
                item = LearningService(self.db, self.user).state(UUID(validated["content_id"]), "saved", validated["saved"], commit=False)
                result = dict(answer="Your resource preference was saved.", href="#/learning/" + item["id"])
            elif row.name in {"draft_lesson", "draft_skill"}:
                draft = (LessonDraft if row.name == "draft_lesson" else SkillDraft).model_validate(validated)
                item = SubmissionService(self.db, self.user).save(draft, None, commit=False)
                result = dict(answer="Your draft was created. Review it before submitting for administrator approval.", href="#/authoring/" + item["id"])
            elif row.name == "draft_listing":
                item = MarketplaceService(self.db, self.user).create_listing(ListingInput.model_validate(validated), commit=False)
                result = dict(answer="Your listing draft was created. Review it before publication.", href="#/opportunities/" + item["id"])
            else:
                raise ValueError("Unsupported write")
            row.status, row.result = "executed", result
            self.db.commit()
            return result
        except ApiError:
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise ApiError(503, "ACTION_FAILED", "The change could not be saved. Nothing from this action was committed.") from None
