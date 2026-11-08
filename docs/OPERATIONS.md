# Local recovery and performance — NFR01/07

## Private backups

Run from backend with an explicitly configured loopback PostgreSQL DATABASE_URL:

```bash
.venv/bin/python -m ops.backup --pg-bin /usr/lib/postgresql/18/bin --output /private/thinkmedia-backups/UNIQUE-NAME.dump --restore-smoke
```

The utility creates a new 0600 custom-format dump, refuses to overwrite a file, and permits only loopback databases. Restoration creates a fresh randomly named database, restores in one transaction and compares every public-table row count, schema version and streamed private-attachment byte fingerprints with the quiescent source. Existing databases are never overwritten or dropped. Keep the source quiescent for the count comparison. Failed artifacts and the fresh restore database are retained for inspection; no cleanup/deletion is automated.

This workspace uses privately unpacked PostgreSQL18 binaries under `/tmp/pg/usr/lib/postgresql/18/bin` with `LD_LIBRARY_PATH=/tmp/pg/usr/lib/x86_64-linux-gnu`. That is an implementation-test environment, not a production dependency or deployment plan.

## Daily recovery plan

Before a pilot, schedule a private backup every day at 02:00 Asia/Manila on the approved host. Use an environment/service file outside Git for credentials, restrict backup access, record success/failure, and test restoration into a fresh isolated database regularly. Proposed maximum data loss is 24 hours; no recovery-time objective is claimed. Verify the restore before any rollback decision. Approve backup retention and deletion policy before removing files.

The local Windows task `ThinkMedia local daily backup` is installed at 02:00
UTC+8 under the presenter's interactive account. Its manual verification returned
result 0. It requires Windows on and the user logged in, with StartWhenAvailable
for missed runs. It starts the existing WSL runtime and creates private dumps;
daily runs do not create extra restore databases. The full restore-smoke command
was checked separately. See the current [presentation guide](PRESENTATION_READINESS.md).
No cloud/production scheduler or production database operation was configured.

## Representative local benchmark

The current revision's [November 8 local report](../backend/reports/performance-presentation.json)
measured 200 GETs with 20 concurrent synthetic students after warmup: p95
729.553ms, zero failures. The fixture contained ten published listings and ten
published resources. Reproduce with `wsl -d Ubuntu -- bash scripts/benchmark-current.sh`
only after database tests finish; it uses the disposable `_test` database and its
own API port 8002, and preserves the presentation database. AI, writes/uploads,
authentication setup and cold startup are outside the timed request mix.

```bash
DATABASE_URL=postgresql+psycopg://LOCAL_USER@127.0.0.1:PORT/thinkmedia_dev .venv/bin/python -m ops.benchmark --concurrency 20 --requests 200 --output reports/performance-local.json
```

The utility permits only loopback HTTP and explicit `_dev`/`_test` databases. It creates 20 distinct synthetic student accounts, warms each actor across profile/listings/content/recommendations, then measures 200 authenticated GET requests with 20 concurrent users. The report records actual path mix, dataset sizes, failures, p95 method, environment and target comparison. Authentication setup, writes/uploads, AI calls and cold startup are outside this timed mix. This is local synthetic load evidence, not a pilot or production performance claim. Synthetic actors are retained; no account is removed.

## Deployment and privacy decisions still required

Approve hosting/TLS, secrets management, actual company-verification procedures,
privacy notice/legal basis, retention/deletion and production recovery settings
before a pilot. Current throttles and counters are process-local. Private API
responses remain no-store; bounded internal public-content projections exclude
personal flags. Administrators can monitor aggregate request/storage usage in
Audit history. Explicit local maintenance can prune expired sessions, while
policy-controlled attachment expiry is implemented as a separate explicit local
command with dry run by default. It preserves application/status history and
adds a durable audit, with410 for authorized expired downloads. Its operator
must supply the approved period/reference and current administrator attribution.
No presentation file was expired. Backup rotation still awaits an approved
retention policy. [Restore evidence](../backend/reports/retention-restore-local.json)
covers both retained bytes and a synthetic expired tombstone plus its audit.
No production deployment is authorized by these scripts.
