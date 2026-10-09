# V2 Historical Replay and Backtest Execution Contract

## Status

Draft — authored for Issue #21. Independent full scoped review required before approval.

## Abstraction level

Detailed replay/backtest design: replay ordering, prediction-snapshot generation runs, run identity/configuration/provenance, the temporal development versus final-evaluation mechanism, candidate and cohort selection, accounting of non-scored cases, grouping metadata for repeated forecasts, the scorer plug-in boundary, and minimum audit artifacts.

This artifact does not define observation, target, or prediction semantics or their technical contracts (#18–#20), final metrics or statistical estimators, model family/features/hyperparameters, replay UI, live inference, or production code.

## Issue / branch

- Issue: #21 — `Design — historical replay and backtest execution contract`
- Parent: #16
- Upstream: #17 `design/SYSTEM_ARCHITECTURE.md`; #18 `design/OBSERVATION_RECONSTRUCTION.md`; #19 `design/TARGET_RECONSTRUCTION.md`; #20 `design/PREDICTION_CONTRACT.md` (all approved and merged)
- Branch: `ccr-d8f3e250-t7uix3` (session task branch used in place of the suggested `design/replay-backtest-contract`)

## Outcome

V2 historical evaluation is executed as four kinds of immutable run, each with a manifest:

```text
ReplayRun            ordered observations + eligibility -> prediction snapshots / failures
DevelopmentRun       development-partition observations + selected resolutions -> model artifact(s)
BacktestRun          one completed ReplayRun + selected resolutions -> evaluation units + accounting
ScoreRun             one BacktestRun + a versioned scorer -> score artifacts
```

The temporal protocol is **season-ordered rolling-origin development followed by a locked, single-use final holdout**:

- prediction-producing choices are made only from development folds, in which each validation season is predicted by procedures fitted on strictly earlier races;
- the chosen procedure is then frozen in an `EvaluationLock` before any final-partition outcome is joined;
- each final partition records, in an append-only ledger, every time its outcomes were opened. Only the first locked procedure evaluated on it may be reported as the primary final claim.

The evaluation unit stays the #20 `PredictionSnapshot` joined to the selected #19 resolution of its own `target_episode_key`. Every candidate checkpoint lands in exactly one accounting category, so nothing disappears silently.

## Upstream locks consumed unchanged

- `contexts/EVALUATION_BACKTESTING.md` — replay versus backtest, the atomic prediction-target unit, entry conditions, end-to-end point-in-time legitimacy, observed-event, terminal no-event and truncation comparison semantics, repeated-forecast identity, no outcome-peeking cohort selection, development versus final separation, temporal ordering, declared protocol, and reproducibility.
- `contexts/PREDICTION_OUTPUT_REPLAY.md` and `decisions/2026-09-09-v2-prediction-output-semantics.md` — immutable successive snapshots; complete distribution plus terminal no-event; truncation is not a prediction category.
- `design/SYSTEM_ARCHITECTURE.md` — replay coordinates but never creates prediction contents. Development assembly and backtest assembly are the only controlled joins with retrospective truth. Rerunning creates new runs.
- `design/OBSERVATION_RECONSTRUCTION.md` — checkpoint boundaries, observation quality states, and source-authority support. Unsupported or unverified scopes stay explicitly indeterminate.
- `design/TARGET_RECONSTRUCTION.md` — `EligibilityDecision`, `TargetEpisodeInitialization`, resolution states, and exactly one selected `TargetResolutionArtifact` per episode per declared `resolution_run_ref`.
- `design/PREDICTION_CONTRACT.md` — `PredictionSnapshot`, `PredictionFailureRecord`, `prediction_run_ref`, `RegionGrid`, and the realized-target mapping with kinds `REALIZED_REGION`, `REALIZED_REGION_SET`, `REALIZED_NO_EVENT`, `NOT_REALIZED`, `MAPPING_CONFLICT`, and `MAPPING_UNAVAILABLE`.

## Replay execution

### Inputs

```text
ReplayRunConfig
  replay_scope: list of RaceSessionKey
  observation_reconstruction_run_ref       # #18 run supplying observations
  target_initialization_run_ref            # #19 eligibility/initialization run
  model_artifact_ref                       # exactly one fixed model per replay run
  inference_seed_policy                    # e.g. derived from (run seed, prediction_key)
  prediction_contract_version
  repository_revision, dependency_lock_ref
```

A replay run consumes no `TargetResolutionArtifact`, no `QualifyingPitEventArtifact`, no realized outcome, and no score. Its dependency closure is checked when the run starts (see *Leakage controls*).

### Ordering

Within one race session, replay processes checkpoint records in the total order:

```text
(prediction_boundary T on the validated information clock,
 trigger_record_ordinal_if_verified,
 driver_entry_key,
 checkpoint_key.completed_laps)
```

- For a fixed driver entry, the order is strictly increasing in `completed_laps`, because #18 boundaries are monotone per driver.
- Across drivers, ties or bounded boundaries are ordered by the deterministic keys above. That order affects only manifest order and presentation, never prediction content. Each prediction depends only on its own observation (#20 input boundary), so it cannot see an "earlier" competitor's prediction.
- Sessions are processed in `RaceSessionKey` order. Sessions are independent in a replay run.

### Per-checkpoint step

For each attempted checkpoint reported by the referenced #18 run, in replay order:

1. If no `CanonicalObservation` exists (`INDETERMINATE_CHECKPOINT`, unsupported source, or another #18 failure state), record the accounting state and continue.
2. Read the #19 `EligibilityDecision` for that observation. If it is `INELIGIBLE` or `INDETERMINATE`, record it and continue. No prediction is requested.
3. If it is `ELIGIBLE`, pass the observation and its `TargetEpisodeInitialization` to the #20 prediction procedure, together with the run's model artifact and seed.
4. Record the returned `snapshot_id` or `PredictionFailureRecord` reference in the manifest.
5. Never revisit or rewrite an earlier record.

The replay orchestrator does not compute eligibility, construct inputs, or create snapshot contents.

### Prediction run identity

Each replay run has exactly one `prediction_run_ref`, equal to its `replay_run_id`. This fills the #20 `prediction_key` field. A snapshot is therefore unique per `(target_episode_key, model_artifact_ref, replay_run_id)`.

### Replay run manifest

```text
ReplayRunManifest
  replay_run_id                     # digest of config + start record
  config: ReplayRunConfig (+ digest)
  records[]:                        # one per attempted checkpoint, in replay order
    semantic_observation_key
    observation_artifact_ref?
    observation_quality_status
    eligibility_decision_ref? / eligibility_status?
    target_episode_key?
    snapshot_id? | prediction_failure_ref?
  counts by state
  status: COMPLETED | ABORTED (+ reason)
  started_at / completed_at          # provenance only
```

A manifest is immutable once its status is `COMPLETED` or `ABORTED`. An aborted run is never resumed in place; a new run is started instead.

## Run identity, provenance, and reproduction

Every run manifest records, as applicable:

- the run type and id, and the config with its content digest;
- repository revision and dependency lock;
- the semantic and design versions it implements (decision/context/design references and `prediction_contract_version`);
- exact upstream run references (observation reconstruction, target initialization, resolution run, development run, replay run);
- the source snapshot manifests, carried through upstream manifests;
- the model artifact reference and its development provenance;
- the protocol and partition references (below);
- randomness: run seed and seed-derivation rule;
- the content digests of all produced artifacts.

**Reproduction rule.** Re-executing a declared run creates a new run id. It is a *reproduction* of the earlier run only if every produced artifact's content digest matches: `content_digest` for snapshots, and record-level digests for evaluation units and accounting. If any digest differs, it is a new, unrelated run; the earlier run and its artifacts are never replaced. A reproduction report artifact records the comparison.

## Temporal development versus final-evaluation protocol

### Temporal unit

The partition unit is the **race session**. All driver entries and checkpoints of one race fall on the same side of any boundary. Races are ordered by official race-session start time.

A model artifact's **training cutoff** is a race-session ordinal `c`. Only races whose session concluded before race `c` started may contribute observations, resolved targets, preprocessing statistics, calibration data, or selection evidence (#20 `development_temporal_boundary_ref`).

### Protocol declaration

```text
BacktestProtocol
  protocol_id                       # digest of this declaration
  supported_scope                   # race sessions supported by the #18/#19 verification support matrix
  development_partition             # ordered list of seasons/sessions
  final_partition                   # strictly later than every development session
  development_folds                 # rolling-origin rule (below)
  final_refit_cadence: NONE | PER_SEASON | PER_RACE
  resolution_run_ref                # selects exactly one resolution per episode
  primary_cohort_rule_version       # see Cohort selection
  candidate_scope_rule              # which sessions/drivers/checkpoints are candidates
  declared_at, repository_revision
```

Constraints:

1. `max(development_partition) < min(final_partition)` in race order.
2. The protocol is committed and digested before any final-partition outcome is joined. Changing it creates a new `protocol_id`.
3. Exact seasons are configuration, not design. **Default shape** for the current repository (thesis-era data covering 2018–2023): the latest supported season forms `final_partition`, and all earlier supported seasons form `development_partition`. If the verification support matrix supports fewer than three seasons, the protocol must say so, and the final claim is labeled as low-power. No unsupported season is substituted.

### Development folds (model selection)

Rolling origin by season inside `development_partition`:

```text
for each development season s_k after the first:
    fit candidate procedures on development races before s_k
    replay s_k  -> ReplayRun(role = DEVELOPMENT_VALIDATION, fold = k)
    BacktestRun on that replay
```

Selection among procedures (model family, input view, hyperparameters, calibration, output form, probability floor) may use only fold BacktestRun/ScoreRun results. Non-temporal resampling inside the training races of a fold is allowed as development evidence, but must be labeled as such.

```text
ProcedureSpec
  procedure_id                      # digest
  estimator/config, input_view_version, calibration config, output_form
  fitting rule (how a ModelArtifact is produced given a cutoff)
```

### Locking and final evaluation

```text
EvaluationLock
  lock_id
  protocol_id
  procedure_id                      # chosen from development evidence only
  final_model_artifact_refs[]       # fitted with cutoff = first final race
                                    # (+ later refits per final_refit_cadence)
  selection_evidence_refs[]         # development ScoreRuns that justified the choice
  locked_at
```

Rules:

1. A final-partition `BacktestRun` requires an `EvaluationLock`. The backtest assembly refuses to join final-partition resolutions without one.
2. With `final_refit_cadence ≠ NONE`, every refit follows the locked `ProcedureSpec` with cutoff equal to the evaluated race (or season), so no final race's outcome reaches its own prediction or an earlier one. Refits are listed in the lock or derived deterministically from it, and do not change the procedure.
3. **Final evaluation ledger:** an append-only `FinalEvaluationLedger` per `final_partition` records every final `BacktestRun` (`lock_id`, `procedure_id`, time).
   - The first lock evaluated on a partition is `PRIMARY_FINAL`.
   - Any later lock evaluated on the same partition with a **different** `procedure_id` is `POST_HOC`. Its results are development evidence and may not be reported as a final claim.
   - A reproduction of the same lock is `REPRODUCTION`.
4. A new primary final claim after a procedure change requires a final partition containing races not yet opened in the ledger.

These mechanics implement `contexts/EVALUATION_BACKTESTING.md` §§11–12 without fixing metrics or exact seasons.

### Development dataset assembly

A `DevelopmentRun` builds its training view through the #17 development join, from:

- observations and initializations of races before its cutoff;
- the selected resolutions under `resolution_run_ref`;
- realized outcomes from the #20 mapping, applied with each observation's own `RegionGrid`.

It records, for the training races, the same accounting categories as a backtest. How fitting treats truncated, `MAPPING_UNAVAILABLE`, or set-valued outcomes is a model and statistical choice, recorded in the `ProcedureSpec`. The output is a #20 `ModelArtifact` whose `development_run_ref` and `development_temporal_boundary_ref` point to this run and cutoff.

## Backtest assembly

### Inputs

`BacktestRunConfig`: one completed `ReplayRunManifest`, `protocol_id`, `lock_id` (required when the replay covers the final partition), the role (`DEVELOPMENT_VALIDATION` or `FINAL_EVALUATION`), `resolution_run_ref`, and the mapping version.

### Candidate population

The candidates are every record in the referenced replay manifest whose race session lies in the declared partition and candidate scope. The candidate scope may restrict sessions or driver entries only by attributes fixed **before** the race and declared in the protocol, such as season, session list, or entry list. It may never use target timing, resolution state, prediction values, or error.

### Accounting categories

Each candidate record receives exactly one category. The categories are evaluated in order:

| # | Category | Condition | Scored in primary cohort |
| --- | --- | --- | --- |
| A1 | `NO_CANONICAL_OBSERVATION` | #18 produced no valid canonical observation (indeterminate checkpoint, unsupported source, identity failure) | No |
| A2 | `TARGET_INELIGIBLE` | #19 `INELIGIBLE` | No (not an evaluation unit) |
| A3 | `ELIGIBILITY_INDETERMINATE` | #19 `INDETERMINATE` | No |
| A4 | `PREDICTION_FAILED` | #20 `PredictionFailureRecord` | No (reported as a procedure defect) |
| A5 | `RESOLUTION_MISSING` | no selected resolution under `resolution_run_ref` | No (pipeline defect) |
| A6 | `TRUNCATED` | mapping `NOT_REALIZED` | No |
| A7 | `MAPPING_CONFLICT` | mapping `MAPPING_CONFLICT` | No (reconstruction defect) |
| A8 | `MAPPING_UNAVAILABLE` | mapping `MAPPING_UNAVAILABLE` | No |
| A9 | `SCORED_EVENT_REGION` | `REALIZED_REGION` | Yes |
| A10 | `SCORED_EVENT_REGION_SET` | `REALIZED_REGION_SET` | Yes |
| A11 | `SCORED_TERMINAL_NO_EVENT` | `REALIZED_NO_EVENT` | Yes |

Properties:

- A2 records are counted but are never turned into evaluation units or negatives.
- A6 is never converted to A11, and A8 is never converted to A6 or A11.
- A4, A5, and A7 count as run defects in reports; they are not excluded silently.
- The **primary cohort** is A9 ∪ A10 ∪ A11 (`primary_cohort_rule_version = cohort/v1`). Inclusion depends only on observation validity, causal eligibility, prediction validity, and the canonical resolvability and mapping state. It never depends on realized timing, distance to the pit stop, prediction value, or error. This matches the gates that `contexts/EVALUATION_BACKTESTING.md` §10 permits.
- Every report shows each category's counts per partition, season, race, and driver entry, so outcome-correlated loss (for example truncation concentrated in some races) can be inspected. Statistical sensitivity treatment of A6/A8 is routed to verification.

### Evaluation unit

```text
EvaluationUnit
  evaluation_unit_id                # digest of (backtest_run_id, snapshot_id)
  backtest_run_id
  snapshot_id                       # #20, immutable
  target_episode_key
  target_resolution_artifact_ref    # selected under resolution_run_ref
  realized_outcome                  # #20 RealizedOutcome
  accounting_category               # A9 | A10 | A11
  grouping: GroupingKeys
  partition_role, fold_id?, lock_id?
```

Each eligible snapshot produces exactly one unit. Snapshots are referenced, never copied or modified. Units are never deduplicated because they share an eventual event.

### Grouping metadata

```text
GroupingKeys
  season
  race_event_key
  race_session_key
  driver_entry_key
  driver_race_key = (race_session_key, driver_entry_key)
  checkpoint_completed_laps L
  target_episode_key
  eventual_event_key?               # qualifying_event_ref for OBSERVED_EVENT; retrospective
  event_trajectory_key?             # (driver_race_key, eventual_event_key)
  region_count K_T                  # from RegionGrid, causal
```

- Keys derived from causal inputs (season, race, driver, L, `K_T`) may define primary reporting groups.
- `eventual_event_key`, `event_trajectory_key`, and any distance-to-event value are **retrospective**. They may be used for dependence-aware clustering (for example, repeated forecasts of one stop) and for diagnostics labeled `RETROSPECTIVE_DIAGNOSTIC`. They may never be used for primary cohort inclusion.
- No key implies statistical independence. Weighting, clustering, and uncertainty estimators belong to verification.

### Backtest run manifest

```text
BacktestRunManifest
  backtest_run_id
  config + digest
  replay_run_ref, protocol_id, lock_id?, ledger_entry_ref?, resolution_run_ref, mapping_version
  accounting: per-category counts, overall and per group
  evaluation_unit_refs (or a digest of the unit table)
  record_digests
  status
```

## Scorer plug-in boundary

```text
Scorer
  scorer_id, scorer_version
  declared_population: primary cohort | named subset rule
  declared_grouping_level: unit | episode | driver_race | race | event_trajectory | ...
  score(units: read-only EvaluationUnit set with snapshots) -> ScoreArtifact
```

Rules:

1. A scorer reads `CanonicalDistribution` and `RealizedOutcome`. It cannot change units, outcomes, snapshots, or accounting.
2. A scorer must accept all three scored kinds (A9–A11), or declare explicitly which it does not support. Silently dropping a kind is forbidden, and terminal no-event is scored through `q`, never through an artificial final lap.
3. A pit-window summary may be scored only in a separately labeled secondary analysis. It never replaces the canonical distribution.
4. Every `ScoreArtifact` records the scorer version, `backtest_run_id`, population, grouping level, and `role` (`DEVELOPMENT`, `PRIMARY_FINAL`, `POST_HOC`, `REPRODUCTION`, `RETROSPECTIVE_DIAGNOSTIC`).
5. Which metrics, set-valued outcome scoring, aggregation, and confidence procedures to use is owned by the verification/statistical phase. New scorers plug in without changing units or the protocol.

## Leakage controls

1. **Dependency closure check:** before a replay run starts, its inputs are checked against an allowlist: observation run, initialization run, model artifact, and config. Any resolution, event, mapping, or score reference aborts the run.
2. **Model cutoff check:** the prediction procedure path refuses a model artifact whose training cutoff is not strictly before the earliest replayed race. For per-race refits, the check is per race.
3. **Lock check:** a final-partition backtest without an `EvaluationLock`, or with a protocol digest that does not match, is refused.
4. **Ledger check:** every final backtest writes a ledger entry first, and its role is derived from the ledger, not chosen by the caller.
5. **Cohort rule check:** the primary cohort is recomputed from categories alone and compared with the unit set.

## Minimum audit artifacts

Enough to reproduce or audit a declared claim:

- `BacktestProtocol` and its digest;
- `EvaluationLock`, plus the `FinalEvaluationLedger` excerpt (for final claims);
- the referenced development `ProcedureSpec`s, `DevelopmentRun` manifests, and model artifacts;
- the upstream observation, initialization, and resolution run manifests, and their source manifests;
- the `ReplayRunManifest` (all records, including non-predicted ones);
- the `BacktestRunManifest` with the full accounting table and evaluation unit table;
- the `ScoreArtifact`s with roles;
- a reproduction report, when a reproduction is claimed.

## Scope guards

- Replay never feeds back into observations, eligibility, or snapshots; backtests never feed back into replay runs.
- No live triggers, streaming, or monitoring are defined.
- No metric, estimator, model family, or exact season allocation is fixed. The default allocation shape is configuration.
- No recommendation or optimization semantics are introduced.
- No production code is introduced.

## Unknown routing

| Question | Classification | Owner | Status |
| --- | --- | --- | --- |
| Which seasons/sessions are actually supported for checkpoints and target truth | Cross-slice dependency | Verification support matrices (#18/#19 handoffs) | Unresolved; the protocol consumes it via `supported_scope` |
| `EntryLapContext` adoption (otherwise all observed events are A8) | Cross-slice dependency | #19 amendment, Issue #27; confirmed at #22 | Not yet satisfied |
| Metrics, set-valued outcome scoring, dependence-aware uncertainty, weighting | Later-phase decision | Verification/statistical phase | Deferred |
| Statistical handling of A6/A8 in fitting and sensitivity analysis | Later-phase decision | Verification/statistical + model experimentation | Deferred; accounting is defined here |
| Exact final/development season allocation and refit cadence | Later-phase decision | Verification/experimentation (protocol config) | Shape fixed here; values configurable |
| Serialization, digest algorithm, storage layout, CLI | Later-phase decision | Implementation | Deferred |

There are no unresolved current-scope decisions.

## Verification handoff

The verification baseline must include at least:

1. replay-order determinism, including cross-driver ties and per-driver strictly increasing `L`;
2. a replay dependency-closure fixture: injecting a resolution or score reference aborts the run;
3. a fixture proving that no snapshot changes when a later replay, resolution version, or backtest runs;
4. a model-cutoff refusal fixture (cutoff at or after the replayed race), including per-race refits;
5. lock and ledger fixtures: a final backtest without a lock is refused; a second procedure on the same final partition is labeled `POST_HOC`; the same lock is labeled `REPRODUCTION`;
6. accounting fixtures covering every category A1–A11, mutual exclusivity, and evaluation order;
7. a cohort fixture proving inclusion does not change when realized timing or prediction values are perturbed within the same category;
8. a successive-forecast fixture: two units sharing `eventual_event_key` with distinct `target_episode_key`s, both retained;
9. a reproduction fixture: an identical declared run gives matching digests and a new run id; changed code gives a non-reproduction;
10. a scorer fixture: a scorer that ignores A11 must declare it, and cannot mutate units.

## Acceptance mapping

- **Replay ordering and snapshot generation:** *Replay execution* defines the order, per-checkpoint steps, and manifest. Snapshots are created only by the #20 procedure.
- **Run identity, configuration, and provenance:** run manifests and the provenance list, plus the reproduction rule.
- **Temporal development versus final mechanism:** race-session temporal unit, rolling-origin development folds, `EvaluationLock`, and `FinalEvaluationLedger`.
- **No-peek inclusion:** candidate scope fixed before the race; primary cohort determined by categories only.
- **Ineligible and truncated accounting:** categories A1–A11.
- **Grouping metadata:** `GroupingKeys`, separating causal keys from retrospective keys.
- **Scorer plug-in:** the `Scorer` boundary.
- **Statistical selection routed:** see *Unknown routing*.
- **Live and production out of scope:** see *Scope guards*.
- **Independent review:** pending.

## Product Owner decisions

None required. The protocol shape, lock and ledger, accounting categories, and run contracts are delegated design choices that implement the approved evaluation semantics without changing them.

## Review record

Pending independent full scoped review under `governance/REVIEW_POLICY.md`.
