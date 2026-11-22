# ThinkMedia — verified local implementation

The current hosted-demo changes, requirement coverage, and remaining sign-off
conditions are documented in [the November 23 audit](REQUIREMENTS_COVERAGE_2026-11-23.md)
and [Render hosting](RENDER_HOSTING.md). The entries below retain their original
local verification dates and deployment scope.

DeepSeek’s existing FastAPI backend is preserved and extended. React/TypeScript
connects to actual FastAPI endpoints and PostgreSQL, using HttpOnly sessions and
CSRF. No functioning endpoint is replaced with frontend mock data. Clearly
labeled synthetic presentation records use their own local database; automated
tests and benchmarks use separate disposable databases.

## Current local presentation verification — November 8, 2026

The current Windows/WSL worktree passes **237 backend tests** (171.21s), **30
browser acceptance tests** in native Chrome (2.3min), **8 evaluation integrity
tests**, the production frontend build and Alembic schema drift validation.
Private local backup/restore matched all 20 table counts and the attachment
fingerprint. A user-scoped daily local backup task is installed and its first
manual execution returned result 0. The app and API both returned HTTP 200.

This pass adds bounded guidance conversation/retry, publication review and
confirmation, accessible custom-field errors, a fictional-data notice, a public
projection cache that excludes learner flags, aggregate maintenance/session
expiry tools, and a tested Gemini 3.8 Flash integration profile. The external
adapter has 35 simulated-provider tests; a live Gemini result awaits private key
configuration and an authorized smoke test. The original synthetic resource
lookup remains available in the prepared presentation runtime.

Administrators can inspect real aggregate API/storage/call-budget snapshots in
Audit history. Bounded counters retain route templates only, with no raw IDs,
queries or bodies. The current isolated warm 20-user benchmark measured 200 GETs,
zero failures and p95 **729.553 ms**; this is synthetic local evidence with the
conditions in [the report](../backend/reports/performance-presentation.json).
The real offline BERTScore implementation ran twice on six fixed synthetic QA
pairs, producing the same mean F1 **0.8282506466**; this is semantic similarity on
fixtures, not accuracy or research effectiveness. See
[semantic evaluation](../evaluation/SEMANTIC_DEMO.md). Human factual review is
explicitly pending. The launcher now tolerates slow cold imports, reports
progress and prevents duplicate starts; [startup evidence](STARTUP_DIAGNOSIS.md)
records the observed timeout and checks.

Attachment retention is now implemented as an explicit policy-controlled local
command with dry run by default. It expires bytes only for old, closed/final
applications with canonical history, preserves references/history, records a
transactional audit and serves authorized expiry as410. No actual presentation
file was expired. A separate synthetic restore smoke verified retained bytes,
an expired tombstone and its audit across all20 tables. Migrations0007–0008
preserve existing bytes and enable external-mode satisfaction feedback; they
refuse downgrades that would discard tombstones or external feedback. A real
retention period is still an operator/policy decision. See
[final SRS audit](FINAL_SRS_AUDIT.md) for evidence and unresolved dependencies.

The project owner explicitly selected local presentation with fictional data.
The [presentation guide](PRESENTATION_READINESS.md) documents startup, exact
verification commands, SRS coverage and outstanding human/pilot evidence.
[Synthetic evaluation](../evaluation/DEMO.md) executes the actual metric pipeline
on labeled generated fixtures; it is not research evidence. Genuine research
metrics, human factual review and real assistive-technology user testing remain
unmeasured. No cloud deployment or live personal-data processing was performed.

## Earlier verification

| Command/check | Verified result |
| --- | --- |
| Backend `TEST_DATABASE_URL=... .venv/bin/python -m pytest -q` | **114 passed**,70.87s; isolated authenticated local PostgreSQL18 |
| Frontend `npm run build` | passed; production bundle built |
| Frontend `npm test` with local Chromium libraries | **21 passed**, approximately1.4min; isolated API/database, responsive/collapsible navigation, illustrated sign-in, consumer discovery and role workflows |
| `python -m unittest evaluation.test_evaluation -v` | **8 passed**,25.753s; explicitly synthetic integrity fixtures |
| `alembic check` | no new upgrade operations |
| `python -m compileall -q app ops` and `pip check` | passed; no broken requirements |
|20-user local benchmark |200 measured authenticated GETs, zero failures, p95 **489.943ms**; warm synthetic workload |
| Private backup/restore |0600dump, fresh isolated restore, schema, private attachment bytes and all19table row counts match |

Detailed evidence: [backend audit](../backend/reports/codex-audit.md), [marketplace](../backend/reports/phase2.md), [learning](../backend/reports/phase3.md), [recommendations](../backend/reports/phase4.md), [performance conditions](../backend/reports/performance-local.json), [restore result](../backend/reports/restore-local.json), and [current API schema](../backend/reports/current.openapi.json).

## Requirement coverage

| Requirement | Implemented behavior/evidence |
| --- | --- |
| FR01–02 | Student/instructor/company registration; separately provisioned administrators; secure sign-in/out; persisted role-specific profiles, company contacts and student background/location. Cross-user access and mass assignment rejected. |
| FR03 | Published-only learning feed/search/topics; explicit saves/reactions; immutable quiz keys hidden from learners; stored answer-key scoring. |
| FR04 | Published verified-company opportunity search/filter/detail and public company information; closed/unavailable items excluded from discovery. |
| FR05 | Required validated PDF<=5MiB, private transactional PostgreSQL storage, unique student/listing application, receipt/reference and tracker/history. |
| FR06–07 | Verified-owner draft/edit/publish/close; own-applicant review; allowed final transitions; atomic actor/time/status history. |
| FR08–09 | Actual TF-IDF/profile ranking; truthful recency/activity fallback; observed-rating neighbor component with thresholds; alpha1 until genuine validation; typed actual interactions and optional strict1–5 ratings. Suggestions embedded in learning/opportunity discovery and a dedicated workspace. |
| FR10 | Read-only approved-resource retrieval, citations, uncertainty, rate limits and provider-unavailable recovery. Gemini 3.8 Flash adapter is implemented and tested with simulated responses; live verification awaits private configuration. |
| FR11 | Company verification, content publication/archive, report resolution and privileged event/audit views. |
| FR12 | Optional authenticated guidance satisfaction intake; offline MAE/RMSE plus same-holdout baselines, cold-start grouped folds and warm-user chronological alpha validation, CSAT reporting and optional local BERTScore pipeline. Genuine research results remain not measured. |

Required negative tests cover cross-tenant access, unverified publication, duplicate applications, closed listings, unauthorized downloads, invalid/oversized uploads, transition/history rollback, concurrent duplicate/closure races and assistant unavailability.

## Quality and operational limits

NFR02–04/06: server-side roles/ownership, Argon2 passwords, private files, parameterized ORM, bounded bodies, versioned additive migrations and actual rollback tests. Tests require explicit TEST_DATABASE_URL; cleanup cannot fall back to application configuration.

NFR05/09/10: inspected360px/desktop captures, labeled controls, written status/error feedback, skip link, visible contrast-corrected focus, mobile inert/focus containment/Escape, reduced motion, English and Asia/Manila dates. Automated scans and keyboard checks passed; manual assistive-technology testing with real users remains pending.

NFR01/07: actual local load and restore evidence is documented in [operations](OPERATIONS.md). The load dataset is small and synthetic; uploads/writes/authentication setup/cold startup are outside the timed GET mix. The daily production backup job is not installed. Production hosting/TLS and scheduling remain unapproved.

NFR08: no pilot observations, respondent counts, MAE/RMSE, fold results or BERTScore have been invented. [Research report](../evaluation/reports/pending.json) explicitly records missing datasets. [Evaluation instructions](EVALUATION.md) explain input provenance and limitations.

NFR03/11: privacy notice/legal basis, retention/deletion schedule, company
evidence procedures and genuine participation must be agreed before a pilot.
Throttles and monitoring counters are process-local. Private responses use
no-store; bounded internal public-content projections exclude personal flags.
Aggregate API/storage usage is visible to administrators. Explicit local
maintenance can prune expired sessions. Policy-controlled attachment expiry is
implemented but requires an explicit period/reference, confirmation and current
administrator attribution. Backup rotation and a real-user policy remain
unapproved. No automatic application deletion is implemented.

## Decisions and execution

User approved the restrained green/light career-workspace direction and chose to keep external AI disabled with resource lookup. Intent and Impeccable informed implementation; Include informed accessibility checks. Independent source/visual review corrections were applied, with a ship verdict covering the scored contrast fix. Later final QA/documentation was completed directly after worker quota/server interruption; it is not represented as a new independent whole-product approval.

No custom team runner, external Antigravity/OpenCode worker, deployment, Git push, real message/email, production database mutation or live credential handling was used. Existing unrelated repository changes were preserved.

## Local MVP usability refinement

Intent and Impeccable were already installed and were applied directly using the latest root requirements DOCX. Role homes now show actual work; URLs survive reload/Back; mobile users have frequent task navigation; application review shows the selected file and recipient before submission and retains edits; learning feed actions mutate real save/react endpoints. Statuses and labels are clearer. The final production build and 12-test browser/API suite passed; Impeccable detector returned no findings. An independent native Codex reviewer verified all three identified recovery defects resolved. [Detailed evidence](ux/thinkmedia-verification.md). Backend logic and local-only scope remain unchanged.

## Illustrated redesign requested by user

The supplied job-app references and palette now replace the earlier green identity. Original branded icons and an optimized transparent student illustration support rounded purple/pastel workspaces and a three-step first-use introduction, with skip, replay and storage-failure recovery. The final build passed, all 15 browser/API tests passed, and four focused post-polish regressions passed. The single Impeccable detector pass returned no findings; asset provenance and formatting checks passed. [Current evidence](ux/thinkmedia-illustrated-verification.md). Backend/security behavior and external-AI-off local MVP scope are preserved.

## Consumer mobile refinement and account

The student view now follows the supplied reference with prominent search, three illustrated categories, swipeable recent-opportunity cards, learning previews and real application tracking. Three new original graphics join the welcome character. A persistent local student account and clearly labeled demo opportunities/guides use actual PostgreSQL; browser and backend regressions use separate databases. Backend114 and browser16 tests passed. [Current consumer/mobile evidence](ux/thinkmedia-consumer-mobile-verification.md). Backend application authorization and migrations are preserved; test defaults/connection URL handling were corrected for the authenticated local test environment.

The final independent mobile review scored both search-copy and clipped-card-focus corrections resolved. Four focused post-fix browser tests passed21.7s, and the final production build passed34.15s. The user-facing demo remains separate from browser/backend test data.

## Collapsible shell and illustrated sign-in

The approved visual identity now has a collapsible persistent desktop rail, adaptive tablet/navigation behavior, mobile drawer scroll/focus recovery and workspace-width discovery columns. Sign-in uses original campus artwork beside the actual account form, with a compact illustrated phone header. The final production build and all 21 browser/API tests passed; the single detector returned no findings and five asset provenance checks passed. [Current UI verification](ux/thinkmedia-layout-signin-verification.md). Backend and user data were preserved.

The final independent review cleared the single sidebar tooltip finding after live pointer-travel, Escape and focus checks. The user-facing local API was restarted and both API health and frontend returned HTTP 200.
