# Legacy thesis evidence

Status: **Approved — bounded re-review passed on PR #10**  
Owner: Wave 1 issue #4 — factual legacy evidence only

This document records what the repository shows about the thesis-era pit-prediction work. It is an evidence baseline for V2 specification work, not V2 semantic authority. Nothing here defines the V2 observation point, pit event, target, output, horizon, evaluation protocol, feature set, model, or architecture.

## Evidence snapshot

The repository contains more than one historical formulation, so there is no single target meaning that can safely be inferred from the phrase “thesis baseline.” The evidence below distinguishes the observed variants.

| Evidence | Observed fact | Authority limit |
| --- | --- | --- |
| [`README.md` at `2d143361`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/2d143361d2a4721f88665bea540ef418707a3ac5/README.md) | The data were collected with FastF1 and intended to train a model “for predicting when a driver will make a pit stop during a race,” with lap-by-lap CSVs. | High-level thesis framing only; it does not define forecast timing or label alignment. |
| [`model_training.ipynb` at `2d143361`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/2d143361d2a4721f88665bea540ef418707a3ac5/model_training.ipynb) | The initial baseline creates `is_pitting = (PitStatus == 'InLap')`, removes `PitStatus` from inputs, and randomly splits rows 80/20 with `train_test_split(..., random_state=42)`. | This is an observed early baseline, not evidence that the final thesis formulation always used same-row labeling. |
| [`training_rf` head `7426255`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/tree/7426255ba9a8185b93fd097a86c49d43aaac5b0c) | The branch-head baseline notebook loads 2019–2022 seasons through an external/local `f1pitpred` package, produces train/test sets, and trains a class-weighted Random Forest. Its recorded test output is highly imbalanced (370 positives of 13,820 rows) and reports about 0.73 balanced accuracy, 0.71 positive recall, and 0.07 positive precision. | The imported `f1pitpred` preprocessing implementation is not present in this branch tree, so exact target alignment and split semantics cannot be reconstructed from that notebook alone. The branch also contains `test_target/shift_*` and `test_target/no_shift_*` artifacts, which is evidence that target shifting was explicitly compared, not evidence that either variant is V2-canonical. |
| [`training_svm` head `981a76b`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/tree/981a76b831ad67c8e6a303d93dd7fab71c36dd9a) | This historical branch contains broad model experimentation, but its branch-head `model_training.ipynb` still trains a Random Forest through the same unavailable `f1pitpred` preprocessing package. | The branch name is not sufficient evidence that an SVM was the selected or final thesis model. No such conclusion is carried forward. |
| [`cleaning` head `fe5abd6`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/tree/fe5abd65acd335c05a472db1e5a45bdbe8cac5b9) | The later refactor makes preprocessing source visible and computes `PitStatusShift = groupby(...).PitStatus.shift(-1)` within `(Year, RoundNumber, DriverNumber)`, then defines `is_pitting = (PitStatusShift == 'InLap')`. The shift is computed before later row-removal steps. | The shifted value refers to the next row in the grouped pre-filtered order; that referenced row may itself be removed later. This historical formulation does not retroactively redefine the earlier notebook or define V2 semantics. |

## Thesis-era problem and workflow

The stable thesis-era intent visible across the repository is behavioral prediction from historical F1 race data: estimate pit-stop likelihood/timing from lap-level race information. A separate `strategy_calculator.ipynb` explicitly frames race strategy as minimizing race time by choosing a tyre strategy; that optimization thread is therefore distinct from the pit-behavior prediction baseline and must not be conflated with it.

The historical workflow was broadly:

1. Extract race/lap data from FastF1, storing one row per driver lap with tyre/stint, track status, gaps/position, selected telemetry, weather, and pit information.
2. Clean and encode lap-level data, derive a binary pit label, remove some direct identifiers and target-source columns, then form train/test data.
3. Train classification models, with Random Forest clearly evidenced in both the thesis-era notebook and later refactor; historical branches/notebooks also contain broader modeling experiments.
4. Evaluate row-level binary predictions with confusion-matrix-derived classification metrics; later work added DVC/DVCLive-style pipeline/metric recording.

The exact details changed across historical artifacts and should be cited by ref rather than described as one immutable pipeline.

## Label and target behavior actually evidenced

### Early baseline: same-row `InLap`

At `2d143361`, `model_training.ipynb` creates a Boolean target directly from the row’s own `PitStatus == 'InLap'`. There is no shift in that target construction. On its face, this is classification of whether the represented lap is an in-lap.

### Later refactor: shifted next row before later filters

On the `cleaning` branch, [`f1_pit_predictor/preprocessing/cleaning.py`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/fe5abd65acd335c05a472db1e5a45bdbe8cac5b9/f1_pit_predictor/preprocessing/cleaning.py) groups rows by year, race round, and driver and computes `PitStatusShift` with `shift(-1)` before `_process_missing_values` and `_process_target` perform later row removals. `is_pitting` is then defined from that already-computed shifted value. A positive retained row therefore means that the next row in the group order as it existed at shift time had `PitStatus == 'InLap'`; it does **not** imply that the shifted-to row itself survives the final preprocessing. Rows whose current or shifted pit status is `OutLap` are subsequently excluded, and rows without `LapTime` plus lap 1 are also removed later in the pipeline.

This target evolution is material. “Legacy target” must therefore be qualified by artifact/ref; V2 must not silently inherit either alignment.

## Data and preprocessing behavior

The later `cleaning` branch provides the most explicit source-level evidence of the historical data pipeline:

- [`extraction.py`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/fe5abd65acd335c05a472db1e5a45bdbe8cac5b9/f1_pit_predictor/extraction.py) builds `PitStatus` as `OutLap` when FastF1 `PitOutTime` is present, `InLap` when `PitInTime` is present, otherwise `NoPit`.
- The same extraction code samples `DriverAhead` and `DistanceToDriverAhead` in a one-second window at lap start, and backward-as-of joins weather to `LapStartTime`. The row also carries lap fields such as `LapTime`, tyre/stint state, position/gaps, and pit-derived fields.
- [`cleaning.py`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/fe5abd65acd335c05a472db1e5a45bdbe8cac5b9/f1_pit_predictor/preprocessing/cleaning.py) removes every row belonging to a `(Year, RoundNumber, DriverNumber)` group that contains any `INTERMEDIATE` or `WET` compound; removes driver-race groups that fail the heuristic `max(LapNumber) + 3 >= max(TotalLaps)`; removes driver-race groups with more than four pit stops; fills several missing gap/ahead values with `-1`; drops rows without `LapTime`; and removes lap 1.
- [`features.py`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/fe5abd65acd335c05a472db1e5a45bdbe8cac5b9/f1_pit_predictor/preprocessing/features.py) one-hot encodes `Compound` and `Track` using an encoder fitted on training data, and removes identifiers/weather, `PitStatus`, shifted status, `IsAccurate`, year/round, and `NumberOfPitStops`. `LapTime`, lap/tyre/stint state, track-status flags, position/gap fields, and `TotalLaps` are not in that removal list.
- [`splitting.py`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/fe5abd65acd335c05a472db1e5a45bdbe8cac5b9/f1_pit_predictor/preprocessing/splitting.py) randomly assigns complete `(Year, RoundNumber, DriverNumber)` groups to train or test. This is an improvement over the early random-row split, but different drivers from the same race may still land on opposite sides, and there is no chronological holdout.
- [`params.yaml`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/fe5abd65acd335c05a472db1e5a45bdbe8cac5b9/f1_pit_predictor/params.yaml) selects `is_pitting` and a class-weighted Random Forest; [`base_trainer.py`](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/blob/fe5abd65acd335c05a472db1e5a45bdbe8cac5b9/f1_pit_predictor/modeling/base_trainer.py) records accuracy in the later refactor.

## Material assumptions, limitations, and leakage risks

These are historical evidence/risks, not judgments about what V2 must choose.

- **Mixed time semantics inside a row.** Extraction explicitly samples some telemetry/weather at lap start while retaining `LapTime` and pit-derived fields from the represented lap. The repository does not define a single historical observation instant that makes every field’s availability unambiguous.
- **Target alignment changed.** The early notebook labels the same row; the later cleaner derives the label from the next row in the driver-race group order before later row filtering. Any comparison that says only “legacy binary target” can hide a material alignment difference.
- **Potential feature leakage depends on observation time.** `LapTime`, tyre/stint state, position/gaps, `TotalLaps`, and historically `NumberOfPitStops` appear in or near modeling inputs. Without a declared observation instant, their legitimate availability for the predicted event cannot be established from the legacy artifacts alone. The later refactor removes `NumberOfPitStops`, but not every time-sensitive field.
- **Early split leakage/correlation risk.** The pre-V2 notebook’s random row split can place neighboring laps from the same driver/race in both train and test.
- **Later split still shares event context.** Grouping by driver-race prevents one driver’s race laps from being split, but can place other drivers from the same event in the opposite set and randomly mixes seasons.
- **Selection bias.** The later cleaner excludes driver-race groups containing any `INTERMEDIATE`/`WET` compound, groups that fail its near-race-distance completion heuristic, and groups with more than four pit stops. Reported performance therefore does not automatically represent the omitted conditions; the completion heuristic is not a definitive finisher/non-finisher classification.
- **Class imbalance is material.** A `training_rf` notebook output has only 370 positives among 13,820 test rows; class weighting was used. Accuracy alone can therefore be misleading as a performance summary.
- **Historical reproducibility is incomplete.** The `training_rf`/`training_svm` notebooks import `f1pitpred` preprocessing code that is not stored in those branch trees. Their exact preprocessing cannot be asserted solely from the notebooks.
- **Branch names are weak evidence.** `training_svm` does not, at its head, establish an SVM as the selected baseline; artifact contents take precedence over branch naming.

## What is worth preserving as evidence

Preserve the legacy artifacts as comparison material for: FastF1 provenance; lap/driver/race terminology; the existence of a binary pit classifier baseline; target-shift experimentation; class-imbalance handling; the move from row-random to driver-race-grouped splitting; historical feature families; and observed failure/performance characteristics.

Do **not** inherit by implication: either legacy target alignment, a historical row timestamp, any feature’s point-in-time legality, driver-race weather-compound/completion-heuristic/pit-count filters, train/test grouping, model family/hyperparameters, missing-value sentinels, class weighting, metrics, thresholds, tyre-strategy optimization semantics, or live/replay behavior.

## Historical ambiguities resolved for this evidence slice

- **Which one label definition was “the” thesis target?** Repository evidence shows at least two definitions (same-row and shifted-next-row-before-later-filtering). This slice records both and deliberately does not collapse them into one canonical target.
- **Does `training_svm` prove the final thesis model was SVM?** No. Its branch-head baseline notebook trains Random Forest, so the evidence supports experimentation, not that conclusion.
- **Can the exact RF/SVM branch preprocessing be reconstructed?** Not from those branch heads alone because the imported `f1pitpred` implementation is absent. The later `cleaning` branch is cited separately where source is explicit.

## Unresolved questions and routing

| Classification | Question | Owner / handling |
| --- | --- | --- |
| Cross-slice | At exactly what race moment does a V2 observation exist, and which fields are then legally available? | Race Observation / Point-in-Time State slice. |
| Cross-slice | What constitutes the V2 pit event, target alignment, censoring, and edge-case treatment? | Pit Event / Target Semantics slice. |
| Cross-slice | What output/horizon/window should V2 expose in replay? | Prediction Output / Replay Semantics slice. |
| Cross-slice | What split and scoring protocol makes V2 evaluation leakage-safe and decision-relevant? | Evaluation / Leakage-Safe Validation slice. |
| Later-phase | Which concrete features, transformations, models, hyperparameters, schemas, and pipeline architecture should be implemented? | Design / Verification / Implementation after semantic locks. |

There is no Product Owner decision required by this evidence slice. Any later V2 decision that uses this material must be made and persisted by the artifact that canonically owns that semantic choice.

## Review record

- **Status:** Approved
- **Reviewer:** Independent scoped reviewer; GitHub review recorded by `Nelson-Jnrnd`.
- **Full scoped review:** PR #10 review `pullrequestreview-5140919429` on head `281ad8479dbd4f010c8c35897eb02516e05c7028` — **REWORK REQUIRED**; one Major and one Minor finding.
- **Rework:** both findings addressed on head `78eea6d96a2b52b97ff4f235742806817f19d6e8` by describing the pre-filter shift ordering and exact driver-race filtering heuristics.
- **Bounded re-review:** PR #10 review `pullrequestreview-5141211663` on head `78eea6d96a2b52b97ff4f235742806817f19d6e8` — **PASS**.
- **Review date:** 2026-09-08
- **Findings after re-review:** No Blocking, Major, or Minor findings remain.
