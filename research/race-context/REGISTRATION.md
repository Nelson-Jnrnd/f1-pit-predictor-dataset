# Race-context experiment registration

Status: proposed for independent review before implementation or scoring.
Owner: issue #57, authorized 15 October 2026. Development only. Existing results
are known; this is not fresh confirmation. No 2026 reads or final evaluation.

## Scope and candidate budget

Preserve all #55/#56 artifacts and viewer behavior. Reuse the exact admitted
133-race partition, canonical observations, checkpoints, labels and saved baseline
fits. No raw reacquisition or historical experiment restart. Six rolling-season
folds (2019, 2020, 2021, 2023, 2024, 2025); every earlier admitted race trains each
fold. 2018 trains only; unavailable 2022 remains excluded. All attempts retained.

Three late candidates: RF_GRID, RF_TYRE, RF_CONTEXT. Existing PERCENT_AHEAD,
PERCENT_PROGRESS and TYRE_RIDGE consumed three slots. Total is six of ten,
excluding B0/B1. No alternative family or tuning search. These three separate
model structure (RF_GRID versus timing baselines), tyre information (RF_TYRE
versus RF_GRID), and timing/traffic information (RF_CONTEXT versus RF_TYRE).

## Features and availability verification

Only the selected immutable CanonicalObservation supplies feature values. Read
and hash-verify its parent manifest and observation payload before extraction.
Check its reference against each checkpoint. Keep input fact references and feature
omissions. Do not read labels while extracting features. No historical CSV inputs.

Grid: checkpoint L, scheduled N_T, L/N_T, offset h, h/N_T and (L+h)/N_T.
Tyres: B1's existing causal age/compound view; age+h, compound one-hot with fixed
six-level vocabulary, missing indicator. Missing age is -1; missing compound is
all zero plus missing indicator. No future stint lookup. No B0 fallback for RF.
Context: latest completed LastLapTime, BestLapTime and their difference; current
Position, GapToLeader, IntervalToPositionAhead. Numeric gaps only; lapped strings,
missing/invalid fields and absent rank stay missing (-1 plus separate indicators).
Position must be integer 1..30. Time/gap values must be finite and nonnegative;
last lap 20..600 seconds, best lap 20..600 seconds, gap/interval 0..3600 seconds.
LastLapTime is admitted only when _last_time_completed_lap equals L and L>0.
BestLapTime requires its explicit Lap in 1..L. No unfinished lap time, sector,
speed, eventual pit count, completion or corrected future tyre field is read.

This is a bounded extension for these TimingData leaves, not admission of a new
stream. The field verification must audit every admitted race: values/parsing,
completion-lap guards, parent hashes, fact-reference stream hashes and boundary
order. It must retain missing counts by race and feature and sample actual source
updates in the existing pre-2026 raw snapshots where available. TimingData shares
the already verified prefix clock; RA1/RA5 historical-version assumptions still
apply. Rank/gap correctness has no independent ground truth. Existing broad
positions/telemetry omissions are not general permission: the reviewed extension
whitelists only timing rank/gaps and completed-lap times, never track coordinates.
No RF execution until independent review of this extension and generated audit.

Circuit is evidenced in thesis but absent as an authorized canonical state fact;
omit it rather than feed race IDs. Stint ordinal is omitted because tyre-service
identity is not independently verified. Track status is evidenced in thesis but
not reconstructed in these canonical observations; omit it. Weather was collected
but removed by the visible historical feature pipeline; omit unsupported streams.
Retain wet running, retirements and unusual stop counts whenever existing episode
semantics admit them. No outcome-based cohort filters are introduced.

## Estimation and output

Python 3.12, NumPy 2.3.5, SciPy 1.17.0, scikit-learn 1.8.0, joblib 1.5.3.
RandomForestClassifier: 64 trees, max_depth=12, min_samples_leaf=100,
max_features='sqrt', bootstrap=True, criterion='log_loss', class_weight=None,
random_state=5702026, n_jobs=2. All choices fixed, no validation tuning.

Use existing resolved-checkpoint person-period construction, retaining repeated
checkpoints explicitly. A9 contributes through its event; A11 through all finite
regions; A6 excluded from fitting only, retained in forecast accounting. Unexpected
A10 fitting is a blocker. Positive periods are all retained. If more than 150,000
negative periods exist, select 150,000 uniformly without replacement with seed
5702026 and weight each by total_negative/150000. Otherwise keep all. Positive
weights are 1. No balanced class weights or uncorrected oversampling: probabilities
must retain prevalence. No learned imputation, feature selection or calibration.
Sampling is training-only; all validation checkpoints are forecast.

At each checkpoint, freeze all context at T. Only deterministic h, projected
progress and age+h vary across future regions. This assumes unchanged tyres and
context until the next stop; it never reads later observations. Each forest
estimates the same subdistribution hazard as B1. Canonical hazard/v1 adapter,
B0's training-only q_open, and the existing 1e-6 PMF floor produce the complete
normalized timing distribution with explicit terminal no-event mass. This is a
new timing model, not conversion of an arbitrary short-horizon classifier score.

## Evaluation, selection and freezing

Compare B0, PERCENT_PROGRESS, TYRE_RIDGE and the three RF procedures on identical
resolvable checkpoints. B1 is documented as unsupported, not silently repaired.
Reuse saved baseline fits and regenerate forecasts; verify saved model identities.
Forecast each validation race before its ledger-gated label join. Reject missing
model forecasts, mapping/lineage defects or mismatched scored cohorts for selection.
All omitted features use the causal policy above; no restricted-cohort winner.

Primary objective: pooled mean log score. Strict simplicity order: B0,
PERCENT_PROGRESS, TYRE_RIDGE, RF_GRID, RF_TYRE, RF_CONTEXT. Apply the existing
one race-cluster standard error rule to the paired difference from the raw best.
Use CR2+t, Webb seed 5302026 and 9999 draws, and leave-one-race-out diagnostics.
Report paired ablations even if the simplicity rule selects a baseline.

Use existing practical_metrics rules for R0-R2 outcomes, set-valued ambiguity,
Brier, reliability, window/v1 coverage/mass/width, full availability and unknown
shares by season. Alert threshold maximizes F1 on 0.01..0.99, tie highest. Pooled
threshold-selection confusion is in-sample. Separately choose thresholds through
2024, apply unchanged to 2025, label exploratory due to prior exposure. Report
precision, recall, F1, prevalence, confusion, always/never baselines, false alerts
per driver-race, deduplicated detected stops and repeated checkpoint alerts.
Report the full threshold tradeoff, not accuracy alone.

Freeze selection, thresholds, registration/code/input hashes before refitting the
selected procedure and B0 on all 133 admitted races (cutoff 2026-01-01). Save exact
training lists, forest arrays/metadata and artifact digests. No EvaluationLock,
merge, deployment, public payload release or viewer replacement. Existing 2026
R1-R16 prior exposure declarations and P-F1/P-F2 lock rules remain unchanged.

## Review and recovery

One full independent protocol/source-extension review, then implementation/result
review under governance/REVIEW_POLICY.md. At most one bounded re-review per slice.
Commit registration before scoring. Outputs are resumable only with exact matching
code/registration/input hashes. Changed procedures require a new registration and
output path. Preserve all substantive code and summaries through commits and a PR.
