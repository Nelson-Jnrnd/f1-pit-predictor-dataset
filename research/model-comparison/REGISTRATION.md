# Model comparison declared before testing

Issue #53. Development only; no viewer replacement, final evaluation, merge or release.

## Shared rules

Use the four P-F1 folds in TASK.md. Fit only races concluding before the first
validation race. Use every eligible checkpoint with a resolvable label for fitting;
exclude indeterminate labels, retaining their records and reasons. Successive
checkpoints count as separate forecast units, not independent stops. No random
split. Keep the open final region and no-event outcome. Apply the protocol's
1e-6 PMF mixture floor after conversion. Missing grid means forecast failure.
No smoothing, regularization, validation-derived bins or fitted preprocessing.
Deterministic fitting; inference has no randomness. Bootstrap seed 5302026;
PIT seed 5302027. Python 3.12, NumPy 2.3.5, SciPy 1.17.0.

## Procedures

- B0: exact protocol pooled discrete hazards, offsets 0..39 and pooled >=40.
  Zero training risk means failure for an affected forecast. Pool final-region
  no-event share among survivors. No guessed tail or repaired baseline.
- B1: exact protocol logistic hazard using age/100, age squared/10000,
  compound indicators and remaining race fraction. Rescaling age changes no
  model family. Reference compound is the first represented compound in the
  fixed order SOFT, MEDIUM, HARD, INTERMEDIATE, WET, OTHER. Drop unrepresented
  indicator columns during fitting; prediction on an unrepresented compound
  fails. Fit final q_open with intercept, remaining race fraction and compound.
  Age is the latest admissible TimingAppData stint TotalLaps (including prior
  use represented by the source), without future correction or extrapolation.
  Omitted age/compound, TyresNotChanged=1, or no admissible stint update after
  the last causal pit entry uses B0. Unknown nonempty compounds map to OTHER.
  Fit by unpenalized maximum likelihood; unavailable/nonconverged/separated
  fits fail explicitly, not via invented coefficients.
- PERCENT_AHEAD: piecewise exponential rate on x=h/N_T.
- PERCENT_PROGRESS: same estimator on x=(L+h)/N_T.

Both percentage procedures use ten fixed equal-width intervals on [0,1].
Their boundaries are mathematical configuration, not estimated from test races.
Fit ten nonnegative rates by Bernoulli person-period maximum likelihood with
per-lap hazard 1-exp(-sum(rate_b * overlap_width_b)). This integrates each lap's
actual percentage width, including laps crossing a boundary. Final q_open is
B0's pooled empirical final share. Final mass remains open-ended rather than
being truncated at 100 percent. A bin with no training exposure is unsupported;
a forecast requiring it fails. A supported bin with zero events may fit zero.
These are the only two experimental candidates, within the budget of ten.

## Numerical rules and comparison

Logistic fitting uses deterministic BFGS, zero start, analytical gradient,
maximum 2000 iterations, gradient tolerance 1e-7 (accept numerical precision
termination only if infinity norm <=1e-5). Coefficients exceeding 1000 in absolute
value or nonfinite coefficients are unsupported. Percentage fitting uses
L-BFGS-B, rate start 1, bounds [0,infinity), max 2000, ftol 1e-12, gtol 1e-7.
No optimizer retry that changes the declared objective.

Complexity order: B0, PERCENT_AHEAD, PERCENT_PROGRESS, B1. Percentage ties use
registration order; B1 has both hazard and final logistic coefficients. Use the
protocol's lowest mean log score and one-standard-error rule. A winner requires
full identical resolvable cohorts and valid runs. Otherwise show secondary
common-intersection comparisons, all unmatched counts, and no selected winner.
B1 fallback coverage is reported separately. Do not reward missing forecasts.

Report per-race and fixed quarter-of-race phase (L/N_T) accuracy and coverage;
phase boundaries are 0,.25,.5,.75,1, fixed before testing. Report calibration
(equal-count deciles), Brier, ranked probability score, entropy, window coverage,
CR2+t intervals, 9999 Webb wild bootstrap, and leave-one-race-out influence.
Intervals describe uncertainty across races conditional on frozen models; LOW_POWER
and archive assumptions remain explicit. Fewer than ten races means descriptive
intervals only. Uncertain labels are never treated as no-event.
