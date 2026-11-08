"""FR03/11, NFR03/11: public caching preserves publication and user isolation."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.content_cache import PublicContentCache
from app.services.learning import LearningService


def projection():
    return dict(
        id=str(uuid4()), title="Resource", summary="Summary", body="Body",
        tags=["resume"], status="published", created_at="2026-11-07T08:00:00+08:00",
        updated_at="2026-11-07T08:00:00+08:00", has_quiz=True,
    )


def test_cache_copies_both_stored_and_returned_values():
    cache = PublicContentCache()
    value = projection()
    cache.put("resource", value)
    value["tags"].append("mutation")
    first = cache.get("resource")
    first["tags"].append("another mutation")
    assert cache.get("resource")["tags"] == ["resume"]


def test_cache_bounds_ttl_and_lru_without_extending_expiry():
    now = [0]
    cache = PublicContentCache(max_entries=2, ttl_seconds=10, clock=lambda: now[0])
    cache.put("first", projection())
    cache.put("second", projection())
    assert cache.get("first")
    cache.put("third", projection())
    assert cache.get("second") is None
    now[0] = 10
    assert cache.get("first") is None
    assert cache.get("third") is None


@pytest.mark.parametrize("changes", [
    {"saved": True}, {"reacted": True}, {"correct_index": 0},
    {"status": "draft"}, {"status": "archived"}, {"body": object()},
])
def test_cache_refuses_private_fields_unpublished_content_and_objects(changes):
    cache = PublicContentCache()
    with pytest.raises((ValueError, TypeError)):
        cache.put("resource", {**projection(), **changes})


def service_fixture(monkeypatch):
    import app.services.learning as module
    monkeypatch.setattr(module, "public_content_cache", PublicContentCache())
    now = datetime.now(timezone.utc)
    row = SimpleNamespace(
        id=uuid4(), title="Original", summary="Summary", body="Body", tags=["resume"],
        status="published", created_at=now, updated_at=now,
    )
    database = object()
    states = {}
    question_calls = []
    db = SimpleNamespace(
        get_bind=lambda: database,
        get=lambda model, key: states.get(key[0]),
    )
    repo = SimpleNamespace(questions=lambda key: question_calls.append(key) or [object()])
    service = LearningService.__new__(LearningService)
    service.db, service.repo = db, repo
    service.user = SimpleNamespace(id="first")
    return service, row, states, question_calls


def test_service_shares_only_public_projection_and_reloads_personal_flags(monkeypatch):
    service, row, states, questions = service_fixture(monkeypatch)
    states["first"] = SimpleNamespace(saved=True, reacted=False)
    first = service.out(row)
    service.user.id = "second"
    second = service.out(row)
    assert first["saved"] is True and second["saved"] is False
    assert first["has_quiz"] is True and len(questions) == 1
    states["second"] = SimpleNamespace(saved=False, reacted=True)
    assert service.out(row)["reacted"] is True
    assert len(questions) == 1


def test_row_version_status_and_database_identity_cannot_reuse_projection(monkeypatch):
    service, row, _, questions = service_fixture(monkeypatch)
    assert service.out(row)["title"] == "Original"
    row.title = "Edited"
    row.updated_at += timedelta(seconds=1)
    assert service.out(row)["title"] == "Edited"
    row.status = "archived"
    assert service.out(row)["status"] == "archived"
    assert service.out(row)["status"] == "archived"
    row.status = "published"
    row.title = "Other database resource"
    other_database = object()
    service.db.get_bind = lambda: other_database
    assert service.out(row)["title"] == "Other database resource"
    assert len(questions) == 5
