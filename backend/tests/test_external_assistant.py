"""FR10/NFR02/03/11 external boundary checks; synthetic HTTP only, no DB/key."""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.providers.assistant import (
    AssistantUnavailable, DisabledProvider, ExternalProvider, provider_for,
)


@pytest.fixture(autouse=True)
def clean_database():
    """Override the inherited DB cleanup: these provider tests never use a DB."""
    yield


def settings(**overrides):
    return Settings(
        _env_file=None,
        **{
            "assistant_mode": "external",
            "assistant_provider_profile": "openai",
            "assistant_endpoint": "https://provider.example/v1/chat/completions",
            "assistant_model": "approved-test-model",
            "assistant_api_key": "synthetic-test-secret",
            "assistant_call_budget": 2,
            **overrides,
        },
    )


def sources():
    return [{"id": "approved-id", "title": "Resume guide", "excerpt": "List relevant skills."}]


def response(output=None, *, finish="stop"):
    output = output if output is not None else {
        "answer": "List relevant skills.", "source_ids": ["approved-id"], "uncertainty": False,
    }
    return httpx.Response(200, json={"choices": [{
        "finish_reason": finish, "message": {"content": json.dumps(output)},
    }]})


def test_explicit_constructor_settings_override_environment(monkeypatch):
    monkeypatch.setenv("APP_ASSISTANT_MODE", "retrieval")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://env@localhost/env")
    monkeypatch.setenv("APP_ASSISTANT_CALL_BUDGET", "99")
    explicit = Settings(
        _env_file=None, assistant_mode="disabled",
        database_url="postgresql+psycopg://test@localhost/isolated_test",
        assistant_call_budget=0,
    )
    assert explicit.assistant_mode == "disabled"
    assert explicit.database_url.endswith("/isolated_test")
    assert explicit.assistant_call_budget == 0
    assert isinstance(provider_for(explicit), DisabledProvider)


def test_external_request_has_only_bounded_public_context_and_no_tools():
    recorded = []

    def handle(request):
        recorded.append(request)
        return response()

    provider = ExternalProvider(settings(), transport=httpx.MockTransport(handle))
    source = {**sources()[0], "private_profile": "PRIVATE-MARKER"}
    answer = provider.respond("How should I write my resume?", [source])
    assert answer["sources"] == [{"id": "approved-id", "title": "Resume guide"}]
    assert answer["mode"] == "external"
    payload = json.loads(recorded[0].content)
    assert payload["store"] is False and payload["stream"] is False
    assert payload["max_completion_tokens"] == 512
    assert payload["n"] == 1 and "tools" not in payload
    assert payload["response_format"]["json_schema"]["strict"] is True
    assert "untrusted" in payload["messages"][0]["content"]
    assert "PRIVATE-MARKER" not in recorded[0].content.decode()
    assert "synthetic-test-secret" not in recorded[0].content.decode()
    assert recorded[0].headers["authorization"] == "Bearer synthetic-test-secret"
    assert provider.calls_used == 1


@pytest.mark.parametrize("failure", ["timeout", "429", "401", "redirect", "malformed", "oversized", "truncated"])
def test_provider_failures_are_generic_and_never_retried(failure):
    requests = []

    def handle(request):
        requests.append(request)
        if failure == "timeout":
            raise httpx.ReadTimeout("synthetic-test-secret private failure")
        if failure in {"429", "401"}:
            return httpx.Response(int(failure), text="synthetic-test-secret")
        if failure == "redirect":
            return httpx.Response(307, headers={"location": "https://elsewhere.example"})
        if failure == "malformed":
            return httpx.Response(200, text="not JSON synthetic-test-secret")
        if failure == "oversized":
            return httpx.Response(200, content=b"x" * (ExternalProvider.MAX_RESPONSE_BYTES + 1))
        return response(finish="length")

    provider = ExternalProvider(settings(), transport=httpx.MockTransport(handle))
    with pytest.raises(AssistantUnavailable) as captured:
        provider.respond("Resume help", sources())
    assert "synthetic-test-secret" not in str(captured.value)
    assert len(requests) == 1 and provider.calls_used == 1


@pytest.mark.parametrize("output", [
    {"answer": "Invented", "source_ids": ["private-draft"], "uncertainty": False},
    {"answer": "Invented", "source_ids": ["approved-id", "approved-id"], "uncertainty": False},
    {"answer": "Invented", "source_ids": ["approved-id"], "uncertainty": "false"},
    {"answer": "", "source_ids": [], "uncertainty": True},
    {"answer": "Fine", "source_ids": [], "uncertainty": True, "extra": "unexpected"},
])
def test_malformed_or_injected_output_is_rejected(output):
    provider = ExternalProvider(settings(), transport=httpx.MockTransport(lambda _: response(output)))
    with pytest.raises(AssistantUnavailable):
        provider.respond("Resume help", sources())


@pytest.mark.parametrize("missing", ["assistant_endpoint", "assistant_model", "assistant_api_key"])
def test_missing_configuration_never_contacts_provider(missing):
    def handle(_):
        pytest.fail("Missing configuration must not make a network request.")

    provider = ExternalProvider(settings(**{missing: ""}), transport=httpx.MockTransport(handle))
    with pytest.raises(AssistantUnavailable, match="not configured"):
        provider.respond("Resume help", sources())
    assert provider.calls_used == 0


def test_no_sources_admits_uncertainty_without_network_or_budget():
    def handle(_):
        pytest.fail("No approved sources must not make a network request.")

    provider = ExternalProvider(settings(assistant_call_budget=0), transport=httpx.MockTransport(handle))
    answer = provider.respond("Tell me about a private application", [])
    assert answer["uncertainty"] is True and answer["sources"] == []
    assert provider.calls_used == 0


def test_call_budget_is_atomic_and_failed_attempts_consume_it():
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(429)

    provider = ExternalProvider(settings(assistant_call_budget=1), transport=httpx.MockTransport(handle))

    def call(_):
        with pytest.raises(AssistantUnavailable):
            provider.respond("Resume help", sources())

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(call, range(4)))
    assert len(requests) == 1 and provider.calls_used == 1


def test_input_caps_are_enforced_before_network():
    provider = ExternalProvider(settings(), transport=httpx.MockTransport(lambda _: pytest.fail("Network forbidden")))
    for question, context in [("x" * 2001, sources()), ("Resume", sources() * 4), ("Resume", [{**sources()[0], "excerpt": "x" * 801}])]:
        with pytest.raises(AssistantUnavailable):
            provider.respond(question, context)
    assert provider.calls_used == 0


def test_total_timeout_cancels_slow_response_before_any_bytes():
    cancelled = []

    async def handle(_):
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            cancelled.append(True)
            raise
        return response()

    provider = ExternalProvider(settings(assistant_timeout_seconds=1), transport=httpx.MockTransport(handle))
    started = time.monotonic()
    with pytest.raises(AssistantUnavailable):
        provider.respond("Resume help", sources())
    assert time.monotonic() - started < 3
    assert cancelled == [True]


def test_request_byte_cap_counts_unicode_before_network():
    provider = ExternalProvider(settings(), transport=httpx.MockTransport(lambda _: pytest.fail("Network forbidden")))
    context = [{"id": str(i), "title": "😀" * 200, "excerpt": "😀" * 800} for i in range(3)]
    with pytest.raises(AssistantUnavailable, match="request is outside"):
        provider.respond("😀" * 2000, context)
    assert provider.calls_used == 0


@pytest.mark.parametrize("endpoint", [
    "http://provider.example/v1/chat/completions", "https://user:password@provider.example/v1/chat/completions",
    "https://provider.example/v1/chat/completions?api_key=bad", "https://provider.example/not-completions",
])
def test_endpoint_requires_explicit_https_completion_url(endpoint):
    with pytest.raises(ValidationError):
        settings(assistant_endpoint=endpoint)


def test_secret_is_masked_in_configuration_serialization():
    configuration = settings()
    assert "synthetic-test-secret" not in repr(configuration)
    assert "synthetic-test-secret" not in configuration.model_dump_json()
    assert configuration.model_dump()["assistant_api_key"].get_secret_value() == "synthetic-test-secret"


@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_gemini_profile_uses_selected_model_endpoint_and_supported_payload(effort):
    requests = []

    def handle(request):
        requests.append(request)
        return response()

    configuration = settings(
        assistant_provider_profile="gemini", assistant_endpoint="", assistant_model="",
        assistant_reasoning_effort=effort,
    )
    provider = ExternalProvider(configuration, transport=httpx.MockTransport(handle))
    result = provider.respond("Resume help", sources())
    request = requests[0]
    payload = json.loads(request.content)
    assert str(request.url) == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    assert payload["model"] == "gemini-3.8-flash"
    assert payload["max_tokens"] == 512 and payload["reasoning_effort"] == effort
    assert not ({"store", "n", "max_completion_tokens", "temperature", "top_p", "tools"} & set(payload))
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["schema"]["additionalProperties"] is False
    assert request.headers["authorization"] == "Bearer synthetic-test-secret"
    assert result["sources"] == [{"id": "approved-id", "title": "Resume guide"}]


def test_gemini_profile_preserves_explicit_token_cap_and_configuration():
    configuration = settings(
        assistant_provider_profile="gemini",
        assistant_endpoint="https://approved-proxy.example/v1/chat/completions",
        assistant_model="gemini-3.8-flash", assistant_max_completion_tokens=256,
    )
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        return response(finish="length")

    provider = ExternalProvider(configuration, transport=httpx.MockTransport(handle))
    with pytest.raises(AssistantUnavailable):
        provider.respond("Resume help", sources())
    assert requests[0]["max_tokens"] == 256
    assert provider.calls_used == 1 and len(requests) == 1
    assert configuration.assistant_effective_endpoint == configuration.assistant_endpoint


def test_gemini_defaults_do_not_activate_external_calls():
    configuration = Settings(_env_file=None, assistant_provider_profile="gemini", assistant_mode="disabled", assistant_call_budget=0)
    assert isinstance(provider_for(configuration), DisabledProvider)
    assert configuration.assistant_call_budget == 0
    assert configuration.assistant_effective_model == "gemini-3.8-flash"


@pytest.mark.parametrize("effort", ["minimal", "none", "off"])
def test_gemini_rejects_unsupported_thinking_levels(effort):
    with pytest.raises(ValidationError):
        settings(assistant_provider_profile="gemini", assistant_reasoning_effort=effort)
