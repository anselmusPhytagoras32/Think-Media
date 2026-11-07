# Learning and guidance contract — FR03/10/11

Proposed next-phase contract. Implement only after marketplace acceptance.

Existing auth/CSRF/error conventions. Published approved resources only in student/instructor feeds and assistant retrieval. All lists paginated. Administration requires server-side administrator role.

Content: id, title, summary, body, tags, status (draft/published/archived), created_at, updated_at. Plain text rendering; never arbitrary HTML.

- GET `/content?q=&tag=&limit=20&offset=0`: authenticated published feed.
- GET `/content/{id}`: published detail; administrator can inspect drafts.
- POST/PATCH `/admin/content[/{id}]`: administrator creates/edits; publication/archive changes audited atomically.
- GET `/admin/content`: all statuses for moderation.
- POST `/content/{id}/save` and `/content/{id}/react`: explicit idempotent save/react desired state; only student/instructor, published content.
- GET `/content/{id}/quiz`: questions/options, never answer key.
- POST `/content/{id}/quiz`: validate complete option IDs and score using stored answer key; authenticated attempt retained.
- POST `/reports`: authenticated report on published content, bounded reason. GET/PATCH `/admin/reports`: queue and audited resolution.

Assistant: POST `/assistant` with bounded question only, authenticated/throttled. Approved published resources retrieved on server. Provider adapter accepts only question + approved resource snippets; no session/user/application/profile/attachment data. External provider is disabled by default with clear 503 ASSISTANT_UNAVAILABLE. Real provider only when independently configured server-side. Grounded local retrieval can list sources but must not pretend to be an external LLM. Response answer, sources [{id,title}], uncertainty. Failures leave application endpoints operational. Never expose credentials, accept arbitrary provider URL from client, or mutate hiring decisions.

Test unpublished hidden, role denial, quiz answer-key non-disclosure/scoring, invalid options, report isolation, audited moderation rollback, assistant unavailable and independent application health.

## Implementation agreement
Content outputs: `id,title,summary,body,tags,status,created_at,updated_at,saved,reacted` (saved/reacted reflect actual current-user records). `POST /content/{id}/save` body `{saved:boolean}` and `/react` body `{reacted:boolean}` are idempotent desired-state writes.

Admin creation: title<=200, summary<=500, body<=20000, tags<=30 of<=80, status draft|published. Optional quiz `questions:[{question,options:string[],correct_index:int}]` with2–6 options each and <=20 questions. Quiz keys accepted only on admin creation; do not rewrite historical quiz questions/answer keys in content edits. Feed/detail learner output never includes correct_index. GET quiz returns `{questions:[{id,question,options}]}`. POST quiz body `{answers:{questionUUID:optionIndex}}`, complete exact question set, returns `{score,total,correct}` and records attempt atomically.

Admin list GET `/admin/content?status=&limit=&offset=`; PATCH content supports title/summary/body/tags/status (draft|published|archived), events recorded transactionally in separate `content_events` to preserve existing verification-audit schema. Content and report events expose admin-only `/admin/content-events` paginated for audit summary.

POST `/reports` body `{content_id,reason}`; admin queue GET `/admin/reports?status=pending|resolved&limit=&offset=`; PATCH `/admin/reports/{id}` body `{status:'resolved',resolution}`. Store actor/time/history, deny unknown targets and repeated final resolution.

Assistant response `{answer,sources:[{id,title}],uncertainty,mode}`. Default provider `disabled` returns503 with clear ASSISTANT_UNAVAILABLE. Implement provider Protocol and optional explicitly configured `retrieval` mode: deterministic approved-resource excerpts with mode='retrieval', explicitly described as resource lookup, never represented as a live LLM. Actual external LLM provider remains a documented pre-pilot dependency. Local retrieval must return uncertainty without matching sources. Max question2000, bounded retrieved snippets/results, per-user request limit; never query profiles/applications/attachments. Tests may inject provider stub for failure/citation validation, clearly test-only.
