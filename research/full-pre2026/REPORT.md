# Issue 53 follow-up: data audit and practical results

## Result

The saved forecasts are available early, but they do not yet provide useful
pit alerts. Most alerts are false and the pit windows are broad. The tyre model
has both numerical and structural fitting failures. No replacement is selected.

The requested full pre-2026 training experiment is blocked by older-source
admission. This report adds diagnostics to PR #55, without rerunning its experiment.
No 2026 source or outcome was opened. No merge, deployment or viewer change occurred.

## Data audit

Every legacy CSV was hashed and inspected. The inventory contains 109 files,
including 104 race exports and five season exports. The season exports overlap
race exports. File counts cannot be treated as distinct race counts.

| Season | Race exports | Season exports | Rows in race exports | Missing compound / tyre age |
| --- | ---: | ---: | ---: | ---: |
| 2018 | 19 | 1 | 20,356 | 300 / 300 |
| 2019 | 21 | 1 | 23,646 | 0 / 0 |
| 2020 | 17 | 1 | 16,993 | 0 / 0 |
| 2021 | 22 | 1 | 23,693 | 0 / 0 |
| 2022 | 22 | 1 | 23,513 | 0 / 0 |
| 2023 | 3 | 0 | 2,988 | 0 / 0 |

Per-race exports have no duplicate track/driver/lap keys. Some season files have
repeated keys or different schemas. All five overlap race exports. None enters
training. Only three 2023 race exports exist, so the CSV corpus is not complete.

| Legacy field | Current use |
| --- | --- |
| PitStatus | QA evidence only. A pit entry can be a drive-through or retirement without tyre service. |
| Compound, TyreLife, Stint | Require causal raw updates. Processed final rows cannot establish their publication/correction history. |
| TotalLaps | Reject as an input. The historical extractor derives it from the completed race's maximum observed lap. |
| LapTime, gaps, position, track status | Mixed observation times and later corrections require raw-source reconstruction. |
| LapStartTime and weather | Effective timestamps alone cannot prove when each value became available. |
| Source records, tyre-service proof, terminal boundaries | Missing from the CSVs. No safe current-target adapter can invent them. |

The existing archive metadata census, retrieved 10 October 2026, identifies 173
pre-2026 sessions: 39 admitted race-day sessions, 110 unverified rewritten sessions,
and 24 unsupported sessions. The latter comprise 22 inaccessible 2022 sessions
and Bahrain/Hungary 2018. This follow-up did not re-fetch older archives or claim
to validate their revision history. All six frozen raw endpoints for each of the
39 admitted races passed byte/hash and source-metadata checks.

## Requested split

After admission, use all admitted pre-2026 races. With at least three seasons,
train on earlier seasons and validate on each later season. Freeze the exact
partition before running. Select using the existing log score rule, then refit
once on all admitted pre-2026 races. Freeze the alert threshold and model artifacts
before opening any final outcome. Existing 2026 final partitions, prior-exposure
qualifier, ledger and F2 rules remain binding.

This expanded selection/refit has not run. The older-source gate and failed B1
reference prevent a valid lock under the existing protocol.

## Saved models and scores

These are the unchanged PR #55 results on 24 later 2025 races. Training blocks
contain 15, 21, 27 and 33 earlier races. Each checkpoint predicts a full timing
probability distribution plus no further stop. Lower log score is better.

| Model | Meaning | Forecasts / eligible | Scored | Mean log score |
| --- | --- | ---: | ---: | ---: |
| B0 | Typical stop timing by laps ahead | 26,595 / 26,595 | 24,674 | 2.426891 |
| Percentage ahead | Timing as a fraction of scheduled distance | 26,595 / 26,595 | 24,674 | 2.446789 |
| Percentage completed | Timing by race progress | 26,595 / 26,595 | 24,674 | 2.426320 |
| B1 | Tyre age and compound | 2,066 / 26,595 | 1,722 | Incomparable partial fallback |

Percentage completed's score difference from B0 is -0.000571, with a 95% interval
across races from -0.084074 to +0.082931. It shows no clear improvement. Percentage
ahead is worse by +0.019898, interval +0.003112 to +0.036684. These are the saved
LOW_POWER development comparisons, conditional on fitted models.

The complete grid-model cohort excludes 1,921 unknown outcomes. They remain
unknown, never no-stop negatives. B1's available forecasts are exactly B0 fallback,
so their smaller-cohort performance cannot establish value from tyre features.

## Three-region pit alerts

The alert probability sums R0, R1 and R2. R0 means entry in the current in-lap
after the checkpoint. A short grid includes its open final region, so the horizon
can cover later entry than the everyday phrase 'three laps' suggests.

For this exploratory saved-run diagnostic, thresholds maximize F1 on R1–R18 of
2025. F1 balances precision and recall equally. Ties choose the highest threshold.
Thresholds are then fixed for R19–R24. The earlier results were already known,
so this is no new confirmatory claim and creates no final EvaluationLock.

| Model | Threshold | TP | FP | FN | TN | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 | 0.08 | 490 | 5,701 | 0 | 298 | 7.9% | 100.0% |
| Percentage ahead | 0.07 | 490 | 5,718 | 0 | 281 | 7.9% | 100.0% |
| Percentage completed | 0.06 | 456 | 4,151 | 34 | 1,848 | 9.9% | 93.1% |

TP means an alert followed by a qualifying stop inside the canonical horizon.
FP means an alert with a known outcome outside it. FN means a missed positive
checkpoint. TN means no alert and a known outcome outside it.

The later cohort has 6,489 known outcomes and 315 unknown outcomes. A positive
occurs at only 7.55% of known checkpoints. Always alerting gives 7.55% precision
and 100% recall. Never alerting gives zero recall and undefined precision.
B0's 7.9% precision is barely above always alerting. Percentage completed reduces
false alerts but still has about nine false alerts for each correct alert.
These counts describe checkpoints, not independent pit stops.

There are 168 identified stops with a known in-horizon checkpoint in these six
races. B0 alerts before all 168, with 322 repeated positive alerts. Percentage
completed alerts before 159 of 168 (94.6%), with 297 repeated positive alerts.
These retrospective stop counts deduplicate event identities. They do not count
unknown or unidentifiable events. B1 misses forecasts on 6,277 known checkpoints
and has no detected stops at its selected fallback threshold. It is unusable as
a tyre-feature comparison.

Six races provide limited precision. summary.json reports results per race,
leave-one-race-out precision/recall checks and race-cluster uncertainty for
prevalence, Brier and alert shares. Those share intervals are not precision/recall
confidence intervals. The report does not treat checkpoints as independent samples.

## Windows and calibration

Window results below use all saved 2025 validation races. The window holds at
least 80% of predicted event probability, conditional on a stop eventually occurring.

| Model | Event coverage | Mean predicted conditional mass | Median width in regions | p25–p75 width |
| --- | ---: | ---: | ---: | ---: |
| B0 | 90.9% | 81.3% | 22 | 12–27 |
| Percentage ahead | 92.2% | 81.2% | 21 | 12–28 |
| Percentage completed | 82.3% | 81.2% | 16 | 10–23 |

Coverage comes from 14,407 resolvable event checkpoints. Higher coverage can come
from broad windows. The median B0 window spans 22 regions, limiting timing precision.
About 1.26% of all grid-model windows include the open final region and therefore
have no finite lap-width upper bound. Region count remains finite.

Across all 24,674 scored checkpoints, B0's absolute window mass averages 53.8%
and observed window hits average 53.1%. Percentage completed predicts 43.0% and
observes 48.1%. These full-cohort figures include known no-stop outcomes as zero
hits. Unknown outcomes are excluded with counts retained.

Three-region Brier scores are 0.075905 for B0, 0.076254 for percentage ahead and
0.076878 for percentage completed. Lower is better. Reliability tables are in
summary.json. In percentage completed's highest probability decile, predicted
probability averages 19.9% while the observed rate is 11.8%, indicating
 overconfidence in that group. No calibration correction was fitted.

## Separate tyre-fit investigation

The hazard fit has numerical precision failures in folds 1, 2 and 4. Scaling
its objective to a mean loss makes optimization terminate successfully in all
folds, but three probes still exceed the original summed-gradient tolerance.
This is diagnostic evidence, not a repaired fit or a forecast-producing candidate.

More fundamentally, the final component sees only no-event outcomes in every
fold: 6,431, 9,152, 10,779 and 13,264 training rows. Its design matrix also has
rank 5 for 6 columns. An unpenalized logistic fit has no finite maximum with
one outcome class. The valid probability boundary is 1, but setting it would
change the registered estimator's fitting policy. A separately registered tyre
candidate should specify boundary treatment and numerical convergence checks
before a new comparison. B1 remains unchanged and failed.

## Owner decision required

Recommend extending the evidence exception to older rewritten raw archives only
after a separate, independently reviewed era/session audit. Keep conservative
clock exclusions, verified tyre-service reconstruction and explicit assumptions
about revision fidelity. Keep CSVs as QA only and unavailable sessions excluded.

The downside is that internal checks cannot prove every historical version was
preserved. This is a change to the expressly bounded 10 October decision and
requires owner approval under governance/DECISION_BOUNDARIES.md. Approval would
authorize verification, not automatic admission. See the pending decision record.
