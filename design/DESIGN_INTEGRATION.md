# V2 Architecture and Design Integration Gate

## Status

PASS (bounded re-check, 2026-10-10, `main` at `b8ae023`). The 2026-10-09 review recorded CHANGES REQUIRED, with one Blocking (F1), one Major (F2), and two Minor (F3, F4) findings. Since then the provider amendments have merged: #19 Amendment A1 (Issue #27, PR #31) and #18/#21 Amendment A1 (Issue #29, PR #32). The bounded re-check finds F1–F4 resolved and no cross-design contradiction introduced. It records one new Minor traceability finding (N1) and one Observation (O3), neither blocking. **Verification-baseline work is unblocked.** No Product Owner decision is required.

## Abstraction level

Architecture/design integration. This is a bounded review of cross-design composition only.

This artifact does not reopen Wave 1 semantics. It does not re-review any approved design slice internally, and it does not patch any slice. It does not select models, features, metrics, statistical procedures, or verification fixtures, and it does not define live inference, recommendation behavior, or production code.

## Issue / branch

- Issue: #22, `Architecture & design — integration gate`
- Parent: #16
- Branch: `ccr-d8f3e250-t7uix3`. This is the session task branch, used instead of the suggested `integrate/design-architecture-gate`. It equalled `origin/main` at `296a0d9` for the initial review and at `b8ae023` for the bounded re-check.

## Reviewed canonical artifacts

All five upstream design slices are approved, with a passing bounded re-review recorded in each one. All are merged to `main`:

| Slice | Artifact | Merge PR | Merge commit |
| --- | --- | --- | --- |
| #17 | `design/SYSTEM_ARCHITECTURE.md`: components, dependency rules, artifact classes, provenance boundary | #23 | `aeef78f` |
| #18 | `design/OBSERVATION_RECONSTRUCTION.md`: source authority, identities, `CanonicalObservation`, run manifest, quality states | #24 | `02ba6a6` |
| #19 | `design/TARGET_RECONSTRUCTION.md`: pit visit/event, eligibility, episode initialization, resolution states, resolution-run selection | #25 | `ac51408` |
| #20 | `design/PREDICTION_CONTRACT.md`: region grid, `CanonicalDistribution`, realized-target mapping, model and snapshot contracts, pit window | #26 | `61ae530` |
| #21 | `design/REPLAY_BACKTEST.md`: run kinds, temporal protocol, lock and ledger, accounting A0–A11, evaluation unit, reproduction | #28 | `296a0d9` |

The semantic baseline consumed unchanged:

- `contexts/RACE_OBSERVATION_STATE.md`, `contexts/PIT_EVENT_TARGET.md`, `contexts/PREDICTION_OUTPUT_REPLAY.md`, `contexts/EVALUATION_BACKTESTING.md`, `contexts/CONTEXT_MAP.md`, and the PASS gate `contexts/WAVE1_SEMANTIC_INTEGRATION.md`;
- `decisions/2026-09-08-v2-project-direction.md`, `decisions/2026-09-08-v2-pit-event-scope.md`, `decisions/2026-09-09-v2-prediction-output-semantics.md`.

Open cross-slice dependency issues considered at the initial review: #27 (`EntryLapContext` adoption in #19), which was then still open and not reflected in `design/TARGET_RECONSTRUCTION.md`.

Amendments consumed at the bounded re-check (each with its own passing independent review recorded in the amended artifact):

| Amendment | Artifact(s) | Issue | Merge PR | Merge commit | Findings addressed |
| --- | --- | --- | --- | --- | --- |
| #19 A1 | `design/TARGET_RECONSTRUCTION.md`: `EntryLapContext`, lap-completion support capability, `TargetInitializationRunManifest`, resolution/dataset reference fields | #27 | #31 | `9bdf6ee` | F1; F4 (#19 part) |
| #18 A1 | `design/OBSERVATION_RECONSTRUCTION.md`: `CheckpointAttemptRecord` and attempt enumeration, `SCHEDULED_RACE_DISTANCE_LAPS`, reason codes | #29 | #32 | `b8ae023` | F2; F3 |
| #21 A1 | `design/REPLAY_BACKTEST.md`: attempt-keyed manifest/ordering/accounting/reproduction, backtest-join initialization-lineage check | #29 | #32 | `b8ae023` | F2 (#21 part); F4 (#21 part) |

## Integration result

The five designs compose into one leakage-safe dependency structure:

```text
frozen source evidence (#18 SourceSnapshotManifest / #19 TargetTruthSourceManifest)
  -> CanonicalObservation (#18)                                   [causal]
  -> EligibilityDecision -> TargetEpisodeInitialization (#19)     [causal]
  -> PredictionRequest -> PredictionSnapshot | FailureRecord (#20, invoked by #21 ReplayRun)
  ...............................................................
  retrospective: PitVisit -> QualifyingPitEvent, TerminalBoundary -> TargetResolutionArtifact (#19)
  controlled joins: DevelopmentRun / BacktestRun (#21) apply the #20 realized-target mapping
  -> accounting A0–A11, EvaluationUnit, ScoreArtifact (#21)
```

Ownership is singular and no consumer redefines a provider contract. Identities chain from observation through episode to snapshot and evaluation unit without ambiguity about what each one means. The causal path cannot structurally receive retrospective truth.

At the initial review, two consumer requirements that #20 and #21 explicitly routed to provider slices were not yet satisfied by those providers:

- the lap count at pit entry, `c(E)`, needed to place observed events on the region grid (owner #19, Issue #27);
- per-attempt checkpoint records in the #18 run manifest (owner #18).

The first left Issue #22 acceptance criterion 4 unsatisfiable. The second left #21's "every candidate checkpoint gets exactly one accounting category" guarantee without a provider contract. Both failed closed, so neither caused leakage or a silent semantic change. They nevertheless prevented an implementable, verifiable end-to-end design.

**Bounded re-check result.** Both providers now supply the required contracts (PRs #31 and #32), the two Minor gaps are closed in the same amendments, and the composed chain is implementable and verifiable end to end. The updated dependency structure adds, without changing direction:

```text
#18 run manifest: CheckpointAttemptRecord[] (attempt_key)  -> #21 ReplayRunManifest / accounting / reproduction
#19 TargetInitializationRunManifest (target_initialization_run_ref) -> #21 ReplayRunConfig, A0, lineage check
retrospective: #19 resolution run -> EntryLapContext (same resolution_run_ref) -> #20 mapping inside #21 joins
#18 SCHEDULED_RACE_DISTANCE_LAPS -> #20 RegionGrid N_T (absent -> REQUIRED_CONTEXT_MISSING -> #21 A4)
```

## Cross-design checks

### 1. Dependency direction and leakage closure — PASS

- #17 dependency rules 1–11 are honored by every slice:
  - #18 consumes no target, prediction, or evaluation input (#18 *Upstream locks*, last paragraph).
  - #19 eligibility and initialization consume only the `CanonicalObservation` and target-definition configuration (#19 *Eligibility input boundary*).
  - #19 resolution never mutates the observation or the initialization.
- The #20 forecast-time closure is no larger than #17's:
  - `ModelInputView` derives from exactly one `CanonicalObservation`.
  - Data-derived configuration enters only through a frozen `ModelArtifact` that is bound by `development_temporal_boundary_ref`.
  - The estimator receives only `input_view`, `region_grid`, and the seed.
- #21 enforces the same closure operationally:
  - the replay direct-input allowlist aborts the run on any direct reference to a resolution, event, mapping, backtest, or score;
  - each race passes the cutoff check `t(cutoff) ≤ t(r)`;
  - the development join and the backtest join are the only two outcome joins, and both write to the ledger first (#17 rules 7 and 8).
- Retrospective grouping keys (`eventual_event_key`, `event_trajectory_key`) are barred from primary inclusion (#21 *Grouping metadata*), which preserves `contexts/EVALUATION_BACKTESTING.md` §10.
- The #20 `c(E)` requirement is correctly routed to the only boundary permitted to read retrospective evidence: #17 rule 4, the #19 resolution boundary. It is not routed to the joins.

### 2. Identity composition — PASS (F4 resolved by PRs #31 and #32)

| Identity | Canonical owner | Consumers | Composition |
| --- | --- | --- | --- |
| `RaceSessionKey`, `DriverEntryKey`, `CheckpointKey` (`completed_laps` unique per entry), semantic observation key | #18 (defined under #17 shared-primitive hosting; #17 delegated "technical identities" to #18) | #19, #20, #21 (manifest order, `GroupingKeys`) | consistent |
| Prediction instant `T` | #18 `prediction_boundary` | #19 (`prediction_boundary_ref`, not recalculated), #20 (snapshot `prediction_boundary_ref`), #21 (chronological order, including bounded `T`) | consistent |
| Observation artifact identity vs semantic key | #18 | all | separated consistently |
| `target_episode_key = (observation_artifact_ref, target_definition_version)` | #19 | #20 `prediction_key`, #21 join and `GroupingKeys` | consistent; observation-owned, not event-owned |
| `PitVisitKey`, `event_key` | #19 | #21 `eventual_event_key` | consistent; distinct from episode identity |
| `TargetResolutionArtifact` + `resolution_run_ref` (one selected per episode per run) | #19 | #20 `RealizedOutcome`, #21 protocol / backtest / ledger | consistent |
| `prediction_key = (target_episode_key, model_artifact_ref, prediction_run_ref)`; `snapshot_id` | #20 | #21 manifest, unit | consistent: #21 sets `prediction_run_ref = replay_run_id`, and `model_schedule` fixes one model per race, so each episode in a replay has exactly one `prediction_key` |
| `ModelArtifact.development_run_ref`, `development_temporal_boundary_ref` | fields #20; values #21 (`DevelopmentRun`, cutoff `RaceSessionKey`) | #21 cutoff check | consistent; #20 explicitly reserved these for #21 |
| Replay / backtest / development / score run ids, `protocol_id`, `lock_id` | #21 | — | consistent |
| `target_initialization_run_ref` | #19 `TargetInitializationRunManifest` (A1, PR #31); every resolution run declares exactly one | #21 `ReplayRunConfig`, A0 detection, backtest-join rule 5, audit | consistent (F4 resolved) |
| `attempt_key = (attempt_level, race_session_key, driver_entry_key \| driver_alias, checkpoint_key?)` | #18 `CheckpointAttemptRecord` (A1, PR #32) | #21 manifest key and order, accounting rows, reproduction keying | consistent; covers key-less identity failures (F2 resolved); `semantic_observation_key` is derived from it for `CHECKPOINT` rows |
| `EntryLapContext.artifact_id`, `entry_lap_context_ref` | #19 (A1, PR #31); at most one per qualifying event per resolution run | #20 `RealizedOutcome.entry_lap_context_ref`, #21 joins | consistent (F1 resolved) |

### 3. Separate ownership of observation and target; target truth cannot mutate prediction-time state — PASS

- #18 and #19 have separate source manifests (`SourceSnapshotManifest` and `TargetTruthSourceManifest`) and separate support validations (`AvailabilityAuthorityValidation` and `TargetReconstructionSupportScope`). #19 states explicitly that the two must not be conflated.
- The `EligibilityDecision` and `TargetEpisodeInitialization` contain no outcome. Resolution artifacts are new immutable versions, never in-place edits (#19 *Resolution cardinality*).
- #20 forbids a snapshot from storing a resolution, a realized outcome, or a score.
- #21 forbids any feedback from replay or backtest into observations, eligibility, or snapshots.

### 4. Target-event timing maps into the prediction region representation — PASS (F1 resolved by PR #31)

The mapping design composes correctly when its input exists:

- #19 fixes the event occurrence at pit-lane entry, exact or bounded, strictly inside `(T, B)`.
- #20 locates that occurrence on the driver-lap-offset grid through `c(E)`, measured on the same as-raced counter that defines #18 checkpoint `L`. Bounded `c(E)` becomes `REALIZED_REGION_SET`, and the open final region gives complete coverage regardless of `N_T` accuracy.
- #20 computes the grid from the observation alone, so development and backtest see the same grid.
- #21 applies the mapping only inside the two controlled joins.

The input itself does not exist. `c(E)` requires the additive #19 `EntryLapContext` (Issue #27), and that artifact is not in `design/TARGET_RECONSTRUCTION.md`. As a result:

- every `OBSERVED_EVENT` maps to `MAPPING_UNAVAILABLE`;
- every #21 backtest run with an observed event in scope is `DEFECTIVE` (category A8);
- no `PRIMARY` score is possible;
- development has no region labels for observed events.

Issue #27 explicitly makes #22 the confirmation point, and confirmation is not possible. See F1.

**Bounded re-check (PR #31).** #19 Amendment A1 adopts `EntryLapContext`, and the #22 confirmation that #20 and Issue #27 require is given here:

- **Definition matches #20.** The counter is the as-raced official completed-race-lap counter of #18 checkpoints, ordered by occurrence, with classification adjustments never substituted. The exact formula `#{k : C_k ≤ E}`, the bounded `c_lo`/`c_hi` formulas, and the "same instant counts as completed" rule are identical to `design/PREDICTION_CONTRACT.md` *Lap count at pit entry*, and #19 cites #20 as the defining source rather than redefining it.
- **Required contents present.** Every field #20 requires (`artifact_id`, `qualifying_event_ref`, `driver_entry_key`, `lap_counter_ref`, `c_exact? | c_lo, c_hi`, `lap_completion_evidence_refs`, `entry_lap_derivation_version`, `provenance`) is in the #19 artifact. The extra fields (`resolution_run_ref`, `support_validation_refs`, `repository_revision`) are additive.
- **Mapping input resolvable.** #20's input "the `EntryLapContext` linked to the referenced `QualifyingPitEventArtifact`" is reached deterministically through the selected `TargetResolutionArtifact.entry_lap_context_ref`, under the same `resolution_run_ref`, with at most one context per event per run. For `OBSERVED_EVENT` exactly one of `entry_lap_context_ref` or `entry_lap_context_absent_reason` is present, so #20's `OBSERVED_EVENT, no EntryLapContext -> MAPPING_UNAVAILABLE` line now fires only for a recorded, evidence-based absence. That is a #21 A8 run defect, removable only through `supported_scope`.
- **F1 requirements (a)–(c) met:** (a) produced only by retrospective resolution, never consumed by observation, eligibility, or prediction (#17 rule 4); (b) bound to the selected resolution run, so #21's reproduction rule ("resolution references are identical") covers it; (c) the *driver official lap-completion occurrence reconstruction* capability is added to the support scope, with `lap_completion_coverage` and verification items 23–24, including the comparison with #18 checkpoint counts that proves the counters are identical.
- No #19 event, visit, episode, eligibility, or resolution semantics changed, and the #20 coverage proof (`c(E) ≥ L`) still rests on the shared counter.

### 5. Observed-event, terminal no-event, ineligible, and truncated states end to end — PASS (the F1 condition is lifted by PR #31)

| State | #19 | #20 | #21 |
| --- | --- | --- | --- |
| No canonical observation | (#18 `INDETERMINATE_*`; session/entry identity failures and `ENUMERATION_INCOMPLETE` as `CheckpointAttemptRecord`s) | no request | A1 causal exclusion, one row per attempt record (F2 resolved, PR #32); `ESTABLISHED` session/entry rows receive no category |
| Target-ineligible | `INELIGIBLE`, no episode | no request | A2, not an evaluation unit |
| Eligibility indeterminate | `INDETERMINATE`, no episode | no request | A3 |
| Prediction invalid | — | `PredictionFailureRecord` | A4 |
| Observed event | `OBSERVED_EVENT` + `qualifying_event_ref` + `entry_lap_context_ref` or `entry_lap_context_absent_reason` | `REALIZED_REGION` / `REALIZED_REGION_SET`; `MAPPING_UNAVAILABLE` only with a recorded absence reason | A9 / A10 (A8 for absence) |
| Terminal no-event | `TERMINAL_NO_EVENT` + `terminal_boundary_ref` | `REALIZED_NO_EVENT`, scored through `q` | A11 |
| Truncated / indeterminate | `TRUNCATED_INDETERMINATE` + reasons | `NOT_REALIZED`, no probability category (V6) | A6 resolvability exclusion |
| Mapping defects | — | `MAPPING_CONFLICT`, `MAPPING_UNAVAILABLE` | A7 / A8 run defects, not cohort filters |

The states are mutually exclusive and never collapse into one another. Terminal no-event is never synthesized from truncation or ineligibility. Truncation is never a prediction outcome.

### 6. Snapshot immutability, distinct successive forecasts, shared eventual event — PASS

- #19 creates one episode per eligible observation, and many episodes may resolve to one `QualifyingPitEventArtifact`.
- In #20, successive checkpoints have distinct `target_episode_key`s and therefore distinct snapshots. Snapshots are never chained, carried forward, or edited, and a re-execution creates a new `prediction_key`.
- In #21, units sharing `eventual_event_key` are never deduplicated, earlier manifest records are never revisited, and aborted runs are never resumed in place.

### 7. Version, provenance, and run-metadata sufficiency without contradictory ownership — PASS (F2 resolved by PR #32; F4 resolved by PRs #31 and #32)

Most of the chain composes:

- #17's provenance boundary is instantiated by each slice: #18 run manifest and observation provenance; #19 manifests and per-artifact policy versions; #20 `ModelArtifact`, snapshot digests, and seeds; #21 common provenance and the semantic-keyed reproduction rule.
- `prediction_contract_version`, `mapping_version`, `dependency_lock_ref`, and the seeds are each owned once and referenced elsewhere. No two slices claim to own the same one.
- #21's reproduction rule uses #20's `request_digest`, `content_digest`, and declared tolerance unchanged.

Two pieces are missing:

- **F2:** #21 accounting and manifest order need a per-attempt checkpoint record from #18, and #18's manifest provides only counts and emitted IDs.
- **F4:** the `target_initialization_run_ref` that #21 references has no defining run or manifest contract in #19, and nothing checks lineage between the initialization a snapshot used and the initialization its selected resolution resolved.

**Bounded re-check (PRs #31 and #32).**

- **F2.** The #18 run manifest now holds one `CheckpointAttemptRecord` per attempt at the `SESSION`, `DRIVER_ENTRY`, and `CHECKPOINT` levels. The enumeration domain covers `RACE_START` and `L = 1 … L_max`, including `LAP_COUNT_JUMP`, unverified-scope, and missing-trigger gaps. Identity failures without a `DriverEntryKey` carry a candidate-distinguishing `driver_alias`. The unique `attempt_key` composes with #21:
  - the manifest total order (attempt-level rank, missing keys last) is independent of `T`, and per-entry `completed_laps` order is preserved;
  - the candidate population is every `CHECKPOINT` record plus every non-`ESTABLISHED` session/entry record, so every candidate gets exactly one category and A1 is not inflated by success rows;
  - reproduction keys on `attempt_key` plus `target_episode_key` where present.

  The retrospective `L_max` is used only to enumerate accounting attempts, never as observation content or a boundary, so the #17 closure and #21 cohort independence are unaffected. #21 consumes the representation without redefining it.
- **F4.** #19 defines `TargetInitializationRunManifest`: exactly one decision per canonical observation of the referenced #18 run, an initialization present iff `ELIGIBLE`, missing records treated as run defects, and no retrospective input. Every resolution run declares exactly one `target_initialization_run_ref` and resolves only initializations from it, so selection by `target_episode_key` is unambiguous. A0 ("observation without a decision") is now defined relative to this run-scoped manifest. #21 backtest-join rule 5 requires the snapshot's `target_episode_initialization_ref` (a #20 snapshot field) to equal the selected resolution's, and the resolution run's `target_initialization_run_ref` to equal the replay's. Any mismatch is an A0 run defect.

### 8. Replay/backtest consumes rather than redefines upstream contracts — PASS

#21 consumes the upstream contracts without redefining them:

| Upstream contract | Consumed by #21 as |
| --- | --- |
| #18 quality states | A1 |
| #19 eligibility states | A2 / A3 |
| #19 resolution selection | `resolution_run_ref` |
| #20 failure records | A4 |
| #20 `RealizedOutcome` kinds | A5–A11 |
| #20 snapshot identity and tolerance | reproduction rule |

#21 invokes the #20 prediction procedure, which remains the sole snapshot creator (#17 component 6). #21 runs the #20 mapping function but does not define it, which settles the routing question #20 left open about who runs the mapping.

#21's `model_schedule` (one fixed artifact per race) refines #17's "fixed model/prediction artifact" without contradicting it. See O1.

### 9. Extension seams do not make live inference an initial commitment — PASS

No slice makes live inference an initial commitment:

- #17 keeps live work to named seams.
- #18 treats contemporaneous capture as an evidence class, explicitly "not an initial live-product commitment".
- #20 is offline and replay-driven, with no serving API.
- #21 defines no live triggers, streaming, or monitoring.

No slice introduces recommendation or optimization semantics.

### 10. Scheduled race distance `N_T` as an observation fact — PASS (F3 resolved by PR #32)

#20's grid needs `N_T` from a legitimate `CanonicalObservation` fact.

Semantic legitimacy is already established:

- `contexts/RACE_OBSERVATION_STATE.md` admits pre-race facts that were available and not superseded by `T`.
- #18's `STATIC_PRIOR` class and its `session/race facts` state domain can express `N_T`.
- A missing `N_T` fails closed: #20 records `REQUIRED_CONTEXT_MISSING`, which #21 counts as causal A4 (or `GRID_UNAVAILABLE` in development). It is never invented.

There is therefore no contradiction. However, #18 names no source, downstream obligation, or verification item for this fact. If it is never produced, no snapshot can be created anywhere. See F3.

**Bounded re-check (PR #32).** #18 now names `SCHEDULED_RACE_DISTANCE_LAPS` as a `canonical_state` session/race fact supplying #20's `N_T`, and this composes with #20:

- **Pre-race value.** A proven pre-race schedule value is admitted as `STATIC_PRIOR`.
- **In-race revisions.** Revisions are admitted only from their own verified availability. That matches #20's "latest known version at `T`" and `scheduled_distance_fact_ref`, and `V7_GRID_MATCH` can read it.
- **Never used.** Final-only values (`max(observed lap)`, the classified distance) are excluded, so no future information enters the grid.
- **Absence.** No admissible value means `SCHEDULED_DISTANCE_UNAVAILABLE`, which leads to #20 `REQUIRED_CONTEXT_MISSING`, which #21 counts as causal A4 (or `GRID_UNAVAILABLE` in development).
- **Possible staleness.** `DISTANCE_REVISION_CHANNEL_UNVERIFIED` flags a value that may be stale. It is informational and scope-based, so it cannot leak whether a revision occurred, and staleness affects only grid resolution, never coverage (#20 *Coverage proof*).
- **Verification.** The source obligation is in #18 verification item 15.

## Findings

### Blocking

**F1: `EntryLapContext` (`c(E)`) not adopted, so pit-entry timing cannot be mapped to the prediction regions.** — **RESOLVED** by #19 Amendment A1 (Issue #27, PR #31, merge `9bdf6ee`). Requirements (a)–(c) are verified in check 4.

- **What is wrong.** #20's realized-target mapping requires an additive #19 artifact that gives the driver's as-raced official completed-lap count at pit entry. Without it, every `OBSERVED_EVENT` becomes `MAPPING_UNAVAILABLE`, and #21 must mark every affected run `DEFECTIVE`.
- **Why this is Blocking.** Issue #22 acceptance criterion 4 ("canonical pit-entry target timing maps cleanly into the complete prediction-distribution representation") cannot be satisfied. Issue #27 names this gate as its confirmation point.
- **Not acceptable as routed.** The routing is correct and fails closed, but leaving it open would let verification start against a mapping with no producer, and no valid primary backtest or region-labelled development set could exist.
- **Owner.** #19 `design/TARGET_RECONSTRUCTION.md`, via Issue #27, as a bounded additive amendment with its own independent scoped review.
- **Requirements the amendment must meet**, beyond those in #27:
  - (a) produced only at the retrospective-resolution boundary (#17 rule 4);
  - (b) deterministically selectable under a declared `resolution_run_ref`, either produced in or bound to the same resolution run as the selected `TargetResolutionArtifact`, so that the #20 mapping and the #21 reproduction rule ("resolution references are identical") stay reproducible;
  - (c) a lap-completion capability added to the `TargetReconstructionSupportScope` / support matrix, which #21's `supported_scope` already consumes.
- **No Product Owner decision.** No event, episode, or resolution semantics change.

### Major

**F2: The #18 run manifest has no per-attempt checkpoint records.** — **RESOLVED** by #18 Amendment A1 and the #21 consequential amendment (Issue #29, PR #32, merge `b8ae023`). Items (a)–(c) and the #21 consumer check are verified in check 7.

- **What is wrong.** The #21 per-checkpoint step, the A1 category, the manifest total order `(race_session_key, driver_entry_key, completed_laps)`, and the guarantee that "every candidate checkpoint gets exactly one accounting category" all require #18 to enumerate every attempted checkpoint with its semantic key and quality or failure state. #18 says "failure/indeterminate attempts remain in run accounting", but its manifest contract lists only counts and emitted artifact IDs.
- **A further hole.** `INDETERMINATE_IDENTITY` attempts have no `DriverEntryKey`, so the #21 record key cannot represent them as currently specified.
- **Why Major.** The design is consistent in direction, but the provider-to-consumer contract is materially incomplete. Coverage accounting and verification items (#21 items 1 and 7) cannot be written against it.
- **Owner.** #18 `design/OBSERVATION_RECONSTRUCTION.md`, as a bounded additive amendment that defines:
  - (a) one manifest record per attempted checkpoint, with semantic key, `observation_artifact_ref?`, quality status, and reason codes;
  - (b) the enumeration domain, including skipped `LAP_COUNT_JUMP` checkpoints;
  - (c) how identity-failure attempts that have no `DriverEntryKey` are recorded.
- **Consequential consumer check.** #21 must confirm, or add with a one-line amendment, how key-less identity-failure records enter its manifest and accounting table. #21 must not redefine #18's representation.

### Minor

**F3: Scheduled race distance `N_T` is not named in #18's downstream contract or verification handoff.** — **RESOLVED** by #18 Amendment A1 (Issue #29, PR #32). Verified in check 10.

- **Owner.** #18.
- **Suggested resolution.** Bundle with the F2 amendment. Name scheduled race distance as a `session/race` fact, `STATIC_PRIOR` when proven pre-race. Any in-race revision is admissible only under verified authority. Add it to the #20 downstream contract and the source-authority support-matrix obligations.
- **Why Minor.** Fail-closed behavior and semantic legitimacy are already in place.

**F4: Target-initialization run identity and resolution lineage.** — **RESOLVED**: the #19 part by PR #31 (`TargetInitializationRunManifest`, one declared initialization run per resolution run), and the #21 part by PR #32 (backtest-join rule 5, A0). Verified in checks 2 and 7.

- **What is wrong.** #21 references `target_initialization_run_ref` and initialization run manifests (*Minimum audit artifacts*), and A0 ("observation without a decision") is only well-defined relative to a run-scoped decision set. #19 defines resolution runs but no initialization run or manifest.
- **A lineage gap.** `target_episode_key` excludes `initialization_policy_version`. A replay's `TargetEpisodeInitialization` and the selected resolution's `target_episode_initialization_ref` could therefore come from different initialization runs, and nothing checks that they agree.
- **Owners.**
  - #19: define the initialization run identity and manifest (can be folded into the #27 amendment);
  - #21: add a backtest-join consistency check that the snapshot's `target_episode_initialization_ref` equals the selected resolution's, or treat a mismatch as A0.
- **Why Minor.** Traceability and lineage only; the target question being answered is unchanged.

### Observations

**O1: Single fixed model vs `model_schedule`.** #17 flow C reads as one fixed model per replay. #21 allows one fixed, pre-declared, cutoff-checked artifact per race. This is a permitted lower-level refinement (#17 delegated the replay contract to #21), and #17's leakage intent is preserved. No change is required. #17 wording may be aligned at its next revision.

**O2: #17 inventory omits the #21 evaluation-governance artifacts.** The #17 artifact-class table does not list `BacktestProtocol`, `ProcedureSpec`, `EvaluationLock`, `DevelopmentRun` manifests, `ScoreArtifact`, or the append-only `FinalEvaluationLedger`, which the development join, the backtest join, and registered ad hoc reads all write. Ownership is still unambiguous (#21, by #17's explicit delegation), and append-only entries are never overwritten, so this is consistent with #17's immutability meaning. No change is required. An optional #17 inventory touch-up can be made at its next revision.

### New at the bounded re-check

**N1 (Minor): stale consumer-side status text for `EntryLapContext` and `N_T`.**

- **What is wrong.** After PRs #31 and #32, these consumer statements still read as unresolved:
  - `design/PREDICTION_CONTRACT.md` (#20) *Owner and artifact* paragraph ("Until #19's owner adopts it…") and its *Unknown routing* rows for `EntryLapContext` (**Not yet satisfied**) and `N_T` ("Assumed expressible…");
  - the `EntryLapContext adoption` row in `design/REPLAY_BACKTEST.md` (#21) *Unknown routing* ("Not yet satisfied…").
- **Why Minor.** This is traceability only. The normative behavior is unchanged and still composes: a missing context maps to `MAPPING_UNAVAILABLE` and A8, now driven by #19's `entry_lap_context_absent_reason`, and a missing `N_T` fails closed. This gate record is the durable confirmation of adoption that #20 and Issue #27 call for.
- **Owner.** #20 and #21 owners, as a metadata-only status touch-up at their next revision. It does not block this gate or verification-baseline work.

**O3 (Observation): lineage assertions outside the backtest join.**

- **What is missing.** #21 rule 5 checks initialization lineage at the backtest join only. The development join (`DevelopmentRunConfig` carries observation/initialization run refs and `resolution_run_ref`) states no equivalent check that the resolution run's `target_initialization_run_ref` equals the development run's. #21 also does not explicitly assert that a replay's `observation_reconstruction_run_ref` equals its initialization run's `observation_reconstruction_run_ref`.
- **Why no change is required.** A replay-side mismatch already fails closed as A0, because decisions are absent for the replay's observations, and F4 was scoped to the backtest join.
- **Suggested routing.** The verification baseline can add a development-join lineage fixture. #21 may state the check explicitly at its next revision.

## Unknown routing

| Question | Classification | Owner / next phase | Status |
| --- | --- | --- | --- |
| Is any cross-design contradiction present? | Current-scope integration decision | #22 | **Resolved**: no contradiction between approved contracts, re-confirmed at the bounded re-check with no regressions from PRs #31 and #32 |
| `EntryLapContext` / `c(E)` production, resolution-run binding, lap-completion support capability | Cross-slice dependency | #19 via Issue #27 | **Resolved (F1)** by PR #31; adoption confirmed by this gate |
| Per-attempt checkpoint records and identity-failure attempts in the #18 run manifest | Cross-slice dependency | #18 (Issue #29); #21 consequential check | **Resolved (F2)** by PR #32 |
| Scheduled race distance `N_T` as a named #18 fact and support-matrix item | Cross-slice dependency | #18 (Issue #29); verification support matrix | **Resolved (F3)** by PR #32; empirical source support deferred to verification (#18 item 15) |
| Target-initialization run/manifest identity; initialization-lineage check at the backtest join | Cross-slice dependency | #19 (Issue #27) and #21 (Issue #29) | **Resolved (F4)** by PRs #31 and #32 |
| Stale "not yet satisfied" status text for `EntryLapContext` / `N_T` in #20 and #21 | Cross-slice traceability | #20 and #21 owners, next revision | Open (N1, Minor, non-blocking) |
| Development-join initialization-lineage check; replay observation-run / initialization-run agreement | Later-phase / optional refinement | Verification baseline fixture; optional #21 wording | Open (O3, Observation) |
| Who runs the realized-target mapping; `prediction_run_ref` vs replay run; `development_temporal_boundary_ref`; resolution-run selection | Cross-slice dependency (raised by #20) | #21 | **Resolved** by #21 as consumed |
| Empirical support matrices (availability authority, target truth, lap-completion, scheduled-distance sources, attempt-record completeness) | Later-phase decision | Verification baseline (#18 items 14–15, #19 items 23–25, #21 item 7) | Deferred |
| Metrics, set-valued scoring, dependence-aware statistics, A6 sensitivity | Later-phase decision | Verification/statistical phase | Deferred |
| Model family, features, loss, calibration, probability floor | Later-phase decision | Model experimentation | Deferred |
| Schemas, formats, digests, storage, access control for gated joins | Later-phase decision | Implementation | Deferred |
| Live inference | Future bounded product/design work | — | Not an initial commitment |

There are no Product Owner-reserved decisions in this gate.

## Acceptance criteria (Issue #22)

- [x] #17–#21 are confirmed approved and merged (PRs #23, #24, #25, #26, #28) before review.
- [x] End-to-end dependency direction is coherent and cannot leak retrospective target truth into observations or predictions.
- [x] All cross-artifact identities and references compose unambiguously. Satisfied at the bounded re-check: `target_initialization_run_ref` is defined by #19 (F4, PR #31), and identity-failure attempts are keyed by `attempt_key` (F2, PR #32).
- [x] Canonical pit-entry target timing maps cleanly into the complete prediction-distribution representation. Satisfied at the bounded re-check: `EntryLapContext` matches #20's `c(E)` definition and is bound to the selected resolution run (F1, PR #31), and `N_T` is a named #18 fact (F3, PR #32).
- [x] Terminal no-event, truncation, ineligibility, and observed-event states remain distinct across reconstruction, prediction, and evaluation.
- [x] Immutable successive prediction semantics are preserved technically.
- [x] Reproducibility, version, and provenance responsibilities compose without duplication or gaps. No duplication; gaps F2 and F4 are closed by PRs #31 and #32.
- [x] Replay/backtest orchestration consumes rather than redefines upstream contracts.
- [x] Every actual design contradiction or gap is routed to its canonical owner and not patched in this gate.
- [x] No semantic lock, live ambition, recommendation behavior, verification fixture, or production implementation is introduced.
- [x] Gate verdict is recorded. Initial review: `CHANGES REQUIRED`. Bounded re-check: **`PASS`**. Verification-baseline work is **unblocked**.

## Gate outcome

**PASS** (bounded re-check, 2026-10-10, `main` at `b8ae023`).

The five approved designs, as amended by #19 A1 (PR #31) and #18/#21 A1 (PR #32), compose into one leakage-safe, implementable, and verifiable end-to-end design. F1–F4 are resolved, the amendments introduce no cross-design contradiction or semantic change, and every Issue #22 acceptance criterion is satisfied. **Verification-baseline work is unblocked.**

Remaining handoffs, none of which blocks the gate:

- **Verification baseline.** Support matrices (availability authority, target truth, lap-completion, scheduled-distance sources); #18 items 1–15, #19 items 1–25, #20 and #21 verification items; and the O3 development-join lineage fixture.
- **Verification/statistical phase.** Metrics, set-valued scoring, dependence-aware statistics, A6 sensitivity.
- **Model experimentation.** Model family, features, loss, calibration, probability floor.
- **Implementation.** Schemas, formats, digests, storage, access control for gated joins.
- **Next revisions, optional.** N1 status touch-up in #20 and #21; O1/O2 wording in #17; O3 wording in #21.

### Initial outcome (2026-10-09, superseded)

**CHANGES REQUIRED.** A bounded design reconciliation is required before verification-baseline work begins:

1. **#19 amendment (Issue #27).** Adopt `EntryLapContext` with requirements F1 (a)–(c). Optionally fold in the F4 initialization run/manifest definition. Requires an independent scoped review of the amendment only.
2. **#18 amendment (new bounded issue).** Add per-attempt checkpoint records, including the enumeration domain and identity-failure attempts (F2). Name scheduled race distance `N_T` as a session/race fact with its support-matrix obligation (F3). Requires an independent scoped review of the amendment only.
3. **#21 consequential touch-up.** Handle key-less identity-failure records as defined by #18 (F2), and add the initialization-lineage consistency check at the backtest join (F4).
4. **Bounded #22 re-check.** After items 1–3 merge, verify only F1–F4 and any regressions they cause, per `governance/REVIEW_POLICY.md`. This is not a fresh review of the slices.

These items do not need to reopen any approved semantic lock, and no Product Owner decision is required.

Items 1–3 were completed by PR #31 (Issue #27) and PR #32 (Issue #29). Item 4 is the bounded re-check recorded below.

## Review record

- Reviewer: independent integration review agent. It did not author any of the reviewed designs. The review is recorded through the repository's connected GitHub account.
- Date: 2026-10-09
- Reviewed state: `main` at `296a0d93e4ca9c2b5c8111b47ba141ca4b51c8db`, which includes the merges of PRs #23, #24, #25, #26, and #28.
- Scope: cross-design composition only, per `governance/REVIEW_POLICY.md` *Integration review* and the Issue #22 scope.
- Outcome (initial review): **CHANGES REQUIRED**. Blocking: F1. Major: F2. Minor: F3, F4. Observations: O1, O2. Superseded by the bounded re-check below.
- Product Owner decision: none required.

### Bounded re-check

- Reviewer: independent integration review agent. It did not author any of the reviewed designs or amendments. The re-check is recorded through the repository's connected GitHub account.
- Date: 2026-10-10
- Reviewed state: `main` at `b8ae023`, which adds the merges of PR #31 (`9bdf6ee`, #19 Amendment A1, Issue #27) and PR #32 (`b8ae023`, #18 and #21 Amendment A1, Issue #29) to the initially reviewed state. The delta reviewed is `git diff 202d307..b8ae023`.
- Scope: bounded per `governance/REVIEW_POLICY.md` *Bounded re-review* and *Integration review*. It covers verification of F1–F4 across the composed designs, cross-design regressions introduced by the amendments, and re-confirmation of the Issue #22 acceptance criteria. It is not a fresh integration review, and no slice was re-reviewed internally.
- Per-finding resolution:
  - F1 (Blocking): **resolved** by PR #31. `EntryLapContext` matches #20's `c(E)` counter, formulas, and required contents, and is bound to the selected resolution run via `entry_lap_context_ref`. Lap-completion support capability added.
  - F2 (Major): **resolved** by PR #32. `CheckpointAttemptRecord` with `attempt_key` covers key-less identity failures, and #21 manifest order, candidate population, accounting, and reproduction consume it.
  - F3 (Minor): **resolved** by PR #32. `SCHEDULED_RACE_DISTANCE_LAPS` supplies `N_T`, and absence leads to `REQUIRED_CONTEXT_MISSING` and A4.
  - F4 (Minor): **resolved** by PRs #31 and #32. `TargetInitializationRunManifest`, one declared initialization run per resolution run, and backtest-join lineage rule 5 (A0).
- Regressions: no cross-design contradiction. Dependency direction, the causal closure, state distinctness, and snapshot immutability are unchanged, and the #17 artifact classes and dependency rules accommodate the new artifacts.
- New findings: N1 (Minor, owners #20/#21, next revision, non-blocking); O3 (Observation, verification baseline / optional #21 wording).
- Outcome: **PASS**. Verification-baseline work is unblocked.
- Product Owner decision: none required.
