# Reproduce issue 53

First download `F1_Development_Model_Comparison_53.zip` referenced in DATASET.md.
Extract it into the repository root. It contains the large frozen source,
observation and run payloads; their manifests and hashes are kept in Git.

```sh
python -m zipfile -e /path/to/F1_Development_Model_Comparison_53.zip .
```

Then, from repository root, with Python 3.12:

```sh
python -m pip install -r research/model-comparison/requirements.txt
python -m unittest discover -s pipeline/tests -v
python -m pipeline.comparison --dataset research/model-comparison/dataset-2 --sources research/model-comparison/sources --output research/model-comparison/evaluation-2
```

The last command checks every completed fold's input/code/dependency identities
and saved hashes, then reuses the frozen outputs. Use a new output directory to
refit and rescore against the same frozen dataset:

```sh
python -m pipeline.comparison --dataset research/model-comparison/dataset-2 --sources research/model-comparison/sources --output /tmp/new-model-comparison
```

To reconstruct fresh canonical observations from the frozen sources:

```sh
python -m pipeline.comparison_data reconstruct --sources research/model-comparison/sources --output /tmp/new-development-dataset
python -m pipeline.comparison --dataset /tmp/new-development-dataset --sources research/model-comparison/sources --output /tmp/fresh-model-comparison
```

Fresh executions use new run identities. Semantic checkpoints, probability vectors
and scores are the reproduction targets, rather than identical run UUIDs. Model
inputs come only from canonical observations. Forecasts are written before the
separate, ledger-recorded validation-label opening.

Sources are already frozen. Acquisition is optional and development-only:

```sh
python -m pipeline.comparison_data acquire --sources /tmp/new-development-sources --output /tmp/acquisition-status --workers 4
```

Requests have a 20-second timeout, three attempts and bounded retry pauses. Each
race reports progress. Complete endpoint caches and complete reconstructed races
are verified and reused. Failed races remain in progress records; the command
exits unsuccessfully rather than silently shrinking the dataset.

Interrupted comparisons reuse completed folds. An unfinished fold is rerun with
new forecast identity and durable ledger entries; completed source/dataset work
is reused. Changing source, registration, helper code, dependencies or saved
artifact bytes prevents unsafe result reuse. There is no resumable partial fit.

Full canonical observations/initializations use lossless xz compression to reduce
repository size. Other dataset/run artifacts use gzip or JSON. Frozen manifests
bind all payload hashes. comparison_pack.py records the verified earlier manifest
and adds initialization/resolution lineage to the model projection without changing
canonical observations, initializations or target resolutions.

Nothing here opens 2026 data, evaluates a final lock, replaces the viewer, merges
branches or deploys the application.
