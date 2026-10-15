# Reproduce the four-hypothesis loop

Restore the existing #57 feature and validation archives, and the 133-race
canonical archive referenced by research/expanded-pre2026/DATASET.md. Verify their
private receipts before extraction at repository root. No raw reacquisition or
historical rerun is necessary. Existing source assumptions remain binding.

```sh
python -m pip install -r research/race-context/requirements.txt
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 timeout 180 python -m unittest discover -s pipeline/tests -v
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 timeout 3600 python -m pipeline.hypotheses --candidate H1_PERCENT
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 timeout 3600 python -m pipeline.hypotheses --candidate H2_DETAIL
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 timeout 3600 python -m pipeline.hypotheses --candidate H3_BOOST
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 timeout 3600 python -m pipeline.hypotheses --candidate H4_RECENT
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 timeout 3600 python -m pipeline.hypotheses --finish
PYTHONPATH=. python research/hypotheses/build_report.py
```

Run in that order, inspecting each summary before proceeding. Four fixed tests
exhaust the candidate budget. A poor result does not authorize parameter search
or a replacement candidate. The hypotheses are exploratory development, including
2025. No 2026 source/outcome opening or final evaluation is part of these commands.

The runner checks dependencies, reviewed feature/admission evidence, all parent
manifests and the exact reference delivery. `inputs.json` binds the registration,
protocol review, Python module bytes, feature evidence and reference completion.
Each fold binds its training scope, fitted model, predictions, scores and practical
metrics. Predictions are saved before each validation-label opening. The actual
opening ledger retains every read. Saved fold/model resumes require the exact
configuration and payload hashes. The reference's all-data model is reused if
the declared recommendation remains RF_CONTEXT.

The completed-run path verifies original saved payloads and exits without writes.
It verifies the original execution, not equivalence to arbitrary changed current
code. For another procedure use a newly reviewed registration and new output path.
Per-candidate summaries may be deterministically regenerated from immutable folds
before final completion. Final completion binds the whole delivery.

Private evidence includes the exact execution source snapshot and local Git
provenance. Git publication uses equivalent source trees through the GitHub
connector because CLI write authentication is unavailable. Local execution
revisions are identifiers, not hosted commit links. No numerical identity is
rewritten to impersonate a later published commit.

The presentation builder is build_presentation.mjs. It reads the final summary
directly, requires the bundled Artifact Tool runtime, and exports editable PPTX
plus a PDF copy. Exact commands and validation status are recorded in the review
and private validation evidence. The retrieval receipt identifies saved private
archives. Detailed payloads are not public release material.
