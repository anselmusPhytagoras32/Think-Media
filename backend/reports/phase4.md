# Phase 4 backend — FR08–09 / NFR02–03,06,08,11

Implemented actual profile recommendations and explicit feedback without
fabricated labels or research measurements. Existing phases are preserved.
Additive migration `a7eed17d111a` creates typed interaction foreign keys, an
exactly-one-target check, event/rating validity check and partial unique indexes
for one latest explicit rating per user/item. Views remain separate actual events.

## Ranking behavior

- Student-only endpoint returns actual current marketplace/content projections.
  Published verified-company listings and published content only; closed, draft,
  archived, unverified and unknown targets are excluded.
- Per-type candidate pool:500 most recent eligible records, stable creation/UUID
  order. Profile program/skills/interests/location and eligible resource text use
  actual scikit-learn TF-IDF/cosine (Unicode accent normalization, word1–2grams,
  maximum20000 features). Shared-term scores are normalized0–1.
- Missing or wholly unmatched profiles use actual recorded view/rating popularity;
  absent activity uses recency. Every result states the actual reason. Nozero
  cosine result is labeled a profile match. Suggestions do not determine hiring.
- Optional hybrid uses at most5000 latest explicit ratings of eligible items.
  Requires5 distinct users,20 ratings, and2 jointly observed items per neighbor.
  Cosine similarity uses only observed common ratings; predicted ratings normalize
  observed1–5 values to0–1. Missing labels never become numericzero.
- `APP_RECOMMENDER_ALPHA` validates0–1 and defaults to1 until real held-out
  validation chooses a weight. An item without eligible neighbors usesalpha1.
  Response limitations explain defaults, caps and pending evaluation.

## Feedback behavior

Student/instructor only, CSRF protected. User and time derive from the server.
Typed eligible target required, strict optional integer1–5 for explicit ratings,
NULL rating for actual views. Client identity/time fields are rejected. Rating
upsert retains the same record ID; view events remain individual records. A
60-write/user/minute in-process bound protects writes without blocking applications.

## Actual verification

Existing Python3.14.4 virtualenv; PostgreSQL18.6, dedicated disposable
`thinkmedia_codex_test` database on local port55433, explicitTEST_DATABASE_URL.

| Check | Verified result |
| --- | --- |
| Full backend suite | **110 passed in39.58s**, exit0 |
| Alembic metadata/migration check | **No new upgrade operations detected**, exit0 |
| Python compilation | exit0 |
| `pip check` | No broken requirements found, exit0 |
| Separate development migration | upgraded toa7eed17d111a, exit0 |
| Development API | restarted with final source onport8000 |

Eleven recommendation tests cover deterministic actual profile ranking/projection,
recent and actual-popularity fallback, wholly unmatched profile fallback,
eligibility filtering, role/mass-assignment denial, strict invalid numeric ratings,
server time/user, upsert/viewNULL, insufficient-dataalpha1, validated configuration,
rate bounds, actual database FK/check enforcement and a **synthetic functional**
5-user22-rating hybrid fixture. This fixture tests behavior, not effectiveness.
All prior auth, applications, uploads, rollback, moderation and assistant tests pass.

Runtime packages are pinned: pandas3.1.1, scikit-learn1.9.1, NumPy2.5.4, plus
resolved transitive dependencies in requirements.lock. Pinned NumPy/SciPy require
Python>=3.12; README minimum reflects that, verified runtime remains3.14.4.
Initial test invocation raced the still-running dependency installation and failed
at import; the reported full suite ran successfully after packages were installed.

## Remaining work

No actual held-out alpha selection, MAE/RMSE, cross-validation or pilot feedback
quality measurement has been performed. Shared multi-worker rate limiting,
feedback consent/retention policy and research data collection remain pre-pilot
work. No production changes, deployment, push or external messaging performed.
