# Expanded pre-2026 experiment registration

Version: expanded-pre2026/v1. Owner approved bounded older-source verification
on 14 October 2026. No new 2026 source/outcome exposure. PR #55 and #56 results
are already known, so expanded validation is development, not a fresh confirmation.

## Admission and splits

Verify all 173 calendar sessions from 2018–2025. Keep every acquisition/exclusion
record. Admit only complete six-endpoint raw snapshots with monotone prefixes,
causal roster and scheduled distance, continuous lap counters, usable clock
anchors and no positive service conflict in served drive-through/stop-go tests.
Existing S-RD rules and RA-1–RA-4 apply to the 39 race-day sessions. Older sessions
retain RA-1–RA-3 and replace the race-day fidelity assumption with RA-5
(rewrite retains contemporaneous versions/order) and RA-6 (shared ±5s clock in
validated healthy windows). Omit every older anomalous lap span, including
single-driver residuals above 1s, and every out-of-band RCM UTC anchor ±60s.
Sparse-clock gaps also stay excluded. No independent tyre-change ground truth is
claimed. Negative/absent tyre-service evidence stays indeterminate.

A session-level structural failure excludes that session before model scoring.
Do not fix lap jumps, fabricate roster entries or impute missing streams from CSV.
Source hashes, admission evidence and exact admitted list must pass independent
review and be committed before reconstruction/training.

ROLLING_SEASON: first admitted season (2018) supplies training only. For each
later admitted season, train on every admitted earlier race and validate all
admitted races of that season. The cutoff is its first admitted validation race.
Never randomly split laps/drivers. Omit an empty season explicitly. Training
sources must have concluded strictly before the cutoff. Retain unresolved labels
and attempts. A9/A11 fit as in saved registration; A6 excluded. Unexpected A10
fitting is rejected until a registered interval likelihood is implemented.

## Models and new candidate

B0, B1, PERCENT_AHEAD and PERCENT_PROGRESS retain the exact saved registered
procedures. New TYRE_RIDGE is a declared late addition, the third experimental
candidate within the ten-candidate budget. It uses B1's causal tyre features and
person-period construction, age/100, squared scaled age, represented compound
indicators and remaining race fraction. It minimizes mean logistic loss plus
0.001 * sum(beta[1:] squared)/2, excluding the intercept from the penalty.
Deterministic BFGS, zero start, 2000 iterations, gradient tolerance 1e-8. Accept
precision termination only if max mean penalized gradient <=1e-7; reject nonfinite
coefficients or abs coefficient >1000. No validation-selected penalty.

TYRE_RIDGE final q_open uses B0's empirical final no-event share, including valid
0/1 boundaries before the common 1e-6 PMF floor. This avoids the structurally
unsupported all-one-class final logistic fit. It is a different candidate, never
a repair relabelled B1. Omitted tyre inputs and compounds absent from training
use exact B0 fallback, counted separately. Any true fit failure remains a failure.
No posterior tyre correction enters inference. No calibration correction is fitted.

Python 3.12, NumPy 2.3.5, SciPy 1.17.0. Fixed percentage intervals, probability
floor, open tail, seeds, losses and unknown policies match the saved registration.

## Selection reconciliation

The main objective stays pooled mean log score on identical complete resolvable
chronological validation cohorts of valid runs. B1 remains a reported reference.
If B1 lacks a valid fit/full cohort, it cannot be selected or serve as the full-
cohort reference. In that predeclared failure case, B0 is the selection reference.
Do not stop all model selection solely because an unsupported reference fails.
This is an explicit technical evaluation-protocol amendment, not a target change.

Eligible procedures: B0, both percentage candidates, TYRE_RIDGE, and B1 only if
it covers the same full cohort. All failure/unmatched counts remain visible.
Any shared resolvable forecast gap or mapping/lineage defect prevents selection.
Complexity order: B0, PERCENT_AHEAD, PERCENT_PROGRESS, TYRE_RIDGE, B1. Choose lowest
mean log score, then the lowest complexity within one race-cluster CR2 standard
error of the paired difference from best. Ties use this strict order. B0 may win.
The original B1-vs-B0 primary comparison remains for the original protocol only.
Expanded final comparison uses the selected model and B0; report B1 unavailability
and reference fallback explicitly. No unsupported B1 final forecast is invented.

## Practical metrics and freezing

Retain log score, race-cluster CR2+t, Webb bootstrap seed 5302026, 9999 draws and
leave-one-race-out checks, LOW_POWER and existing prior exposure. Compute every
metric on checkpoint cohorts, grouping uncertainty by race. Deduplicate event_ref
for the separately labelled unique-stop diagnostic. Unknown outcomes never become
negative, including when a model has no forecast.

R0–R2 alert, window/v1, set-valued ambiguity, calibration and width rules are in
research/full-pre2026/REGISTRATION.md. Select each procedure's final alert threshold
on its chronological validation forecasts using max F1 over 0.01..0.99, tie highest.
Freeze those diagnostic thresholds before any final outcome read. Report the
selection-cohort confusion as in-sample. A separate development diagnostic chooses
thresholds on seasons through 2024 and applies them unchanged to 2025, if both
classes exist. These new 2025 diagnostics are exploratory due to prior exposure.

After model selection, freeze ProcedureSpec, selection evidence and thresholds.
Refit selected and B0 once on ALL admitted pre-2026 races with cutoff 2026 R1.
Produce model artifacts, complete hashes, dependency/code identities and a
final-readiness record. Do not claim an EvaluationLock unless all canonical
resolution references, final lists and ledger gates are implemented and verified.
This task does not open 2026 or run final testing. Preserve existing P-F1/P-F2
final lists, metadata-only F2 inclusion, prior-exposure declarations and ledger
protections. Do not silently claim unavailable B1 satisfies an old lock slot.
