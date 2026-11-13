# ThinkMedia QA and presentation acceptance — November 13, 2026

## Verdict and specification

The local fictional-data presentation passes the functional, browser and recovery
checks below. A later authorized Gemini 3.5 Flash-Lite test also returned a live
source-backed answer. Full SRS sign-off remains pending genuine research
observations, human factual review, and the decisions required before a real-user pilot.

Authority: latest cumulative PD7 sections 1–7 in `Requirements Software Engineering.docx`.
The root document and `.ai-team/spec/ThinkMedia_Original_SRS.docx` both have SHA256
`C3A07844558595B05867EDFC05211C53E99279CACAB3EE3E269006BC979A57F9`.
The requirements in tables 89–98 govern this review; earlier drafts do not override them.

## Fresh execution evidence

| Check | Actual result |
|---|---|
| `wsl -d Ubuntu -- bash scripts/verify-local.sh` | 237 backend tests passed in 141.57s; Alembic reports no new upgrade operations; 8 evaluation tests passed in 18.907s |
| `npm.cmd run build` in `frontend` | TypeScript/Vite production build passed after the footer change; JS 371.99 kB / gzip 106.18 kB |
| Playwright against isolated API 8001 / web 5174, installed Chrome | Final run: 39 passed in 121.053s; zero skipped, unexpected or flaky tests |
| `scripts/check-readiness.ps1` | Passed delayed readiness, timeout, reuse, identity and duplicate-launch checks |
| `scripts/present.ps1` | Existing presentation app ready at `http://127.0.0.1:5173` |
| `scripts/check-presentation.py` | Student, instructor, company and administrator: login 200, matching identity/role, logout 204 |
| Impeccable detector over three changed UI files | Exit 0, findings `[]` |
| `scripts/backup-local.sh` | Fresh private dump restored into a new database; all 20 table counts, attachment bytes and states matched; no existing DB overwritten |
| Daily Windows backup task | Last checked run November 13, result 0; next run November 14 at 02:00 Manila |
| Synthetic retained/expired attachment restore | Passed with 2 applications, 1 retained file, 1 expired file and preserved history/audit; [report](../backend/reports/retention-restore-local.json) |
| `scripts/benchmark-current.sh` | 20 concurrent users, 200 warmed requests, p95 518.21ms, zero failures; two-second target met for the recorded synthetic non-AI GET workload |
| `evaluation/demo.py` | Passed: 100 synthetic rating rows, 5 grouped folds, warm temporal validation; zero real participants |
| `python evaluation/semantic_demo.py` | Actual offline BERTScore completed on 6 fixed synthetic pairs; no provider calls, human review pending |
| `evaluation/run.py` without supplied datasets | Genuine recommender, CSAT and assistant results remain `not_measured`; [report](../evaluation/reports/pending.json) |

The final browser machine report is `.local/qa-20261113-browser-final.json`.
Local screenshots under `.impeccable/review/` were refreshed by the suite; sign-in
at 360/1440px, mobile learning and company listing closure were also visually inspected.
These are Chrome emulated viewports, not physical-device or human screen-reader trials.

## Changes and failures resolved

- Removed the shared disclaimer dropdown and its separator/spacing from every
  signed-in page. Registration retains visible, non-collapsible data-use text
  for W01/NFR03. The existing profile regression checks that the footer is absent;
  sign-in coverage verifies registration privacy text remains visible.
- The initial completed browser run had 33 passes and 6 failures. DOM evidence
  confirmed stale tests expected the former “Welcome back.” title, a now-hidden
  registration tab, and a Guidance navigation link. The existing app uses “Login
  to your account”, “Create an account”, and a floating Guidance panel.
- Updated those tests to exercise the current visible controls. The More check
  opens Guidance, closes it with Escape, and checks focus returns. No assertion
  was replaced with a skip; the complete final 39-test run passed.
- An interrupted run lost its test services. Restarted the isolated API and
  reran the suites to completion; partial runs are not counted as passes.

## Functional requirement coverage

| ID | Evidence and acceptance status |
|---|---|
| FR01 | Pass: real registration/login/logout, CSRF/session checks, role denials and administrator self-assignment rejection (`test_auth.py`, browser foundation/API tests). |
| FR02 | Pass: persisted role-specific profiles, field validation, Unicode and cross-user privacy (`test_profiles.py`, browser foundation/profile checks). |
| FR03 | Pass: published-only resources, search/topics, saves/reactions and quiz answer-key scoring; real learner-to-admin moderation flow (`test_learning.py`, browser learning tests). |
| FR04 | Pass: active published opportunity search, combined type/skill/location filters, details, URL persistence and empty states (marketplace/consumer/opportunity browser tests). |
| FR05 | Pass: required valid private PDF, confirmation, reference, tracking/history, duplicate/closed protection and authorized downloads (`test_marketplace.py`, attachment and marketplace browser tests). |
| FR06 | Pass: verified owner creates/edits/publishes/closes; other owners and unverified companies denied (`test_verified_company.py`, marketplace tests). |
| FR07 | Pass: owning company reviews; allowed transitions, final-state protection, actor/time history and transactional rollback; real browser acceptance flow. |
| FR08 | Implementation pass: eligible deterministic profile ranking, real observed-rating hybrid inputs and cold fallback (`test_recommendations.py`). Genuine effectiveness and validated weighting remain pending participant data. |
| FR09 | Pass: valid typed interactions, server-derived user/time and optional explicit ratings; missing ratings are not fabricated (`test_recommendations.py`). |
| FR10 | Live smoke pass with Gemini 3.5 Flash-Lite: app HTTP 200, external answer, one approved source resolving successfully, 9,900.4ms latency. Earlier Gemini 3.8 attempts failed with high demand. Approved-only/read-only boundaries and failure recovery also have automated coverage; human factual evaluation remains pending. |
| FR11 | Pass: administrator verification/publication/report review, role restrictions, confirmations, durable audit and rollback (`test_admin.py`, `test_learning.py`, browser administration). |
| FR12 | Pipeline pass, research pending: held-out/common-baseline MAE/RMSE, grouped folds, temporal validation, CSAT and semantic pipeline exist. No genuine ratings, CSAT responses or human-reviewed reference answers were supplied; no research effectiveness claim is justified. |

## Quality requirement coverage

| ID | Evidence and acceptance status |
|---|---|
| NFR01 | See fresh benchmark result below; synthetic warmed non-AI GET workload only. A separate live AI smoke request took 9,900.4ms; one observation does not establish a latency distribution. |
| NFR02 | Local security checks pass: password/session hashing, CSRF, server roles/ownership, bounded requests, parameterized persistence and private downloads. Presentation remains loopback HTTP; production HTTPS is not verified. |
| NFR03 | Registration data-use notice and private application/AI boundaries verified. Real-user privacy/contact, retention and company-verification evidence procedures still require owner decisions. |
| NFR04 | Pass: actual PostgreSQL duplicate/concurrent submission, history integrity, status rollback and retention rollback tests. |
| NFR05 | Pass in tested states: 360px through desktop, registration/application input preservation, readable errors, keyboard/drawer/navigation checks. |
| NFR06 | Pass: required React/FastAPI/PostgreSQL modular monolith, module boundaries, versioned migrations, no schema drift and core workflow tests. |
| NFR07 | Local pass: actual fresh backup restoration and attachment-state verification; daily task result 0. Workstation must be on and user logged in; no always-on production recovery claim. |
| NFR08 | Implementation pass: split-before-fitting, same held-out baselines and validation-only weight selection verified by 8 integrity tests. Genuine dataset provenance and human factual assessment remain pending. |
| NFR09 | Automated pass in tested states: axe scans, semantic labels, visible keyboard/focus behavior, announcements and error focus. Human assistive-technology assessment remains pending. |
| NFR10 | Pass: English document/UI, UTF-8 profile tests and Asia/Manila formatting. Additional language translations are not implemented or claimed. |
| NFR11 | Pass for implemented mechanisms: pagination/cache, upload/AI bounds, aggregate operations and audited explicit expiry. Automatic real-data expiry and backup rotation await an approved retention policy. |

W01–W08 are exercised by registration/profile, learning, opportunity, application,
company, suggestions, Guidance and administration tests. UC01–UC08 map to the
same workflow coverage. ADR01–03/05 retain the prescribed architecture, profile-first
ranking and private storage. ADR04's external adapter lacks a live acceptance run;
ADR06's production hosting/provider terms remain undecided. Document export,
LMS submission, consultations, participant recruitment and team sign-off are human
course deliverables and cannot be established by app tests.

## Presentation use and remaining sign-off

Open `RUN_THINKMEDIA.cmd`; use the four presentation accounts described in
[the presentation runbook](PRESENTATION_READINESS.md). Their existing passwords
remain in the ignored local manifest. Use `presentation/fictional-resume.pdf`.
Follow the runbook's verification → publish → apply → review → learning →
suggestions → Guidance sequence. The pending company permits showing actual
verification; confirm its state before rehearsal if an earlier demonstration changed it.

Describe Guidance as approved-resource lookup. Demonstrate numerical/semantic
evaluations only as fixture-based pipeline execution, with zero real respondents.
Do not describe this as full paper compliance or a real-user production release.

Full sign-off needs:

1. Genuine consented ratings/CSAT and fixed candidate/reference answers, then
   actual held-out evaluations and separate human factual review.
2. Approved privacy, retention/deletion and verification procedures before real
   personal data; human accessibility/pilot assessment and HTTPS/hosting before
   deployment.

## Performance and semantic conditions

The [fresh performance report](../backend/reports/performance-presentation.json)
records 24 synthetic accounts, 10 listings and 10 resources, 80 warmup requests,
then 200 measured GETs across profile, listings, content and recommendations.
With 20 concurrent users, p95 was 518.21ms and maximum latency 646.231ms, with
zero failures. This meets the 2,000ms target for that warmed local workload.
AI, uploads, application/status writes, cold starts and a real-user pilot are
outside that measurement. Backend tests and browser/semantic runs finished
before the performance run started.

The offline semantic rerun used the existing pinned local DistilBERT assets,
6 layers, CPU, IDF disabled and no baseline rescaling. Mean precision was
0.8384666443, recall 0.8194179535 and F1 0.8282506466 on the six fixed synthetic
pairs. These values demonstrate pipeline execution, not factual accuracy or
research effectiveness. Human factual review remains pending. See
[the semantic protocol](../evaluation/SEMANTIC_DEMO.md) and
`evaluation/reports/semantic-synthetic-demo.json` for hashes/configuration.

The first native semantic attempt encountered a sandbox file-read denial;
the permitted rerun completed without downloading assets. The source and restore
fixture databases created by verification were preserved for inspection.

## Authorized live AI check — November 13, 23:01 Manila

The owner supplied `backend/.env.local` and explicitly authorized a live test.
The presentation backend was restarted and confirmed external mode, a present
private key and a 25-attempt process budget. No key or raw provider body was
printed or included in this report.

Two source-grounded app requests returned HTTP 503 / `ASSISTANT_UNAVAILABLE`
in 8,842.01ms and 4,591.24ms, respectively. A separate bounded diagnostic request
returned HTTP 503 directly from the configured provider. Three live attempts
were made in total; the running app reports two consumed attempts because the
diagnostic used its own process. No successful answer, citation validation or
key validity is established by these failed requests. No automatic retry loop
or configuration-limit increase was introduced.

Listings returned HTTP 200 after both app failures. Local diagnostic artifacts
are `.local/live-ai-result.json` and `.local/live-ai-diagnostic.json`; neither
contains the credential. The earlier presentation instruction to describe
resource lookup applies to retrieval mode; the current external mode instead
shows its recoverable unavailable state while the provider is failing.

### Direct dotenv/provider follow-up

At the owner's request, `backend/.env.local` was parsed directly with credentials
redacted. It has no duplicate setting names or key whitespace. The configured
`models/gemini-3.8-flash` appears in the authenticated provider model inventory:
the inventory request returned HTTP 200 and listed 64 models. This establishes
successful model-list authentication, not successful answer generation.

The provider's generation response contains an array-wrapped error with
`code=503`, `status=UNAVAILABLE`, and message: “This model is currently experiencing
high demand. Spikes in demand are usually temporary. Please try again later.”
A diagnostic using the short ID `gemini-3.8-flash` returned the same high-demand
error. This identifies provider capacity as the observed cause; no working
source-backed live answer is claimed. The model and private credential were not
changed. `.local/live-ai-model-inventory.json` retains the redacted inventory result.

## Successful Flash-Lite live test — November 13, 23:13 Manila

The owner authorized switching to `gemini-3.5-flash-lite` and testing again.
Only the private model setting was changed, and the presentation backend was
restarted. The actual authenticated student-to-app request returned HTTP 200
with `mode=external`, a nonempty answer and one source citation. Its cited
approved learning resource resolved successfully. The app's external call count
increased from 0 to 1 of 25; listings still returned HTTP 200 afterward.

Measured request latency was 9,900.4ms, including the smoke script's CSRF
bootstrap. This is one successful run, not an availability guarantee, p95
measurement, or human factual assessment. No research score is inferred.
The [credential-free live evidence](../backend/reports/live-ai-presentation.json)
records the result. The current runtime uses live Flash-Lite; the earlier
resource-lookup presentation instructions describe the previous retrieval mode.
