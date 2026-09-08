# Race Observation / Point-in-Time State

## Status

Approved

## Abstraction level

Wave 1 — semantic specification.

## Outcome

Define the canonical V2 race observation and its point-in-time information boundary so downstream target, prediction-output, replay, and evaluation work share one leakage-safe meaning of what was knowable when a prediction was made.

## Scope

### In scope

- the canonical prediction-point cadence within race progression;
- the information-time boundary for a point-in-time observation;
- occurrence-time versus availability-time semantics;
- treatment of partial, delayed, corrected, and later-confirmed race information;
- the minimum race/session/driver/lap/time identities required to identify an observation without fixing a technical schema;
- the semantic contract consumed by downstream Wave 1 slices.

### Explicitly out of scope

- what counts as the relevant pit event, next-pit target construction, censoring, or target eligibility;
- exact pit-window representation, horizon, probability/uncertainty encoding, or replay presentation;
- evaluation metrics, dataset splits, scoring, or backtest procedure beyond consuming this observation contract;
- feature selection, feature engineering, schemas, timestamp column names, APIs, packages, storage, architecture, model choice, UI, or provider-specific implementation;
- strategy recommendation or optimization.

## Upstream inputs / semantic locks

- `product/PROJECT_VISION.md` — V2 predicts likely next-pit timing from legitimately available information and is historical-replay/backtesting first.
- `product/RESEARCH_PROBLEM.md` — predictions must be point-in-time correct; exact observation timing and availability rules are owned here.
- `product/SYSTEM_SCOPE.md` — future information must not influence an earlier prediction; live inference remains a later extension.
- `contexts/CONTEXT_MAP.md` — Race Observation / State canonically owns prediction-point meaning and the legitimate-information boundary; downstream slices consume rather than redefine it.
- `decisions/2026-09-08-v2-project-direction.md` — predictive, not prescriptive; pit-window-style next-pit timing is the core direction; point-in-time availability is a durable semantic lock.
- Issue #4 legacy thesis evidence, when available, is evidence only and cannot override these V2 semantics.

## Canonical ownership

This slice owns:

- what a V2 prediction point means in race progression;
- the causal/information boundary of the point-in-time state at that point;
- the meaning of occurrence time, availability time, and as-of time for race information;
- the observation identities needed by downstream semantic slices;
- the rule for historical knowledge when information is delayed, corrected, or confirmed later.

This slice does not own:

- pit-event identity, target construction, censoring, or target eligibility;
- prediction-window/horizon/output representation;
- replay UI or presentation cadence beyond the canonical semantic prediction points;
- evaluation metrics, splits, scoring, or model-selection procedure;
- features, schemas, provider adapters, timestamp fields, storage, architecture, or implementation.

## Semantics / findings

### 1. Canonical observation

A **race observation** is the point-in-time state for one driver entry in one specific race session at one canonical prediction point.

It is not a final race record truncated by lap number. It is a reconstruction of what could legitimately have been known at the prediction instant.

Each observation has:

- one race-session identity;
- one driver-entry identity within that session;
- one checkpoint in that driver's race progression;
- one prediction instant / as-of boundary;
- the race information legitimately available by that boundary.

### 2. Canonical prediction points

For the V2 core, predictions are made at driver-relative progression checkpoints:

1. an initial checkpoint when the official race start is available to the observer, with the driver's completed-race-lap count equal to `0`; and
2. one checkpoint whenever a new official race-lap completion for that driver becomes available to the observer.

For a completed-lap checkpoint, let `L` be the official race lap just completed by the selected driver. The prediction instant is the first information-time instant at which that lap completion is legitimately observable. The observation is therefore an as-of state at that instant, not merely a row labeled with lap `L`.

The lap index is driver-relative. A selected driver being on completed lap `L` says nothing about which lap the leader or another driver has completed.

A later live extension may introduce additional intra-lap trigger types only through a bounded semantic extension/reconciliation. It must not silently reinterpret these V2 core checkpoints.

### 3. Prediction instant and information-time ordering

The **prediction instant** is the causal cutoff for an observation. It is ordered on the race session's information timeline and is the instant at which the checkpoint trigger itself has become observable.

The point-in-time state includes information available no later than that instant. Information first available after it is future information for that prediction, regardless of when the underlying event physically occurred.

The boundary is inclusive: information demonstrably available at or before the prediction instant may be considered known. If a source gives only coarse timestamps and the ordering of two supposedly simultaneous facts cannot be established, equality of timestamps alone is not proof that the other fact was available before the prediction. Later data/verification work must use source ordering guarantees or a conservative treatment rather than assume a favorable order.

### 4. Occurrence time is not availability time

Two temporal notions are distinct when they materially affect leakage:

- **Occurrence/effective time** — when the underlying race event happened, or the period/event to which a statement refers.
- **Availability time** — when the information or claim became observable to the prediction process.

Point-in-time legitimacy is governed by availability time, not by retrospective occurrence time.

Consequences:

- An incident may occur before the prediction instant but remain unknown until after it; it is not legitimate information for that prediction.
- A fact may be recorded or confirmed after the prediction instant even though it describes an earlier event; the later-confirmed fact must not be backfilled into the earlier observation.
- A message available before the prediction instant may legitimately refer to a future plan, expectation, forecast, or instruction. The message itself is known; the later realized outcome is not thereby known.
- Pre-race/session facts are legitimate during the race if they were already available and have not been superseded by information available by the prediction instant.

### 5. Legitimate-information rule

A race fact, claim, state element, or deterministic derivation may be used in an observation only if all of the following are true:

1. the information available by the prediction instant is the same version being represented in the observation;
2. the information's availability time is no later than the prediction instant;
3. any derivation uses only inputs that are themselves legitimate at that instant; and
4. the derivation does not depend on a later race outcome, later correction, final classification, future normalization, or any other retrospectively known value.

This rule defines permission, not a required feature set. Later design may intentionally use a smaller subset of legitimate information but may not use information outside this boundary.

### 6. Partial-lap information

A checkpoint is indexed by the selected driver's completed-lap progression, but the state is not restricted to fully completed laps.

If information about an ongoing/partial lap is genuinely available by the prediction instant, it is legitimate point-in-time information. This applies to the selected driver and to other competitors. However, a summary or value that requires a lap to finish is not legitimate until the information needed to establish that completed-lap result is available.

Therefore downstream work must not reconstruct a checkpoint by simply taking all final rows whose lap number is less than or equal to the selected driver's checkpoint lap. That shortcut can both omit legitimately known intra-lap information and include retrospectively completed information that was not yet available.

### 7. Race-wide facts are aligned by time, not by lap number

At a selected driver's prediction instant, other drivers may be ahead, behind, lapped, in the pit lane, retired, or on different completed-lap counts.

Race-wide information is included according to its availability by the selected driver's prediction instant. It must not be aligned by giving every driver the same lap number as the selected driver, nor by importing facts from another driver's later checkpoint.

This same rule applies to session/race-control state: a safety-car state, red flag, penalty, retirement status, classification change, weather observation, or similar race fact is legitimate only to the extent it was available by the prediction instant. The examples do not mandate any feature.

### 8. Delayed, corrected, and later-confirmed information

Historical truth and historical knowledge are distinct.

- **Delayed information:** if first availability is after the prediction instant, exclude it from the earlier observation even if occurrence was earlier.
- **Correction:** a corrected value becomes legitimate only from the time the correction is available. It does not retroactively rewrite earlier observations.
- **Later confirmation:** if an earlier claim was provisional and confirmation arrives later, earlier observations retain only the provisional knowledge that was actually available then. The confirmed final state is legitimate only from its availability onward.
- **Supersession:** once a correction/superseding claim is available, later observations may use the then-current known version; earlier observations remain unchanged.

A historical source that stores only a final corrected value does not, by itself, prove that value was knowable at earlier prediction points. Later data/verification work must establish defensible availability evidence or a conservative reconstruction rule before such information can be used leakage-safely.

### 9. Minimum semantic identities

The observation contract requires the following concepts to be unambiguous without prescribing field names or storage types:

- **Race event identity:** enough identity to distinguish the championship event/race occurrence from every other event.
- **Race-session identity:** the specific race session instance within that event; other session types are not interchangeable with it.
- **Driver-entry identity:** the specific competitor entry participating in that race session; display name, abbreviation, or car number alone need not be the canonical technical key.
- **Driver lap identity:** the selected driver's official race-lap ordinal, with `0` reserved semantically for the initial race-start checkpoint and positive values representing completed official race laps.
- **Prediction instant / as-of identity:** a session-relative instant or equivalent total ordering sufficient to decide whether information was available before, at, or after the checkpoint.
- **Occurrence/effective time and availability time:** distinct temporal meanings for information whenever conflating them could alter point-in-time legitimacy.

No particular schema, timestamp precision, provider ID, or storage representation is fixed here.

### 10. Immutable replay meaning

Once an observation at prediction instant `T` has been defined, later race knowledge must not alter what that observation means.

A replay may display later corrections or outcomes when advancing beyond `T`, but it must not silently rewrite the input state of the prediction that was made at `T`. Reproducible evaluation must be able to reconstruct the same semantic knowledge state for the same observation under the declared source/reconstruction policy.

### 11. Downstream observation/state contract

Pit Event / Target Semantics, Prediction Output / Replay Semantics, and Evaluation / Backtesting must consume the following contract:

- A prediction is attached to one driver-specific observation identified by race session, driver entry, checkpoint progression, and prediction instant.
- The prediction instant is the authoritative boundary between knowledge available to the prediction and information that is future for that prediction.
- Availability, not retrospective occurrence, determines whether race information is legitimate at that boundary.
- Later corrections/confirmations do not retroactively change prior observation states.
- Driver/race-wide state is aligned by the common prediction instant, not by forcing equal lap numbers across competitors.
- Partial-lap information is legitimate only when actually available by the prediction instant; completed-lap summaries cannot be used before they become available.
- Any derived state must be causally computable from information legitimate at the same boundary.

Downstream ownership remains unchanged:

- Pit Event / Target Semantics decides which pit event, if any, is the relevant future event and how eligibility/censoring works. When it needs a notion of "future", it must relate that event to this observation's prediction instant rather than redefine information availability.
- Prediction Output / Replay Semantics decides the pit-window/horizon/output meaning and presentation/update behavior while associating outputs with this observation contract.
- Evaluation / Backtesting decides units, splits, metrics, and scoring while reconstructing observations under this same point-in-time boundary.

## Unknown routing

| Question | Classification | Owner / next artifact | Status |
| --- | --- | --- | --- |
| What exact pit event is the future target, and how are eligibility/censoring handled? | Cross-slice dependency | Pit Event / Target Semantics | Unresolved here by design |
| What pit-window/horizon/probability representation is emitted? | Cross-slice dependency | Prediction Output / Replay Semantics | Unresolved here by design |
| How are observations scored, split, sampled, or aggregated in backtests? | Cross-slice dependency | Evaluation / Backtesting | Unresolved here by design |
| Which source/provider fields establish occurrence and availability time, including tie ordering? | Later-phase decision | Data/design + verification | Deferred; must satisfy this semantic boundary |
| What conservative reconstruction policy is used when historical sources do not preserve availability time or correction history? | Later-phase decision | Data/design + verification | Deferred; may not assume retrospective final truth was available earlier |
| Which legitimate state elements become model features or derived variables? | Later-phase decision | Feature/model design | Deferred |
| What schema, IDs, timestamp types, storage, API, package, or runtime representation implements these concepts? | Later-phase decision | Architecture / implementation | Deferred |
| Should a future live product add intra-lap prediction triggers beyond the V2 core checkpoints? | Later-phase decision | Future product/semantic extension | Deferred; would require bounded reconciliation before changing core semantics |

There are no unresolved Current-scope decisions in this slice.

## Acceptance criteria

- [x] A prediction point is defined unambiguously at semantic level.
- [x] Legitimately available versus future information is explicit.
- [x] Point-in-time correctness is strong enough to prevent downstream slices from silently using future race knowledge.
- [x] Relevant race/driver/session/lap/time identities are unambiguous without freezing a technical schema.
- [x] Occurrence time and information-availability time are distinguished where materially necessary.
- [x] Delayed/corrected/later-confirmed information has coherent semantic treatment where relevant.
- [x] Downstream target, output, and evaluation slices receive one canonical observation/state contract rather than duplicating it.
- [x] Target meaning, output representation, metrics, features, schemas, architecture, and implementation remain outside scope.
- [x] Every unresolved question is classified as Current-scope, Cross-slice, or Later-phase.
- [x] No human-reserved change to the approved information philosophy was required; this slice preserves and makes operational the existing point-in-time correctness lock.
- [x] Required independent review is completed before approval.

## Review record

- Full scoped review: PASS — independent scoped reviewer; GitHub review recorded by `Nelson-Jnrnd` on PR #9, review `pullrequestreview-5140916570`, against head `05595fb5ee0ef70b6e929ec01d45d1c4f51ff651` on 2026-09-08. No Blocking, Major, or Minor findings.
- Rework: none required; only review metadata/traceability was updated after the passing review, as explicitly requested by the reviewer.
- Bounded re-review: not applicable because no substantive rework was required.
- Approval evidence: passing PR #9 review `pullrequestreview-5140916570`; artifact transitioned to `Approved` without semantic changes.
