"""FR11 / NFR01/02/03/11: bounded, private, read-only process telemetry."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.errors import request_id_var
from app.observability import APIMetrics, ROUTE_LIMIT, WINDOW_LIMIT
from tests.helpers import create_admin, login_admin, register_and_login


def test_metrics_clock_percentile_bounds_and_unknown_labels():
    clock = [0]
    metrics = APIMetrics({f"/api/v1/template{i}" for i in range(1000)}, clock=lambda: clock[0])
    assert metrics.snapshot()["latency"]["p95_ms"] is None
    for i in range(1000):
        started = metrics.start()
        clock[0] += i / 1000
        metrics.record(method="GET", route=f"/api/v1/template{i}", status=200, started=started)
    metrics.record(method="PRIVATE-METHOD", route="/raw/private-id?secret=query", status=404, started=metrics.start())
    snapshot = metrics.snapshot()
    assert snapshot["requests"] == {"total": 1001, "client_errors": 1, "server_errors": 0}
    assert snapshot["latency"]["sample_count"] == WINDOW_LIMIT
    assert snapshot["latency"]["p95_ms"] == 974
    assert len(snapshot["routes"]) == ROUTE_LIMIT
    assert sum(route["count"] for route in snapshot["routes"]) == 1001
    assert "PRIVATE" not in json.dumps(snapshot) and "secret" not in json.dumps(snapshot)


def test_metrics_concurrent_records_do_not_lose_counts():
    metrics = APIMetrics({"/api/v1/content"})
    def record(_):
        metrics.record(method="GET", route="/api/v1/content", status=503, started=metrics.start())
    with ThreadPoolExecutor(max_workers=8) as workers:
        list(workers.map(record, range(1000)))
    result = metrics.snapshot()
    assert result["requests"]["total"] == result["requests"]["server_errors"] == 1000
    assert result["latency"]["sample_count"] == WINDOW_LIMIT


def test_unknown_methods_and_paths_use_fixed_labels():
    metrics = APIMetrics()
    metrics.record(method="SECRET-METHOD", route="/raw/private-user?query=private", status=404, started=metrics.start())
    assert metrics.snapshot()["routes"] == [{"method": "OTHER", "route": "UNMATCHED", "count": 1}]


def test_operations_requires_current_admin_for_all_roles(app):
    assert TestClient(app).get("/api/v1/admin/operations").status_code == 401
    for role in ("student", "instructor", "company"):
        actor = TestClient(app)
        register_and_login(actor, email=f"operations-{role}@example.test", role=role,
                           company_name="Synthetic company" if role == "company" else None)
        assert actor.get("/api/v1/admin/operations").status_code == 403


def test_snapshot_excludes_itself_and_health_and_retains_only_route_templates(app, db):
    create_admin(app)
    actor = TestClient(app)
    login_admin(actor)
    actor.get("/health")
    marker = str(uuid4())
    actor.get(f"/api/v1/applications/{marker}?private-query-name=private-value")
    actor.get(f"/api/v1/no-route/{marker}?secret=hidden")
    before = app.state.operations.snapshot()["requests"]["total"]
    response = actor.get("/api/v1/admin/operations")
    assert response.status_code == 200
    result = response.json()
    assert result["requests"]["total"] == before
    assert app.state.operations.snapshot()["requests"]["total"] == before + 1
    assert response.headers["cache-control"] == "no-store"
    assert result["started_at"].endswith("+08:00") and result["generated_at"].endswith("+08:00")
    assert {"method": "GET", "route": "/api/v1/applications/{id}", "count": 1} in result["routes"]
    assert any(row["route"] == "UNMATCHED" for row in result["routes"])
    assert not any(word in response.text for word in (marker, "private-query-name", "private-value", "hidden", "password", "token", "endpoint"))
    assert result["storage"]["database_bytes"] > 0
    assert result["storage"]["application_count"] == 0
    assert result["storage"]["attachment_bytes"] == 0
    assert result["assistant"]["calls_used"] == 0


def test_expired_sessions_count_is_actual_storage_aggregate(app, db):
    create_admin(app)
    actor = TestClient(app)
    login_admin(actor)
    now = datetime.now(timezone.utc)
    db.execute(text("INSERT INTO sessions (id, token_hash, created_at, expires_at) VALUES (:id, :hash, :created, :expired)"),
               {"id": uuid4(), "hash": "f" * 64, "created": now - timedelta(days=2), "expired": now - timedelta(days=1)})
    db.commit()
    response = actor.get("/api/v1/admin/operations")
    assert response.status_code == 200
    assert response.json()["storage"]["expired_session_count"] == 1
    assert db.scalar(text("SELECT count(*) FROM sessions WHERE token_hash = :hash"), {"hash": "f" * 64}) == 1


def test_storage_counts_private_attachment_bytes_without_returning_file_data(app):
    from tests.test_marketplace import PDF, company, listing, student, upload
    recruiter = company(app)
    learner = student(app)
    opportunity = listing(recruiter)
    receipt = upload(learner, opportunity["id"])
    assert receipt.status_code == 201
    create_admin(app)
    admin = TestClient(app)
    login_admin(admin)
    response = admin.get("/api/v1/admin/operations")
    assert response.status_code == 200
    storage = response.json()["storage"]
    assert storage["application_count"] == 1
    assert storage["attachment_bytes"] == len(PDF)
    assert receipt.json()["id"] not in response.text and "PDF-1.4" not in response.text


def test_body_rejection_counts_and_failure_hides_details_with_security_headers(app):
    actor = TestClient(app, raise_server_exceptions=False)
    response = actor.post("/api/v1/auth/register", content=b"x" * 70000)
    assert response.status_code == 413
    assert app.state.operations.snapshot()["requests"] == {"total": 1, "client_errors": 1, "server_errors": 0}
    @app.get("/api/v1/__test_failure__")
    def failing():
        raise RuntimeError("private-error-password")
    response = actor.get("/api/v1/__test_failure__", headers={"X-Request-ID": "safe-request-id"})
    assert response.status_code == 500
    assert "private-error" not in response.text
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"] == "safe-request-id"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert request_id_var.get() == ""
    assert app.state.operations.snapshot()["requests"] == {"total": 2, "client_errors": 1, "server_errors": 1}


def test_failed_storage_does_not_substitute_zero_or_leak_exception(app, monkeypatch):
    from app.api.routes import admin
    create_admin(app)
    actor = TestClient(app, raise_server_exceptions=False)
    login_admin(actor)
    def fail(_):
        raise RuntimeError("database-password-private")
    monkeypatch.setattr(admin, "storage_snapshot", fail)
    response = actor.get("/api/v1/admin/operations")
    assert response.status_code == 500
    assert "storage" not in response.json() and "database-password" not in response.text
    assert app.state.operations.snapshot()["requests"]["server_errors"] == 1
