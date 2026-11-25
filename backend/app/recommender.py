"""FR02/08/09/12, NFR08/11: shared runtime/offline hybrid scoring.

Only explicit ratings enter collaborative filtering. Text and ratings must be
restricted to the training partition when this module is used for evaluation.
"""

from collections import defaultdict
import math

from sklearn.feature_extraction.text import TfidfVectorizer

MODEL_VERSION = "hybrid-v2"
MIN_RATINGS = 20
MIN_USERS = 5
MIN_OVERLAP = 2
MAX_NEIGHBORS = 30


def profile_text(profile):
    """Relevant self-described background only; no name, email or private files."""
    return " ".join([profile.program, profile.background, *profile.skills, *profile.interests, profile.location]) if profile else ""


def listing_text(listing, company=None):
    return " ".join([listing.title, listing.description, listing.requirements, listing.location, *listing.skills,
                     company.description if company else ""])


def fit_text(documents):
    vectorizer = TfidfVectorizer(max_features=20000, strip_accents="unicode", ngram_range=(1, 2))
    try:
        return vectorizer.fit(documents)
    except ValueError as error:
        if "empty vocabulary" not in str(error):
            raise
        return None


def content_scores(vectorizer, profiles, documents):
    if len(profiles) != len(documents):
        raise ValueError("Profile and item projections must align.")
    if vectorizer is None or not documents:
        return [0.0] * len(documents)
    left = vectorizer.transform(profiles)
    right = vectorizer.transform(documents)
    return [min(1.0, max(0.0, float(value))) for value in left.multiply(right).sum(axis=1).A1]


class HybridScorer:
    def __init__(self, ratings):
        self.histories = defaultdict(dict)
        for row in ratings:
            user, item, rating = str(row["user_id"]), str(row["item_id"]), row["rating"]
            if not user or not item or isinstance(rating, bool) or not isinstance(rating, (int, float)) or not math.isfinite(rating) or not 1 <= rating <= 5:
                raise ValueError("Only observed ratings from 1 to 5 are supported.")
            if item in self.histories[user]:
                raise ValueError("Use one latest explicit rating per user/item.")
            self.histories[user][item] = float(rating)
        self.rating_count = sum(map(len, self.histories.values()))
        self.ready = self.rating_count >= MIN_RATINGS and len(self.histories) >= MIN_USERS

    def neighbors(self, user_id):
        current = self.histories.get(str(user_id), {})
        if not self.ready or len(current) < MIN_OVERLAP:
            return []
        neighbors = []
        for peer, history in self.histories.items():
            if peer == str(user_id):
                continue
            common = sorted(current.keys() & history.keys())
            if len(common) < MIN_OVERLAP:
                continue
            divisor = math.sqrt(sum(current[item] ** 2 for item in common) * sum(history[item] ** 2 for item in common))
            similarity = sum(current[item] * history[item] for item in common) / divisor
            if similarity > 0:
                neighbors.append((similarity, peer, history))
        return sorted(neighbors, key=lambda value: (-value[0], value[1]))[:MAX_NEIGHBORS]

    def predict(self, user_id, item_ids, scores, *, alpha):
        if not math.isfinite(alpha) or not 0 <= alpha <= 1 or len(item_ids) != len(scores):
            raise ValueError("Use aligned items/scores and alpha between zero and one.")
        neighbors = self.neighbors(user_id) if alpha < 1 else []
        output = []
        for item, content in zip(item_ids, scores):
            votes = [(weight, (history[str(item)] - 1) / 4) for weight, _, history in neighbors if str(item) in history]
            collaborative = sum(w * score for w, score in votes) / sum(w for w, _ in votes) if votes else None
            effective = alpha if collaborative is not None else 1.0
            content = min(1.0, max(0.0, float(content)))
            score = content if collaborative is None else effective * content + (1 - effective) * collaborative
            output.append(dict(score=score, content_score=content, collaborative_score=collaborative,
                               effective_alpha=effective, strategy="hybrid" if collaborative is not None else "profile",
                               neighbor_count=len(votes)))
        return output
