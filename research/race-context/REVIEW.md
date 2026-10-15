# Independent implementation and result review

Outcome: PASS after one bounded re-review. No Blocking or Major findings remain.
This approves the issue #57 implementation and development results for a reviewable
PR. It does not approve merge, viewer replacement, deployment or final testing.

Reviewer: independent agent `/root/review_implementation`, 15 October 2026.
Reference: issue #57, PR [#58](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/pull/58).
Reviewed implementation head: `24f6149446314f86726edd8309dfb8da23a4451f`.
The author must link the corresponding GitHub review record after publication.

## Full scoped review and bounded rework

The initial code review found two Major provenance defects:

1. The execution-code hash omitted `comparison_models.py`, although it supplies
   training-period construction and the canonical probability adapter.
2. The selection freeze did not bind all input and fold identities, the reused
   full-data baseline lacked integrity/scope checks, and final artifacts lacked
   a completion manifest.

Both are resolved. The current runner hashes the missing dependency. Original
execution bytes and eleven module hashes are preserved. I independently matched
those hashes to the original execution commit. Unchanged numerical helpers and
the exact reviewed upgraded runner are required for explicit original-cache
acceptance. Original fold configs, model IDs and forecasts remain unchanged.

The input freeze binds all 133 parent manifests and feature payloads, audit,
source verification, feature review, registration and the verified old baseline.
All six fold completions were bound before selection existed. The selected-model
freeze binds that evidence and the summary before full-data refit reads. The old
baseline matches its preserved DELIVERY hash, exact 133-race list, cutoff and
artifact identity. The final completion binds 62 payloads; every digest passes.
Completed-run verification preserves the saved outputs.

The first aggregate save failed on a NumPy integer after all folds completed.
Recovery aggregates verified saved JSON; it does not retrain the fold models or
change forecasts. Recovery and original forecast code identities remain separate.
Cached confusion counts retain the original policy. All 99 thresholds match the
original implementation on mixed known, unknown, missing and excluded fixtures.

## Independent numerical checks

Reviewed the registered model, feature, observation, output and evaluation
contracts, admission reviews, implementation, tests, recovery and report.
Training uses earlier admitted seasons only. Resolved event/no-event periods,
training-only negative sampling with inverse inclusion weights, frozen checkpoint
context and the complete probability adapter match registration. No label or
future observation enters inference. Unknown outcomes retain their accounting.

For every fold I checked all saved payload hashes, unique identical attempt
cohorts across six procedures, every distribution's grid, floor and normalization,
primary/practical score equality, and exact reused baseline model identities.
All eighteen saved forest hashes and fixed parameters pass. Reloaded forests
independently reproduce 54 sampled checkpoint distributions from frozen inputs.

Independently reconstructed pooled scores and the paired one-standard-error
selection rule. Each procedure has 130,836 attempts and 93,650 scored checkpoints
across 115 races. There are 29,166 unknown outcomes and no missing model forecasts,
mapping defects or unmatched scored units. RF_CONTEXT is both raw best and the
registered selection: mean log score 2.169202, versus 2.343230 for B0.

Independently reconstructed RF_CONTEXT thresholds: 0.22 pooled, and 0.24 using
validation through 2024. The unchanged 0.24 threshold produces 2025 confusion
counts TP=908, FP=2,293, FN=1,140, TN=20,333. Saved results match exactly.
Precision is 28.4% and recall 44.3%; these are exploratory checkpoint alerts.

The final selected forest's artifact digest, estimator hash, 64 trees, fixed
parameters and cutoff pass. Exactly 133 unique pre-2026 full-refit openings follow
the recorded selection freeze. Its training metadata retains 55,400 positive and
1,239,034 negative periods; 150,000 sampled negatives have weight 8.2602266667.
B0 is the unchanged, verified full-data refit. All ledger openings are pre-2026.

The original 89-test suite passed independently. The final nine targeted tests
also pass independently; the final full-suite record shows 93 passing tests.

## Interpretation and limits

REPORT.md accurately separates probability scores from accuracy, development
from final evaluation, and repeated alerts from distinct stops. Tyre information
improves the matched forest comparison. The smaller pace/traffic increment has a
95% race-cluster interval spanning zero. Frequent false alerts, missed positive
checkpoints, broad windows, missing features and unknown outcomes remain visible.

The separate source-admission review remains authoritative. Bounded raw samples
do not establish independent timing/rank truth or historical-version fidelity;
the admitted archive assumptions still apply. Intervals condition on these fitted
procedures. The report does not claim dependable operational performance.
No protected 2026 source, outcome or capability evidence was read during review.
No new experiment, final evaluation or public release of detailed evidence was
performed by the reviewer.
