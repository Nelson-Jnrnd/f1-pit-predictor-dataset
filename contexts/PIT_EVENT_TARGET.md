# Pit Event / Target Semantics

## Status

Blocked — one Product Owner-reserved current-scope decision remains: the material definition of the V2 pit event. All other semantics below are drafted subject to that event definition and the required independent review.

## Abstraction level

Wave 1 — semantic specification.

## Outcome

Define the canonical V2 relationship between an approved point-in-time race observation and the driver's next relevant pit event, including target lifecycle, eligibility, terminal no-event/censoring, and truncation semantics without choosing a dataset encoding or model formulation.

## Scope

### In scope

- the domain meaning of the relevant V2 pit event;
- how "next" is ordered relative to the canonical prediction point;
- target lifecycle from an eligible observation until event occurrence or a terminal/end condition;
- semantic eligibility of a driver-observation / prediction-target pair;
- domain-level treatment of no later relevant event, end of driver participation, end of race, and genuinely truncated/non-observable follow-up;
- the event/target contract consumed by Prediction Output / Replay and Evaluation / Backtesting.

### Explicitly out of scope

- redefining prediction-point cadence, prediction instant, legitimate information, occurrence-time/availability-time rules, or replay immutability owned by Race Observation / Point-in-Time State;
- exact pit-window representation, output horizon, probability bins, uncertainty encoding, or replay presentation;
- loss functions, metrics, evaluation splits, scoring, aggregation, or model-selection procedure;
- label columns, dataframe schemas, timestamp fields, IDs, provider adapters, APIs, storage, packages, architecture, feature design, model family, or implementation;
- strategy recommendation or optimization semantics;
- next-compound prediction or multi-stint forecasting.

## Upstream inputs / semantic locks

- `decisions/2026-09-08-v2-project-direction.md` — V2 predicts likely timing of a driver's next pit stop from legitimately available information; it predicts behavior rather than recommending strategy; historical replay/backtesting is the initial ambition.
- `product/RESEARCH_PROBLEM.md` — exact pit-event definition is intentionally delegated to this slice; the target remains next-pit timing rather than the thesis-era next-lap binary formulation.
- `product/SYSTEM_SCOPE.md` — exact target/censoring semantics belong here; live inference, next-compound prediction, and recommendation remain outside the initial core.
- `contexts/CONTEXT_MAP.md` — this slice canonically owns pit-event identity, relation to the prediction point, target lifecycle, and censoring/eligibility semantics.
- `contexts/RACE_OBSERVATION_STATE.md` — every target attaches to one approved driver-specific observation; its prediction instant is the authoritative temporal boundary, and this slice must not redefine information availability.
- `legacy/THESIS_EVIDENCE.md` — legacy same-row `InLap` and shifted-next-row labels are evidence only; neither alignment is inherited implicitly by V2.

## Canonical ownership

This slice owns:

- what constitutes one relevant V2 pit event for a driver entry;
- which relevant event is "next" after an observation;
- when a target episode opens and closes;
- when a canonical observation is semantically eligible to form a prediction-target pair;
- terminal no-event/censoring and genuinely truncated/non-observable target outcomes at domain level;
- the downstream semantic contract for target consumers.

This slice does not own:

- when prediction points occur or what information is legitimate at them;
- how a pit-window prediction is represented or how far it extends;
- how target outcomes are encoded into rows, labels, tensors, survival records, bins, or other data structures;
- how predictions are scored, weighted, sampled, split, or aggregated;
- provider-specific detection logic or technical event reconstruction;
- model, feature, architecture, API, UI, storage, or implementation choices.

## Semantics / findings

### 1. Target attaches to an approved observation

A **prediction-target pair** begins with one canonical race observation defined by `contexts/RACE_OBSERVATION_STATE.md` for one race session and one driver entry at prediction instant `T`.

This slice does not create additional prediction points. It only determines the future target outcome, if any, associated with an already-valid observation.

The observation state at `T` remains immutable. The later event outcome is retrospective target truth used for replay/evaluation; it is not information that becomes available to the prediction at `T`.

### 2. Relevant V2 pit event — Product Owner decision pending

The material interpretation of the event the model predicts is Product Owner-reserved under `governance/DECISION_BOUNDARIES.md`. Wave 0 deliberately left the exact pit-event definition undecided, and legacy `InLap` behavior is non-normative evidence.

Until the Product Owner approves and the decision is persisted, **relevant pit event** below is an abstract placeholder for the approved event definition. No provider field, lap label, pit timestamp, tyre change, service action, or pit-lane transition is normative merely because it exists in historical data.

The recommended proposal for Product Owner approval is:

> A relevant V2 pit event is the start of a race pit-lane visit by the selected driver that results in a genuine pit stop/service during that visit. It includes ordinary tyre service, repairs or adjustments, and a stationary penalty served as part of the stop. It excludes a drive-through/pass-through with no stop, pre-race/grid movements, and garage/pit-lane movements after the driver's race participation has already ended. The event occurrence is anchored to the start of that qualifying pit-lane visit, not to later service completion or pit exit.

This proposal intentionally predicts **when the driver commits to the qualifying pit visit**, while requiring that the visit actually qualifies as a pit stop rather than treating every pit-lane traversal as the predicted event. The exact technical evidence used to establish the event later belongs to data/design and verification.

### 3. "Next" is ordered by event occurrence after the prediction instant

For an eligible observation at prediction instant `T`, the **next relevant pit event** is the earliest relevant event for the same driver entry and race session whose event occurrence is demonstrably **strictly after** `T`.

Consequences:

- "Next" is defined by race-event occurrence ordering, not by dataframe row order, minimum later lap number, provider record order, or legacy label shifting.
- An event that has already occurred by `T` is not the target for that observation even if its record or confirmation becomes available only later.
- An event already in progress at `T` is not a future event merely because the visit or service finishes after `T`; the next target, if any, is the next distinct relevant event that starts after `T`.
- If more than one qualifying event can occur within the same official race lap, the earliest qualifying occurrence after `T` is the target. Shared lap identity does not collapse multiple visits into one event.
- If ordering between `T` and a candidate event cannot be established from the eventual evidence, later data/verification work must treat the relation conservatively rather than assume the event is future.

The future-event relation uses eventual event occurrence truth to construct the target. It does **not** grant the prediction access to that future truth at `T`.

### 4. Target lifecycle

For one eligible prediction-target pair:

1. **Open:** the target episode opens at the observation's prediction instant `T`.
2. **At risk:** while the driver entry remains within the race-participation scope and no later relevant event has yet occurred, the target remains open.
3. **Observed event:** if a relevant event occurs strictly after `T` before the target reaches a terminal boundary, the earliest such event closes the target as an observed next-pit event.
4. **Terminal no-event / domain censoring:** if the driver entry reaches its terminal race-participation boundary, or the race session reaches its terminal boundary for that entry, without a later relevant event, the timing target closes without an observed event. Semantically, no later relevant pit event occurred within the remaining race scope. This is the canonical domain-level no-event/censoring outcome; later statistical encoding is not fixed here.
5. **Truncated / non-observable follow-up:** if the available historical evidence ends or becomes insufficient before either an observed event or a defensible terminal boundary can be established, the pair is truncated/indeterminate rather than being silently treated as a normal no-event outcome.

Once closed, a target episode is not reopened by later corrections to unrelated race facts. If later evidence changes whether the event itself occurred or whether a terminal boundary was correctly reconstructed, data/verification must resolve that target truth under an explicit reconstruction policy; it must not alter the earlier observation state.

### 5. Eligibility for a prediction-target pair

A canonical race observation is **target-eligible** only when all of the following semantic conditions hold at prediction instant `T`:

1. the observation is valid under `contexts/RACE_OBSERVATION_STATE.md` for one identifiable race session and driver entry;
2. the selected driver entry has not already reached a terminal race-participation state by `T`;
3. there remains race progression in which a later relevant pit event could semantically occur for that entry; and
4. the prediction-target relation can be anchored to `T` without requiring future information to alter the observation itself.

Eligibility is about whether the target question "what is this driver's next relevant pit event after now?" is meaningful at that observation. It does not require knowing at `T` that a future event will occur.

Therefore:

- an observation may be eligible even if retrospective truth later shows that no further relevant pit event occurred;
- an observation at or after the driver's terminal race-participation boundary is not target-eligible merely to create a convenient negative label;
- the final canonical observation produced by Race Observation / State can exist as a race-state checkpoint yet be ineligible for this target if no future race progression remains for that entry;
- temporary race neutralization or suspension does not by itself end eligibility if the driver entry remains capable of continuing when the race resumes;
- eligibility must not be retroactively decided from whether a later pit event happened. Outcome occurrence and pair eligibility are separate concepts.

### 6. Driver terminal boundary

The target stops following a driver entry when that entry's participation has reached a race-terminal state such that no later relevant V2 race pit event can occur within the same participation.

Examples include a completed race/finish for that entry, definitive retirement/withdrawal from further race participation, or another race-status outcome that makes later participation impossible. Exact provider status values, classification codes, or reconstruction rules are later data/design concerns.

If a qualifying relevant pit event occurs before or as part of the sequence that leads to retirement, the event is observed if and only if it satisfies the approved event definition and its occurrence is after `T`. Retirement does not erase an already-observed qualifying event.

### 7. End of race and no future pit

If the race or the selected driver's participation ends without another relevant pit event after `T`, the target has a **known race-bounded no-event outcome**: no next relevant pit event occurred before the semantic target boundary.

At this semantic level, that outcome is called **terminal no-event / domain censoring** because the next-event timing is unobserved within the finite race follow-up. This terminology does not force later modeling to use a particular censoring variable, survival formulation, infinite time, extra class, or output bin.

Prediction Output / Replay must decide how a prediction communicates probability over its chosen future scope. Evaluation / Backtesting must decide how such terminal outcomes are scored. Neither consumer may redefine the underlying fact that no later relevant event occurred before the entry/race terminal boundary.

### 8. Truncation is not ordinary terminal no-event

A pair is **truncated/indeterminate** when the historical evidence is insufficient to establish either:

- the next relevant event after `T`, or
- a defensible terminal boundary proving that no such event occurred within the remaining race scope.

Examples can include missing event coverage, incomplete race records, unresolved ordering around `T`, or an evidence gap that prevents determining whether a candidate pit visit qualifies under the approved event definition.

Truncation is an evidence/reconstruction failure, not a semantic negative. Later data/verification work may define exclusion, conservative handling, or validation requirements, but it must not silently convert indeterminate follow-up into a no-event target.

### 9. Event truth and prediction-time knowledge are separate

Target construction is retrospective by nature: after the race, later facts may be used to determine what event actually occurred and when, subject to a defensible event-reconstruction policy.

This does not violate point-in-time correctness because the future event truth is target/evaluation truth, not an input to the prediction at `T`.

Conversely, later event truth must not be used to alter:

- whether information was legitimate in the observation at `T`;
- a provisional/corrected race fact's historical version at `T`;
- the observation's prediction instant; or
- the set of inputs from which the prediction was produced.

### 10. Edge-case rules at semantic level

Subject to the approved event definition:

- **Multiple stops:** the first distinct relevant event strictly after `T` is the target; later stops belong to later target episodes from later eligible observations.
- **Same-lap stops:** lap equality does not determine event equality or ordering; occurrence ordering governs.
- **Pit event already underway at `T`:** it is not the future target; only a later distinct relevant event can be next.
- **Safety-car, VSC, red-flag, weather, damage, or penalty context:** motive does not by itself change event identity. A visit counts or does not count according to the approved event definition, not whether it was strategically planned.
- **Retirement after a qualifying stop:** the qualifying event remains the observed target if it occurred first after `T`.
- **Retirement without a later qualifying stop:** close at the driver's terminal boundary as terminal no-event/domain censoring.
- **Race finish without a later qualifying stop:** close at the applicable terminal boundary as terminal no-event/domain censoring.
- **Post-finish/post-retirement garage movement:** outside the race target scope once participation is terminal.
- **Ambiguous event classification or ordering:** truncated/indeterminate until a later approved data/verification policy can establish defensible truth; do not guess for semantic convenience.

### 11. Downstream event/target contract

Prediction Output / Replay and Evaluation / Backtesting must consume the following canonical contract:

- Every target attaches to one approved driver-specific observation and its prediction instant `T`.
- The target asks for the first relevant V2 pit event for the same driver entry and race session occurring strictly after `T`.
- "Next" is determined by event occurrence ordering, not implementation row/lap convenience.
- Eligibility is determined at the semantic observation boundary and does not depend on whether a future event later occurs.
- A later qualifying event closes the target as observed.
- End of driver participation or race scope without a later qualifying event closes the target as terminal no-event/domain censoring.
- Insufficient evidence before either event or terminal boundary is truncation/indeterminate follow-up, not an ordinary negative.
- Future target truth may be used retrospectively for labeling/evaluation but may not leak into the point-in-time observation.
- Dataset encoding, output horizon/representation, statistical censoring representation, and scoring remain owned by later slices/phases.

Consumers may refine only their owned representation/evaluation questions; they may not redefine the event, temporal relation, eligibility, or terminal semantics established here.

## Unknown routing

| Question | Classification | Owner / next artifact | Status |
| --- | --- | --- | --- |
| What materially counts as the V2 pit event (qualifying service visit versus materially different alternatives)? | Current-scope decision — Product Owner reserved | Product Owner / this artifact + durable decision record | **Blocking — approval requested** |
| What exact future horizon/window/probability representation is emitted, including representation beyond race end? | Cross-slice dependency | Prediction Output / Replay Semantics | Unresolved here by design |
| How are observed, terminal no-event/censored, and truncated pairs scored, weighted, sampled, or aggregated? | Cross-slice dependency | Evaluation / Backtesting | Unresolved here by design |
| Which provider fields/events prove a qualifying pit visit, event occurrence time, terminal state, or ordering around `T`? | Later-phase decision | Data/design + verification | Deferred; must implement this contract without changing it |
| How are terminal no-event/censoring and truncation represented in concrete labels/tables/tensors? | Later-phase decision | Data/model design | Deferred |
| What conservative policy applies when provider history cannot establish event classification or temporal ordering? | Later-phase decision | Data/design + verification | Deferred; may exclude/mark indeterminate but may not invent target truth |
| What model family, hazard/survival/regression/classification formulation, features, schemas, APIs, storage, or runtime implements the target? | Later-phase decision | Architecture / model / implementation | Deferred |

No other unresolved Current-scope decision is presently identified. The event-definition row must be resolved and persisted before this artifact can enter independent review as semantically complete.

## Acceptance criteria

- [ ] The relevant pit event is defined unambiguously enough to determine whether an event occurred for a driver. **Blocked on Product Owner decision.**
- [x] "Next pit" is defined relative to the canonical prediction point rather than by implementation convenience.
- [x] Eligibility for a prediction-target pair is explicit at semantic level.
- [x] Censoring/truncation/end-of-race and no-future-event cases have coherent domain semantics.
- [x] Event/target semantics do not rely on future information being available at the prediction point.
- [x] The target meaning is independent of any chosen dataset encoding or model formulation.
- [x] Prediction Output / Replay and Evaluation / Backtesting receive one canonical event/target contract.
- [x] Observation timing, output representation, metrics, schemas, features, architecture, and implementation remain outside scope.
- [x] Every unresolved question is classified as Current-scope, Cross-slice, or Later-phase.
- [ ] Any human-reserved change to the material meaning of the predicted event is escalated under `governance/USER_INTERACTION.md` and persisted only after approval. **Escalation pending Product Owner response; no semantic decision has been persisted as approved.**
- [ ] Required independent review is completed before approval.

## Review record

- Full scoped review: pending; do not request until the Product Owner-reserved event definition is resolved and persisted.
- Rework: pending / not yet applicable.
- Bounded re-review: pending / not yet applicable.
- Approval evidence: pending.
