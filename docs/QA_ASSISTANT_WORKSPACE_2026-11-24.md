# ThinkMedia assistant workspace verification — November 24, 2026

This is functional prototype evidence for the owner's approved assistant and
fictional catalog extension. The fixed proposal and original presentation were
not edited. Earlier reports retain their dated results.

## Implemented behavior

FR02–04/06/08/10–11, NFR02–06/09/11: the configured model can select one
registered local function. Students can find lessons and opportunities, open
suggestions, save resources, and propose permitted profile changes. Instructors
can prepare lesson/quiz and skill drafts. Verified companies can prepare listing
drafts. All writes require an on-screen preview and explicit confirmation.
Administrators receive navigation to their authorized review screens.

Applications, publication, company verification and hiring decisions continue
through existing role-authorized screens. The model cannot execute arbitrary
code, open arbitrary URLs, impersonate another account, or bypass review.
See [the assistant contract](API_ASSISTANT_WORKSPACE.md) for the permission matrix,
confirmation lifecycle and provider data boundary.

The demo catalog adds a separate verified fictional company, six published
opportunities (four OJT, two jobs), and one editable listing draft. The original
pending company remains available for verification demonstrations. Initialization
preserves existing passwords, records, edits, applications and later decisions.
Three published practice lessons, three approved skill categories, lesson PDFs,
quizzes, links and editable instructor examples remain available.

## Local checks

The final complete backend suite passed **279 tests in 305.49 seconds**.
Alembic reported **no new upgrade operations detected** after the additive
`0010_assistant_actions` migration. This run includes the nested-quiz schema
regression and all existing authentication, marketplace and instructor checks.

The full browser suite passed **53 tests in 2.6 minutes** using installed Edge,
native Windows Python/PostgreSQL, and isolated API `127.0.0.1:8003` / frontend
`127.0.0.1:5175`. The first whole-browser attempt passed 49 checks and reached
the disposable server's registration throttle in four later tests. Raising only
that test server's registration allowance to the documented fixture setting
resolved the failures; the deployed registration limit was not changed.

The final assistant browser subset passed **two tests** after its final UI
wording update. These overlap the 53 checks and are not added to that total.
They cover preview-before-write, single confirmation, cancellation, readable
long text at 360 pixels, public result links and rejection of an external result
URL. Both preview states had no serious or critical automated axe findings.
Desktop and mobile screenshots were inspected. The browser tests use explicit
provider-response fixtures; they are not live model evaluations.

The production TypeScript/Vite build passed. All **eight evaluation integrity
checks** passed; these validate evaluation tooling, not research effectiveness.
Backend checks include proposal ownership/session binding, CSRF, expiry,
cancellation, replay denial, stale profile preconditions, role/verification
revalidation, transaction rollback, unpublished content exclusion, bounded model
requests, provider failure and the existing marketplace negative cases.

One live Groq `openai/gpt-oss-20b` request selected a valid lesson search. A
separate request with the complete instructor tool registry produced a validated
fictional lesson and one quiz question in one attempt. A prior drafting attempt
used an unsupported answer-letter property. Inlining the nested quiz schema and
describing the required zero-based `correct_index` resolved the observed failure;
local validation still rejects the unsupported property. This is a functional
check of those requests, not a guarantee about all generated lesson quality.

Reproduction, with private environment variables pointed at disposable local
databases (never the hosted demo):

```powershell
cd backend
./.venv/Scripts/python.exe -m pytest -q --junitxml=../.local/workspace-backend-final.xml
./.venv/Scripts/python.exe -m alembic check
cd ../frontend
npm run build
$env:PLAYWRIGHT_CHANNEL = 'msedge'
$env:PLAYWRIGHT_API_TARGET = 'http://127.0.0.1:8003'
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:5175'
npm test -- --reporter=line,junit
```

Set `TEST_DATABASE_URL` and `DATABASE_URL` explicitly for the disposable backend
test database. The separate browser server uses its own migrated fixture
database, retrieval mode, zero live-call budget and `APP_REGISTER_MAX_ATTEMPTS=1000`.
Use the existing browser-fixture instructions in the presentation guide for its
student/admin test identities. Private XML, screenshots, live-check receipts and
access sheets remain in ignored `.local` storage.

## Limitations

The assistant performs one supported action per question. Drafts require human
accuracy and suitability review. Only approved public excerpts, the user's
question, bounded preceding questions, page name and allowed tool definitions
reach the provider; private account objects, application records and PDFs do
not. Users should keep sensitive details out of their questions.

Real pilot data, MAE/RMSE, cross-validation results, CSAT findings, BERTScore,
human factual review and real assistive-technology testing remain pending.
Fictional catalog records and automated checks are not research findings.
Free hosting can sleep; the shared free database expires December 22, 2026.
See [hosting and recovery](RENDER_HOSTING.md) for private configuration, backup
conditions and operating limits. No production-readiness claim is made.
