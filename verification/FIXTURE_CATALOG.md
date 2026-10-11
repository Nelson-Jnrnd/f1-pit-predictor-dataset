# V2 Reference Scenarios and Acceptance Fixture Catalog

## Status

Draft. Authored for Issue #36. Independent full scoped review is required before approval.

## Abstraction level

This is a verification specification. It turns every verification handoff item of the approved designs, plus the verification parameters of #35 and #37, into catalogued reference scenarios and acceptance fixtures, each with an exact expected outcome. Implementation turns each entry into an automated test without inventing expected behaviour.

This artifact contains no test code and does not change any design rule. If a fixture exposes a contradiction, it is routed to the owning design.

## Issue / branch

- Issue: #36. Parent: #34.
- Branch: `ccr-d8f3e250-t7uix3`.
- Sources:
  - `design/OBSERVATION_RECONSTRUCTION.md` (#18, items O-1…O-15)
  - `design/TARGET_RECONSTRUCTION.md` (#19, items T-1…T-25)
  - `design/PREDICTION_CONTRACT.md` (#20, items P-1…P-10 and P-6a)
  - `design/REPLAY_BACKTEST.md` (#21, items R-1…R-12)
  - `design/DESIGN_INTEGRATION.md` observation O3
  - `verification/SUPPORT_MATRIX.md` (#35)
  - `verification/EVALUATION_PROTOCOL.md` (#37)

## Conventions

- **ID prefix** gives the owning design: `FX-OBS`, `FX-TGT`, `FX-PRD`, `FX-RPL`, `FX-SUP` (#35 parameters), `FX-EVL` (#37), `FX-E2E` (cross-component).
- **Basis:**
  - `SYN`: a synthetic record stream or artifact built in the test.
  - `REAL(scope)`: a frozen real session, by `RaceSessionKey`. It must be in the stated #35 scope and loaded from bytes whose SHA-256 matches `verification/evidence/probe_*_v2.json`.
- **Level:**
  - `U`: unit (a pure function).
  - `C`: contract (an artifact/invariant at a component boundary).
  - `E2E`: a chain across components.
  - `L`: a leakage or dependency-closure test.
- **Record notation** in synthetic streams is `P=<prefix seconds>` on one endpoint. Unless stated, all synthetic sessions have:
  - `SessionStatus Started` at P = 3600;
  - `Finished` at P = 9000;
  - `TotalLaps` 57 published at P = 60;
  - every Heartbeat and RCM anchor consistent;
  - every window clock-healthy.
- **"Expected"** values are exact. Floating-point comparisons use a 1e-9 tolerance unless stated.
- A source item that is genuinely implementation-internal, or cannot be built from available truth, is marked **DEFERRED** with a reason.

## Traceability index

Every handoff item maps to at least one catalog entry, or is explicitly deferred.

| Source items | Catalog entries |
| --- | --- |
| #18 O-1, O-2, O-3, O-13 | FX-SUP-01…04, FX-SUP-10 (scope classification) |
| #18 O-4 | FX-OBS-01, FX-OBS-02 |
| #18 O-5 | FX-OBS-03…05 |
| #18 O-6, O-12 | FX-OBS-06, FX-OBS-07 |
| #18 O-7 | FX-SUP-05…08 |
| #18 O-8 | FX-OBS-08, FX-SUP-07 |
| #18 O-9 | FX-OBS-09 |
| #18 O-10 | FX-OBS-10 |
| #18 O-11 | FX-OBS-11 |
| #18 O-14 | FX-OBS-12…16 |
| #18 O-15 | FX-OBS-17…19, FX-SUP-11 |
| #19 T-1 | FX-TGT-01, FX-TGT-02 |
| #19 T-2, T-3 | FX-TGT-03, FX-TGT-04 |
| #19 T-4 | FX-TGT-05 |
| #19 T-5 | FX-TGT-06 |
| #19 T-6 | DEFERRED (see FX-TGT-07) |
| #19 T-7, T-8 | FX-TGT-08, FX-TGT-09 |
| #19 T-9, T-10, T-11, T-12 | FX-TGT-10…13 |
| #19 T-13 | FX-TGT-14 |
| #19 T-14, T-15 | FX-TGT-15, FX-TGT-16 |
| #19 T-16 | FX-TGT-17 |
| #19 T-17 | FX-TGT-18…20 |
| #19 T-18, T-19 | FX-TGT-21, FX-TGT-22 |
| #19 T-20 | FX-TGT-23 |
| #19 T-21 | FX-TGT-24 |
| #19 T-22 | FX-TGT-25 |
| #19 T-23, T-24 | FX-TGT-26…29 |
| #19 T-25 | FX-TGT-30 |
| #20 P-1…P-3 | FX-PRD-01…04 |
| #20 P-4 | FX-PRD-05 (V1–V7) |
| #20 P-5 | FX-PRD-06, FX-PRD-07 |
| #20 P-6 | FX-PRD-08…12 |
| #20 P-6a | FX-PRD-13 |
| #20 P-7 | FX-PRD-14…17 |
| #20 P-8 | FX-PRD-18 |
| #20 P-9 | FX-PRD-19 |
| #20 P-10 | FX-PRD-20 |
| #21 R-1 | FX-RPL-01, FX-RPL-02 |
| #21 R-2 | FX-RPL-03 |
| #21 R-3 | FX-RPL-04 |
| #21 R-4 | FX-RPL-05 |
| #21 R-5 | FX-RPL-06…13 |
| #21 R-6 | FX-RPL-14 |
| #21 R-7 | FX-RPL-15…18 |
| #21 R-8 | FX-RPL-19, FX-RPL-20 |
| #21 R-9 | FX-RPL-21 |
| #21 R-10 | FX-RPL-22 |
| #21 R-11 | FX-RPL-23 |
| #21 R-12 | FX-RPL-24 |
| Gate O3 | FX-RPL-25, FX-RPL-26 |
| #35 parameters | FX-SUP-01…14 |
| #37 parameters | FX-EVL-01…14 |
| Cross-component | FX-E2E-01…09 |

## Observation reconstruction (#18)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-OBS-01 | O-4 | SYN | C | `SessionStatus` Started at P = 3600 in an S-RD-classified source → exactly one `RACE_START` checkpoint (`completed_laps = 0`), boundary P = 3600 (bounded [3595, 3605]) |
| FX-OBS-02 | O-4 | SYN | C | `Started` at 3600, `Aborted` at 5000, `Started` at 5600 → one `RACE_START` checkpoint at 3600. The restart creates **no** second start checkpoint, and lap checkpoints continue from the counter |
| FX-OBS-03 | O-5 | SYN | C | Driver #44 has `NumberOfLaps` 1, 2, 2 (duplicate), 3 at P = 3700, 3790, 3791, 3880 → lap checkpoints L = 1, 2, 3 at 3700, 3790, 3880. The duplicate creates no checkpoint |
| FX-OBS-04 | O-5 | SYN | C | Counts 5 → 7 (jump) at P = 4100 → checkpoint L = 7 at 4100; the L = 6 attempt record is `INDETERMINATE_CHECKPOINT` with reason `LAP_COUNT_JUMP` |
| FX-OBS-05 | O-5 | SYN | C | Counts 8, then 7 (regression) at P = 4300, then 8 at 4400 → the L = 8 checkpoint stays at its first availability; the regression record is preserved; no new L = 8 checkpoint is created; later observations see the latest state (append-only, #18 rule 5) |
| FX-OBS-06 | O-6 | REAL(S-RD) | C | British 2025 race, all 8 streams → stored snapshot bytes reproduce the evidence SHA-256 per stream. `ArchiveRecordKey` ordinals are contiguous from 0, and prefixes equal the raw prefixes. No `SourceAvailabilityKey` exists without an authority validation reference |
| FX-OBS-07 | O-12 | REAL(S-RD) | C | Reconstruct the same session twice from identical snapshots and config → identical observation artifact digests and identical attempt-record lists |
| FX-OBS-08 | O-8 | SYN | C | A malformed JSON line in `TimingData` at P = 5000 → the record is counted in source-gap metadata, no fact is admitted from it, and the run manifest reports it. A checkpoint whose trigger lies in a gap that can hide the trigger becomes `INDETERMINATE_SOURCE` |
| FX-OBS-09 | O-9 | SYN | C | FastF1 processed `Laps.Time` differs from the raw `TimingData` advance prefix by 3 s → the boundary uses the raw advance prefix only. Processed values never appear as availability evidence |
| FX-OBS-10 | O-10 | SYN | C | Driver #1's `LastLapTime` for lap 10 is published at P = 4000 as 1:32.5, and corrected at P = 4500 to 1:33.0 → the observation at L = 10 (trigger P = 4000) shows 1:32.5. Observations with boundaries after 4510 show 1:33.0. The L = 10 artifact is unchanged after the correction |
| FX-OBS-11 | O-11 | SYN | C | At #44's L = 10 trigger (P = 5000), #1 is mid-lap 12 with a sector update at P = 4985 (same stream) → #1's sector state is admitted (same stream, earlier in stream order). #1's lap-12 completion at P = 5003 is excluded. No equal-lap alignment is performed |
| FX-OBS-12 | O-14 | SYN | C | Session identity mismatch → exactly one `SESSION` record, `INDETERMINATE_IDENTITY`, and no child records |
| FX-OBS-13 | O-14 | SYN | C | Session with 20 entries, one with lap evidence up to 57 → for that entry, 1 `DRIVER_ENTRY` record (`ESTABLISHED`) and 58 `CHECKPOINT` records (L = 0…57), all with unique `attempt_key` |
| FX-OBS-14 | O-14 | SYN | C | Two candidates share racing number 81 → two `DRIVER_ENTRY` records, `INDETERMINATE_IDENTITY`, with distinct `driver_alias` values (provider ID or roster ordinal) and no checkpoints. Their attempt keys are unique |
| FX-OBS-15 | O-14 | SYN | C | (a) An established entry with no lap evidence → one `DRIVER_ENTRY` record, `ENUMERATION_INCOMPLETE` (`LAP_COUNT_EVIDENCE_MISSING`), plus a `RACE_START` record only. (b) Identity established, zero entry candidates → `SESSION` record `ENUMERATION_INCOMPLETE` (`NO_ENTRY_CANDIDATES`). (c) Identity established, enumeration prevented by a source gap → `SESSION` record `INDETERMINATE_SOURCE`, no children |
| FX-OBS-16 | O-14 | SYN | L | The stream tail is truncated, so the last available count is 40 although the race ran 57 → `L_max` = 40. 41 checkpoint attempts (0…40) are enumerated. `L_max` appears in no observation content or boundary (inspect the dependency closure) |
| FX-OBS-17 | O-15 | SYN | C | `TotalLaps` 58 at P = 6 → the start observation (Started at 3600) has `SCHEDULED_RACE_DISTANCE_LAPS` = 58 (admissible under the 300 s pre-race margin, FX-SUP-09) |
| FX-OBS-18 | O-15 | SYN | C | Aborted start: `TotalLaps` 58 at P = 6, revised to 57 at P = 3550 → the start observation (3600) has **58**, because 3550 + 300 ≥ 3595 fails the pre-race margin. Observations with in-race triggers after 3560 (cross-stream margin) have 57 |
| FX-OBS-19 | O-15 | SYN | C | Only a final-classification distance is available (no stream value) → fact omitted, `SCHEDULED_DISTANCE_UNAVAILABLE`, and #20 yields `REQUIRED_CONTEXT_MISSING` (FX-PRD-21) |

## Target reconstruction (#19)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-TGT-01 | T-1 | SYN | U | `InPit` False→True at P = 5000, True→False at P = 5022 for #16 → one `PitVisitArtifact`: entry P = 5000, exit P = 5022 |
| FX-TGT-02 | T-1 | REAL(S-RD) | C | Every race in S-RD → every Jolpica stop (`api.jolpi.ca`, frozen response hash as in `capabilities_raceday_scope_v2.json`) has exactly one visit with `c(E) + 1 ==` Jolpica lap. Expected total: 1998/1998 |
| FX-TGT-03 | T-2 | SYN | C | An `InPit` transition at P = 1200 (before Started) → visit `OUTSIDE_RACE_PARTICIPATION`; no qualifying event |
| FX-TGT-04 | T-3 | SYN | C | #31 `Retired` at P = 6000 (last advance 5950), with an `InPit` entry at 6100 → visit `OUTSIDE_RACE_PARTICIPATION` (at or after terminal); not a target. Same for any entry after the last `Finished` |
| FX-TGT-05 | T-4 | SYN | C | (a) Duplicate `InPit:true` at 5000 and 5000.4 with no exit between → one visit. (b) `InPit:false` with no prior entry → segmentation anomaly flagged, no visit. (c) Entry with no exit before session end → exit-open visit retained |
| FX-TGT-06 | T-5 | SYN | C | Two entries for #4 at P = 5000 (exit 5021) and P = 5040 (exit 5062), both with `c(E)` = 30 → two visits with distinct `visit_discriminator`s, ordered by entry |
| FX-TGT-07 | T-6 | — | — | **DEFERRED.** Canonical reconstruction does not use FastF1 `PitInTime`/`PitOutTime` (#35). An optional implementation diagnostic may report discrepancies; it is not acceptance-relevant |
| FX-TGT-08 | T-7 | SYN | U | Visit window updates: stint 2 `{TyresNotChanged:"1"}` at entry + 1 s, then stint 2 `{TyresNotChanged:"0", New:"true", Compound:"HARD"}` at entry + 6 s → `CONFIRMED_TYRE_SERVICE` (last update) |
| FX-TGT-09 | T-8 | SYN | U | Last update `{TyresNotChanged:"0", New:"false", Compound:"MEDIUM", StartLaps:8}`, previous stint MEDIUM → `CONFIRMED_TYRE_SERVICE`. Compound equality is not a negative |
| FX-TGT-10 | T-9 | SYN | C | RCM "DRIVE THROUGH PENALTY FOR CAR 63" issued at P = 7400; #63's first in-race entry afterwards at 7647; RCM "PENALTY SERVED - DRIVE THROUGH PENALTY FOR CAR 63" at 9500 → that visit is `CONFIRMED_NO_TYRE_SERVICE`, whatever the stint data says |
| FX-TGT-11 | T-10 | REAL(S-RD) | C | The penalty test set in S-RD (9 visits, `capabilities_raceday_scope_v2.json`) → all have last-update `TyresNotChanged:"1"`, none `"0"`. A visit with `"1"` and no penalty → `INDETERMINATE_TYRE_SERVICE`, never `CONFIRMED_NO_TYRE_SERVICE` |
| FX-TGT-12 | T-11 | SYN | U | A drive-through opens stint 1 (`TyresNotChanged:"1"`, `StartLaps:53`) with no penalty messages → `INDETERMINATE_TYRE_SERVICE`, **not** confirmed service, despite the stint increment |
| FX-TGT-13 | T-12 | SYN | U | Visit with no stint update in [entry, next entry) → `INDETERMINATE_TYRE_SERVICE` |
| FX-TGT-14 | T-13 | SYN | U | T = 5000, with bounds [4995, 5005] (S-RD). Entry E at P = 5011 → `STRICTLY_AFTER_T`. E at 5009 → `INDETERMINATE_PREDICTION_RELATION`, because [5004, 5014] overlaps. E at 4989 (bounds [4984, 4994], upper bound ≤ T's lower bound 4995) → `BEFORE_OR_AT_T`. E at 4994 (bounds [4989, 4999]) → indeterminate. E at exactly 5000 → not strictly after (indeterminate) |
| FX-TGT-15 | T-14 | SYN | U | B bounded as (5950, 6000]. Entry bounds [5935, 5945] → `STRICTLY_BEFORE_TERMINAL`. Entry [6005, 6015] → `AT_OR_AFTER_TERMINAL`. Entry [5955, 5965] → `INDETERMINATE_TERMINAL_RELATION` |
| FX-TGT-16 | T-15 | SYN | C | Episode T = 5000, B = 8000, confirmed-service in-scope entries at 5600 and 7000 → `OBSERVED_EVENT` references the 5600 event. A confirmed-service entry at 8100 never resolves any episode |
| FX-TGT-17 | T-16 | SYN | C | Two potentially qualifying entries for one driver with overlapping bounds [6000, 6012] and [6008, 6020] → `TRUNCATED_INDETERMINATE` (ordering changes the target) |
| FX-TGT-18 | T-17 | SYN | U | `Retired:true` at P = 6000, last lap advance 5950 → terminal, B ∈ (5950, 6000] |
| FX-TGT-19 | T-17 | SYN | U | `Stopped:true` at 6000 after the last advance 5950, before the last `Finished` → terminal. `Stopped:true` at 5000 followed by advances at 5100+ (red flag) → **not** terminal. Post-race disqualification only → not a participation terminal. In-race black-flag disqualification → terminal |
| FX-TGT-20 | T-17 | REAL(S-RD) | C | Combined terminal rule over S-RD → agrees with the Jolpica non-finishers (disqualifications excluded) in 157/158 (`capabilities_raceday_scope_v2.json`). Regression guard: the count does not decrease |
| FX-TGT-21 | T-18 | SYN | C | A source gap in `TimingData` over [6000, 6200] for #10, with episode T = 5800 and no confirmed event before 6000 → `TRUNCATED_INDETERMINATE`. Same gap but a confirmed in-scope event at 5900 → `OBSERVED_EVENT` (the later gap is irrelevant) |
| FX-TGT-22 | T-19 | SYN | C | Episode T = 8500, finish terminal B = 8900, no visits in (T, B), complete coverage → `TERMINAL_NO_EVENT`. Same, but an `INDETERMINATE_TYRE_SERVICE` visit at 8700 → `TRUNCATED_INDETERMINATE`, never no-event |
| FX-TGT-23 | T-20 | SYN | C | Checkpoints L = 20 (T = 5000) and L = 21 (T = 5090), with one confirmed event at 5600 → two episodes with distinct `target_episode_key`s, both `OBSERVED_EVENT`, same `event_key` |
| FX-TGT-24 | T-21 | SYN | C | Re-resolve one episode under a second resolution run → two immutable resolution artifacts; exactly one selected per `resolution_run_ref`; the first is unchanged |
| FX-TGT-25 | T-22 | REAL(S-RD) | C | Resolve the same session twice with identical inputs and config → identical resolution artifact digests |
| FX-TGT-26 | T-23 | REAL(S-RD) | C | For every S-RD race, the lap-completion counter used for `c(E)` equals the #18 checkpoint counter (same `NumberOfLaps` advances). 0 jumps and 0 regressions (`capabilities_raceday_scope_v2.json`) |
| FX-TGT-27 | T-24 | SYN | U | Completions at P = 4900 (lap 30) and 5000 (lap 31); entry at P = 5000 in stream order **after** the lap-31 advance → `c_exact = 31`. Entry before the lap-31 record in stream order → `c_exact = 30` |
| FX-TGT-28 | T-24 | SYN | U | Red flag after lap 40; classification countback to lap 39; as-raced counter = 40 at entry → `c_exact = 40` (as-raced, never countback) |
| FX-TGT-29 | T-24 | SYN | U | A driver's lap-count stream jumps 30 → 32 before the entry → no `EntryLapContext`; `entry_lap_context_absent_reason` is set; the resolution remains `OBSERVED_EVENT` |
| FX-TGT-30 | T-25 | SYN | C | #18 run with 10 canonical observations (7 eligible, 2 ineligible, 1 indeterminate) → the initialization manifest has exactly 10 records, 7 initialization references, and an initialization present iff `ELIGIBLE` |

## Prediction contract (#20)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-PRD-01 | P-1 | SYN | U | L = 10, N_T = 57 → K_T = 47. c(E) = 10 → R_0; 30 → R_20; 56 → R_46; 60 → R_46 |
| FX-PRD-02 | P-1 | SYN | U | Property test: random L ∈ [0, 77], N_T ∈ [44, 78], c ≥ L → exactly one region index in [0, K_T − 1] |
| FX-PRD-03 | P-2 | SYN | U | L = 56, N_T = 57 → K_T = 1, and c = 56 → R_0. L = 57, N_T = 57 → K_T = 1. A distribution with one region plus `q` is valid |
| FX-PRD-04 | P-3 | SYN | U | Grid from N_T = 71 at T; race shortened to 69; event with c = 68, L = 60 → R_8 (K_T = 11). A lapped finisher with c = 66, L = 60 → R_6. Coverage is complete regardless of N_T accuracy |
| FX-PRD-05 | P-4 | SYN | C | One failing distribution per invariant, each producing a `PredictionFailureRecord` with that code and no snapshot: V1 (`p_0 = NaN`); V2 (`p_1 = −0.1`); V3 (`len(p) = K_T − 1`); V4 (sum + q = 1.001); V5 (`q` absent); V6 (an extra `"truncated"` outcome); V7 (grid L ≠ observation L) |
| FX-PRD-06 | P-5 | SYN | U | Hazard K_T = 3, λ = [0.2, 0.5], q_open = 0.25 → p = [0.2, 0.4, 0.3], q = 0.1; sum = 1 (within 1e-9) |
| FX-PRD-07 | P-5 | SYN | U | PMF with sum + q = 1 + 5e-7 → rescaled, `normalization_applied = true`. With sum + q = 1 + 2e-6 → V4 failure |
| FX-PRD-08 | P-6 | SYN | U | L = 10, K_T = 47, `c_lo = 12`, `c_hi = 13` → `REALIZED_REGION_SET {2..3}` |
| FX-PRD-09 | P-6 | SYN | U | L = 10, `[c_lo, c_hi] = [9, 11]` → `c_lo' = 10` → `REALIZED_REGION_SET {0..1}`. `[7, 9]` → `MAPPING_CONFLICT`. Exact c = 9 → `MAPPING_CONFLICT` |
| FX-PRD-10 | P-6 | SYN | U | `OBSERVED_EVENT` with no `EntryLapContext` → `MAPPING_UNAVAILABLE` |
| FX-PRD-11 | P-6 | SYN | U | `TRUNCATED_INDETERMINATE` → `NOT_REALIZED`. `TERMINAL_NO_EVENT` → `REALIZED_NO_EVENT` |
| FX-PRD-12 | P-6 | SYN | U | Countback context (FX-TGT-28) with L = 35 → region index 5, from the as-raced c = 40 |
| FX-PRD-13 | P-6a | SYN | C | Hazard output λ = [1.0], q_open = 1.5 (K_T = 2) → R4 failure **before** conversion; no snapshot. Wrong form → R1; `len(λ) ≠ K_T − 1` → R2; NaN → R3 |
| FX-PRD-14 | P-7 | SYN | U | p = [0.125, 0.5, 0.25, 0.0625], q = 0.0625, α = 0.8, L = 10 → window [1, 2]; in-laps 12–13; `mass_in_window` 0.75; before 0.125; after 0.0625; q 0.0625 |
| FX-PRD-15 | P-7 | SYN | U | Tie: p = [0.25, 0.25, 0.25, 0.125], q = 0.125, α = 0.5 → window [0, 1] (equal width and mass; smallest a) |
| FX-PRD-16 | P-7 | SYN | U | P_event = 0 (q = 1) → window `NONE`, with in/before/after masses all 0 |
| FX-PRD-17 | P-7 | SYN | U | α = 1, p = [0.5, 0, 0.25, 0.25], q = 0 → window [0, 3]. A window ending at the final region is labelled "L + K_T or later" |
| FX-PRD-18 | P-8 | SYN | L | Pass a `TargetResolutionArtifact` (or a score, or an event) to the request builder or input-view derivation → refused (`FORBIDDEN_INPUT`). Static import check: the prediction and input-view modules import no target-resolution or evaluation module |
| FX-PRD-19 | P-9 | SYN | C | FX-TGT-23 episodes → two snapshots with distinct `prediction_key`s; re-running resolution does not change either `snapshot_id` or `content_digest` |
| FX-PRD-20 | P-10 | SYN | C | Identical `request_digest` re-executed in a new run → identical distribution and `content_digest`, new `prediction_key` and `snapshot_id` |
| FX-PRD-21 | (#18 A1 / #20) | SYN | C | Observation lacking `SCHEDULED_RACE_DISTANCE_LAPS` → `PredictionFailureRecord` `REQUIRED_CONTEXT_MISSING`; no snapshot |

## Replay and backtest (#21; gate O3)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-RPL-01 | R-1 | SYN | U | Attempt records: SESSION (ESTABLISHED); DRIVER_ENTRY #1, #44; DRIVER_ENTRY alias "cand-2" (identity failure); CHECKPOINT #1 L = 0, 1; #44 L = 0 → manifest order is: SESSION, DE #1, DE #44, DE cand-2, CP #1 L0, CP #1 L1, CP #44 L0. Key-less records sort after keyed ones at their level |
| FX-RPL-02 | R-1 | SYN | U | Chronological stream: #44 L1 T = 5000 [4995, 5005]; #1 L1 T = 5000 [4995, 5005] (exact tie) → order #1 before #44 (manifest key). Bounded (upper, lower) ordering applied |
| FX-RPL-03 | R-2 | SYN | L | Replay config with a `TargetResolutionArtifact` as a direct input → run `ABORTED`. A model artifact whose provenance references development resolutions → allowed |
| FX-RPL-04 | R-3 | SYN | C | Run replay R1, then a new resolution run, a backtest and replay R2 → R1 snapshots are byte-identical before and after |
| FX-RPL-05 | R-4 | SYN | C | Races r1 < r2 < r3. A model with cutoff r2 predicting r2 → accepted. The same model predicting r1 → refused. A `PER_RACE` schedule {r2: cutoff r2, r3: cutoff r2} → accepted. {r3: cutoff after r3} → refused |
| FX-RPL-06 | R-5 | SYN | C | Final backtest with no lock → refused |
| FX-RPL-07 | R-5 | SYN | C | First `FINAL_EVALUATION` of race r under lock L1 → `PRIMARY_FINAL`. Rerun under L1 with matching contents → `REPRODUCTION`. Rerun with a different seed policy → refused at replay (seed mismatch) |
| FX-RPL-08 | R-5 | SYN | C | Rerun under L1 with non-matching contents → `POST_HOC` |
| FX-RPL-09 | R-5 | SYN | C | A new protocol and lock L2 evaluating already-opened r → `POST_HOC` |
| FX-RPL-10 | R-5 | SYN | C | New primary claim on partition {r (opened), r4 (fresh)} → rejected |
| FX-RPL-11 | R-5 | SYN | C | Registered `AD_HOC_OPENING` of r5, then its first `FINAL_EVALUATION` → `POST_HOC` |
| FX-RPL-12 | R-5 | SYN | C | `FINAL_REFIT_TRAINING` of r6 under abandoned lock L3, then L4 evaluates r6 → `POST_HOC`. A development join of r7 under another protocol, then a final evaluation → `POST_HOC` |
| FX-RPL-13 | R-5 | SYN | C | Final backtest with a non-protocol `resolution_run_ref` → refused. The same run declared as a correction → `RESOLUTION_REEVALUATION`, reported alongside the primary |
| FX-RPL-14 | R-6 | SYN | C | Development join including a final-partition race, before the lock → refused. After the lock, as `FINAL_REFIT` → accepted, with `FINAL_REFIT_TRAINING` opening(s) written before the read |
| FX-RPL-15 | R-7 | SYN | U | One record per category A0…A11, constructed precisely → each lands in exactly its category under the ordered evaluation |
| FX-RPL-16 | R-7 | SYN | U | Key-less SESSION `INDETERMINATE_IDENTITY` and DRIVER_ENTRY alias failure → A1 rows, in manifest order |
| FX-RPL-17 | R-7 | SYN | U | Snapshot `target_episode_initialization_ref` ≠ selected resolution's → A0 |
| FX-RPL-18 | R-7 | SYN | U | `ESTABLISHED` SESSION and DRIVER_ENTRY rows → no category assigned, and not counted as candidates |
| FX-RPL-19 | R-8 | SYN | C | Perturb the realized region (R_3 → R_7) and the prediction values of A9 units → the cohort set is unchanged |
| FX-RPL-20 | R-8 | SYN | C | Any single A8 (or A5, A7, A0) row in scope → run `DEFECTIVE`; scorer refuses `analysis_class = PRIMARY` |
| FX-RPL-21 | R-9 | SYN | C | FX-TGT-23 units → both retained; same `eventual_event_key`; distinct `target_episode_key`s |
| FX-RPL-22 | R-10 | SYN | C | Re-execute a backtest → new run id. Semantic-keyed comparison with distributions differing by 1e-12 (within tolerance) → `REPRODUCTION`. With one category differing → not a reproduction |
| FX-RPL-23 | R-11 | SYN | C | Scorer with `supported_kinds = {A9, A10}` → `analysis_class` forced to `SECONDARY`. A subset rule "units with an observed event" → `RETROSPECTIVE_DIAGNOSTIC` |
| FX-RPL-24 | R-12 | SYN | C | Final partition {r1, r2}, with replays covering only r1 → run `DEFECTIVE` (coverage) |
| FX-RPL-25 | Gate O3 | SYN | C | Development join where an episode's resolution comes from a different initialization run than the observation's initialization → join refuses, or records A0-equivalent defect rows for development accounting |
| FX-RPL-26 | Gate O3 | SYN | C | Replay whose `observation_reconstruction_run_ref` ≠ the initialization run's observation run → replay refused at configuration time |

## Verification parameters (#35)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-SUP-01 | #35 (A) | REAL | C | Scope classifier on `headscan_v1.json` rows → 55 S-RD, 112 rewritten (`UNVERIFIED_ARCHIVE`), 22 + 7 HTTP 403. Bahrain 2018 and Hungary 2018 → `UNSUPPORTED` |
| FX-SUP-02 | #35 (A) | SYN | U | `Last-Modified` = race date + 2 days → not S-RD (`UNVERIFIED_ARCHIVE`). Race date + 1 day → S-RD |
| FX-SUP-03 | #35 (A) | REAL(S-RD) | C | `--verify` of an S-RD race whose stored hash differs from the evidence → the race is removed from S-RD until re-validated |
| FX-SUP-04 | #35 (A) | SYN | C | Endpoint `TrackStatus` in S-RD → facts omitted as an `UNVERIFIED_ARCHIVE` optional domain |
| FX-SUP-05 | #35 bounds | SYN | U | Cross-stream fact P = 989.9, trigger P = 1000 → admitted. P = 990.0 → omitted (990 + 5 < 995 is false) |
| FX-SUP-06 | #35 bounds | SYN | U | Same-stream (`TimingData`) record at P = 999.9 preceding the trigger in stream order → admitted. A field carried in the trigger record → admitted. Same-stream record **after** the trigger in stream order, even with an equal prefix → omitted |
| FX-SUP-07 | #35 health (a) | SYN | U | Lap-fixture residuals > 1 s for drivers #1 and #10 in overlapping laps [8620, 8820] → unhealthy window. A trigger at 8700 → `INDETERMINATE_CHECKPOINT` (`COARSE_TIME_AMBIGUITY`); facts there omitted. A single-driver +30/−30 paired residual → **no** unhealthy window |
| FX-SUP-08 | #35 health (b) | SYN | U | In-race interval [6000, 6300] with no lap-fixture check: (i) and no RCM anchor within ±60 s in band → unhealthy; (ii) an RCM anchor at 6150 with deviation +0.3 s → healthy; (iii) an anchor with deviation +0.9 s (outside [−1.2, +0.7]) → unhealthy |
| FX-SUP-09 | #35 pre-race | SYN | U | Started at 3400. A pre-race fact at P = 3094.9 → admitted for in-race checkpoints. P = 3095.0 → omitted |
| FX-SUP-10 | #35 health (c) | SYN | U | A record after the last `Finished` → unhealthy; never admitted as a fact for in-race checkpoints |
| FX-SUP-11 | #35 (D) | SYN | U | `TotalLaps` series [(5, 58), (47, 0), (453, 58)] → value 58, with the 0 ignored. Series [(9.9, 0), (13.6, 44)] → 44. Series [(5, 0)] only → `SCHEDULED_DISTANCE_UNAVAILABLE` |
| FX-SUP-12 | #35 (C) | REAL(S-RD) | C | The `c(E)` method on S-RD → 1998/1998 Jolpica in-lap matches (FX-TGT-02 cross-check) |
| FX-SUP-13 | #35 (C) | SYN | U | Red-flag race: all cars `Stopped:true` at P = 5000, all advance laps after 5600 → no terminal assigned (red-flag rule). (Regression guard for the unexplained Tuscany 2020 behaviour in S-RG) |
| FX-SUP-14 | #35 provenance | SYN | C | A `CONFIRMED_TYRE_SERVICE` produced by the positive rule carries the support-record reference noting limited independent validation |

## Evaluation protocol (#37)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-EVL-01 | §1 | SYN | U | p_j = 0.25 → S = 1.386294. Set {1, 2} with masses 0.5 and 0.25 → S = 0.287682. q = 0.0625 → S = 2.772589 |
| FX-EVL-02 | §1 | SYN | U | A unit with realized-outcome probability 0 → unit S = +∞; aggregate +∞; claim reported as failed; accounting unchanged |
| FX-EVL-03 | §1 floor | SYN | U | K_T = 3, p = [1, 0, 0], q = 0 → floored p' = [0.999997, 1e-6, 1e-6], q' = 1e-6; sum 1. Re-expressed hazards round-trip through `hazard/v1` to p' (within 1e-12) |
| FX-EVL-04 | §1 floor | SYN | C | Lock check: a development snapshot with min probability 5e-7 → lock refused |
| FX-EVL-05 | §2 | SYN | U | Paired ΔS over units {(1.0, 1.2), (0.5, 0.4)} → ΔS = −0.05 |
| FX-EVL-06 | §3 | SYN | U | G = 12 races with known per-unit differences → the CR2 SE matches a reference implementation (within 1e-9), and the interval uses t with 11 degrees of freedom. G = 7 → interval flagged descriptive-only |
| FX-EVL-07 | §3 | SYN | U | Wild cluster bootstrap with seed s → reproducible interval; Webb six-point weights used |
| FX-EVL-08 | §4 | SYN | C | B1 input at T with an omitted compound → B1 emits B0's distribution. Latest admissible stint update `TyresNotChanged:"1"` → B0 fallback. No stint update since the last entry → B0 fallback |
| FX-EVL-09 | §6 | SYN | U | Candidates A (rank 2, mean 1.000) and C (rank 1, mean 1.020, ΔS_C,A = 0.020, SE 0.030) → choose C. If SE = 0.010 → choose A |
| FX-EVL-10 | §6 | SYN | U | The chosen candidate has ΔS against B1 ≥ 0 on development → lock B1, and the primary comparison becomes B1 against B0 |
| FX-EVL-11 | §6 | SYN | C | An 11th candidate registered → refused. B0 and B1 do not count toward the budget |
| FX-EVL-12 | §7 | SYN | C | The F2 inclusion check parses no record content (instrumented reader). A race with HTTP 200, race-day `Last-Modified` and identical hashes 24 h apart → admitted. Hashes differ → excluded |
| FX-EVL-13 | §8 | SYN | U | Run with A6 = 600, A9 + A10 + A11 = 500 → share = 0.545 → `analysis_class` downgraded to `SECONDARY`; `ledger_role` unchanged |
| FX-EVL-14 | §8.5 | SYN | U | A6 unit with indeterminate visit at region v = 3, p = [0.1, 0.2, 0.1, 0.3, …] → S_a = −ln 0.3, S_b = −ln(1 − 0.4). Without a visit lap context → diagnostic reported "not computable" |

## Cross-component reference scenarios (end to end)

Each scenario runs the full chain: observation → eligibility/initialization → prediction → resolution → mapping → accounting → score. Each uses a synthetic session (`SYN`) unless stated.

| ID | Scenario | Expected end state |
| --- | --- | --- |
| FX-E2E-01 | **Observed event.** #16, L = 20 at T = 5000. N_T = 57 (K_T = 37). Confirmed tyre service at entry P = 5450 with c = 22 | Snapshot created; `OBSERVED_EVENT`; `REALIZED_REGION {2}`; category A9; scored `−ln p_2` |
| FX-E2E-02 | **Terminal no-event.** #16, L = 50 at T = 8200. No visits until the finish at 8900. Complete coverage | `TERMINAL_NO_EVENT` → `REALIZED_NO_EVENT` → A11 → scored `−ln q` |
| FX-E2E-03 | **Truncated.** As E2E-01, but the visit at 5450 has `TyresNotChanged:"1"` and no penalty | `TRUNCATED_INDETERMINATE` → `NOT_REALIZED` → A6; not scored; counted in the truncation share |
| FX-E2E-04 | **Ineligible.** #31 has `Retired:true` before T | `INELIGIBLE`; no request or snapshot; A2 |
| FX-E2E-05 | **Defective.** As E2E-01, but the lap evidence jumps before the entry (no `EntryLapContext`) | `MAPPING_UNAVAILABLE` → A8 → run `DEFECTIVE` → no `PRIMARY` score |
| FX-E2E-06 | **Leakage: future fact.** A rival's pit entry at P = 5003 (same stream, **after** the L = 20 trigger record at P = 5000) and an RCM message at P = 4993 (cross-stream, within 10 s) | Neither appears in the L = 20 observation, its input view or the snapshot (dependency-closure and content assertions) |
| FX-E2E-07 | **Successive checkpoints, same event.** L = 20 (T = 5000) and L = 21 (T = 5090), event at 5450 with c = 22 | Two snapshots and two units: regions {2} on L = 20's grid and {1} on L = 21's grid; same `eventual_event_key`; distinct episodes |
| FX-E2E-08 | **Clock anomaly.** Common-mode window [6000, 6200]; a lap trigger at 6100 | `INDETERMINATE_CHECKPOINT`; no observation; A1; no snapshot |
| FX-E2E-09 | **Real-session smoke test.** REAL(S-RD): one race (Spanish 2024) through the full chain | Each A9 unit's `c(E)` agrees with Jolpica; every category count is reproducible across two runs; no `MAPPING_CONFLICT` |

## Deferred and routed items

| Item | Reason / route |
| --- | --- |
| #19 T-6 (`PitInTime` comparison) | Not used canonically (#35). An optional diagnostic only |
| A real red-flag countback session | Not in the inspected samples; FX-TGT-28 and FX-PRD-12 are synthetic. Add a REAL fixture when such a session is identified in S-RD |
| §8.5 visit lap context (#37) | Cross-slice dependency on #19; FX-EVL-14 covers the "not computable" path |
| Tuscany 2020 terminal behaviour (S-RG) | Root cause unexplained (#35). FX-SUP-13 guards the red-flag rule; S-RG terminal claims stay qualified |

No design contradiction was found while compiling this catalog.

## Acceptance mapping (Issue #36)

- **Every handoff item mapped or explicitly deferred:** see *Traceability index* and *Deferred and routed items*.
- **Expected results unambiguous and traceable:** every entry cites its source clause and states exact values.
- **End-to-end leakage and state-distinctness scenarios present:** FX-E2E-01…09, FX-PRD-18 and FX-RPL-03.
- **Independent review:** pending.

## Review record

Pending an independent full scoped review under `governance/REVIEW_POLICY.md`.
