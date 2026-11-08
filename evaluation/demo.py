"""FR12/NFR08: reproducible synthetic pipeline demonstration, never pilot data.

Run from the repository root:
    backend/.venv/bin/python evaluation/demo.py
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
from importlib.metadata import version
import json
from pathlib import Path
import random
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.run import bertscore, csat, pending, recommender, warm_hybrid


DATASET_ORIGIN = "synthetic demonstration; not pilot evidence"
NOTICE = "NOT research results. All input values are generated fixtures; no human participants or actual interactions are represented."
DEFAULT_SEED = 20261107
OUTPUT = Path(__file__).resolve().parent / "reports" / "synthetic-demo.json"


def fixture_rows(seed: int):
    """Create arbitrary numerical labels, without pretending measured relevance."""
    rng = random.Random(seed)
    profiles = [
        "python data analysis statistics",
        "web development react accessibility",
        "design communication presentation",
        "software testing security databases",
    ]
    item_texts = [
        "python programming beginner learning resource",
        "statistics data analysis spreadsheet preparation",
        "react web development accessible forms",
        "communication workplace presentation guide",
        "software testing quality assurance internship",
        "database sql transactions security fundamentals",
        "design typography portfolio preparation",
        "resume interview career preparation guide",
        "python backend api development opportunity",
        "professional teamwork workplace safety resource",
    ]
    start = datetime.fromisoformat("2026-11-01T09:00:00+08:00")
    ratings = []
    for user in range(10):
        for position in range(10):
            item = (user + position) % 10
            ratings.append({
                "user_id": f"synthetic-user-{user:02d}",
                "item_id": f"synthetic-item-{item:02d}",
                "rating": rng.randint(1, 5),
                "profile_text": profiles[user % len(profiles)],
                "item_text": item_texts[item],
                "occurred_at": (start + timedelta(hours=position)).isoformat(),
                "dataset_origin": DATASET_ORIGIN,
            })
    satisfaction = [
        {"participant_id": f"synthetic-fixture-row-{index:02d}",
         "rating": rng.randint(1, 5), "dataset_origin": DATASET_ORIGIN}
        for index in range(12)
    ]
    return ratings, satisfaction


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def mark_synthetic(result):
    """Keep evaluator numbers, correcting generic supplied-data provenance."""
    if isinstance(result, list):
        return [mark_synthetic(value) for value in result]
    if not isinstance(result, dict):
        return result
    marked = {key: mark_synthetic(value) for key, value in result.items()}
    if "status" in marked:
        marked["dataset_origin"] = DATASET_ORIGIN
        if marked["status"] in {"measured_offline", "measured_from_supplied_responses"}:
            marked["evaluator_status"] = marked["status"]
            marked["status"] = "computed_synthetic_demo"
    if "provenance" in marked:
        marked["provenance"]["origin"] = "Deterministically generated temporary fixtures from evaluation/demo.py; no consented research data."
    return marked


def build_report(seed: int):
    ratings, satisfaction = fixture_rows(seed)
    with TemporaryDirectory(prefix="thinkmedia-synthetic-evaluation-") as temporary:
        root = Path(temporary)
        rating_path = root / "synthetic-ratings.csv"
        satisfaction_path = root / "synthetic-satisfaction.csv"
        write_csv(rating_path, ratings)
        write_csv(satisfaction_path, satisfaction)
        cold = mark_synthetic(recommender(rating_path, seed=seed, folds=5))
        warm = mark_synthetic(warm_hybrid(rating_path))
        satisfaction_result = mark_synthetic(csat(satisfaction_path))
    satisfaction_result["limitations"] = [
        "No people were surveyed. sample_count counts synthetic fixture rows only.",
        "These arbitrary numbers demonstrate aggregation, not satisfaction with ThinkMedia.",
    ]
    return {
        "requirement": "FR12/NFR08 pipeline demonstration only",
        "dataset_origin": DATASET_ORIGIN,
        "notice": NOTICE,
        "seed": seed,
        "configuration": {
            "generator": "Python random.Random(seed); integer labels drawn uniformly from 1 through 5",
            "rating_fixture_rows": len(ratings),
            "synthetic_user_ids": 10,
            "synthetic_item_ids": 10,
            "satisfaction_fixture_rows": len(satisfaction),
            "real_participants": 0,
            "real_interactions": 0,
            "packages": {name: version(name) for name in ("scikit-learn", "numpy", "pandas")},
            "fixtures": "Temporary CSVs; deterministic LF bytes and SHA256 provenance; removed after evaluation.",
            "network_calls": 0,
            "database_operations": 0,
        },
        "recommender_cold_start": cold,
        "recommender_warm_temporal": warm,
        "satisfaction_aggregation": satisfaction_result,
        "assistant": {
            "dataset_origin": DATASET_ORIGIN,
            "bertscore": mark_synthetic(bertscore(None)),
            "human_factual_review": mark_synthetic(pending("No fixed answer/reference set or human factual review supplied. No review is simulated.")),
        },
        "limitations": [
            NOTICE,
            "Arbitrary random labels intentionally do not establish predictive quality or favorable performance.",
            "This exercises the existing offline reference evaluator; it does not validate runtime ranking or select a deployed alpha.",
            "Cold-start user-disjoint results and warm-user temporal results answer different questions and must be presented separately.",
            "evaluation/reports/pending.json remains the report for absent genuine research data.",
            "No BERTScore model/dependency download, live LLM call, app record, or mock survey respondent is created.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    if not 0 <= args.seed <= 2**32 - 1:
        parser.error("seed must be between 0 and 4294967295 for the split protocol")
    report = build_report(args.seed)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    comparison = report["recommender_cold_start"]["comparison"]
    print(NOTICE)
    print(f"Synthetic rating rows: 100; real participants: 0; seed: {args.seed}")
    for name in ("model", "item_mean_baseline", "global_mean_baseline"):
        result = comparison[name]
        print(f"{name}: example MAE={result['mae']:.6f}, RMSE={result['rmse']:.6f}")
    print("Grouped folds: 5; warm temporal validation: computed; BERTScore/human review: pending.")
    print(f"Report: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
