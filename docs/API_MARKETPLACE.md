# Marketplace contract — FR04–07 / NFR02–04, 06, 11

Base `/api/v1`; existing session/CSRF conventions. All endpoints authenticated. Errors use existing error envelope. No frontend fixtures replace real API responses.

Listing output: `id, company_id, company_name, title, description, requirements, location, type (ojt|job), skills: string[], status (draft|published|closed), created_at, updated_at`. Public company details include description/website/location only (no private contact fields). List envelopes `items,total,limit,offset`.

- GET `/listings?q=&location=&type=&skill=&limit=20&offset=0`: published listings of verified companies only, stable order.
- GET `/listings/{id}`: published/closed public detail; drafts only visible to owner.
- GET `/company/listings`: own listings including drafts/closed.
- POST `/company/listings`: verified company only, create draft from title, description, requirements, location, type, skills.
- PATCH `/company/listings/{id}`: owner + verified company; edit fields in draft/published, closed immutable.
- POST `/company/listings/{id}/publish`: draft -> published.
- POST `/company/listings/{id}/close`: published -> closed. No reopening. Log actor/time/old/new status with transactional history.

Application output: `id, reference, listing_id, listing_title, company_name, student_id, student_name, status (submitted|under_review|accepted|rejected), cover_letter, attachment_name, created_at, history: [{actor_id,old_status,new_status,created_at}]`. Company detail additionally includes applicant role-specific profile, no unrelated applications. Private application endpoints use no-store.

- POST `/listings/{id}/applications`: multipart `cover_letter` plus `file`, student only. Default PDF only, required, <=5MiB, extension/MIME/signature validated. Store bytes privately in PostgreSQL in same transaction as application and initial history; safe default avoids orphan files and public paths. Reject invalid/missing files. Bound request before parsing. Serialize submission against listing close; unique student/listing constraint. Returns 201 receipt application output.
- GET `/applications/me`: student own applications only.
- GET `/company/applications?listing_id=`: company own applicants only, paginated.
- GET `/applications/{id}`: student owner or listing company owner only; instructor/admin denied.
- GET `/applications/{id}/attachment`: same owner checks, PDF attachment with safe filename, no-store/nosniff.
- PATCH `/applications/{id}/status`: company owner only, body `{status}`. submitted -> under_review|rejected; under_review -> accepted|rejected; final immutable. Lock application, commit decision/history atomically; failure rolls back. Conflicting transition 409.

Ownership failures 403 or non-disclosing 404; missing auth 401; duplicate/closed/conflict 409; validation 422; too-large 413. Bounded input, UUID parameters, parameterized ORM, unique/FK/check constraints, versioned additive migration.

Tests: verified publish/student submit/review; unverified and wrong-role denied; cross-company/student isolation; duplicate race; closed listing; missing/oversized/disguised PDF; unauthorized download; invalid transition; injected history failure rollback; close/submission synchronization.

Review clarifications: `/applications/me` paginates with the same 20 default/100 maximum. Actual-byte request envelope cap 6MiB applies only to the application POST; other routes retain 64KiB. Listing title 200, description/requirements 10000 each, location 200, <=30 skills of <=80 each; cover_letter <=5000. Applicant projection explicitly limited to display name, institution, program, skills, interests, location, background; no account email/session/password/other applications. Student output excludes company private contact details. Durable separate marketplace events record listing create/edit/transitions; verification audit table remains unchanged. History records decision actor/time/status atomically.
