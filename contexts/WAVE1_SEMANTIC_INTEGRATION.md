# Wave 1 Semantic Integration Gate

## Status

PASS — no Blocking, Major, or Minor cross-slice incompatibility found across the approved Wave 1 semantic contracts.

## Abstraction level

Wave 1 — bounded semantic integration review.

This artifact records cross-slice composition only. It does not reopen or redefine the internal semantics of the approved provider slices and does not define architecture, schemas, models, metrics, provider reconstruction, or implementation.

## Issue / branch

- Issue: #14 — `Wave 1 — Semantic integration gate`
- Branch: `integrate/w1-semantic-gate`

## Reviewed canonical artifacts

All required upstream Wave 1 artifacts are approved on `main`:

- `contexts/RACE_OBSERVATION_STATE.md` — prediction-point cadence, prediction instant, identities, and point-in-time information boundary;
- `contexts/PIT_EVENT_TARGET.md` — qualifying pit event, event occurrence, target lifecycle, eligibility, terminal no-event/domain censoring, and truncation;
- `contexts/PREDICTION_OUTPUT_REPLAY.md` — complete remaining-target-scope probability output, terminal no-event probability, pit-window summary meaning, and immutable successive replay predictions;
- `contexts/EVALUATION_BACKTESTING.md` — valid replay/backtest meaning, per-prediction-target evaluation unit, leakage guarantees, target-state comparison semantics, and development/final-evaluation separation.

The ownership/dependency baseline is `contexts/CONTEXT_MAP.md`. Durable Product Owner decisions consumed by the integrated contracts include:

- `decisions/2026-09-08-v2-project-direction.md`;
- `decisions/2026-09-08-v2-pit-event-scope.md`;
- `decisions/2026-09-09-v2-prediction-output-semantics.md`.

Legacy thesis material remains evidence only and carries no normative V2 semantic authority.

## Integration result

The four Wave 1 semantic slices compose coherently. No consumer redefines an upstream provider contract, and no approved semantic lock must be reopened.

The integrated chain is:

1. Race Observation / State defines one canonical driver-specific observation at prediction instant `T` and the information legitimately available by `T`.
2. Pit Event / Target attaches one target episode to a target-eligible observation and defines its target as the first qualifying tyre-service pit event for the same driver entry and race session whose pit-lane entry occurs strictly after `T`.
3. Prediction Output / Replay attaches one immutable probability distribution to that same eligible observation and target episode, covering the complete remaining semantic target scope with explicit terminal no-event probability.
4. Evaluation / Backtesting treats that immutable prediction-target pair as one atomic evaluation unit and compares it only with the canonical resolved target state under the approved point-in-time and target rules.

This dependency direction matches `contexts/CONTEXT_MAP.md` and contains no ownership inversion.

## Cross-slice consistency checks

### 1. Ownership and dependency direction — PASS

Canonical ownership remains singular and directional:

- Observation owns prediction timing, as-of state, information availability, and observation identities.
- Target consumes the observation boundary and owns event qualification, event ordering relative to `T`, target eligibility, lifecycle, terminal no-event, and truncation.
- Output consumes observation and target semantics and owns prediction probability/coverage and replay-update meaning.
- Evaluation consumes all three contracts and owns evaluation units, comparison interpretation, backtest validity, and later verification obligations.

No downstream slice silently changes a provider-owned semantic concept.

### 2. Identity composition — PASS

The same identity chain is preserved end to end:

- one race session;
- one driver entry in that session;
- one canonical driver-relative checkpoint;
- one prediction instant / as-of boundary `T`;
- one target-eligible observation when the next-pit question is meaningful;
- one distinct prediction-target episode for that observation;
- zero or one resolved next qualifying pit event for that episode, or terminal no-event, with truncation retained separately.

Evaluation does not substitute race, driver-race, lap, or eventual pit-event identity for the per-observation prediction-target identity. Event identity and target-episode identity remain distinct.

### 3. Time semantics and event ordering — PASS

There is one authoritative prediction-time boundary: the observation's prediction instant `T`, ordered on the race session information timeline.

Information legitimacy is governed by availability time at or before `T`; later-confirmed or retrospectively corrected truth does not enter the observation at `T`.

The target event uses a different but compatible temporal role: eventual retrospective event truth identifies qualifying tyre-service pit visits, while the occurrence of a qualifying event is anchored to pit-lane entry. The next target is the earliest qualifying pit-lane entry demonstrably strictly after `T`.

This separation is coherent: availability time determines what the prediction may know; retrospective event truth and pit-entry occurrence determine what outcome the fixed prediction is later judged against.

### 4. Target and output compatibility — PASS

The target lifecycle has exactly the resolved outcomes required by the approved output semantics:

- observed next qualifying event within the remaining race scope; or
- terminal no-event when the episode reaches its canonical terminal boundary without another qualifying event.

The canonical prediction covers these possibilities with:

- probability over mutually exclusive future race-progression timing regions for the next qualifying event; plus
- explicit terminal no-event probability.

These possibilities are collectively exhaustive for a resolved target episode. There is no hidden finite-horizon residual category and no conflict between target closure and prediction coverage.

A consumer-facing pit window remains only a summary of concentrated timing probability and is not substituted for the complete distribution in evaluation.

### 5. Eligibility, terminal no-event, and truncation — PASS

The three concepts remain distinct across all consumers:

- target-ineligible observation: no ordinary next-pit target episode exists for that observation;
- terminal no-event/domain censoring: the target episode is valid and resolves with known race-bounded truth that no later qualifying event occurred before the canonical terminal boundary;
- truncated/indeterminate follow-up: historical evidence is insufficient to establish either the next qualifying event or a defensible terminal no-event boundary.

Output assigns probability to terminal no-event but not to truncation, because truncation is an evidence/reconstruction failure rather than a race-behavior outcome.

Evaluation may ordinarily score resolved observed-event and terminal no-event cases, must account explicitly for truncation, and may not manufacture ordinary negatives from target-ineligible or indeterminate cases.

### 6. Successive prediction and event/episode semantics — PASS

Every target-eligible observation creates its own immutable prediction and its own target episode.

When no qualifying pit event occurs between `T1` and `T2`, the distinct episodes opened at those observations may retrospectively resolve to the same eventual pit event. They remain separate forecasts from different legitimate information states and are not deduplicated or merged into one episode.

When a qualifying event occurs between `T1` and `T2`, the later episode targets the next distinct qualifying event after `T2`.

Evaluation preserves this distinction while also requiring later aggregation/statistical work not to mistake repeated within-race forecasts for independent races.

### 7. Leakage and replay immutability — PASS

The leakage boundary is consistent end to end:

- observation reconstruction may use only information legitimately available by `T`;
- derivations and prediction-producing transformations may not import future race knowledge;
- later corrections do not rewrite earlier observation or prediction snapshots;
- future tyre-service qualification and final target truth may be used retrospectively to construct/resolve the target only after the prediction is fixed;
- evaluation may use resolved target truth to judge the immutable prediction but may not use that truth to create, select, tune, or retroactively improve the prediction being judged;
- final historical backtest claims additionally require a declared temporal development/training boundary so future evaluation outcomes do not leak through learned artifacts or model-selection choices.

No slice weakens the point-in-time guarantee established by Race Observation / State.

### 8. Evaluation-unit compatibility — PASS

Evaluation's atomic unit of one prediction-target pair is compatible with the upstream semantics because each eligible observation already owns one immutable prediction and one distinct target episode.

Observed-event comparison uses the canonical qualifying event and pit-entry occurrence. Terminal no-event comparison uses the explicit terminal no-event component of the prediction. Truncation is not silently promoted into a fully resolved outcome.

The backtest may later group or aggregate units by race, driver, event, phase, or other declared levels, but those later statistical choices cannot change the semantic unit itself.

## Findings

### Blocking

None.

### Major

None.

### Minor

None.

### Observations / later-phase handoffs

The following are not semantic integration defects and remain deliberately deferred:

1. **Information-time reconstruction:** data/design + verification must establish defensible provider/source ordering and conservative treatment when historical availability or correction history is ambiguous.
2. **Pit-event reconstruction:** data/design + verification must prove that qualifying tyre service and pit-entry occurrence can be reconstructed reliably enough to implement the approved event contract.
3. **Timing-region representation:** model/data design must choose a representation that can map the canonical pit-entry event timing into the approved complete remaining-target-scope distribution without changing its meaning.
4. **Truncation policy:** verification/statistical design must specify exclusion, partial-information, or sensitivity handling without turning indeterminate follow-up into terminal no-event.
5. **Repeated-observation statistics:** verification/statistical design must choose grouping, weighting, dependence-aware uncertainty, and aggregation methods consistent with repeated within-race forecast semantics.
6. **Temporal development protocol:** verification/design must define a concrete chronology/split/retraining policy that preserves the semantic separation between development/model selection and final historical backtest evidence.

These handoffs belong to later architecture/data/model/verification work and do not block semantic integration.

## Unknown routing

| Question | Classification | Owner / next phase | Status |
| --- | --- | --- | --- |
| Is any cross-slice semantic contradiction present? | Current-scope integration decision | Wave 1 integration gate | **Resolved — no contradiction found** |
| How are availability time, corrections, and tie ordering reconstructed from concrete sources? | Later-phase decision | Data/design + verification | Deferred |
| How are tyre-service qualification and pit-entry occurrence reconstructed technically? | Later-phase decision | Data/design + verification | Deferred |
| What exact timing regions / probability parameterization implement the approved output? | Later-phase decision | Model/data design + verification | Deferred |
| What metrics, scoring formulas, aggregation, dependence treatment, and confidence procedures are used? | Later-phase decision | Verification/statistical design | Deferred |
| What temporal split/retraining protocol implements final leakage-safe historical backtesting? | Later-phase decision | Verification/design | Deferred |
| What schemas, packages, interfaces, storage, APIs, and runtime components implement the semantics? | Later-phase decision | Architecture / detailed design | Deferred |

There are no unresolved Product Owner-reserved Current-scope decisions in this gate.

## Acceptance criteria

- [x] All four upstream Wave 1 artifacts are confirmed approved and are reviewed only for cross-slice composition.
- [x] Ownership/dependency direction matches `contexts/CONTEXT_MAP.md`; no consumer silently redefines a provider contract.
- [x] Race/session/driver/checkpoint/prediction-instant identities compose consistently across observation, target, output, and evaluation.
- [x] The canonical next relevant event is consistently the first qualifying tyre-service pit entry strictly after the observation's prediction instant.
- [x] Each eligible observation has its own prediction-target episode; successive episodes may resolve to the same eventual event without being conflated.
- [x] The complete remaining-target-scope prediction distribution plus explicit terminal no-event probability is compatible with observed-event and terminal no-event target outcomes.
- [x] Truncated/indeterminate follow-up is never converted into terminal no-event or a normal prediction category.
- [x] Evaluation uses one prediction-target pair as its atomic unit and preserves repeated-within-race dependence/identity semantics.
- [x] Point-in-time availability and replay immutability are preserved end to end; retrospective target truth is used only for target construction/evaluation.
- [x] Any demonstrated contradiction is classified and routed to its canonical owner; none was found. Later-phase questions are deferred rather than solved here.
- [x] Gate outcome is `PASS`; no Blocking or Major cross-slice incompatibility remains.
- [x] Architecture/detailed design is unblocked without changing approved semantics.

## Gate outcome

**PASS.** Wave 1 semantic integration is coherent at the approved abstraction level.

Architecture and detailed design may now begin, consuming the approved Wave 1 contracts as semantic locks. Later work may refine technical representations and verification mechanisms but may not silently change prediction-point availability, pit-event/target meaning, complete prediction-output semantics, replay immutability, or evaluation guarantees.

No Product Owner decision is required by this gate.