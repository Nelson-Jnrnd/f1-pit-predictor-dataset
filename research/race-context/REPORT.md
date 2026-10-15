# Does richer race information improve pit-stop prediction?

The richer Random Forest beats the simple baselines on probability scoring.
The selected procedure is **Random Forest: tyres + pace/traffic (RF_CONTEXT)**. Its chronological
validation log score is **2.169202**, compared with
**2.343230** for the lap baseline and
**2.278056** for race progress. Lower is better;
these values are probability penalties, not percentage accuracy.

On the exploratory 2025 alert diagnostic, **2,293 of
3,201 alerts are false**. Precision is **28.4%**
and recall is **44.3%**. The threshold is fixed using earlier
seasons. These figures describe alerts at successive checkpoints, so one stop
can trigger several alerts. It still raises frequent false alerts and misses many positive checkpoints.
Its practical value remains limited. This does not establish 2026 performance.

## Exactly what was compared

| Procedure | Inputs available at the checkpoint | Mean log score |
| --- | --- | ---: |
| Lap baseline | Laps ahead; grid length | 2.343230 |
| Race progress | Fraction of scheduled race completed | 2.278056 |
| Stable tyre baseline | Causal tyre age/compound and race progress; fixed logistic model | 2.263576 |
| RF_GRID | Completed/scheduled laps, race progress and future offset | 2.341942 |
| RF_TYRE | RF_GRID plus current compound and projected tyre age | 2.182081 |
| RF_CONTEXT | RF_TYRE plus completed-lap pace, last-minus-best pace, rank, numeric gaps | 2.169202 |

All forests use 64 trees, depth at most 12 and at least 100 sampled rows per leaf.
Settings are fixed; no validation tuning search was run. Negative training-period
sampling is corrected by weights. There are no balanced class weights, learned
imputation or fitted probability calibration. The full timing distribution has
explicit no-stop probability; it is not an arbitrary conversion of a binary score.

The raw lowest score belongs to **Random Forest: tyres + pace/traffic**. The registered rule selects
**Random Forest: tyres + pace/traffic** after allowing for race-level uncertainty and preferring the
simpler procedure within one standard error. Selection does not establish utility.
Original B1 remains unsupported. B1-R0, historically called B-thesis, is only a
B1 diagnostic and is not the historical Random Forest. Historical result IDs stay
unchanged. [Thesis and feature audit](THESIS_AND_FEATURES.md) identifies the pinned
historical evidence and exact retained/excluded features.

## What the added information contributed

The following matched comparisons use the identical complete resolvable cohort.
Positive differences favour the model in the second column. Intervals group
checkpoints by race and are conditional on these fitted procedures.

| Compared procedure | Added-information procedure | Log-score reduction | 95% race-cluster interval |
| --- | --- | ---: | --- |
| Random Forest: timing | Random Forest: timing + tyres | 0.159861 | 0.117755 to 0.201967 |
| Random Forest: timing + tyres | Random Forest: tyres + pace/traffic | 0.012879 | -0.007036 to 0.032793 |
| Stable tyre baseline | Random Forest: timing + tyres | 0.081495 | 0.026931 to 0.136058 |
| Race progress | Random Forest: timing | -0.063886 | -0.115381 to -0.012392 |

Tyres provide a clear improvement. The smaller extra gain from pace/traffic
has a race-level 95% interval spanning zero, so that added value remains uncertain.
The nested forest comparisons isolate tyre information and the pace/traffic group.
The stable-tyre-versus-forest comparison also changes the estimation procedure.
The timing-baseline comparison changes the available grid representation as well
as the model. Feature importance alone is not used as evidence of improvement.

## Training and evaluation scope

All 133 admitted pre-2026 races support the declared features, including explicit
missing values. Training uses earlier races; validation uses every admitted race
in the next season. No random split of laps or drivers is used. Existing raw and
canonical evidence, prior source assumptions and all #55/#56 results are preserved.
Legacy CSVs do not enter training. No eventual wet-running, completion or stop-count
filter is introduced. Circuit, stint ordinal, track status and weather are omitted
for the reasons in the feature audit; unsupported data are not fabricated.

| Validation season | Earlier training races | Later validation races | Scored checkpoints per procedure | Unknown share of eligible target cohort |
| --- | ---: | ---: | ---: | ---: |
| 2019 | 18 | 19 | 8,481 | 54.4% |
| 2020 | 37 | 12 | 6,946 | 42.2% |
| 2021 | 49 | 16 | 7,896 | 53.5% |
| 2023 | 65 | 21 | 21,433 | 8.2% |
| 2024 | 86 | 23 | 24,220 | 4.2% |
| 2025 | 109 | 24 | 24,674 | 7.2% |

Every procedure forecasts **122,816 / 122,816 eligible
validation checkpoints** and is scored on **93,650 identical resolved
checkpoints** across 115 races. Each model retains the full attempt accounting.
There are no restricted feature-cohort winners or missing model forecasts.
Unknown/truncated outcomes stay unknown and are never no-stop negatives. Results
describe the resolvable population. Prior validation exposure makes these further
comparisons development, not fresh confirmation.

## Alert performance in 2025

An alert concerns qualifying tyre-service entry in the first up to three canonical
regions: usually the current lap and next two. For short grids, the last region
is open-ended. The same definition is used for every model.

| Model | Earlier-season threshold | Precision | Recall | F1 | False alerts |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lap baseline | 0.14 | undefined | 0.0% | 0.0% | 0 |
| Race progress | 0.07 | 10.4% | 91.6% | 18.7% | 16,079 |
| Random Forest: tyres + pace/traffic | 0.24 | 28.4% | 44.3% | 34.6% | 2,293 |
| Random Forest: timing | 0.15 | 10.7% | 46.4% | 17.4% | 7,913 |
| Random Forest: timing + tyres | 0.22 | 25.6% | 47.8% | 33.3% | 2,850 |
| Stable tyre baseline | 0.15 | 14.7% | 60.9% | 23.6% | 7,261 |

Selected-model confusion: **908 correct alerts**, **2,293
false alerts**, **1,140 missed positive checkpoints**, and
**20,333 correct no-alert checkpoints**. Positive prevalence is
8.3%. Always alerting yields that precision and 100% recall;
never alerting yields 0% recall and undefined precision. Accuracy alone would hide
this imbalance. All 99 probability thresholds and their precision/recall/confusion
tradeoffs are retained in the saved results.

There are **4.8 false checkpoint alerts per
eligible driver-race** across 479 driver-races.
At least one alert detects **353 of 697**
identifiable stops with known in-horizon evidence. There are
**555 repeated positive checkpoint alerts**.
Stops without known horizon evidence remain outside this separate diagnostic.
The 2025 binary cohort has 24,674 known outcomes,
1,921 unknown eligible outcomes and
541 excluded attempts. Missing forecasts for known
binary outcomes: 0.

The diagnostic threshold uses validation seasons through 2024 only; 2025 was already
exposed in previous development and remains exploratory. A separate final threshold
of **0.22** uses all pre-2026 validation forecasts.
Its confusion counts are in-sample threshold-selection statistics, not the 2025
figures above. No final-test outcomes influenced either threshold.

## Calibration and timing windows

The selected model's short-horizon Brier score is **0.083067**,
versus **0.090575** for the lap baseline.
Lower is better. Reliability tables for short-horizon probability, first-region
probability and no-event probability are saved; no probability correction was fitted.

The median pit window spans **12 regions**
(middle half 8–17).
Conditional event coverage is **76.6%**, versus
**81.8%** mean predicted conditional mass. Absolute window coverage
is 43.3%, versus 51.5% predicted mass.
Open-ended windows account for 1.1%; they have no finite
upper lap-width bound. Wider windows can increase coverage while saying less
about when a stop will occur.

Paired log-score evidence includes CR2+t intervals,9,999 Webb draws with fixed seed
and leave-one-race-out influence checks. Alert-share and Brier uncertainty, per-race
confusion and leave-one-race-out ratios remain saved. Checkpoints are not treated
as independent stops. LOW_POWER and the historical archive assumptions remain
explicit; intervals do not include training variability.

## Frozen model and review status

Selection and alert thresholds were frozen before full-data refitting. The selected
procedure was fitted on all 133 admitted races with cutoff 2026-01-01. B0's existing
byte-verified full-data refit is reused with exact scope/DELIVERY checks. Model
artifacts, source feature evidence, predictions, targets opened in the actual read
ledger, full metrics, input/fold bindings and final completion hashes are retained
in private evidence. The explicit provenance repair is described in README.md;
original execution/model identities are not relabelled.

No new 2026 source or outcome was read. Existing R1–R16 prior exposure declarations,
P-F1/P-F2 final lists and lock gates remain binding. No EvaluationLock, deployment,
viewer replacement or merge was performed. Independent protocol/source review is
recorded in PROTOCOL_REVIEW.md and FEATURE_REVIEW.md; implementation/result review
is recorded separately in REVIEW.md. Review PASS alone does not mean useful
prediction quality.
