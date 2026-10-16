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
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 timeout 1800 env PYTHONPATH=. python research/hypotheses/preserve_b0.py
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
metrics. Predictions are saved before each validation-label opening. The original runner wrote an actual
opening ledger. The archival losses below limit its surviving evidence. Saved fold/model resumes require the exact
configuration and payload hashes. The reference's all-data model is reused if
the declared recommendation remains RF_CONTEXT.

The completed-run path verifies original saved payloads and exits without writes.
It verifies the original execution, not equivalence to arbitrary changed current
code. For another procedure use a newly reviewed registration and new output path.
Per-candidate summaries may be deterministically regenerated from immutable folds
before final completion. Final completion binds the whole delivery.

Independent review found that recomputed B0 metadata was referenced but not
separately saved. `preserve_b0.py` deterministically reconstructs its exact artifact
identity from each H4 scope and any newly selected refit scope. It must match
B0_ref, q_open and k_terciles exactly. It preserves the original completion,
models and forecasts, adds supplemental B0 JSON and an actual read ledger, then
binds everything in delivery-complete.json. Repeating the helper verifies that
complete delivery and exits without writes. The pipeline CLI alone verifies its
original completion; use the helper to verify the complete supplemented delivery.

## H4 execution interruption

The first H4 execution stopped during 2024 validation. The session/process was
absent; no traceback or cgroup OOM event established a cause. Four completed
folds and the 2024 fitted estimator survived. Existing partial race forecasts
were copied into interrupted-validation before an exact-cache resume. No
completed model was retrained and no completed fold was rewritten. Validation
forecasts for that incomplete fold receive new snapshot/run identities; their
numerical probabilities are checked against the preserved partial forecasts.
The actual read ledger records repeated reads. This is execution recovery, not
a parameter retry or a new candidate. interruption.json records the event.

The first completion captured a redirected stdout log before its final success
message was printed. The original completion expected the empty stdout snapshot.
The full captured log is preserved separately; the exact original empty snapshot
was restored, without changing the completion, models, forecasts, scores or
selection. stdout-binding-repair.json records both hashes. The supplemental
delivery binds this explicit repair. Subsequent validation logs stay outside the
bound result directory.

The original private execution source snapshot and local Git bundles did not
survive the workspace reset. The reconstructed inputs reproduce the exact original
input digest, including all numerical Python source hashes. Git publication uses equivalent source trees through the GitHub
connector because CLI write authentication is unavailable. Local execution
revisions are identifiers, not hosted commit links. No numerical identity is
rewritten to impersonate a later published commit.

The presentation builder is build_presentation.mjs. It reads the final summary
directly, requires the bundled Artifact Tool runtime, and exports editable PPTX
and rendered previews. A PDF copy can be exported through the bundled soffice
converter. Exact commands and validation status are recorded in the review
and private validation evidence. The retrieval receipt identifies saved private
archives. Detailed payloads are not public release material.

## Recovery after the workspace reset

The four candidate archives and all parent archives survived with their recorded
SHA-256 digests. Their 24 completed validation folds, estimators, predictions,
scores and per-candidate summaries remain unchanged. The separate hypothesis
root ledger, completion manifests, final selected model, B0 supplements, original
selection-freeze, interruption/stdout evidence and reviewer scratch files were
lost. The prior independent checks remain recorded conclusions. Historical
opening times, forecast-before-label ordering and interruption parity cannot be
re-audited from the missing root files. Do not interpret reconstructed metadata
as proof of those historical operations.

The original final-fit log had 132 entries for 133 training races, missing 2020
round 13. The following recovery performs only a new final fit of the already
published H1 choice, with unchanged parameters. It does not rerun any validation
candidate, add a hypothesis or restore invented historical timestamps.

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python -m research.hypotheses.recover_delivery aggregate
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python -m research.hypotheses.recover_delivery refit
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python -m research.hypotheses.recover_delivery b0
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python -m research.hypotheses.recover_delivery complete
python -m research.hypotheses.recover_delivery verify
```

Restore candidate and parent archives at repository root first. Aggregate recovery
reconstructs inputs to the exact original digest, verifies all fold bindings and
scores, and reasserts the published H1 selection before the new fit. The new fit
persists a read intent before labels and checks each actual read, ordered race
scope and source hashes. It saves all 133 reads and B0 explicitly. B0 reconstruction
for the six H4 folds must match their original artifact IDs. New recovery timestamps
are not original execution timestamps. The new estimator digest is compared only
to the original digest recorded before the outage, because the original estimator
bytes are unavailable.

Use `recovery-complete.json` for the recovered delivery. Its selected artifact is
`recovery/selected-refit/model.json`. `recovery/inventory.json` states archival
limits. The new completion binds surviving candidates and recovery files without
pretending to be the lost original completion. A completed recovery verifies and
exits without writes. A partially written new fit is preserved and requires
explicit review before another attempt. Keep logs outside the evaluation directory.
