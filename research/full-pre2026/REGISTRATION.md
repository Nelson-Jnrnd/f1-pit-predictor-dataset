# Expanded experiment and practical diagnostics

Version: full-pre2026/v1. Declared after PR #55 results were known.
No new 2026 exposure. Existing final ledger and exposure declaration remain binding.

## Expanded experiment, pending admission

All available races before 2026 are candidates for audit. Only races passing the
observation and target support gates enter the fixed development manifest.
Missing races and exclusions remain in the audit, without invented observations.
Do not reduce the requested scope silently to the 39 already supported races.

When at least three seasons pass admission, use ROLLING_SEASON: fit on all
admitted earlier seasons and validate each later admitted season. The first
admitted season supplies the minimum training block. Two supported seasons use
the existing four 2025 six-race blocks with 2024 R10–R24 minimum training.
All preprocessing and fitted features use training races only. Freeze the exact
race list, source hashes, support evidence and protocol digest before scoring.

Retain B0, B1, PERCENT_AHEAD and PERCENT_PROGRESS as declared in the saved
registration. Any repaired tyre procedure is a separately registered candidate,
never a silent B1 repair. Investigate fitting separately before declaring it.
Retain log score and the existing full-cohort, one-standard-error selection rule.
An unavailable B1 fit blocks the existing selection rule. Do not choose B0 by eye.
After a valid choice, refit selected and reference procedures on all admitted
pre-2026 races with cutoff 2026 R1. Then freeze models, alert thresholds, seeds,
source/resolution identities, exposure declaration and both final protocol locks.
Final partitions and F2 inclusion/exposure rules remain unchanged.

## Alert diagnostics

The event is entry in R0, R1 or R2, using sum(p[:3]). R0 means entry in the
current in-lap after the checkpoint. A shorter grid uses its available regions,
including its open final region. Report shorter-grid counts explicitly. This
horizon can include later entry in the open region and is not always literally
three laps of clock time.

Unknown/truncated outcomes stay unclassified. A bounded set wholly inside the
horizon is positive, wholly outside negative, and crossing it is ambiguous.
Report crossing sets separately. Use p >= threshold for alerts.

Threshold rule: maximize checkpoint F1 over the fixed grid 0.01..0.99 in steps
of 0.01. Ties within 1e-12 choose the highest threshold to reduce false alerts.
Precision/recall/F1 are undefined when their denominator is zero. Require both
classes and at least one forecast in selection data. This tradeoff weighs
precision and recall equally and imposes no minimum precision guarantee.

For an expanded experiment, select the final alert threshold from all chronological
pre-2026 validation predictions of the selected procedure. Freeze it before final
opening. For honest development threshold diagnostics, select from earlier
validation blocks and report later blocks separately.

## Saved-run diagnostic only

Reuse the four frozen PR #55 folds. Choose each model's diagnostic threshold on
2025 R1–R18, then apply it unchanged to R19–R24. These are exploratory additions
to an already inspected development experiment, not a new confirmatory result or
a final EvaluationLock. Keep in-sample selection metrics separate from holdout
metrics. B1 partial fallback results cannot establish tyre-feature performance.

Report checkpoint confusion counts, precision/recall, prevalence, always-alert
and never-alert baselines, p3 Brier and reliability tables. Keep existing full-
distribution log score and race-cluster uncertainty alongside them. Compute
uncertainty by race, never treating checkpoints as independent observations.

A unique-stop diagnostic counts each qualifying event_ref once among known stops
with a resolvable in-horizon checkpoint. A stop is detected if at least one such
checkpoint has an alert. Keep missing-forecast checkpoints in that denominator.
This is a retrospective diagnostic on identifiable stops, not all race stops.
Report repeated alerts and stops lacking any resolvable in-horizon checkpoint.

Use unchanged pit-window/v1 with 0.8 conditional event mass. Report conditional
coverage versus actual mean conditional mass, absolute calibration over the scored
cohort, region-count width quantiles, and open-ended-window share. An open-ended
window has no finite lap-width upper bound. Bounded outcomes straddling the window
have unknown hit status and are excluded from binary coverage with counts retained.
No unknown outcome becomes a negative. No result changes the frozen models.
