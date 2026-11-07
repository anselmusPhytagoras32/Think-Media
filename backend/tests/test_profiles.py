"""Profile read/update, role separation and cross-user isolation (FR02)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import InstructorProfile, StudentProfile, User
from tests.helpers import (
    create_admin,
    login,
    login_admin,
    patch_json,
    register_and_login,
)


def test_student_profile_persists_across_sessions(client, app):
    register_and_login(client, email="student@example.org")
    response = client.get("/api/v1/profiles/me")
    assert response.status_code == 200
    assert response.json()["profile"] == {
        "kind": "student",
        "institution": "",
        "program": "",
        "location": "",
        "background": "",
        "skills": [],
        "interests": [],
    }

    updated = patch_json(
        client,
        "/api/v1/profiles/me",
        {
            "display_name": "  Maria Ángela  ",
            "institution": "  University of the Philippines  ",
            "program": "BS Computer Science",
            "skills": [" Python ", "SQL"],
            "interests": ["OJT", "Data"],
        },
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["user"]["display_name"] == "Maria Ángela"
    assert body["profile"]["institution"] == "University of the Philippines"
    assert body["profile"]["skills"] == ["Python", "SQL"]

    # A brand-new client/session sees the persisted values.
    second = TestClient(app)
    assert login(second, email="student@example.org").status_code == 200
    again = second.get("/api/v1/profiles/me")
    assert again.status_code == 200
    assert again.json()["profile"]["program"] == "BS Computer Science"
    assert again.json()["user"]["display_name"] == "Maria Ángela"
    assert again.headers["Cache-Control"] == "no-store"


def test_profile_update_requires_a_field(client):
    register_and_login(client, email="empty@example.org")
    response = patch_json(client, "/api/v1/profiles/me", {})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_student_cannot_edit_company_or_verification_fields(client, db):
    register_and_login(client, email="student2@example.org")
    response = patch_json(
        client,
        "/api/v1/profiles/me",
        {"company_name": "Acme", "description": "x", "location": "Manila"},
    )
    assert response.status_code == 422
    assert set(response.json()["error"]["fields"]) >= {"company_name", "description"}

    for extra in (
        {"verification_status": "verified"},
        {"verification_version": 2},
        {"role": "administrator"},
        {"email": "other@example.org"},
        {"user_id": "00000000-0000-0000-0000-000000000000"},
        {"is_admin": True},
    ):
        response = patch_json(client, "/api/v1/profiles/me", extra)
        assert response.status_code == 422, (extra, response.text)

    user = db.scalar(select(User).where(User.email == "student2@example.org"))
    assert user.role == "student"


def test_instructor_profile_is_stored_separately(client, db):
    register_and_login(
        client,
        email="instructor@example.org",
        role="instructor",
        display_name="Prof. Reyes",
    )
    response = client.get("/api/v1/profiles/me")
    assert response.status_code == 200
    assert response.json()["profile"] == {"kind": "instructor", "institution": ""}

    updated = patch_json(
        client,
        "/api/v1/profiles/me",
        {"institution": "  Ateneo de Manila University  "},
    )
    assert updated.status_code == 200
    assert updated.json()["profile"]["institution"] == "Ateneo de Manila University"

    user = db.scalar(select(User).where(User.email == "instructor@example.org"))
    assert db.scalar(select(InstructorProfile).where(InstructorProfile.user_id == user.id))
    assert (
        db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id)) is None
    )

    # Instructor cannot fill student-only fields.
    response = patch_json(
        client,
        "/api/v1/profiles/me",
        {"program": "BS CS", "skills": ["Python"], "interests": ["OJT"]},
    )
    assert response.status_code == 422
    assert set(response.json()["error"]["fields"]) == {"program", "skills", "interests"}


def test_company_profile_update_excludes_verification_fields(client, db):
    register_and_login(
        client,
        email="company@example.org",
        role="company",
        company_name="Acme",
    )
    response = client.get("/api/v1/profiles/me")
    assert response.json()["profile"]["verification_status"] == "pending"
    assert response.json()["profile"]["verification_version"] == 1

    updated = patch_json(
        client,
        "/api/v1/profiles/me",
        {
            "company_name": "Acme Philippines",
            "description": "  We build things.  ",
            "location": "Quezon City",
            "website": "https://acme.example",
        },
    )
    assert updated.status_code == 200, updated.text
    profile = updated.json()["profile"]
    assert profile["company_name"] == "Acme Philippines"
    assert profile["description"] == "We build things."
    assert profile["website"] == "https://acme.example"
    assert profile["verification_status"] == "pending"
    assert profile["verification_version"] == 1

    for extra in (
        {"verification_status": "verified"},
        {"verification_version": 2},
    ):
        response = patch_json(client, "/api/v1/profiles/me", extra)
        assert response.status_code == 422, (extra, response.text)


def test_company_website_and_length_validation(client):
    register_and_login(
        client, email="company2@example.org", role="company", company_name="Beta"
    )
    assert patch_json(client, "/api/v1/profiles/me", {"website": "ftp://beta.example"}).status_code == 422
    assert patch_json(client, "/api/v1/profiles/me", {"website": "not a url"}).status_code == 422
    assert patch_json(client, "/api/v1/profiles/me", {"website": "x" * 2049}).status_code == 422
    assert patch_json(client, "/api/v1/profiles/me", {"description": "x" * 2001}).status_code == 422
    assert patch_json(client, "/api/v1/profiles/me", {"location": "x" * 201}).status_code == 422
    assert patch_json(client, "/api/v1/profiles/me", {"company_name": "  "}).status_code == 422

    blank = patch_json(client, "/api/v1/profiles/me", {"website": "   "})
    assert blank.status_code == 200
    assert blank.json()["profile"]["website"] is None


def test_student_skills_are_bounded_and_unique(client):
    register_and_login(client, email="skills@example.org")
    duplicate = patch_json(
        client, "/api/v1/profiles/me", {"skills": ["Python", " Python "]}
    )
    assert duplicate.status_code == 422
    assert "skills" in duplicate.json()["error"]["fields"]

    too_many = patch_json(
        client, "/api/v1/profiles/me", {"skills": [f"skill-{i}" for i in range(31)]}
    )
    assert too_many.status_code == 422

    too_long = patch_json(client, "/api/v1/profiles/me", {"skills": ["x" * 81]})
    assert too_long.status_code == 422

    blank_entry = patch_json(client, "/api/v1/profiles/me", {"skills": ["   "]})
    assert blank_entry.status_code == 422

    program_too_long = patch_json(
        client, "/api/v1/profiles/me", {"program": "x" * 201}
    )
    assert program_too_long.status_code == 422


def test_administrator_edits_display_name_only(client, app):
    create_admin(app)
    login_admin(client)
    response = patch_json(
        client, "/api/v1/profiles/me", {"display_name": "  Lead Admin  "}
    )
    assert response.status_code == 200
    assert response.json()["profile"] == {"kind": "administrator"}
    assert response.json()["user"]["display_name"] == "Lead Admin"

    for field in ("institution", "company_name", "skills"):
        response = patch_json(client, "/api/v1/profiles/me", {field: "x"})
        assert response.status_code == 422, (field, response.text)


def test_cross_user_profiles_are_isolated(client, app, db):
    # User A.
    register_and_login(client, email="alpha@example.org", display_name="Alpha")
    patch_json(client, "/api/v1/profiles/me", {"institution": "Alpha University"})

    # User B cannot read or mutate A's profile. There is intentionally no
    # profile-by-ID endpoint.
    other = TestClient(app)
    register_and_login(other, email="beta@example.org", display_name="Beta")
    beta_id = db.scalar(select(User.id).where(User.email == "beta@example.org"))
    alpha_id = db.scalar(select(User.id).where(User.email == "alpha@example.org"))

    assert other.get(f"/api/v1/profiles/{alpha_id}").status_code == 404
    attempt = patch_json(
        other, "/api/v1/profiles/me", {"user_id": str(alpha_id), "display_name": "Hacked"}
    )
    assert attempt.status_code == 422

    patch_json(other, "/api/v1/profiles/me", {"institution": "Beta College"})
    alpha = client.get("/api/v1/profiles/me").json()
    beta = other.get("/api/v1/profiles/me").json()
    assert alpha["profile"]["institution"] == "Alpha University"
    assert beta["profile"]["institution"] == "Beta College"
    assert alpha["user"]["display_name"] == "Alpha"
    assert beta["user"]["display_name"] == "Beta"
    assert beta_id != alpha_id


def test_csv_like_unicode_values_and_manila_timestamps(client):
    register_and_login(client, email="unicode@example.org", display_name="José Rizal")
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    created_at = response.json()["user"]["created_at"]
    assert created_at.endswith("+08:00")
    assert response.json()["user"]["display_name"] == "José Rizal"


def test_student_location_and_background_persist_and_remain_private(client, app):
    """FR02/NFR03: added profile data persists and remains self-only."""
    registration = register_and_login(client, email="details@example.org")
    response = patch_json(client, "/api/v1/profiles/me", {
        "location": " Legazpi City ", "background": " Building accessible web apps. "
    })
    assert response.status_code == 200, response.text
    second_session = TestClient(app)
    login(second_session, email="details@example.org")
    saved = second_session.get("/api/v1/profiles/me").json()["profile"]
    assert saved["location"] == "Legazpi City"
    assert saved["background"] == "Building accessible web apps."
    other = TestClient(app)
    register_and_login(other, email="different@example.org")
    assert other.get("/api/v1/profiles/me").json()["profile"]["background"] == ""
    for payload in ({"background": "x" * 2001}, {"location": "x" * 201}, {"background": None}, {"contact_email": "hr@example.org"}):
        assert patch_json(client, "/api/v1/profiles/me", payload).status_code == 422
    assert client.get("/api/v1/profiles/me").json()["profile"]["background"] == saved["background"]


def test_company_contacts_validate_persist_and_clear(client, app):
    register_and_login(client, email="contacts@example.org", role="company", company_name="Local Company")
    response = patch_json(client, "/api/v1/profiles/me", {
        "contact_email": " HR@Example.ORG ", "contact_phone": " +63 (917) 123-4567 "
    })
    assert response.status_code == 200, response.text
    other = TestClient(app)
    login(other, email="contacts@example.org")
    profile = other.get("/api/v1/profiles/me").json()["profile"]
    assert profile["contact_email"] == "hr@example.org"
    assert profile["contact_phone"] == "+63 (917) 123-4567"
    for payload in ({"contact_email": "invalid"}, {"contact_phone": "call me"}, {"contact_phone": "12"}, {"contact_phone": "1" * 16}, {"background": "private"}):
        assert patch_json(client, "/api/v1/profiles/me", payload).status_code == 422
    response = patch_json(client, "/api/v1/profiles/me", {"contact_email": None, "contact_phone": " "})
    assert response.status_code == 200
    assert response.json()["profile"]["contact_email"] is None
    assert response.json()["profile"]["contact_phone"] is None


def test_instructor_cannot_assign_new_role_specific_details(client):
    register_and_login(client, email="limited@example.org", role="instructor")
    for payload in ({"background": "x"}, {"location": "Manila"}, {"contact_phone": "+639171234567"}, {"contact_email": "hr@example.org"}):
        assert patch_json(client, "/api/v1/profiles/me", payload).status_code == 422
