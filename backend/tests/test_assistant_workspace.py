"""FR02/03/10, NFR02/03/04: authenticated, confirmed workspace actions."""

from datetime import timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.time_utils import utcnow
from tests.helpers import get_csrf, login, post_json
from tests.test_learning import administrator, create_content, learner


class Planner:
    def __init__(self, name, arguments):
        self.name, self.arguments = name, arguments
        self.seen = []

    def plan(self, question, sources, tools, *, page, previous_questions=None):
        self.seen.append(dict(question=question, sources=sources, tools=tools, page=page))
        return {"name": self.name, "arguments": self.arguments}


def ask(actor, question="Find resume lessons", **updates):
    return post_json(actor, "/api/v1/assistant", {"question": question, "workspace": True, "page": "assistant", **updates})


def confirm(actor, proposal):
    return post_json(actor, f"/api/v1/assistant/actions/{proposal['id']}/confirm", {})


def test_search_returns_published_results_without_private_provider_context(app):
    admin = administrator(app)
    visible = create_content(admin)
    create_content(admin, status="draft", title="PRIVATE_UNPUBLISHED_MARKER")
    actor = learner(app)
    planner = Planner("find_lessons", {"q": "resume"})
    app.state.assistant_provider = planner
    response = ask(actor)
    assert response.status_code == 200, response.text
    result = response.json()
    assert [row["id"] for row in result["results"]] == [visible["id"]]
    assert result["results"][0]["href"] == "#/learning/" + visible["id"]
    assert "PRIVATE_UNPUBLISHED_MARKER" not in str(planner.seen)
    assert "learner@example.test" not in str(planner.seen)
    assert all(set(source) == {"id", "title", "excerpt"} for source in planner.seen[0]["sources"])


def test_saving_requires_confirmation_and_cannot_be_replayed(app):
    content = create_content(administrator(app))
    actor = learner(app)
    app.state.assistant_provider = Planner("save_resource", {"content_id": content["id"], "saved": True})
    response = ask(actor, "Save this resume lesson")
    assert response.status_code == 200, response.text
    proposal = response.json()["proposal"]
    assert actor.get(f"/api/v1/content/{content['id']}").json()["saved"] is False
    other = learner(app, email="other@example.test")
    assert confirm(other, proposal).status_code == 404
    assert confirm(actor, proposal).status_code == 200
    assert actor.get(f"/api/v1/content/{content['id']}").json()["saved"] is True
    assert confirm(actor, proposal).status_code == 409


def test_proposal_is_session_bound_cancellable_expiring_and_rechecks_publication(app, db):
    from app.models.assistant_action import AssistantAction
    admin = administrator(app)
    content = create_content(admin)
    actor = learner(app)
    app.state.assistant_provider = Planner("save_resource", {"content_id": content["id"], "saved": True})
    proposal = ask(actor).json()["proposal"]
    second = TestClient(app)
    assert login(second, email="learner@example.test").status_code == 200
    assert confirm(second, proposal).status_code == 404
    cancelled = post_json(actor, f"/api/v1/assistant/actions/{proposal['id']}/cancel", {})
    assert cancelled.status_code == 200
    assert confirm(actor, proposal).status_code == 409
    proposal = ask(actor).json()["proposal"]
    row = db.get(AssistantAction, UUID(proposal["id"]))
    row.expires_at = utcnow() - timedelta(seconds=1)
    db.commit()
    assert confirm(actor, proposal).status_code == 409
    proposal = ask(actor).json()["proposal"]
    from tests.helpers import patch_json
    assert patch_json(admin, f"/api/v1/admin/content/{content['id']}", {"status": "archived"}).status_code == 200
    assert confirm(actor, proposal).status_code == 404


def test_profile_preview_rejects_stale_state_and_role_escalation(app):
    actor = learner(app)
    app.state.assistant_provider = Planner("update_profile", {"skills": ["Python", "React"]})
    response = ask(actor, "Set my skills to Python and React")
    assert response.status_code == 200, response.text
    proposal = response.json()["proposal"]
    from tests.helpers import patch_json
    assert patch_json(actor, "/api/v1/profiles/me", {"skills": ["SQL"]}).status_code == 200
    assert confirm(actor, proposal).status_code == 409
    app.state.assistant_provider = Planner("update_profile", {"role": "administrator"})
    assert ask(actor).status_code == 503
    assert actor.get("/api/v1/auth/me").json()["user"]["role"] == "student"


def test_model_cannot_request_forbidden_tools_or_external_navigation(app):
    actor = learner(app)
    for name, arguments in [("verify_company", {}), ("draft_lesson", {"title": "Denied"}), ("navigate", {"page": "audit"}), ("navigate", {"page": "https://evil.example"})]:
        app.state.assistant_provider = Planner(name, arguments)
        assert ask(actor).status_code == 503


def test_instructor_creates_only_a_draft_after_confirmation(app):
    actor = learner(app, role="instructor")
    payload = {"title": "Explain a project", "summary": "Practice a project explanation.", "body": "Describe your own contribution.", "tags": ["OJT"], "questions": []}
    app.state.assistant_provider = Planner("draft_lesson", payload)
    response = ask(actor, "Draft a project explanation lesson")
    assert response.status_code == 200, response.text
    assert actor.get("/api/v1/instructor/learning").json()["total"] == 0
    result = confirm(actor, response.json()["proposal"])
    assert result.status_code == 200, result.text
    rows = actor.get("/api/v1/instructor/learning").json()["items"]
    assert len(rows) == 1 and rows[0]["status"] == "draft"
    assert actor.get("/api/v1/content").json()["total"] == 0


def test_confirmation_requires_csrf_and_rolls_back_when_effect_fails(app, db, monkeypatch):
    from app.models.assistant_action import AssistantAction
    from app.services.learning import LearningService
    content = create_content(administrator(app))
    actor = learner(app)
    app.state.assistant_provider = Planner("save_resource", {"content_id": content["id"], "saved": True})
    proposal = ask(actor).json()["proposal"]
    assert actor.post(f"/api/v1/assistant/actions/{proposal['id']}/confirm", json={}).status_code == 403
    original = LearningService.state
    def fail_after_effect(*args, **kwargs):
        original(*args, **kwargs)
        raise ValueError("Synthetic failure before commit")
    monkeypatch.setattr(LearningService, "state", fail_after_effect)
    response = confirm(actor, proposal)
    assert response.status_code == 503
    db.expire_all()
    row = db.get(AssistantAction, UUID(proposal["id"]))
    assert row.status == "pending"
    assert actor.get(f"/api/v1/content/{content['id']}").json()["saved"] is False


def test_model_planner_uses_one_bounded_groq_tool_call_with_no_structured_output_mode():
    import json
    import httpx
    from app.config import Settings
    from app.providers.assistant import RoutedProvider, AssistantUnavailable
    seen = []
    def respond(request):
        payload = json.loads(request.content)
        seen.append(payload)
        assert payload['model'] == 'openai/gpt-oss-20b'
        assert 'response_format' not in payload
        assert payload['parallel_tool_calls'] is False
        assert payload['tool_choice'] == 'required'
        assert payload['max_completion_tokens'] == 512
        return httpx.Response(200, json={'choices':[{'finish_reason':'tool_calls','message':{'tool_calls':[{'type':'function','function':{'name':'find_lessons','arguments':'{"q":"resume"}'}}]}}]})
    settings = Settings(_env_file=None, assistant_mode='external', assistant_provider_profile='groq', groq_api_key='synthetic-key', assistant_call_budget=1)
    provider = RoutedProvider(settings, transport=httpx.MockTransport(respond))
    tools = [{'type':'function','function':{'name':'find_lessons','description':'Search lessons','parameters':{'type':'object','properties':{'q':{'type':'string'}}}}}]
    result = provider.plan('Find resume lessons', [], tools, page='learning')
    assert result == {'name':'find_lessons','arguments':{'q':'resume'}}
    assert provider.calls_used == 1
    import pytest
    with pytest.raises(AssistantUnavailable):
        provider.plan('Find again', [], tools, page='learning')
    assert len(seen) == 1


def test_draft_tool_exposes_nested_quiz_contract_and_rejects_letter_answers():
    """Groq's live draft used answer='A' when the quiz shape was behind $ref."""
    import json
    from types import SimpleNamespace
    import pytest
    from app.services.assistant_workspace import WorkspaceAssistant
    workspace = WorkspaceAssistant(None, SimpleNamespace(role="instructor"), None, None, None, None)
    lesson = next(tool["function"] for tool in workspace.tools() if tool["function"]["name"] == "draft_lesson")
    assert "$ref" not in json.dumps(lesson["parameters"])
    question = lesson["parameters"]["properties"]["questions"]["items"]
    assert "correct_index" in question["required"]
    assert "zero-based" in question["properties"]["correct_index"]["description"]
    assert question["additionalProperties"] is False
    payload = {"title": "Progress updates", "summary": "Practice a short update.", "body": "State progress and next steps.",
               "questions": [{"question": "Which is clearer?", "options": ["Done", "Completed 2 of 3 tasks"], "answer": "B"}]}
    with pytest.raises(ValueError):
        workspace.validate("draft_lesson", payload)
    payload["questions"][0].pop("answer")
    payload["questions"][0]["correct_index"] = 1
    assert workspace.validate("draft_lesson", payload)["questions"][0]["correct_index"] == 1


def test_verified_company_can_prepare_a_draft_but_never_publish_with_assistant(app):
    from tests.helpers import get_company_id, patch_json
    from tests.helpers import register_and_login
    company = TestClient(app)
    register_and_login(company, email='workspace-company@example.test', role='company', company_name='Fictional workspace company')
    admin = administrator(app)
    payload = {'title':'Fictional OJT','description':'A fictional development placement.','requirements':'Use fictional records only.','location':'Legazpi City','type':'ojt','skills':['React']}
    app.state.assistant_provider = Planner('draft_listing', payload)
    assert ask(company).status_code == 503
    company_id = get_company_id(app, 'workspace-company@example.test')
    assert patch_json(admin, f'/api/v1/admin/companies/{company_id}/verification', {'status':'verified','reason':'Fictional test company only.','expected_version':1}).status_code == 200
    response = ask(company)
    assert response.status_code == 200, response.text
    saved = confirm(company, response.json()['proposal'])
    assert saved.status_code == 200, saved.text
    listings = company.get('/api/v1/company/listings').json()['items']
    assert len(listings) == 1 and listings[0]['status'] == 'draft'
    app.state.assistant_provider = Planner('publish_listing', {'id': listings[0]['id']})
    assert ask(company).status_code == 503
