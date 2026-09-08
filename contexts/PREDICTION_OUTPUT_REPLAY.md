# Prediction Output / Historical Replay Semantics

## Status

Blocked — non-reserved replay and target-alignment semantics are established below, but the Product Owner must approve the material consumer-facing likelihood/coverage semantics before this slice can be completed.

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
- how any approved likelihood/uncertainty statement relates to future race progression and the canonical next relevant pit event;
- the semantic meaning of declared output coverage/horizon and any residual/outside-coverage possibility;
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

A high likelihood assigned to a future pit timing means only that the behavior is judged more plausible under the prediction semantics eventually approved for this slice. It does not imply strategic desirability.

### 4. Historical prediction snapshots are immutable

A prediction issued at `T1` is a historical forecast snapshot tied permanently to the observation and information boundary at `T1`.

When replay advances to a later eligible prediction instant `T2`, the new prediction is a separate forecast produced from the later legitimate information state. It may replace the `T1` forecast as the consumer's **current** view at `T2`, but it does not alter, overwrite, backfill, or retroactively improve the forecast that existed at `T1`.

Later corrections, event qualification, final race truth, or later model outputs may affect retrospective target reconstruction or evaluation under their owning policies, but they must not change what prediction was associated with the historical observation at `T1`.

### 5. Successive predictions may or may not concern the same eventual event

Two successive predictions can be interpreted as updates about the same open target episode only when no qualifying pit event has occurred between their prediction instants and the later observation remains target-eligible.

If a qualifying event occurs between them, the earlier target episode has closed. The later prediction begins from the later observation and refers to the next qualifying event after that later instant, if the target remains meaningful.

Replay or evaluation must therefore not assume that every adjacent prediction for a driver forecasts one fixed pit event across the whole race.

### 6. Updating means new information, not historical revision

A change between successive predictions is semantically an update caused by moving to a later canonical observation with a later information boundary. The change may reflect newly legitimate race information and the reduced/changed future race progression still available.

The contract does not require predictions to change monotonically, smoothly, or by any particular amount. Stability, calibration, responsiveness, and scoring are evaluation/model questions, not semantic requirements here.

### 7. Coverage/horizon and likelihood semantics are a current-scope Product Owner decision

The approved upstream direction intentionally left the exact pit-window representation, prediction horizon, and uncertainty representation open. These choices materially determine what a consumer understands a V2 prediction to mean and are Product Owner-reserved under `governance/DECISION_BOUNDARIES.md`.

Before this slice can be completed, the Product Owner must approve a coherent semantic form that answers at least:

- whether the output expresses probability/likelihood across mutually exclusive future race-progression regions, a central window with confidence, or another consumer-facing uncertainty form;
- whether coverage is a finite declared future horizon or the remaining race scope;
- how possibilities outside the explicitly presented window/coverage are represented so omitted future outcomes are not mistaken for impossible outcomes; and
- how terminal no-event/domain-censoring possibility is interpreted within that output without redefining the target contract.

No option is normative until a durable Product Owner decision is persisted and this section is revised accordingly.

### 8. Output identity without a technical schema

At semantic level, a persisted or replayed prediction must be unambiguously attributable to:

- the race session;
- the driver entry;
- the canonical prediction checkpoint and prediction instant `T`; and
- the prediction semantics/version under which it was issued, when needed to prevent materially different approved semantics from being conflated.

Exact field names, IDs, storage types, serialization, versioning mechanism, or API shape are later design decisions.

### 9. Contract to Evaluation / Backtesting

Evaluation / Backtesting must consume the following settled parts of this output contract:

- one prediction is attached to one target-eligible canonical observation and prediction instant;
- the prediction concerns the canonical first qualifying tyre-service pit entry strictly after that instant;
- output meaning is predictive behavior estimation, not recommendation/optimization;
- each historical prediction snapshot is immutable and later predictions are separate later-state forecasts;
- adjacent predictions concern the same target episode only while no qualifying event has occurred between them;
- later target truth may be used to judge an earlier prediction but may not be treated as prediction-time information;
- evaluation may choose metrics and scoring only after consuming the final approved likelihood/coverage semantics from this slice.

Evaluation / Backtesting may define how these predictions are scored, weighted, sampled, grouped, and compared. It may not redefine their target, observation boundary, consumer-facing meaning, or replay immutability.

## Unknown routing

| Question | Classification | Owner / next artifact | Status |
| --- | --- | --- | --- |
| What exact consumer-facing likelihood/uncertainty form and coverage/horizon should a V2 pit-window prediction use, including treatment of outside-coverage and terminal no-event possibility? | Current-scope decision — Product Owner reserved | Product Owner / this slice + durable decision under `decisions/` | **Blocking — approval required** |
| How should approved output semantics be scored against observed-event, terminal no-event, and truncated target outcomes? | Cross-slice dependency | Evaluation / Backtesting | Unresolved here by design |
| What metrics, split policy, sampling/weighting, aggregation, and model-selection criteria should be used? | Cross-slice dependency | Evaluation / Backtesting | Unresolved here by design |
| What exact mathematical formulation realizes the approved output semantics? | Later-phase decision | Model/design + verification | Deferred |
| What exact probability parameterization, binning, calibration procedure, loss, or uncertainty estimation method is used? | Later-phase decision | Model/design + experimentation | Deferred |
| What schema, serialization, IDs, versioning mechanism, API, persistence, chart, or UI implements the output? | Later-phase decision | Architecture / implementation | Deferred |
| How should a future live product consume or refresh these predictions intra-lap? | Later-phase decision | Future product/semantic extension | Deferred; must not silently change the V2 core checkpoint semantics |

## Acceptance criteria

- [x] A consumer can explain which future event one V2 prediction concerns without reference to a model family or file format.
- [x] The output is clearly predictive of likely team/driver behavior and cannot be mistaken for strategy recommendation/optimization.
- [x] The relationship between the prediction and the canonical next-pit event is explicit.
- [ ] Horizon/coverage semantics are explicit enough that omitted future possibilities are not silently misinterpreted. Blocked on Product Owner decision.
- [x] Successive replay predictions have coherent historical/update semantics and later predictions do not retroactively alter earlier outputs.
- [ ] Uncertainty/likelihood meaning is explicit at the approved abstraction level without freezing a statistical implementation. Blocked on Product Owner decision.
- [ ] Evaluation / Backtesting receives one complete canonical prediction-output contract. Pending the same Product Owner decision.
- [x] Observation timing, event/censoring meaning, metrics, models, features, schemas, architecture, UI technology, and implementation remain outside scope.
- [x] Every unresolved question is classified as Current-scope, Cross-slice, or Later-phase.
- [ ] Any human-reserved choice that materially changes prediction semantics or uncertainty representation is escalated under `governance/USER_INTERACTION.md` and persisted only after approval. Escalation required now.
- [ ] Required independent review is completed before approval.

## Review record

- Full scoped review: pending completion of the Product Owner-reserved current-scope decision.
- Rework: pending.
- Bounded re-review: pending if substantive rework is required after full review.
- Approval evidence: pending.
