"""FR03/11: real PostgreSQL review, role boundaries and published materials."""

import json
from pathlib import Path

from sqlalchemy import func, select

from app.models import LearningReview
from tests.helpers import get_csrf, patch_json, post_json
from tests.test_learning import administrator, learner

INSTRUCTOR = "/api/v1/instructor/learning"
ADMIN = "/api/v1/admin/learning-submissions"
SKILL = {"kind": "skill", "title": "Interview communication", "summary": "Practice structured answers."}
LESSON = {
    "kind": "lesson",
    "title": "Present a project using STAR",
    "summary": "Practice a short structured interview answer.",
    "body": "State the situation, task, action and result in a real project.",
    "tags": ["OJT"],
    "links": [{"label": "Interview practice", "url": "https://example.org/practice"}],
    "questions": [{
        "question": "Which part explains what you did?",
        "options": ["Action", "Situation"],
        "correct_index": 0,
        "feedback": "Action explains your own contribution.",
    }],
}
PDF = (Path(__file__).resolve().parents[2] / "presentation" / "fictional-resume.pdf").read_bytes()


def save(client, payload, *, item=None, attachment=None, remove=False):
    data = {"draft": json.dumps(payload)}
    if item:
        data["expected_version"] = str(item["version"])
    if remove:
        data["remove_attachment"] = "true"
    return client.request(
        "PUT" if item else "POST", f"{INSTRUCTOR}/{item['id']}" if item else INSTRUCTOR,
        headers={"X-CSRF-Token": get_csrf(client)}, data=data,
        files={"file": attachment} if attachment else None,
    )


def submit(actor, item):
    return post_json(actor, f"{INSTRUCTOR}/{item['id']}/submit", {"expected_version": item["version"]})


def review(admin, item, decision="approved", feedback=""):
    return patch_json(admin, f"{ADMIN}/{item['id']}", {
        "expected_version": item["version"], "decision": decision, "feedback": feedback,
    })


def checked(response, code=200):
    assert response.status_code == code, response.text
    return response.json()


def test_review_resubmission_publishes_a_skill_and_lesson_atomically(app, db):
    instructor = learner(app, email="author@example.test", role="instructor")
    peer = learner(app, email="peer@example.test", role="instructor")
    student = learner(app)
    admin = administrator(app)

    skill = checked(save(instructor, SKILL), 201)
    assert student.get("/api/v1/learning-skills").json()["total"] == 0
    assert admin.get(f"{ADMIN}/{skill['id']}").status_code == 404
    skill = checked(submit(instructor, skill))
    assert review(instructor, skill).status_code == 403
    skill = checked(review(admin, skill))
    assert student.get("/api/v1/learning-skills?q=INTERVIEW").json()["items"][0]["id"] == skill["id"]

    payload = {**LESSON, "skill_ids": [skill["id"]]}
    draft = checked(save(instructor, payload, attachment=("lesson.pdf", PDF, "application/pdf")), 201)
    id = draft["id"]
    assert checked(instructor.get(f"{INSTRUCTOR}/{id}"))["draft"] == draft["draft"]
    assert peer.get(f"{INSTRUCTOR}/{id}").status_code == 404
    assert save(peer, payload, item=draft).status_code == 404
    assert peer.get(f"{INSTRUCTOR}/{id}/attachment").status_code == 404
    assert student.get(f"{INSTRUCTOR}/{id}/attachment").status_code == 403
    assert admin.get(f"{ADMIN}/{id}/attachment").status_code == 404
    assert instructor.get(f"{INSTRUCTOR}/{id}/attachment").content == PDF
    pending = checked(submit(instructor, draft))
    assert save(instructor, payload, item=pending).status_code == 409
    assert submit(instructor, draft).status_code == 409
    assert student.get("/api/v1/content").json()["total"] == 0
    assert admin.get(f"{ADMIN}/{id}/attachment").content == PDF
    assert review(instructor, pending).status_code == 403
    assert review(admin, pending, "changes_requested").status_code == 422
    changed = checked(review(admin, pending, "changes_requested", "Include a result."))
    assert checked(instructor.get(f"{INSTRUCTOR}/{id}"))["review"]["feedback"] == "Include a result."
    assert review(admin, pending).status_code == 409

    updated = checked(save(instructor, {**payload, "body": payload["body"] + " Add a measurable result."}, item=changed))
    assert updated["attachment_name"] == "lesson.pdf"
    again = checked(submit(instructor, updated))
    approved = checked(review(admin, again))
    assert review(admin, again).status_code == 409
    assert db.scalar(select(func.count()).select_from(LearningReview).where(LearningReview.submission_id == id)) == 2
    content_id = approved["published_content_id"]
    assert student.get(f"/api/v1/content?tag={SKILL['title']}").json()["items"][0]["id"] == content_id
    detail = checked(student.get(f"/api/v1/content/{content_id}"))
    assert detail["links"] == LESSON["links"] and detail["attachment_name"] == "lesson.pdf"
    assert "questions" not in detail and "review" not in detail
    response = student.get(f"/api/v1/content/{content_id}/attachment")
    assert response.content == PDF
    assert response.headers["content-disposition"] == 'attachment; filename="lesson.pdf"'
    question = checked(student.get(f"/api/v1/content/{content_id}/quiz"))["questions"][0]
    assert set(question) == {"id", "question", "options"}
    scored = checked(post_json(student, f"/api/v1/content/{content_id}/quiz", {"answers": {question["id"]: 0}}))
    assert scored["correct"] == 1 and scored["feedback"][0]["text"] == LESSON["questions"][0]["feedback"]
    checked(patch_json(admin, f"/api/v1/admin/content/{content_id}", {"status": "archived"}))
    assert student.get(f"/api/v1/content/{content_id}/attachment").status_code == 404


def test_rejects_invalid_materials_and_duplicate_skill_publication(app):
    instructor = learner(app, email="author@example.test", role="instructor")
    student = learner(app)
    admin = administrator(app)
    assert save(student, LESSON).status_code == 403
    assert save(instructor, LESSON, attachment=("invalid.pdf", b"not a PDF", "application/pdf")).status_code == 422
    assert save(instructor, LESSON, attachment=("large.pdf", b" " * (5 * 1024 * 1024 + 1), "application/pdf")).status_code == 413
    assert save(instructor, {**LESSON, "links": [{"label": "Invalid", "url": "file:///invalid"}]}).status_code == 422
    assert save(instructor, {**LESSON, "status": "published"}).status_code == 422

    first = checked(save(instructor, SKILL), 201)
    assert save(instructor, {**LESSON, "skill_ids": [first["id"]]}).status_code == 422
    checked(review(admin, checked(submit(instructor, first))))
    duplicate = checked(save(instructor, {**SKILL, "title": SKILL["title"].upper()}), 201)
    pending = checked(submit(instructor, duplicate))
    response = review(admin, pending)
    assert response.status_code == 409 and response.json()["error"]["code"] == "SKILL_EXISTS"
    assert checked(admin.get(f"{ADMIN}/{duplicate['id']}"))["status"] == "pending"

    draft = checked(save(instructor, LESSON, attachment=("old.pdf", PDF, "application/pdf")), 201)
    draft = checked(save(instructor, LESSON, item=draft, remove=True))
    assert draft["attachment_name"] is None
    assert instructor.get(f"{INSTRUCTOR}/{draft['id']}/attachment").status_code == 404
