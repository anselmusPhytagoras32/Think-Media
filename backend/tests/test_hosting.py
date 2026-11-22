"""FR01/03/10, NFR02/06: hosted configuration and provider failover."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app
from app.providers.assistant import AssistantUnavailable, RoutedProvider
from ops.hosted import bootstrap_demo


def provider_settings(**updates):
    return Settings(
        _env_file=None,
        **{
            "assistant_mode": "external",
            "assistant_provider_profile": "groq_openrouter",
            "groq_api_key": "synthetic-groq",
            "openrouter_api_key": "synthetic-openrouter",
            "assistant_call_budget": 2,
            **updates,
        },
    )


def test_hosted_same_origin_static_files_and_csrf(settings, tmp_path):
    (tmp_path / "index.html").write_text("<html>ThinkMedia build</html>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("export const app = true;")
    hosted = create_app(settings.model_copy(update={
        "frontend_dist": str(tmp_path),
        "app_env": "demo",
        "public_origin": "https://thinkmedia.example",
    }))
    try:
        with TestClient(hosted, base_url="https://thinkmedia.example") as client:
            assert client.get("/").text == "<html>ThinkMedia build</html>"
            assert client.get("/").headers["cache-control"] == "no-cache"
            assert client.get("/assets/app.js").status_code == 200
            assert client.get("/assets/missing.js").status_code == 404
            assert client.get("/.env").status_code == 404
            assert client.get("/health").json() == {"status": "ok"}
            assert client.get("/api/v1/unknown").json()["error"]["code"] == "NOT_FOUND"
            csrf = client.get("/api/v1/auth/csrf").json()["csrf_token"]
            response = client.post("/api/v1/auth/register", headers={
                "X-CSRF-Token": csrf,
                "Origin": "https://thinkmedia.example",
            }, json={
                "email": "hosted@example.test", "password": "synthetic-hosting-42",
                "display_name": "Hosted student", "role": "student",
            })
            assert response.status_code == 201, response.text
    finally:
        hosted.state.engine.dispose()


def test_render_database_urls_and_secure_origin(monkeypatch):
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://thinkmedia.example")
    config = Settings(
        _env_file=None, app_env="demo",
        database_url="postgres://role:password@db.example/thinkmedia?sslmode=require",
    )
    assert config.database_url.startswith("postgresql+psycopg://")
    assert config.database_url.endswith("?sslmode=require")
    assert "https://thinkmedia.example" in config.origin_set
    assert config.cookie_secure_enabled is True
    for origin in ("http://thinkmedia.example", "https://thinkmedia.example/extra"):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, public_origin=origin)


def test_cloud_demo_is_idempotent_and_preserves_an_instructor_edit(db, monkeypatch):
    from app.models import LearningSubmission, User
    from sqlalchemy import func, select
    for role in ("administrator", "instructor", "student", "company"):
        monkeypatch.setenv(f"APP_DEMO_{role.upper()}_PASSWORD", "synthetic-password-" + role)
    first = bootstrap_demo(db)
    db.commit()
    assert first == {"skills_created": 3, "lessons_published": 3, "drafts_created": 3}
    draft = db.scalar(select(LearningSubmission).where(LearningSubmission.status == "draft"))
    draft.payload = {**draft.payload, "title": "An instructor's saved change"}
    db.commit()
    assert bootstrap_demo(db) == {"skills_created": 0, "lessons_published": 0, "drafts_created": 0}
    db.commit()
    db.refresh(draft)
    assert draft.payload["title"] == "An instructor's saved change"
    assert db.scalar(select(func.count()).select_from(User)) == 4


def test_provider_failover_counts_both_attempts_and_validates_citations():
    seen = []
    sources = [{"id": "approved", "title": "OJT guide", "excerpt": "Prepare a project example."}]
    def handle(request):
        payload = json.loads(request.content)
        seen.append((request.url.host, payload))
        assert "tools" not in payload
        if request.url.host == "api.groq.com":
            assert "store" not in payload
            assert payload["model"] == "openai/gpt-oss-20b"
            return httpx.Response(429)
        assert payload["model"] == "nvidia/nemotron-3.5-super-vl:free"
        assert payload["response_format"] == {"type": "json_object"}
        return httpx.Response(200, json={"choices": [{
            "finish_reason": "stop",
            "message": {"content": json.dumps({
                "answer": "Prepare a project example.", "source_ids": ["approved"], "uncertainty": False,
            })},
        }]})
    provider = RoutedProvider(provider_settings(), transport=httpx.MockTransport(handle))
    answer = provider.respond("How do I prepare?", sources)
    assert answer["sources"] == [{"id": "approved", "title": "OJT guide"}]
    assert provider.calls_used == 2
    with pytest.raises(AssistantUnavailable):
        provider.respond("Another question", sources)
    assert len(seen) == 2


def test_invalid_fallback_citations_are_rejected_and_missing_keys_stay_off():
    def handle(_request):
        return httpx.Response(200, json={"choices": [{
            "finish_reason": "stop",
            "message": {"content": json.dumps({
                "answer": "Invalid.", "source_ids": ["private-application"], "uncertainty": False,
            })},
        }]})
    sources = [{"id": "approved", "title": "OJT guide", "excerpt": "An approved excerpt."}]
    provider = RoutedProvider(provider_settings(), transport=httpx.MockTransport(handle))
    with pytest.raises(AssistantUnavailable):
        provider.respond("Question", sources)
    assert provider.calls_used == 2
    empty = RoutedProvider(provider_settings(groq_api_key="", openrouter_api_key=""))
    with pytest.raises(AssistantUnavailable):
        empty.respond("Question", sources)
    assert empty.calls_used == 0
