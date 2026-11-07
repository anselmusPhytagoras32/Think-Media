"""Health, uniform error envelopes, request IDs and body bounds."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.helpers import TEST_ORIGIN, get_csrf, post_json


def test_health_is_minimal(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    body = response.text.lower()
    assert "postgres" not in body
    assert "database" not in body


def test_unknown_route_uses_error_envelope(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "NOT_FOUND"
    assert payload["error"]["fields"] == {}
    assert payload["error"]["request_id"] == response.headers["X-Request-ID"]


def test_request_id_is_echoed_when_safe(client):
    response = client.get("/api/v1/does-not-exist", headers={"X-Request-ID": "req-123"})
    assert response.headers["X-Request-ID"] == "req-123"
    assert response.json()["error"]["request_id"] == "req-123"


def test_unsafe_request_id_is_replaced(client):
    response = client.get(
        "/api/v1/does-not-exist", headers={"X-Request-ID": "bad\nvalue"}
    )
    assert response.headers["X-Request-ID"] != "bad\nvalue"


def test_validation_errors_use_uniform_envelope(client):
    response = post_json(
        client,
        "/api/v1/auth/register",
        {
            "email": "not-an-email",
            "password": "short",
            "display_name": "",
            "role": "student",
        },
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert set(error["fields"]) >= {"email", "password", "display_name"}
    assert error["request_id"]


def test_malformed_json_uses_uniform_envelope(client):
    token = get_csrf(client)
    response = client.post(
        "/api/v1/auth/register",
        content=b"{not json",
        headers={
            "Content-Type": "application/json",
            "X-CSRF-Token": token,
            "Origin": TEST_ORIGIN,
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "body" in response.json()["error"]["fields"]


def test_method_not_allowed_uses_envelope(client):
    response = client.delete("/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_oversized_body_is_rejected(client):
    response = client.post(
        "/api/v1/auth/register",
        content=b"x" * (65 * 1024),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_chunked_oversized_body_is_rejected(client):
    """NFR02/11: no Content-Length must not bypass actual-byte bounds."""
    response = client.post(
        "/api/v1/auth/register",
        content=iter([b"x" * (32 * 1024), b"x" * (33 * 1024)]),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_false_content_length_does_not_bypass_body_limit(client):
    response = client.post(
        "/api/v1/auth/register",
        content=b"x" * (65 * 1024),
        headers={"Content-Type": "application/json", "Content-Length": "1"},
    )
    assert response.status_code == 413


def test_internal_error_hides_details(app):
    @app.get("/__test__/boom")
    def boom():
        raise RuntimeError("secret-token-should-not-leak")

    probe = TestClient(app, raise_server_exceptions=False)
    response = probe.get("/__test__/boom")
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["fields"] == {}
    assert "secret-token" not in response.text
    assert "Traceback" not in response.text
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]


def test_openapi_exposes_only_contracted_phase1_paths(client):
    spec = client.get("/openapi.json").json()
    expected = {
        "/api/v1/auth/csrf",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/me",
        "/api/v1/auth/logout",
        "/api/v1/profiles/me",
        "/api/v1/admin/companies",
        "/api/v1/admin/companies/{company_id}",
        "/api/v1/admin/companies/{company_id}/verification",
        "/api/v1/admin/audit-events",
        "/health",
    }
    assert expected <= set(spec["paths"])
    assert "/api/v1/listings" in spec["paths"]
    assert "/api/v1/applications/{id}" in spec["paths"]
