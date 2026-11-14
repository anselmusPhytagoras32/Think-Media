# Start with empty local data

The normal app launcher does not seed accounts, listings or learning content.
Register new student, instructor and company accounts through the app. An
existing administrator can verify companies and publish the resources you want
to use. Guidance still has access to the versioned public OJT and product guides
bundled with the app; the reset does not create learning records or user data.
Questions outside those guides and published learning resources still receive
an uncertainty response.

From the repository root in PowerShell, preview the reset:

```powershell
wsl -d Ubuntu -- bash scripts/wipe-local-data.sh
```

Apply the reset:

```powershell
wsl -d Ubuntu -- bash scripts/wipe-local-data.sh --execute
```

In WSL or a Linux shell at the repository root, use
`bash scripts/wipe-local-data.sh --execute` directly.

The script loads the same private runtime and `backend/.env.local` precedence
as the presentation API. It only accepts `APP_ENV=local` and an explicit loopback
PostgreSQL database ending in `_local`, without connection-string overrides.
Production and remote targets are rejected. The disposable browser-test database
is a separate target and is not reset by this command.

Before any deletion, it locks application tables against writes and creates a
private PostgreSQL custom-format backup under `.local/resets/`. A backup failure
prevents deletion. All deletions occur in one transaction and roll back on
failure. Unknown/missing tables also stop the reset. PostgreSQL tools must be
available through the existing `PG_BIN` configuration.

The reset removes:

- All student, instructor and company accounts and their profiles.
- All listings, applications, uploaded attachment bytes and status histories.
- All learning resources, quizzes, saves, reactions and moderation records.
- All recommendation interactions, satisfaction feedback and activity/audit logs.
- All sessions, including administrator sessions.

It preserves every administrator account and password, the schema and Alembic
migration version, `.env.local`, API keys and other configuration. No administrator
account is created or promoted by the reset. Sign in again using your existing
administrator credentials afterward. The script refuses execution if there is
no administrator to preserve.

Existing historical reports, ignored credential journals, source knowledge
files, test fixtures and old backups are not active application data. They are
not imported on startup. Avoid explicitly running the legacy demo seed or
presentation-account provisioning commands if you want to keep a clean state.
The optional knowledge publication command also requires an explicit invocation.

To inspect the backup, use `pg_restore --list PATH_TO_DUMP` with your configured
PostgreSQL tools. Restore into a separate local database first when recovering;
this reset command never overwrites or restores another database automatically.

Requirements: FR01–FR12 resettable local acceptance environment; NFR02/03 local
scope and private data, NFR04 atomic cleanup, NFR07 recoverable backup, NFR06
separated operator tooling. This is a local test reset, not a production
retention or deletion policy.

Verified November 14: the requested reset removed six non-administrator
accounts, three listings and eleven learning resources, leaving two unchanged
administrators and zero application/activity rows immediately after the reset.
The saved 145579-byte backup passed PostgreSQL archive inspection and SHA-256
verification. All eleven reset tests and six affected browser checks passed;
the production build passed. Existing administrator sign-in and actual empty
views were checked at 360px and 1440px. Evidence:
[local-reset-2026-11-14.json](../backend/reports/local-reset-2026-11-14.json).
