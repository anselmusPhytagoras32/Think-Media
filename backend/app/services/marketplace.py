"""FR04–07 marketplace authorization, serialization and atomic workflows."""

import re

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.errors import ApiError
from app.models import Application, CompanyProfile, Listing, StudentProfile, User
from app.repositories.marketplace import MarketplaceRepository
from app.repositories.profiles import ProfileRepository
from app.schemas.marketplace import ListingInput
from app.services.verification import load_verified_company
from app.time_utils import iso_manila


class MarketplaceService:
    def __init__(self, db, user):
        self.db = db
        self.user = user
        self.repo = MarketplaceRepository(db)

    def require_role(self, role):
        if self.user.role != role:
            raise ApiError(403, "FORBIDDEN", f"A {role} account is required.")

    def company(self):
        self.require_role("company")
        return ProfileRepository(self.db).get_company_by_user_id(self.user.id)

    def own_listing(self, id, lock=False, verified=False):
        company = (
            load_verified_company(self.db, self.user).company
            if verified
            else self.company()
        )
        row = self.repo.listing(id, lock)
        if row is None or row.company_id != company.id:
            raise ApiError(404, "NOT_FOUND", "Listing not found.")
        return row

    def listing_out(self, row):
        company = self.db.get(CompanyProfile, row.company_id)
        return dict(
            id=str(row.id),
            company_id=str(row.company_id),
            company_name=company.company_name,
            title=row.title,
            description=row.description,
            requirements=row.requirements,
            location=row.location,
            type=row.type,
            skills=row.skills,
            status=row.status,
            created_at=iso_manila(row.created_at),
            updated_at=iso_manila(row.updated_at),
            company_description=company.description,
            company_website=company.website,
        )

    def listing_detail(self, id):
        row = self.repo.listing(id)
        if row is None:
            raise ApiError(404, "NOT_FOUND", "Listing not found.")
        company = self.db.get(CompanyProfile, row.company_id)
        if row.status == "draft" or company.verification_status != "verified":
            if self.user.role != "company" or company.user_id != self.user.id:
                raise ApiError(404, "NOT_FOUND", "Listing not found.")
        return self.listing_out(row)

    def list_listings(self, limit, offset, own=False, **filters):
        query = select(Listing)
        if own:
            query = query.where(Listing.company_id == self.company().id)
        else:
            query = query.join(CompanyProfile).where(
                Listing.status == "published",
                CompanyProfile.verification_status == "verified",
            )
        for field, value in filters.items():
            if not value:
                continue
            if field == "q":
                query = query.where(
                    Listing.title.icontains(value, autoescape=True)
                    | Listing.description.icontains(value, autoescape=True)
                )
            elif field == "skill":
                query = query.where(Listing.skills.any(value))
            elif field == "location":
                query = query.where(Listing.location.icontains(value, autoescape=True))
            elif field == "type":
                query = query.where(Listing.type == value)
        rows, total = self.repo.page(
            query.order_by(Listing.created_at.desc(), Listing.id), limit, offset
        )
        return dict(
            items=[self.listing_out(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def create_listing(self, payload):
        company = load_verified_company(self.db, self.user).company
        row = Listing(company_id=company.id, **payload.model_dump())
        self.db.add(row)
        self.db.flush()
        self.repo.event(row, self.user, "created", None)
        self.db.commit()
        return self.listing_out(row)

    def edit_listing(self, id, payload):
        row = self.own_listing(id, lock=True, verified=True)
        if row.status == "closed":
            raise ApiError(409, "LISTING_CLOSED", "Closed listings cannot be edited.")
        patch = payload.model_dump(exclude_unset=True)
        if not patch or any(value is None for value in patch.values()):
            raise ApiError(422, "VALIDATION_ERROR", "Provide editable non-null fields.")
        # Validate merged state through the same complete contract as creation.
        try:
            valid = ListingInput.model_validate(
                {
                    **{key: getattr(row, key) for key in ListingInput.model_fields},
                    **patch,
                }
            )
        except ValidationError:
            raise ApiError(
                422, "VALIDATION_ERROR", "Listing fields are invalid."
            ) from None
        for key, value in valid.model_dump().items():
            setattr(row, key, value)
        self.repo.event(row, self.user, "edited", row.status)
        self.db.commit()
        return self.listing_out(row)

    def transition_listing(self, id, status):
        row = self.own_listing(id, lock=True, verified=True)
        expected = "draft" if status == "published" else "published"
        if row.status != expected:
            raise ApiError(
                409, "INVALID_TRANSITION", "Listing status cannot change this way."
            )
        old = row.status
        row.status = status
        self.repo.event(row, self.user, status, old)
        self.db.commit()
        return self.listing_out(row)

    def authorized_application(self, id, lock=False):
        row = self.repo.application(id, lock)
        if row is None:
            raise ApiError(404, "NOT_FOUND", "Application not found.")
        listing = self.repo.listing(row.listing_id)
        company = self.db.get(CompanyProfile, listing.company_id)
        if not (
            self.user.role == "student"
            and row.student_id == self.user.id
            or self.user.role == "company"
            and company.user_id == self.user.id
        ):
            raise ApiError(404, "NOT_FOUND", "Application not found.")
        return row

    def application_out(self, row):
        listing = self.repo.listing(row.listing_id)
        company = self.db.get(CompanyProfile, listing.company_id)
        student = self.db.get(User, row.student_id)
        result = dict(
            id=str(row.id),
            reference=row.reference,
            listing_id=str(row.listing_id),
            listing_title=listing.title,
            company_name=company.company_name,
            student_id=str(row.student_id),
            student_name=student.display_name,
            status=row.status,
            cover_letter=row.cover_letter,
            attachment_name=row.attachment_name,
            created_at=iso_manila(row.created_at),
            history=[
                dict(
                    actor_id=str(h.actor_id),
                    old_status=h.old_status,
                    new_status=h.new_status,
                    created_at=iso_manila(h.created_at),
                )
                for h in self.repo.history(row.id)
            ],
        )
        if self.user.role == "company":
            profile = self.db.get(StudentProfile, row.student_id)
            result["student_profile"] = {
                key: getattr(profile, key)
                for key in (
                    "institution",
                    "program",
                    "skills",
                    "interests",
                    "location",
                    "background",
                )
            }
            result["student_profile"]["display_name"] = student.display_name
        return result

    def submit(self, id, cover_letter, name, content_type, data):
        self.require_role("student")
        if len(cover_letter) > 5000:
            raise ApiError(
                422, "VALIDATION_ERROR", "Cover letter must be at most 5000 characters."
            )
        if len(data) > 5 * 1024 * 1024:
            raise ApiError(413, "PAYLOAD_TOO_LARGE", "PDF must be at most 5 MiB.")
        if (
            not name
            or not name.lower().endswith(".pdf")
            or content_type != "application/pdf"
            or not data.startswith(b"%PDF-")
            or b"%%EOF" not in data[-1024:]
        ):
            raise ApiError(422, "INVALID_UPLOAD", "Attach a valid PDF document.")
        row = self.repo.listing(id, lock=True)
        if row is None:
            raise ApiError(404, "NOT_FOUND", "Listing not found.")
        company = self.db.get(CompanyProfile, row.company_id)
        if row.status != "published" or company.verification_status != "verified":
            raise ApiError(
                409, "LISTING_CLOSED", "This listing is not accepting applications."
            )
        name = re.sub(r"[^A-Za-z0-9._ -]", "_", name.replace("\\", "/").split("/")[-1])[
            :196
        ]
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        application = Application(
            listing_id=id,
            student_id=self.user.id,
            cover_letter=cover_letter,
            attachment_name=name,
            attachment=data,
        )
        try:
            self.db.add(application)
            self.db.flush()
            self.repo.add_history(application, self.user, None)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            if (
                getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
                != "uq_application_student_listing"
            ):
                raise
            raise ApiError(
                409,
                "DUPLICATE_APPLICATION",
                "You have already applied to this listing.",
            ) from None
        return self.application_out(application)

    def list_applications(self, limit, offset, company=False, listing_id=None):
        query = select(Application)
        if company:
            owner = self.company()
            query = query.join(Listing).where(Listing.company_id == owner.id)
            if listing_id:
                self.own_listing(listing_id)
                query = query.where(Application.listing_id == listing_id)
        else:
            self.require_role("student")
            query = query.where(Application.student_id == self.user.id)
        rows, total = self.repo.page(
            query.order_by(Application.created_at.desc(), Application.id), limit, offset
        )
        return dict(
            items=[self.application_out(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def change_status(self, id, status):
        self.require_role("company")
        row = self.authorized_application(id, lock=True)
        allowed = {
            "submitted": {"under_review", "rejected"},
            "under_review": {"accepted", "rejected"},
        }
        if status not in allowed.get(row.status, set()):
            raise ApiError(
                409, "INVALID_TRANSITION", "Application status cannot change this way."
            )
        old = row.status
        row.status = status
        self.repo.add_history(row, self.user, old)
        self.db.commit()
        return self.application_out(row)
