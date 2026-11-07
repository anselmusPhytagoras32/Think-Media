"""FR08–09 explainable eligible matching and observed-only optional hybrid.

Weights are implementation configuration, never claimed as evaluated quality.
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

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

    @staticmethod
    def _profile_scores(profile_text, documents):
        if not profile_text.strip() or not documents:
            return [0.0] * len(documents)
        try:
            matrix = TfidfVectorizer(
                max_features=20000, strip_accents="unicode", ngram_range=(1, 2)
            ).fit_transform([profile_text, *documents])
            return cosine_similarity(matrix[0], matrix[1:]).ravel().tolist()
        except ValueError:
            return [0.0] * len(documents)

    def recommend(self, limit):
        if self.user.role != "student":
            raise ApiError(403, "FORBIDDEN", "A student account is required.")
        profile = self.db.get(StudentProfile, self.user.id)
        profile_text = (
            " ".join(
                [profile.program, *profile.skills, *profile.interests, profile.location]
            )
            if profile
            else ""
        )
        has_profile = bool(profile_text.strip())
        pools = {kind: self.repo.candidates(kind) for kind in ("listing", "content")}
        profile_scores = {}
        for kind, rows in pools.items():
            documents = [
                " ".join([row.title, row.description, row.location, *row.skills])
                if kind == "listing"
                else " ".join([row.title, row.body, *row.tags])
                for row in rows
            ]
            profile_scores[kind] = self._profile_scores(profile_text, documents)
        # A filled profile with no overlapping terms must not imply matching.
        has_profile = has_profile and any(
            score > 0 for scores in profile_scores.values() for score in scores
        )
        eligible = {f"{kind}:{row.id}" for kind, rows in pools.items() for row in rows}
        observed = []
        for event in self.repo.ratings():
            key = (
                f"listing:{event.listing_id}"
                if event.listing_id
                else f"content:{event.content_id}"
            )
            if key in eligible:
                observed.append(
                    dict(user=str(event.user_id), item=key, rating=event.rating)
                )
        frame = pd.DataFrame(observed, columns=["user", "item", "rating"])
        sufficient = len(frame) >= 20 and frame["user"].nunique() >= 5
        neighbors = []
        if has_profile and sufficient and self.alpha < 1:
            current = (
                frame[frame["user"] == str(self.user.id)]
                .set_index("item")["rating"]
                .to_dict()
            )
            for user, ratings in frame.groupby("user", sort=True):
                if user == str(self.user.id):
                    continue
                other = ratings.set_index("item")["rating"].to_dict()
                common = sorted(set(current) & set(other))
                if len(common) < 2:
                    continue
                # Similarity uses only co-observed ratings, never missing labels.
                left = np.array([current[item] for item in common], dtype=float)
                right = np.array([other[item] for item in common], dtype=float)
                similarity = float(cosine_similarity([left], [right])[0, 0])
                if similarity > 0:
                    neighbors.append((similarity, other))
        results = {}
        any_hybrid = False
        for kind, rows in pools.items():
            scores = profile_scores[kind]
            popular = (
                self.repo.popularity(kind, [row.id for row in rows])
                if not has_profile
                else {}
            )
            max_pop = max(popular.values(), default=0)
            ranked = []
            for index, row in enumerate(rows):
                content_score = float(scores[index])
                score = content_score
                if has_profile:
                    reason = (
                        "Based on shared terms in your profile and this resource."
                        if score > 0
                        else "No shared profile terms; ordered with recent resources first."
                    )
                    key = f"{kind}:{row.id}"
                    votes = [
                        (similarity, (values[key] - 1) / 4)
                        for similarity, values in neighbors
                        if key in values
                    ]
                    if votes:
                        collaborative = sum(
                            similarity * rating for similarity, rating in votes
                        ) / sum(similarity for similarity, _ in votes)
                        score = (
                            self.alpha * content_score
                            + (1 - self.alpha) * collaborative
                        )
                        any_hybrid = True
                        reason = "Based on your profile and optional ratings from users with shared observed ratings."
                elif max_pop:
                    score = popular.get(row.id, 0) / max_pop
                    reason = (
                        "Based on actual popularity from recorded views and optional ratings."
                        if popular.get(row.id, 0)
                        else "No recorded activity; recent eligible resource."
                    )
                else:
                    score = 1 - index / max(1, len(rows))
                    reason = "Recent eligible resource; no profile or activity match is available yet."
                item = (
                    MarketplaceService(self.db, self.user).listing_out(row)
                    if kind == "listing"
                    else LearningService(self.db, self.user).out(row)
                )
                ranked.append(
                    (
                        index,
                        dict(item=item, score=round(float(score), 6), reason=reason),
                    )
                )
            ranked.sort(key=lambda pair: (-pair[1]["score"], pair[0]))
            results["listings" if kind == "listing" else "content"] = [
                value for _, value in ranked[:limit]
            ]
        return dict(
            **results,
            mode="hybrid" if any_hybrid else "profile" if has_profile else "general",
            alpha=self.alpha if any_hybrid else 1.0,
            limitations=[
                f"Candidate pool is capped at {CANDIDATE_CAP} recent eligible items per type; collaborative input at {RATING_CAP} latest explicit ratings.",
                "Suggestions support exploration and are not placement or hiring decisions.",
                "Alpha defaults to 1; choosing a hybrid weight requires held-out evaluation that has not been performed.",
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
