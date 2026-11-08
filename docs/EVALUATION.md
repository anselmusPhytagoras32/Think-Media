# Research evaluation — FR12 / NFR08

Executable tools and input schemas are in [evaluation/README.md](../evaluation/README.md). The current [report](../evaluation/reports/pending.json) records all research metrics as **not measured** because no genuine pilot rating dataset, CSAT cohort or fixed answer-reference set was supplied.

```bash
backend/.venv/bin/python -m unittest evaluation.test_evaluation -v
backend/.venv/bin/python evaluation/run.py --output evaluation/reports/pending.json
```

Eight integrity tests passed using explicitly synthetic, temporary unit fixtures. They verify user-disjoint holdouts, training-only vocabulary fitting through the complete pipeline, comparable baselines, rejection of missing/invalid ratings, participant deduplication, chronological warm-user alpha selection using validation only, and separate pending semantic/human factual review. Their generated test scores are not pilot findings.

Actual optional numerical relevance ratings are stored separately from views; views are never converted into rating labels. Optional satisfaction feedback after guidance is authenticated, strictly 1–5, and retains one latest response per user without storing conversation text. Before a pilot, agree informed participation, retention/deletion rules, pseudonymization and the cohort/export procedure. Do not use local synthetic accounts as respondents.

The offline recommender evaluator compares an explicitly labeled profile-only reference model against training item/global means on the same user-disjoint holdout. It does not validate the deployed hybrid weighting; alpha remains1 until suitable real held-out evaluation supports another value. Five grouped folds run only when input counts support the documented protocol.

BERTScore requires installed dependencies and a local model, paired reference
answers, model/layer configuration and separate human factual checks. The
[semantic demonstration](../evaluation/SEMANTIC_DEMO.md) now runs the actual
scorer on six explicitly fictional pairs using a pinned local DistilBERT model.
Two runs produced mean precision 0.8384666443, recall 0.8194179535 and F1
0.8282506466. These are fixture similarity calculations; they do not establish
factual correctness, live assistant quality or pilot effectiveness. All six
human reviews remain pending. The genuine-data pending report is unchanged.
Gemini 3.8 Flash integration is prepared but live responses still require the
private runtime credential; current resource lookup cites approved material.

Warm-user evaluation uses `--protocol warm_temporal` and timestamped observations. It selects alpha on prior validation only, never the final test labels, while preserving missing feedback and per-item content-only fallbacks. This protocol is separate from unseen-user grouped cross-validation. See evaluation/README.md for exact counts, assumptions and limitations.
