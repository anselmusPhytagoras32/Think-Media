# ThinkMedia requirements coverage

This audit uses the cumulative PD7 requirements summarized in
THINKMEDIA_AGENT_BRIEF.md and the subsequently approved instructor-authoring
workflow. The November 23 change authorizes a free online demonstration with
fictional data. Earlier local-only deployment decisions are historical.

## Functional requirements

| Requirement | Implementation and verification |
| --- | --- |
| FR01 | Registration, login, logout, secure sessions, server-controlled roles, and separately provisioned administrators. Auth, CLI, cross-user, and browser tests. Hosted bootstrap uses private runtime passwords and checks existing identities. |
| FR02 | Persistent student, instructor, and company profiles with validated fields. Profile tests and browser reload/login checks. |
| FR03 | Published Learning Library, search/tags, saves/reactions, scored quizzes, and post-submission feedback. Instructor-owned drafts support skill categories, links, PDFs, quizzes, revision feedback, resubmission, and administrator publication. |
| FR04 | Published active listings from verified companies, combined keyword/type/location/skill filtering, details, pagination, and empty/error handling. Marketplace and consumer browser tests. |
| FR05 | Private bounded PDF upload, single application per student/listing, reference and tracker, authorized download, attachment expiry metadata. Marketplace, constraint, concurrency, and retention tests. |
| FR06 | Verified companies create, edit, publish, and close their own listings. Server ownership and verification checks reject other actors. |
| FR07 | Submitted/Under Review/final decision workflow, actor/time history, locked transitions, and transactional rollback. Private applications remain limited to the student and owning company. |
| FR08 | Eligible profile-content ranking with collaborative signals above documented thresholds. Closed/unavailable candidates are excluded. Cold-start reasons describe the actual fallback. |
| FR09 | Server-derived interaction identity/time and optional strict 1–5 ratings. Repeated explicit ratings update the existing record. Missing ratings remain absent. |
| FR10 | Approved-only source retrieval, bounded context, read-only answers, citation validation, uncertainty, throttling, and recoverable provider errors. Groq GPT OSS 20B is primary, OpenRouter Nemotron 3.5 Super VL is fallback. Both share an attempt budget. Legacy Gemini/OpenAI profiles remain supported. |
| FR11 | Administrator company verification, learning publication, instructor review, content reports, durable decision history, and aggregate operations/audit views. |
| FR12 | Reproducible grouped holdouts, common baselines, MAE/RMSE, grouped folds, warm temporal validation, optional CSAT analysis, and offline BERTScore. Actual pilot measurements require genuine inputs and human review. |

## Quality requirements

| Requirement | Implementation and limits |
| --- | --- |
| NFR01 | Current warmed local synthetic benchmark: 20 distinct students, 200 GETs, zero failures, p95 764.759 ms against the 2,000 ms target. Windows Python 3.13.7/PostgreSQL 18.7, 10 listings and 13 resources; 80 warmup GETs excluded. AI, authentication setup, writes/uploads and cold startup were excluded. Free Render performance remains unmeasured. |
| NFR02 | Argon2 passwords, hashed opaque sessions, CSRF/Origin checks, server authorization, parameterized ORM, bounded inputs, private files, and secret-free source. Hosted service uses managed HTTPS and secure cookies. |
| NFR03 | Fictional-data notice, minimal response fields, and private application/PDF isolation from AI. Legal basis, real-user privacy notice, company-verification evidence, and retention periods require owner decisions before a real-data pilot. |
| NFR04 | PostgreSQL uniqueness, row locking, atomic application/status/audit writes, and rollback tests. Instructor publication and its review history commit together. |
| NFR05 | Working responsive forms, navigation, loading/empty/error states, and recovery down to 360 pixels. Full browser acceptance suite covers the main role workflows. |
| NFR06 | React/TypeScript, FastAPI, PostgreSQL, modular services, versioned migrations, contracts, and tests. Docker packages the existing monolith and serves one origin. |
| NFR07 | Dedicated hosted export, daily 02:00 UTC+8 workstation task, successful task result 0, and actual restoration into a new local database. All 22 public-table counts and two PDF SHA-256 fingerprints matched. The free PostgreSQL plan has no managed backup service. The workstation/user/network must be available; the proposed 24-hour recovery point cannot be guaranteed during outages. |
| NFR08 | Training-only fitting, held-out baselines, validation-only weight selection, provenance hashes, and honest missing-data reports. Synthetic functional checks provide no pilot effectiveness estimate. |
| NFR09 | Labels, keyboard navigation, visible focus, mobile drawer containment, status announcements, and automated axe checks. Real assistive-technology user evaluation remains pending. |
| NFR10 | English interface, Unicode support, and Asia/Manila date formatting. |
| NFR11 | Paginated data, bounded public projections, PDF and request caps, provider attempt budgets, throttles, aggregate metrics, and explicit policy-based attachment cleanup. Retention is activated only with an approved period. |

## Verification evidence

The production TypeScript/Vite build passed. All 51 browser acceptance tests
passed in 3.7 minutes using installed Edge against an isolated local API and
PostgreSQL database. The new hosting/provider subset passed 41 tests.

The complete backend suite passed **266 tests in 385.94 seconds**. An additional
instructor-publication rollback test, added after that collection, passed
separately in 1.99 seconds: **267 backend checks across the two runs**. The
41-test hosting/provider subset overlaps the complete suite and is not added to
that total. All **eight evaluation integrity tests** passed. Alembic reported
no new upgrade operations. The Windows dependency lock installs successfully
with uvloop excluded on Windows; the runtime Docker build passed on Render.

The deployed HTTPS app passed **38 HTTP checks**: all four demo-role logins,
profile reads, authorization denial, prepared lessons and drafts, PDF integrity,
quiz scoring/feedback, suggestions, instructor skill creation, and logout. Both
configured providers returned independently validated source-cited answers to a
generic OJT résumé question with public guide context. No private application,
profile or PDF data was included. Shared-budget failover was tested with mocked
provider failure; no live outage was induced.

An isolated Edge browser also verified the hosted instructor materials page,
completed the new-browser introduction, opened the skill editor, and checked
360-pixel containment. Desktop and mobile screenshots were visually inspected
with transitions disabled, matching the local suite's reduced-motion setting.

The application is live at https://thinkmedia-demo-m74t.onrender.com.
The initial deployed commit was `f6ed08e`. Runtime secrets and generated demo
passwords are outside Git. The source OpenAPI contract was regenerated to
include instructor authoring and review endpoints. PDF Git attributes preserve
the sample's exact bytes across Windows and Linux checkouts.

Commands used, after setting private database/runtime variables to the
appropriate isolated targets:

```text
backend: python -m pytest -q --junitxml=../.local/hosting-backend.xml
backend: python -m pytest tests/test_hosting.py tests/test_external_assistant.py -q
backend: python -m pytest tests/test_learning_submissions.py::test_publication_audit_failure_rolls_back_review_and_published_content -q
backend: python -m alembic check
root:    python -m unittest evaluation.test_evaluation -q
frontend: npm run build
frontend: npm test -- --reporter=list,junit
backend: python -m ops.benchmark --base-url http://127.0.0.1:8004 --concurrency 20 --requests 200 --output ../.local/hosting-benchmark.json
root:    powershell -File scripts/backup-render.ps1
```

Browser configuration: `PLAYWRIGHT_CHANNEL=msedge`,
`PLAYWRIGHT_API_TARGET=http://127.0.0.1:8003`, and
`PLAYWRIGHT_BASE_URL=http://127.0.0.1:5175`. The browser API used retrieval mode
and its own disposable database; it made no external provider calls. Backend
tests used a separate database. Benchmark fixtures used a newly restored,
disposable local database. No automated test cleanup targeted the hosted app.

Private JUnit, HTTP smoke, benchmark, and restore reports reside in ignored
`.local` state. The public [verification record](../backend/reports/hosting-verification-2026-11-23.json)
contains aggregate evidence only. Earlier dated QA reports remain historical.

## Remaining completion conditions

Genuine ratings, consented CSAT observations, a fixed reviewed reference-answer
set, human factual assessment, and real assistive-technology evaluation remain
external requirements. A free online demo also retains service sleep,
shared-instance capacity, database expiry, and backup-availability limits.
Those constraints prevent an unconditional production or pilot sign-off.
