# ThinkMedia local presentation acceptance

**November 23 update:** the approved fictional-data demo is available at
https://thinkmedia-demo-m74t.onrender.com. See [Render hosting](RENDER_HOSTING.md)
for credentials, prepared lessons, provider configuration, backups, and free-plan
limits, and [current requirements coverage](REQUIREMENTS_COVERAGE_2026-11-23.md)
for rerun evidence. Native Windows Python/PostgreSQL and Edge were used for the
current checks. The WSL launcher instructions, empty-data state, local-only scope,
and dated results below describe the earlier November presentation setup.

**Current data state — November 14:** at the owner's request, all local data
except administrator accounts has been reset after a private backup. Earlier
seed accounts, listings and published guides are no longer in the active
presentation database. Normal startup stays empty. See [Local reset](LOCAL_RESET.md)
for the wipe script and how to begin testing with your own accounts and content.

Latest whole-app QA: [November 13 requirements and presentation acceptance](QA_PRESENTATION_2026-11-13.md).
Latest functional correction: [November 14 cross-role sync and useful Guidance](QA_FUNCTIONAL_SYNC_2026-11-14.md), with 245 backend checks, 48 browser checks and four live source-grounded answers passing.
The dated results below remain historical; use the latest report for current checks and limitations.

Scope confirmed by the project owner: local presentation, fictional accounts,
fictional applications and sample PDFs; no cloud deployment or real participant
data. The developers/presenters control the demo database. External AI integration
is requested but must be enabled with a separately configured provider/model/key.

## Start on this Windows workstation

Double-click `RUN_THINKMEDIA.cmd` in the repository root. It starts the API and
frontend if needed, checks readiness and opens the local app in your browser.
It reuses an already running ThinkMedia instance. Startup logs stay in `.local`.
Both the ready-instance and cold-start paths have been exercised successfully.
Cold WSL/Python library initialization can take several minutes. The launcher
waits up to five minutes per service and reports progress while its process is
alive. Repeat launches reuse a tracked startup and a concurrent launch is
prevented. Logs are named in the console; no database or provider keys are shown.

For startup without opening the browser:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\present.ps1
```

The backend virtual environment and database are Linux artifacts in Ubuntu WSL.
For individual service terminals, use two PowerShell terminals from the root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-local.ps1 api
```

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-local.ps1 web
```

Open http://127.0.0.1:5173. Keep both terminals open. Ctrl+C stops each server.
The database persists across restarts. Use `npm.cmd ci` in `frontend` if native
Windows dependencies need installation. This does not replace PostgreSQL data.
The private runtime configuration remains outside Git. Do not paste its contents
into a presentation, screenshot, issue, or chat.

Dedicated presentation accounts are ready for all four roles:
`presentation-student@example.test`, `presentation-instructor@example.test`,
`presentation-company@example.test`, and
`presentation-administrator@example.test`. Their generated local-only passwords
are in `.local/presentation/presentation-accounts.private.json`, which is ignored
by Git. All four were checked through the running HTTP API: sign-in 200 and
sign-out 204, with matching role and account ID. The company starts pending so
you can demonstrate actual administrator verification. The administrator was
provisioned locally, with no public registration or privilege elevation.

Existing accounts and passwords were preserved. Repeating
`wsl -d Ubuntu -- bash scripts/prepare-presentation.sh` creates no duplicate
accounts and does not reset edits made during the demonstration. A regression
checks that the default credential path resolves inside this repository.
Use `presentation/fictional-resume.pdf` as the sample application attachment.
It contains fictional data and can be reproduced with
`python scripts/create-demo-pdf.py`.

## Demonstration sequence

1. Show student registration/profile validation and the visible registration data-use notice.
2. Sign in as the demonstration company; explain pending verification. As the
   separately provisioned administrator, verify the company with a reason.
3. Create a draft OJT listing, publish it, and find it from student search.
4. As student, choose a fictional PDF of at most 5 MiB, review and submit. Show
   the reference, duplicate protection and application history.
5. As company, review the applicant, move to Under Review then a final decision.
   As student, show the resulting read-only history. Close the listing and show
   that it no longer appears as an open opportunity.
6. As administrator, prepare a resource and quiz. Review and confirm publication.
   As learner, save/react, answer the quiz, and report content. Resolve the report
   from the administrator workspace and inspect audit events.
7. Show Suggestions and reasons. Update skills/interests and demonstrate the
   profile matching fallback. Ratings in this demo are synthetic demonstration
   events and cannot be counted as research respondents.
8. Ask guidance a question covered by an approved resource. Show its sources,
   uncertainty, bounded conversation and retry. Clearly identify resource lookup
   versus a configured live provider using the displayed response label.

## Fresh verification

On November 8, 2026, the current revision passed 237 backend tests against the
separate disposable PostgreSQL database, 8 evaluation integrity tests, Alembic
schema drift validation and the Windows frontend production build. The initial
run exposed a configuration precedence defect; the fix and regression are part
of those 237 passing tests. All 30 browser acceptance tests passed in 2.3 minutes
using installed Windows Chrome and the isolated browser API/database. They cover
actual registration, profiles, administrator verification, company publishing,
student application/review/closure, learning/moderation, suggestions and the new
guidance/confirmation/error cases. Automated accessibility scans passed in the
tested states. The final frontend build passed after the rendered review fix.

```powershell
wsl -d Ubuntu -- bash scripts/verify-local.sh
cd frontend
npm.cmd run build
```

Browser tests use the separate `browser-api` server on 8001, never the presentation
database. Start it with `start-local.ps1 browser-api`; run from frontend:

```powershell
$env:PLAYWRIGHT_API_TARGET='http://127.0.0.1:8001'
$env:PLAYWRIGHT_BASE_URL='http://127.0.0.1:5174'
$env:PLAYWRIGHT_CHANNEL='chrome' # Installed Chrome; omit for Playwright Chromium.
npm.cmd test
```

The browser-test configuration now refuses missing API configuration and refuses
the presentation API on port 8000. These refusal paths were exercised; explicitly
selecting isolated port 8001 loads the isolated suite successfully.

## Requirements and remaining evidence

| Requirement | Current acceptance evidence or dependency |
|---|---|
| FR01–02 | Role/auth/profile tests; administrator cannot be self-selected |
| FR03 | Publication visibility, learner state and answer-key scoring tests |
| FR04–07 | Search, verified ownership, private upload/download, duplicate/closed protection, concurrency and transaction rollback tests |
| FR08–09 | Eligible profile/hybrid ranking and explicit-feedback tests; real effectiveness metrics require future real datasets |
| FR10 | Approved-only retrieval and Gemini 3.8 Flash HTTPS adapter; 35 synthetic provider-boundary tests; [private configuration](AI_SETUP.md) and a live run are still needed for live-success evidence |
| FR11 | Company verification, publication/moderation and atomic audit tests |
| FR12/NFR08 | Reproducible evaluator and 8 integrity tests; [synthetic metric pipeline](../evaluation/DEMO.md) and [actual BERTScore on six fictional pairs](../evaluation/SEMANTIC_DEMO.md); genuine research results and human factual checks remain unmeasured |
| NFR01 | Current warm synthetic 20-user run: 200 GETs, zero failures, p95 729.553ms; [conditions and limits](../backend/reports/performance-presentation.json) |
| NFR02–04 | Authorization/privacy boundaries and transactional tests; HTTP is limited to loopback presentation use |
| NFR05/09/10 | Browser keyboard/360px/axe checks and English/Manila dates; human assistive-technology verification still needs a human session |
| NFR06 | Modular React/FastAPI/PostgreSQL, versioned schema, build and workflow tests |
| NFR07 | Private backup/restore verified; local user daily backup task installed and manually executed successfully (result 0) |
| NFR11 | Public projection cache, pagination, bounds and admin monitoring; explicit audited attachment expiry is implemented with a dry-run default, while the real policy period remains unapproved |

## Operations

Run `wsl -d Ubuntu -- bash scripts/backup-local.sh` before the presentation while
the demo is idle. It produces a private dump and verifies restoration into a fresh
database. It preserves existing databases and does not overwrite prior backups.
The November 7 presentation backup/restore succeeded: 19 table counts and the
private-attachment fingerprint matched the source database. The demo source had
no application attachments at that time; backend tests cover populated private
application workflows separately.
The Windows task `ThinkMedia local daily backup` is installed for 02:00 local
time (this workstation uses UTC+8, matching Asia/Manila). It runs under the
presenter's interactive Windows account with limited privileges and starts WSL
as needed. Its first manual execution completed with LastTaskResult 0. Windows
must be on and the user logged in; missed runs use StartWhenAvailable. Daily
runs create dumps without fresh restore databases; run the full backup command
periodically to verify restoration. Inspect with
`Get-ScheduledTaskInfo -TaskName 'ThinkMedia local daily backup'`.
The install script refuses to replace an existing task. No cloud scheduler is
configured. Backup deletion/rotation remains pending a retention decision.

`python -m ops.maintenance` from backend reports aggregate storage only with an
explicit local `DATABASE_URL` and `APP_ENV`. Its default performs no deletion.
`--prune-expired-sessions` removes expired login sessions transactionally.
Application records and status history remain retained. Attachment expiry uses
the separate [policy-controlled command](API_ATTACHMENT_RETENTION.md), with no
assumed period or enabled scheduler. Its bytes/tombstone/audit restoration was
verified using [two synthetic applications](../backend/reports/retention-restore-local.json).
The actual presentation database upgraded to0008 with seven accounts preserved,
zero expiry events, and a successful20-table backup/restore. Use fictional data
only in this presentation build.

Do not describe research metrics or live AI success as completed until the
corresponding actual run exists. Course consultations, participant recruitment,
LMS submission and team sign-off remain human deliverables.
