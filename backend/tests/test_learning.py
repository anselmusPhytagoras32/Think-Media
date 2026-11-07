"""FR03/10/11 learning, moderated publication and isolated guidance tests."""

from uuid import UUID
import json

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from tests.helpers import (
    create_admin,
    login_admin,
    patch_json,
    post_json,
    register_and_login,
)

CONTENT = dict(
    title="Prepare your resume",
    summary="A resume preparation guide.",
    body="Prepare a concise resume that describes your skills and relevant projects. Review spelling before submitting.",
    tags=["resume", "OJT"],
    status="published",
)
QUESTIONS = [
    dict(
        question="What belongs on a resume?",
        options=["Relevant projects", "A password"],
        correct_index=0,
    ),
    dict(
        question="What should you check?",
        options=["Only color", "Spelling"],
        correct_index=1,
    ),
]


def administrator(app):
    create_admin(app)
    actor = TestClient(app)
    login_admin(actor)
    return actor


def learner(app, email="learner@example.test", role="student"):
    actor = TestClient(app)
    register_and_login(actor, email=email, role=role)
    return actor


def create_content(admin, *, status="published", questions=False, title=None):
    payload = {**CONTENT, "status": status}
    if title:
        payload["title"] = title
    if questions:
        payload["questions"] = QUESTIONS
    response = post_json(admin, "/api/v1/admin/content", payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_publication_visibility_search_and_admin_only_management(app):
    admin = administrator(app)
    student = learner(app)
    draft = create_content(admin, status="draft", title="Private draft material")
    published = create_content(admin)
    feed = student.get("/api/v1/content?q=resume&tag=OJT").json()
    assert feed["total"] == 1 and feed["items"][0]["id"] == published["id"]
    assert student.get(f"/api/v1/content/{draft['id']}").status_code in (403, 404)
    assert admin.get(f"/api/v1/content/{draft['id']}").status_code == 200
    assert student.get("/api/v1/admin/content").status_code == 403
    assert post_json(student, "/api/v1/admin/content", CONTENT).status_code == 403
    assert (
        patch_json(
            student, f"/api/v1/admin/content/{published['id']}", {"status": "archived"}
        ).status_code
        == 403
    )
    assert student.get("/api/v1/content?q=unmatched").json()["total"] == 0
    assert student.get("/api/v1/content?limit=101").status_code == 422
    assert TestClient(app).get("/api/v1/content").status_code == 401
    archived = patch_json(
        admin, f"/api/v1/admin/content/{published['id']}", {"status": "archived"}
    )
    assert archived.status_code == 200, archived.text
    assert student.get("/api/v1/content").json()["total"] == 0
    assert student.get(f"/api/v1/content/{published['id']}").status_code in (403, 404)
    assert admin.get("/api/v1/admin/content?status=archived").json()["total"] == 1
    assert admin.get("/api/v1/admin/content-events").json()["total"] >= 3
    assert student.get("/api/v1/admin/content-events").status_code == 403


def test_content_input_bounds_and_historical_quiz_keys_are_protected(app):
    admin = administrator(app)
    for invalid in (
        {"title": ""},
        {"title": "x" * 201},
        {"summary": "x" * 501},
        {"body": "x" * 20001},
        {"tags": ["x"] * 31},
        {"status": "invalid"},
        {"questions": [dict(question="Invalid", options=["one"], correct_index=0)]},
        {
            "questions": [
                dict(question="Invalid", options=["one", "two"], correct_index=2)
            ]
        },
    ):
        response = post_json(admin, "/api/v1/admin/content", {**CONTENT, **invalid})
        assert response.status_code == 422, response.text
    content = create_content(admin, questions=True)
    response = patch_json(
        admin, f"/api/v1/admin/content/{content['id']}", {"questions": QUESTIONS}
    )
    assert response.status_code == 422


def test_save_and_react_desired_state_are_idempotent_private_and_role_limited(app):
    admin = administrator(app)
    content = create_content(admin)
    student = learner(app)
    instructor = learner(app, email="instructor@example.test", role="instructor")
    company = TestClient(app)
    register_and_login(
        company,
        email="company@example.test",
        role="company",
        company_name="Synthetic Company",
    )
    for action, field in (("save", "saved"), ("react", "reacted")):
        path = f"/api/v1/content/{content['id']}/{action}"
        for actor in (student, instructor):
            for _ in range(2):
                response = post_json(actor, path, {field: True})
                assert response.status_code == 200, response.text
            detail = actor.get(f"/api/v1/content/{content['id']}").json()
            assert detail[field] is True
        assert post_json(company, path, {field: True}).status_code == 403
        assert post_json(admin, path, {field: True}).status_code == 403
        assert post_json(student, path, {field: "yes"}).status_code == 422
        assert post_json(student, path, {field: False}).status_code == 200
        assert student.get(f"/api/v1/content/{content['id']}").json()[field] is False
        assert instructor.get(f"/api/v1/content/{content['id']}").json()[field] is True
    draft = create_content(admin, status="draft")
    assert post_json(
        student, f"/api/v1/content/{draft['id']}/save", {"saved": True}
    ).status_code in (403, 404)


def test_quiz_hides_keys_and_scores_exact_complete_answer_set(app):
    admin = administrator(app)
    content = create_content(admin, questions=True)
    student = learner(app)
    feed = student.get("/api/v1/content").text
    detail = student.get(f"/api/v1/content/{content['id']}").text
    quiz_response = student.get(f"/api/v1/content/{content['id']}/quiz")
    assert quiz_response.status_code == 200
    assert "correct_index" not in quiz_response.text + feed + detail
    quiz = quiz_response.json()["questions"]
    assert len(quiz) == 2 and all(set(q) == {"id", "question", "options"} for q in quiz)
    by_text = {q["question"]: q for q in quiz}
    answers = {
        by_text[QUESTIONS[0]["question"]]["id"]: 0,
        by_text[QUESTIONS[1]["question"]]["id"]: 1,
    }
    result = post_json(
        student, f"/api/v1/content/{content['id']}/quiz", {"answers": answers}
    )
    assert result.status_code == 200, result.text
    assert result.json()["correct"] == 2 and result.json()["total"] == 2
    assert result.json()["score"] == 100
    partial = dict(answers)
    partial[by_text[QUESTIONS[1]["question"]]["id"]] = 0
    result = post_json(
        student, f"/api/v1/content/{content['id']}/quiz", {"answers": partial}
    )
    assert result.status_code == 200
    assert result.json()["correct"] == 1 and result.json()["score"] == 50
    from app.models import QuizAttempt

    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(QuizAttempt)) == 2
    for invalid in (
        {},
        {next(iter(answers)): 0},
        {**answers, "00000000-0000-0000-0000-000000000000": 0},
        {key: 99 for key in answers},
        {key: True for key in answers},
    ):
        assert (
            post_json(
                student, f"/api/v1/content/{content['id']}/quiz", {"answers": invalid}
            ).status_code
            == 422
        )
    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(QuizAttempt)) == 2
    draft = create_content(admin, status="draft", questions=True)
    assert student.get(f"/api/v1/content/{draft['id']}/quiz").status_code in (403, 404)


def test_reports_are_admin_only_and_resolution_is_final_audited(app):
    admin = administrator(app)
    content = create_content(admin)
    student = learner(app)
    other = learner(app, email="other@example.test")
    report = post_json(
        student,
        "/api/v1/reports",
        {"content_id": content["id"], "reason": "This guidance needs review."},
    )
    assert report.status_code == 201, report.text
    report_id = report.json()["id"]
    for actor in (student, other):
        assert actor.get("/api/v1/admin/reports").status_code == 403
        assert (
            patch_json(
                actor,
                f"/api/v1/admin/reports/{report_id}",
                {"status": "resolved", "resolution": "Ignore"},
            ).status_code
            == 403
        )
    queue = admin.get("/api/v1/admin/reports?status=pending").json()
    assert queue["total"] == 1 and queue["items"][0]["id"] == report_id
    resolution = patch_json(
        admin,
        f"/api/v1/admin/reports/{report_id}",
        {"status": "resolved", "resolution": "Reviewed and corrected the wording."},
    )
    assert resolution.status_code == 200, resolution.text
    resolved = admin.get("/api/v1/admin/reports?status=resolved").json()
    assert resolved["total"] == 1
    assert resolved["items"][0]["resolution"] == "Reviewed and corrected the wording."
    assert admin.get("/api/v1/admin/reports?status=pending").json()["total"] == 0
    assert (
        patch_json(
            admin,
            f"/api/v1/admin/reports/{report_id}",
            {"status": "resolved", "resolution": "Repeated"},
        ).status_code
        == 409
    )
    assert admin.get("/api/v1/admin/content-events").json()["total"] >= 2
    assert (
        post_json(
            student, "/api/v1/reports", {"content_id": content["id"], "reason": " "}
        ).status_code
        == 422
    )
    assert (
        post_json(
            student,
            "/api/v1/reports",
            {
                "content_id": "00000000-0000-0000-0000-000000000000",
                "reason": "Unknown target",
            },
        ).status_code
        == 404
    )
    draft = create_content(admin, status="draft")
    assert post_json(
        student,
        "/api/v1/reports",
        {"content_id": draft["id"], "reason": "Private material"},
    ).status_code in (403, 404)


def test_content_and_report_updates_roll_back_when_event_insert_fails(app, monkeypatch):
    from app.repositories.learning import ContentRepository

    admin = administrator(app)
    content = create_content(admin, status="draft")
    published = create_content(admin)
    student = learner(app)
    report = post_json(
        student,
        "/api/v1/reports",
        {"content_id": published["id"], "reason": "Needs review"},
    ).json()

    def fail_event(*args, **kwargs):
        raise RuntimeError("injected content audit failure")

    monkeypatch.setattr(ContentRepository, "add_event", fail_event)
    probe = TestClient(app, raise_server_exceptions=False)
    probe.cookies.update(admin.cookies)
    assert (
        patch_json(
            probe, f"/api/v1/admin/content/{content['id']}", {"status": "published"}
        ).status_code
        == 500
    )
    assert admin.get(f"/api/v1/content/{content['id']}").json()["status"] == "draft"
    assert (
        patch_json(
            probe,
            f"/api/v1/admin/reports/{report['id']}",
            {"status": "resolved", "resolution": "Review completed"},
        ).status_code
        == 500
    )
    assert admin.get("/api/v1/admin/reports?status=pending").json()["total"] == 1
    assert admin.get("/api/v1/admin/reports?status=resolved").json()["total"] == 0


def test_assistant_default_disabled_and_failure_leave_marketplace_operational(app):
    student = learner(app)
    disabled = post_json(
        student, "/api/v1/assistant", {"question": "How can I prepare for OJT?"}
    )
    assert disabled.status_code == 503
    assert disabled.json()["error"]["code"] == "ASSISTANT_UNAVAILABLE"
    assert student.get("/health").status_code == 200
    assert student.get("/api/v1/listings").status_code == 200
    assert student.get("/api/v1/applications/me").status_code == 200

    class FailingProvider:
        def respond(self, question, sources):
            raise TimeoutError("provider timeout with secret not-for-browser")

    app.state.assistant_provider = FailingProvider()
    failed = post_json(student, "/api/v1/assistant", {"question": "Help with a resume"})
    assert failed.status_code == 503
    assert "not-for-browser" not in failed.text
    assert student.get("/api/v1/listings").status_code == 200
    assert (
        post_json(student, "/api/v1/assistant", {"question": "x" * 2001}).status_code
        == 422
    )
    assert (
        post_json(
            student,
            "/api/v1/assistant",
            {"question": "Help", "provider_url": "https://attacker.example"},
        ).status_code
        == 422
    )


def test_assistant_receives_only_approved_resources_and_checks_citations(app):
    admin = administrator(app)
    published = create_content(admin)
    draft = create_content(admin, status="draft", title="PRIVATE DRAFT MARKER")
    student = learner(app)
    patch_json(student, "/api/v1/profiles/me", {"background": "PRIVATE PROFILE MARKER"})
    received = []

    class RecordingProvider:
        def respond(self, question, sources):
            received.append((question, sources))
            return dict(
                answer="Review the approved resume guide.",
                sources=[{"id": published["id"], "title": published["title"]}],
                uncertainty=True,
                mode="external",
            )

    app.state.assistant_provider = RecordingProvider()
    result = post_json(
        student, "/api/v1/assistant", {"question": "How do I prepare a resume?"}
    )
    assert result.status_code == 200, result.text
    assert received and received[0][0] == "How do I prepare a resume?"
    serialized = json.dumps(received, default=str)
    assert (
        "PRIVATE DRAFT MARKER" not in serialized
        and "PRIVATE PROFILE MARKER" not in serialized
    )
    assert published["id"] in serialized and draft["id"] not in serialized
    assert all(source["id"] == published["id"] for source in result.json()["sources"])

    class InvalidCitationProvider:
        def respond(self, question, sources):
            return dict(
                answer="Invented unsupported statement",
                sources=[{"id": draft["id"], "title": draft["title"]}],
                uncertainty=True,
                mode="external",
            )

    app.state.assistant_provider = InvalidCitationProvider()
    rejected = post_json(
        student, "/api/v1/assistant", {"question": "Tell me about my resume"}
    )
    assert rejected.status_code == 503
    assert "PRIVATE DRAFT MARKER" not in rejected.text


def test_explicit_retrieval_provider_is_labeled_and_handles_no_matches(app):
    from app.providers.assistant import RetrievalProvider

    admin = administrator(app)
    published = create_content(admin)
    student = learner(app)
    app.state.assistant_provider = RetrievalProvider()
    response = post_json(student, "/api/v1/assistant", {"question": "resume"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["mode"] == "retrieval"
    assert published["id"] in {source["id"] for source in result["sources"]}
    assert (
        "lookup" in result["answer"].lower() or "resource" in result["answer"].lower()
    )
    unknown = post_json(
        student, "/api/v1/assistant", {"question": "zzzunmatchedtermzzz"}
    )
    assert unknown.status_code == 200
    assert unknown.json()["sources"] == []
    assert unknown.json()["uncertainty"]


def test_assistant_rate_limit_is_bounded_and_does_not_block_applications(app):
    from app.security.throttle import Throttle

    actor = learner(app)
    app.state.assistant_throttle = Throttle(max_attempts=2, window_seconds=60)
    for _ in range(2):
        assert (
            post_json(actor, "/api/v1/assistant", {"question": "resume"}).status_code
            == 503
        )
    limited = post_json(actor, "/api/v1/assistant", {"question": "resume"})
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"
    assert int(limited.headers["Retry-After"]) > 0
    assert actor.get("/api/v1/applications/me").status_code == 200
    assert actor.get("/health").status_code == 200
