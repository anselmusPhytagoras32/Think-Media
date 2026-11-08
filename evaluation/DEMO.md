# Synthetic evaluation demonstration — FR12/NFR08

**NOT research results. All inputs are generated fixtures. There are zero real participants and zero real interactions.**

This optional local presentation demonstrates that the existing evaluation pipeline executes. The genuine research status stays in `reports/pending.json`, which the demonstration never modifies.

From the repository root in Linux/WSL, run:

```bash
backend/.venv/bin/python evaluation/demo.py
```

From PowerShell with the existing Ubuntu environment:

```powershell
wsl -d Ubuntu -- backend/.venv/bin/python evaluation/demo.py
```

The script writes `evaluation/reports/synthetic-demo.json` and prints a short, explicitly synthetic result. It uses existing installed dependencies, temporary CSV files and the real functions in `evaluation/run.py`. It performs no database operations, provider calls or downloads.

## Reproduction and interpretation

The default seed is **20261107**. Python's `random.Random(seed)` draws arbitrary integer labels from 1 to 5. There are 100 rating fixture rows across 10 fictional user IDs and 10 fictional item IDs, plus 12 satisfaction fixture rows. The generator does not simulate consented observations, measured relevance, survey participants, or real satisfaction. Text and timestamps are fixed; each synthetic user has ten distinct items with unambiguous hourly order. Input hashes, package versions and configuration are recorded. `--seed INTEGER` can reproduce another intentionally synthetic example.

The cold-start evaluator holds out 25% of synthetic users, fits vocabulary on training rows only, and computes MAE/RMSE for the profile reference model and item/global-mean baselines on the same holdout. Five grouped folds use separate training-only fits. The warm-user evaluator uses within-user chronological 60/20/20 splits, selects alpha on prior validation and evaluates on untouched later rows. These are separate protocols; neither establishes deployed recommendation quality.

Numerical results are calculations on fixture values. A high or low error says nothing about ThinkMedia's research effectiveness. The example deliberately uses arbitrary labels rather than tuning the fixture to make the recommender look successful. Satisfaction output demonstrates arithmetic and distributions only. Its sample count is the number of fictional fixture rows, never a respondent count.

This particular report leaves BERTScore pending. The separate
[semantic demonstration](SEMANTIC_DEMO.md) executes the real scorer on six fixed
fictional answer/reference pairs with a pinned local model. Human factual review
remains **not measured** in both reports; no human assessment is simulated.
No deployment alpha is changed by either demonstration.

Suggested presentation wording:

> This is a reproducible demonstration using synthetic input. The pipeline computes error metrics, comparable baselines and grouped folds. These figures are not pilot findings. Genuine evaluation still requires consented ratings, satisfaction responses, reference answers and human factual checks.

Every saved report prominently declares `dataset_origin="synthetic demonstration; not pilot evidence"`. The original evaluator statuses are retained under `evaluator_status`, while computed demonstration sections use `computed_synthetic_demo` to prevent confusion with research results.
