# V2 Pit-Event Reconstruction and Target-Episode Dataset Contract

## Status

Draft — reworked after the full scoped review on PR #25. Bounded re-review required before approval.

## Abstraction level

Detailed data/target design — retrospective pit-visit/event reconstruction, tyre-service qualification, target eligibility materialization, target-episode identity, target resolution states, terminal/race-participation scope, truncation handling, and provenance.

This artifact does not redefine point-in-time observation legitimacy, prediction probability representation, model formulation, evaluation metrics/statistics, live inference, or production implementation.

## Issue / branch

- Issue: #19 — `Design — pit-event reconstruction and target-episode dataset contract`
- Parent: #16
- Upstream architecture: #17 / `design/SYSTEM_ARCHITECTURE.md`
- Upstream observation design: #18 / `design/OBSERVATION_RECONSTRUCTION.md`
- Branch: `design/target-reconstruction`
- PR: #25

## Outcome

The V2 target subsystem has two technically separate boundaries with different causal permissions:

1. **Causal target eligibility / episode initialization** consumes one immutable `CanonicalObservation` and no future event truth. It decides whether the next-pit question is defined and, when eligible, creates one immutable target-episode identity.
2. **Retrospective event reconstruction / target resolution** may use later race evidence to reconstruct pit visits, determine whether tyre service occurred, establish pit-entry occurrence, establish race-participation/terminal scope, and resolve the already-created episode.

A pit-lane visit and a relevant V2 pit event are not the same object. Every reconstructed visit is retained as a visit candidate. A visit becomes a relevant V2 event only when both conditions are defensibly established:

- tyre service occurred during that visit; and
- the visit belongs to the driver's race participation, before the applicable terminal participation boundary.

The event occurrence remains the pit-lane entry of that same visit.

For an eligible observation at prediction instant `T`, the target is the earliest qualifying pit-entry occurrence that is demonstrably **strictly after `T` and strictly before the applicable terminal boundary**. A visit/event at or after the terminal boundary is outside target scope. If ordering against `T`, another candidate visit, or the terminal boundary is unresolved in a way that could change target membership or identity, the episode resolves as `TRUNCATED_INDETERMINATE`; reconstruction never guesses past the ambiguity.

## Upstream locks consumed unchanged

This design consumes and does not redefine:

- `contexts/PIT_EVENT_TARGET.md` — tyre-service-only event meaning, pit-lane-entry occurrence anchor, strict-after-`T` ordering, eligibility, target lifecycle, race-participation terminal boundary, terminal no-event, and truncation semantics;
- `decisions/2026-09-08-v2-pit-event-scope.md` — Product Owner-approved tyre-service-only scope and pit-entry occurrence anchor, including exclusion of post-finish/post-retirement movements;
- `contexts/RACE_OBSERVATION_STATE.md` — canonical observation identity and prediction instant / point-in-time information boundary;
- `design/OBSERVATION_RECONSTRUCTION.md` — immutable observation artifact, race/session/driver/checkpoint identities, verified prediction boundary, and observation quality/provenance;
- `design/SYSTEM_ARCHITECTURE.md` — target ownership is split between causal episode initialization and retrospective target resolution; replay/prediction may consume the causal boundary but not retrospective target truth;
- `contexts/WAVE1_SEMANTIC_INTEGRATION.md` — event identity and target episode identity remain distinct, and future target truth cannot flow backward into observations or predictions.

A material change to tyre-service-only qualification, pit-lane-entry occurrence, or target race-participation scope requires reconciliation of approved semantics. This design only makes those locks technically reconstructable.

## Evidence roles: prediction availability versus retrospective truth

The availability-authority rules in #18 govern whether information may appear in the historical prediction-time observation. They do **not** imply that the same source is unusable as retrospective target evidence after the race.

Target reconstruction has a separate evidence question:

> Is the frozen historical evidence sufficiently complete and reliable to establish the actual pit visit, tyre-service qualification, pit-entry occurrence, race-participation membership, and terminal follow-up needed to resolve this target episode?

A static archive may be `UNVERIFIED_ARCHIVE` for historical prediction-time availability yet still contribute retrospective target truth if its target-reconstruction behavior is independently validated for the claimed endpoint/era. Conversely, a source suitable for an observation boundary is not automatically sufficient to prove tyre service, race-participation membership, or terminal no-event.

The two validations must not be conflated.

## Concrete source evidence inventory

FastF1 implementation/documentation evidence below was inspected at upstream commit `227cf301fb4bcf1705bcb1866de1fe5dbcef6071` (2026-08-28). This is evidence, not a package-version commitment.

| Evidence | Observed behavior | V2 target use | Limitation / required validation |
| --- | --- | --- | --- |
| Raw `TimingData` driver updates | FastF1 parser documents `InPit=True` as received once on pit entry and `InPit=False` once on pit exit | Primary candidate evidence for pit-visit segmentation and pit-entry occurrence | Archive completeness, duplicate/correction behavior, grid/pre-race movement, post-terminal movement, and same-lap multiple visits require verification |
| FastF1 `PitInTime` / `PitOutTime` | Parsed/calculated lap fields representing pit entry/exit session times | Cross-check / fallback candidate only under a validated reconstruction rule | FastF1 may correct/postprocess lap timing; calculated timestamps have provider limitations |
| Raw `TimingAppData` `Stints` | Contains stint index plus sparse `Compound`, `New`, `TotalLaps`, `StartLaps`, `TyresNotChanged`, etc. | Candidate retrospective tyre-state evidence around visits | Sparse/delta-like; exact field meanings vary; `TyresNotChanged` is explicitly uncertain in FastF1 source |
| Processed lap tyre fields | `Compound`, `TyreLife`, `FreshTyre`, `Stint` available in `Session.laps` | Retrospective cross-check and normalized tyre-state evidence when lineage/reliability is established | Processed data can be corrected/filled; cannot alone prove every same-compound change or no-change visit |
| FastF1 stint construction | FastF1 source notes each drive through pit lane starts a new stint independent of tyres being changed | Important negative constraint | **Stint change alone is not proof of tyre service** |
| Session results | Driver result includes classification, status, completed laps, etc. | Candidate evidence for final participation outcome | Final status can establish terminal outcome but may not identify an exact terminal instant |
| Session status | Session lifecycle includes started/finished/finalized transitions | Candidate race-terminal evidence | Session terminal time and driver-specific terminal time remain distinct |
| Race-control messages | Can include driver/session event messages | Corroborative participation/terminal evidence | Message absence is not proof of continued or ended participation |
| Legacy CSV `PitStatus` | Derived from `PitInTime`/`PitOutTime`; one lap row with tyre/stint fields | Historical comparison / QA only | Does not retain raw visit identity, raw order, correction history, or reliable multiple-same-lap distinction |

### Key provider findings

FastF1's current timing parser handles raw `InPit` state changes as pit-entry and pit-exit transitions and derives `PitInTime`/`PitOutTime` from those updates. It also performs corrections around grid laps, late data, lap alignment, and missing/edge laps. Processed lap fields are therefore not the sole technical identity of a pit visit.

FastF1's `TimingAppData` exposes tyre/stint records, but its source labels `TyresNotChanged` as uncertain. That field is not accepted as sole service/no-service authority without a separate verification result.

FastF1 also notes that its source considers each passage through the pit lane the beginning of a new stint independent of whether tyres were changed. Consequently, `Stint` transition may correlate with a visit but is not itself a tyre-service signal.

## Target-truth source snapshot and support contract

### Frozen retrospective evidence

Every target reconstruction run consumes frozen, identifiable source snapshots. The target subsystem may consume the same raw bytes as observation reconstruction or additional retrospective sources, but records them under target-specific reconstruction provenance and support rules.

A logical `TargetTruthSourceManifest` records at least:

- `RaceSessionKey`;
- source/provider family and acquisition mode;
- endpoint/source names used for pit-entry, tyre-service, participation, and terminal evidence;
- exact frozen content identities/hashes;
- retrieval/capture date;
- parser/adapter revision;
- completeness/gap indicators;
- target-reconstruction support validation references by endpoint/era;
- repository revision and reconstruction run ID.

Freezing makes target reconstruction reproducible. It does not by itself prove source completeness or semantic reliability.

### Target reconstruction support validation

Verification must maintain scoped support records:

```text
TargetReconstructionSupportScope = (
    source/provider family,
    acquisition_mode,
    endpoint/evidence family,
    season/era range,
    provider/archive revision where relevant
)
```

A support result may independently establish capabilities such as:

- pit-entry transition reconstruction;
- pit-exit/visit segmentation;
- tyre-service positive qualification;
- tyre-service negative qualification;
- race-participation membership reconstruction;
- terminal participation reconstruction;
- complete interval coverage for no-event claims.

A source may support one capability without supporting another. No single global `SUPPORTED` flag is sufficient.

## Reconstructed pit-visit contract

### Pit visit is distinct from qualifying event

A `PitVisit` is one reconstructed traversal/occupancy episode of the pit lane for one `DriverEntryKey`. It exists independently of whether tyre service occurred and independently of whether the traversal ultimately belongs to the V2 race target scope.

```text
PitVisitArtifact
  artifact_id
  pit_visit_key
    race_session_key
    driver_entry_key
    visit_discriminator
  pit_entry_occurrence
  pit_exit_occurrence?
  race_participation_scope
  visit_segmentation_quality
  source_lineage
  reconstruction_policy_version
  target_truth_support_refs
  service_qualification
  quality / reason_codes
```

`pit_exit_occurrence` may be absent when entry is defensibly reconstructed but the driver never exits or exit evidence is missing. Exit is not the event occurrence anchor.

### Pit visit identity

A pit visit is never keyed solely by lap number, stint number, `NumberOfPitStops`, or dataframe row.

```text
PitVisitKey = (
    DriverEntryKey,
    visit_discriminator
)
```

`visit_discriminator` deterministically identifies one distinct reconstructed pit-entry transition within the frozen evidence. Exact serialization belongs to implementation.

Invariants:

- two distinct entry transitions produce distinct visit keys even on the same official lap;
- duplicate representations of the same transition do not create duplicate visits once equivalence is defensibly established;
- lap/stint labels are descriptive metadata only;
- revised evidence/reconstruction may create a new artifact version without overwriting prior artifacts.

### Visit state-machine reconstruction

For a source validated to represent driver pit-lane state transitions:

```text
OUTSIDE_PIT --entry evidence--> IN_PIT
IN_PIT     --exit evidence----> OUTSIDE_PIT
```

Rules:

1. A canonical entry transition starts one candidate visit.
2. A canonical exit transition closes that visit but does not determine qualification.
3. Duplicate identical-state updates are ignored only when source-lineage equivalence demonstrates duplication.
4. Entry while already `IN_PIT`, or exit while `OUTSIDE_PIT`, is a segmentation anomaly unless an explicit source reset/correction rule explains it.
5. A visit may remain exit-open at terminal participation; this does not erase a defensible pit entry.
6. Pre-race/grid movements are retained as raw/reconstructed traversals when useful for audit but classified outside `RACE_PARTICIPATION` and cannot create V2 events.
7. **Post-terminal pit/garage movements are likewise classified outside `RACE_PARTICIPATION` and cannot create V2 events.**
8. Same-lap entries remain separate visits when transition evidence distinguishes them.
9. If a source gap can hide an additional entry/exit and thereby change visit identity/order or race-scope membership, affected coverage is indeterminate.

Exact parser/reset logic is implementation/verification work; these invariants are the design contract.

## Pit-entry occurrence representation

The relevant event occurrence is the pit-lane entry of a qualifying in-scope visit.

Historical evidence may have finite precision, so occurrence is represented as an exact instant or conservative interval/bounds:

```text
PitEntryOccurrence
  session_clock_reference
  exact_time?
  lower_bound?
  upper_bound?
  precision / quality
  source_evidence_refs
  reconstruction_method_version
```

A processed FastF1 `PitInTime` may contribute under a validated method, but the event is not defined by that provider field.

## Race-participation and terminal scope

### Applicable terminal boundary

For one driver entry, retrospective target reconstruction produces the earliest defensible boundary after which that entry cannot produce another V2 race pit event within the same participation:

```text
TerminalBoundary
  artifact_id
  terminal_kind
    DRIVER_PARTICIPATION_TERMINAL
    RACE_SESSION_TERMINAL
  driver_entry_key
  occurrence_time_or_bounds
  evidence_refs
  terminal_reconstruction_method_version
  quality
```

Potential evidence includes official/final result status/classification, completed-lap evidence, session status, timing/race-control evidence of definitive retirement/withdrawal, and other independently validated participation evidence.

Final results are legitimate retrospective target evidence, but a final `Status` string alone may establish that participation ended without proving an exact instant. Precision is required only to the extent needed to decide target membership/order.

Processed/synthetic laps inserted by FastF1 for retired drivers are not sole authority for the retirement instant.

### Visit relation to terminal boundary

Every pit visit that could affect a target is classified against the applicable terminal boundary `B`:

```text
VisitTerminalRelation =
  STRICTLY_BEFORE_TERMINAL
  AT_OR_AFTER_TERMINAL
  INDETERMINATE_TERMINAL_RELATION
```

For exact comparable instants:

- `E < B` => `STRICTLY_BEFORE_TERMINAL`;
- `E >= B` => `AT_OR_AFTER_TERMINAL`.

For bounded/coarse evidence:

- if `E.upper_bound < B.lower_bound`, the visit is proven strictly before terminal;
- if `E.lower_bound >= B.upper_bound`, the visit is proven at/after terminal;
- otherwise the intervals overlap and the relation is indeterminate.

No equality or overlapping bound is promoted to an in-scope pre-terminal event.

### Race-participation scope state

A reconstructed visit carries one of:

```text
VisitRaceParticipationScope =
  IN_RACE_PARTICIPATION
  OUTSIDE_RACE_PARTICIPATION
  INDETERMINATE_RACE_PARTICIPATION
```

For a race visit to be `IN_RACE_PARTICIPATION`, evidence must establish that it occurs after the applicable race-start boundary and strictly before the applicable terminal boundary. Pre-race/grid and post-terminal movements are `OUTSIDE_RACE_PARTICIPATION`. If start/terminal ordering uncertainty could change scope membership, the visit is `INDETERMINATE_RACE_PARTICIPATION`.

This scope state is target truth. It must not be backfilled into the historical observation at `T`.

## Relation to observation prediction instant

The resolver consumes the exact prediction boundary from the immutable #18 observation artifact and does not recalculate `T`.

Candidate entry `E` relative to `T` is classified:

```text
VisitPredictionRelation =
  BEFORE_OR_AT_T
  STRICTLY_AFTER_T
  INDETERMINATE_PREDICTION_RELATION
```

For exact comparable times, ordinary numeric ordering applies. For bounds, `E.lower_bound > T.upper_bound` proves strictly-after and `E.upper_bound <= T.lower_bound` proves before-or-at. Overlap is indeterminate. Equality is never promoted to strictly-after.

## Tyre-service qualification

### Three-state qualification

Each reconstructed visit receives exactly one retrospective service state:

```text
TyreServiceQualification =
  CONFIRMED_TYRE_SERVICE
  CONFIRMED_NO_TYRE_SERVICE
  INDETERMINATE_TYRE_SERVICE
```

This may use evidence first available after pit entry or after `T` because it is target truth, not prediction input.

### Positive tyre-service evidence

Tyre service is confirmed only when validated retrospective evidence establishes that one or more fitted race tyres were changed during that same visit.

Potential evidence includes:

- explicit validated tyre-set/fitting transition attributable to the visit;
- validated `TimingAppData` tyre update whose semantics and visit association prove a new/different fitted set;
- defensible pre-/post-visit tyre identity transition, including same-compound changes when set identity/equivalent evidence proves replacement;
- multiple independent source facts whose validated combination proves a tyre change.

Compound change can be strong positive evidence when attribution is reliable, but compound equality does not imply no tyre change.

### Evidence insufficient by itself

The following do not independently prove qualifying tyre service:

- `Stint` increment;
- pit-stop count increment;
- `PitInTime` or legacy `PitStatus=InLap`;
- pit-lane entry/exit;
- presence of an out-lap;
- lap-row compound without defensible before/after set attribution;
- tyre-life reset/decrease without validated set-transition semantics;
- absence of a `Compound` update;
- legacy same-row or shifted target labels.

### Negative tyre-service evidence

`CONFIRMED_NO_TYRE_SERVICE` requires evidence whose semantics establish that fitted tyres were retained through the visit, or another validated reconstruction that proves no tyre replacement occurred.

FastF1 `TyresNotChanged` is not accepted as sole negative authority at #19 design time because its source semantics are uncertain. Absence of positive tyre-change evidence is not proof of no change.

### Ambiguous qualification

When neither positive nor negative qualification can be proven, the visit remains `INDETERMINATE_TYRE_SERVICE`.

A resolver must not skip such a visit if it could lie inside the target-at-risk interval and precede the first known qualifying event or terminal boundary.

## Qualifying pit-event contract

A `QualifyingPitEventArtifact` exists only for a visit satisfying **both**:

1. `service_qualification = CONFIRMED_TYRE_SERVICE`; and
2. `race_participation_scope = IN_RACE_PARTICIPATION`.

```text
QualifyingPitEventArtifact
  artifact_id
  event_key
    pit_visit_key
    event_kind = TYRE_SERVICE_PIT_EVENT
  pit_visit_artifact_ref
  driver_entry_key
  pit_entry_occurrence
  race_participation_scope_ref
  terminal_boundary_ref
  tyre_service_evidence_refs
  event_reconstruction_policy_version
  source/provenance refs
  quality
```

A tyre-serviced visit that is proven pre-race/grid or at/after terminal participation is not a V2 qualifying event. A tyre-serviced visit whose race-participation membership is indeterminate does not become a qualifying event until membership is resolved; if it can affect an episode, that episode truncates rather than assuming inclusion/exclusion.

Event occurrence is the referenced visit's pit-entry occurrence; it is never shifted to pit-box arrival, tyre-service time, pit exit, or the first later record confirming tyre service.

## Causal eligibility and target-episode initialization

### Eligibility input boundary

Eligibility consumes only the immutable `CanonicalObservation` and target-definition configuration/version. It may not inspect future pit visits, future tyre-service evidence, eventual event identity, retrospective terminal result, target-resolution artifact, prediction result, or evaluation result.

### Eligibility states

Every canonical observation presented to the target subsystem produces an immutable decision:

```text
EligibilityStatus =
  ELIGIBLE
  INELIGIBLE
  INDETERMINATE
```

`ELIGIBLE` means the causal observation establishes that the approved next-pit question is meaningfully defined: the driver entry is identifiable, has not already reached a known terminal participation state at `T`, and remaining race progression exists in which a later relevant event could occur.

`INELIGIBLE` means the causal observation itself establishes that the target is no longer semantically defined, for example participation is already terminal or no future race progression remains.

`INDETERMINATE` means the observation is technically valid but causal state needed to establish eligibility is missing/ambiguous. It is never converted to a convenient negative.

A `VALID_WITH_OMISSIONS` #18 observation may still be eligible when omitted facts do not affect eligibility.

### Eligibility decision contract

```text
EligibilityDecision
  artifact_id
  observation_artifact_ref
  semantic_observation_key
  target_definition_version
  status
  causal_reason_codes
  causal_input_fact_refs
  target_initialization_policy_version
  provenance
```

No later outcome is backfilled into this artifact.

### Target episode identity

Exactly one `TargetEpisodeInitialization` is created for each `ELIGIBLE` observation. No ordinary episode is created for `INELIGIBLE` or `INDETERMINATE` decisions.

```text
TargetEpisodeInitialization
  artifact_id
  target_episode_key
    observation_artifact_ref
    target_definition_version
  observation_artifact_ref
  semantic_observation_key
  driver_entry_key
  prediction_boundary_ref
  eligibility_decision_ref
  target_definition_version
  initialization_policy_version
  provenance
```

The episode key is observation-owned, not event-owned. Successive eligible observations always create distinct episode identities even when they later resolve to the same qualifying event.

The initialization artifact contains no eventual event ID, terminal outcome, or truncation result.

## Retrospective target resolution

### Resolution inputs

A resolver consumes:

- one immutable `TargetEpisodeInitialization`;
- its exact observation/prediction-boundary references;
- the reconstructed pit-visit/event catalog for the same driver entry/session;
- the applicable retrospective terminal boundary and participation evidence;
- reconstruction coverage/support metadata;
- target-resolution policy/configuration/version.

It never mutates the observation, eligibility decision, or episode initialization.

### Target-at-risk interval

For resolution purposes, the semantic at-risk interval is:

```text
(T, B)
```

where `T` is the observation prediction boundary and `B` is the applicable terminal participation boundary. Both ends are open for event membership: a qualifying pit entry must be strictly after `T` and strictly before `B`.

If `B` cannot be reconstructed precisely enough to determine whether an otherwise target-relevant visit lies before terminal, the resolver does not assume that visit is in scope.

### Candidate traversal

For one episode, visits are evaluated in defensible occurrence order with both prediction and terminal relations:

1. `BEFORE_OR_AT_T` visits cannot be the episode's future target.
2. A visit with `INDETERMINATE_PREDICTION_RELATION` truncates if it could lie inside `(T, B)` and affect the earliest qualifying event.
3. A visit proven `AT_OR_AFTER_TERMINAL` is outside target scope and is excluded, regardless of tyre service.
4. A visit with `INDETERMINATE_TERMINAL_RELATION` or `INDETERMINATE_RACE_PARTICIPATION` truncates if it could lie inside `(T, B)` and affect target membership/identity.
5. Only a visit proven `STRICTLY_AFTER_T` **and** `STRICTLY_BEFORE_TERMINAL` / `IN_RACE_PARTICIPATION` is an in-scope future candidate.
6. For an in-scope future visit with `CONFIRMED_NO_TYRE_SERVICE`, continue following the episode.
7. For an in-scope future visit with `INDETERMINATE_TYRE_SERVICE`, truncate if that visit could precede the first known qualifying event or target closure.
8. For an in-scope future `QualifyingPitEventArtifact`, resolve `OBSERVED_EVENT` only if no earlier unresolved visit/order/scope ambiguity could also qualify.
9. Once a canonical in-scope observed event is fixed, later visits or later terminal-boundary gaps that cannot affect that earlier event identity do not invalidate it.

A later confirmed event cannot be selected by skipping an earlier unresolved in-scope or potentially in-scope visit.

### Ordering multiple candidate events

If two potentially qualifying in-scope entries have exact/comparable order, the earliest is canonical.

If occurrence bounds overlap or evidence cannot determine which qualifying visit occurred first, and choosing between them changes target event identity/timing, resolve `TRUNCATED_INDETERMINATE`. Do not sort by lap, source row, stint, or artifact ID.

## Terminal no-event and follow-up completeness

A known terminal state is not enough on its own. `TERMINAL_NO_EVENT` requires all of:

- a defensible applicable terminal boundary `B`;
- complete enough visit coverage over `(T, B)` to rule out hidden target-relevant pit entries;
- every reconstructed in-scope visit over `(T, B)` either confirmed no tyre service or otherwise proven irrelevant;
- no unresolved ordering/scope ambiguity that could hide or move a qualifying event into `(T, B)`.

If pit-entry coverage, tyre-service qualification coverage, race-scope membership, or ordering is insufficient in a way that could hide a relevant event, the episode is truncated/indeterminate instead.

Post-terminal movements do not prevent `TERMINAL_NO_EVENT`; they are outside the target interval. Uncertainty about whether a movement is pre- or post-terminal does prevent the no-event conclusion when that movement could qualify.

## Resolution states

A completed historical target-resolution artifact has exactly one of three mutually exclusive states:

```text
TargetResolutionState =
  OBSERVED_EVENT
  TERMINAL_NO_EVENT
  TRUNCATED_INDETERMINATE
```

### `OBSERVED_EVENT`

Required invariants:

- `qualifying_event_ref` is present;
- referenced event belongs to the same driver entry/session;
- referenced visit is `IN_RACE_PARTICIPATION`;
- pit-entry occurrence is demonstrably `STRICTLY_AFTER_T`;
- pit-entry occurrence is demonstrably `STRICTLY_BEFORE_TERMINAL` relative to the applicable boundary;
- applicable `terminal_boundary_ref` (or equivalent immutable participation-scope proof linked to that boundary) is retained;
- the event is demonstrably the earliest qualifying event inside `(T, B)`;
- no earlier unresolved visit/order/scope gap can change that conclusion;
- terminal-no-event fields are absent as the outcome.

An entry at, after, or ambiguously overlapping the terminal boundary cannot resolve `OBSERVED_EVENT`.

### `TERMINAL_NO_EVENT`

Required invariants:

- no qualifying event exists inside `(T, B)`;
- no unresolved visit/gap/scope ambiguity could hide one;
- a defensible terminal boundary reference is present;
- relevant pit-entry and tyre-service follow-up coverage is sufficient for the entire target-at-risk interval;
- `qualifying_event_ref` is absent.

This is known race-bounded truth, not a missing label.

### `TRUNCATED_INDETERMINATE`

Used when evidence is insufficient to establish either canonical outcome. Reasons include:

- ambiguous pit-entry relation to `T`;
- ambiguous pit-entry relation to the terminal boundary;
- indeterminate race-participation membership for a potentially target-relevant visit;
- unresolved ordering between potentially qualifying visits;
- indeterminate tyre-service qualification for a visit that could be target-relevant;
- source gap that could hide a pit visit;
- missing terminal evidence;
- imprecise terminal time whose overlap with a visit could change target membership;
- incomplete source coverage before closure.

It carries explicit reason and affected-coverage metadata and is never silently mapped to no-event or observed event.

### Open versus completed historical resolution

`OPEN` is a lifecycle state before retrospective follow-up is complete; it is not one of the three completed historical outcomes. A historical run that claims completed follow-up maps unresolved evidence to `TRUNCATED_INDETERMINATE`, not indefinitely open and not no-event.

## Coverage model

Target reconstruction records capability-sensitive coverage over the relevant interval:

```text
TargetEvidenceCoverage
  pit_entry_coverage
  visit_segmentation_coverage
  race_participation_scope_coverage
  tyre_service_positive_coverage
  tyre_service_negative_coverage
  terminal_coverage
  known_gaps[]
  support_validation_refs[]
```

A source gap after an already-observed canonical event does not invalidate that episode if it cannot alter the earlier event identity or prove that the event was outside participation. A gap before closure that could hide an earlier qualifying event, change race-scope membership, or move the terminal boundary does.

Lack of validated negative-service evidence matters when a no-service classification is required to skip a visit; it does not automatically invalidate a clearly tyre-serviced, in-scope event whose earliest ordering is otherwise proven.

## Target-resolution artifact and version lineage

```text
TargetResolutionArtifact
  artifact_id
  target_episode_initialization_ref
  target_episode_key
  resolution_run_ref
  observation_artifact_ref
  driver_entry_key
  prediction_boundary_ref
  resolution_state
  qualifying_event_ref?          # OBSERVED_EVENT only
  terminal_boundary_ref?         # required whenever used to prove scope/closure
  truncation_reasons[]            # TRUNCATED_INDETERMINATE
  evidence_coverage
  source_manifest_refs
  event_reconstruction_policy_version
  tyre_service_policy_version
  terminal_policy_version
  target_resolution_policy_version
  repository_revision
  supersedes_resolution_ref?
  provenance
```

A resolution artifact is immutable for one declared source/configuration/policy/run. Improved evidence or reconstruction creates a new artifact/version; it does not mutate a result already consumed by a replay/backtest run.

### Resolution cardinality

Global lineage is intentionally **one episode to many immutable resolution versions over time**:

```text
TargetEpisodeInitialization 1 -> 0..many TargetResolutionArtifact versions
```

For any one declared `resolution_run_ref` / source snapshot / configuration / policy version, there is **exactly one selected `TargetResolutionArtifact` per initialized episode**. A dataset or replay/backtest run must reference that exact resolution artifact (and its `resolution_run_ref`), not merely the episode key.

A later resolution may carry `supersedes_resolution_ref` for audit lineage. Earlier artifacts remain valid historical records for the runs that consumed them.

## Canonical dataset / consumer contract

The target subsystem exposes distinct artifacts rather than one hindsight-mutated row.

### Causal forecast-time side

Prediction/replay may consume:

- exact `CanonicalObservation`;
- `EligibilityDecision`;
- when eligible, `TargetEpisodeInitialization`.

They may not consume target resolution to generate the forecast being evaluated.

### Retrospective development/evaluation side

Controlled development/evaluation assembly may join:

- `TargetEpisodeInitialization`;
- one explicitly selected immutable `TargetResolutionArtifact` for the declared resolution run;
- referenced `QualifyingPitEventArtifact` or terminal/truncation metadata;
- exact observation identity/provenance.

```text
TargetEpisodeDatasetRecord
  target_episode_key
  target_resolution_artifact_ref
  resolution_run_ref
  observation_artifact_ref
  semantic_observation_key
  driver_entry_key
  prediction_boundary_ref
  resolution_state
  event_ref? / event_entry_occurrence?
  terminal_boundary_ref?
  truncation_reasons[]
  evidence_coverage
  reconstruction_version_refs
```

Physical columns/types/file format are implementation choices. Observed-event, terminal-no-event, and truncation remain explicit non-overlapping states, and causal initialization is never rewritten with future truth.

## Identity relationships

```text
CanonicalObservation
  1 -> 1 EligibilityDecision
  1 -> 0..1 TargetEpisodeInitialization

DriverEntry
  1 -> many PitVisitArtifact

PitVisitArtifact
  1 -> 0..1 QualifyingPitEventArtifact

TargetEpisodeInitialization
  1 -> 0..many immutable TargetResolutionArtifact versions globally
  1 -> exactly 1 selected TargetResolutionArtifact per declared resolution run

TargetResolutionArtifact (OBSERVED_EVENT)
  many episodes may -> same QualifyingPitEventArtifact
```

This preserves repeated-forecast semantics and immutable re-resolution lineage. Two observations at `T1` and `T2` may create separate episodes that both resolve to the same later in-scope tyre-service event when no qualifying event occurred between them.

## Ambiguity and conservative handling

Target reconstruction never makes convenience assumptions to increase label coverage.

| Ambiguity | Required outcome |
| --- | --- |
| Pit entry relation to `T` overlaps/equal/unknown | Truncate if visit could lie inside `(T, B)` and be target-relevant |
| Pit entry relation to terminal boundary overlaps/unknown | Truncate if visit could lie inside `(T, B)` and be target-relevant |
| Visit proven at/after terminal | Exclude from V2 target scope, regardless of tyre service |
| Pre-race/grid or post-terminal traversal | Keep only as audit evidence; not a qualifying V2 event |
| Two potential in-scope qualifying entries cannot be ordered | `TRUNCATED_INDETERMINATE` if ordering changes target identity |
| Visit known, tyre service cannot be confirmed or ruled out | `INDETERMINATE_TYRE_SERVICE`; truncate if potentially in-scope and target-relevant |
| Stint changed but no tyre-change proof | Do not infer tyre service |
| No compound update | Do not infer no service |
| `TyresNotChanged` semantics unverified | Do not use as sole negative proof |
| Processed `PitInTime` conflicts materially with validated raw entry evidence | Reconstruction conflict; never choose whichever gives convenient ordering |
| Source gap may hide visit before event/terminal | `TRUNCATED_INDETERMINATE` |
| Final status proves retirement but terminal instant overlaps a candidate visit | `TRUNCATED_INDETERMINATE` unless other evidence resolves ordering |
| Legacy `PitStatus` disagrees with canonical evidence | Legacy value is QA only; canonical reconstruction follows validated target sources |

## Provenance and versioning

Every event/target artifact is traceable, as applicable, to:

- exact repository revision;
- approved target semantic version / decision references;
- exact observation artifact and prediction-boundary reference;
- frozen target-truth source manifest/content identities;
- provider/parser/adapter revision;
- target-reconstruction support validation IDs;
- pit-visit segmentation policy/version;
- pit-entry occurrence reconstruction method/version;
- race-participation/terminal reconstruction policy/version;
- tyre-service qualification policy/version;
- target eligibility/initialization policy/version;
- target resolution policy/version;
- exact source/evidence lineage for material claims;
- resolution run identity and supersession lineage when applicable.

A later correction to source evidence, provider behavior, or reconstruction policy creates new artifacts/run lineage. Existing artifacts used by a declared run are never overwritten.

## Verification handoff

The verification baseline after the design integration gate must establish a target-reconstruction support matrix and representative fixtures. At minimum it must cover:

1. raw `TimingData` `InPit=True/False` behavior for normal race pit visits;
2. pre-race/grid pit-lane movements and first-lap edge handling;
3. **post-finish/post-retirement pit/garage movements proving they are outside race-participation scope**;
4. duplicate, missing, malformed, correction, and reset transition cases;
5. multiple distinct pit visits within one official lap when present or a synthetic fixture proving identity behavior;
6. comparison of canonical raw-entry reconstruction with FastF1 `PitInTime`/`PitOutTime` and documented discrepancy bounds;
7. `TimingAppData` tyre/stint update behavior around confirmed tyre changes;
8. same-compound tyre changes so compound equality cannot become a false negative;
9. drive-through/pass-through, penalty-only, repair-only, and other known no-tyre-service visits where truth can establish them;
10. independent validation or rejection of `TyresNotChanged` semantics by endpoint/era;
11. proof that stint increment alone is not used as tyre-service qualification;
12. missing/sparse tyre evidence producing `INDETERMINATE_TYRE_SERVICE` rather than guessed labels;
13. event-entry relation to exact/bounded prediction boundaries, including equality and overlap;
14. **event-entry relation to exact/bounded terminal boundaries: strictly before, equal/after, and overlapping intervals**;
15. **observed-event fixtures proving the selected event is inside `(T, B)` and never post-terminal**;
16. ordering of multiple potentially qualifying in-scope visits and conservative handling of overlapping occurrence bounds;
17. finish and retirement terminal boundaries across representative sessions;
18. source gaps that can hide visits causing truncation, while irrelevant post-closure gaps do not invalidate earlier proven events;
19. terminal-no-event cases proving complete pit/service/race-scope follow-up rather than relying on final status alone;
20. successive target episodes resolving to the same eventual event while retaining distinct episode IDs;
21. multiple immutable resolution versions for one episode with exactly one selected resolution per declared run;
22. deterministic reconstruction/provenance from identical frozen sources/configuration.

Verification may establish support only for a subset of seasons/source eras. Unsupported historical scopes remain explicitly truncated/indeterminate rather than backfilled from legacy labels.

## Decisions intentionally deferred

| Question | Owner |
| --- | --- |
| Exact source/endpoint/season support matrix and empirical reliability/tolerances | Verification baseline after #22 |
| Exact physical schemas, file formats, hashing, package classes, parser code, CLI commands | Implementation |
| Exact probability timing-region representation and mapping of resolved in-scope event occurrence into it | #20 — prediction distribution/model-facing contract |
| Replay ordering, temporal development/final-evaluation mechanics, resolution-version selection/accounting | #21 — replay/backtest contract |
| Final metrics, censoring/truncation statistical treatment, weighting/dependence estimators | Verification/statistical phase |
| Model features, model family, calibration, hyperparameters | Model verification/experimentation |
| Live target capture/runtime behavior | Future bounded live design |

## Acceptance mapping

- **Concrete source evidence:** raw `TimingData`, `PitInTime`/`PitOutTime`, `TimingAppData`, processed tyre fields, session/results/race-control evidence, and legacy limitations are inventoried with explicit authority limits.
- **Technical visit/event identities:** visit identity is entry-evidence based rather than lap based; same-lap visits remain distinct; qualifying event identity remains separate.
- **Tyre-service qualification:** three-state service qualification prevents stint/compound/absence convenience assumptions from substituting for the approved event definition.
- **Pit-entry occurrence:** event occurrence is exact/bounded pit entry and remains the ordering anchor even when service is confirmed later.
- **Race-participation scope:** pre-race and post-terminal movements are excluded; observed events must be defensibly inside the open interval `(T, B)`; terminal/event overlap fails closed.
- **Eligibility and episode creation:** eligibility consumes only the causal canonical observation; every eligible observation creates its own immutable episode without future-event-dependent eligibility.
- **Resolution states:** observed event, terminal no-event, and truncation are explicit, non-overlapping, terminal-aware, and coverage-aware.
- **Identity separation/versioning:** observation, target episode, pit visit, event, and resolution-version identities are distinct; one episode can have multiple immutable resolution versions globally but exactly one selected result per declared run.
- **Ambiguity handling:** unresolved service, entry ordering, race-scope/terminal ordering, visit segmentation, source gaps, and terminal uncertainty fail closed when they can change target truth.
- **Consumer contract:** #20/#21 receive one canonical target initialization/resolution contract without redefining target semantics.
- **Scope discipline:** no probability output representation, model, metric/statistical method, live runtime, or production implementation is selected.

## Product Owner decisions

None required. Tyre-service-only qualification, pit-lane-entry occurrence, and target race-participation semantics are already approved. The reconstruction, terminal-scope, identity, conservative ambiguity, and provenance rules here are delegated technical choices implementing those locks.

## Review record

### Full scoped review — FAIL, rework required

- PR: #25
- Review: `PRR_kwDOJBBaD88AAAABNAfFXg`
- Date: 2026-09-10
- Outcome: **FAIL — rework required**
- Blocking finding: `OBSERVED_EVENT` was not constrained to occur before the applicable terminal boundary / within the remaining race-participation scope.
- Minor finding: resolution cardinality was ambiguous under immutable re-resolution/versioning.
- Product Owner decision: none required.

### Rework

The design now:

1. makes race-participation membership and visit-to-terminal ordering explicit;
2. defines the semantic target-at-risk interval as open interval `(T, B)`;
3. excludes proven at/post-terminal visits and events from V2 target scope;
4. requires `OBSERVED_EVENT` to be strictly after `T` and strictly before the terminal boundary;
5. maps overlapping/indeterminate event-versus-terminal ordering to `TRUNCATED_INDETERMINATE` when target membership can change;
6. adds terminal/race-scope handling to candidate traversal, event creation, ambiguity rules, coverage, and verification fixtures;
7. clarifies resolution lineage as one episode to many immutable resolution versions globally, with exactly one selected resolution per declared resolution run.

### Bounded re-review

Required under `governance/REVIEW_POLICY.md`. It should verify the prior Blocking and Minor findings, regressions introduced by this rework, and the original #19 acceptance criteria. It is not a fresh unlimited review.
