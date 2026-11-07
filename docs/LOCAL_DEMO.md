# Local ThinkMedia demo

The local consumer setup uses real PostgreSQL and the FastAPI API. It supports FR01–04, FR06, FR08 and FR10–11 with synthetic demonstration records. It does not provide research observations or real vacancies.

For the workspace prepared on November 7, 2026, run `bash .local/start-backend.sh` from the repository root, then run `npm run dev -- --host 127.0.0.1` in `frontend`. Open http://127.0.0.1:5173 and sign in with `student@example.test`. The locally supplied password is kept in the private runtime environment as `LOCAL_DEMO_STUDENT_PASSWORD`. This account is Alex Student with the student role; it cannot open administrator tools. Three clearly labeled demo opportunities and three approved demo learning guides are stored in the database. Each guide includes a practice quiz. Application and saved-resource history begins empty and records your actual local actions.

The ignored launcher reads `/home/gebhel_santos/.local/share/thinkmedia/local.env`, starts the existing database if needed, applies additive migrations and starts FastAPI on `127.0.0.1:8000`. PostgreSQL listens only on `127.0.0.1:55432`. Its persistent data, native PostgreSQL binaries, private environment, demo ownership manifest and backups live under `/home/gebhel_santos/.local/share/thinkmedia/`, outside `/tmp` and Git. `thinkmedia_local` holds consumer data; `thinkmedia_test` is a separate disposable test database. Do not run tests against `thinkmedia_local`. Private runtime files use owner-only permissions on the Linux filesystem.

No previous persistent database or logical backup was found when restoring this workspace. The earlier temporary `/tmp` database was unavailable after the environment restarted; the new demonstration setup does not claim to recover that data.

To restart manually, without the ignored launcher:

```bash
source /home/gebhel_santos/.local/share/thinkmedia/local.env
# Run pg_ctl start only when pg_ctl status reports the cluster is stopped.
"$PG_BIN/pg_ctl" -D /home/gebhel_santos/.local/share/thinkmedia/pgdata status
"$PG_BIN/pg_ctl" -D /home/gebhel_santos/.local/share/thinkmedia/pgdata \
  -l /home/gebhel_santos/.local/share/thinkmedia/postgres.log \
  -o '-h 127.0.0.1 -p 55432 -k /home/gebhel_santos/.local/share/thinkmedia/socket' start
cd backend
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`APP_ASSISTANT_MODE=retrieval` enables deterministic guidance drawn from published resources; it makes no external AI call. Runtime provider credentials are not configured.

The seed helper, run from `backend` as `.venv/bin/python -m ops.local_demo`, uses existing account, profile, verification, listing and publication services. It requires `APP_ENV=local`, a loopback PostgreSQL database whose name ends in `_local`, the private environment and its ownership manifest. Repeated runs preserve existing profiles, passwords, applications, listing states and resources. It refuses accounts outside its ownership manifest. For a new empty database only, `--bootstrap-admin` provisions the separate demonstration administrator using `LOCAL_DEMO_ADMIN_PASSWORD`; administrator registration remains unavailable through the public API. Do not use the bootstrap flag to modify existing accounts. The synthetic company verification has an explicit local-demo audit reason and does not imply a real partnership.

Create a private logical backup from `backend` after sourcing the local environment:

```bash
DATABASE_URL="$LOCAL_BACKUP_DATABASE_URL" .venv/bin/python -m ops.backup --pg-bin "$PG_BIN" \
  --output "/home/gebhel_santos/.local/share/thinkmedia/backups/local-$(date +%Y%m%d-%H%M%S).dump" \
  --restore-smoke
```

The command uses the separate local backup role, creates a fresh restore database and preserves it for inspection. The API's database role has no superuser or database-creation privilege. Never overwrite an existing database to test recovery. Back up daily before meaningful local work; no automated daily schedule is installed by this setup (NFR07).

For a fresh environment with your own PostgreSQL installation, follow the backend README and provision a local database and private environment first. Use a persistent Linux data directory rather than `/tmp`; the ignored launcher and runtime environment are machine-local files, not distributable configuration.

You can also exercise the complete role workflow:

1. Provision an administrator through the backend CLI. Never choose an administrator role during public registration.
2. Register a company and complete its organization/contact details. As administrator, review and verify it with a recorded reason.
3. As company, create a draft, enter requirements and publish. As student, complete a profile, search the opportunity and inspect details.
4. Attach a permitted PDF, review and confirm. Keep the returned reference. As company, review the applicant and move through Under Review to a final decision. As student, inspect status history. Close the listing and confirm its existing application remains.
5. As administrator, publish a learning resource with a quiz. As learner, open it, save/react, answer the quiz and inspect the actual score. Report content; as administrator, inspect and resolve the report with an audited reason.
6. Open Suggestions, inspect actual reasons and optionally submit a relevance rating. Profile changes influence profile-based matching; unavailable/closed items are excluded.
7. Ask guidance a question matched by approved resources. Read the lookup label, uncertainty and cited source text. Optionally share satisfaction feedback. No external AI call or hiring decision occurs.

Automated tests create clearly synthetic local records. Do not use those accounts or feedback rows as pilot research observations. Research reports remain pending until genuine datasets are supplied. No public deployment or production action is part of this demo.
