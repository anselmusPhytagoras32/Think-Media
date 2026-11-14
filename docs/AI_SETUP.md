# Optional Gemini assistant — FR10 / NFR02/03/11

The owner selected **Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`)** for the
current presentation runtime after Gemini 3.8 Flash returned high-demand errors.
Set the model explicitly in the private dotenv file; the application's omitted-model
default remains `gemini-3.8-flash`. ThinkMedia includes a Google compatibility
profile tested with mocked HTTPS responses. No runtime key is included in Git;
actual live results are recorded separately in the QA report.

The November 13 Flash-Lite live smoke check passed through the app: HTTP 200,
one resolvable source citation and 9,900.4ms request latency.
[Recorded evidence](../backend/reports/live-ai-presentation.json) covers one
successful request; human factual assessment and research evaluations remain pending.

For the local presentation, `APP_ASSISTANT_MODE=retrieval` uses approved-resource excerpts without an external call. `disabled` shows a recoverable unavailable message. Student applications work in all modes.

## Configure privately

For this workstation, edit `backend/.env.local` and paste your Gemini key into
`APP_ASSISTANT_API_KEY='...'`. This file is ignored by Git and never served by
the frontend. The presentation launcher reads it after its private WSL runtime
configuration, overriding the old retrieval settings without changing database
configuration. Both plain `NAME=value` and `export NAME=value` work; quote values
with single quotes. Windows CRLF line endings are supported by the launcher.

Restart the existing backend after saving; reopening `RUN_THINKMEDIA.cmd` alone
reuses the running process. Direct backend launches load `.env`, then `.env.local`,
with existing process environment variables taking precedence. Isolated browser
QA explicitly forces retrieval, an empty provider key and zero external budget.

Set these values in the private environment used to start FastAPI, then restart that process:

```dotenv
APP_ASSISTANT_MODE=external
APP_ASSISTANT_PROVIDER_PROFILE=gemini
APP_ASSISTANT_MODEL=gemini-3.5-flash-lite
APP_ASSISTANT_ENDPOINT=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
APP_ASSISTANT_API_KEY=REPLACE_WITH_YOUR_PRIVATE_GEMINI_KEY
APP_ASSISTANT_REASONING_EFFORT=low
APP_ASSISTANT_TIMEOUT_SECONDS=20
APP_ASSISTANT_MAX_COMPLETION_TOKENS=1024
APP_ASSISTANT_CALL_BUDGET=25
```

The Gemini profile resolves an omitted endpoint to the URL above; an omitted
model still uses `gemini-3.8-flash`, so keep the explicit Flash-Lite setting.
A key and a positive call budget are required for network calls. Keep the key
outside Git and the frontend; never place it in a `VITE_*` variable, screenshot
or presentation. Obtain/configure it privately through Google AI Studio. A
developer's Codex or Gemini coding-agent login is separate from the app's API credential.

If starting through a launcher, change the private runtime environment that launcher loads. Existing process environment values override `backend/.env`; editing that file alone may not change a launcher's configured mode. Do not replace database settings while configuring the assistant.

## Request compatibility and limits

The Gemini profile sends `model`, text `messages`, `stream=false`, `response_format=json_schema`, `max_tokens` and `reasoning_effort`. It omits OpenAI's `store`, `n` and `max_completion_tokens` fields, plus sampling parameters, tools, attachments, file APIs, browser/search tools and conversation storage. Requests contain only the question, up to three preceding user questions (1000 characters each), and up to three approved public excerpts (1600 characters each). Private profiles, applications, resumes, sessions and user identities never enter the provider adapter. Users should keep sensitive personal details out of questions.

Google documents Gemini 3.8 thinking levels as `low`, `medium` and `high`; `minimal` is unsupported. The profile defaults to `low` and never silently disables reasoning or increases token limits. The default 512-token cap includes reasoning and visible output. The local presentation configuration deliberately uses 1024 tokens and a 20-second deadline to allow more useful answers. A response that exhausts the cap is rejected as incomplete and the app offers recovery; the cap is not automatically raised. An operator can deliberately increase `APP_ASSISTANT_MAX_COMPLETION_TOKENS` up to 2048 or the timeout up to 30 seconds after reviewing quota and cost limits. These settings do not guarantee that every question completes.

All external attempts, including failures, consume the configured process-lifetime call budget. With 25 calls, the 26th attempt is blocked. Restarting resets it and multiple workers have separate budgets, so it is not a monetary spending limit. Set provider account spending/quota controls separately. There are no automatic retries or redirects. The total request deadline is 10 seconds by default, request JSON is capped at 16KiB and responses at 32KiB. Provider retention and region remain governed by the approved account terms; omitting `store` is not a claim of zero provider retention.

## What to demonstrate

Ask a matching question such as “What should I include in my OJT resume?” The service can retrieve the versioned public resume guide even after local data is reset. Administrator-published learning resources remain available as additional, preferred sources when relevant. Every returned source ID is validated against the retrieved context; bundled guide IDs resolve through the read-only guidance source endpoint. The UI should show the answer, matching source previews and uncertainty when appropriate. A schematic provider response is:

```json
{
  "answer": "List the relevant skills described in the approved resume guide.",
  "source_ids": ["THE_ACTUAL_APPROVED_RESOURCE_ID"],
  "uncertainty": false
}
```

This is a schema illustration, not a recorded live answer. If no matching approved material exists, ThinkMedia admits uncertainty without contacting Gemini. Provider errors, quota exhaustion, timeouts, malformed JSON and unknown citations produce a safe unavailable response; applications remain usable. Do not describe retrieval mode as a live model response.

For an OpenAI profile, set `APP_ASSISTANT_PROVIDER_PROFILE=openai` and explicitly configure the approved endpoint/model/key. That profile retains `store=false`, `n=1` and `max_completion_tokens`; it does not send Gemini thinking controls.

## Evidence and official sources

Provider tests use synthetic HTTPX transports and verify both request profiles, timeout cancellation, bounds, citation checks, missing settings, quota errors, secret masking and no-source behavior. Run from `backend`:

```bash
.venv/bin/python -m pytest -q tests/test_external_assistant.py
```

Implementation was checked against the official [Gemini 3.8 Flash model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash), [OpenAI compatibility guide](https://ai.google.dev/gemini-api/docs/openai), and [thinking guide](https://ai.google.dev/gemini-api/docs/thinking). Google's [compatibility token-limit clarification](https://discuss.ai.google.dev/t/gemini-3-6-flash-openai-compatible-token-limits-response-fields-and-auth-keys/183372) describes `max_tokens` as the combined thinking/output cap; its cited example concerns Gemini 3.6, while the selected model and supported thinking levels come from the current Gemini 3.8 documentation. Live account access, configured quotas and response behavior still require an authorized key and a real smoke test.
