# Offline evaluation — FR12 / NFR08

Run from the repository root using the backend environment:

```bash
backend/.venv/bin/python evaluation/run.py --output evaluation/reports/pending.json
backend/.venv/bin/python -m unittest evaluation.test_evaluation -v
backend/.venv/bin/python evaluation/run.py --ratings /private/ratings.csv --folds 5 --csat /private/csat.csv --answers /private/answers.csv --output /private/evaluation.json
```

No data is manufactured. Missing datasets produce `not_measured`, never numerical results. Tests generate explicitly synthetic fixtures only. Do not report their scores as pilot evidence.

Ratings CSV: `user_id,item_id,rating,profile_text,item_text`. Use pseudonymous IDs, one latest explicit integer rating 1–5 per user/item, consistent item text. Split users before fitting. TF-IDF vocabulary fits training rows only; the same held-out observations evaluate profile-cosine, training item-mean and global-mean baselines. At least four users/eight observations are required. Five grouped folds require five users/ten observations. This offline profile reference model does not validate deployed hybrid weighting; alpha remains 1 pending a suitable genuine validation run. Reports include provenance hashes, counts, seed, configuration, holdout hashes, user separation and limitations.

CSAT CSV: `participant_id,rating`, one actual five-point response per pseudonymous participant. Reports include real supplied sample count, distribution, mean and sampling limitations. A proposed target of 4/5 is not a measured result. The application accepts optional authenticated guidance feedback through `/api/v1/feedback/csat`; no feedback is inferred from activity.

Answers CSV: `id,candidate,reference`, optional `human_factual_correct` containing true/false/blank. Maintain a fixed reference set and record separate human factual review. Optional `--bert-model /local/model --bert-layers 12` uses installed `bert-score`/PyTorch and a local model only; no weights or provider calls are downloaded automatically. Missing model/dependencies produce pending results. BERTScore alone does not establish factual correctness. Model layer count is an explicit configuration and must match the selected model.

Collect real consented data and establish provenance before claiming research findings. Store private CSVs outside Git; do not include names, emails, resumes or application documents. No genuine datasets or respondent records have been provided for this implementation.

The BERTScore call uses the [official score interface](https://github.com/Tiiiger/bert_score/blob/master/bert_score/score.py).
It has now been executed offline against pinned local model weights on six
explicitly synthetic pairs; [commands and evidence](SEMANTIC_DEMO.md) describe
the result and its limits. This does not supply genuine research observations
or human factual review. The genuine-data report remains pending.

## Warm-user hybrid validation

For users with prior observed ratings, add timezone-aware `occurred_at` timestamps and select `--protocol warm_temporal`. This uses the first60%/next20%/last20% of each user's observations as training/validation/test, respectively. Require at least five users/five distinct ratings each and at least20training observations; ambiguous timestamp ties across boundaries are rejected. Only training text/ratings fit features and neighbors. A grid of alpha0/.25/.5/.75/1 is selected on validation MAE, with ties preferring1. The untouched test set compares the chosen hybrid, profile-only and observed item/global means. Neighbors require two co-observed items; missing feedback remains missing and uncovered items use content-only scores. Validation observations are not folded back into training histories. This evaluates warm users; it is not an unseen-user claim and cannot be combined with the grouped-fold flag.

```bash
backend/.venv/bin/python evaluation/run.py --protocol warm_temporal --ratings /private/timestamped-ratings.csv --output /private/warm-evaluation.json
```

This provides a reproducible weight-selection protocol, not a validated weight without genuine input. Deployed candidate eligibility, bounded pools and runtime feature construction still require integration checks; no metric from synthetic unit fixtures is a research result.
