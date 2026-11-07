# Backend audit — 2026-11-05

The existing DeepSeek FastAPI implementation is preserved. The baseline supports
FR01 accounts, FR02 role profiles (partially), and FR11 company verification
with PostgreSQL transactions and privileged audit events. There were no listing,
application, private attachment, content, recommendation or assistant routes at
the start of this audit.

## Verified commands

Commands ran from `backend/`, against disposable PostgreSQL 18.6 at localhost
port 55433, database `thinkmedia_codex_test`, using the existing `.venv`.

| Check | Actual result |
| --- | --- |
| Original `python -m pytest -q` | 75 passed in 14.09s, exit 0 |
| Tests after bounded-body correction | 77 passed in 13.89s, exit 0 |
| `alembic check` | No new upgrade operations detected, exit 0 |
| `python -m compileall -q app` | exit 0 |
| Development DB `alembic upgrade head` | foundation migration applied, exit 0 |

The initial test attempt without a database URL failed at fixture setup; no
SQLite substitution was used. PostgreSQL was started in `/tmp` for this audit.
The browser integration server uses a separate `thinkmedia_codex_dev` database
to avoid test truncation affecting browser sessions.

## Correction

NFR02/NFR11: the existing body limit trusted `Content-Length`, permitting chunked
requests or a false smaller header to bypass the cap. Middleware now counts
actual streamed bytes and rejects oversized input before route processing.
Regression tests cover both bypasses and the uniform error/request-ID response.

## Remaining scope at audit baseline

- FR02 student location/background and company contact information are absent
  from the foundation schema; existing profile fields are validated and private.
- FR04–07 marketplace and file workflows, FR03 learning, FR08–09 recommendations
  and feedback, FR10 assistant and FR12 evaluation have not been implemented.
- Company verification is real and audited, but evidence collection and review
  policy remain pre-pilot decisions.
- In-process throttles require shared storage before a multi-worker pilot;
  expired-session cleanup, production TLS, privacy/retention policy and daily
  backup/restore rehearsal remain outstanding.
- No pilot performance, MAE/RMSE, cross-validation, BERTScore or CSAT measurements
  have been made or inferred from functional tests.

## FR02 completion following audit

Added student location/background (200/2000 characters) and nullable company
contact_email/contact_phone fields through additive migration
`0002_profile_details`. Email is normalized; phone accepts 7–15 digits with
common punctuation. Fields are role restricted and remain self-only; company
contacts are also included in the administrator review response.

Full suite after the extension: **80 passed in 16.62s**. Migration preservation
and downgrade/re-upgrade test was then strengthened and rerun: **1 passed in
0.70s**. `alembic check` again reported no new operations. The separate
development database was upgraded to 0002 for browser integration.

No production database, credentials, deployment, external messages or Git push
were used.
