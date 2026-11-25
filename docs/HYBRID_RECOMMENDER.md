# ThinkMedia hybrid recommender

FR02/08/09/12, NFR03/06/08/11. The November 25 refinement connects the existing
profile, listing, learning and feedback workflows to shared hybrid scoring and
five-fold evaluation. It leaves the fixed proposal unchanged.

## Matching behavior

Content matching uses TF-IDF and cosine similarity. Student features include
program, self-described background, skills, interests and location. Opportunity
features include title, description, requirements, location, skills and the
offering company's public description. Learning features include title, body
and tags. Names, emails, contact details, private applications and PDFs are not
model features, and recommender computation does not call an LLM.

Only published resources and published listings belonging to verified companies
enter the bounded candidate pool. Closed and unavailable listings remain
excluded. Instructor feedback remains recordable through the existing API, but
collaborative matching for students uses explicit student ratings only.

Collaborative filtering requires at least 20 eligible explicit ratings from
five students. A neighbor must share at least two observed rated items with the
current student. Up to 30 neighbors are selected deterministically by cosine
similarity on shared observed ratings. Missing ratings are never treated as
zero or inferred from views.

For an item with eligible neighbor ratings:

```text
content_score = cosine(profile_text, item_text)                 # 0–1
collaborative_score = weighted mean of (neighbor_rating - 1) / 4 # 0–1
score = alpha * content_score + (1 - alpha) * collaborative_score
```

The prototype default is `APP_RECOMMENDER_ALPHA=0.5`, an explicitly provisional
blend, not an optimal or validated parameter. Set it to `1` to disable the
collaborative contribution. A missing neighbor/item rating automatically uses
profile-only scoring with effective alpha 1. With no content match and no usable
collaborative signal, recorded popularity or recency supplies the general
fallback. Each result reports its actual strategy, component scores, effective
alpha and a readable reason. Scores are ranking values, not probabilities of
placement or proof of qualifications.

`GET /api/v1/recommendations` retains its previous keys and adds per-item
`content_score`, `collaborative_score` (nullable), `strategy`, `effective_alpha`
and `neighbor_count`. Aggregate `method` metadata records model version
`hybrid-v2`, configured alpha, provisional weight status and rating thresholds.
No peer identity or individual peer feedback is returned.

## Evaluation

The runtime and offline evaluators import the same text-feature and collaborative
scoring module, `backend/app/recommender.py`. Evaluation fits text and neighbors
on training observations only. Runtime fits text on its current eligible catalog
and the current student's profile. The offline protocol explicitly controls the
feature-fitting boundary rather than using future catalog text.

The existing grouped five-fold protocol evaluates unseen users and therefore
uses the profile-only cold-start path. The new `hybrid_kfold` protocol evaluates
returning users across five expanding chronological test folds. Each fold has
globally earlier training data, a separate later validation block and a still
later test block. Timestamp groups are kept intact. Alpha is selected from
0, .25, .5, .75 and 1 using validation MAE; ties prefer 1. Test labels never
select that fold's weight or fit its vocabulary/neighbors.

MAE and RMSE compare predicted ratings `1 + 4 * score` with observed ratings
on the same test observations as profile-only, item-mean and global-mean
baselines. The mapping is uncalibrated and must be assessed through the reported
baselines. Reports include each fold, aggregate test metrics, collaborative
coverage, split times, provenance and limitations. The selected fold parameters
are not automatically deployed.

From the repository root, after configuring the backend environment:

```powershell
# Genuine timestamped explicit ratings; private input and output stay outside Git.
./backend/.venv/Scripts/python.exe evaluation/run.py --protocol hybrid_kfold --folds 5 --ratings C:/private/ratings.csv --output C:/private/hybrid-evaluation.json

# Separate unseen-user evaluation.
./backend/.venv/Scripts/python.exe evaluation/run.py --protocol cold_start --folds 5 --ratings C:/private/ratings.csv --output C:/private/cold-start.json

# Reproducible fictional plumbing demonstration only.
./backend/.venv/Scripts/python.exe evaluation/hybrid_demo.py --output .local/hybrid-synthetic-demo.json

# No inputs: all research metrics remain not_measured.
./backend/.venv/Scripts/python.exe evaluation/run.py --protocol hybrid_kfold --output .local/hybrid-pending.json
```

Ratings columns are `user_id,item_id,rating,profile_text,item_text,occurred_at`.
Use pseudonymous IDs, one latest explicit integer rating 1–5 per user/item,
consistent item text and timezone-aware timestamps. Profile/item text must be a
valid historical snapshot; later edits require versioned research data. Every
fold needs 20 training ratings from five users. Insufficient data yields
`not_measured`; invalid observations are rejected.

The [synthetic receipt](../evaluation/reports/hybrid-synthetic-demo.json) contains
168 generated observations, five folds and 99 test observations with a
collaborative signal. These numbers demonstrate code execution only. No
participants, genuine ratings or research findings were created.

## Objectives and remaining evidence

| Objective | Current implementation | Evidence still needed |
| --- | --- | --- |
| 1. Profiling | Persisted student background/skills/interests and company profile; relevant text now contributes to matching | Consented, suitable real profile data |
| 2. Opportunity management | Verified company posting, editing, publication, closure and owned applicant review | Real partner/pilot validation |
| 3. Hybrid and MAE/RMSE | Shared content/collaborative scorer, cold starts and same-holdout statistical comparisons | Genuine held-out ratings and weight calibration |
| 4. Assistant and CSAT | Configured assistant plus optional authenticated satisfaction feedback and offline CSAT analysis | Actual satisfaction responses; a high score cannot be guaranteed by implementation |
| 5. k-fold tests | Grouped cold-start folds and chronological warm-user hybrid folds | Adequate genuine timestamped observations |
| 6. BERTScore | Existing offline candidate/reference evaluation with separate human factual-review accounting | A fixed genuine answer/reference set and completed human review |

See [evaluation instructions](../evaluation/README.md) for CSAT and BERTScore
commands. BERTScore measures semantic similarity; it does not establish factual
correctness. Synthetic examples and functional tests remain separate from pilot
results.
