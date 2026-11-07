# ThinkMedia backend — Phase 1 implementation report

Date: 2026-11-05
Owner: DeepSeek through OpenCode (backend write path only)
Scope source of truth: `.orchestrator/plan.md` Phase 1 contract
Status: **Phase 1 implementation complete and locally verified. Not committed, pushed, deployed, or approved for advancement.**

## 1. Delivered scope

Phase 1 foundation only: accounts, authentication/sessions, profiles, company verification, audit trail, migrations, security defaults, tests and documentation. No Phase 2 marketplace, listing, application, file-upload, feed or AI-assistant behavior was implemented.

### Endpoints (11 paths, matching the frozen contract)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness, minimal body, no infrastructure details |
| GET | `/api/v1/auth/csrf` | Bootstrap session-bound CSRF token, `Cache-Control: no-store` |
| POST | `/api/v1/auth/register` | Public registration (student/instructor/company), 201, no auto-login |
| POST | `/api/v1/auth/login` | Session rotation, generic invalid-credential error |
| GET | `/api/v1/auth/me` | Current profile envelope |
| POST | `/api/v1/auth/logout` | Revoke session, idempotent, CSRF required |
| GET | `/api/v1/profiles/me` | Own profile for any authenticated role |
| PATCH | `/api/v1/profiles/me` | Role-scoped profile edit, privileged fields rejected |
| GET | `/api/v1/admin/companies` | Admin review queue, status filter, bounded pagination |
| GET | `/api/v1/admin/companies/{company_id}` | Admin company detail |
| PATCH | `/api/v1/admin/companies/{company_id}/verification` | Atomic verify/reject + audit |
| GET | `/api/v1/admin/audit-events` | Newest-first audit list |

Generated evidence: `backend/reports/phase1.openapi.json` (11 paths, shared `ErrorEnvelope`, registration role enum limited to the three public roles).

### Code layout

- `backend/app/models/` — SQLAlchemy models for `users`, `student_profiles`, `company_profiles`, `instructor_profiles`, `sessions`, `audit_events`.
- `backend/app/schemas/` — Pydantic request/response contracts with `extra="forbid"`.
- `backend/app/repositories/` — persistence and locking primitives.
- `backend/app/services/` — auth, profile, administration (atomic verification + audit).
- `backend/app/api/routes/` — thin HTTP layer, no business logic.
- `backend/app/api/deps.py` — DB, CSRF, authentication, role and `require_verified_company` dependencies.
- `backend/app/core/` — settings, security (Argon2id, session tokens, CSRF HMAC), errors.
- `backend/app/cli.py` — `create-admin` only, hidden password prompt, no password CLI flag.
- `backend/alembic/versions/0001_phase1_foundation.py` — schema, constraints, role guards, reversible downgrade.
- `backend/tests/` — 75 PostgreSQL-backed tests.
- `backend/README.md`, `.env.example`, `.gitignore`, `requirements*.txt`, `requirements.lock`.

## 2. Security and data invariants implemented

- Passwords hashed with **Argon2id**; plaintext never stored, logged or returned.
- Opaque random session tokens stored only as SHA-256 hashes; `tm_session` cookie is `HttpOnly`, `SameSite=Lax`, `Path=/`, `Secure` outside explicit local HTTP mode, eight-hour absolute expiry.
- Session rotation on login; old session revoked; logout revokes and repeated logout is safe.
- CSRF token derived by HMAC from the session token hash plus `APP_CSRF_SECRET` (not persisted); rotation invalidates the old token. `POST`/`PATCH` require `X-CSRF-Token`; a present `Origin` must match the allowlist. A missing `Origin` is accepted for non-browser clients — documented in `README.md`.
- Email normalized (`strip().casefold()`), bounded to 254 characters, stored lowercase, unique (`CHECK (email = lower(email))` + unique constraint).
- Database `CHECK` constraints for role, status, display-name length, session expiry, audit action/status and one-profile-per-user; triggers prevent profile/role misclassification.
- Company verification: `SELECT … FOR UPDATE`, pending-only transitions, version increment, stale/repeated decisions return `409 VERIFICATION_CONFLICT`, update and audit insert commit in one transaction, audit failure rolls both back.
- Authorization re-reads the current actor role/verification state from the database on every protected request; service layer re-checks administrator role as defense in depth.
- `require_verified_company` reusable dependency reads current DB status; proven through an isolated test router. Unverified, rejected and wrong-role actors are denied with `403 COMPANY_NOT_VERIFIED` / `403 FORBIDDEN`.
- Uniform error envelope `{error:{code,message,fields,request_id}}` for validation, malformed JSON, 404, 405, 413, 429, 500; internal errors leak no trace or secret.
- Body size bounded; request IDs sanitized; auth throttles are configurable and testable (login: 5 failures per email+IP / 15 min; registration: 20 per IP / hour).
- Administrator created only through the local CLI with hidden password input; no default administrator, no public privilege escalation, administrator is outside the public registration enum.
- Secrets remain outside Git; only placeholder values exist in `backend/.env.example`.

## 3. Verification evidence

Environment: Python 3.14.4 (repo-local `backend/.venv`), PostgreSQL 18.6 on a disposable local instance at `127.0.0.1:55432`, database `thinkmedia_test`.

Commands were executed from `backend/`. Exit codes are the real shell exit codes.

| Command | Result | Exit code |
| --- | --- | --- |
| `DATABASE_URL=… .venv/bin/alembic upgrade head` | Migration applied, no errors | `0` |
| `DATABASE_URL=… .venv/bin/alembic check` | `No new upgrade operations detected.` | `0` |
| `TEST_DATABASE_URL=… .venv/bin/python -m pytest -q` | `75 passed in 13.67s` | `0` |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m compileall -q app` | No syntax errors | `0` |
| `.venv/bin/python -m app.cli --help` | Shows only `create-admin` | `0` |

Migration test additionally covers `upgrade → downgrade → upgrade` on the same disposable database.

### Test distribution (75 tests)

| File | Count | Focus |
| --- | --- | --- |
| `test_auth.py` | 21 | Registration, normalization, privilege mass assignment, login rotation, cookie flags, hashing, logout/revocation, expiry, CSRF/Origin, throttles, no default admin |
| `test_admin.py` | 11 | Role denial, service re-check, queue filtering/pagination, atomic audited decisions, reason validation, stale/repeated/concurrent conflicts, rollback on audit failure, current-DB role, newest-first audit |
| `test_constraints.py` | 10 | Real PostgreSQL `CHECK`/FK/unique/trigger enforcement, normalized emails, session and audit constraints |
| `test_profiles.py` | 10 | Persistence across sessions, role-scoped edits, forbidden fields, separate instructor storage, company validation, bounded skills, admin display-name-only, cross-user isolation, Unicode and Asia/Manila timestamps |
| `test_health_and_errors.py` | 10 | Minimal health, uniform envelopes for 404/405/413/422/500, request-ID handling, OpenAPI path surface |
| `test_cli.py` | 5 | Admin-only provisioning, duplicate rejection, hidden confirmation prompt, CLI surface without password argument |
| `test_verified_company.py` | 3 | Pending/rejected/wrong-role denial and current-state re-read |
| `test_migrations.py` | 1 | Upgrade/downgrade/re-upgrade |

### Required negative cases covered

- Cross-user/cross-tenant profile read and edit isolation.
- Non-administrator and unauthenticated access to every admin endpoint.
- Administrator self-registration and privileged-field mass assignment.
- Duplicate case-insensitive email and duplicate application-level registration.
- Unverified/rejected company denied by the publication-eligibility guard.
- Invalid, missing, wrong and replayed CSRF tokens, plus mismatched `Origin`.
- Stale version, repeated final transition and concurrent verification (exactly one winner).
- Injected audit-insert failure rolling back status and version.
- Expired and revoked sessions; logout invalidation and idempotence.
- Oversized bodies, malformed JSON, validation failures, hidden internal errors.
- Migration reversibility against real PostgreSQL.

## 4. Requirement coverage

| Requirement | Phase 1 contribution | Evidence |
| --- | --- | --- |
| FR01 — register/login/logout, server-enforced roles | Opaque sessions, Argon2id, server-side role/authorization, administrator not self-selectable | `test_auth.py`, `test_admin.py`, `test_cli.py` |
| FR02 — student/company profiles and validation | Student, instructor and company profiles with bounded, validated fields; private profile isolation | `test_profiles.py`, `test_constraints.py` |
| FR11 — company verification and privileged audit | Pending-only atomic verification with durable actor/time/reason audit; pending-company publication guard foundation | `test_admin.py`, `test_verified_company.py` |
| NFR02 — HTTPS/security/access control | Hashed passwords and sessions, parameterized ORM queries, server-side checks, secret-free errors, unauthorized-access tests | `test_auth.py`, `test_health_and_errors.py`, `README.md` |
| NFR03 — data minimization/privacy | Only necessary account/profile fields; no files or AI calls; placeholder-only secrets; retention/privacy flagged as pre-pilot decisions | Schema, `.env.example`, `README.md` |
| NFR04 — atomic history/rollback | Verification and audit commit atomically; rollback proven; version conflicts rejected | `test_admin.py` |
| NFR06 — separation, migrations, tests | Routers/schemas/services/repositories separated; Alembic migration; 75 real-DB tests | Layout, `test_migrations.py`, `test_constraints.py` |
| W01 — registration/profile and separately provisioned admin | Public registration for three roles, CLI-only administrator | `test_auth.py`, `test_cli.py` |

NFR01 (pilot latency at 20 concurrent users) and NFR11 (pagination/caching/upload bounds/expired-file cleanup) are only partially or not applicable in Phase 1; no performance or measurement results are claimed.

## 5. Documented limitations and pre-pilot decisions

These are honest gaps, not implemented assumptions:

1. **Auth throttles are in-process.** They are correct for verification and single-process local use; multi-instance deployments need a shared store. Documented in `README.md`.
2. **Missing `Origin` is accepted** for non-browser clients. Browser-origin allowlisting is enforced when the header is present.
3. **Privacy notice, retention schedule and real company-verification procedure** are not invented; they remain documented pre-pilot decisions owned by the project.
4. **No HTTPS termination, production secrets, backups or deployment** were configured; that is explicitly out of Phase 1 and requires approval.
5. **No Phase 2 behaviors** (listings, applications, files, assistant, recommendations) exist, so their negative tests are deferred by contract.
6. **No performance, availability or penetration testing** was executed; no measurements are fabricated.
7. `ruff` was used only as a local cleanup aid and is not part of `requirements.lock`; the committed toolchain is the pinned requirements plus pytest.

## 6. Change surface

Only `backend/` was created/modified by this work. Pre-existing modified/untracked files outside `backend/` (`.ai-team/`, `.orchestrator/`, `AGENTS.md`, `.gitignore`, etc.) were left untouched. No commit, push, deployment, production migration, real email/message or live credential handling was performed.
