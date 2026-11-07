"""Administrator verification queue, audit trail and concurrency (FR11, NFR04)."""

from __future__ import annotations

import threading
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

from app.errors import ApiError
from app.models import AuditEvent, CompanyProfile, User
from app.repositories.audit import AuditRepository
from app.services.administration import AdministrationService
from tests.helpers import (
    create_admin,
    get_company_id,
    login_admin,
    patch_json,
    register,
    register_and_login,
)


def _register_company(client: TestClient, email: str, name: str):
    response = register(client, email=email, role="company", company_name=name)
    assert response.status_code == 201, response.text
    return response


def _verify(client: TestClient, company_id, *, version=1, status="verified", reason="Reviewed"):
    return patch_json(
        client,
        f"/api/v1/admin/companies/{company_id}/verification",
        {"status": status, "reason": reason, "expected_version": version},
    )


def test_unauthenticated_and_non_admin_roles_are_denied(client, app):
    _register_company(client, "company@example.org", "Acme")
    create_admin(app)

    assert client.get("/api/v1/admin/companies").status_code == 401

    for role in ("student", "instructor", "company"):
        actor = TestClient(app)
        register_and_login(
            actor,
            email=f"{role}-actor@example.org",
            role=role,
            company_name="Actor Co" if role == "company" else None,
        )
        assert actor.get("/api/v1/admin/companies").status_code == 403
        company_id = get_company_id(app, "company@example.org")
        response = _verify(actor, company_id)
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"

    with app.state.session_factory() as session:
        company = session.scalar(select(CompanyProfile))
        assert company.verification_status == "pending"
        assert company.verification_version == 1


def test_service_rechecks_current_actor_role(client, app, db):
    _register_company(client, "direct@example.org", "Direct Co")
    register_and_login(client, email="student-direct@example.org", role="student")
    company_id = get_company_id(app, "direct@example.org")
    student_id = db.scalar(select(User.id).where(User.email == "student-direct@example.org"))

    with app.state.session_factory() as session:
        actor = session.get(User, student_id)
        with pytest.raises(ApiError) as exc:
            AdministrationService(session).change_verification(
                company_id=company_id,
                new_status="verified",
                reason="Direct call",
                expected_version=1,
                actor=actor,
            )
    assert exc.value.status_code == 403
    assert exc.value.code == "FORBIDDEN"

    with app.state.session_factory() as session:
        company = session.get(CompanyProfile, company_id)
        assert company.verification_status == "pending"
        assert company.verification_version == 1


def test_admin_queue_defaults_to_pending_and_paginates(client, app):
    _register_company(client, "one@example.org", "One")
    _register_company(client, "two@example.org", "Two")
    _register_company(client, "three@example.org", "Three")
    create_admin(app)
    login_admin(client)

    response = client.get("/api/v1/admin/companies")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert body["items"] == sorted(body["items"], key=lambda item: (item["created_at"], item["id"]))
    assert {item["company_name"] for item in body["items"]} == {"One", "Two", "Three"}

    page = client.get("/api/v1/admin/companies?limit=2&offset=1")
    assert page.status_code == 200
    assert page.json()["total"] == 3
    assert len(page.json()["items"]) == 2

    assert client.get("/api/v1/admin/companies?limit=0").status_code == 422
    assert client.get("/api/v1/admin/companies?limit=101").status_code == 422
    assert client.get("/api/v1/admin/companies?offset=-1").status_code == 422
    assert client.get("/api/v1/admin/companies?status=bogus").status_code == 422


def test_admin_queue_filters_by_status_and_detail(client, app):
    _register_company(client, "filter@example.org", "Filter Co")
    create_admin(app)
    login_admin(client)
    company_id = get_company_id(app, "filter@example.org")

    detail = client.get(f"/api/v1/admin/companies/{company_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == str(company_id)
    assert detail.json()["verification_status"] == "pending"

    assert _verify(client, company_id).status_code == 200

    pending = client.get("/api/v1/admin/companies?status=pending").json()
    verified = client.get("/api/v1/admin/companies?status=verified").json()
    rejected = client.get("/api/v1/admin/companies?status=rejected").json()
    assert pending["total"] == 0
    assert verified["total"] == 1
    assert rejected["total"] == 0
    assert verified["items"][0]["id"] == str(company_id)

    missing = client.get(f"/api/v1/admin/companies/{uuid.uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"
    assert client.get("/api/v1/admin/companies/not-a-uuid").status_code == 422


def test_verification_is_audited_with_actor_and_time(client, app):
    _register_company(client, "audit@example.org", "Audit Co")
    admin_id = create_admin(app)
    login_admin(client)
    company_id = get_company_id(app, "audit@example.org")

    response = _verify(client, company_id, reason="  Business permit checked.  ")
    assert response.status_code == 200, response.text
    body = response.json()
    company = body["company"]
    event = body["audit_event"]
    assert company["verification_status"] == "verified"
    assert company["verification_version"] == 2
    assert event["actor_id"] == str(admin_id)
    assert event["action"] == "company.verification_changed"
    assert event["target_id"] == str(company_id)
    assert event["old_status"] == "pending"
    assert event["new_status"] == "verified"
    assert event["reason"] == "Business permit checked."
    assert event["created_at"].endswith("+08:00")

    # A fresh administrator session still sees the durable audit record.
    second = TestClient(app)
    login_admin(second)
    audit = second.get("/api/v1/admin/audit-events")
    assert audit.status_code == 200
    assert audit.json()["total"] == 1
    assert audit.json()["items"][0]["id"] == event["id"]


def test_rejection_and_reason_validation(client, app):
    _register_company(client, "reject@example.org", "Reject Co")
    create_admin(app)
    login_admin(client)
    company_id = get_company_id(app, "reject@example.org")

    assert _verify(client, company_id, reason="").status_code == 422
    assert _verify(client, company_id, reason="   ").status_code == 422
    assert _verify(client, company_id, reason="x" * 1001).status_code == 422
    assert _verify(client, company_id, version=0).status_code == 422
    assert _verify(client, company_id, status="pending").status_code == 422
    extra = patch_json(
        client,
        f"/api/v1/admin/companies/{company_id}/verification",
        {
            "status": "verified",
            "reason": "ok",
            "expected_version": 1,
            "actor_id": str(uuid.uuid4()),
        },
    )
    assert extra.status_code == 422

    response = _verify(client, company_id, status="rejected", reason="Incomplete documents")
    assert response.status_code == 200
    assert response.json()["company"]["verification_status"] == "rejected"
    assert response.json()["company"]["verification_version"] == 2
    assert response.json()["audit_event"]["new_status"] == "rejected"


def test_stale_and_repeated_verification_return_conflict(client, app):
    _register_company(client, "conflict@example.org", "Conflict Co")
    create_admin(app)
    login_admin(client)
    company_id = get_company_id(app, "conflict@example.org")

    stale = _verify(client, company_id, version=2)
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "VERIFICATION_CONFLICT"

    assert _verify(client, company_id, version=1).status_code == 200

    repeated = _verify(client, company_id, version=2, status="rejected")
    assert repeated.status_code == 409
    assert repeated.json()["error"]["code"] == "VERIFICATION_CONFLICT"

    with app.state.session_factory() as session:
        company = session.get(CompanyProfile, company_id)
        assert company.verification_status == "verified"
        assert company.verification_version == 2
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1


def test_audit_insert_failure_rolls_back_status_and_version(
    client, app, db, monkeypatch
):
    _register_company(client, "rollback@example.org", "Rollback Co")
    admin_id = create_admin(app)
    company_id = get_company_id(app, "rollback@example.org")

    with app.state.session_factory() as session:
        actor = session.get(User, admin_id)
        monkeypatch.setattr(
            AuditRepository,
            "create",
            lambda self, **kwargs: (_ for _ in ()).throw(RuntimeError("audit down")),
        )
        with pytest.raises(RuntimeError):
            AdministrationService(session).change_verification(
                company_id=company_id,
                new_status="verified",
                reason="Should roll back",
                expected_version=1,
                actor=actor,
            )

    with app.state.session_factory() as session:
        company = session.get(CompanyProfile, company_id)
        assert company.verification_status == "pending"
        assert company.verification_version == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0


def test_concurrent_decisions_allow_exactly_one_winner(client, app):
    _register_company(client, "race@example.org", "Race Co")
    admin_id = create_admin(app)
    company_id = get_company_id(app, "race@example.org")

    barrier = threading.Barrier(2)
    results: list[tuple[str, object]] = []
    lock = threading.Lock()

    def worker() -> None:
        session = app.state.session_factory()
        try:
            actor = session.get(User, admin_id)
            barrier.wait(timeout=5)
            try:
                response = AdministrationService(session).change_verification(
                    company_id=company_id,
                    new_status="verified",
                    reason="Concurrent review",
                    expected_version=1,
                    actor=actor,
                )
                with lock:
                    results.append(("ok", response.company.verification_version))
            except ApiError as exc:
                with lock:
                    results.append(("error", exc.status_code))
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert len(results) == 2
    assert sorted(result[0] for result in results) == ["error", "ok"]
    assert [result[1] for result in results if result[0] == "error"] == [409]

    with app.state.session_factory() as session:
        company = session.get(CompanyProfile, company_id)
        assert company.verification_status == "verified"
        assert company.verification_version == 2
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1


def test_admin_role_is_read_from_current_database_state(client, app, db):
    _register_company(client, "demote@example.org", "Demote Co")
    admin_id = create_admin(app)
    login_admin(client)
    assert client.get("/api/v1/admin/companies").status_code == 200

    # Role changes happen outside the HTTP API (the API exposes no elevation).
    # The next request must observe the current database role, not a cached one.
    db.execute(text("UPDATE users SET role = 'student' WHERE id = :id"), {"id": admin_id})
    db.commit()

    response = client.get("/api/v1/admin/companies")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_audit_list_is_newest_first(client, app):
    _register_company(client, "first@example.org", "First")
    _register_company(client, "second@example.org", "Second")
    create_admin(app)
    login_admin(client)
    first_id = get_company_id(app, "first@example.org")
    second_id = get_company_id(app, "second@example.org")

    assert _verify(client, first_id, reason="first").status_code == 200
    assert _verify(client, second_id, reason="second").status_code == 200

    response = client.get("/api/v1/admin/audit-events?limit=1&offset=0")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["items"][0]["target_id"] == str(second_id)

    second_page = client.get("/api/v1/admin/audit-events?limit=1&offset=1")
    assert second_page.json()["items"][0]["target_id"] == str(first_id)
