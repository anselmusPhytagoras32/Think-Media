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

The daily job is documented but not installed: hosting, production resources and retention policy require approval. No production database operation or scheduler change was performed.

## Representative local benchmark

```bash
DATABASE_URL=postgresql+psycopg://LOCAL_USER@127.0.0.1:PORT/thinkmedia_dev .venv/bin/python -m ops.benchmark --concurrency 20 --requests 200 --output reports/performance-local.json
```

The utility permits only loopback HTTP and explicit `_dev`/`_test` databases. It creates 20 distinct synthetic student accounts, warms each actor across profile/listings/content/recommendations, then measures 200 authenticated GET requests with 20 concurrent users. The report records actual path mix, dataset sizes, failures, p95 method, environment and target comparison. Authentication setup, writes/uploads, AI calls and cold startup are outside this timed mix. This is local synthetic load evidence, not a pilot or production performance claim. Synthetic actors are retained; no account is removed.

## Deployment and privacy decisions still required

Approve hosting/TLS, secrets management, the actual company-verification evidence procedure, privacy notice/legal basis, retention/deletion schedule, backup destination and scheduler before a pilot. Current throttles are in-process and require shared state for multiple workers. Private personalized API responses use no-store; public-content caching and scheduled expired-session/file cleanup remain future operational work under an agreed policy. No production deployment is authorized by these scripts.
