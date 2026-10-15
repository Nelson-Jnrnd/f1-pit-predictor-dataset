# Expanded pre-2026 model comparison

## Result

The registered rule selects **Race progress (PERCENT_PROGRESS)**. Its pooled mean validation
log score is 2.278056, compared with
2.343230 for the lap baseline. Lower is better.
This is a probability penalty, not a percentage accuracy.

On the exploratory 2025 alert diagnostic, precision is 10.4% and
recall is 91.6%. Its threshold uses earlier validation seasons only.
These are development findings under the approved archive assumptions. They do
not establish 2026 performance. The current viewer remains unchanged.

## Data audit and chronological split

All 173 calendar sessions before 2026 were audited. The fixed list admits 133:
94 older raw archives and 39 frozen race-day sessions. Forty are excluded:
22 unavailable 2022 sessions, 13 counter failures, two roster failures, one
lifecycle failure and two previously unsupported 2018 races. Every exclusion stays
in admission/verify.json. No inaccessible race or missing stream is fabricated.

The separate CSV audit covers 109 files: 104 race exports and five overlapping
season exports. No CSV enters training. Same-row PitStatus does not identify the
next qualifying tyre-service entry, and final TyreLife or TotalLaps cannot establish
what was available earlier. Historical raw compound names outside the declared
categories map to OTHER. Stint age uses causal TimingAppData updates.

| Validation season | Earlier training races | Validation races |
| --- | ---: | ---: |
| 2019 | 18 | 19 |
| 2020 | 37 | 12 |
| 2021 | 49 | 16 |
| 2023 | 65 | 21 |
| 2024 | 86 | 23 |
| 2025 | 109 | 24 |

2018 supplies initial training only. Each subsequent fold trains on every admitted
earlier race and predicts the later season before joining its labels. Validation
covers 115 races. No random split of checkpoints or drivers is used. No 2022 fold
exists because those archives were unavailable. The final refit uses all 133 races.

The canonical dataset contains 150,033 attempts,
137,821 eligible labels, and
39,065 unknown outcomes. Unknown outcomes never become
negatives. There are 3,566 distinct qualifying
events identified by at least one resolved checkpoint. Several checkpoints can
refer to the same stop. They do not create independent stop events.

## Models and probability scores

B0 learns typical timing by laps ahead. Percentage ahead scales future distance
by scheduled race length. Race progress uses the fraction of the race completed.
Original B1 adds causal tyre age and compound. Its original fitting rules remain
unchanged. The separate stable tyre candidate uses the same tyre hazard features,
a fixed ridge penalty of 0.001 and B0's empirical final no-event share. No validation
search selected that penalty. Python 3.12, NumPy 2.3.5 and SciPy 1.17.0 fit the models.

| Model | Forecasts / eligible | Scored checkpoints | Mean log score |
| --- | ---: | ---: | ---: |
| Laps ahead | 122,816 / 122,816 | 93,650 | 2.343230 |
| Original tyre model | 15,129 / 122,816 | 9,123 | Unsupported; partial fallback |
| Percentage ahead | 122,816 / 122,816 | 93,650 | 2.341169 |
| Race progress | 122,816 / 122,816 | 93,650 | 2.278056 |
| Stable tyre model | 122,816 / 122,816 | 93,650 | 2.263576 |

Selection uses the complete, identical resolvable cohort. It prefers the simplest
procedure within one race-level standard error of the best score. B1 lacks a
supported full-cohort fit, so the predeclared expanded protocol uses B0 as reference.
B1 failures and unmatched counts stay visible. A smaller fallback cohort cannot win.

B0 minus selected-model log score is 0.065174, with 95% race-cluster
interval 0.025993 to 0.104355. Positive values favour
the selected model. This interval is conditional on the fitted procedures.

## Practical alerts in 2025

An alert predicts a qualifying tyre-service entry in R0, R1 or R2. R0 is the current
in-lap after the checkpoint. Short grids can include their open final region, so
this is not always literally three laps of clock time. Thresholds maximize F1 on
the fixed 0.01–0.99 grid, choosing the highest tied threshold. This diagnostic
selects thresholds on validation seasons through 2024 and applies them to 2025.
Prior 2025 exposure makes it exploratory.

| 2025 diagnostic | Lap baseline | Selected model |
| --- | ---: | ---: |
| Correct alerts | 0 | 1,875 |
| False alerts | 0 | 16,079 |
| Missed positive checkpoints | 2,048 | 173 |
| Correct no-alert checkpoints | 22,626 | 6,547 |
| Precision | Undefined | 10.4% |
| Recall | 0.0% | 91.6% |
| Positive prevalence | 8.3% | 8.3% |
| Earlier-season threshold | 0.14 | 0.07 |

The baseline's earlier-selected 0.14 threshold raises no alerts in 2025. Its
precision is undefined and recall is zero. The threshold stays fixed despite
this later result.

The selected diagnostic includes 24,674 known binary outcomes,
1,921 unknown eligible outcomes and 541
excluded attempts. Missing forecasts for known binary outcomes:
0. Unknown outcomes never become no-stop labels.
Always alerting gives 8.3% precision and 100% recall. Never
alerting gives zero recall and undefined precision. These counts describe checkpoints.

At least one alert precedes 637 of
697 identifiable stops with
known in-horizon checkpoints. Each event counts once. There are
1,238 repeated positive checkpoint
alerts. Stops without identifiable/resolved horizon evidence stay outside this
diagnostic. Full missing-forecast and unique-stop accounting remains saved.

## Pit windows, calibration and uncertainty

Across validation, the selected model's median window spans
13 canonical regions, with middle half
9–19. Conditional event coverage is
76.7%, compared with 81.4% mean predicted mass.
A wider window can catch more stops while giving less precise timing.
1.1% of windows include an open final region and have no
finite upper bound in laps. Width uses region count rather than a fabricated
finite width for that tail.

Across the full scored window cohort, mean predicted hit probability is
46.0% and observed frequency is 43.3%.
The selected three-region Brier score is 0.092284, versus
0.090575 for B0. Lower is better. Reliability tables
compare predicted probabilities with observed frequencies. No calibration
correction was fitted. No-stop calibration, entropy and ranked probability scores
also remain in the saved summaries.

Uncertainty groups checkpoints by race using CR2+t intervals, Webb bootstrap and
leave-one-race-out checks. Per-season scores, truncation shares, forecast failures
and availability remain visible. Checkpoints never count as independent stops.
Results describe resolvable outcomes, not the unknown population. Sparse-cohort
LOW_POWER flags and inherited prior-exposure declarations remain binding.

## Tyre fitting investigation

The original B1 has numerical hazard failures and a final no-stop logistic
component with only one class in the saved training blocks. That component has no
finite unpenalized maximum-likelihood fit. More data alone does not repair the
registered estimator. research/full-pre2026/tyre-diagnostic-1 preserves the separate
investigation. TYRE_RIDGE is an explicitly new candidate with bounded optimization
and boundary handling, never a relabelled B1 repair. Omitted inputs or unseen
compounds use exact, counted B0 fallback. True fit failures remain failures.

## Frozen selection and refit

selection-freeze.json records the selected procedure, evidence and final alert
thresholds before refitting. The selected final threshold is
0.07, chosen on all chronological pre-2026
validation forecasts. Its pooled confusion counts are in-sample threshold-selection
diagnostics, separate from the earlier-threshold 2025 diagnostic above.

The selected model and B0 have saved fits using all 133 admitted pre-2026 races.
Training lists, input manifests, dependencies and procedure identities accompany
them. The conservative date cutoff is 1 January 2026, before the symbolic 2026 R1
boundary. DELIVERY.json binds exact admission, canonical manifests, six completed
folds, selection, refit and ledger hashes. It maps source-specific assumptions.

Older archives carry RA1–3 plus RA5/6: rewritten historical versions/order and
healthy-window clock availability remain assumptions. Race-day sources retain
RA1–4. Independent checks cannot prove every historical version or independent
tyre-change ground truth. The owner approved that evidence tradeoff. Negative or
missing tyre-service evidence remains indeterminate.

This experiment adds no 2026 source or outcome exposure. Earlier declared final-
partition exposure remains binding and must qualify later final claims.
No canonical EvaluationLock or final claim
is created. Final resolution-run identity and F2 metadata-only fixed-list resolution
remain separate gated work under the existing evaluation protocol. No merge,
deployment, public data release or viewer replacement occurred.

Independent admission/protocol review: ADMISSION_REVIEW.md. Implementation/result
review: REVIEW.md. Reproduction and interrupted-session recovery: README.md and
DATASET.md. The frozen PR #55 and earlier PR #56 diagnostic reports remain distinct.
