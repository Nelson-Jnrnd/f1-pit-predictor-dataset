# Four exploratory training hypotheses

Status: proposed for independent protocol review before implementation/scoring.
Owner: follow-up to #57, authorized 15 October 2026. Development evidence only.

## Ordered loop and stopping rule

Run H1, inspect its result, run H2, inspect, then H3 and H4. The first iteration
starts from the selected RF_CONTEXT in #58. Each subsequent iteration tests one
specified explanation for its weaknesses against that same frozen reference.
Interpretation may adapt after each result. Features, parameters and procedures
below may not adapt. This is a finite four-test loop, not an unlimited search.
No additional candidate, tuning retry or hidden failed fit. Six previous slots
plus these four exhaust the ten-candidate budget. No new EvaluationLock.

| ID | Hypothesis | Exact difference from RF_CONTEXT |
| --- | --- | --- |
| H1_PERCENT | Raw lap counts hinder transfer across race distances | Replace the six grid features with L/N, h/N, (L+h)/N and 1/N. Replace projected tyre age with (age+h)/N. Preserve tyre missing flag, compounds and all context features. Same forest parameters and training races. |
| H2_DETAIL | The forest smooths away useful interactions | RF_CONTEXT inputs and training. Forest max_depth=20, min_samples_leaf=30. All other parameters unchanged. |
| H3_BOOST | Sequentially fitted trees capture patterns better than a forest | Same RF_CONTEXT inputs, training and sampling. HistGradientBoostingClassifier(loss=log_loss, learning_rate=0.08, max_iter=150, max_leaf_nodes=15, max_depth=None, min_samples_leaf=100, l2_regularization=10, max_bins=255, early_stopping=False, class_weight=None, random_state=5702026). No validation stopping. |
| H4_RECENT | Older seasons dilute current behaviour | RF_CONTEXT inputs and parameters, train on the two most recent admitted seasons strictly before each validation season. Early folds use available seasons. B0 q_open and metadata recomputed on that exact subset with the unchanged B0 estimator. |

RF parameters unless changed: 64 trees, max_depth=12, min_samples_leaf=100,
max_features=sqrt, bootstrap=True, criterion=log_loss, class_weight=None,
random_state=5702026, n_jobs=2. NumPy 2.3.5, SciPy 1.17.0, sklearn 1.8.0,
joblib 1.5.3, Python 3.12. Training-period sampling is exactly #57: all positive
periods, at most 150000 uniform sampled negatives, inverse-inclusion weights,
seed 5702026. Missing sentinels and causal context freeze remain unchanged.
H4 refits B0 only, avoiding fits of unregistered alternative procedures.

## Inputs and chronological evaluation

Reuse byte-verified #57 feature projections, checked canonical checkpoints and
outcomes for all 133 admitted pre-2026 races. No new feature stream, raw source
read or unsupported circuit/weather/status facts. Inherit RA1..RA6, missingness
and target censoring. Never turn unknown outcomes into no-stop outcomes.
Same six validation seasons: 2019, 2020, 2021, 2023, 2024, 2025 (115 races).
All earlier admitted races train H1-H3; H4's declared two-season subset is reported.
No random split. Every candidate forecasts every eligible checkpoint. Compare
all scored keys exactly against frozen RF_CONTEXT for each fold. Retain every
attempt, exclusion, unknown outcome and fit/forecast failure. Any cohort mismatch,
lineage defect or missing eligible forecast invalidates that candidate's selection.

Use unchanged person-period target and hazard/v1 canonical adapter. B0's fitted
training-only q_open supplies terminal allocation. Preserve the full probability
distribution, no-stop mass and 1e-6 floor. No standalone binary conversion.
Freeze features at T. Only registered progress and projected age vary with h.
H1's inverse scheduled distance is known at T, never finalized race distance.
Persist each race's predictions before its ledger-gated validation-label opening.
Loaded training scopes must end before validation; protected seasons are rejected
before any outcome file is opened. Code/registration/input/model/forecast hashes
bind every cached fold. Resume validates hashes and exact configuration.

## Scores and interpretation

Primary: pooled mean full-distribution log score, lower is better. Report paired
race-cluster CR2+t, Webb 9999 draws/seed 5302026 and leave-one-race-out uncertainty
against RF_CONTEXT and per-season scores. Exact matched score cohort required.
All known validation results and this entire adaptive narrative are development,
including 2025. No claim of fresh confirmation or operational usefulness.

Secondary: short-horizon Brier and reliability, window coverage/width/mass,
precision-recall table across 0.01..0.99 and confusion counts. Select each alert
threshold by maximum F1 through 2024, ties highest, then apply unchanged in 2025.
Report false alerts per eligible driver-race, repeated alerts, distinct-stop
detection, prevalence, always/never alerts, unknown shares and exclusions.
Also save pooled pre-2026 threshold diagnostics explicitly as in-sample.

Recommendation is descriptive only: report raw lowest log score, then prefer
RF_CONTEXT/H1/H2/H3/H4 in that order within one paired race-cluster standard error
of the raw best. Missing/failed candidates remain failures, never silently dropped.
No assertion that a lower score guarantees more useful alerts. Freeze the
recommendation and thresholds before refitting the recommended procedure on its
declared all-pre2026 training scope (H4 uses last two admitted seasons, others
all 133). Preserve #57 reference and any non-improving recommendation explicitly.
No promotion, viewer change or final evaluation.

## Verification and delivery

Before scoring: independent protocol review. Tests cover causal design, scheduled
distance transforms, training subset cutoffs, class weighting, target/floor/output,
hash tampering and immutable completed-run resume. Independent result review
checks matched cohorts, saved forecast reproduction and score/confusion identities.
One full review and at most one bounded re-review per slice.

Save code, aggregate report and review records in Git and a follow-up PR. Save
detailed input identities, fitted models, predictions, labels ledger and completion
hashes privately with a retrieval receipt. Final presentation explains each
hypothesis, score, practical alert quality and limitations in plain language.
