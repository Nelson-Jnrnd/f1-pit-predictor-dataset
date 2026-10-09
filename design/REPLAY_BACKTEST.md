# V2 Historical Replay and Backtest Execution Contract

## Status

Draft — reworked after the full scoped review on PR #28. Bounded re-review required before approval.

## Abstraction level

Detailed replay/backtest design: replay ordering, prediction-snapshot generation runs, run identity/configuration/provenance, the temporal development versus final-evaluation mechanism, candidate and cohort selection, accounting of non-scored cases, grouping metadata for repeated forecasts, the scorer plug-in boundary, and minimum audit artifacts.

This artifact does not define observation, target, or prediction semantics or their technical contracts (#18–#20), final metrics or statistical estimators, model family/features/hyperparameters, replay UI, live inference, or production code.

## Issue / branch

- Issue: #21 — `Design — historical replay and backtest execution contract`
- Parent: #16
- Upstream: #17 `design/SYSTEM_ARCHITECTURE.md`; #18 `design/OBSERVATION_RECONSTRUCTION.md`; #19 `design/TARGET_RECONSTRUCTION.md`; #20 `design/PREDICTION_CONTRACT.md` (all approved and merged)
- Branch: `ccr-d8f3e250-t7uix3` (session task branch used in place of the suggested `design/replay-backtest-contract`)
- PR: #28

## Outcome

V2 historical evaluation is executed as four kinds of immutable run:

```text
DevelopmentRun   development-allowed observations + selected resolutions -> ModelArtifact(s)
ReplayRun        observations + eligibility + model schedule -> prediction snapshots / failures
BacktestRun      replay run(s) + selected resolutions -> record-level accounting + evaluation units
ScoreRun         one BacktestRun + a versioned scorer -> ScoreArtifact (its own manifest)
```

The temporal protocol is **season-ordered rolling-origin development followed by a locked final holdout whose outcomes are opened at most once per race**:

- prediction-producing choices are made only from development folds, in which every validation race is predicted by models trained on strictly earlier races;
- the chosen procedure, its seeds, and its exact model schedule are frozen in an `EvaluationLock` before any final-partition outcome is joined by any run;
- an append-only `FinalEvaluationLedger`, keyed by **race session**, records every opening of a final-partition outcome. Only the first locked evaluation of a race can be its primary final evidence.

The evaluation unit stays the #20 `PredictionSnapshot` joined to the selected #19 resolution of its own `target_episode_key`. Every candidate checkpoint gets exactly one record-level accounting category. Per-record exclusions are limited to causal gates and truncation. Missing or unmappable outcome data is treated as a run-validity defect, never as a silent cohort filter.

## Upstream locks consumed unchanged

- `contexts/EVALUATION_BACKTESTING.md` — replay versus backtest, the atomic prediction-target unit, entry conditions, end-to-end point-in-time legitimacy, observed-event, terminal no-event and truncation comparison semantics, repeated-forecast identity, no outcome-peeking cohort selection (§10), development versus final separation (§§11–12), declared protocol, and reproducibility.
- `contexts/PREDICTION_OUTPUT_REPLAY.md` and `decisions/2026-09-09-v2-prediction-output-semantics.md` — immutable successive snapshots; complete distribution plus terminal no-event; truncation is not a prediction category.
- `design/SYSTEM_ARCHITECTURE.md` — replay coordinates but never creates prediction contents. Development assembly and backtest assembly are the only controlled joins with retrospective truth. Rerunning creates new runs.
- `design/OBSERVATION_RECONSTRUCTION.md` — `RaceSessionKey`, `DriverEntryKey`, `CheckpointKey`, checkpoint boundaries, observation quality states, and source-authority support.
- `design/TARGET_RECONSTRUCTION.md` — `EligibilityDecision`, `TargetEpisodeInitialization`, resolution states, `event_key`, and exactly one selected `TargetResolutionArtifact` per episode per declared `resolution_run_ref`.
- `design/PREDICTION_CONTRACT.md` — `PredictionSnapshot` (`prediction_key`, `content_digest`, `request_digest`), `PredictionFailureRecord`, `RegionGrid`, the declared deterministic tolerance, and the realized-target mapping kinds.

## Temporal reference

- Races are ordered by official race-session start time. A race is identified by its `RaceSessionKey`.
- A model artifact's **training cutoff** is a `RaceSessionKey` `c`, with start time `t(c)`. It is **exclusive**: only races whose session concluded before `t(c)` may contribute observations, resolved targets, preprocessing statistics, calibration data, or selection evidence. This value fills #20 `development_temporal_boundary_ref`.
- A model with cutoff `c` may predict race `r` only if `t(c) ≤ t(r)`. In particular, cutoff `c = r` (trained on everything before `r`) is valid for predicting `r`.

This single convention is used by the lock, refits, leakage control 2, and verification item 4.

## Protocol

```text
BacktestProtocol
  protocol_id                       # digest of this declaration
  supported_scope                   # race sessions supported by the #18/#19 verification support
                                    # matrices, including EntryLapContext support (Issue #27)
  candidate_scope_rule              # pre-race attributes only (season, session list, entry list)
  development_partition             # ordered race sessions
  final_partition                   # every race strictly later than all development races
  development_fold_rule             # see Development folds
  final_refit_cadence: NONE | PER_SEASON | PER_RACE
  resolution_run_ref                # selects exactly one resolution per episode
  primary_cohort_rule_version       # cohort/v2
  prior_exposure[]                  # known earlier uses of final-partition races (see below)
  declared_at, repository_revision
```

Constraints:

1. `development_partition`, `final_partition` ⊆ `supported_scope`, and every development race precedes every final race.
2. The protocol is committed and digested before any final-partition outcome is opened. Changing it creates a new `protocol_id`; it does not reset the ledger (see *Ledger*).
3. A final partition is valid for a new primary claim only if **every** race in it is unopened in the ledger.
4. **Prior exposure.** The protocol lists known earlier exposure of final-partition races to prediction-producing choices: thesis-era work (which used random season-mixing splits over the 2018–2023 data in `data/`, per `legacy/THESIS_EVIDENCE.md`), exploratory notebooks, and so on. If the list is non-empty, every final claim carries the qualifier `PRIOR_EXPOSURE_DECLARED`.
5. **Default allocation shape** (configuration, not design): prefer a final partition made of supported seasons absent from thesis-era data (2024 or later) when the support matrices cover them. Otherwise use the latest supported season, with prior exposure declared. All earlier supported seasons form the development partition. Unsupported seasons are never substituted.

### Development folds

`development_fold_rule` is one of:

- `ROLLING_SEASON` (default when the development partition spans at least 3 supported seasons). For each development season `s_k` after the first, fit with cutoff = the first race of `s_k`, and validate on all races of `s_k`.
- `ROLLING_RACE_BLOCK` (fallback for 2 seasons, or 1 season). The development races are split into consecutive blocks of a declared size `b`. Each block is validated by models with cutoff = the block's first race, starting from a declared minimum training block.
- `PRESPECIFIED`. No selection is performed: a single `ProcedureSpec` is fixed before any development outcome is examined, and `selection_evidence_refs` is empty by declaration. Required when fewer development races exist than the declared minimum.

The fold rule, `b`, and minimums are part of the protocol digest. A protocol with fewer than three supported development seasons carries the qualifier `LOW_POWER`.

## Run contracts

### Common provenance

Every run manifest records, as applicable:

- run type and id, and the config with its digest;
- repository revision and dependency lock;
- `protocol_id`, `partition_role` (`DEVELOPMENT_FIT`, `DEVELOPMENT_VALIDATION`, `FINAL_REFIT`, `FINAL_EVALUATION`), `fold_id?`, and `lock_id?`;
- semantic and design versions (decision/context/design references, `prediction_contract_version`, mapping version);
- exact upstream run references (observation reconstruction, target initialization, resolution run, development runs, replay runs);
- source snapshot manifests, carried through upstream manifests;
- every seed (fit seeds, inference seed policy) and the seed-derivation rule;
- content digests of all produced artifacts.

### ProcedureSpec

```text
ProcedureSpec
  procedure_id                      # digest
  estimator/config, input_view_version, calibration config, output_form
  fitting rule: how a ModelArtifact is produced given a cutoff
  fit_seed_rule, inference_seed_policy
  handling of truncated / set-valued outcomes in fitting
```

### DevelopmentRun

```text
DevelopmentRunConfig
  protocol_id, partition_role (DEVELOPMENT_FIT | FINAL_REFIT), fold_id?, lock_id?
  procedure_id
  cutoff c
  training_races                    # all races r with t(r) concluded before t(c), within supported_scope
  observation/initialization run refs, resolution_run_ref, mapping version
```

The development join (#17 rule 7) enforces:

1. Every training race has concluded before `t(c)`.
2. If any training race is in the protocol's `final_partition`, the run must be `FINAL_REFIT` and must reference a `lock_id` whose procedure and seeds it uses. Before a lock exists, final-partition races are refused.
3. Every final-partition race it reads is recorded in the ledger as an opening (`FINAL_REFIT_TRAINING`) before the join executes.

It produces record-level development accounting (see *Development categories*) and a #20 `ModelArtifact` with `development_run_ref` and `development_temporal_boundary_ref = c`.

### ReplayRun

```text
ReplayRunConfig
  protocol_id, partition_role (DEVELOPMENT_VALIDATION | FINAL_EVALUATION), fold_id?, lock_id?
  replay_scope: list of RaceSessionKey
  model_schedule: RaceSessionKey -> model_artifact_ref   # one entry per race; constant if no refit
  observation_reconstruction_run_ref
  target_initialization_run_ref
  inference_seed_policy
  prediction_contract_version
  repository_revision, dependency_lock_ref
```

Rules:

- **Direct-input allowlist:** the run's direct inputs may be only the observation run, the initialization run, the model artifacts in `model_schedule`, and the config. A model artifact's own provenance legitimately references development resolutions; that is not a direct input. Any direct reference to a resolution, event, mapping, backtest, or score aborts the run.
- **Per-race cutoff check:** for every race `r` in scope, `t(cutoff(model_schedule[r])) ≤ t(r)`.
- **Final evaluation:** `model_schedule` must equal the lock's `final_model_schedule` exactly.

#### Ordering

Manifest records use the total order `(race_session_key, driver_entry_key, checkpoint_key.completed_laps)`. This order does not depend on `T`, so it also covers attempts that have no canonical observation.

For a chronological replay stream (presentation and audit), records with a canonical observation are ordered within a session by the prediction boundary `T`:

- comparable exact values are ordered numerically;
- bounded values are ordered by `(upper bound, lower bound)`;
- remaining ties are broken by the manifest key.

For one driver entry, both orders give strictly increasing `completed_laps`. Every prediction depends only on its own observation (#20 input boundary), so cross-driver order never affects prediction contents.

#### Per-checkpoint step

For each attempted checkpoint record of the referenced #18 run:

1. If there is no canonical observation, record the #18 state.
2. Otherwise read the #19 decision. If there is no decision, or the decision is `ELIGIBLE` but has no `TargetEpisodeInitialization`, record an upstream-linkage defect.
3. If the decision is `INELIGIBLE` or `INDETERMINATE`, record it. No prediction is requested.
4. If it is `ELIGIBLE`, call the #20 prediction procedure with the observation, the initialization, `model_schedule[r]`, and the seed derived from the policy.
5. Record the returned `snapshot_id` or `PredictionFailureRecord` reference. Earlier records are never revisited.

Each replay run has exactly one `prediction_run_ref`, equal to its `replay_run_id`.

```text
ReplayRunManifest
  replay_run_id, config + digest
  records[] (manifest order):
    semantic_observation_key, observation_artifact_ref?, observation_quality_status
    eligibility_decision_ref?, eligibility_status?, target_episode_key?
    model_artifact_ref?, snapshot_id? | prediction_failure_ref?
  status: COMPLETED | ABORTED (+ reason)      # aborted runs are never resumed in place
```

**Cross-slice dependency (#18):** this step requires the #18 run manifest to list every attempted checkpoint, with its semantic key and failure state, not only counts and emitted IDs. This is recorded for confirmation at #22.

### BacktestRun

```text
BacktestRunConfig
  protocol_id, partition_role (DEVELOPMENT_VALIDATION | FINAL_EVALUATION), fold_id?, lock_id?
  replay_run_refs[]                 # one or more, same lock/fold; together cover the scope
  resolution_run_ref, mapping_version
```

The backtest join (#17 rule 8) enforces:

1. **Coverage:** the union of replay scopes equals `partition ∩ supported_scope ∩ candidate scope` (for a fold, its validation races). A missing race is a run-validity defect.
2. **Final gating:** for `FINAL_EVALUATION`, a lock is required, every replay must carry the lock's model schedule, and the ledger openings are written **before** any final-partition resolution is read. The ledger assigns the role; the caller does not.

Outputs: record-level accounting, evaluation units, and the manifest.

```text
BacktestRunManifest
  backtest_run_id, config + digest
  ledger_entry_refs[]               # FINAL_EVALUATION only
  run_validity: VALID | DEFECTIVE (+ defect counts)
  accounting_table_ref              # one row per candidate record (below)
  evaluation_unit_table_ref
  per-category counts, overall and per group
  record_digests (semantic-keyed; see Reproduction)
  qualifiers: LOW_POWER?, PRIOR_EXPOSURE_DECLARED?
```

### ScoreRun

A `ScoreRun` has no separate manifest: its manifest is the `ScoreArtifact` (see *Scorer plug-in boundary*).

## Evaluation lock and ledger

```text
EvaluationLock
  lock_id
  protocol_id
  procedure_id                      # chosen from development evidence only (or PRESPECIFIED)
  seeds: fit seeds + inference seed policy
  final_model_schedule              # RaceSessionKey -> ModelArtifact or deterministic refit rule
  selection_evidence_refs[]         # development ScoreRuns that justified the choice
  locked_at
```

With `final_refit_cadence ≠ NONE`, refits use the lock's procedure and seeds with cutoff = the predicted race (or the first race of its season). Every refit is a `FINAL_REFIT` `DevelopmentRun` that references the lock. Refits are reproducible from the lock and do not change the procedure.

```text
FinalEvaluationLedger               # append-only, keyed by RaceSessionKey
  entry
    race_session_key
    opening_kind: FINAL_EVALUATION | FINAL_REFIT_TRAINING | AD_HOC_OPENING
    lock_id?, protocol_id?, run_ref?
    resolution_run_ref
    label (assigned by the ledger)
    recorded_at
```

Labels for `FINAL_EVALUATION` openings of race `r`:

| Condition | Label |
| --- | --- |
| first `FINAL_EVALUATION` of `r`, and no earlier `AD_HOC_OPENING` of `r` | `PRIMARY_FINAL` |
| same lock as the primary, same `resolution_run_ref`, and record contents equal to the primary under the reproduction rule | `REPRODUCTION` |
| same lock as the primary, different `resolution_run_ref` declared as a resolution correction | `RESOLUTION_REEVALUATION`, reported alongside the primary and never replacing it |
| anything else (different lock, procedure, seeds, schedule, or non-matching contents) | `POST_HOC` (development evidence) |
| first evaluation of `r` after an `AD_HOC_OPENING` of `r` | `POST_HOC` |

Rules:

- `FINAL_REFIT_TRAINING` openings of race `r` are legitimate only when the refit cutoff is later than `r`, under the same lock. They do not change `r`'s label.
- Final-partition resolution artifacts are accessed only through the backtest and development joins. Any other read (notebooks, exploratory analysis) must be registered as an `AD_HOC_OPENING` before it happens. Unregistered access is a protocol violation, and the affected races must be treated as opened.
- A race's label is determined by its own ledger history. Redefining partitions or protocols cannot reset it.

## Accounting

### Backtest categories

Every candidate record gets exactly one category. The categories are evaluated in order:

| # | Category | Condition | Class |
| --- | --- | --- | --- |
| A0 | `UPSTREAM_LINKAGE_DEFECT` | canonical observation without a decision, or `ELIGIBLE` without an initialization | run defect |
| A1 | `NO_CANONICAL_OBSERVATION` | #18 produced no valid canonical observation | causal exclusion |
| A2 | `TARGET_INELIGIBLE` | #19 `INELIGIBLE` | causal exclusion (not an evaluation unit) |
| A3 | `ELIGIBILITY_INDETERMINATE` | #19 `INDETERMINATE` | causal exclusion |
| A4 | `PREDICTION_FAILED` | #20 `PredictionFailureRecord` | causal exclusion (procedure defect, reported) |
| A5 | `RESOLUTION_MISSING` | no selected resolution under `resolution_run_ref` | run defect |
| A6 | `TRUNCATED` | mapping `NOT_REALIZED` | resolvability exclusion |
| A7 | `MAPPING_CONFLICT` | mapping `MAPPING_CONFLICT` | run defect |
| A8 | `MAPPING_UNAVAILABLE` | mapping `MAPPING_UNAVAILABLE` | run defect |
| A9 | `SCORED_EVENT_REGION` | `REALIZED_REGION` | primary cohort |
| A10 | `SCORED_EVENT_REGION_SET` | `REALIZED_REGION_SET` | primary cohort |
| A11 | `SCORED_TERMINAL_NO_EVENT` | `REALIZED_NO_EVENT` | primary cohort |

### Primary cohort (`cohort/v2`)

- **Per-record exclusions** are only:
  - the causal gates A1–A4: observation validity, eligibility, and prediction validity, all fixed at `T`;
  - the resolvability gate A6 (truncation).
  
  These are exactly the gates that `contexts/EVALUATION_BACKTESTING.md` §10 permits.
- **A0, A5, A7, and A8 are not cohort filters.** They are run-validity defects. A backtest run with any of them in scope is `DEFECTIVE`, and none of its scores may carry analysis class `PRIMARY`. Because A7 and A8 can occur only for observed events, filtering them per record would select by outcome type.
- To evaluate despite such defects, races or eras must be removed beforehand through `supported_scope`, for example by the `EntryLapContext` support matrix. They are never removed record by record.
- The primary cohort of a `VALID` run is A9 ∪ A10 ∪ A11. It is recomputed from the categories and checked against the unit table.
- **Comparing procedures:** comparisons use the intersection of their scored records, or report A4 counts alongside the scores.

### Record-level accounting table

One row per candidate record:

```text
semantic_observation_key, grouping keys, category, observation_artifact_ref?,
target_episode_key?, snapshot_id?, prediction_failure_ref?,
target_resolution_artifact_ref?, resolution_state?, realized_outcome_kind?
```

Statistical sensitivity treatment of A6 and other analyses operate on this table.

### Development categories

Development runs use the same table, with these differences:

- A4 is replaced by `GRID_UNAVAILABLE` (no legitimate `N_T`, so no `RegionGrid` can be built);
- no snapshot column.

How fitting treats A6 or set-valued outcomes is recorded in the `ProcedureSpec`. A0, A5, A7, and A8 in training races are reported as defects.

### Evaluation unit

```text
EvaluationUnit
  evaluation_unit_id                # run-scoped
  backtest_run_id
  snapshot_id                       # #20, immutable, referenced not copied
  target_episode_key
  target_resolution_artifact_ref
  realized_outcome                  # #20 RealizedOutcome
  accounting_category               # A9 | A10 | A11
  grouping: GroupingKeys
```

Units exist only for A9–A11, one per such record. They are never deduplicated because they share an eventual event.

### Grouping metadata

```text
GroupingKeys
  season, race_session_key          # #18 RaceSessionKey; one race per event in scope
  driver_entry_key
  driver_race_key = (race_session_key, driver_entry_key)
  checkpoint_completed_laps L
  region_count K_T                  # from RegionGrid
  target_episode_key
  eventual_event_key?               # #19 event_key, OBSERVED_EVENT only
  event_trajectory_key              # (driver_race_key, eventual_event_key) for events;
                                    # (driver_race_key, TERMINAL) for terminal no-event
```

- Causal keys (season, race, driver, `L`, `K_T`) may define primary reporting groups.
- `eventual_event_key`, `event_trajectory_key`, and distance-to-event are retrospective. They may be used for dependence-aware clustering and for `RETROSPECTIVE_DIAGNOSTIC` analyses, never for primary inclusion.
- No key implies independence. Weighting, clustering, and uncertainty estimators belong to verification.

## Reproduction rule

A re-executed run gets a new run id. It is a reproduction of an earlier run only if, after removing run-scoped identifiers (`run ids`, `snapshot_id`, `evaluation_unit_id`, `prediction_run_ref`) and keying records by semantic keys (`semantic_observation_key`, `target_episode_key`), the following all hold:

- the record sets are identical;
- the categories are identical;
- the resolution references are identical;
- each prediction's `request_digest` is equal;
- each prediction's distribution is equal within #20's declared deterministic tolerance.

A reproduction report artifact records the comparison. A non-matching re-execution is a new, unrelated run; nothing earlier is replaced.

## Scorer plug-in boundary

```text
Scorer
  scorer_id, scorer_version
  supported_kinds ⊆ {A9, A10, A11}
  declared_population: primary cohort | named subset rule
  declared_grouping_level
  score(read-only accounting + units + snapshots) -> ScoreArtifact

ScoreArtifact                       # also the ScoreRun manifest
  score_run_id, scorer_version, backtest_run_id, population, grouping level
  ledger_role: DEVELOPMENT | PRIMARY_FINAL | REPRODUCTION | RESOLUTION_REEVALUATION | POST_HOC
  analysis_class: PRIMARY | SECONDARY | RETROSPECTIVE_DIAGNOSTIC
  qualifiers: LOW_POWER?, PRIOR_EXPOSURE_DECLARED?
  results
```

Rules:

1. A scorer reads the canonical distribution and the realized outcome. It cannot change units, outcomes, snapshots, or accounting.
2. `analysis_class = PRIMARY` requires all of:
   - `supported_kinds = {A9, A10, A11}`;
   - the population is the full primary cohort;
   - the backtest run is `VALID`.
   
   Terminal no-event is then scored through `q`, never through an artificial final lap.
3. A scorer that omits a kind, or uses a subset defined by outcomes, is forced to `SECONDARY` (an outcome-free subset rule) or `RETROSPECTIVE_DIAGNOSTIC` (an outcome-defined subset).
4. Pit-window summaries may be scored only as `SECONDARY` and never replace the canonical distribution.
5. `ledger_role` is copied from the ledger labels of the races in the run. A run mixing labels reports per-label results.
6. Metrics, set-valued outcome scoring, aggregation, and confidence procedures are owned by verification/statistics. New scorers plug in without changes here.

## Leakage controls

1. **Replay direct-input allowlist** (see *ReplayRun*).
2. **Per-race cutoff check** using the single convention `t(cutoff) ≤ t(r)`.
3. **Lock check:** a final backtest requires a lock, a matching protocol digest, and replays whose model schedule equals the lock's.
4. **Development-join check:** final-partition races are refused before a lock exists, and require `FINAL_REFIT` with the lock after it.
5. **Ledger-first:** every final-partition resolution read through a join writes its ledger opening first. Ad hoc reads must be registered.
6. **Coverage check:** final backtest replays cover the declared scope.
7. **Cohort check:** the primary cohort is recomputed from categories, and run validity from defect categories.

## Minimum audit artifacts

- `BacktestProtocol` (including `prior_exposure`) and its digest;
- `EvaluationLock`, the `ProcedureSpec`s, and the full ledger history of every race in the claim;
- `DevelopmentRun` manifests, model artifacts, and refit runs;
- upstream observation, initialization, and resolution run manifests, and their source manifests;
- all `ReplayRunManifest`s, with every record;
- the `BacktestRunManifest`, the record-level accounting table, and the evaluation unit table;
- the `ScoreArtifact`s with ledger role, analysis class, and qualifiers;
- reproduction reports when a reproduction is claimed.

## Scope guards

- Replay never feeds back into observations, eligibility, or snapshots; backtests never feed back into replay runs.
- No live triggers, streaming, or monitoring are defined.
- No metric, estimator, model family, or exact season allocation is fixed; the allocation shape and fold rules are configuration.
- No recommendation or optimization semantics are introduced.
- No production code is introduced.

## Unknown routing

| Question | Classification | Owner | Status |
| --- | --- | --- | --- |
| Supported seasons/sessions for checkpoints, target truth, and lap-at-entry | Cross-slice dependency | Verification support matrices (#18/#19 handoffs; Issue #27) | Unresolved; consumed via `supported_scope` |
| Per-attempt checkpoint records in the #18 run manifest | Cross-slice dependency | #18; confirmed at #22 | Required guarantee stated here |
| `EntryLapContext` adoption | Cross-slice dependency | #19 amendment, Issue #27; confirmed at #22 | Not yet satisfied; without it, in-scope runs are `DEFECTIVE` (A8) |
| Metrics, set-valued outcome scoring, dependence-aware uncertainty, weighting | Later-phase decision | Verification/statistical phase | Deferred |
| Statistical handling of A6 in fitting and sensitivity analysis | Later-phase decision | Verification/statistics + model experimentation | Deferred; record-level table provided |
| Exact season allocation, block size, minimums, refit cadence | Later-phase decision | Verification/experimentation (protocol config) | Shape fixed here; values configurable |
| Serialization, digest algorithm, storage layout, CLI, access control for the gated joins | Later-phase decision | Implementation | Deferred |

There are no unresolved current-scope decisions.

## Verification handoff

The verification baseline must include at least:

1. manifest-order and chronological-order determinism, including bounded `T`, ties, and attempts without an observation;
2. direct-input allowlist fixtures: a direct resolution reference aborts the run; a model artifact provenance link does not;
3. a fixture proving no snapshot changes when later replays, resolution versions, or backtests run;
4. cutoff fixtures under `t(cutoff) ≤ t(r)`: `cutoff = r` accepted, cutoff after `r` refused, checked per race with `PER_RACE` schedules;
5. lock and ledger fixtures: no lock refused; first evaluation `PRIMARY_FINAL`; a matching rerun `REPRODUCTION`; a non-matching rerun or reseeded rerun under the same lock `POST_HOC`; a new protocol over opened races `POST_HOC`; a partition with one fresh race rejected for a new primary claim; an ad hoc opening making a later evaluation `POST_HOC`; a resolution correction labelled `RESOLUTION_REEVALUATION`;
6. a development-join fixture: final-partition races are refused before a lock, and a `FINAL_REFIT` records its openings;
7. accounting fixtures for A0–A11 and the development categories: exhaustiveness, mutual exclusivity, and order;
8. a cohort fixture: inclusion is unchanged under perturbations of realized timing or prediction values; a nonzero A8 (or A5, A7, A0) count marks the run `DEFECTIVE` and blocks `PRIMARY` scores;
9. a successive-forecast fixture: units sharing `eventual_event_key` with distinct `target_episode_key`s are both retained;
10. reproduction fixtures: semantic-keyed comparison, tolerance boundary, and a new run id;
11. scorer fixtures: a scorer omitting A11 cannot produce `PRIMARY`; an outcome-defined subset is forced to `RETROSPECTIVE_DIAGNOSTIC`;
12. a coverage fixture: a missing final race marks the run `DEFECTIVE`.

## Acceptance mapping

- **Replay ordering and snapshot generation:** *ReplayRun* covers manifest and chronological order, the per-checkpoint step, and the model schedule. Snapshots are created only by #20.
- **Run identity, configuration, and provenance:** common provenance, run contracts, and the semantic-keyed reproduction rule.
- **Temporal development versus final mechanism:** the single cutoff convention, fold rules with fallbacks, the gated development and backtest joins, the lock with seeds and schedule, the per-race ledger, and prior-exposure declaration.
- **No-peek inclusion:** per-record exclusions only for causal gates and truncation; outcome-data defects are run validity; candidate scope uses pre-race attributes.
- **Ineligible and truncated accounting:** A2 and A6, plus the record-level table.
- **Grouping metadata:** `GroupingKeys`, with causal keys separate from retrospective keys.
- **Scorer plug-in:** two-dimensional role, plus the PRIMARY requirements.
- **Statistical selection routed:** see *Unknown routing*.
- **Live and production out of scope:** see *Scope guards*.
- **Independent review:** full scoped review FAIL; rework complete; bounded re-review pending.

## Product Owner decisions

None required. The protocol shape, lock and ledger, accounting categories, and run contracts are delegated design choices that implement the approved evaluation semantics without changing them.

## Review record

### Full scoped review — FAIL, rework required

- PR: #28
- Reviewer: independent review agent; recorded on PR #28 as a `COMMENT` review through the connected account
- Date: 2026-10-09
- Outcome: **FAIL — rework required**
- Blocking: contradictory training-cutoff convention.
- Major:
  - per-race/per-season refits were not expressible;
  - the ledger could be gamed;
  - final outcomes were gated only at the backtest join, and prior exposure was undeclared;
  - per-record A5/A7/A8 exclusions exceeded the §10 gates;
  - scorers could produce primary-labelled scores on outcome-selected subsets.
- Minor: incomplete categories and count-only accounting; dependence of ordering on `T` and on #18 per-attempt records; reproduction digests depending on run ids; grouping-key ownership; no fallback for few seasons; allowlist scope, role naming, and coverage check.
- Product Owner decision: none required.

### Rework

1. One exclusive cutoff convention, `t(cutoff) ≤ t(r)`, used everywhere.
2. Replay `model_schedule` per race, matched against the lock; backtests accept multiple replay runs; `partition_role` and fold fields added.
3. Ledger keyed by race session, with labels assigned by the ledger (including `REPRODUCTION` only on verified match, `RESOLUTION_REEVALUATION`, and `AD_HOC_OPENING`); seeds in `ProcedureSpec` and the lock; a new primary claim requires all-unopened races.
4. `DevelopmentRun` contract with a protocol reference, refusal of final-partition races before the lock, `FINAL_REFIT` openings, and a `prior_exposure` declaration and qualifier.
5. A0/A5/A7/A8 reclassified as run-validity defects (`DEFECTIVE` runs cannot produce `PRIMARY` scores); exclusions by scope only.
6. Two-dimensional score role (ledger role × analysis class), with PRIMARY requiring all kinds and the full cohort.
7. A0 linkage category, record-level accounting table, development categories, and corrected unit wording.
8. Manifest order independent of `T`; bounded-`T` chronological rule; #18 per-attempt records routed.
9. Semantic-keyed reproduction honouring #20's tolerance.
10. Grouping keys aligned to #18/#19 owners; terminal trajectory key.
11. `ROLLING_RACE_BLOCK` and `PRESPECIFIED` fallbacks and the `LOW_POWER` qualifier.
12. Direct-input allowlist wording, `partition_role` rename, and coverage check; `ScoreArtifact` as the `ScoreRun` manifest.

### Bounded re-review

Required under `governance/REVIEW_POLICY.md`.
