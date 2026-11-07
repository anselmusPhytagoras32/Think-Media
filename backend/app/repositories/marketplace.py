"""Parameterized marketplace data access (FR04–07)."""

from sqlalchemy import func, select

from app.models import (
    Application,
    ApplicationStatusHistory,
    Listing,
    MarketplaceEvent,
)


class MarketplaceRepository:
    def __init__(self, db):
        self.db = db

    def listing(self, id, lock=False):
        query = select(Listing).where(Listing.id == id)
        return self.db.scalar(query.with_for_update() if lock else query)

    def application(self, id, lock=False):
        query = select(Application).where(Application.id == id)
        return self.db.scalar(query.with_for_update() if lock else query)

    def page(self, query, limit, offset):
        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        return list(self.db.scalars(query.limit(limit).offset(offset))), total

    def history(self, id):
        return list(
            self.db.scalars(
                select(ApplicationStatusHistory)
                .where(ApplicationStatusHistory.application_id == id)
                .order_by(
                    ApplicationStatusHistory.created_at, ApplicationStatusHistory.id
                )
            )
        )

    def add_history(self, row, actor, old):
        self.db.add(
            ApplicationStatusHistory(
                application_id=row.id,
                actor_id=actor.id,
                old_status=old,
                new_status=row.status,
            )
        )
        self.db.flush()

    def event(self, row, actor, action, old):
        self.db.add(
            MarketplaceEvent(
                listing_id=row.id,
                actor_id=actor.id,
                action=action,
                old_status=old,
                new_status=row.status,
            )
        )
        self.db.flush()
