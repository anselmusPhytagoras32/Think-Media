# Actual BERTScore on synthetic answers — FR12/NFR08

**NOT research results. This demonstration uses six fixed fictional answer/reference pairs, zero human participants and no live Gemini answers.**

The local command exercises the existing `evaluation.run.bertscore` function with a real embedding model. Semantic similarity is calculated; human factual review is not simulated. The original genuine-data report, `reports/pending.json`, remains unchanged.

## Primary-source findings

The [official BERTScore implementation](https://github.com/Tiiiger/bert_score/blob/v0.3.13/bert_score/score.py) accepts candidate/reference sentences, a local `model_type`, explicit layer count, CPU device, IDF setting and baseline-rescaling flag. It returns precision, recall and F1 tensors. Its [model-loading source](https://github.com/Tiiiger/bert_score/blob/v0.3.13/bert_score/utils.py) loads the configured tokenizer/model and selects the requested representation layer. The repository evaluator calls this interface and records aggregate tensor means. This is contextual embedding similarity, not an independent factual correctness check.

The [first-party DistilBERT model card](https://huggingface.co/distilbert/distilbert-base-uncased) describes an English uncased distilled BERT encoder and warns of inherited training biases. The [pinned configuration](https://huggingface.co/distilbert/distilbert-base-uncased/blob/12040accade4e8a0f71eabdb258fecc2e7e948be/config.json) defines six layers. This demonstration uses layer **6** for compact local execution; it does not claim this is an optimal model/layer for OJT answer evaluation.

## Installation and pinned assets

The prepared environment uses native Windows Python 3.13 and its already installed PyTorch/Transformers dependencies. Only `bert-score==0.3.13` is installed under the repository's ignored `.local/semantic-deps` directory; the backend environment and global packages are not modified:

```powershell
python -m pip install --target .local/semantic-deps --no-deps --retries 0 bert-score==0.3.13
```

The isolated package uses the existing compatible dependencies; the resulting report records actual versions. The published distribution version is 0.3.13, while its internal `bert_score.__version__` string is 0.3.12; both are reported rather than silently treating them as identical.

Model repository: `distilbert/distilbert-base-uncased`. Pinned revision: **`12040accade4e8a0f71eabdb258fecc2e7e948be`**. The only weight file used is `model.safetensors` (267,954,768 bytes), SHA256 **`5e3f1108e3cb34ee048634875d8482665b65ac713291a7e32396fb18f6ff0063`**, verified against the repository's [pinned metadata API](https://huggingface.co/api/models/distilbert/distilbert-base-uncased/revision/12040accade4e8a0f71eabdb258fecc2e7e948be?blobs=true). Config/tokenizer/license/card files are verified against their pinned Git blob hashes; SHA256 hashes of every asset are recorded in the computed report.

For a fresh checkout, explicitly download these public assets into `.local/semantic-model` before scoring. This setup command uses a finite download timeout and writes only the named local asset files:

```powershell
$revision = '12040accade4e8a0f71eabdb258fecc2e7e948be'
$modelDirectory = Join-Path (Get-Location) '.local/semantic-model'
New-Item -ItemType Directory -Force -Path $modelDirectory | Out-Null
$files = @('config.json','tokenizer.json','tokenizer_config.json','vocab.txt','README.md','LICENSE','model.safetensors')
foreach ($file in $files) {
    $uri = 'https://huggingface.co/distilbert/distilbert-base-uncased/resolve/' + $revision + '/' + $file
    Invoke-WebRequest -UseBasicParsing -TimeoutSec 900 -Uri $uri -OutFile (Join-Path $modelDirectory $file)
}
```

Do not use pickle `.bin` weights, unpinned model aliases or remote model code. No access token is required for these public files.

## Execute and interpret

From the repository root:

```powershell
python evaluation/semantic_demo.py
```

Execution is offline after setup. The wrapper verifies the pinned assets, restricts model/tokenizer loading to that local directory, explicitly sets `trust_remote_code=False`, `local_files_only=True` and safetensors loading, and redirects library cache/config directories inside `.local`. It runs on CPU with seed 0 and four PyTorch threads. It does not connect to the application database or any AI provider.

The fixed CSV includes questions and fictional approved-resource excerpts so the source of each authored reference is visible. Candidate answers deliberately include paraphrases, incomplete answers and contradictions. All `human_factual_correct` cells are blank. The source set is a demonstration fixture, not a human-validated research reference set. The report records `human_factual_review.status=not_measured` and six pending reviews.

The command prints the actual mean precision/recall/F1 and writes `reports/semantic-synthetic-demo.json`. Values are raw embedding similarity scores; **never describe them as a percentage of correct answers or chatbot accuracy**. A semantically similar contradiction can still score highly. No separate baseline answer set is supplied, so baseline comparison remains explicitly unmeasured. IDF and baseline rescaling are disabled and recorded. No live assistant effectiveness, user satisfaction, pilot findings or research validation is established by these numbers.

The report's `dataset_origin` is `synthetic demonstration; not pilot evidence`, and its status is `computed_synthetic_demo`. Preserve those labels when presenting or copying the results.

## Actual execution — November 8, 2026

Two offline runs completed with the same mean precision **0.8384666443**, recall
**0.8194179535**, and F1 **0.8282506466** on the six authored pairs. All model
assets passed the pinned integrity checks. All six human factual reviews remain
pending. The load report discards the pretrained masked-language-model head;
BERTScore uses the matched base encoder, not that task-specific output head.
No API provider, application database or human participant was involved.
