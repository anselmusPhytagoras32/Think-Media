"""Seed synthetic local consumer data through existing domain services.

FR01–04/06/08/10–11; NFR02–03/06. No research feedback is fabricated.
Run from backend with DATABASE_URL and LOCAL_DEMO_STUDENT_PASSWORD set.
Only a new, empty local database may bootstrap its separate administrator.
Existing accounts, profiles, listing states and resources are never reset.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.engine import make_url

from app.config import Settings
from app.db import build_engine, build_session_factory
from app.models import LearningContent, Listing, User
from app.repositories import ProfileRepository, UserRepository
from app.schemas import ProfileUpdateRequest, RegisterRequest
from app.schemas.learning import ContentInput, ContentPatch, QuestionInput
from app.schemas.marketplace import ListingInput
from app.services.accounts import AccountService
from app.services.administration import AdministrationService
from app.services.learning import LearningService
from app.services.marketplace import MarketplaceService
from app.services.profiles import ProfileService


LISTINGS = (
    ("Demo: Frontend OJT practice", ["React", "JavaScript", "CSS"],
     "Practice accessible React components, responsive layouts and code review."),
    ("Demo: Python and data OJT practice", ["Python", "SQL", "Data analysis"],
     "Practice Python scripts, parameterized SQL and documenting data quality."),
    ("Demo: UX and product OJT practice", ["UX research", "Figma", "Communication"],
     "Practice clear task flows, usability observations and interface writing."),
)
RESOURCES = (
    ("Demo guide: Prepare your OJT application", ["OJT", "Resume", "Career"],
     "Build a clear resume and check an opportunity before applying.",
     "List your program, relevant skills and a few projects in a concise resume. "
     "Explain what you contributed and link only material you can share. Read the "
     "listing requirements and location before applying. Confirm your school's "
     "OJT requirements with your coordinator. In ThinkMedia, attach a PDF up to "
     "5 MiB, review your cover letter and submit once per listing. Track the "
     "application status in My applications. Never upload identity documents or "
     "sensitive personal information unless an authorized process requires them."),
    ("Demo guide: Build a React portfolio", ["React", "JavaScript", "Portfolio"],
     "Choose a small project that shows how you solve a real interface task.",
     "Start with one useful task, such as filtering a list of learning resources. "
     "Build readable React components with labeled inputs and keyboard focus. "
     "Show loading, empty and error states. Check the layout at 360 pixels and "
     "desktop widths. Explain the problem, your decisions and what you tested "
     "in a README. Remove private data and credentials before sharing code. "
     "Describe your own contribution honestly; a portfolio is evidence of "
     "practice, not a guarantee of placement."),
    ("Demo guide: Practice Python and SQL safely", ["Python", "SQL", "Data analysis"],
     "Use a synthetic dataset to practice cleaning and querying data.",
     "Create a small synthetic CSV of course topics and study time. Validate "
     "missing values and data types with Python before calculating summaries. "
     "Use parameterized SQL for database filters and keep database passwords "
     "outside source control. Split real evaluation data before fitting models "
     "and document the configuration and limitations. Label practice data as "
     "synthetic. Never report synthetic records, quiz activity or local demo "
     "ratings as pilot participants or research findings."),
)


def seed(state_dir: Path, bootstrap_admin: bool) -> dict:
    settings = Settings()
    url = make_url(settings.database_url)
    if not url.drivername.startswith("postgresql") or url.host not in {
        "localhost", "127.0.0.1", "::1"
    } or settings.app_env != "local":
        raise ValueError("Seed requires APP_ENV=local and loopback PostgreSQL.")
    if not url.database or not url.database.endswith("_local"):
        raise ValueError("Use a dedicated local database ending in _local.")
    student_password = os.environ["LOCAL_DEMO_STUDENT_PASSWORD"]
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    manifest_path = state_dir / "demo-manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    database_key = str(url.set(password=None))
    if manifest and manifest.get("database") != database_key:
        raise ValueError("Manifest belongs to a different local database.")
    manifest["database"] = database_key

    def remember(key, user):
        manifest[key] = str(user.id)
        descriptor = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w") as output:
            json.dump(manifest, output, indent=2)

    engine = build_engine(settings)
    try:
        with build_session_factory(engine)() as db:
            accounts = AccountService(db)
            users = UserRepository(db)
            empty_database = db.scalar(select(func.count()).select_from(User)) == 0
            admin = users.get_by_email("admin@example.test")
            if admin is None:
                if not (empty_database and bootstrap_admin):
                    raise ValueError("No demo administrator; bootstrap only a new empty DB.")
                admin = accounts.create_administrator(
                    email="admin@example.test",
                    password=os.environ["LOCAL_DEMO_ADMIN_PASSWORD"],
                    display_name="Local Demo Administrator",
                )
                remember("administrator", admin)
            elif admin.role != "administrator" or manifest.get("administrator") != str(admin.id):
                raise ValueError("Existing administrator is not owned by this demo manifest.")

            def registered(key, email, role, name, password, **extra):
                existing = users.get_by_email(email)
                if existing is not None:
                    if existing.role != role or manifest.get(key) != str(existing.id):
                        raise ValueError(f"Existing {key} is not owned by this demo manifest.")
                    return existing, False
                accounts.register(RegisterRequest(
                    email=email, password=password, display_name=name, role=role, **extra
                ))
                existing = users.get_by_email(email)
                remember(key, existing)
                return existing, True

            student, created = registered(
                "student", "student@example.test", "student", "Alex Student", student_password
            )
            # Verify the requested sign-in works without changing an existing password.
            accounts.authenticate(student.email, student_password)
            if created:
                ProfileService(db).update_me(student, ProfileUpdateRequest(
                    institution="Demo Campus (synthetic)",
                    program="BS Information Technology", location="Metro Manila",
                    skills=["React", "JavaScript", "Python", "SQL"],
                    interests=["OJT", "Web development", "Data analysis"],
                    background="Synthetic local demonstration profile; not a real student.",
                ))
            company, created = registered(
                "company", "demo-company@example.test", "company", "Demo Company Coordinator",
                secrets.token_urlsafe(32), company_name="Demo Practice Studio (synthetic)"
            )
            if created:
                ProfileService(db).update_me(company, ProfileUpdateRequest(
                    description="Synthetic local demonstration company. No real vacancies or partnership.",
                    location="Metro Manila", contact_email="demo-company@example.test"
                ))
            profile = ProfileRepository(db).get_company_by_user_id(company.id)
            if profile.verification_status == "pending":
                AdministrationService(db).change_verification(
                    company_id=profile.id, new_status="verified",
                    reason="Local synthetic demonstration only; no real company verification or partnership.",
                    expected_version=profile.verification_version, actor=admin,
                )
            marketplace = MarketplaceService(db, company)
            for title, skills, description in LISTINGS:
                existing = db.scalar(select(Listing).where(
                    Listing.company_id == profile.id, Listing.title == title
                ))
                if existing is None:
                    row = marketplace.create_listing(ListingInput(
                        title=title, skills=skills, type="ojt", location="Metro Manila (demo)",
                        description="Local synthetic demonstration, not a real vacancy. " + description,
                        requirements="Practice listing only. Use synthetic documents for local testing. "
                        "Basic familiarity with " + ", ".join(skills) + ".",
                    ))
                    marketplace.transition_listing(UUID(row["id"]), "published")
            learning = LearningService(db, admin)
            for title, tags, summary, body in RESOURCES:
                existing = db.scalar(select(LearningContent).where(
                    LearningContent.author_id == admin.id, LearningContent.title == title
                ))
                if existing is None:
                    resource = learning.create(ContentInput(
                        title=title, tags=tags, summary=summary,
                        body="Local demonstration guidance, not institutional policy. " + body,
                        questions=[QuestionInput(
                            question="How should local demonstration data be described?",
                            options=["Clearly synthetic; not research evidence", "As real pilot results"],
                            correct_index=0,
                        )],
                    ))
                    learning.edit(UUID(resource["id"]), ContentPatch(status="published"))
            return {
                "student_email": student.email, "role": student.role,
                "published_listings": MarketplaceService(db, student).list_listings(20, 0)["total"],
                "published_resources": LearningService(db, student).feed(20, 0)["total"],
                "synthetic_only": True,
            }
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path,
                        default=Path.home() / ".local/share/thinkmedia")
    parser.add_argument("--bootstrap-admin", action="store_true")
    args = parser.parse_args()
    print(json.dumps(seed(args.state_dir, args.bootstrap_admin), indent=2))


if __name__ == "__main__":
    main()
