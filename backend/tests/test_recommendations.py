"""FR08–09: real-item ranking and observed feedback, without efficacy claims."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models import CompanyProfile, User
from tests.helpers import patch_json, post_json
from tests.test_marketplace import company, student
from tests.test_learning import administrator, create_content


def opportunity(owner, title, skills=None):
    response = post_json(
        owner,
        "/api/v1/company/listings",
        dict(
            title=title,
            description=title,
            requirements="Submit a PDF resume.",
            location="Legazpi",
            type="ojt",
            skills=skills or [],
        ),
    )
    assert response.status_code == 201, response.text
    row = response.json()
    assert (
        post_json(owner, f"/api/v1/company/listings/{row['id']}/publish").status_code
        == 200
    )
    return row


def feedback(actor, item_id, *, item_type="listing", event_type="rating", rating=5):
    body = dict(item_type=item_type, item_id=item_id, event_type=event_type)
    if event_type == "rating":
        body["rating"] = rating
    return post_json(actor, "/api/v1/interactions", body)


def test_profile_cosine_ranking_is_deterministic_and_returns_actual_items(app):
    owner = company(app)
    matching = opportunity(owner, "React frontend interface development", ["React"])
    unrelated = opportunity(
        owner, "Accounting bookkeeping reconciliation", ["Accounting"]
    )
    admin = administrator(app)
    relevant_content = create_content(
        admin, title="React frontend interface development"
    )
    actor = student(app)
    patch_json(
        actor,
        "/api/v1/profiles/me",
        {
            "program": "Frontend development",
            "skills": ["React"],
            "interests": ["interface"],
            "location": "Legazpi",
        },
    )
    first = actor.get("/api/v1/recommendations?limit=10")
    assert first.status_code == 200, first.text
    result = first.json()
    assert result["mode"] == "profile" and result["alpha"] == 1
    assert result == actor.get("/api/v1/recommendations?limit=10").json()
    assert result["listings"][0]["item"]["id"] == matching["id"]
    assert result["listings"][0]["score"] > next(
        item["score"]
        for item in result["listings"]
        if item["item"]["id"] == unrelated["id"]
    )
    assert result["content"][0]["item"]["id"] == relevant_content["id"]
    assert all(
        0 <= item["score"] <= 1 and item["reason"]
        for group in ("listings", "content")
        for item in result[group]
    )
    assert result["limitations"]
    assert actor.get("/api/v1/recommendations?limit=21").status_code == 422
    assert actor.get("/api/v1/recommendations?limit=0").status_code == 422


def test_cold_start_explains_recent_then_observed_popularity(app):
    owner = company(app)
    older = opportunity(owner, "Earlier eligible opportunity")
    recent = opportunity(owner, "Latest eligible opportunity")
    actor = student(app)
    first = actor.get("/api/v1/recommendations").json()
    assert first["mode"] == "general" and first["alpha"] == 1
    assert first["listings"][0]["item"]["id"] == recent["id"]
    assert "recent" in first["listings"][0]["reason"].lower()
    observer = student(app, email="observer@example.test")
    assert feedback(observer, older["id"], event_type="view").status_code == 201
    popular = actor.get("/api/v1/recommendations").json()
    assert popular["listings"][0]["item"]["id"] == older["id"]
    assert "popular" in popular["listings"][0]["reason"].lower()
    assert popular["alpha"] == 1


def test_closed_draft_unverified_and_unpublished_items_are_excluded(app):
    owner = company(app)
    eligible = opportunity(owner, "Eligible React position", ["React"])
    closed = opportunity(owner, "Closed React position", ["React"])
    assert (
        post_json(owner, f"/api/v1/company/listings/{closed['id']}/close").status_code
        == 200
    )
    draft_response = post_json(
        owner,
        "/api/v1/company/listings",
        dict(
            title="Draft React",
            description="React",
            requirements="Resume",
            location="Legazpi",
            type="ojt",
            skills=["React"],
        ),
    )
    assert draft_response.status_code == 201
    unverified_owner = company(app, email="revoked@example.test")
    unverified = opportunity(unverified_owner, "Unverified React position", ["React"])
    with app.state.session_factory() as db:
        profile = db.get(CompanyProfile, UUID(unverified["company_id"]))
        profile.verification_status = "rejected"
        db.commit()
    admin = administrator(app)
    published = create_content(admin)
    draft_content = create_content(admin, status="draft")
    archived = create_content(admin)
    assert (
        patch_json(
            admin, f"/api/v1/admin/content/{archived['id']}", {"status": "archived"}
        ).status_code
        == 200
    )
    actor = student(app)
    patch_json(actor, "/api/v1/profiles/me", {"skills": ["React"]})
    result = actor.get("/api/v1/recommendations").json()
    assert {entry["item"]["id"] for entry in result["listings"]} == {eligible["id"]}
    assert {entry["item"]["id"] for entry in result["content"]} == {published["id"]}
    for id in (closed["id"], draft_response.json()["id"], unverified["id"]):
        assert feedback(actor, id).status_code in (403, 404, 409)
    for id in (draft_content["id"], archived["id"]):
        assert feedback(actor, id, item_type="content").status_code in (403, 404, 409)


def test_recommendations_roles_and_feedback_roles_are_server_enforced(app):
    owner = company(app)
    row = opportunity(owner, "Observed opportunity")
    actor = student(app)
    teacher = student(app, email="teacher@example.test", role="instructor")
    admin = administrator(app)
    assert TestClient(app).get("/api/v1/recommendations").status_code == 401
    for other in (owner, teacher, admin):
        assert other.get("/api/v1/recommendations").status_code == 403
    for other in (owner, admin):
        assert feedback(other, row["id"]).status_code == 403
    assert feedback(teacher, row["id"]).status_code == 201
    assert feedback(actor, row["id"]).status_code == 201


def test_invalid_ratings_and_mass_assignment_create_no_events(app):
    owner = company(app)
    row = opportunity(owner, "Validated feedback opportunity")
    actor = student(app)
    base = dict(item_type="listing", item_id=row["id"], event_type="rating")
    for invalid in (None, 0, 6, True, False, 3.0, 3.5, "3"):
        response = post_json(actor, "/api/v1/interactions", {**base, "rating": invalid})
        assert response.status_code == 422, (invalid, response.text)
    for field, value in (
        ("user_id", str(uuid4())),
        ("created_at", "2000-01-01T00:00:00Z"),
        ("timestamp", "2000-01-01T00:00:00Z"),
    ):
        assert (
            post_json(
                actor, "/api/v1/interactions", {**base, "rating": 3, field: value}
            ).status_code
            == 422
        )
    assert (
        post_json(
            actor, "/api/v1/interactions", {**base, "event_type": "view", "rating": 4}
        ).status_code
        == 422
    )
    assert (
        post_json(
            actor,
            "/api/v1/interactions",
            {**base, "event_type": "invented", "rating": 3},
        ).status_code
        == 422
    )
    assert (
        post_json(
            actor, "/api/v1/interactions", {**base, "item_type": "other", "rating": 3}
        ).status_code
        == 422
    )
    assert feedback(actor, str(uuid4())).status_code == 404
    assert feedback(actor, str(uuid4()), item_type="content").status_code == 404
    from app.models import Interaction

    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Interaction)) == 0


def test_rating_upsert_views_and_server_identity_time(app):
    owner = company(app)
    row = opportunity(owner, "Actual feedback opportunity")
    actor = student(app)
    admin = administrator(app)
    resource = create_content(admin)
    first = feedback(actor, row["id"], rating=2)
    assert first.status_code == 201, first.text
    updated = feedback(actor, row["id"], rating=4)
    assert updated.status_code in (200, 201), updated.text
    assert updated.json()["id"] == first.json()["id"] and updated.json()["rating"] == 4
    before = datetime.now(timezone.utc)
    viewed = feedback(actor, row["id"], event_type="view")
    assert viewed.status_code == 201, viewed.text
    assert viewed.json()["rating"] is None
    assert (
        viewed.json()["item_type"] == "listing"
        and viewed.json()["item_id"] == row["id"]
    )
    occurred = datetime.fromisoformat(viewed.json()["created_at"])
    assert 0 <= (occurred - before).total_seconds() < 10
    assert (
        feedback(
            actor, resource["id"], item_type="content", event_type="view"
        ).status_code
        == 201
    )
    from app.models import Interaction

    with app.state.session_factory() as db:
        own_id = db.scalar(select(User.id).where(User.email == "student@example.test"))
        events = list(db.scalars(select(Interaction)))
        assert len(events) == 3
        assert all(event.user_id == own_id for event in events)
        ratings = [event for event in events if event.event_type == "rating"]
        assert len(ratings) == 1 and ratings[0].rating == 4
        assert all(
            event.rating is None for event in events if event.event_type == "view"
        )
        assert all(
            (event.listing_id is None) != (event.content_id is None) for event in events
        )


def test_insufficient_explicit_feedback_falls_back_to_alpha_one(app):
    owner = company(app)
    row = opportunity(owner, "React frontend development", ["React"])
    actor = student(app)
    patch_json(actor, "/api/v1/profiles/me", {"skills": ["React"]})
    app.state.settings.recommender_alpha = 0.25
    observer = student(app, email="single-observer@example.test")
    assert feedback(observer, row["id"], rating=5).status_code == 201
    result = actor.get("/api/v1/recommendations").json()
    assert result["mode"] == "profile" and result["alpha"] == 1
    assert result["listings"][0]["item"]["id"] == row["id"]
    assert result["limitations"]


def test_synthetic_observed_neighbors_enable_configured_hybrid_without_fabricated_ratings(
    app,
):
    """Synthetic functional fixture only; this does not measure recommendation quality."""
    owner = company(app)
    rows = [
        opportunity(owner, title, ["React"] if index == 2 else [])
        for index, title in enumerate(
            (
                "Observed item A",
                "Observed item B",
                "React frontend candidate",
                "Accounting candidate",
                "General candidate",
            )
        )
    ]
    actor = student(app)
    patch_json(actor, "/api/v1/profiles/me", {"skills": ["React"]})
    # Target and four peers share two real, explicit ratings. Each peer has
    # three additional observed items; absent target ratings stay absent.
    assert feedback(actor, rows[0]["id"], rating=5).status_code == 201
    assert feedback(actor, rows[1]["id"], rating=1).status_code == 201
    for index in range(4):
        peer = student(app, email=f"peer-{index}@example.test")
        for row, rating in zip(rows, (5, 1, 5, 1, 3)):
            assert feedback(peer, row["id"], rating=rating).status_code == 201
    app.state.settings.recommender_alpha = 0.25
    result = actor.get("/api/v1/recommendations").json()
    assert result["mode"] == "hybrid", result
    assert result["alpha"] == 0.25
    by_id = {entry["item"]["id"]: entry for entry in result["listings"]}
    assert by_id[rows[2]["id"]]["score"] > by_id[rows[3]["id"]]["score"]
    assert result["limitations"]
    from app.models import Interaction

    with app.state.session_factory() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(Interaction)
                .where(Interaction.event_type == "rating")
            )
            == 22
        )
        own_id = db.scalar(select(User.id).where(User.email == "student@example.test"))
        assert (
            db.scalar(
                select(func.count())
                .select_from(Interaction)
                .where(
                    Interaction.user_id == own_id, Interaction.event_type == "rating"
                )
            )
            == 2
        )


def test_unmatched_profile_uses_truthful_general_fallback(app):
    owner = company(app)
    row = opportunity(owner, "Accounting bookkeeping")
    actor = student(app)
    patch_json(actor, "/api/v1/profiles/me", {"skills": ["zzznomatchzzz"]})
    result = actor.get("/api/v1/recommendations").json()
    assert result["mode"] == "general" and result["alpha"] == 1
    assert result["listings"][0]["item"]["id"] == row["id"]
    assert "recent" in result["listings"][0]["reason"].lower()


def test_feedback_rate_limit_and_alpha_bounds(app):
    from app.security.throttle import Throttle
    from app.config import Settings
    from pydantic import ValidationError
    import pytest

    owner = company(app)
    row = opportunity(owner, "Bounded feedback")
    actor = student(app)
    app.state.interaction_throttle = Throttle(max_attempts=1, window_seconds=60)
    assert feedback(actor, row["id"], event_type="view").status_code == 201
    limited = feedback(actor, row["id"], event_type="view")
    assert limited.status_code == 429 and int(limited.headers["Retry-After"]) > 0
    assert actor.get("/api/v1/applications/me").status_code == 200
    for alpha in (-0.1, 1.1, float("inf"), float("nan")):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, APP_RECOMMENDER_ALPHA=alpha)


def test_interaction_foreign_keys_and_typed_target_are_enforced_in_database(app):
    import pytest
    from sqlalchemy.exc import IntegrityError
    from app.models import Interaction

    owner = company(app)
    row = opportunity(owner, "Typed reference")
    actor = student(app)
    with app.state.session_factory() as db:
        user_id = db.scalar(select(User.id).where(User.email == "student@example.test"))
        invalid_targets = [
            dict(listing_id=uuid4()),
            dict(),
            dict(listing_id=UUID(row["id"]), content_id=uuid4()),
        ]
        for target in invalid_targets:
            db.add(
                Interaction(user_id=user_id, event_type="view", rating=None, **target)
            )
            with pytest.raises(IntegrityError):
                db.commit()
            db.rollback()
        assert db.scalar(select(func.count()).select_from(Interaction)) == 0
