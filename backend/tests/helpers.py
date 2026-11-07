"""HTTP/database helpers shared by backend tests."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.security.tokens import hash_session_token

TEST_ORIGIN = "http://testserver"
TEST_PASSWORD = "correct-horse-battery-staple"
ADMIN_PASSWORD = "administrator-password-123"


def get_csrf(client: TestClient) -> str:
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


def csrf_headers(token: str, *, origin: str | None = TEST_ORIGIN) -> dict[str, str]:
    headers = {"X-CSRF-Token": token}
    if origin is not None:
        headers["Origin"] = origin
    return headers


def post_json(
    client: TestClient,
    path: str,
    payload: dict | None = None,
    *,
    origin: str | None = TEST_ORIGIN,
    token: str | None = None,
    headers: dict[str, str] | None = None,
):
    token = token if token is not None else get_csrf(client)
    merged = csrf_headers(token, origin=origin)
    if headers:
        merged.update(headers)
    return client.post(path, json=payload, headers=merged)


def patch_json(
    client: TestClient,
    path: str,
    payload: dict,
    *,
    origin: str | None = TEST_ORIGIN,
    token: str | None = None,
    headers: dict[str, str] | None = None,
):
    token = token if token is not None else get_csrf(client)
    merged = csrf_headers(token, origin=origin)
    if headers:
        merged.update(headers)
    return client.patch(path, json=payload, headers=merged)


def register(
    client: TestClient,
    *,
    email: str,
    role: str = "student",
    password: str = TEST_PASSWORD,
    display_name: str = "Test User",
    company_name: str | None = None,
    extra: dict | None = None,
):
    payload: dict = {
        "email": email,
        "password": password,
        "display_name": display_name,
        "role": role,
    }
    if company_name is not None:
        payload["company_name"] = company_name
    if extra:
        payload.update(extra)
    return post_json(client, "/api/v1/auth/register", payload)


def login(
    client: TestClient,
    *,
    email: str,
    password: str = TEST_PASSWORD,
):
    return post_json(
        client, "/api/v1/auth/login", {"email": email, "password": password}
    )


def register_and_login(
    client: TestClient, *, email: str, role: str = "student", **kwargs
):
    response = register(client, email=email, role=role, **kwargs)
    assert response.status_code == 201, response.text
    response = login(client, email=email, password=kwargs.get("password", TEST_PASSWORD))
    assert response.status_code == 200, response.text
    return response


def create_admin(app, *, email: str = "admin@example.org", display_name: str = "Admin"):
    from app.services.accounts import AccountService

    with app.state.session_factory() as session:
        user = AccountService(session).create_administrator(
            email=email, password=ADMIN_PASSWORD, display_name=display_name
        )
        return user.id


def login_admin(client: TestClient, email: str = "admin@example.org"):
    response = login(client, email=email, password=ADMIN_PASSWORD)
    assert response.status_code == 200, response.text
    return response


def get_company_row(app, user_id: uuid.UUID):
    from app.models import CompanyProfile

    with app.state.session_factory() as session:
        return session.query(CompanyProfile).filter_by(user_id=user_id).one()


def get_company_id(app, email: str) -> uuid.UUID:
    from sqlalchemy import select

    from app.models import CompanyProfile, User

    with app.state.session_factory() as session:
        company_id = session.scalar(
            select(CompanyProfile.id)
            .join(User, User.id == CompanyProfile.user_id)
            .where(User.email == email)
        )
        assert company_id is not None
        return company_id


def session_token_hash_from_client(client: TestClient) -> str | None:
    raw = client.cookies.get("tm_session")
    return hash_session_token(raw) if raw else None
