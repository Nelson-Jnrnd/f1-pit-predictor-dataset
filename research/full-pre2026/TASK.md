# Issue 53: all available pre-2026 data

Status: original audit and diagnostic implementation independently passed. The
owner-approved continuation admits 133 independently verified pre-2026 races.
Expanded registration and results live in research/expanded-pre2026. This task supersedes the next experiment's
scope, preserving the completed TASK, REGISTRATION, REPORT and REVIEW from
research/model-comparison and PRs #54/#55 unchanged.

## Authorized outcome

Audit all available pre-2026 CSVs and archives. Use every admitted earlier race
for development. Validate chronologically on later pre-2026 races. After model
selection, refit once on all admitted pre-2026 races. Keep 2026 for locked final
testing only. No merge, deployment, public data release or viewer replacement.

## Canonical dependencies

AGENTS.md and all four required governance files; verification/SUPPORT_MATRIX.md;
verification/EVALUATION_PROTOCOL.md; decisions/2026-10-10-v2-race-day-archive-evidence-exception.md;
design/OBSERVATION_RECONSTRUCTION.md, TARGET_RECONSTRUCTION.md,
PREDICTION_CONTRACT.md, REPLAY_BACKTEST.md; pipeline/README.md;
research/model-comparison/TASK.md, REGISTRATION.md, REPORT.md, REVIEW.md, DATASET.md;
research/development-race/REPORT.md and research/replay-readability/REPORT.md.

## Admission gate

CSV schema alignment alone cannot prove historical availability or tyre service.
Never turn same-row PitStatus into the current target or final TotalLaps into a
prediction-time feature. Audit records remain evidence, outside model input.
Older archive scopes remain UNVERIFIED_ARCHIVE or UNSUPPORTED under the existing
matrix. No generalization of the race-day exception is implicit in this task.
An owner decision or independently reviewed availability evidence must resolve
this gate before expanded reconstruction/training. Preserve protected-data guards.

## Work that can proceed before that gate

- Hash and audit every 2018–2023 CSV, including season files, missing fields,
  repeated driver-laps, absent service/availability evidence and schema variants.
- Reconcile pre-2026 archive metadata and existing admitted manifests.
- Extend practical diagnostics without modifying/retraining frozen PR #55 models.
- Diagnose B1 hazard and final-component failures separately on pre-2026 training.
- Declare the expanded protocol and alert selection rule before any new experiment.
- Test unknown outcomes, bounded region sets, open tails, event deduplication,
  chronological threshold selection, source/forecast hashes and final refusal.
- One independent scoped review, followed by at most one bounded re-review.

## Completion gate

Expanded selection/refit/final lock cannot be claimed complete while admission is
blocked. A partial diagnostic report must distinguish saved 39-race results from
the requested larger experiment. No final testing is authorized in this task.

## Owner continuation approval

The Product Owner approved the bounded older-archive exception on 14 October 2026
at 23:04 Europe/Zurich. The decision record above now records approval. Continue
with independent admission verification, expanded training and one final refit.
Technical estimator/selection refinements must be explicitly registered, reviewed
and committed before new validation scoring. Keep prior reports frozen.
