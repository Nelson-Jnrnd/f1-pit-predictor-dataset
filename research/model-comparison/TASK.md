# Train on more races and compare model choices

Issue: [#53](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/issues/53).
Status: prepared task. Independent scoped authoring review PASS.
Starting point: PR #52 at 0469828240e06988f8af2c3d82f4cffee23e5853, stacked on #51, #50 and #49.

## Goal

Find out how well the models predict on later races, and whether race percentages improve on counting laps ahead.

The current viewer uses B0 fitted on Spain 2024 alone. It has no measured accuracy result. Lap-based prediction was a design choice, not the winner of a comparison.

## Scope and authorization

The owner asked to prepare this task. This preparation does not start downloads, training, scoring, merging, deployment, or changes to the viewer. Start execution when the owner requests it.

Use the approved development races: 2024 R10–R24 and 2025 R1–R24, 39 races in total. Do not use protected 2026 final-test data. Do not include older archives just to increase the dataset size.

Keep the current Austria viewer, saved model, forecasts, sources, and position exports unchanged. New training runs get separate output directories and identities.

## Existing rules to read

Read AGENTS.md and its required governance first. Then read:

- verification/EVALUATION_PROTOCOL.md, especially sections 4, 6 and 7.
- verification/SUPPORT_MATRIX.md and decisions/2026-10-10-v2-race-day-archive-evidence-exception.md.
- design/OBSERVATION_RECONSTRUCTION.md and design/TARGET_RECONSTRUCTION.md.
- design/PREDICTION_CONTRACT.md and design/REPLAY_BACKTEST.md.
- pipeline/README.md and pipeline/development.py.
- research/development-race/REPORT.md and research/replay-readability/REPORT.md.

These files own the data, target, output, split, scoring, and review rules. This task does not replace them.

## Delivery 1: a reusable development dataset

- Acquire and freeze only the 39 allowed races. Record hashes, source dates and retrieval details. Verify each race rather than assuming every archived file is usable.
- Produce the approved historical observations, eligibility decisions and separate future labels. Record every attempted checkpoint and every exclusion.
- Extend the Spain/Austria-only implementation only where broader sessions require it, including supported red-flag restarts. Never invent missing timing or silently discard a difficult race.
- Refuse final-test reads before opening a source or target file.
- Cache completed work and resume interrupted runs. Use finite network timeouts, bounded retries, and per-race progress. Save useful checkpoints and commit completed work.
- Report the usable race count, driver count, checkpoint count, label count, and exclusion reasons. Repeated checkpoints are not independent pit stops.

A source or session the current code cannot safely handle is a named dependency on observation/target implementation. Resolve it under the approved design, or explain the limitation before scoring.

## Delivery 2: declare the comparisons before testing

Start with B0 and the specified B1 tyre-age model. Add these two experimental candidates:

1. **Percentage ahead:** use future distance as a fraction of scheduled race length, h / N_T, instead of a raw lap offset.
2. **Percentage completed:** use race progress, (L + h) / N_T.

Here L is the driver's completed lap count, h is the number of further completed laps before entry, and N_T is the race distance known at prediction time. h = 0 means entry during the next in-lap.

The two percentage candidates use the same available grid information as B0. Comparing B1 separately tests the value of tyre age and compound.

Before scoring any validation race, commit each candidate's exact fitting rule, bins or curve, final no-event treatment, unsupported-input policy, floor, seeds, dependencies, and complexity rank. Choose bin boundaries and fitted transforms from training races only. Count these candidates within the protocol's maximum of 10, excluding B0/B1.

A percentage representation is internal to the estimator. Every candidate still returns the same complete per-lap probability vector and no-event probability. Keep the open final region and the declared probability floor. Account for different percentage widths per lap when converting rates or masses. Do not simply treat a per-percentage rate as a per-lap rate.

Do not guess unsupported B0 rates or change its declared fit to make it look complete. A new fallback or smoothing rule is a separately declared candidate, not a silent baseline repair.

## Delivery 3: test on later races

Follow the existing P-F1 development folds exactly:

| Test races | Training races |
| --- | --- |
| 2025 R1–R6 | 2024 R10–R24 |
| 2025 R7–R12 | Earlier development races, including 2025 R1–R6 |
| 2025 R13–R18 | Earlier development races, including 2025 R1–R12 |
| 2025 R19–R24 | Earlier development races, including 2025 R1–R18 |

Each cutoff is the first race in the test block. Do not randomly mix laps or drivers from the same race across training and testing. Do not fit on all 39 races before testing these blocks.

Run B0, B1 and the declared candidates on identical checkpoints. Use the protocol's main log score: lower is better. Include the probability assigned to no further stop.

Report missing forecasts and uncertain labels alongside scores. A model must not appear better by refusing harder checkpoints. Apply the approved full-cohort and common-intersection comparison rules, including all unmatched counts. If a full comparison cannot be made, clearly label the smaller comparison and its limits.

Use the existing checks for calibration, window coverage, and uncertainty across races. Follow the declared model-selection rule instead of choosing a winner by eye. Separate planned tests from any later exploratory additions.

## Deliverables and completion checks

- Reproducible commands, pinned dependencies, dataset manifests, and separate frozen models and prediction runs for each fold.
- A comparison table showing scores, forecast coverage, exclusions and race counts for every model.
- Results by race and by race phase, including early-lap forecast availability.
- A short report answering: do percentages help, do tyre features help, and what remains uncertain? Include source assumptions and no unsupported accuracy claim.
- Tests for forbidden final-data access, cutoffs, future-information isolation, percentage-to-lap conversion, complete probability totals, failures and resume behavior.
- Independent review using one full scoped review and, if needed, one bounded re-review.

Preparation creates this task only. Executing it does not authorize a final evaluation, replacing the viewer model, merging, or public release. Those remain separate steps.

## Preparation review

Reviewer: /root/review_model_comparison_task.
Full scoped review: PASS on substantive head 18210cafdb8cf2958f0e1781997ddabdfdaa38ba, with no required findings.
[GitHub review](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/pull/54#pullrequestreview-5516205576).
This final note records the result only. It does not start task execution or change the reviewed scope.
