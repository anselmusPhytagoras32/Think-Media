# ThinkMedia backend — current implementation

The preserved foundation now also includes marketplace/private applications, learning and moderation, recommendations/feedback, approved-resource guidance and optional CSAT. [Current verified results](../docs/IMPLEMENTATION_STATUS.md), [API schema](reports/current.openapi.json), [operations](../docs/OPERATIONS.md) and [research evaluation](../docs/EVALUATION.md) describe the delivered scope and genuine limits.

Use Python 3.12+ and the pinned requirements.lock. `APP_ASSISTANT_MODE=disabled` is the safe code default. For approved-resource lookup without any external provider, explicitly set `APP_ASSISTANT_MODE=retrieval` when starting the API. No API key or external call is used. Tests require explicit `TEST_DATABASE_URL` and a separate disposable PostgreSQL database.

`POST /api/v1/feedback/csat` accepts only an authenticated, CSRF-protected strict integer rating 1–5. It stores one latest satisfaction response per user, server-derived mode and timestamp, without conversation text. Other relevant API groups are detailed below and in current.openapi.json.

## Foundation setup and API reference

# ThinkMedia backend — Phase 1

FastAPI modular monolith for accounts, role-specific profiles, company
verification and the privileged-action audit trail. Phase 1 scope is FR01–FR02,
the relevant part of FR11, and NFR02/03/04/06. Marketplace listings,
applications, learning content, recommendations and the AI assistant are **not**
implemented yet.

- Python 3.12+ (verified on 3.14.4; pinned NumPy/SciPy require 3.12+)
- FastAPI + SQLAlchemy 2 + Alembic
- PostgreSQL (verified on 18.6; `gen_random_uuid()` requires PostgreSQL 13+)
- Argon2id password hashes, opaque hashed sessions, session-bound CSRF

## Layout

```
backend/
  app/
    api/routes/        auth, profiles, admin routes
    api/deps.py        DB session, CSRF, current user, RBAC dependencies
    models/            users, student/instructor/company profiles, sessions, audit
    repositories/      parameterized data access
    schemas/           strict request/response models (unknown fields rejected)
    services/          accounts, profiles, administration, verification guard
    security/          Argon2id, opaque tokens, cookies, throttles
    config.py          environment settings (no secrets committed)
    errors.py          uniform error envelope + handlers
    cli.py             local administrator provisioning
    main.py            application factory
  alembic/             versioned schema migrations
  tests/               real-PostgreSQL API, constraint, migration and concurrency tests
  reports/phase1.md    commands, exit codes and requirement coverage
```

## Local setup

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.lock      # full dev/test lock

cp .env.example .env
# Edit DATABASE_URL and APP_CSRF_SECRET. .env is git-ignored.

createdb thinkmedia
export DATABASE_URL="postgresql+psycopg://thinkmedia:REPLACE_WITH_LOCAL_PASSWORD@localhost:5432/thinkmedia"
alembic upgrade head

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`APP_ENV=local` (the default) is the **explicit local HTTP mode**: the session
cookie is not marked `Secure`. For `APP_ENV=production` (or any environment other
than `local`/`test`/`development`), `Secure` is enabled unless
`APP_COOKIE_SECURE` overrides it. Terminate TLS in front of the app.

The React frontend is served same-origin (or through the Vite development proxy);
the API intentionally does not enable wildcard CORS.

## Administrator provisioning (no default account)

Administrators are created **only** by a local command with hidden password
entry. There is no HTTP registration or elevation path for administrators.

```bash
cd backend
export DATABASE_URL="postgresql+psycopg://.../thinkmedia"
python -m app.cli create-admin \
  --email admin@example.org \
  --display-name "Site Administrator"
# Prompts: "Administrator password:" and "Confirm administrator password:"
```

The command:
- reads the password with `getpass` (never a CLI argument, never echoed);
- validates email/display name/password with the same rules as registration;
- refuses duplicates (exit 1) and invalid input (exit 2);
- creates the account with `role=administrator` and no role-specific profile.

## API (base `/api/v1`)

| Method | Path | Notes |
|---|---|---|
| GET | `/health` (root, not `/api/v1`) | `{"status":"ok"}` only |
| GET | `/auth/csrf` | bootstraps/reuses a session; returns `csrf_token`; `no-store` |
| POST | `/auth/register` | 201 profile envelope; creates account atomically; does not sign in |
| POST | `/auth/login` | rotates session; sets `tm_session`; 401 generic on bad credentials |
| GET | `/auth/me` | current profile envelope or 401 |
| POST | `/auth/logout` | 204; revokes session; idempotent with a revoked cookie |
| GET | `/profiles/me` | own profile only |
| PATCH | `/profiles/me` | role-specific editable fields; at least one required |
| GET | `/admin/companies` | admin only; default `status=pending`; stable `created_at,id` order |
| GET | `/admin/companies/{company_id}` | admin only |
| PATCH | `/admin/companies/{company_id}/verification` | `verified`/`rejected`, reason, `expected_version` |
| GET | `/admin/audit-events` | admin only; newest first |

Every POST/PATCH requires `X-CSRF-Token` from `GET /auth/csrf` and (when an
`Origin` header is present) an allow-listed origin. A missing `Origin` is
accepted for non-browser clients, which do not carry ambient cross-site
credentials; browser `fetch`/XHR sends `Origin` and is checked.

Errors are always:

```json
{"error":{"code":"VALIDATION_ERROR","message":"...","fields":{"field":["..."]},"request_id":"..."}}
```

with `X-Request-ID` echoed on the response. Status/code mapping follows the
Phase 1 contract (`401`, `403`, `404`, `409`, `422`, `429`, `500`); `413`
`PAYLOAD_TOO_LARGE` and `405` `METHOD_NOT_ALLOWED` are documented extensions for
bounded input and unsupported methods.

## Security defaults (implementation defaults, not pilot policy)

- **Passwords**: Argon2id (`time_cost=3`, `memory_cost=65536 KiB`,
  `parallelism=4`, 32-byte hash, 16-byte salt), 12–128 characters, never
  trimmed, never returned.
- **Sessions**: 256-bit opaque cookie value; only its SHA-256 hash is stored.
  Cookie `tm_session` is `HttpOnly`, `SameSite=Lax`, `Path=/`, absolute 8-hour
  expiry, `Secure` outside local/test. Login revokes the prior session and
  issues a new one; logout revokes.
- **CSRF**: derived HMAC token bound to the session hash. A fresh token must be
  fetched after login. `APP_CSRF_SECRET` must be shared by all workers in a
  multi-process deployment.
- **Email**: trimmed + case-folded before storage; `CHECK (email = lower(email))`
  plus a unique constraint make normalized uniqueness enforceable in PostgreSQL.
- **RBAC**: every request re-loads the user and role from PostgreSQL. Profiles
  are self-only; there is no profile-by-ID route. Administrator checks are
  server-side.
- **Verification**: `SELECT ... FOR UPDATE` locks the company row; only
  `pending -> verified|rejected` is allowed; the status/version update and the
  audit insert commit in one transaction. Stale versions and repeated/final
  decisions return `409 VERIFICATION_CONFLICT`; an audit insert failure rolls
  both back.
- **Verified-company foundation**: `app.services.verification.ensure_verified_company`
  and `app.api.deps.require_verified_company` re-read the stored company status
  on every call. Phase 2 write endpoints must depend on them.
- **Bounded input**: strict Pydantic schemas (unknown fields rejected), length
  limits, and a 64 KiB request-body cap.
- **Throttles**: login 5 failures per email+IP per 15 minutes; registration 20
  attempts per IP per hour. `429` includes `Retry-After`. Both limits are
  configurable and tested with an injectable clock.
- **Secrets**: read from environment/`.env`; only placeholders are in
  `.env.example`. No password, session token, CSRF token or database URL is
  logged or returned.

## Database invariants

- `users.role ∈ {student, instructor, company, administrator}`.
- `company_profiles.verification_status ∈ {pending, verified, rejected}`;
  defaults to `pending`, `verification_version` starts at 1.
- Foreign keys on every profile/session/audit actor; company profile is one per
  user.
- Instructors are stored in `instructor_profiles`, **never** in
  `student_profiles`. PostgreSQL triggers also reject a profile row whose
  `user_id` role does not match that profile table.
- `audit_events.actor_id` uses `ON DELETE RESTRICT`; there is no API that
  updates or deletes audit records.

## Tests

Tests require an explicit `TEST_DATABASE_URL` pointing to a disposable database;
`DATABASE_URL` is never used by destructive test cleanup. Tests run against a
**real PostgreSQL database** and apply the real Alembic
migration. Create a disposable database first:

```bash
createdb thinkmedia_test
cd backend
export TEST_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/thinkmedia_test"
python -m pytest
```

The migration test creates and drops its own temporary database, so the
configured role needs `CREATEDB`. It verifies upgrade → downgrade to base →
upgrade again, constraint/trigger names and table removal.

Useful checks:

```bash
DATABASE_URL="$TEST_DATABASE_URL" alembic upgrade head
DATABASE_URL="$TEST_DATABASE_URL" alembic check        # metadata/migration drift
python -m compileall -q app
```

Test coverage includes registration for all public roles, administrator
self-registration rejection, mass-assignment rejection, duplicate/case-insensitive
email, login rotation, session revocation/expiry, CSRF/Origin failures,
throttle recovery, cross-user profile isolation, instructor/student separation,
real constraint enforcement, migration rollback/reapply, non-admin verification
denial, role changes observed from the database, audit actor/time/reason,
stale/repeated conflict, injected audit-failure rollback, concurrent decisions
(exactly one winner), and the unverified-company guard.

## Pre-pilot decisions still required (not invented here)

These remain open product/legal/operational decisions and are **not** claimed as
implemented:

- Privacy notice text, lawful basis, retention/deletion schedule for accounts,
  profiles, sessions and audit records (RA 10173).
- The real company-verification evidence and review procedure.
- TLS/hosting topology, secret manager, database backup/restore runbook and
  recovery testing (target RPO 24 hours is proposed, not measured).
- Shared throttle storage (e.g. Redis) for multi-worker deployments; current
  throttles are in-process.
- Session/expired-row cleanup job and log retention.
- Administrator account recovery/second-person approval process.
- Final upload limits/extension policy (Phase 2) and AI provider/budget policy
  (Phase 3).

## Marketplace extension (FR04–07)

The additive `4b1f750c284b` migration adds listings, applications, application
status history and separate marketplace events. Existing verification audit
records and foundation endpoints are preserved.

Authenticated discovery: `GET /api/v1/listings` supports `q`, `location`, `type`
(`ojt|job`), `skill`, `limit` and `offset`. Published listings from verified
companies are returned; closed detail remains available and drafts remain private.
Companies manage their own records at `/api/v1/company/listings` using POST,
PATCH `/{id}`, and POST `/{id}/publish` or `/{id}/close`. All writes require a
verified company plus CSRF. Listing changes carry durable actor/time events.

Students submit multipart `file` and `cover_letter` to
`POST /api/v1/listings/{id}/applications`. The implementation default is a
required PDF up to 5 MiB, checked by filename, declared MIME, PDF header and EOF
trailer. This is format validation, not a malware scanning service. Actual
request bytes are capped at 6 MiB on this endpoint; JSON routes retain 64 KiB.
PDF bytes are stored privately in PostgreSQL in the application transaction,
never exposed through a public file path.

`GET /api/v1/applications/me` is student-only; company review uses
`GET /api/v1/company/applications?listing_id=...`. Both paginate (20 default,
100 maximum). `GET /api/v1/applications/{id}` and `/{id}/attachment` authorize
only the applicant or listing owner, excluding instructors and administrators.
Companies PATCH `/{id}/status` with `under_review`, `accepted` or `rejected`.
History and status commit atomically. Submitted may enter review or rejection;
review may enter acceptance or rejection; final decisions stay final. A unique
student/listing constraint rejects duplicates. Submission and closure lock the
same listing row to serialize their competing transactions.

Company application responses include only `student_profile` display name,
institution, program, skills, interests, location and background. Listing
responses flatten public company information into `company_description` and
`company_website`; private company contacts remain excluded. Every API response
uses no-store; PDF downloads also use attachment disposition and nosniff.

## Learning and guidance (FR03/10/11)

Additive migration `7208323f78db` adds published learning resources, immutable
quiz questions, stored quiz attempts, per-user save/react states, moderation
reports and separate content events. Public feed/detail never returns answer
keys. Administrators create resources (optional questions/answer keys at creation
only), edit publication/text/tags, resolve reports, and view the paginated
`/api/v1/admin/content-events` audit. Publication and report decisions commit with
their events; event-insert failure rolls back the change.

Authenticated feed: `GET /api/v1/content?q=...&tag=...`; administration uses
`/api/v1/admin/content` with additional status filtering. Lists default to20 and
maximum100 records. Outputs include actual current-user saved/reacted flags and
`has_quiz`. Student/instructor POST `/content/{id}/save` with `{saved:true}` or
`/react` with `{reacted:true}`; repeating a desired state is idempotent. Requests
lock the same content row to preserve both flags across concurrent updates.

`GET /content/{id}/quiz` returns question UUIDs/options only. POST the complete
`{answers:{questionUUID:optionIndex}}` map to the same path; missing/extra/invalid
options are rejected. The stored answer key yields `{score,total,correct}`,
where score is a percentage0–100. Attempts are retained; edits cannot rewrite
historical question keys.

POST `/api/v1/reports` with `{content_id,reason}` targets a published resource.
Only administrators can inspect `/admin/reports` and PATCH `/{id}` with
`{status:"resolved",resolution}`. Actor/time/resolution are retained and repeated
final decisions conflict.

POST `/api/v1/assistant` accepts only a bounded question. Provider mode defaults
to `APP_ASSISTANT_MODE=disabled`, giving503 `ASSISTANT_UNAVAILABLE` without
interfering with applications. Explicit `retrieval` mode returns labeled resource
lookup excerpts from at most3 matching published resources, each at most800
characters; it is **not a live LLM**. No-match lookup returns uncertainty. The
provider Protocol receives only question and approved excerpts; it never receives
user/session/profile/application/file objects. Returned citations are checked
against those approved sources and titles are drawn from server records.
Malformed output/provider errors become a generic503. Guidance is limited to10
requests/user/minute by default (in-process; configure via `.env.example`).

An actual external LLM adapter, provider selection/budget/retention review and
pilot credentials remain pending pre-pilot dependencies. No live AI or measured
factual/semantic accuracy is claimed by the local retrieval implementation.

## Recommendations and feedback (FR08–09)

`GET /api/v1/recommendations?limit=10` is student-only (maximum20 per type).
Ranked entries include actual listing/content projections, normalized score and
reason; unavailable/draft/closed/unverified items are excluded. Candidate pools
are capped to500 recent eligible items per type. TF-IDF (scikit-learn, Unicode
accent normalization, word1–2grams, maximum20000 features) compares program,
skills, interests and location against listing/resource text. Stable ties follow
recent creation time then UUID. Missing/unmatched profiles fall back to actual
recorded view/rating popularity; without activity they use recent publications.
Reasons identify the actual fallback; suggestions are not hiring decisions.

Optional hybrid input is limited to5000 latest **explicit** ratings of eligible
items. At least5 distinct users,20 rating records and2 jointly rated items per
neighbor are required. Similarity uses jointly observed ratings only; no missing
rating is filled as numericzero. Neighbor predictions normalize observed1–5
ratings to0–1. Eligible predictions combine with content cosine by configured
alpha; items without neighbors use alpha 1. `APP_RECOMMENDER_ALPHA` is bounded0–1
and defaults to1 until real held-out evaluation selects a weight. Synthetic
functional test fixtures with a non1 weight do not establish effectiveness.

Student/instructor POST `/api/v1/interactions` records actual `view` events or
optional explicit `rating`1–5 for a typed listing/content UUID. Numeric ratings
are strict integers; views haveNULL rating. User and time are server derived;
unknown/ineligible targets and client-supplied identity/time are rejected. Typed
foreign keys/check constraints prevent orphan targets, partial unique indexes
retain one latest explicit rating per user/item, and repeated rating writes
update that record. Views remain individual events. Feedback is bounded to60
writes/user/minute in-process; failure does not affect applications. Shared
throttles and pilot feedback consent/retention remain pre-pilot decisions.
