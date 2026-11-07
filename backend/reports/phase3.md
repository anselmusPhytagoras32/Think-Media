# Phase 3 backend — FR03/10/11 / NFR02–06,09–11

The existing foundation/marketplace is preserved. Additive migration
`7208323f78db` creates learning_content, quiz_questions, quiz_attempts,
content_states, moderation_reports and content_events. Verification audit records
remain unchanged. Schema migration tests include downgrade/re-upgrade of these
new tables on a disposable database.

## Delivered behavior

- Authenticated published feed with keyword/tag filters and paginated responses;
  administrator list also filters status. Draft/archived detail remains private
  to administrators. Plain text body and real per-user saved/reacted flags plus
  `has_quiz` are returned; answer keys never enter feed/detail/quiz responses.
- Administrator creation supports bounded optional quiz questions and keys.
  Content edits cannot rewrite quiz questions or historical keys. Student and
  instructor attempts require the complete exact UUID/option set; score is a
  percentage with correct/total counts and an actual retained attempt.
- Desired-state save/react is idempotent and role restricted; upsert and content
  row locking preserve the other flag across concurrent updates.
- Reports target published content only. Queues, resolution and content events
  require administrator authorization. Publication/report decisions and actor/time
  events share transactions, with failure rollback tested.
- A provider Protocol receives only question plus at most three approved public
  excerpts (800 characters each), never user/session/profile/application/file
  objects. Citations are checked against retrieved approved IDs; their titles
  come from server records. Invalid responses/provider exceptions become503.
- Default provider is disabled and clearly returns503 ASSISTANT_UNAVAILABLE.
  Explicit `APP_ASSISTANT_MODE=retrieval` is deterministic labeled resource lookup
  with uncertainty, never claimed as a live LLM. No matching source returns an
  uncertainty response. Per-user guidance rate limits default to10/minute.
  Application workflows remain available independently of provider failure/429.

## Actual verification

Environment: existing Python3.14.4 virtualenv, PostgreSQL18.6, dedicated local
`thinkmedia_codex_test` database on port55433, explicit `TEST_DATABASE_URL`.

| Command/check | Verified result |
| --- | --- |
| First complete suite after integration | 98 passed in28.37s, exit0 |
| Final full suite including assistant rate-limit isolation | **99 passed in29.70s**, exit0 |
| `alembic check` | **No new upgrade operations detected**, exit0 |
| `python -m compileall -q app` | exit0 |
| Separate development database migration | upgraded to7208323f78db, exit0 |
| Local development API | restarted with final source, default disabled provider |

New tests cover publication visibility/admin checks, schema bounds, immutable
keys, save/react privacy/idempotence/role denial, answer-key non-disclosure and
exact scoring, invalid answer sets without extra attempts, report isolation and
final resolution, injected publication/report event failure rollback, disabled
and failed providers, private/draft data excluded from provider context, rejected
unapproved citations, labeled retrieval/no-match uncertainty and429 isolation.
Existing authentication, marketplace, private-file, concurrency and rollback
tests remain passing. Root owns browser/frontend verification separately.

## Remaining dependencies

No actual external LLM provider adapter/credentials have been configured; source
lookup is available only through explicit local retrieval mode. External provider
selection, budget/timeout/retention policies, live factual evaluation and real
pilot CSAT/BERTScore remain pending. In-process rate limits need shared storage
before multiple API workers. No evaluation numbers are inferred from unit/API
checks. No production resources, deployment, push or external messaging used.
