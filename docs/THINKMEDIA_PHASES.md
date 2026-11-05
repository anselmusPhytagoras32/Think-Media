# ThinkMedia — ordered implementation workflow

**Execution**: `python3 thinkmedia_phases.py start` from the root of the existing repository. The launcher invokes the Codex supervisor for each phase, with Gemini and DeepSeek working concurrently where their assigned files do not overlap. Each phase requires a separate Sol plan + verification review. Continue with `python3 thinkmedia_phases.py resume` after interruption.

Always read `AGENTS.md` and `docs/THINKMEDIA_AGENT_BRIEF.md`. Document the linked requirement IDs in reports, tests and commit messages. API contracts must precede parallel implementation.

## Phase 1 — Foundation (B01, B02 foundation; FR01–02, FR11; NFR02–04, 06)

**Sol**: inspect existing tree and setup; confirm user role matrix, create the API contract and database schema responsibilities; avoid rewriting working app. Choose disjoint owned paths and define REST resources. Document any unanswered security/privacy design decisions.

**Gemini**: using Intent and Impeccable, build W01 role choice, registration/sign-in, role-specific profile screens, responsive navigation, loading/validation/error states, company verification banner, basic administrator verification screen. Use typed API mocks while backend is unfinished.

**DeepSeek**: implement PostgreSQL schema/migrations, FastAPI modular project structure, secure login/logout and hashed passwords, server-side RBAC, student/company profiles, separately provisioned administrator account, company verification service and audit log. Implement tests including unauthorized and cross-user access and unverified company blocked from publishing.

**Exit**: frontend builds; backend migrations/tests pass; accounts/profile and verification work end to end; no user self-assigns admin.

## Phase 2 — OJT marketplace (B02–B04; FR04–07; NFR03–04)

**Sol**: define listing/search/application/status APIs, attachment constraints, response errors (401/403/404/409), ownership rules, transaction boundaries and allowed state transitions before dispatch.

**Gemini**: build W03 opportunity search/filter and listing detail; W04 application form, attachment field, confirmation/receipt and status history; W05 verified company listing/create/edit/close/applicant-review dashboards, owner-only empty/error states. Closed listing disables Apply.

**DeepSeek**: listing lifecycle, published-only search, verified owner write checks, private upload/storage adapter with type/size validation, duplicate-proof application transaction, read-own application status/history, own-applicant review with allowed transitions and durable audit. Add positive and negative API/transaction tests.

**Exit**: verified company publishes; student finds/applies once with authorized private attachment; company can review/update; another student/company is denied; duplicate/closed/invalid submissions are blocked.

## Phase 3 — Learning and grounded assistant (B05, B07, B09; FR03, FR10–11)

**Sol**: define approved content search/retrieval and assistant provider adapter contract; ensure chatbot cannot read private applications or mutate system records; define budget cap/error behavior for any LLM provider.

**Gemini**: build W02 learning feed with published content/cards/topic filters, saves/react, quizzes, empty/loading/error states; W07 assistant chat with answer source links, uncertainty, provider-offline/retry states. Apply Intent and Impeccable again for this UI scope.

**DeepSeek**: admin publication/moderation and content APIs, quiz key scoring and interaction events, LLM provider abstraction with server-only credentials, approved-content retrieval/citations, input/output validation, graceful timeout/rate limits. Add disabled/mock provider for local testing; do not pass resumes or private applications to LLM.

**Exit**: published feed works, unpublished content hidden, quizzes score correctly, assistant cites approved content and cannot access or change private application data; provider unavailable leaves marketplace operational.

## Phase 4 — Hybrid recommendations and feedback (B06, B08; FR08–09)

**Sol**: specify cold-start assumptions, content features, collaborative inputs, eligibility filtering, score normalization and evaluate/test interfaces. Define reference data requirements without inventing data.

**Gemini**: build W06 recommendations, reason-label display ('based on skills/interests'), profile-edit CTA, feedback/rating UI where consented, fallback when personalization unavailable; integrate into feed and OJT listings.

**DeepSeek**: content/profile-based ranking, verified/active eligibility filter, interaction logging, optional explicit ratings. Add collaborative component when enough real interaction data exists; use `score = alpha * contentScore + (1-alpha) * collaborativeScore`, choose alpha from validation and alpha=1 for cold start. Do not treat missing ratings as numeric zero or infer fabricated explicit feedback. Test deterministic ranking, eligibility and cold start.

**Exit**: students get valid, explainable recommendations and captured feedback; no closed listing; cold start gracefully uses profile or popularity fallback; API and UI connect.

## Phase 5 — Research evaluation, cross-cutting QA, pilot readiness (B10/FR12 + all NFRs)

**Sol**: audit all FR01–FR12 / NFR01–11 against existing implementation and actual test outputs. Assign targeted fixes only. Report missing real pilot data and remaining decisions as gaps, not accomplishments.

**Gemini**: complete responsive/accessibility audit (360px, keyboard/focus, screen-reader announcements), cross-role navigation and clear statuses, English and Asia/Manila display, performance-friendly pagination, polished state handling. Recheck Intent and Impeccable usage.

**DeepSeek**: test security/authorization, migrations, transactional rollback, performance benchmark p95 non-AI with 20 concurrent users; implement evaluation pipeline with reproducible held-out data, MAE/RMSE + baseline, k-fold only if sufficient data, BERTScore + reference set, real CSAT survey intake and reports with sample size. Daily database backups/restoration smoke test. Mark actual results 'not measured' until a genuine data collection run.

**Exit**: all must-have acceptance tests demonstrably pass or are explicitly listed as gaps; actual datasets/reports are evidence-based; documented local startup, privacy/retention TODOs, final demo flow and rollback plan.

## Restrictions on automatic advancement

- A phase only advances if Sol's independent review explicitly approves its verified test results.
- Stop for unresolved authorization failures, schema conflicts, inaccurate/missing provider access, manual/ethical research data collection needs, or dangerous production operations.
- Temporary agent quota limits pause **that agent** while the supervisor is alive. The five-hour wait is a fallback not a guarantee of restored access.
- Do not deploy publicly, run migrations against production, scrape third-party platforms, or send live emails without explicit user approval.
