"""Prepare fictional instructor drafts and published OJT lessons in a local demo database."""

import argparse
import json
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy import select, text

from app.db import build_engine, build_session_factory
from app.models import LearningSubmission, User
from app.schemas.learning import QuestionInput
from app.schemas.learning_submission import LessonDraft, ResourceLink, ReviewDecision, SkillDraft
from app.services.learning_submissions import SubmissionService
from app.uploads import pdf_filename
from ops.presentation_accounts import MANIFEST_NAME, configuration, private_state_dir, provision

EXAMPLES = (
    (
        "resume",
        "Résumé preparation",
        "Turn a class project into an OJT résumé entry",
        "Practice writing a project bullet with a concrete contribution and result.",
        "Choose a project that relates to the listing. State your own contribution in one sentence. "
        "Start with a verb, name the task and include an outcome you can explain.\n\n"
        "Fictional example: “Built the search and filtering controls for a three-person inventory "
        "project and tested them with 20 sample records.” Add the course, dates, and technologies "
        "only if they help the reader understand the work.\n\n"
        "Practice: write a bullet for one school project and compare it with the fictional résumé. "
        "Remove personal information that the placement does not require.",
        ResourceLink(
            label="Harvard career center résumé guide",
            url="https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/",
        ),
        QuestionInput(
            question="Which bullet gives the clearest evidence of your own work?",
            options=["Helped with a project.", "Built search controls and tested them with 20 sample records."],
            correct_index=1,
            feedback="Name the work you did and give an outcome you can explain in an interview.",
        ),
    ),
    (
        "star",
        "STAR interviews",
        "Answer an OJT interview question using STAR",
        "Use Situation, Task, Action, and Result to give a concise answer.",
        "Start with the Situation, describe your Task, explain your Action, and close with the Result.\n\n"
        "Fictional example: A group presentation was due the next morning and the slides repeated "
        "several findings. The student was responsible for the summary. They grouped the findings by "
        "theme, assigned each teammate a slide, and ran one rehearsal. The group gave a clear "
        "presentation within the eight-minute limit.\n\n"
        "Practice: answer “Tell me about a time you solved a problem with a team.” Give enough "
        "context to make the problem clear, then spend most of the answer on your own actions.",
        ResourceLink(
            label="National Careers Service guide to the STAR method",
            url="https://nationalcareers.service.gov.uk/careers-advice/interview-advice/the-star-method",
        ),
        QuestionInput(
            question="Where should you explain how you reorganized the slides?",
            options=["Action", "Result", "Situation"],
            correct_index=0,
            feedback="Action describes what you did. Result describes what happened afterward.",
        ),
    ),
    (
        "communication",
        "Workplace communication",
        "Send an OJT progress update that asks for a decision",
        "Use a clear subject, a brief status update, and a specific request.",
        "Give the recipient enough context to act. Put the task in the subject, then state what "
        "is complete, what is blocked, and what response you need.\n\n"
        "Fictional example: “Subject: Feedback requested on inventory form by Thursday. "
        "The form captures the item name and quantity. I need to confirm whether supplier codes "
        "are required before I finish the validation. Could you confirm by Thursday at 2 p.m.?”\n\n"
        "Practice: rewrite a vague update into three sentences. Include a deadline if it matters, "
        "and verify that any attachments are appropriate to share.",
        ResourceLink(
            label="Purdue OWL professional email guidance",
            url="https://owl.purdue.edu/owl/general_writing/academic_writing/email_etiquette.html",
        ),
        QuestionInput(
            question="What makes the example easiest for the supervisor to act on?",
            options=["It says which decision is needed and when.", "It omits the task to keep the message short."],
            correct_index=0,
            feedback="A specific question and deadline tell the recipient how and when to respond.",
        ),
    ),
)


def seed_examples(db, instructor, administrator):
    """Insert the samples together. Stable IDs preserve edits on repeat runs."""
    db.execute(text("SELECT pg_advisory_xact_lock(2026111709)"))
    service = SubmissionService(db, administrator)
    counts = {"skills_created": 0, "lessons_published": 0, "drafts_created": 0}
    resume_path = Path(__file__).resolve().parents[2] / "presentation" / "fictional-resume.pdf"
    resume = resume_path.read_bytes()
    resume_name = pdf_filename(resume_path.name, "application/pdf", resume)

    def publish(row):
        db.add(row)
        db.flush()
        service.stage_review(
            row,
            ReviewDecision(
                expected_version=row.version,
                decision="approved",
                feedback="Approved for the fictional local demonstration.",
            ),
        )
        db.flush()

    for key, skill_name, title, summary, body, link, question in EXAMPLES:
        skill = db.scalar(
            select(LearningSubmission).where(LearningSubmission.approved_skill_key == skill_name.casefold())
        )
        if skill is None:
            skill = LearningSubmission(
                id=uuid5(instructor.id, f"learning-demo:skill:{key}"),
                author_id=instructor.id, kind="skill", status="pending",
                payload=SkillDraft(
                    kind="skill", title=skill_name, summary=f"Practice {skill_name.lower()} for OJT.",
                ).model_dump(mode="json"),
            )
            publish(skill)
            counts["skills_created"] += 1

        for variant in ("published", "draft"):
            id = uuid5(instructor.id, f"learning-demo:{variant}:{key}")
            if db.get(LearningSubmission, id) is not None:
                continue
            lesson = LessonDraft(
                kind="lesson", title=f"Practice: {title}" if variant == "published" else f"Demo draft: {title}",
                summary=summary, body="Fictional OJT practice material.\n\n" + body,
                tags=["OJT"], skill_ids=[skill.id], links=[link], questions=[question],
            )
            row = LearningSubmission(
                id=id, author_id=instructor.id, kind="lesson",
                status="pending" if variant == "published" else "draft",
                payload=lesson.model_dump(mode="json"),
                attachment_name=resume_name if key == "resume" else None,
                attachment=resume if key == "resume" else None,
            )
            if variant == "published":
                publish(row)
                counts["lessons_published"] += 1
            else:
                db.add(row)
                counts["drafts_created"] += 1
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path)
    args = parser.parse_args()
    try:
        settings, _ = configuration()
        state_dir = private_state_dir(args.state_dir)
        roles = provision(state_dir)
        manifest = json.loads((state_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
        engine = build_engine(settings)
        try:
            with build_session_factory(engine)() as db, db.begin():
                instructor = db.get(User, UUID(manifest["accounts"]["instructor"]["id"]))
                administrator = db.get(User, UUID(manifest["accounts"]["administrator"]["id"]))
                counts = seed_examples(db, instructor, administrator)
        finally:
            engine.dispose()
    except Exception as failure:
        # Connection errors and private configuration can contain credentials.
        parser.exit(1, f"Learning demo setup failed ({type(failure).__name__}). Check the local database and migration.\n")
    print(json.dumps({"synthetic_only": True, **counts, "credentials_file": roles["credentials_file"]}, indent=2))


if __name__ == "__main__":
    main()
