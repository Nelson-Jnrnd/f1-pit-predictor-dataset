# Decision: V2 prediction-output coverage and uncertainty semantics

- **Status:** Approved
- **Date:** 2026-09-09
- **Owner:** Product Owner
- **Affected artifact:** `contexts/PREDICTION_OUTPUT_REPLAY.md`
- **Issue:** #7

## Question

What uncertainty and future-coverage meaning should one V2 pit-window prediction communicate?

## Decision

A V2 prediction represents a **remaining-race probability distribution** for the canonical next relevant pit event.

For one target-eligible observation at prediction instant `T`, the prediction assigns probability across mutually exclusive future race-progression regions in which the first qualifying tyre-service pit event after `T` may occur, together with an explicit **terminal no-event** outcome for the possibility that the target episode reaches its canonical terminal boundary without another qualifying event.

At the semantic level, these event-timing possibilities plus terminal no-event are collectively exhaustive for the target question and their probability mass is normalized across the complete remaining target scope. There is therefore no implicit finite-horizon cutoff and no hidden "after horizon" probability in the canonical V2 output.

The consumer-facing **pit window** is an interpretable summary of where next-pit timing probability is concentrated within this complete distribution. A presented window must not imply that probability outside the highlighted region is zero. The canonical semantic output remains the full remaining-race distribution plus explicit terminal no-event probability.

Exact mathematical formulation, future-region partitioning or binning, continuous versus discrete representation, calibration procedure, model family, loss, schema, serialization, and UI presentation remain later-phase decisions.

## Rationale

This form gives the consumer a complete interpretation of the next-pit prediction without silently discarding low-probability later possibilities or requiring an arbitrary finite forecast horizon. It also matches the approved Pit Event / Target lifecycle: the episode either closes with a first qualifying pit event at some future point in race progression or reaches its terminal boundary without such an event.

Keeping the complete distribution canonical allows a pit-window summary to remain useful while preserving the probability mass outside the highlighted window for evaluation and uncertainty interpretation.

## Consequences / semantic locks

- One prediction concerns the timing of the canonical first qualifying tyre-service pit entry strictly after its prediction instant.
- Prediction coverage is the complete remaining semantic target scope, not a fixed finite number of future laps.
- The timing component represents mutually exclusive future race-progression regions for possible occurrence of that next event.
- Terminal no-event has explicit probability and means no later qualifying event occurs before the target episode's canonical terminal boundary.
- Event-timing probability plus terminal no-event probability is collectively exhaustive and normalized at semantic level.
- There is no canonical residual "after horizon" outcome because the approved coverage has no finite forecast horizon.
- A pit window is a consumer-facing summary of concentrated timing probability, not a replacement for the complete distribution and not an assertion that outside-window timings are impossible.
- Truncated/indeterminate historical follow-up is not a predicted race-behavior outcome and therefore receives no prediction probability category; Evaluation / Backtesting must handle such cases under its own contract.
- Successive predictions are separate probability distributions tied to their own immutable canonical observations and remaining target scopes.
- The output remains predictive of likely team/driver behavior and does not recommend or optimize strategy.
- Exact probability parameterization, bin boundaries, continuous/discrete formulation, calibration, model choice, metrics, schemas, APIs, UI, and implementation are not fixed by this decision.
- A material change to full-remaining-race coverage, explicit terminal no-event probability, or the probability-distribution interpretation requires a new Product Owner decision and reconciliation of affected downstream artifacts.

## Alternatives considered

- A finite-horizon probability distribution with explicit residual mass for pit timing after that horizon and terminal no-event.
- A central pit-window interval with an associated confidence statement rather than a complete remaining-race distribution.

## Follow-up

- Update `contexts/PREDICTION_OUTPUT_REPLAY.md` to consume this decision and complete the Issue #7 semantic contract.
- Submit the completed slice for the required independent scoped review.
- Evaluation / Backtesting must consume this output contract without redefining its prediction meaning.
