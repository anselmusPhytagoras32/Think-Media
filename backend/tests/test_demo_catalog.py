"""FR04/06/08/11: fictional opportunity seeding preserves owned data."""

import pytest
from sqlalchemy import func, select

from app.models import AuditEvent, CompanyProfile, Listing, User
from app.security.passwords import verify_password
from tests.helpers import create_admin


def test_catalog_is_idempotent_preserves_edits_and_records_synthetic_verification(app, db):
    from ops.demo_catalog import seed_catalog, catalog_password
    admin_id = create_admin(app)
    admin = db.get(User, admin_id)
    secret = catalog_password("synthetic-company-password")
    first = seed_catalog(db, admin, secret)
    db.commit()
    assert first == {"opportunities_created": 7, "company_created": True}
    user = db.scalar(select(User).where(User.email == "presentation-catalog-company@example.test"))
    assert user.role == "company" and verify_password(secret, user.password_hash)
    company = db.scalar(select(CompanyProfile).where(CompanyProfile.user_id == user.id))
    assert company.verification_status == "verified"
    assert "fictional" in company.company_name.lower()
    assert db.scalar(select(func.count()).select_from(AuditEvent)) == 1
    assert len(list(db.scalars(select(Listing).where(Listing.status == "published")))) == 6
    changed = db.scalar(select(Listing).where(Listing.status == "draft"))
    changed.title = "My edited demonstration draft"
    db.commit()
    assert seed_catalog(db, admin, secret) == {"opportunities_created": 0, "company_created": False}
    db.commit()
    db.refresh(changed)
    assert changed.title == "My edited demonstration draft"
    assert db.scalar(select(func.count()).select_from(Listing)) == 7


def test_catalog_rejects_identity_collision_and_nonadmin_without_changes(app, db):
    from ops.demo_catalog import seed_catalog
    from tests.test_learning import learner
    learner(app, email="presentation-catalog-company@example.test")
    admin = db.get(User, create_admin(app))
    with pytest.raises(ValueError):
        seed_catalog(db, admin, "synthetic-catalog-password")
    assert db.scalar(select(func.count()).select_from(Listing)) == 0
