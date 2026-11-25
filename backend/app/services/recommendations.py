"""FR08-09 explainable eligible matching and observed-only optional hybrid.

Weights are implementation configuration, never claimed as evaluated quality.
"""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.recommender import HybridScorer, MODEL_VERSION, MIN_RATINGS, MIN_USERS, MIN_OVERLAP, content_scores, fit_text, listing_text, profile_text
from app.errors import ApiError
from app.models import (
    CompanyProfile,
    Interaction,
    LearningContent,
    Listing,
    StudentProfile,
)
from app.repositories.recommendations import (
    CANDIDATE_CAP,
    RATING_CAP,
    RecommendationRepository,
)
from app.services.learning import LearningService
from app.services.marketplace import MarketplaceService
from app.time_utils import iso_manila, utcnow


class RecommendationService:
    def __init__(self, db, user, alpha):
        self.db = db
        self.user = user
        self.alpha = alpha
        self.repo = RecommendationRepository(db)

    def recommend(self, limit):
        if self.user.role != "student":
            raise ApiError(403, "FORBIDDEN", "A student account is required.")
        profile = profile_text(self.db.get(StudentProfile, self.user.id))
        pools = {kind: self.repo.candidates(kind) for kind in ("listing", "content")}
        companies = {row.id: row for row in self.db.scalars(select(CompanyProfile).where(
            CompanyProfile.id.in_({row.company_id for row in pools["listing"]}))) } if pools["listing"] else {}
        documents = {kind: [listing_text(row, companies.get(row.company_id)) if kind == "listing" else " ".join([row.title, row.body, *row.tags])
                            for row in rows] for kind, rows in pools.items()}
        # Fit once on the current eligible public catalog and own profile.
        # The offline evaluator uses the same functions with training text only.
        vectorizer = fit_text([profile, *documents["listing"], *documents["content"]])
        similarities = {kind: content_scores(vectorizer, [profile] * len(values), values) for kind, values in documents.items()}
        has_profile = any(score > 0 for scores in similarities.values() for score in scores)
        eligible = {f"{kind}:{row.id}" for kind, rows in pools.items() for row in rows}
        observed = []
        for event in self.repo.ratings():
            key = f"listing:{event.listing_id}" if event.listing_id else f"content:{event.content_id}"
            if key in eligible:
                observed.append(dict(user_id=str(event.user_id), item_id=key, rating=event.rating))
        model = HybridScorer(observed)
        results = {}
        any_hybrid = False
        for kind, rows in pools.items():
            projections = model.predict(str(self.user.id), [f"{kind}:{row.id}" for row in rows], similarities[kind], alpha=self.alpha)
            popular = self.repo.popularity(kind, [row.id for row in rows]) if not has_profile else {}
            max_pop = max(popular.values(), default=0)
            ranked = []
            for index, (row, component) in enumerate(zip(rows, projections)):
                if component["strategy"] == "hybrid":
                    any_hybrid = True
                    reason = "Based on your profile and optional ratings from users with shared observed ratings."
                elif has_profile:
                    reason = ("Based on shared terms in your profile and this resource." if component["content_score"] > 0
                              else "No shared profile terms; ordered with recent resources first.")
                else:
                    component["strategy"] = "general"
                    component["score"] = popular.get(row.id, 0) / max_pop if max_pop else 1 - index / max(1, len(rows))
                    reason = ("Based on actual popularity from recorded views and optional ratings." if max_pop and popular.get(row.id, 0)
                              else "Recent eligible resource; no profile or activity match is available yet.")
                item = (MarketplaceService(self.db, self.user).listing_out(row) if kind == "listing"
                        else LearningService(self.db, self.user).out(row))
                entry = dict(item=item, reason=reason, **component)
                for field in ("score", "content_score", "collaborative_score"):
                    if entry[field] is not None:
                        entry[field] = round(entry[field], 6)
                ranked.append((index, entry))
            ranked.sort(key=lambda pair: (-pair[1]["score"], pair[0]))
            results["listings" if kind == "listing" else "content"] = [value for _, value in ranked[:limit]]
        return dict(
            **results, mode="hybrid" if any_hybrid else "profile" if has_profile else "general",
            alpha=self.alpha if any_hybrid else 1.0,
            method=dict(version=MODEL_VERSION, configured_alpha=self.alpha, weight_status="provisional_not_validated",
                        explicit_ratings=model.rating_count, distinct_raters=len(model.histories),
                        minimum_ratings=MIN_RATINGS, minimum_raters=MIN_USERS, minimum_shared_items=MIN_OVERLAP),
            limitations=[
                f"Candidate pool is capped at {CANDIDATE_CAP} recent eligible items per type; collaborative input at {RATING_CAP} latest explicit ratings.",
                "Suggestions support exploration and are not placement or hiring decisions.",
                "The configured blend is provisional; genuine held-out evaluation is required before claiming accuracy or an optimal weight.",
                "Items without eligible neighbors use profile-only matching (alpha 1); missing ratings are never invented.",
            ],
        )


class InteractionService:
    def __init__(self, db, user, throttle):
        self.db = db
        self.user = user
        self.throttle = throttle

    def record(self, payload):
        if self.user.role not in {"student", "instructor"}:
            raise ApiError(
                403, "FORBIDDEN", "A student or instructor account is required."
            )
        retry = self.throttle.retry_after(str(self.user.id))
        if retry is not None:
            raise ApiError(
                429,
                "RATE_LIMITED",
                "Too many feedback requests. Try again later.",
                headers={"Retry-After": str(retry)},
            )
        field = "listing_id" if payload.item_type == "listing" else "content_id"
        model = Listing if field == "listing_id" else LearningContent
        row = self.db.scalar(
            select(model).where(model.id == payload.item_id).with_for_update()
        )
        if row is None or row.status != "published":
            raise ApiError(404, "NOT_FOUND", "Eligible resource not found.")
        if (
            field == "listing_id"
            and self.db.get(CompanyProfile, row.company_id).verification_status
            != "verified"
        ):
            raise ApiError(404, "NOT_FOUND", "Eligible resource not found.")
        self.throttle.record_attempt(str(self.user.id))
        values = dict(
            user_id=self.user.id,
            event_type=payload.event_type,
            rating=payload.rating,
            created_at=utcnow(),
            **{field: payload.item_id},
        )
        statement = insert(Interaction).values(**values)
        if payload.event_type == "rating":
            statement = statement.on_conflict_do_update(
                index_elements=["user_id", field],
                index_where=Interaction.event_type == "rating",
                set_=dict(rating=payload.rating, created_at=values["created_at"]),
            )
        event = self.db.scalar(statement.returning(Interaction))
        self.db.commit()
        return dict(
            id=str(event.id),
            item_type=payload.item_type,
            item_id=str(payload.item_id),
            event_type=event.event_type,
            rating=event.rating,
            created_at=iso_manila(event.created_at),
        )
