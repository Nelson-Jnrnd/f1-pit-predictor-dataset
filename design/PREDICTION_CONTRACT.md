# V2 Prediction Distribution and Model-Facing Contract

## Status

Draft — authored for Issue #20. Independent full scoped review required before approval.

## Abstraction level

Detailed prediction/model-interface design: timing-region representation, probability normalization and validity invariants, realized-target-to-region mapping, model-facing input/output boundary, model and prediction artifact identity/versioning, and exact pit-window derivation.

This artifact does not define observation reconstruction, target-event semantics or reconstruction, replay/backtest orchestration, headline metrics or statistical procedures, model family/features/loss/calibration, live inference, or production implementation.

## Issue / branch

- Issue: #20 — `Design — prediction distribution and model-facing contract`
- Parent: #16
- Upstream architecture: #17 / `design/SYSTEM_ARCHITECTURE.md`
- Upstream observation design: #18 / `design/OBSERVATION_RECONSTRUCTION.md`
- Upstream target design: #19 / `design/TARGET_RECONSTRUCTION.md` (approved; merged via PR #25)
- Branch: `ccr-d8f3e250-t7uix3` (session task branch used in place of the suggested `design/prediction-contract`)

## Outcome

One V2 prediction is a **finite, explicitly normalized probability vector** over:

1. `K_T` mutually exclusive **driver-lap timing regions** `R_0 … R_{K_T−1}`, indexed by how many further official race laps the selected driver has completed when the next qualifying pit entry occurs; the final region is **open-ended**; and
2. one explicit **terminal no-event** outcome.

Because the final region is open-ended and every in-scope pit entry has a well-defined non-negative lap offset, the regions cover every semantically possible next-event timing inside the target-at-risk interval `(T, B)` by construction. There is no residual "after horizon" class and no truncation class.

The model-facing boundary is a pure function from a causal **prediction request** (observation-derived input view + region grid) to a **raw distribution** in one of two declared output forms. The prediction procedure alone validates that output, converts it to the canonical form, and creates an immutable **prediction snapshot**. The consumer-facing pit window is derived from the snapshot by one exact, versioned rule and always reports the probability outside the window.

## Upstream locks consumed unchanged

- `decisions/2026-09-09-v2-prediction-output-semantics.md` and `contexts/PREDICTION_OUTPUT_REPLAY.md` — complete remaining-target-scope distribution, explicit terminal no-event probability, normalization at semantic level, no hidden finite-horizon residual, pit window as a non-exclusive summary, truncation not a prediction category, immutable successive snapshots, predictive not prescriptive.
- `contexts/PIT_EVENT_TARGET.md`, `decisions/2026-09-08-v2-pit-event-scope.md`, and `design/TARGET_RECONSTRUCTION.md` — target is the first tyre-service pit entry strictly after `T` and strictly before terminal boundary `B`; pit-entry occurrence (exact or bounded) is the timing anchor; resolution states `OBSERVED_EVENT`, `TERMINAL_NO_EVENT`, `TRUNCATED_INDETERMINATE`; episode identity is observation-owned; one selected resolution artifact per declared resolution run.
- `contexts/RACE_OBSERVATION_STATE.md` and `design/OBSERVATION_RECONSTRUCTION.md` — driver-relative checkpoint lap `L` (`0` for race start), prediction boundary `T`, immutable `CanonicalObservation`, and the rule that model-facing representations derive only from canonical observation state.
- `design/SYSTEM_ARCHITECTURE.md` — the prediction procedure is the sole creator of prediction snapshots; its inputs are one canonical observation, one eligible `TargetEpisodeInitialization`, and one fixed model artifact; retrospective target resolution is outside the forecast-time dependency closure.

## Timing-region representation

### Race-progression axis

The axis is the **selected driver's official completed race-lap count at the occurrence of the qualifying pit entry**, written `c(E)`.

This axis is chosen because:

- it is the same driver-relative lap ordinal that defines V2 checkpoints, so region boundaries align with the replay checkpoint cadence;
- it is the consumer-meaningful unit ("pits at the end of lap N"; the in-lap ordinal is `c(E) + 1`);
- it is retrospectively determinable from race evidence without requiring prediction-time availability authority;
- it is integer-valued and monotone in session time, which makes the partition exact.

Session-clock time, fuel/tyre age, or other continuous axes are not used as the canonical partition. A model may use any of them internally (see *Experimentation-owned choices*).

### Region grid for one prediction

For an observation at checkpoint lap `L` with prediction boundary `T`:

```text
N_T  = scheduled race distance in laps, as legitimately represented in the
       CanonicalObservation at T (latest known version at T)
K_T  = max(1, N_T − L)

h(E) = c(E) − L                         # lap offset of the pit entry, h(E) ≥ 0

R_j  = { E : h(E) = j }      for 0 ≤ j < K_T − 1
R_{K_T−1} = { E : h(E) ≥ K_T − 1 }      # final region, open-ended
```

Plain-language reading: `R_0` is "pit entry during the lap the driver is currently on (in-lap `L+1`)"; `R_j` is "in-lap `L+j+1`"; the final region is "in-lap `L+K_T` (the last scheduled lap) or later".

```text
RegionGrid
  region_representation_version   # "driver-lap-offset/v1"
  checkpoint_lap L
  scheduled_distance_fact_ref      # observation fact supplying N_T
  N_T
  K_T
```

The grid is a deterministic function of `(L, N_T, region_representation_version)`. It is computed by the prediction procedure, not chosen by the model.

### Coverage proof

Let `E` be any pit entry that could be the target of the episode, i.e. `T < E < B`.

1. `T` is the availability instant of the selected driver's lap-`L` completion (or of race start when `L = 0`), so the lap-`L` completion occurred no later than `T`.
2. Official completed-lap counts are monotone non-decreasing in session time, so `c(E) ≥ L` and `h(E) ≥ 0`.
3. `h(E)` is an integer. If `h(E) < K_T − 1`, `E` is in exactly one of `R_0 … R_{K_T−2}`; otherwise it is in `R_{K_T−1}`.

Therefore `{R_0, …, R_{K_T−1}}` is a partition of every possible target timing in `(T, B)`, independent of whether `N_T` later changes (shortened race, red-flag classification, lapped finish) and independent of when `B` occurs. The terminal no-event outcome covers the complement: no qualifying entry in `(T, B)`. The `K_T + 1` outcomes are mutually exclusive and collectively exhaustive.

`N_T` affects only resolution (how many single-lap regions exist before the open final region), never completeness.

### Missing scheduled distance

If the canonical observation does not represent a legitimate scheduled-race-distance fact, the prediction procedure does not invent one. It records a `PredictionFailureRecord` with reason `REQUIRED_CONTEXT_MISSING` and creates no snapshot. This is a prediction-run failure, not a race outcome. (Cross-slice dependency on #18, see *Unknown routing*.)

## Canonical probability representation

```text
CanonicalDistribution
  region_grid: RegionGrid
  event_region_probabilities: p[0 .. K_T−1]   # float64
  terminal_no_event_probability: q            # float64
```

### Invariants

A canonical distribution is valid if and only if all hold:

| Code | Invariant |
| --- | --- |
| `V1_FINITE` | every `p_j` and `q` is a finite real number (no NaN/±Inf) |
| `V2_RANGE` | `0 ≤ p_j ≤ 1` and `0 ≤ q ≤ 1` |
| `V3_GRID_LENGTH` | `len(p) == K_T` and `K_T == max(1, N_T − L)` for the grid's own `L`, `N_T` |
| `V4_NORMALIZED` | `abs(sum(p) + q − 1) ≤ 1e-9` |
| `V5_NO_EVENT_PRESENT` | `q` is explicitly present (an absent value is never interpreted as `0`) |
| `V6_NO_EXTRA_OUTCOMES` | no additional outcome (truncation, "after horizon", "unknown", ineligible) is present |
| `V7_GRID_MATCH` | the grid's `L` equals the observation's `selected_driver_completed_laps`, and `N_T` is read from the referenced observation fact |

Normalization is exact in intent: the prediction procedure may apply one declared conversion/normalization step (see *Output adapters*) **before** validation, recorded by adapter version. The validator never repairs a distribution; failing any invariant produces a `PredictionFailureRecord`, not a snapshot.

Exact zero probabilities are structurally permitted. Whether a model must apply a probability floor (for example to keep logarithmic scores finite) is an experimentation/verification choice, not a contract invariant.

### Derived quantities

These are pure functions of the canonical distribution and are not stored as independent truths:

- event probability `P_event = sum(p) = 1 − q` (up to tolerance);
- cumulative event probability by offset `F(j) = p_0 + … + p_j`;
- any coarser grouping of contiguous regions (sum of members).

## Realized-target mapping

The mapping converts one selected immutable `TargetResolutionArtifact` (#19) for the same `target_episode_key` into a realized outcome on the snapshot's grid. It is a deterministic function used only by controlled retrospective joins (development assembly, backtest assembly), never by the prediction procedure.

### Inputs

- the snapshot's `RegionGrid` (`L`, `K_T`);
- the selected `TargetResolutionArtifact` and its `resolution_state`;
- for `OBSERVED_EVENT`: the qualifying event's `pit_entry_occurrence` (exact or bounded) and a retrospective **lap-count-at-entry** value `c(E)`, exact or as integer bounds `[c_lo, c_hi]`, derived from frozen race evidence by a versioned derivation (`entry_lap_derivation_version`).

### Rule

```text
OBSERVED_EVENT, c(E) exact:
    j = min(c(E) − L, K_T − 1)            -> REALIZED_REGION {j}

OBSERVED_EVENT, c(E) bounded [c_lo, c_hi]:
    a = min(c_lo − L, K_T − 1)
    b = min(c_hi − L, K_T − 1)
    if a == b                             -> REALIZED_REGION {a}
    else                                  -> REALIZED_REGION_SET {a .. b}

OBSERVED_EVENT, c_lo < L (contradicts E > T)
                                          -> MAPPING_CONFLICT

TERMINAL_NO_EVENT                         -> REALIZED_NO_EVENT

TRUNCATED_INDETERMINATE                   -> NOT_REALIZED
```

```text
RealizedOutcome
  target_episode_key
  target_resolution_artifact_ref
  resolution_run_ref
  region_grid (L, K_T, region_representation_version)
  kind: REALIZED_REGION | REALIZED_REGION_SET | REALIZED_NO_EVENT
        | NOT_REALIZED | MAPPING_CONFLICT
  region_index_low? / region_index_high?
  entry_lap_count_ref? / entry_lap_derivation_version?
  mapping_version
```

Properties:

- The mapping never changes event meaning: it consumes the pit-entry occurrence fixed by #19 and only locates it on the lap axis. Service time, pit exit, or stint labels are never substituted.
- `REALIZED_REGION_SET` is not truncation. The target outcome is known; only its lap offset is bounded. The predicted probability of the realized outcome is `sum(p_a … p_b)`, which is well defined. How scoring treats set-valued outcomes is owned by the verification/statistical phase.
- `NOT_REALIZED` is never converted to `REALIZED_NO_EVENT` or to any region. Accounting is owned by #21.
- `MAPPING_CONFLICT` indicates contradictory retrospective evidence (the target contract guarantees `E > T`, hence `c(E) ≥ L`). It is a reconstruction defect routed to accounting/verification, never silently clipped to region 0.
- The mapping uses the grid stored in the snapshot, so a later change to `N_T` evidence cannot move a realized outcome between grids.

## Model-facing interface

### Boundary

```text
PredictionRequest                       # constructed by the prediction procedure
  observation_artifact_ref
  semantic_observation_key
  target_episode_initialization_ref
  target_episode_key
  region_grid: RegionGrid
  input_view: ModelInputView

ModelInputView
  input_view_version                    # identifies the derivation
  values                                # derived only from CanonicalObservation.canonical_state
  derivation_input_fact_refs            # causal facts consumed
  omissions                             # facts unavailable at T, kept explicit

Estimator.predict(model_artifact, PredictionRequest) -> RawModelOutput
```

Rules:

1. `ModelInputView` is a deterministic function of exactly one `CanonicalObservation` (plus static, version-pinned configuration). It may not read source evidence, processed provider tables, other observations with later boundaries, target resolution artifacts, qualifying events, terminal boundaries, or evaluation results. This keeps the forecast-time dependency closure identical to the #17 architecture.
2. `TargetEpisodeInitialization` is passed for identity linkage only; it carries no outcome truth by #19's contract.
3. The estimator is a pure function of `(model_artifact, PredictionRequest)`. If an estimator is stochastic at inference time, its seed is part of the request provenance and is recorded in the snapshot.
4. The estimator is invoked only for `ELIGIBLE` decisions. `INELIGIBLE` or `INDETERMINATE` decisions produce no request.
5. Missing optional facts arrive as explicit omissions; the input view may not impute them from retrospective data.

### Output forms

An estimator declares exactly one output form in its model artifact:

```text
RawModelOutput (form = PMF)
  p[0 .. K_T−1], q

RawModelOutput (form = DISCRETE_HAZARD)
  λ[0 .. K_T−2]       # λ_j = P(entry in R_j | no entry in R_0..R_{j−1}); empty when K_T = 1
  q_open              # P(no entry before B | no entry in R_0..R_{K_T−2})
```

### Output adapters

The prediction procedure converts raw output to `CanonicalDistribution` with a versioned adapter:

```text
PMF adapter (pmf/v1):
  identity; optional single rescale by s = sum(p)+q only if
  abs(s − 1) ≤ 1e-6, recorded as `normalization_applied`; otherwise fail V4.

DISCRETE_HAZARD adapter (hazard/v1):
  S_0 = 1
  for j in 0 .. K_T−2:   p_j = λ_j · S_j ;  S_{j+1} = S_j · (1 − λ_j)
  final region:          p_{K_T−1} = (1 − q_open) · S_{K_T−1}
                         q          = q_open · S_{K_T−1}
  requires all λ_j, q_open in [0, 1]
```

Because the final region is open-ended, the hazard form needs `q_open` to split surviving mass between "pits on the final scheduled lap or later before `B`" and terminal no-event. Both adapters preserve the canonical meaning; neither introduces a horizon residual.

Additional output forms (for example a continuous-time density integrated onto the grid) may be added later as a new adapter version without changing `CanonicalDistribution`.

## Model artifact contract

```text
ModelArtifact
  artifact_id                         # content digest of the frozen bundle
  model_family_label                  # descriptive, free text
  output_form: PMF | DISCRETE_HAZARD
  region_representation_version       # must equal "driver-lap-offset/v1"
  input_view_version
  prediction_contract_version
  development_run_ref                 # #21 owns development-run mechanics
  development_temporal_boundary_ref   # #21 owns the boundary definition
  development_dataset_refs
  calibration_step_ref?               # if calibration is part of the frozen bundle
  randomness: seeds / determinism notes
  repository_revision
  dependency_lock_ref
  supersedes_model_ref?
```

A model artifact is immutable. Calibration, re-fitting, or any change to the frozen bundle creates a new artifact. The prediction procedure refuses a model artifact whose `region_representation_version`, `input_view_version`, or `prediction_contract_version` is incompatible with the request.

## Prediction snapshot contract

```text
PredictionSnapshot
  snapshot_id                         # digest of identity fields + distribution
  prediction_key
    target_episode_key
    model_artifact_ref
    prediction_run_ref
  observation_artifact_ref
  semantic_observation_key            # race session, driver entry, checkpoint
  prediction_boundary_ref             # T as recorded in the observation
  eligibility_decision_ref
  target_episode_initialization_ref
  distribution: CanonicalDistribution
  output_form / adapter_version / normalization_applied
  input_view_version / input_view_digest
  inference_seed?
  prediction_contract_version
  semantic_refs                       # approved decision/context versions
  prediction_procedure_revision
  validation: PASS (all V1–V7)
  recorded_at                         # wall clock; provenance only, not identity
```

```text
PredictionFailureRecord
  prediction_key
  observation_artifact_ref
  target_episode_initialization_ref
  failure_codes[]                     # REQUIRED_CONTEXT_MISSING, V1..V7,
                                      # MODEL_INCOMPATIBLE, FORBIDDEN_INPUT, ESTIMATOR_ERROR
  details
  prediction_contract_version
  prediction_run_ref
```

### Identity and immutability rules

1. Exactly one snapshot or one failure record exists per `prediction_key`.
2. Successive checkpoints are distinct snapshots because their `target_episode_key`s are distinct (#19). Snapshots are never chained, carried forward, or edited.
3. Different model artifacts or runs for the same episode produce different `prediction_key`s; neither replaces the other.
4. A snapshot never stores a resolution reference, realized outcome, or score. Those live in retrospective join artifacts that reference the snapshot.
5. Re-executing the same request with the same model artifact, input view, and seed must reproduce the same `distribution` bit-for-bit or to within the declared deterministic tolerance; otherwise it is a new run, not a correction.
6. Linkage: `snapshot → observation_artifact_ref → semantic_observation_key` identifies race session, driver entry, checkpoint, and `T`; `snapshot → target_episode_key` connects to the selected resolution in a declared resolution run; many snapshots may resolve to the same `QualifyingPitEventArtifact`.

## Pit-window derivation

The pit window is a derived, versioned summary. It is computed from a snapshot's `CanonicalDistribution` only.

### Rule `pit-window/v1`

Parameter: window mass level `α ∈ (0, 1]` recorded in the presentation configuration (default `0.8`; the value is a presentation choice, not a semantic lock).

```text
P_event = sum(p)

if P_event == 0:
    window = NONE

target = α · P_event

candidates = all contiguous index ranges [a, b] with 0 ≤ a ≤ b ≤ K_T−1
             such that sum(p_a .. p_b) ≥ target − 1e-12

choose the candidate with:
    1. smallest width (b − a + 1);
    2. then largest mass sum(p_a .. p_b);
    3. then smallest a.
```

### Required window output

```text
PitWindowSummary
  snapshot_id
  window_rule_version = "pit-window/v1"
  alpha
  window: NONE | [a, b]
  in_lap_range: (L + a + 1) .. (L + b + 1)   # b = K_T−1 shown as "L + K_T or later"
  mass_in_window       = sum(p_a .. p_b)
  mass_before_window   = sum(p_0 .. p_{a−1})
  mass_after_window    = sum(p_{b+1} .. p_{K_T−1})
  terminal_no_event_probability = q
```

`mass_in_window + mass_before_window + mass_after_window + q = 1` (within tolerance). A presentation must expose the outside-window masses and `q` alongside the window; it may not render the window as the full prediction or imply zero probability outside it. The window is not used as an evaluation target. The rule is deterministic and reproducible from the snapshot alone.

## Experimentation-owned choices (not frozen here)

| Choice | Owner |
| --- | --- |
| Model family, estimator, hyperparameters | Model verification/experimentation |
| `ModelInputView` contents (features, encodings, omission handling) | Model verification/experimentation, constrained by the input boundary above |
| Loss function, censoring/truncation treatment during fitting | Model verification/experimentation + statistical design |
| Calibration algorithm and whether it is part of the frozen bundle | Model verification/experimentation |
| PMF versus discrete-hazard output form | Per model artifact |
| Probability floor / zero handling | Verification/statistical phase |
| Default pit-window `α` value | Presentation/verification; contract requires only that it is recorded |
| Scoring of set-valued realized outcomes, metrics, aggregation | Verification/statistical phase |

## Evolution behind the contract

- New models: produce new `ModelArtifact`s and new snapshots; consumers see the same `CanonicalDistribution` shape and can compare models on identical grids.
- New input views: new `input_view_version`; must still derive only from `CanonicalObservation`.
- New output forms: new adapter version; canonical distribution unchanged.
- New pit-window rule: new `window_rule_version`; snapshots unchanged.
- Changing the axis or partition (for example sub-lap regions): new `region_representation_version` plus a new mapping version. Because a different grid could change consumer meaning, such a change must pass a bounded design reconciliation; it must not alter the approved complete-coverage, terminal no-event, or no-truncation-category semantics.
- `prediction_contract_version` changes when any invariant, snapshot identity rule, or mapping rule changes.

## Scope guards

- The distribution is a descriptive forecast of likely team/driver behavior. Nothing here ranks, recommends, or optimizes a pit decision.
- No live trigger, streaming interface, latency budget, or serving API is defined; the request/estimator boundary is offline and replay-driven.
- No production code is introduced.

## Unknown routing

| Question | Classification | Owner | Status |
| --- | --- | --- | --- |
| Scheduled race distance `N_T` must be represented as a legitimate fact in `CanonicalObservation` (e.g. `STATIC_PRIOR`, updated if a change is available by `T`) | Cross-slice dependency | #18 observation reconstruction; verification support matrix | Assumed expressible under #18's existing fact classes; missing fact fails closed as `REQUIRED_CONTEXT_MISSING` |
| Retrospective `c(E)` (lap count at pit-entry occurrence) derivation and its evidence support | Cross-slice dependency (retrospective evidence) | Verification baseline; derivation consumes #19's `pit_entry_occurrence` and frozen race evidence | Contract defined here; empirical support matrix deferred |
| Which component physically runs the realized-target mapping and how `NOT_REALIZED` / `MAPPING_CONFLICT` are accounted | Cross-slice dependency | #21 replay/backtest | Mapping function owned here; orchestration/accounting owned by #21 |
| Development temporal boundary referenced by `ModelArtifact` | Cross-slice dependency | #21 | Field reserved here |
| Metrics, scoring rules, set-valued outcome scoring, dependence-aware statistics | Later-phase decision | Verification/statistical phase | Deferred |
| Model family, features, loss, calibration, probability floor | Later-phase decision | Model experimentation | Deferred |
| Serialization, file formats, digest algorithm, package layout | Later-phase decision | Implementation | Deferred |

There are no unresolved current-scope decisions.

## Verification handoff

The verification baseline must include at least:

1. coverage fixtures: for random `L`, `N_T`, and `c(E) ≥ L`, the mapping returns exactly one region; fixtures with `c(E) ≥ N_T` land in the final region;
2. `K_T = 1` (checkpoint with `L ≥ N_T − 1`, i.e. the driver is on the final scheduled lap or beyond) produces one open region plus `q`;
3. shortened-race and lapped-finisher scenarios proving coverage does not depend on `N_T` accuracy;
4. every invariant `V1`–`V7` has a failing fixture producing `PredictionFailureRecord` rather than a snapshot;
5. both adapters: hazard→PMF conversion sums to one and matches a hand-computed example; PMF rescale tolerance boundary;
6. bounded `c(E)` producing `REALIZED_REGION_SET`; `c_lo < L` producing `MAPPING_CONFLICT`; truncated resolutions producing `NOT_REALIZED`;
7. pit-window determinism, tie-breaking, `P_event = 0`, `α = 1`, final-region windows, and mass-accounting identity;
8. dependency-closure test: the prediction procedure and input-view derivation cannot import or receive target-resolution, event, terminal, or evaluation artifacts;
9. successive-checkpoint fixture: two snapshots with distinct episode keys resolving to the same event, with no snapshot mutation;
10. reproducibility: identical request + model artifact + seed reproduces the identical distribution and `snapshot_id`.

## Acceptance mapping

- **Exact region representation with complete coverage:** driver-lap-offset grid with open final region; coverage proof above.
- **Normalization/invariants:** `CanonicalDistribution` invariants `V1`–`V7`; terminal no-event explicit.
- **Unambiguous realized mapping:** deterministic rule from #19 resolution states and pit-entry lap count to `RealizedOutcome`.
- **Stable model-facing boundary without estimator lock-in:** `PredictionRequest` / `Estimator.predict` / two output forms + adapters.
- **Artifact identity, linkage, versioning, immutability:** `ModelArtifact`, `PredictionSnapshot`, `PredictionFailureRecord`, identity rules.
- **Invalid outputs detectable:** invariant codes and failure record.
- **Exact faithful pit-window rule:** `pit-window/v1` with mandatory outside-window and `q` reporting.
- **Experimentation routing:** table above.
- **No recommendation, live, or production semantics:** scope guards.
- **Independent review:** pending.

## Product Owner decisions

None required. The representation implements the approved complete-distribution semantics; the lap-offset axis, open final region, adapters, and window rule are delegated detailed-design choices that do not change prediction meaning.

## Review record

Pending independent full scoped review under `governance/REVIEW_POLICY.md`.
