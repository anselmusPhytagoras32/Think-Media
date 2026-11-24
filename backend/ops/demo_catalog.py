"""FR04/06/08/11: additive, fictional opportunity catalog for the approved demo."""

from hashlib import sha256
import hmac
from uuid import uuid5

from sqlalchemy import select, text

from app.models import AuditEvent, CompanyProfile, Listing, MarketplaceEvent, User
from app.security.passwords import hash_password, verify_password

CATALOG_EMAIL = "presentation-catalog-company@example.test"


def catalog_password(company_password):
    """A distinct demo-only credential derived from the private runtime secret."""
    return hmac.new(company_password.encode(), b"thinkmedia:catalog-company:v1", sha256).hexdigest()


EXAMPLES = (
    ("react-ojt", "React web development OJT", "ojt", "Legazpi City", ["React", "JavaScript", "CSS"], "Build accessible search controls and test a small web interface."),
    ("python-ojt", "Python and SQL data preparation OJT", "ojt", "Remote", ["Python", "SQL"], "Clean fictional records, write parameterized queries, and explain the results."),
    ("design-ojt", "UI design and usability OJT", "ojt", "Legazpi City", ["Figma", "Communication"], "Prepare a small interface prototype, document user tasks, and review accessibility."),
    ("support-ojt", "IT support and documentation OJT", "ojt", "Naga City", ["Troubleshooting", "Communication"], "Practice documenting support requests and communicating progress using fictional exercises."),
    ("frontend-job", "Junior frontend developer", "job", "Remote", ["React", "TypeScript"], "Maintain responsive interface components and review changes with the development team."),
    ("data-job", "Junior data assistant", "job", "Legazpi City", ["SQL", "Spreadsheets"], "Prepare clear reports from fictional datasets and check data quality."),
    ("demo-draft", "Draft: software development OJT walkthrough", "ojt", "Legazpi City", ["React", "Python", "SQL"], "Editable example for demonstrating the company listing editor before publication."),
)


def seed_catalog(db, administrator, password):
    if administrator.role != "administrator" or not password or len(password) < 16:
        raise ValueError("Explicit demo administrator and private credential required.")
    db.execute(text("SELECT pg_advisory_xact_lock(2026112401)"))
    user_id = uuid5(administrator.id, "thinkmedia:demo-catalog-company:v1")
    user = db.scalar(select(User).where(User.email == CATALOG_EMAIL))
    created = user is None
    if user is not None:
        if user.id != user_id or user.role != "company" or not verify_password(password, user.password_hash):
            raise ValueError("Catalog identity is not owned by this initializer; no account will be reset.")
        company = db.scalar(select(CompanyProfile).where(CompanyProfile.user_id == user.id))
        if company is None:
            raise ValueError("Catalog company profile is missing.")
    else:
        if db.get(User, user_id) is not None:
            raise ValueError("Catalog identity collides with an existing account.")
        user = User(id=user_id, email=CATALOG_EMAIL, password_hash=hash_password(password),
                    display_name="Practice Studio (fictional company)", role="company")
        db.add(user)
        db.flush()
        company = CompanyProfile(id=uuid5(user_id, "company"), user_id=user_id,
                                 company_name="ThinkMedia Practice Studio (fictional)",
                                 description="Fictional demonstration organization. No real vacancies, recruitment, or partnership.",
                                 location="Legazpi City", verification_status="verified", verification_version=2)
        db.add(company)
        db.flush()
        db.add(AuditEvent(actor_id=administrator.id, action="company_verification_changed", target_id=company.id,
                          old_status="pending", new_status="verified",
                          reason="Approved fictional demo fixture only; not verification of a real organization."))
    count = 0
    for slug, title, kind, location, skills, description in EXAMPLES:
        id = uuid5(user_id, "opportunity:" + slug)
        if db.get(Listing, id) is not None:
            continue
        # Respect any subsequent administrator decision about the fixture company.
        if company.verification_status != "verified":
            continue
        item = Listing(id=id, company_id=company.id, title="[Fictional demo] " + title,
                       type=kind, location=location, skills=skills,
                       description="FICTIONAL DEMONSTRATION ONLY. " + description + " This is not a real vacancy.",
                       requirements="Use fictional details and the provided sample PDF only. Explain one relevant class project and your own contribution. No real personal documents are needed.",
                       status="draft" if slug == "demo-draft" else "published")
        db.add(item)
        db.flush()
        db.add(MarketplaceEvent(listing_id=item.id, actor_id=user.id, action="created", old_status=None, new_status=item.status))
        count += 1
    db.flush()
    return {"opportunities_created": count, "company_created": created}
