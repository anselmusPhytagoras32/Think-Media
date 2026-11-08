# Attachment retention contract — FR05/07/11; NFR02/03/04/11

No retention period is approved for real users. Add capability with no automatic
expiry, no startup deletion, and no enabled scheduler for attachments.

## Application response and download

Application projections add `attachment_available: boolean` and
`attachment_deleted_at: string | null` (Asia/Manila ISO). Existing
`attachment_name`, application reference, decision and history remain present.
Fresh uploads have available=true and deleted_at=null. Expiry removes bytes and
scrubs the original filename to `expired.pdf`, retaining a tombstone timestamp.

`GET /api/v1/applications/{id}/attachment` must authorize the student or owning
company FIRST. Unauthorized callers receive the existing denial, including for
expired files. Authorized callers receive 410 `ATTACHMENT_EXPIRED` with a clear
message when bytes have expired. Existing files retain private attachment
disposition, bounded content and no-store. The frontend shows an expired-file
notice instead of a download action when availability=false and handles a 410
race gracefully. Decisions and status history remain usable.

## Explicit local operator command

`python -m ops.attachment_retention --retention-days DAYS --policy-reference TEXT`
defaults to dry run. Require an explicit loopback PostgreSQL URL with no query
overrides and explicit local/test/development APP_ENV. Do not infer a policy or
period from missing arguments. Results contain aggregate count/bytes/cutoff only,
not application IDs, user names, filenames, credentials or file contents.

Apply additionally requires `--apply --confirm-expiry --actor-email EMAIL`.
Re-read that actor's current administrator role from PostgreSQL. Require a
nonempty bounded policy reference. There is no HTTP cleanup endpoint or AI tool.
No production cleanup is authorized by this implementation.

Eligible files must belong to a Closed listing AND an Accepted/Rejected
application. The listing update, submission and latest decision-history times
must all be older than the supplied policy period. Pending, recently closed,
recently decided, open, already expired and incomplete-history records remain.
Use row locks and rechecked state so concurrent expiry is idempotent. Bound each
batch (maximum 100 files); repeated explicit runs can continue remaining work.

In one transaction remove bytes, set deletion timestamp and scrub filename, and
insert a uniquely linked retention audit event. Preserve the application,
reference and complete status history. An audit failure must roll back deletion.
The audit stores actor, application FK, time, retention days, policy reference and
previous byte count; no original filename or document contents. An administrator
is required for execution even in local mode. An all-aggregate dry run is read-only.

## Storage and migration

Allocate additive migration `0007_attachment_retention` after the existing
satisfaction migration. Existing bytes stay intact. Nullable bytes are legal
ONLY with a deletion timestamp; present bytes require no timestamp and still
must satisfy the 1-byte–5-MiB constraint. A separate retention-event table provides
durable history. Downgrade must refuse if tombstones/audit rows exist because
deleted bytes cannot be reconstructed; never pretend it restores documents.

Backup/restore fingerprints must support both retained bytes and tombstones and
preserve audit rows. Update the backup utility accordingly. Old backups still
contain old bytes: file expiry is not complete backup erasure or a legal
retention policy. Backup rotation and real policy approval remain separate.

## Required verification

Use only disposable PostgreSQL fixtures for expiry tests. Cover dry-run
immutability, explicit confirmation and actor guards, eligible expiry with
intact history, unauthorized access to expired files, 410 for both authorized
parties, ineligible/recent/pending preservation, repeat/concurrent execution,
audit-insert rollback, schema constraints and downgrade refusal. Do not expire
any actual presentation attachment during verification.
