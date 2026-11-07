# Research evaluation — FR12 / NFR08

Executable tools and input schemas are in [evaluation/README.md](../evaluation/README.md). The current [report](../evaluation/reports/pending.json) records all research metrics as **not measured** because no genuine pilot rating dataset, CSAT cohort or fixed answer-reference set was supplied.

```bash
backend/.venv/bin/python -m unittest evaluation.test_evaluation -v
backend/.venv/bin/python evaluation/run.py --output evaluation/reports/pending.json
```

Eight integrity tests passed using explicitly synthetic, temporary unit fixtures. They verify user-disjoint holdouts, training-only vocabulary fitting through the complete pipeline, comparable baselines, rejection of missing/invalid ratings, participant deduplication, chronological warm-user alpha selection using validation only, and separate pending semantic/human factual review. Their generated test scores are not pilot findings.

Actual optional numerical relevance ratings are stored separately from views; views are never converted into rating labels. Optional satisfaction feedback after guidance is authenticated, strictly 1–5, and retains one latest response per user without storing conversation text. Before a pilot, agree informed participation, retention/deletion rules, pseudonymization and the cohort/export procedure. Do not use local synthetic accounts as respondents.

The offline recommender evaluator compares an explicitly labeled profile-only reference model against training item/global means on the same user-disjoint holdout. It does not validate the deployed hybrid weighting; alpha remains1 until suitable real held-out evaluation supports another value. Five grouped folds run only when input counts support the documented protocol.

BERTScore requires optional installed dependencies and a local model, paired reference answers, model/layer configuration and separate human factual checks. No model weights were downloaded and no semantic/factual accuracy number is claimed. External LLM calls remain disabled at the user’s request; local resource lookup cites approved material and states its limits.

Warm-user evaluation uses `--protocol warm_temporal` and timestamped observations. It selects alpha on prior validation only, never the final test labels, while preserving missing feedback and per-item content-only fallbacks. This protocol is separate from unseen-user grouped cross-validation. See evaluation/README.md for exact counts, assumptions and limitations.
