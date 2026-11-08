# SRS completion audit — November 8, 2026

The root `Requirements Software Engineering.docx` and bundled original still
match SHA256 `C3A07844558595B05867EDFC05211C53E99279CACAB3EE3E269006BC979A57F9`.
The latest cumulative PD7 requirements govern this audit. The owner selected a
local presentation using fictional data, with Gemini 3.8 Flash integration
prepared and no cloud deployment.

The local implementation is verified. Full research/live-provider completion
is not established: the remaining dependencies below require external inputs
or human decisions and cannot be replaced with generated observations.

## Current evidence

- `scripts/verify-local.sh`:237 backend tests passed171.21s, Alembic no drift,
  eight evaluation integrity tests passed11.764s against disposable PostgreSQL.
- Native Chrome browser suite:30 tests passed2.3min, including real role flows,
 360px/keyboard/axe checks, expiry recovery and normal private PDF download.
- Frontend TypeScript/Vite production build passed after final UI changes.
- `scripts/check-readiness.ps1` passed; actual restarted API reached ready with
  progress output, without treating a slow live process as a crash.
- [20-user benchmark](../backend/reports/performance-presentation.json):200 warm
  GETs, zero failures, p95 729.553ms on ten published listings/resources each.
- [Retention restore](../backend/reports/retention-restore-local.json):20 table
  counts, retained bytes, expired tombstone and audit match in a fresh database.
  A separate actual presentation backup/restore also passed; seven accounts and
  existing records remain, with zero presentation expiry events.
- Both [numerical fixture evaluation](../evaluation/DEMO.md) and
  [real offline BERTScore on six fixtures](../evaluation/SEMANTIC_DEMO.md) execute.
  They have zero real participants and do not prove research effectiveness.

## Functional requirements

| ID | Current evidence and limits |
|---|---|
| FR01 | Auth/CLI/role tests; separately provisioned admin; public admin assignment denied. All four local role logins checked through HTTP. |
| FR02 | Profile persistence, required-field validation and cross-user denial tests; company contacts and student background/location persist. |
| FR03 | Published-only learning, saves/reactions and immutable-key quiz scoring; backend and browser workflow checks. |
| FR04 | Active verified-company search/type/skill/location filters and detail; closed listings excluded; empty/error UI. |
| FR05 | Required bounded private PDF, duplicate protection, receipt/reference and tracker; authorized downloads and expiry recovery preserve history. |
| FR06 | Verified owner draft/edit/publish/close; ownership and unverified publication negative cases. |
| FR07 | Allowed decision transitions, actor/time history, final immutability, atomic rollback and cross-tenant denial. |
| FR08 | Eligible profile ranking, observed-rating neighbors with thresholds, truthful cold fallback; real effectiveness/alpha validation remains pending genuine data. |
| FR09 | Server-derived user/time and typed target interactions; optional strict numerical ratings, never inferred from missing values. |
| FR10 | Approved-only read-only retrieval plus bounded Gemini HTTPS adapter;35 simulated-provider cases. No successful live Gemini response is recorded yet. |
| FR11 | Company verification, resource publication/moderation and durable audits; policy-driven file expiry also audited with current scalar administrator-role checks. |
| FR12 | Leakage-controlled holdouts, baselines, grouped folds, warm temporal validation, CSAT and semantic pipelines. Synthetic computations work; genuine research and human factual review remain pending. External-mode CSAT storage is now migrated and tested. |

## Quality requirements

| ID | Current evidence and limits |
|---|---|
| NFR01 | Controlled warm synthetic benchmark meets the two-second target under its recorded GET workload. AI, uploads/writes and startup excluded; no pilot/production claim. |
| NFR02 | Hashed credentials/sessions, CSRF, roles/ownership, private files, bounds and parameterized SQL. Local presentation uses loopback HTTP; production TLS is outside the owner's local-only scope. |
| NFR03 | Fictional-data use notice, minimal projections and private resumes; application records never enter AI context. Real legal notice, retention period and verification evidence procedure need owner approval before a real-data pilot. |
| NFR04 | Actual PostgreSQL application/history and retention/audit rollback tests; unique application and concurrency checks. |
| NFR05 | Responsive360px/desktop, preserved valid inputs, clear receipts/errors and tested task recovery. |
| NFR06 | React/FastAPI/PostgreSQL modular monolith, contracts, migrations and real workflow tests; no framework replacement. |
| NFR07 | Daily user-scoped local backup task and restore checks. Windows must be on/user logged in; this is not an always-on production recovery guarantee. |
| NFR08 | Train-only fitting, common held-out baselines and validation-only alpha choice; real reference-set/human factual checks remain pending. |
| NFR09 | Labels, keyboard, visible focus, live status and automated scans in tested states. Real assistive-technology user evaluation is not established. |
| NFR10 | English, Manila dates, UTF-8 profile names and date conversion checks; no additional-language deployment is claimed. |
| NFR11 | Pagination, bounded public projections, upload/AI budgets and admin aggregate monitoring; explicit dry-run retention capability is implemented. No period is invented or automatic attachment expiry enabled. |

W01–W08 have working registration/profile, learning, discovery, application,
company, suggestion, guidance and administration screens respectively, exercised
by the role/browser workflows. Guidance has bounded conversation/retry and
citations; publication/verification have confirmation; expired files retain
application context. ADR01–03 retain the required stack, monolith and profile-first
ranking. ADR04 has an external adapter awaiting private runtime setup. ADR05 has
private storage/authorization and explicit retention. ADR06 remains local hosting
with Gemini selected; production cost/region/retention terms are not approved.

## Inputs that prevent full SRS sign-off

1. Configure a private Gemini API credential and positive provider budget, then
   obtain an actual source-backed live response and separate latency evidence.
   [Setup](AI_SETUP.md) is ready; no key may be invented or borrowed from agent login.
   The final authenticated operations snapshot reports `mode=retrieval`,
   `calls_used=0`, `call_budget=0`; both local web and API returned HTTP200.
   This confirms the current runtime cannot provide live Gemini answers yet.
2. Genuine ratings/CSAT observations, a human-reviewed fixed answer set and human
   factual checks are required for genuine research claims. The owner currently
   permits mock presentation data only, so those results stay unmeasured.
3. Before real users: approve retention/privacy/contact and company-verification
   procedures and conduct real assistive-technology/pilot assessment. Production
   hosting/TLS decisions are deferred by the explicit local presentation scope.

The local demo can be presented using its fictional accounts and resource lookup.
These remaining dependencies are not silently counted as completed requirements.

## Resumed verification — November 8, 2026

- The web/API processes were stopped. `scripts/present.ps1` restarted them and
  reported ready; all four fictional presentation roles then logged in through
  HTTP200 and logged out through HTTP204 with matching role/account identities.
- An authenticated `/admin/operations` request still reports assistant mode
  `retrieval`, zero calls and zero budget. A private configuration presence check
  confirms no application provider key is configured; no credential was printed.
- Native Chrome rendered the new 3D sign-in artwork at 1440x1000 and 360x800.
  Both loaded the intended asset with HTTP200 and had no horizontal overflow.
  Left-aligned framing now preserves the student and task objects on narrow
  screens (NFR05/09). The resulting TypeScript/Vite production build passed.
- The local daily backup task reports last-run result zero. The synthetic
  retention restore report linked above is included in Git so the published
  audit's evidence link resolves on a fresh checkout.

These are fresh startup/authentication/render/build checks. The full 237/30/8
test gates above describe the earlier complete runs and were not rerun for this
CSS framing correction. Genuine research reports remain `not_measured` and the
three external dependencies listed above still prevent full SRS sign-off.
