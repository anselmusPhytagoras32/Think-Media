"""Authentication, sessions, CSRF, cookies and throttling (FR01, NFR02)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import Settings
from app.models import SessionToken, User
from app.security.cookies import set_session_cookie
from app.security.throttle import Throttle
from app.security.tokens import hash_session_token
from app.time_utils import utcnow
from tests.helpers import (
    TEST_ORIGIN,
    TEST_PASSWORD,
    csrf_headers,
    get_csrf,
    login,
    post_json,
    register,
)


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_register_all_public_roles_and_no_password_leak(client, db):
    for role in ("student", "instructor", "company"):
        response = register(
            client,
            email=f"{role}@example.org",
            role=role,
            display_name=f"{role.title()} User",
            company_name="Acme Corp" if role == "company" else None,
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["user"]["role"] == role
        assert body["user"]["email"] == f"{role}@example.org"
        assert body["profile"]["kind"] == role
        assert "password" not in response.text.lower()
        if role == "company":
            assert body["profile"]["verification_status"] == "pending"
            assert body["profile"]["verification_version"] == 1

    users = db.scalars(select(User)).all()
    assert len(users) == 3
    assert all(user.password_hash.startswith("$argon2id$") for user in users)


def test_email_is_normalized_and_unique_case_insensitively(client):
    first = register(client, email="  Student@Example.ORG ")
    assert first.status_code == 201
    assert first.json()["user"]["email"] == "student@example.org"

    duplicate = register(client, email="STUDENT@example.org")
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_EXISTS"

    login_response = login(client, email="sTuDeNt@ExAmPlE.oRg")
    assert login_response.status_code == 200


def test_administrator_cannot_self_register(client, db):
    response = register(client, email="admin@example.org", role="administrator")
    assert response.status_code == 422
    assert "role" in response.json()["error"]["fields"]
    assert db.scalar(select(func.count()).select_from(User)) == 0


def test_public_payload_cannot_mass_assign_privileged_fields(client, db):
    for extra in (
        {"is_admin": True},
        {"verification_status": "verified"},
        {"verification_version": 99},
        {"password_hash": "$argon2id$fake"},
        {"user_id": "00000000-0000-0000-0000-000000000000"},
    ):
        response = register(client, email=f"x{len(extra)}@example.org", extra=extra)
        assert response.status_code == 422, (extra, response.text)
        assert set(response.json()["error"]["fields"]) & set(extra)
    assert db.scalar(select(func.count()).select_from(User)) == 0


@pytest.mark.parametrize(
    "payload,field",
    [
        ({"password": "too-short"}, "password"),
        ({"password": "x" * 129}, "password"),
        ({"display_name": " "}, "display_name"),
        ({"display_name": "x" * 101}, "display_name"),
        ({"email": "a" * 250 + "@example.org"}, "email"),
    ],
)
def test_bounded_registration_inputs(client, payload, field):
    body = {
        "email": "valid@example.org",
        "password": TEST_PASSWORD,
        "display_name": "Valid Person",
        "role": "student",
    }
    body.update(payload)
    response = post_json(client, "/api/v1/auth/register", body)
    assert response.status_code == 422
    assert field in response.json()["error"]["fields"]


def test_company_registration_requires_company_name(client):
    response = register(client, email="co@example.org", role="company")
    assert response.status_code == 422
    assert "company_name" in response.json()["error"]["fields"]

    response = register(
        client, email="student@example.org", role="student", company_name="Acme"
    )
    assert response.status_code == 422
    assert "company_name" in response.json()["error"]["fields"]


def test_registration_does_not_sign_in(client):
    response = register(client, email="nosignin@example.org")
    assert response.status_code == 201
    assert client.get("/api/v1/auth/me").status_code == 401


def test_display_name_is_unicode_safe_and_trimmed(client):
    response = register(client, email="maria@example.org", display_name="  María Ángela  ")
    assert response.status_code == 201
    assert response.json()["user"]["display_name"] == "María Ángela"


def test_login_failures_are_generic(client):
    register(client, email="known@example.org")
    wrong = login(client, email="known@example.org", password="wrong-password-123")
    unknown = login(client, email="nobody@example.org", password="wrong-password-123")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["error"]["code"] == unknown.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert wrong.json()["error"]["message"] == unknown.json()["error"]["message"]


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_login_rotates_session_and_csrf(client, app):
    register(client, email="rotate@example.org")
    old_csrf = get_csrf(client)
    old_cookie = client.cookies.get("tm_session")

    response = login(client, email="rotate@example.org")
    assert response.status_code == 200
    new_cookie = client.cookies.get("tm_session")
    assert new_cookie != old_cookie

    # Old CSRF token is invalid for the new session.
    stale = client.patch(
        "/api/v1/profiles/me",
        json={"display_name": "Nope"},
        headers=csrf_headers(old_csrf),
    )
    assert stale.status_code == 403
    assert stale.json()["error"]["code"] == "CSRF_INVALID"

    # Old session cookie no longer authenticates.
    old_client = TestClient(app)
    old_client.cookies.set("tm_session", old_cookie)
    assert old_client.get("/api/v1/auth/me").status_code == 401


def test_session_cookie_is_hashed_and_flags_are_safe(client, db):
    register(client, email="cookie@example.org")
    response = login(client, email="cookie@example.org")
    assert response.status_code == 200
    raw = client.cookies.get("tm_session")
    assert raw

    stored = db.scalar(
        select(SessionToken).where(SessionToken.token_hash == hash_session_token(raw))
    )
    assert stored is not None
    assert stored.token_hash != raw
    assert len(stored.token_hash) == 64

    set_cookie = response.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Path=/" in set_cookie
    assert "Secure" not in set_cookie  # explicit test/local HTTP mode

    production = Settings(
        _env_file=None,
        app_env="production",
        database_url="postgresql+psycopg://unused@localhost/unused",
        csrf_secret="test-secret",
    )
    from starlette.responses import Response

    prod_response = Response()
    set_session_cookie(prod_response, "opaque", production)
    prod_cookie = prod_response.headers["set-cookie"]
    assert "Secure" in prod_cookie
    assert "HttpOnly" in prod_cookie


def test_logout_revokes_session_and_is_idempotent(client, app):
    register(client, email="logout@example.org")
    login(client, email="logout@example.org")
    cookie = client.cookies.get("tm_session")
    token = get_csrf(client)

    response = client.post("/api/v1/auth/logout", headers=csrf_headers(token))
    assert response.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401

    # Repeated logout with the same (now revoked) cookie + CSRF token is safe.
    again = TestClient(app)
    again.cookies.set("tm_session", cookie)
    response = again.post("/api/v1/auth/logout", headers=csrf_headers(token))
    assert response.status_code == 204


def test_logout_requires_csrf(client):
    register(client, email="logout2@example.org")
    login(client, email="logout2@example.org")
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_INVALID"
    assert client.get("/api/v1/auth/me").status_code == 200


def test_expired_session_is_rejected(client, app, db):
    register(client, email="expired@example.org")
    login(client, email="expired@example.org")
    raw = client.cookies.get("tm_session")
    row = db.scalar(
        select(SessionToken).where(SessionToken.token_hash == hash_session_token(raw))
    )
    now = utcnow()
    row.created_at = now - timedelta(hours=10)
    row.expires_at = now - timedelta(hours=1)
    db.commit()

    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_revoked_session_is_rejected(client, db):
    register(client, email="revoked@example.org")
    login(client, email="revoked@example.org")
    raw = client.cookies.get("tm_session")
    row = db.scalar(
        select(SessionToken).where(SessionToken.token_hash == hash_session_token(raw))
    )
    row.revoked_at = utcnow()
    db.commit()
    assert client.get("/api/v1/auth/me").status_code == 401


def test_csrf_missing_wrong_and_origin_checks(client):
    token = get_csrf(client)
    payload = {
        "email": "csrf@example.org",
        "password": TEST_PASSWORD,
        "display_name": "CSRF User",
        "role": "student",
    }

    missing = client.post("/api/v1/auth/register", json=payload, headers={"Origin": TEST_ORIGIN})
    assert missing.status_code == 403
    assert missing.json()["error"]["code"] == "CSRF_INVALID"

    wrong = client.post(
        "/api/v1/auth/register",
        json=payload,
        headers={"X-CSRF-Token": "wrong", "Origin": TEST_ORIGIN},
    )
    assert wrong.status_code == 403
    assert wrong.json()["error"]["code"] == "CSRF_INVALID"

    bad_origin = client.post(
        "/api/v1/auth/register",
        json=payload,
        headers={"X-CSRF-Token": token, "Origin": "https://evil.example"},
    )
    assert bad_origin.status_code == 403
    assert bad_origin.json()["error"]["code"] == "CSRF_INVALID"

    # Documented implementation default: non-browser clients without an Origin
    # header are accepted (they carry no ambient cross-site credentials).
    no_origin = client.post(
        "/api/v1/auth/register", json=payload, headers={"X-CSRF-Token": token}
    )
    assert no_origin.status_code == 201


def test_csrf_endpoint_is_no_store(client):
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["csrf_token"]


def test_login_throttle_blocks_then_recovers(client, app):
    register(client, email="throttle@example.org")
    clock = Clock()
    app.state.login_throttle = Throttle(
        max_attempts=3, window_seconds=60, clock=clock
    )

    for _ in range(3):
        response = login(client, email="throttle@example.org", password="wrong-password-123")
        assert response.status_code == 401

    blocked = login(client, email="throttle@example.org", password=TEST_PASSWORD)
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "RATE_LIMITED"
    assert int(blocked.headers["Retry-After"]) >= 1

    clock.now += 61
    recovered = login(client, email="throttle@example.org", password=TEST_PASSWORD)
    assert recovered.status_code == 200


def test_registration_throttle_is_testable(client, app):
    app.state.registration_throttle = Throttle(
        max_attempts=2, window_seconds=60, clock=Clock()
    )
    assert register(client, email="one@example.org").status_code == 201
    assert register(client, email="two@example.org").status_code == 201
    blocked = register(client, email="three@example.org")
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "RATE_LIMITED"


def test_no_default_administrator_exists(client, db):
    assert db.scalar(select(func.count()).select_from(User).where(User.role == "administrator")) == 0
