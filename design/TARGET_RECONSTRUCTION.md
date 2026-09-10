# V2 Pit-Event Reconstruction and Target-Episode Dataset Contract

## Status

Draft — Issue #19, branch `design/target-reconstruction`. Independent scoped review required before approval.

## Abstraction level

Detailed data/target design — retrospective pit-visit/event reconstruction, tyre-service qualification, target eligibility materialization, target-episode identity, target resolution states, terminal/truncation handling, and provenance.

This artifact does not redefine point-in-time observation legitimacy, prediction probability representation, model formulation, evaluation metrics/statistics, live inference, or production implementation.

## Issue / branch

- Issue: #19 — `Design — pit-event reconstruction and target-episode dataset contract`
- Parent: #16
- Upstream architecture: #17 / `design/SYSTEM_ARCHITECTURE.md`
- Upstream observation design: #18 / `design/OBSERVATION_RECONSTRUCTION.md`
- Branch: `design/target-reconstruction`

## Outcome

The V2 target subsystem has two technically separate boundaries with different causal permissions:

1. **Causal target eligibility / episode initialization** consumes one immutable `CanonicalObservation` and no future event truth. It decides whether the next-pit question is defined and, when eligible, creates one immutable target-episode identity.
2. **Retrospective event reconstruction / target resolution** may use later race evidence to reconstruct pit visits, determine whether tyre service occurred, establish pit-entry occurrence, establish terminal follow-up, and resolve the already-created episode.

A pit-lane visit and a relevant V2 pit event are not the same object. Every reconstructed visit is retained as a visit candidate. It becomes a relevant V2 event only when tyre service is defensibly confirmed. The event occurrence remains the pit-lane entry of that same visit.

The target for an eligible observation at prediction instant `T` is the earliest qualifying pit-entry occurrence that can be demonstrated to be strictly after `T`. If an unresolved visit or ordering ambiguity could change which event is earliest, the episode is `TRUNCATED_INDETERMINATE`; reconstruction never guesses past the ambiguity.

## Upstream locks consumed unchanged

This design consumes and does not redefine:

- `contexts/PIT_EVENT_TARGET.md` — tyre-service-only event meaning, pit-lane-entry occurrence anchor, strict-after-`T` ordering, eligibility, target lifecycle, terminal no-event, and truncation semantics;
- `decisions/2026-09-08-v2-pit-event-scope.md` — Product Owner-approved tyre-service-only scope and pit-entry occurrence anchor;
- `contexts/RACE_OBSERVATION_STATE.md` — canonical observation identity and prediction instant / point-in-time information boundary;
- `design/OBSERVATION_RECONSTRUCTION.md` — exact immutable observation artifact, race/session/driver/checkpoint identities, verified prediction boundary, and observation quality/provenance;
- `design/SYSTEM_ARCHITECTURE.md` — target ownership is split between causal episode initialization and retrospective target resolution; replay/prediction may consume the causal boundary but not retrospective target truth;
- `contexts/WAVE1_SEMANTIC_INTEGRATION.md` — event identity and target episode identity remain distinct, and future target truth cannot flow backward into observations or predictions.

A material change to tyre-service-only qualification or the pit-lane-entry occurrence anchor requires a new Product Owner decision. This design makes those approved semantics technically reconstructable; it does not revisit them.

## Evidence roles: prediction availability versus retrospective truth

The availability-authority rules in #18 govern whether information may appear in the historical prediction-time observation. They do **not** imply that the same source is unusable as retrospective target evidence after the race.

Target reconstruction therefore has a separate evidence question:

> Is the frozen historical evidence sufficiently complete and reliable to establish the actual pit visit, tyre-service qualification, event occurrence, and terminal follow-up needed to resolve this target episode?

A static archive may be `UNVERIFIED_ARCHIVE` for historical prediction-time availability yet still contribute retrospective event truth if its target-reconstruction behavior is independently validated for the claimed endpoint/era. Conversely, a source that is suitable for an observation boundary is not automatically sufficient to prove tyre service or terminal no-event.

The two validations must not be conflated.

## Concrete source evidence inventory

FastF1 implementation/documentation evidence below was inspected at upstream commit `227cf301fb4bcf1705bcb1866de1fe5dbcef6071` (2026-08-28). This is evidence, not a package-version commitment.

| Evidence | Observed behavior | V2 target use | Limitation / required validation |
| --- | --- | --- | --- |
| Raw `TimingData` driver updates | FastF1 parser documents `InPit=True` as received once on pit entry and `InPit=False` once on pit exit | Primary candidate evidence for pit-visit segmentation and pit-entry occurrence | Archive completeness, duplicate/correction behavior, grid/pre-race movements, and same-lap multiple visits require verification |
| FastF1 `PitInTime` / `PitOutTime` | Parsed/calculated lap fields representing pit entry/exit session times | Cross-check / fallback candidate only under a validated reconstruction rule | FastF1 may correct/postprocess lap timing; docs state calculated timestamps cannot be verified to millisecond precision |
| Raw `TimingAppData` `Stints` | Contains stint index plus sparse `Compound`, `New`, `TotalLaps`, `StartLaps`, `TyresNotChanged`, etc. | Candidate retrospective tyre-state evidence around visits | Sparse/delta-like; exact field meanings/latency vary; `TyresNotChanged` is explicitly uncertain in FastF1 source |
| Processed lap tyre fields | `Compound`, `TyreLife`, `FreshTyre`, `Stint` available in `Session.laps` | Retrospective cross-check and normalized tyre-state evidence when lineage/reliability is established | Processed data can be corrected/filled; cannot alone prove every same-compound change or no-change visit |
| FastF1 stint construction | FastF1 source notes each drive through pit lane starts a new stint independent of tyres being changed | Important negative constraint | **Stint change alone is not proof of tyre service** |
| Session results | Driver result includes classification, status, completed laps, etc. | Candidate evidence for final participation outcome | Final classification can show terminal outcome but may not identify exact retirement instant |
| Session status | Session lifecycle includes started/finished/finalized transitions | Candidate race-terminal evidence | Session terminal time and driver-specific terminal time remain distinct |
| Race-control messages | Can include driver/session event messages | Corroborative terminal/incident evidence | Message absence is not proof of continued/ended participation |
| Legacy CSV `PitStatus` | Derived from `PitInTime`/`PitOutTime`; one lap row with tyre/stint fields | Historical comparison / QA only | Does not retain raw visit identity, raw order, correction history, or reliable multiple-same-lap visit distinction |

### Key provider findings

FastF1's current timing parser explicitly handles raw `InPit` state changes as pit-entry and pit-exit transitions and derives `PitInTime`/`PitOutTime` from those updates. It also performs corrections around grid laps, late data, lap alignment, and missing/edge laps. Therefore processed lap fields are not treated as the sole technical identity of a pit visit.

FastF1's `TimingAppData` exposes tyre/stint records, but its own source labels `TyresNotChanged` as uncertain (`??? Probably a flag...`). The field is therefore not accepted as sole service/no-service authority without a separate verification result.

FastF1 also notes that its source considers each passage through the pit lane the beginning of a new stint independent of whether tyres were changed. Consequently, `Stint` transition is useful for correlating a visit but is not itself a qualifying tyre-service signal.

## Target-truth source snapshot and support contract

### Frozen retrospective evidence

Every target reconstruction run consumes frozen, identifiable source snapshots. The target subsystem may consume the same raw bytes as observation reconstruction or additional retrospective sources, but it records them under its own reconstruction provenance and support rules.

A logical `TargetTruthSourceManifest` records at least:

- `RaceSessionKey`;
- source/provider family and acquisition mode;
- endpoint/source names used for pit-entry, tyre-service, and terminal evidence;
- exact frozen content identities/hashes;
- retrieval/capture date;
- parser/adapter revision;
- completeness/gap indicators;
- target-reconstruction support validation references by endpoint/era;
- repository revision and reconstruction run ID.

Freezing makes the target reconstruction reproducible. It does not, by itself, prove source completeness or semantic reliability.

### Target reconstruction support validation

The verification phase must maintain a scoped support record for evidence used to make event-truth claims:

```text
TargetReconstructionSupportScope = (
    source/provider family,
    acquisition mode,
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
- terminal participation reconstruction;
- complete interval coverage for no-event claims.

A source may support one capability without supporting another. No single global `SUPPORTED` flag is sufficient.

## Reconstructed pit-visit contract

### Pit visit is distinct from qualifying event

A `PitVisit` is one reconstructed traversal/occupancy episode of the race pit lane for one `DriverEntryKey`. It exists independently of whether tyre service occurred.

Its logical contract is:

```text
PitVisitArtifact
  artifact_id
  pit_visit_key
    race_session_key
    driver_entry_key
    visit_discriminator
  pit_entry_occurrence
  pit_exit_occurrence? 
  visit_segmentation_quality
  source_lineage
  reconstruction_policy_version
  target_truth_support_refs
  service_qualification
  quality / reason_codes
```

`pit_exit_occurrence` may be absent when an entry is otherwise defensibly reconstructed but the driver never exits or exit evidence is missing. Exit is not the event occurrence anchor.

### Pit visit identity

A pit visit is never keyed solely by lap number, stint number, `NumberOfPitStops`, or dataframe row.

The canonical semantic visit key is based on driver entry plus one distinct reconstructed pit-entry occurrence/evidence identity:

```text
PitVisitKey = (
    DriverEntryKey,
    visit_discriminator
)
```

`visit_discriminator` must deterministically identify the distinct entry transition within the frozen reconstruction evidence, for example a canonical source-lineage identity derived from the accepted entry evidence. Exact serialization belongs to implementation.

The important invariants are:

- two distinct entry transitions produce distinct visit keys even if they occur on the same official lap;
- duplicate representations of the same transition do not create duplicate visits once equivalence is defensibly established;
- a lap or stint label is descriptive metadata only;
- a revised source/reconstruction run may create a new artifact identity for the same semantic visit without overwriting prior artifacts.

### Visit state-machine reconstruction

For a source validated to represent driver pit-lane state transitions, reconstruction is conceptually:

```text
OUTSIDE_PIT --entry evidence--> IN_PIT
IN_PIT     --exit evidence----> OUTSIDE_PIT
```

Rules:

1. A verified/canonical entry transition starts one candidate visit.
2. A canonical exit transition closes that visit but does not determine whether it qualifies as a V2 event.
3. Duplicate identical-state updates are ignored only when the source contract or source-lineage equivalence demonstrates duplication; otherwise unexpected transition sequences are surfaced as ambiguity.
4. Entry while already `IN_PIT`, or exit while `OUTSIDE_PIT`, is a segmentation anomaly unless an explicit source reset/correction rule explains it.
5. A visit may remain exit-open at the end of participation; this does not erase a defensible pit entry.
6. Pre-race/grid pit movements are excluded from race-visit scope using race/session participation boundaries, not by assuming the first parsed `PitInTime` is a race stop.
7. Same-lap entries remain separate visits when transition evidence distinguishes them.
8. If a source gap can hide an additional entry/exit and thereby change visit identity/order, affected visit coverage is indeterminate.

Exact parser logic and endpoint-specific reset behavior are implementation/verification responsibilities; these invariants are the design contract.

## Pit-entry occurrence representation

The relevant event occurrence is the pit-lane entry of the qualifying visit.

Because historical evidence may have finite precision, occurrence is represented as an exact instant or conservative interval/bounds rather than forcing false precision:

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

A processed FastF1 `PitInTime` may contribute to the occurrence reconstruction under a validated method, but the event is not defined by the provider field itself.

### Relation to observation prediction instant

The target resolver consumes the exact prediction boundary from the immutable #18 observation artifact. It does not recalculate or reinterpret `T`.

The relation between candidate entry `E` and prediction instant `T` is classified conservatively:

- `BEFORE_OR_AT_T` — evidence proves `E <= T`; the visit cannot be this episode's future event.
- `STRICTLY_AFTER_T` — evidence proves `E > T`; the visit is a future candidate.
- `INDETERMINATE_RELATION` — bounds/clock evidence do not prove either relation.

When exact times share a validated comparable clock, ordinary numeric ordering applies. For bounded/coarse evidence, `E.lower_bound > T.upper_bound` can prove strictly-after and `E.upper_bound <= T.lower_bound` can prove before-or-at. Overlap is indeterminate.

Equality is never promoted to `STRICTLY_AFTER_T`.

## Tyre-service qualification

### Three-state qualification

Each reconstructed visit receives exactly one service qualification state:

- `CONFIRMED_TYRE_SERVICE`
- `CONFIRMED_NO_TYRE_SERVICE`
- `INDETERMINATE_TYRE_SERVICE`

This state is retrospective. It may use evidence first available after pit entry or after the observation's `T` because it is target truth, not prediction input.

### Positive tyre-service evidence

Tyre service is confirmed only when validated retrospective evidence establishes that one or more fitted race tyres were changed during that visit.

Potential evidence families include:

- an explicit validated tyre-set/fitting transition attributable to the visit;
- a validated `TimingAppData` tyre update whose semantics and visit association prove a new/different fitted set;
- a defensible pre-visit/post-visit tyre identity transition, including same-compound changes when set identity or equivalent evidence proves replacement;
- multiple independent source facts whose validated combination proves a tyre change.

A change of compound can be strong positive evidence when the before/after attribution is reliable, but compound equality does **not** imply no tyre change because a driver may fit another set of the same compound.

### Evidence that is insufficient by itself

The following do not independently prove qualifying tyre service:

- `Stint` increment;
- pit-stop count increment;
- `PitInTime` or `PitStatus=InLap`;
- pit-lane entry/exit;
- presence of an out-lap;
- a lap-row compound value with no defensible before/after set attribution;
- tyre-life reset/decrease without validated set-transition semantics;
- absence of a `Compound` update;
- legacy same-row or shifted target labels.

In particular, FastF1's source explicitly documents that every drive through pit lane can begin a new stint independent of tyre changes.

### Negative tyre-service evidence

`CONFIRMED_NO_TYRE_SERVICE` requires evidence whose semantics explicitly establish that fitted tyres were retained through the visit, or another validated reconstruction that proves no tyre replacement occurred.

Examples may include:

- a source field with independently validated no-change semantics tied to that visit;
- continuous tyre-set identity across entry/service/exit under a source contract strong enough to prove retention;
- another verified event record explicitly classifying the visit as no tyre service.

At #19 design time, FastF1 `TyresNotChanged` is **not** accepted as sole negative authority because FastF1's current source describes its meaning as uncertain. Verification may later validate it for a scoped era/source or reject it.

Absence of positive tyre-change evidence is not proof of no change.

### Ambiguous qualification

When neither positive nor negative qualification can be proven, the visit remains `INDETERMINATE_TYRE_SERVICE`.

Target resolution must not skip such a visit if it could be the earliest qualifying event after `T`.

## Qualifying pit-event contract

A `QualifyingPitEventArtifact` exists only for a visit with `CONFIRMED_TYRE_SERVICE`.

```text
QualifyingPitEventArtifact
  artifact_id
  event_key
    pit_visit_key
    event_kind = TYRE_SERVICE_PIT_EVENT
  pit_visit_artifact_ref
  driver_entry_key
  pit_entry_occurrence
  tyre_service_evidence_refs
  event_reconstruction_policy_version
  source/provenance refs
  quality
```

The event key and visit key remain distinct concepts even though the event is one-to-one with a qualifying visit under the V2 event definition.

The event occurrence is copied/referenced from that visit's pit-entry occurrence; it is never shifted to pit-box arrival, tyre-service time, pit exit, or the first later record that confirms tyre service.

## Causal eligibility and target-episode initialization

### Eligibility input boundary

Eligibility consumes only the immutable `CanonicalObservation` and target-definition configuration/version. It may not inspect:

- future pit visits;
- future tyre-service evidence;
- eventual qualifying event identity;
- retrospective terminal result;
- target-resolution artifact;
- prediction/evaluation result.

This preserves the causal target-owned boundary established by #17.

### Eligibility states

Every canonical observation presented to the target subsystem produces an immutable `EligibilityDecision`:

```text
EligibilityStatus =
  ELIGIBLE
  INELIGIBLE
  INDETERMINATE
```

`ELIGIBLE` means the approved semantic next-pit question is meaningfully defined from the causal observation state: the driver entry is identifiable, has not already reached a known terminal participation state at `T`, and the observation state establishes remaining race progression in which a later relevant event could occur.

`INELIGIBLE` means the causal observation itself establishes that the target question is no longer semantically defined, for example the driver's race participation is already terminal or no future race progression remains for that entry.

`INDETERMINATE` means the observation is a valid technical observation artifact but omits/contains ambiguous causal state necessary to establish eligibility. It is not converted to a convenient negative.

An observation marked `VALID_WITH_OMISSIONS` by #18 may still be `ELIGIBLE` when the omissions do not affect the required eligibility facts.

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

The episode key is observation-owned, not event-owned. Successive eligible observations always create distinct episode identities even when they later resolve to the same qualifying pit event.

The initialization artifact contains no eventual event ID, terminal outcome, or truncation result. Those belong only to the separate resolution artifact.

## Retrospective target resolution

### Resolution inputs

A resolver consumes:

- one immutable `TargetEpisodeInitialization`;
- its exact immutable observation/prediction-boundary references;
- the reconstructed pit-visit/event catalog for the same driver entry/session;
- retrospective participation/terminal evidence;
- reconstruction coverage/support metadata;
- target-resolution policy/configuration/version.

It never mutates the observation, eligibility decision, or episode initialization.

### Candidate traversal

For one episode at `T`, candidate visits are considered in defensible pit-entry occurrence order.

For each visit that could affect the target:

1. If entry is proven `BEFORE_OR_AT_T`, it is not a future candidate for this episode.
2. If relation to `T` is `INDETERMINATE_RELATION` and the visit might be after `T`, resolution becomes `TRUNCATED_INDETERMINATE` unless later evidence proves the visit cannot affect the earliest qualifying event.
3. For a `STRICTLY_AFTER_T` visit with `CONFIRMED_NO_TYRE_SERVICE`, continue following the episode.
4. For a `STRICTLY_AFTER_T` visit with `CONFIRMED_TYRE_SERVICE`, it resolves the episode as `OBSERVED_EVENT` only if no earlier unresolved visit/order ambiguity could also qualify.
5. For a `STRICTLY_AFTER_T` visit with `INDETERMINATE_TYRE_SERVICE`, resolution becomes `TRUNCATED_INDETERMINATE` if that visit could precede the first known qualifying event or the terminal boundary.

A later confirmed event cannot be selected by simply skipping an earlier unresolved visit.

### Ordering multiple candidate events

If two potentially qualifying entries have exact/comparable occurrence order, the earliest strictly-after-`T` event is canonical.

If occurrence bounds overlap or the evidence cannot determine which qualifying visit happened first, and choosing between them would change the target event identity/timing, the episode is `TRUNCATED_INDETERMINATE` with an ordering reason rather than arbitrarily sorted by lap, source row, or artifact ID.

## Terminal participation and race boundary

### Terminal boundary object

Retrospective target resolution may close an episode as terminal no-event only when a defensible terminal boundary exists:

```text
TerminalBoundary
  terminal_kind
    DRIVER_PARTICIPATION_TERMINAL
    RACE_SESSION_TERMINAL
  driver_entry_key
  occurrence_time_or_bounds
  evidence_refs
  terminal_reconstruction_method_version
  quality
```

The applicable boundary is the earliest defensible boundary after which the selected entry cannot produce another V2 race pit event within the same participation.

### Evidence roles

Potential terminal evidence includes:

- official/final driver result status/classification and completed-lap evidence;
- race/session finished/finalized status;
- timing/race-control evidence that establishes a definitive retirement/withdrawal or final participation point;
- other independently validated final participation evidence.

Final results are legitimate retrospective target evidence, but a final `Status` string alone may establish that participation ended without proving the exact terminal instant. Exact time is required only when its uncertainty could change whether a candidate pit entry lies before or after the terminal boundary.

Processed/synthetic laps inserted by FastF1 for a retired driver are not sole authority for the retirement instant.

### Terminal no-event requires complete relevant follow-up

A known terminal state is not enough on its own. `TERMINAL_NO_EVENT` requires that target reconstruction can also establish there was no unresolved qualifying visit between `T` and the terminal boundary.

If pit-entry coverage, tyre-service qualification coverage, or event ordering is insufficient in a way that could hide a relevant event, the episode is truncated/indeterminate instead.

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
- pit-entry occurrence is demonstrably strictly after `T`;
- it is demonstrably the earliest qualifying event after `T`;
- no earlier unresolved visit/order gap can change that conclusion;
- terminal-no-event fields are absent as the outcome.

### `TERMINAL_NO_EVENT`

Required invariants:

- no qualifying event after `T` and before the applicable terminal boundary is present;
- no unresolved visit/gap could hide such an event;
- a defensible terminal boundary reference is present;
- relevant pit-entry and tyre-service follow-up coverage is sufficient for the entire target-at-risk interval;
- `qualifying_event_ref` is absent.

This is known race-bounded truth, not a missing label.

### `TRUNCATED_INDETERMINATE`

Used when evidence is insufficient to establish either canonical outcome. Reasons include, but are not limited to:

- ambiguous pit-entry relation to `T`;
- unresolved ordering between potentially qualifying visits;
- indeterminate tyre-service qualification for a visit that could be target-relevant;
- a source gap that could hide a pit visit;
- missing terminal evidence;
- ambiguous driver terminal time that could change target membership;
- incomplete source coverage before closure.

It must carry explicit reason and affected-coverage metadata. It is never silently mapped to `TERMINAL_NO_EVENT` or an observed event.

### Open versus completed historical resolution

`OPEN` is a lifecycle state of the causal episode before retrospective follow-up is complete; it is not one of the three completed historical target outcomes above. When a historical reconstruction run claims completed follow-up, an episode that cannot be resolved becomes `TRUNCATED_INDETERMINATE`, not indefinitely open and not no-event.

## Coverage model

Target reconstruction records whether the evidence is sufficiently complete over the episode's relevant interval.

Logical coverage dimensions include:

```text
TargetEvidenceCoverage
  pit_entry_coverage
  visit_segmentation_coverage
  tyre_service_positive_coverage
  tyre_service_negative_coverage
  terminal_coverage
  known_gaps[]
  support_validation_refs[]
```

Coverage is interval- and capability-sensitive. A source gap after an already-observed canonical event does not invalidate that episode if it cannot affect the earlier event identity. A gap before closure that could hide an earlier qualifying event does.

Likewise, lack of validated negative-service evidence matters when a no-service classification is required to skip a visit; it does not automatically invalidate a clearly tyre-serviced event whose earliest ordering is otherwise proven.

## Target-resolution artifact

```text
TargetResolutionArtifact
  artifact_id
  target_episode_initialization_ref
  target_episode_key
  observation_artifact_ref
  driver_entry_key
  prediction_boundary_ref
  resolution_state
  qualifying_event_ref?          # OBSERVED_EVENT only
  terminal_boundary_ref?         # TERMINAL_NO_EVENT when applicable
  truncation_reasons[]            # TRUNCATED_INDETERMINATE
  evidence_coverage
  source_manifest_refs
  event_reconstruction_policy_version
  tyre_service_policy_version
  terminal_policy_version
  target_resolution_policy_version
  repository_revision
  provenance
```

This artifact is immutable for a declared source/configuration/version. Improved evidence or reconstruction produces a new resolution artifact/version and does not mutate a result already consumed by a replay/backtest run.

## Canonical dataset / consumer contract

The target subsystem exposes distinct artifacts rather than one hindsight-mutated row.

### Causal forecast-time side

Prediction/replay may consume:

- exact `CanonicalObservation`;
- `EligibilityDecision`;
- when eligible, `TargetEpisodeInitialization`.

They may not consume `TargetResolutionArtifact` to generate the forecast being evaluated.

### Retrospective development/evaluation side

Controlled development/evaluation assembly may join:

- `TargetEpisodeInitialization`;
- its immutable `TargetResolutionArtifact`;
- referenced `QualifyingPitEventArtifact` or terminal/truncation metadata;
- exact observation identity/provenance.

A logical target dataset view may therefore expose one record per initialized episode with explicit columns/concepts equivalent to:

```text
TargetEpisodeDatasetRecord
  target_episode_key
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

Physical columns/types/file format are implementation choices. The key invariant is that observed-event, terminal-no-event, and truncation are explicit non-overlapping states and that the causal initialization artifact is not rewritten with future truth.

## Relationship between observation, episode, visit, and event identity

The identity graph is:

```text
CanonicalObservation
  1 -> 1 EligibilityDecision
  1 -> 0..1 TargetEpisodeInitialization

DriverEntry
  1 -> many PitVisitArtifact

PitVisitArtifact
  1 -> 0..1 QualifyingPitEventArtifact

TargetEpisodeInitialization
  1 -> 1 TargetResolutionArtifact

TargetResolutionArtifact (OBSERVED_EVENT)
  many episodes may -> same QualifyingPitEventArtifact
```

This preserves repeated-forecast semantics. Two observations at `T1` and `T2` may create separate episodes that both resolve to the same later tyre-service event when no qualifying event occurred between them.

## Ambiguity and conservative handling

Target reconstruction never makes convenience assumptions to increase label coverage.

| Ambiguity | Required outcome |
| --- | --- |
| Pit-lane entry exists but exact relation to `T` overlaps/equal/unknown | `TRUNCATED_INDETERMINATE` if the visit could be future and target-relevant |
| Two potential qualifying entries cannot be ordered | `TRUNCATED_INDETERMINATE` if ordering changes target identity |
| Visit known, tyre service cannot be confirmed or ruled out | `INDETERMINATE_TYRE_SERVICE`; truncate if target-relevant |
| Stint changed but no tyre-change proof | Do not infer tyre service |
| No compound update | Do not infer no service |
| `TyresNotChanged` semantics unverified | Do not use as sole negative proof |
| Processed `PitInTime` conflicts materially with validated raw entry evidence | Flag reconstruction conflict; do not choose whichever yields convenient ordering |
| Source gap may hide visit before candidate event/terminal | `TRUNCATED_INDETERMINATE` |
| Final status proves retirement but terminal instant is imprecise | Use bounded terminal evidence; truncate only when uncertainty can affect target closure/order |
| Legacy `PitStatus` disagrees with canonical evidence | Legacy value is QA evidence only; canonical reconstruction follows validated target sources |

## Provenance and versioning

Every event/target artifact must be traceable, as applicable, to:

- exact repository revision;
- approved target semantic version / decision references;
- exact observation artifact and prediction-boundary reference;
- frozen target-truth source manifest/content identities;
- provider/parser/adapter revision;
- target-reconstruction support validation IDs;
- pit-visit segmentation policy/version;
- pit-entry occurrence reconstruction method/version;
- tyre-service qualification policy/version;
- terminal reconstruction policy/version;
- target eligibility/initialization policy/version;
- target resolution policy/version;
- exact source-record/evidence lineage for material claims.

A later correction to source evidence, provider behavior, or reconstruction policy creates new artifacts/run lineage. Existing target artifacts used by a declared run are never overwritten in place.

## Verification handoff

The verification baseline after the design integration gate must establish a target-reconstruction support matrix and representative fixtures. At minimum it must cover:

1. raw `TimingData` `InPit=True/False` behavior for normal race pit visits;
2. pre-race/grid pit-lane movements and first-lap edge handling;
3. duplicate, missing, malformed, correction, and reset transition cases;
4. multiple distinct pit visits within one official lap when present or a synthetic fixture proving identity behavior;
5. comparison of canonical raw-entry reconstruction with FastF1 `PitInTime`/`PitOutTime` and documented discrepancy bounds;
6. `TimingAppData` tyre/stint update behavior around confirmed tyre changes;
7. same-compound tyre changes so compound equality cannot become a false negative;
8. drive-through/pass-through, penalty-only, repair-only, and other known no-tyre-service visits where source truth can establish them;
9. independent validation or explicit rejection of `TyresNotChanged` semantics by endpoint/era;
10. proof that stint increment alone is not used as tyre-service qualification;
11. missing/sparse tyre evidence producing `INDETERMINATE_TYRE_SERVICE` rather than guessed labels;
12. event-entry relation to exact/bounded prediction boundaries, including equality and overlap cases;
13. ordering of multiple potentially qualifying visits and conservative handling of overlapping occurrence bounds;
14. finish and retirement terminal boundaries across representative sessions;
15. source gaps that can hide visits causing truncation, while irrelevant post-closure gaps do not invalidate earlier observed events;
16. terminal-no-event cases proving complete relevant pit/service follow-up rather than relying on final status alone;
17. successive target episodes resolving to the same eventual event while retaining distinct episode IDs;
18. deterministic reconstruction/provenance from identical frozen sources/configuration.

Verification may establish support only for a subset of seasons/source eras. Unsupported historical scopes remain explicitly truncated/indeterminate rather than being backfilled from legacy labels.

## Decisions intentionally deferred

| Question | Owner |
| --- | --- |
| Exact source/endpoint/season support matrix and empirical reliability/tolerances | Verification baseline after #22 |
| Exact physical schemas, file formats, hashing, package classes, parser code, CLI commands | Implementation |
| Exact probability timing-region representation and mapping of resolved event occurrence into it | #20 — prediction distribution/model-facing contract |
| Replay ordering, temporal development/final-evaluation mechanics, target-state accounting in runs | #21 — replay/backtest contract |
| Final metrics, censoring/truncation statistical treatment, weighting/dependence estimators | Verification/statistical phase |
| Model features, model family, calibration, hyperparameters | Model verification/experimentation |
| Live target capture/runtime behavior | Future bounded live design |

## Acceptance mapping

- **Concrete source evidence:** raw `TimingData`, `PitInTime`/`PitOutTime`, `TimingAppData`, processed tyre fields, session/results/race-control evidence, and legacy limitations are inventoried with explicit authority limits.
- **Technical visit/event identities:** visit identity is entry-evidence based rather than lap based; same-lap distinct visits remain distinct; qualifying event identity remains separate.
- **Tyre-service qualification:** three-state service qualification prevents stint/compound/absence convenience assumptions from substituting for the approved event definition.
- **Pit-entry occurrence:** event occurrence is reconstructed as exact/bounded pit entry and remains the ordering anchor even when service is confirmed later.
- **Eligibility and episode creation:** eligibility consumes only the causal canonical observation; every eligible observation creates its own immutable episode without future-event-dependent eligibility.
- **Resolution states:** observed event, terminal no-event, and truncation/indeterminacy are explicit, non-overlapping, and coverage-aware.
- **Identity separation:** observation, target episode, pit visit, and eventual qualifying event have distinct identities and explicit links.
- **Ambiguity handling:** unresolved service, entry ordering, visit segmentation, source gaps, and terminal uncertainty fail closed when they can change target truth.
- **Consumer contract:** #20/#21 receive one canonical target-episode initialization/resolution contract without redefining target semantics.
- **Scope discipline:** no probability output representation, model, metric/statistical method, live runtime, or production implementation is selected.

## Product Owner decisions

None required. All material event semantics are already approved: tyre-service-only qualification and pit-lane-entry occurrence. The reconstruction, identity, conservative ambiguity, and provenance rules here are delegated technical choices that implement those locks.

## Review

This artifact requires one independent full scoped review under `governance/REVIEW_POLICY.md` before approval. Review should judge `design/TARGET_RECONSTRUCTION.md` against Issue #19, the approved #18 observation contract, `contexts/PIT_EVENT_TARGET.md`, and `decisions/2026-09-08-v2-pit-event-scope.md`. Exact model/output, statistical metrics, and production implementation owned by later phases are not required for approval.