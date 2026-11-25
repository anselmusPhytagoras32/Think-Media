# ThinkMedia conversation correction — November 25, 2026

FR10, NFR03/05/06/09/11. A student reported that sending “Hi” repeated an earlier
“Open opportunities” response. A live hosted reproduction returned a greeting
without history, then returned opportunity navigation when the identical latest
message included that earlier request. A direct Groq check reproduced the same
difference with identical tools, current page and empty source context. This
isolated the history interpretation from retrieval and browser submission.

Earlier questions followed the current question inside one JSON user message,
and the planner had no explicit conversational response function. The model
treated a completed request as the active task. Earlier task-focused tests had
not covered this conversational sequence.

## Correction

The backend recognizes whole-message English greetings and acknowledgements
before model planning. These local replies remain throttled and make no provider
request. Messages containing an actual task, such as “Hi, open opportunities”,
continue through normal planning. A bounded, read-only `reply` function supports
model-generated clarification and available-help responses.

Completed previous questions and approved public context now precede a separate
final user message containing the current question. The planner is instructed
to answer that latest message and to use older questions only as context.
No role, ownership, publication, source-validation or confirmation requirement
was weakened. No migration or sample-record reset was needed.

The frontend displays these replies as Conversation, with an appropriate status
announcement. It omits empty-source warnings and guidance-rating controls for
conversational replies. Existing guidance retains sources, uncertainty, retry,
source preview and feedback.

## Verification

Before the fix, five greeting/thanks regressions, the conversational-reply check
and the latest-message protocol check failed. The explicit task after a greeting
already passed. A browser regression also reproduced the missing conversational
display. After the fix, all 17 assistant backend checks and the ten focused
guidance/workspace/requirements browser checks passed. Two direct Groq requests
then selected `reply` for “Hi” both with and without the prior navigation request.

The final full backend suite passed **286 tests in 482.47 seconds**, and the
full Edge browser suite passed **54 tests in 315.89 seconds**. These totals
include the focused checks above; overlapping runs are not added together.
The production TypeScript/Vite build passed and Alembic reported no new upgrade
operations. Two further direct Groq requests correctly selected a conversational
reply for a help question after navigation and application navigation for an
explicit new request beginning with “Hi”.

Commands use private, explicitly selected disposable databases, never the hosted
database:

```powershell
cd backend
./.venv/Scripts/python.exe -m pytest -q --junitxml=../.local/chat-backend.xml
./.venv/Scripts/python.exe -m alembic check
cd ../frontend
npm run build
$env:PLAYWRIGHT_CHANNEL = 'msedge'
$env:PLAYWRIGHT_API_TARGET = 'http://127.0.0.1:8003'
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:5175'
npm test -- --reporter=line,junit
```

Local receipts and screenshots remain in ignored `.local` storage. All live
questions in this check are generic, use fictional demo access, and omit private
profiles, applications, PDFs and provider credentials from the request context.
These are functional checks, not pilot or research findings.
