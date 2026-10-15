# Independent hypothesis protocol review

Outcome: PASS. No Blocking, Major or Minor protocol findings.
Implementation and scoring may proceed under the registered procedures. This
review does not approve implementation, results, final testing or a follow-up merge.

Reviewer: independent agent `/root/hypothesis_protocol_review`, 15 October 2026.
Reviewed head: `ad21f43bd1a777a1c15610039b507276ed57a97c`.
Registration SHA-256:
`f685d52a133501e193ce0794da0c42417d4ba519144a53f752c42b1ddc0072c8`.
Task reference: [issue #59](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/issues/59).
The parent must link this passing review to the follow-up GitHub PR/review record.

## Review boundary

Read AGENTS.md and its required governance, issue #59 and upstream issue #57,
the new decision and evaluation-protocol delta, the #57 registration/protocol
review/report, expanded-experiment registration, and the canonical observation,
target, output and evaluation contracts. No protected 2026 source, outcome or
capability evidence was opened. No implementation or empirical result was reviewed.

## Findings

The four exact procedures consume the remaining four candidate slots after the
six existing procedures. The ordered H1 through H4 loop is finite. Interpretation
may respond to results; features, parameters, sampling and additional attempts may
not. The reference remains the frozen RF_CONTEXT, so later hypotheses do not
silently inherit earlier changes. Failures stay visible and do not create free
replacement candidates.

H1 uses scheduled distance known at the checkpoint, not eventual distance. It
changes the grid/age representation while retaining missingness and the existing
context freeze. H2 tests depth and leaf-size changes jointly. H3 changes the model
family with fixed parameters and no validation-driven early stopping. H4 changes
the training history, with the two latest admitted seasons strictly before each
validation season and available history in early folds. Its B0 terminal-allocation
estimate is explicitly fitted on that same subset. The final H4 refit likewise
uses its last-two-season scope rather than silently switching to all seasons.

All procedures keep the same person-period target, canonical hazard adapter,
terminal no-event mass and probability floor. Training-only negative sampling
retains inverse-inclusion weights; no class balancing or unregistered calibration
changes prevalence. The source-feature extension is reused without widening it.
The six chronological validation seasons, all eligible forecast attempts, exact
matched scored keys, unknown outcomes and failure accounting remain explicit.

Selection keeps pooled full-distribution log score primary, with a fixed preference
order within one paired race-cluster standard error of the raw best. CR2+t, Webb
bootstrap and leave-one-race-out diagnostics are inherited explicitly. Alert
thresholds use seasons through 2024 before unchanged application in 2025; pooled
threshold diagnostics are identified as in-sample. Probability quality and alert
usefulness remain separate conclusions. Existing exposure makes the entire
comparison exploratory development, including 2025.

The recommendation and thresholds freeze before the final pre-2026 refit. No
EvaluationLock, 2026 opening, viewer promotion or final evaluation is authorized.
Hash-bound caches, forecast persistence before validation-label opening, protected
season rejection before file access and independent result review are declared.
These satisfy the protocol-level requirements; implementation review must verify
that the code actually enforces them.

## Interpretation notes

These are observations, not requested rework. H1 tests the specified representation
change as a whole; a score change should not be attributed to normalization alone.
H2 cannot separate the contributions of depth and leaf size. H4 measures a training
history procedure change, including its matching terminal-allocation fit. The
preference order is a declared selection policy, not proof that later entries are
intrinsically more complex. None of the uncertainty intervals removes uncertainty
from model selection or prior validation exposure.

One bounded protocol re-review remains available only for substantive rework.
Implementation/result review remains a separate required slice.
