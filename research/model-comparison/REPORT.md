# Results: more races and percentage predictions

Issue #53. Development experiment only. No final-test data was opened, and the
Austria viewer and its saved model remain unchanged.

## Answer

Race percentages did not give a clear improvement over counting laps ahead.
Percentage completed was almost tied with B0. Percentage ahead scored worse.
We cannot yet tell whether tyre features help: B1 did not produce a supported
fit in any of the four training blocks. No replacement model is selected.

These findings apply to the two percentage estimators declared in
REGISTRATION.md, not to every possible model using percentages.

## Data and tests

All 39 approved development races were frozen and reconstructed: 2024 R10–R24
and 2025 R1–R24. The dataset has 27 driver codes and 779 driver entries, 44,203 attempted checkpoints,
43,374 eligible target labels and 1,167 distinct qualifying pit events. Many
checkpoints predict the same eventual stop; they are not independent pit stops.

There are 40,851 resolvable labels and 2,523 uncertain labels. The uncertain
labels remain uncertain. Their reasons are:

| Reason | Checkpoints |
| --- | ---: |
| Clock coverage gap | 1,300 |
| Uncertain tyre service | 962 |
| Missing terminal evidence | 165 |
| Terminal boundary overlaps prediction | 61 |
| Pit-entry boundary overlap | 35 |

Another 828 attempts have no canonical observation, and one has uncertain
eligibility. Every attempted checkpoint is retained. São Paulo 2024's restart is
handled without treating a temporary red-flag stop as retirement.

Each model was trained on earlier races and tested on the next six races of 2025.
Training blocks contain 15, 21, 27 and 33 races. Models were never fitted on all
39 races before these tests. Model rules were committed before validation scoring.

## Forecast coverage and scores

The test blocks contain 27,136 attempts. Of those, 26,595 are eligible checkpoints;
540 lack a canonical observation and one has uncertain eligibility.
Lower log score is better. It scores the full distribution, including no further
stop. It is not a percentage of correct predictions.

| Model | Forecasts / eligible checkpoints | Scored forecasts | Mean log score |
| --- | ---: | ---: | ---: |
| B0: laps ahead | 26,595 / 26,595 | 24,674 | 2.426891 |
| Percentage ahead | 26,595 / 26,595 | 24,674 | 2.446789 |
| Percentage completed | 26,595 / 26,595 | 24,674 | 2.426320 |
| B1: tyre features | 2,066 / 26,595 | 1,722 | Not comparable |

The three grid models cover the same 24,674 resolvable test checkpoints across
24 races: 14,407 pit-event outcomes and 10,267 no-event outcomes. Their other
1,921 forecasts have uncertain labels, a 7.22 percent truncation share. These
are not scored as failures or no-event outcomes.

B1 has 24,529 explicit forecast failures. Its 2,066 available forecasts are all
the protocol's B0 fallback for omitted/unusable tyre inputs. The 1,722 scored
fallbacks have exactly the same predictions as B0 on those checkpoints. Their
mean score, 2.690545, must not be compared with B0's full-cohort mean.

B1's first, second and fourth fits fail the registered gradient/convergence
check after numerical precision termination. The third fails because a logistic
fit has only one outcome class. Neither coefficients nor tail rates were guessed.
A separately declared fitting investigation is needed before testing tyre value.
Owner: model-fitting verification/experimentation; no baseline repair is hidden
in this experiment.

## Do the differences matter?

The interval below measures uncertainty across the 24 races. Negative differences
favour the percentage model. Both comparisons use identical complete resolvable
cohorts, with no unmatched checkpoints and no run-validity defects.

| Percentage model minus B0 | Mean difference | 95 percent race-cluster interval |
| --- | ---: | ---: |
| Percentage ahead | +0.019898 | +0.003112 to +0.036684 |
| Percentage completed | -0.000571 | -0.084074 to +0.082931 |

The tiny apparent advantage of percentage completed is well inside the uncertainty
range. Percentage ahead is worse on this comparison. These are development
results with the protocol's LOW_POWER qualifier, conditional on the fitted models.
The co-reported Webb bootstrap and leave-one-race-out checks are in summary.json.
There is no final evaluation, significance test or claim about unseen 2026 races.

The indicative truncation sensitivities also show no reliable percentage advantage:

| Sensitivity, model minus B0 | Percentage ahead | Percentage completed |
| --- | ---: | ---: |
| Inverse-resolvable-share weighting (secondary) | +0.020466 | +0.017703 |
| Below-median-truncation races (retrospective diagnostic) | +0.021376 | -0.056459 |

Weighting assumes missingness within each race and remaining-distance group is
unrelated to the hidden outcome. The known indeterminate-visit mechanism violates
that assumption, so these are indicative checks. B1 remains incomparable.

The registered selection rule cannot select a replacement because B1 does not
cover the complete resolvable cohort. B1 comparisons are secondary intersections,
with all unmatched counts retained. A model cannot win by refusing checkpoints.

## Early forecasts

The broader B0 fit covers all eligible checkpoints in the first quarter of the
test races: 7,080 forecasts. It no longer needs to wait until lap 33 because the
larger training block supplies the missing offset support. The current viewer
still uses the separate Spain-only model; this experiment does not replace it.

| Race phase, by completed fraction | Eligible grid-model forecasts | B0 score | Percentage completed score |
| --- | ---: | ---: | ---: |
| First quarter | 7,080 | 3.745781 | 3.843476 |
| Second quarter | 6,699 | 3.284785 | 3.333737 |
| Third quarter | 6,700 | 2.011454 | 1.933529 |
| Last quarter | 6,116 | 0.429854 | 0.349603 |

Phase boundaries were fixed before testing. These breakdowns describe behaviour;
they do not override the declared overall selection rule.

## Checks and limits

Every fold saves its fitted models, full forecast distributions, individual
accounting/score rows, input identities and hashes. summary.json contains per-race
and phase results, no-event calibration, Brier and ranked probability scores,
entropy, event-only randomized PIT, window coverage, race-cluster intervals and
influence checks. It also contains truncation by race, driver-race, training-fixed
K tercile and phase, indicative inverse-resolvable-share weighting and the
below-median-truncation race analysis. Those sensitivities carry their declared
secondary/retrospective labels. Visit-specific mechanism sensitivity is explicitly
not computable until the target subsystem supplies indeterminate-visit lap contexts.

The archive assumptions RA-1–RA-4 and the approved race-day evidence exception
still apply. This is an assumption-based historical reconstruction, without
independent tyre-change ground truth. Unsupported visits and timing windows are
retained as uncertainty. Results describe resolvable checkpoints, not all possible
pit events or uncertain episodes.

The first implementation run, evaluation-1, is superseded after independent review
found five code defects. Only evaluation-2 is the delivered comparison. The fixes
follow the original declarations and add no candidate or result-driven tuning.

See README.md for commands, REVIEW.md for the independent review, and
DATASET.md for the frozen source and execution identities.
