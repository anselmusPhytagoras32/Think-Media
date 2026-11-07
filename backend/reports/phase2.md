# Phase 2 backend — FR04–07 / NFR02–04,06,11

Preserves the DeepSeek foundation and adds a layered marketplace implementation:
strict input schemas, HTTP adapters, transaction/authorization service,
parameterized repository and SQLAlchemy records. Additive Alembic revision
`4b1f750c284b` creates listings, private applications, status history and
marketplace events; the existing verification audit schema remains unchanged.

Verified workflows include company draft/edit/publish/close, authenticated
published search/filter/detail, student PDF submission/reference/tracking,
company-only applicant projection, authorized private download and confirmed
status transitions. No mock responses are used by these endpoints.

PDF bytes (default maximum 5 MiB) and the initial application/history share a
single PostgreSQL transaction. Actual-byte multipart envelope cap is 6 MiB;
other requests retain the 64 KiB cap. Application submission and listing closure
lock the same listing row; the database unique student/listing constraint also
protects duplicates. Status update and history are atomic. Only the actual
unique application constraint is translated into a duplicate response; unrelated
integrity failures remain generic internal errors and roll back.

## Verification

All commands ran from `backend/` against the explicitly disposable PostgreSQL
18.6 database `thinkmedia_codex_test`, localhost port 55433, Python 3.14.4.

- Original foundation after integration: 80 passed in 16.11s.
- Initial expanded run: 88 passed, one failed: non-disclosing detail returned
  403 where the test required 404. Corrected to 404 for hidden listing details.
- Corrected complete suite: **89 passed in 26.71s**, exit 0.
- Final rerun after explicit `TEST_DATABASE_URL` requirement: **89 passed in 26.98s**, exit 0.
- `alembic check`: **No new upgrade operations detected**, exit 0.
- `python -m compileall -q app`: exit 0.
- Separate disposable development DB upgraded to the marketplace revision.

Nine new marketplace tests cover lifecycle/events, unverified/wrong-role access,
cross-company/student/instructor/administrator privacy, duplicate/closed/final
transitions, invalid/missing/oversized files, chunked-envelope bounds, injected
history failure rollback (submission and status decision), unrelated database
integrity failure, concurrent duplicate winner and submission/closure race.
Migration tests also include all marketplace tables in downgrade/re-upgrade checks.

Tests now require `TEST_DATABASE_URL` explicitly; they never fall back to the
application's `DATABASE_URL` before destructive fixture cleanup.

## Integration contract

Listing responses expose `company_description` and `company_website` as flattened
public details. Company-only application responses include `student_profile`
containing display_name, institution, program, skills, interests, location and
background. They exclude account email, credentials and unrelated records.
Both student and company application lists paginate, default 20/maximum 100.

No production migration, deployment, push or external messages were performed.
PDF checks verify format markers, MIME and extension; malware scanning is not
implemented. Upload/retention policy remains a pre-pilot decision. Learning,
recommendations, assistant and research measurements remain later-phase work.
