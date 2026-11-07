"""FR08–09 bounded eligible candidate queries and observed interactions."""

from sqlalchemy import func, select

from app.models import CompanyProfile, Interaction, LearningContent, Listing

CANDIDATE_CAP = 500
RATING_CAP = 5000


class RecommendationRepository:
    def __init__(self, db):
        self.db = db

    def candidates(self, item_type):
        if item_type == "listing":
            query = (
                select(Listing)
                .join(CompanyProfile)
                .where(
                    Listing.status == "published",
                    CompanyProfile.verification_status == "verified",
                )
            )
            model = Listing
        else:
            query = select(LearningContent).where(LearningContent.status == "published")
            model = LearningContent
        return list(
            self.db.scalars(
                query.order_by(model.created_at.desc(), model.id).limit(CANDIDATE_CAP)
            )
        )

    def ratings(self):
        return list(
            self.db.scalars(
                select(Interaction)
                .where(Interaction.event_type == "rating")
                .order_by(Interaction.created_at.desc(), Interaction.id)
                .limit(RATING_CAP)
            )
        )

    def popularity(self, item_type, ids):
        field = (
            Interaction.listing_id if item_type == "listing" else Interaction.content_id
        )
        query = select(field, func.count()).where(field.in_(ids)).group_by(field)
        return {id: count for id, count in self.db.execute(query)} if ids else {}
