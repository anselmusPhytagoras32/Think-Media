"""require_verified_company foundation (no Phase 2 marketplace endpoints)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.api.deps import require_verified_company
from app.models import CompanyProfile
from app.services.verification import VerifiedCompany
from tests.helpers import (
    create_admin,
    login,
    login_admin,
    patch_json,
    register,
    register_and_login,
)

# Test-only surface: this route exists only inside the test, proving the guard
# without adding any listing/marketplace functionality to the application.
guard_router = APIRouter()


@guard_router.get("/__test__/verified-company-guard")
def verified_company_guard(
    context: VerifiedCompany = Depends(require_verified_company),
):
    return {"company_id": str(context.company.id), "user_id": str(context.user.id)}


def _app_with_guard(app):
    app.include_router(guard_router)
    return app


def test_pending_company_is_denied_by_guard(app):
    _app_with_guard(app)
    client = TestClient(app)
    register_and_login(
        client, email="pending@example.org", role="company", company_name="Pending Co"
    )
    response = client.get("/__test__/verified-company-guard")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "COMPANY_NOT_VERIFIED"

    # Client-supplied hints cannot bypass the stored state.
    spoof = client.get(
        "/__test__/verified-company-guard",
        headers={"X-Verification-Status": "verified", "X-Role": "company"},
    )
    assert spoof.status_code == 403


def test_unverified_rejected_and_wrong_role_are_denied(app, db):
    _app_with_guard(app)
    client = TestClient(app)
    register(client, email="rejected@example.org", role="company", company_name="Rejected Co")
    login(client, email="rejected@example.org")

    # Rejected via the real admin flow.
    create_admin(app)
    admin = TestClient(app)
    login_admin(admin)
    company_id = db.query(CompanyProfile.id).filter_by(company_name="Rejected Co").scalar()
    response = patch_json(
        admin,
        f"/api/v1/admin/companies/{company_id}/verification",
        {"status": "rejected", "reason": "Not eligible", "expected_version": 1},
    )
    assert response.status_code == 200

    denied = client.get("/__test__/verified-company-guard")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "COMPANY_NOT_VERIFIED"

    student = TestClient(app)
    register_and_login(student, email="student@example.org", role="student")
    response = student.get("/__test__/verified-company-guard")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "COMPANY_NOT_VERIFIED"

    assert TestClient(app).get("/__test__/verified-company-guard").status_code == 401


def test_verified_company_passes_and_guard_reads_current_state(app, db):
    _app_with_guard(app)
    company_client = TestClient(app)
    register_and_login(
        company_client, email="verified@example.org", role="company", company_name="Verified Co"
    )

    create_admin(app)
    admin = TestClient(app)
    login_admin(admin)
    company_id = db.query(CompanyProfile.id).filter_by(company_name="Verified Co").scalar()

    assert company_client.get("/__test__/verified-company-guard").status_code == 403
    response = patch_json(
        admin,
        f"/api/v1/admin/companies/{company_id}/verification",
        {"status": "verified", "reason": "Documents checked", "expected_version": 1},
    )
    assert response.status_code == 200

    allowed = company_client.get("/__test__/verified-company-guard")
    assert allowed.status_code == 200
    assert allowed.json()["company_id"] == str(company_id)

    # If the stored status changes, the very next request is denied. There is
    # no cached "verified" flag on the session.
    row = db.query(CompanyProfile).filter_by(id=company_id).one()
    row.verification_status = "rejected"
    db.commit()

    denied = company_client.get("/__test__/verified-company-guard")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "COMPANY_NOT_VERIFIED"
