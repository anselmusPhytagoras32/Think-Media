# ThinkMedia — repository agent instructions

These rules apply to GPT-6.1 Sol in Codex CLI and to all delegated coding workers in this repository.

## Canonical specification

Read `docs/THINKMEDIA_AGENT_BRIEF.md` and `docs/THINKMEDIA_PHASES.md` before planning or editing. The underlying source is the uploaded Software Engineering Requirements document (cumulative PD7, sections 1–7). If the source document is also copied to `docs/Requirements Software Engineering.docx`, treat its most recent cumulative sections as authoritative; do not substitute earlier draft requirements when they conflict.

## Stack and boundaries

- One repository, **React frontend + Python FastAPI backend + PostgreSQL** (modular monolith).
- No framework replacement or microservices without explicit user approval.
- Sol plans, defines contracts, coordinates workers, reviews integration and tests. Gemini through Antigravity implements UI/UX. DeepSeek through OpenCode implements APIs, database and ML integration.
- Frontend worker MUST locate, open, and use both installed **Intent** and **Impeccable** skills; missing skills are an explicit blocker, never a fake success.
- Each worker may read the entire repository, but may write only its paths assigned by Sol for the current phase. Treat lockfiles, migrations, shared schema files and API contracts as Sol-controlled until explicitly allocated. Concurrent edits to a file are forbidden.
- Maintain a shared API contract and use realistic typed response fixtures while backend work is in progress.
- Implement one phase at a time. The acceptance checks for a phase must pass before moving to the next.

## Non-negotiable product rules

- Roles: student, instructor, company, and separately provisioned administrator. Administrator privileges must never be self-assigned.
- Only verified company accounts can publish listings. Companies can change only their own listings and applications. Only students submit applications. Instructors cannot access private applications.
- Listings: Draft -> Published -> Closed. Applications: Submitted -> Under Review -> Accepted or Rejected (direct rejection allowed). Reject disallowed transitions and log actor/time/history.
- A student can apply only once to a given listing. Closed listings cannot accept applications. Application, attachment references and status history require transactional integrity and authorization checks.
- Files (resumes/requirements) must be private, validated, bounded in size and downloadable only by authorized parties. Never send private application data to the AI provider.
- Feed and AI assistant use approved/published resources. AI answers should cite their source material, admit uncertainty and fail gracefully without preventing application workflows. The assistant is read-only with respect to application decisions.
- Recommender starts with content/profile matching, uses collaborative signals when sufficient, excludes closed/unavailable items, and labels output as suggestions rather than hiring decisions.
- Do not invent measurements, pilot data, CSAT survey respondents, MAE/RMSE, k-fold results, or BERTScore. Produce reproducible scripts, reports and limitations; report pending evaluations honestly.
- Honor RA 10173 (Data Privacy Act), separation of concerns, hashed passwords, server-side authorization, parameterized queries, HTTPS, minimal retained data, secrets outside Git, daily backup/restore plan, and auditable privileged actions.
- No production deployment, destructive DB migrations, real emails/messages, Git push, or live credential handling without explicit approval.

## Required verification

- Every code change must link to FR01–FR12 and relevant NFRs where practical.
- Run actual project commands and report pass/fail with evidence, not only model claims.
- Include negative tests: cross-tenant access, unverified company, duplicate application, closed listing, unauthorized download, invalid upload, status transition rollback, assistant unavailable.
- Frontend: responsive down to 360px, readable status and errors, accessible labels/keyboard/focus, English text and Asia/Manila times.
- Backend: transactional workflows, migrations, role/ownership checks, evaluation scripts with held-out data and documented configuration.
- Prioritize completion of must-have requirements and genuine testing over speculative extras.

## Scope excluded by specification

Do not build native mobile apps, payments, full LMS, realtime user chat/video, automated hiring decisions, or automated social-platform scraping. Social media imports require separate terms-of-use and workflow approval.

## Agent failure/cooldown

If a worker encounters a **temporary provider rate/quota limit**, save session/checkpoints and suspend that worker for the configured five-hour fallback cooldown, allowing unrelated work to continue. API credits exhausted, authentication failures and context overflows are distinct; do not spin indefinitely or imply a five-hour wait fixes them. The persistent supervisor—not the LLM—owns retries.
