# Prediction Output / Historical Replay Semantics

## Status

In review — the Product Owner approved the remaining-race probability-distribution semantics on 2026-09-09 and the decision is persisted in `decisions/2026-09-09-v2-prediction-output-semantics.md`. The semantic slice is complete at its declared abstraction level and awaits the required independent scoped review on PR #12.

## Abstraction level

Wave 1 — semantic specification.

## Outcome

Define what one V2 next-pit prediction means to a consumer and how successive point-in-time predictions coexist during historical replay, while preserving the approved observation and pit-event contracts and avoiding premature statistical or technical design.

## Scope

### In scope

- consumer-facing meaning of a next-pit / pit-window prediction;
- relationship between one prediction and the canonical next relevant pit event;
- semantic coverage/horizon and uncertainty meaning at product level;
- successive prediction/update semantics during historical replay;
- immutable historical interpretation of earlier predictions;
- the output contract consumed by Evaluation / Backtesting.

### Explicitly out of scope

- prediction-point timing, information availability, occurrence-time/availability-time rules, and observation reconstruction;
- pit-event qualification, occurrence anchor, target eligibility, target lifecycle, terminal no-event/domain censoring, and truncation meaning;
- exact probability parameterization, statistical formulation, binning, calibration algorithm, loss, model family, or feature set;
- evaluation metrics, scoring rules, split design, sampling, aggregation, or model selection;
- schemas, serialization, APIs, persistence, packages, architecture, chart design, UI technology, live inference infrastructure, or implementation;
- strategy recommendation, optimization, counterfactual action advice, or next-compound prediction.

## Upstream inputs / semantic locks

- `decisions/2026-09-08-v2-project-direction.md` — V2 estimates when a driver's next pit stop is likely to occur, predicts likely team/driver behavior rather than recommending strategy, and is historical-replay/backtesting first.
- `decisions/2026-09-09-v2-prediction-output-semantics.md` — the canonical output is a probability distribution across the complete remaining target scope, with explicit terminal no-event probability; a pit window is a summary of concentrated timing probability rather than the complete semantic output.
- `product/PROJECT_VISION.md` — the output should communicate likely pit timing over more than a single binary instant and support replay/evaluation.
- `product/RESEARCH_PROBLEM.md` — the primary problem is next-pit timing expressed conceptually as a pit window / likelihood over future race progression; exact output semantics, horizon, and uncertainty representation are owned here.
- `product/SYSTEM_SCOPE.md` — live inference and recommendation/optimization are outside the initial core.
- `contexts/CONTEXT_MAP.md` — this slice owns prediction-output meaning and replay/update semantics and provides the canonical output contract to Evaluation / Backtesting.
- `contexts/RACE_OBSERVATION_STATE.md` — every prediction attaches to one canonical driver-specific observation and prediction instant `T`; information legitimacy is fixed by that observation, and later knowledge never retroactively changes it.
- `contexts/PIT_EVENT_TARGET.md` — the target is the first qualifying tyre-service pit event for the same driver entry and race session whose pit-lane-entry occurrence is strictly after `T`; terminal no-event/domain censoring and truncation/indeterminate follow-up retain their canonical target meanings.
- `decisions/2026-09-08-v2-pit-event-scope.md` — qualifying events require tyre service and occur semantically at pit-lane entry.
- `legacy/THESIS_EVIDENCE.md`, when useful — historical baseline evidence only; legacy next-lap binary behavior is not V2 semantic authority.

## Canonical ownership

This slice owns:

- what a V2 prediction communicates about likely future next-pit timing;
- how probability/uncertainty relates to future race progression and the canonical next relevant pit event;
- complete remaining-target-scope coverage and explicit terminal no-event probability;
- the relationship between the complete probability distribution and a consumer-facing pit-window summary;
- how successive predictions are interpreted, supersede one another as current forecasts, and remain historically immutable;
- the prediction-output contract consumed by Evaluation / Backtesting.

This slice does not own:

- observation timing or legitimate-information rules;
- pit-event identity, target eligibility, terminal boundaries, censoring, or truncation;
- evaluation metrics or scoring;
- mathematical/statistical parameterization or technical representation;
- model, feature, schema, API, UI, architecture, persistence, or implementation choices.

## Semantics / findings

### 1. One prediction is attached to one canonical observation

A V2 prediction is issued for one target-eligible canonical race observation for one race session and driver entry at prediction instant `T`, as defined by `contexts/RACE_OBSERVATION_STATE.md` and `contexts/PIT_EVENT_TARGET.md`.

The observation at `T` is the complete semantic information boundary for that prediction. The prediction must not be reinterpreted as if it had access to facts that became available after `T`.

This contract does not create additional prediction points and does not redefine target eligibility. An observation may exist without being eligible for this next-pit target; any UI or technical handling of such a state is later work.

### 2. The predicted quantity is the canonical next relevant pit event

For an eligible observation at `T`, the prediction concerns the timing of the **first qualifying tyre-service pit event whose pit-lane entry is strictly after `T`** for the same driver entry and race session.

The prediction therefore concerns future behavior relative to the current observation. It does not predict a pit visit whose pit entry has already occurred by `T`, even if service is still underway or tyre-service qualification is only established retrospectively later.

If a qualifying pit event occurs between two prediction instants, the later prediction no longer concerns the event forecast by the earlier prediction. It concerns the next distinct qualifying event after the later instant, subject to the target-eligibility and terminal rules owned by `contexts/PIT_EVENT_TARGET.md`.

### 3. Predictive, not prescriptive

The output communicates what the team/driver is estimated to be likely to do next and when, under the observed race state.

It must not be described as:

- the optimal lap to pit;
- a recommended strategy action;
- an instruction to pit;
- an estimate of the best race-time or finishing-position decision; or
- a counterfactual claim about what should happen under alternative actions.

A high probability assigned to a future pit timing means only that the behavior is judged more plausible under this prediction contract. It does not imply strategic desirability.

### 4. Historical prediction snapshots are immutable

A prediction issued at `T1` is a historical forecast snapshot tied permanently to the observation and information boundary at `T1`.

When replay advances to a later eligible prediction instant `T2`, the new prediction is a separate forecast produced from the later legitimate information state. It may replace the `T1` forecast as the consumer's **current** view at `T2`, but it does not alter, overwrite, backfill, or retroactively improve the forecast that existed at `T1`.

Later corrections, event qualification, final race truth, or later model outputs may affect retrospective target reconstruction or evaluation under their owning policies, but they must not change what prediction was associated with the historical observation at `T1`.

### 5. Successive predictions may or may not concern the same eventual event

Two successive predictions can be interpreted as updates about the same open target episode only when no qualifying pit event has occurred between their prediction instants and the later observation remains target-eligible.

If a qualifying event occurs between them, the earlier target episode has closed. The later prediction begins from the later observation and refers to the next qualifying event after that later instant, if the target remains meaningful.

Replay or evaluation must therefore not assume that every adjacent prediction for a driver forecasts one fixed pit event across the whole race.

### 6. Updating means new information, not historical revision

A change between successive predictions is semantically an update caused by moving to a later canonical observation with a later information boundary. The change may reflect newly legitimate race information and the reduced or otherwise changed future race progression still available.

Each successive prediction is a complete new probability distribution for its own observation and remaining target scope. Probability mass from the prior prediction is not mechanically carried forward, renormalized, or edited by this semantic contract; exact model update mechanics are later design concerns.

The contract does not require predictions to change monotonically, smoothly, or by any particular amount. Stability, calibration, responsiveness, and scoring are evaluation/model questions, not semantic requirements here.

### 7. Canonical uncertainty form — remaining-race probability distribution

Per `decisions/2026-09-09-v2-prediction-output-semantics.md`, one V2 prediction expresses a **probability distribution over the complete remaining semantic target scope**.

For an eligible observation at `T`, the event-timing part of the distribution assigns probability to mutually exclusive future race-progression regions in which the canonical next relevant pit event may occur. These regions collectively represent possible timing locations for the first qualifying pit entry strictly after `T` while the target episode remains open.

The exact region boundaries, number of regions, granularity, and whether the eventual statistical representation is discrete, continuous, or otherwise parameterized are not defined here. Whatever later representation is chosen must preserve the consumer-level meaning established by this slice.

### 8. Complete coverage and explicit terminal no-event probability

Prediction coverage is not a fixed finite number of future laps. It extends across the complete remaining target scope defined by `contexts/PIT_EVENT_TARGET.md`: from prediction instant `T` until the target episode closes either by the next qualifying event or by the canonical terminal boundary for that driver entry/race scope.

The output therefore includes two collectively exhaustive kinds of possibility:

1. the first qualifying pit event occurs in one of the represented future race-progression timing regions; or
2. no later qualifying event occurs before the target episode reaches its canonical terminal boundary.

The second possibility has explicit **terminal no-event probability**. At semantic level, the event-timing probability mass plus terminal no-event probability is normalized across the complete target question.

Because coverage is the complete remaining target scope, the canonical V2 prediction has no hidden finite-horizon cutoff and no residual "pit after the horizon" category. A later presentation may choose to display only part of the timing distribution for usability, but it may not silently discard omitted probability mass or imply that unshown timings are impossible.

This section does not redefine terminal no-event/domain censoring. Its underlying target meaning remains owned by `contexts/PIT_EVENT_TARGET.md`; this slice only specifies that the possibility receives explicit prediction probability.

### 9. Meaning of the pit window

The **pit window** is the consumer-facing summary of where the prediction's next-pit timing probability is concentrated within the complete remaining-race distribution.

It is not a separate target, a hard allowed interval, or a claim that a pit outside the highlighted window has zero probability. A pit window may summarize the most relevant portion of the distribution, but the canonical output contract remains the complete timing distribution plus terminal no-event probability.

The exact rule used to derive or display a window — for example a probability threshold, central interval, top-ranked regions, width constraint, or visualization choice — is not fixed at this semantic level. Later design may choose a presentation rule only if it faithfully represents the approved complete-distribution semantics.

### 10. Truncation is not a prediction outcome

`contexts/PIT_EVENT_TARGET.md` distinguishes a known terminal no-event outcome from truncated/indeterminate historical follow-up caused by insufficient evidence.

The prediction models race behavior, not whether the historical dataset will later contain adequate evidence. Therefore truncation/indeterminate follow-up does **not** receive a probability category in the canonical output.

If retrospective follow-up is truncated, Evaluation / Backtesting must decide whether and how that prediction can be scored without converting the evidence failure into terminal no-event truth.

### 11. Output identity without a technical schema

At semantic level, a persisted or replayed prediction must be unambiguously attributable to:

- the race session;
- the driver entry;
- the canonical prediction checkpoint and prediction instant `T`; and
- the prediction semantics/version under which it was issued, when needed to prevent materially different approved semantics from being conflated.

Exact field names, IDs, storage types, serialization, versioning mechanism, or API shape are later design decisions.

### 12. Contract to Evaluation / Backtesting

Evaluation / Backtesting must consume the following canonical prediction-output contract:

- one prediction is attached to one target-eligible canonical observation and prediction instant;
- the prediction concerns the canonical first qualifying tyre-service pit entry strictly after that instant;
- output meaning is predictive behavior estimation, not recommendation/optimization;
- the canonical uncertainty form is a probability distribution over the complete remaining semantic target scope;
- mutually exclusive future race-progression regions carry the event-timing probability for when that next qualifying event may occur;
- explicit terminal no-event probability represents the possibility that no qualifying event occurs before the target episode's canonical terminal boundary;
- event-timing mass plus terminal no-event probability is collectively exhaustive and normalized at semantic level;
- there is no hidden finite-horizon residual category in the canonical output;
- a pit-window display is a summary of concentrated timing probability and must not redefine or discard the complete distribution;
- truncated/indeterminate historical follow-up is not a predicted outcome category;
- each historical prediction snapshot is immutable and later predictions are separate later-state forecasts;
- adjacent predictions concern the same target episode only while no qualifying event has occurred between them;
- later target truth may be used to judge an earlier prediction but may not be treated as prediction-time information.

Evaluation / Backtesting may define metrics, scoring rules, weighting, sampling, grouping, aggregation, and comparison procedures. It may not redefine the target, observation boundary, probability meaning, coverage, terminal no-event interpretation, pit-window meaning, or replay immutability established here.

## Unknown routing

| Question | Classification | Owner / next artifact | Status |
| --- | --- | --- | --- |
| What consumer-facing likelihood/uncertainty form and coverage/horizon should a V2 pit-window prediction use, including terminal no-event treatment? | Current-scope decision — Product Owner reserved | Product Owner / `decisions/2026-09-09-v2-prediction-output-semantics.md` | **Satisfied — remaining-race probability distribution + explicit terminal no-event approved** |
| How should approved output semantics be scored against observed-event, terminal no-event, and truncated target outcomes? | Cross-slice dependency | Evaluation / Backtesting | Unresolved here by design |
| What metrics, split policy, sampling/weighting, aggregation, and model-selection criteria should be used? | Cross-slice dependency | Evaluation / Backtesting | Unresolved here by design |
| What exact mathematical formulation realizes the approved output semantics? | Later-phase decision | Model/design + verification | Deferred |
| What exact future-region partitioning, probability parameterization, binning, calibration procedure, loss, or uncertainty estimation method is used? | Later-phase decision | Model/design + experimentation | Deferred |
| What exact rule derives a displayed pit window from the canonical distribution? | Later-phase decision | Product/design + verification | Deferred; must faithfully summarize the approved distribution without implying zero probability outside the window |
| What schema, serialization, IDs, versioning mechanism, API, persistence, chart, or UI implements the output? | Later-phase decision | Architecture / implementation | Deferred |
| How should a future live product consume or refresh these predictions intra-lap? | Later-phase decision | Future product/semantic extension | Deferred; must not silently change the V2 core checkpoint semantics |

There are no unresolved Current-scope decisions in this slice.

## Acceptance criteria

- [x] A consumer can explain what one V2 prediction means without reference to a specific model family or file format.
- [x] The output is clearly predictive of likely team/driver behavior and cannot be mistaken for strategy recommendation/optimization.
- [x] The relationship between future race-progression likelihood and the canonical next-pit event is explicit.
- [x] Horizon/coverage semantics are explicit enough that omitted future possibilities are not silently misinterpreted.
- [x] Successive replay predictions have coherent historical/update semantics and later predictions do not retroactively alter earlier outputs.
- [x] Uncertainty/likelihood meaning is explicit at the approved abstraction level without freezing a statistical implementation.
- [x] Evaluation / Backtesting receives one complete canonical prediction-output contract.
- [x] Observation timing, event/censoring meaning, metrics, models, features, schemas, architecture, UI technology, and implementation remain outside scope.
- [x] Every unresolved question is classified as Current-scope, Cross-slice, or Later-phase.
- [x] The human-reserved prediction-semantics choice was escalated under `governance/USER_INTERACTION.md`, approved by the Product Owner, and persisted in `decisions/2026-09-09-v2-prediction-output-semantics.md` before being made normative here.
- [ ] Required independent review is completed before approval.

## Review record

- Full scoped review: pending on PR #12 against the completed semantic artifact.
- Rework: pending review outcome.
- Bounded re-review: pending only if substantive rework is required after the full review.
- Approval evidence: pending a passing independent review or bounded re-review as required by `governance/REVIEW_POLICY.md`.
