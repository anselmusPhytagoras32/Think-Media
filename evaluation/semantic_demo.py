"""FR12/NFR08 actual offline BERTScore on fixed synthetic answers, not research.

Requires repo-local bert-score and pinned DistilBERT assets; downloads are an
explicit setup step documented in SEMANTIC_DEMO.md. This command is offline.
"""

from __future__ import annotations

import csv
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / ".local" / "semantic-deps"
MODEL = ROOT / ".local" / "semantic-model"
FIXTURES = ROOT / "evaluation" / "semantic-fixtures.csv"
OUTPUT = ROOT / "evaluation" / "reports" / "semantic-synthetic-demo.json"
REVISION = "12040accade4e8a0f71eabdb258fecc2e7e948be"
MODEL_ID = "distilbert/distilbert-base-uncased"
ORIGIN = "synthetic demonstration; not pilot evidence"
NOTICE = "NOT research results. Six fixed fictional resource/answer pairs; zero human respondents and no live model-generated answers."
EXPECTED_GIT_BLOBS = {
    "config.json": "150367d8744161cd17b3f6462a14f3a9648752da",
    "tokenizer.json": "949a6f013d67eb8a5b4b5b46026217b888021b88",
    "tokenizer_config.json": "e5c73d8a50df1f56fb5b0b8002d7cf4010afdccb",
    "vocab.txt": "fb140275c155a9c7c5a3b3e0e77a9e839594a938",
    "README.md": "1db487d688fd5ddc3c6714a4a3a3fe5f679cbf04",
    "LICENSE": "f49a4e16e68b128803cc2dcea614603632b04eac",
}
EXPECTED_WEIGHTS = "5e3f1108e3cb34ee048634875d8482665b65ac713291a7e32396fb18f6ff0063"


def digest(path: Path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verified_assets():
    hashes = {}
    for name, expected in EXPECTED_GIT_BLOBS.items():
        data = (MODEL / name).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if blob != expected:
            raise ValueError(f"Pinned model asset integrity mismatch: {name}")
        hashes[name] = hashlib.sha256(data).hexdigest()
    weights = MODEL / "model.safetensors"
    if weights.stat().st_size != 267954768 or digest(weights) != EXPECTED_WEIGHTS:
        raise ValueError("Pinned safetensors integrity mismatch")
    hashes[weights.name] = EXPECTED_WEIGHTS
    config = json.loads((MODEL / "config.json").read_text(encoding="utf-8"))
    if config.get("auto_map") or config.get("model_type") != "distilbert" or config.get("n_layers") != 6:
        raise ValueError("Only the pinned six-layer built-in DistilBERT architecture is permitted")
    return hashes


def main():
    print(NOTICE, flush=True)
    hashes = verified_assets()
    with FIXTURES.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 6 or any(row["dataset_origin"] != ORIGIN or row["human_factual_correct"] for row in rows):
        raise ValueError("Expected six explicit synthetic pairs with blank human review")
    os.environ.update({
        "HF_HOME": str(ROOT / ".local" / "hf-cache"),
        "HF_HUB_CACHE": str(ROOT / ".local" / "hf-cache" / "hub"),
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "TORCH_HOME": str(ROOT / ".local" / "semantic-torch"),
        "MPLCONFIGDIR": str(ROOT / ".local" / "semantic-matplotlib"),
    })
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(DEPS))
    import bert_score
    import torch
    import transformers
    from evaluation.run import bertscore

    if not Path(bert_score.__file__).resolve().is_relative_to(DEPS.resolve()):
        raise ValueError("Use the repository-local bert-score package, never a global replacement")
    torch.manual_seed(0)
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    original_model = transformers.AutoModel.from_pretrained
    original_tokenizer = transformers.AutoTokenizer.from_pretrained

    def safe_model(path, *args, **kwargs):
        if Path(path).resolve() != MODEL.resolve():
            raise ValueError("Only the verified local model may be loaded")
        return original_model(path, *args, **{
            **kwargs, "trust_remote_code": False,
            "local_files_only": True, "use_safetensors": True,
        })

    def safe_tokenizer(path, *args, **kwargs):
        if Path(path).resolve() != MODEL.resolve():
            raise ValueError("Only the verified local tokenizer may be loaded")
        return original_tokenizer(path, *args, **{
            **kwargs, "trust_remote_code": False, "local_files_only": True,
        })

    # The existing evaluator stays unchanged. Guards add explicit local-only,
    # safe serialization and remote-code restrictions to its library loads.
    with patch.object(transformers.AutoModel, "from_pretrained", side_effect=safe_model), patch.object(
        transformers.AutoTokenizer, "from_pretrained", side_effect=safe_tokenizer
    ):
        result = bertscore(FIXTURES, MODEL, layers=6)
    if result.get("status") != "measured_offline" or not result.get("metrics"):
        raise RuntimeError(f"Actual BERTScore did not execute: {result.get('reason')}")
    result["evaluator_status"] = result["status"]
    result["status"] = "computed_synthetic_demo"
    result["dataset_origin"] = ORIGIN
    result["provenance"]["origin"] = "Fixed fictional QA fixtures in evaluation/semantic-fixtures.csv; no pilot observations."
    result["configuration"]["model"] = ".local/semantic-model"
    report = {
        "requirement": "FR12/NFR08 semantic pipeline demonstration only",
        "dataset_origin": ORIGIN, "notice": NOTICE,
        "status": "computed_synthetic_demo",
        "semantic_similarity": result,
        "human_factual_review": {
            "status": "not_measured", "reviewed": 0, "pending": 6,
            "reason": "All human_factual_correct fields are blank. No human review is simulated.",
        },
        "baseline": {"status": "not_measured", "reason": "No separate baseline candidate set was supplied; no baseline comparison is claimed."},
        "execution": {
            "command": "python evaluation/semantic_demo.py",
            "python": platform.python_version(), "system": platform.system(),
            "device": "cpu", "seed": 0, "torch_threads": 4,
            "packages": {name: version(name) for name in (
                "bert-score", "torch", "transformers", "numpy", "safetensors",
            )},
            "bert_score_internal_version": getattr(bert_score, "__version__", None),
            "evaluator_sha256": digest(ROOT / "evaluation" / "run.py"),
            "fixture_sha256": digest(FIXTURES),
            "model": {"repository": MODEL_ID, "revision": REVISION,
                      "num_layers": 6, "asset_sha256": hashes,
                      "trust_remote_code": False, "weights": "safetensors", "local_files_only": True},
            "live_provider_calls": 0, "database_operations": 0,
        },
        "limitations": [
            NOTICE,
            "Candidates are authored fixtures, including partial and deliberately contradictory answers; none are actual Gemini answers.",
            "Contextual similarity can be high for a false or contradictory answer. BERTScore does not establish factual correctness.",
            "DistilBERT layer 6 was chosen for a compact local demonstration, not tuned or validated on genuine domain data.",
            "idf=false; baseline rescaling=false; aggregate precision/recall/F1 come from the existing evaluator.",
            "This does not replace genuine ratings, CSAT responses, reference-set review or pilot evaluation; pending.json remains unchanged.",
        ],
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["metrics"], indent=2), flush=True)
    print(f"Real computation completed on {len(rows)} synthetic pairs; human review pending. Report: {OUTPUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
