# V2 Reference Scenarios and Acceptance Fixture Catalog

## Status

Approved, including the split section. The bounded re-review on PR #40 (head `d2b15d5`) resolved all 23 prior findings, but found two Major regressions (N1, N2) in FX-E2E-04 and FX-E2E-10.

Under the non-convergence rule, those two scenarios were **split into Issue #41**, which gets its own independent review. They are fixed in this file and marked "split slice, #41". The #41 sub-slice passed its bounded re-review (see *Split sub-slice (#41) review*). Minor findings N3–N9 are applied. Every other entry stands as reviewed.

## Abstraction level

This is a verification specification. It turns three sources into catalogued reference scenarios and acceptance fixtures with exact expected outcomes:

- every verification handoff item of the approved designs;
- the verification parameters of #35;
- the verification parameters of #37.

Implementation turns each entry into an automated test without inventing expected behaviour. Where a design leaves a case undecided, the entry is marked **PENDING-OWNER** and routed. The catalog never decides such a case itself.

## Issue / branch

- Issue: #36 (parent #34).
- Branch: `ccr-d8f3e250-t7uix3`. PR: #40.
- Sources:
  - #18 `design/OBSERVATION_RECONSTRUCTION.md` (O-1…O-15);
  - #19 `design/TARGET_RECONSTRUCTION.md` (T-1…T-25);
  - #20 `design/PREDICTION_CONTRACT.md` (P-1…P-10, P-6a);
  - #21 `design/REPLAY_BACKTEST.md` (R-1…R-12);
  - gate observation O3 (`design/DESIGN_INTEGRATION.md`);
  - #35 `verification/SUPPORT_MATRIX.md`;
  - #37 `verification/EVALUATION_PROTOCOL.md`.

## Conventions

- **ID prefix** gives the owner: `FX-OBS` (#18), `FX-TGT` (#19), `FX-PRD` (#20), `FX-RPL` (#21), `FX-SUP` (#35), `FX-EVL` (#37), `FX-E2E` (cross-component).
- **Basis:**
  - `SYN`: a synthetic stream or artifact built in the test.
  - `REAL(key, scope)`: a frozen real session, cited by `RaceSessionKey` (season, round). Its bytes must match the SHA-256 recorded in `verification/evidence/probe_*_v2.json`. Scope is a #35 scope.
  - `REAL+TAMPER`: a real session with a deliberately altered byte or hash.
- **Level:** `U` unit (pure function); `C` contract (artifact or invariant at a boundary); `E2E` chain; `L` leakage or dependency closure.
- **Synthetic session defaults.** These apply unless an entry overrides them.
  - Source scope S-RD, so `VERIFIED_BOUNDED_TIME` bounds [P − 5, P + 5].
  - `SessionStatus`: `Started` at P = 3600 for the leader's race; `Finished` at P = 9000, when the leader takes the flag.
  - `LapCount.TotalLaps` = 57 at P = 60.
  - The generator emits, for every running driver, a `TimingData` lap advance carrying `LastLapTime` at least every 100 s, with residual 0 (lap-time fixture checks).
  - The generator emits one RCM anchor every 60 s with a deviation of 0. All windows are therefore clock-healthy by construction.
  - Heartbeat is not generated; it plays no part in the error model.
  - Unless given, stream order equals prefix order.
- **Exactness.** Expected values are exact expressions (e.g. `−ln 0.25`, `600/1100`). Implementations compare floating-point results to 1e-12 unless an entry states otherwise.
- **PENDING-OWNER.** The tested behaviour depends on a clarification routed under *Routing*. The fixture is written for the unambiguous part, and the open part is marked.

## Traceability index

| Source items | Catalog entries |
| --- | --- |
| #18 O-1, O-2, O-3, O-13 | FX-SUP-01…04, FX-OBS-20, FX-OBS-21 |
| #18 O-4 | FX-OBS-01, FX-OBS-02, FX-OBS-20 |
| #18 O-5 | FX-OBS-03…05, FX-OBS-21 |
| #18 O-6, O-12 | FX-OBS-06, FX-OBS-07 |
| #18 O-7 | FX-SUP-05, FX-SUP-06, FX-SUP-07, FX-SUP-08 |
| #18 O-8 | FX-OBS-08, FX-OBS-09a |
| #18 O-9 | FX-OBS-09 |
| #18 O-10 | FX-OBS-10, FX-OBS-22 |
| #18 O-11 | FX-OBS-11 |
| #18 O-14 | FX-OBS-12…16 |
| #18 O-15 | FX-OBS-17…19, FX-OBS-23, FX-SUP-11 |
| #19 T-1 | FX-TGT-01, FX-TGT-02 |
| #19 T-2 | FX-TGT-03, FX-TGT-03a |
| #19 T-3 | FX-TGT-04 |
| #19 T-4 | FX-TGT-05, FX-TGT-05a; reset/correction DEFERRED |
| #19 T-5 | FX-TGT-06 |
| #19 T-6 | DEFERRED |
| #19 T-7, T-8 | FX-TGT-08, FX-TGT-09 |
| #19 T-9 | FX-TGT-10, FX-TGT-10a; repair-only DEFERRED |
| #19 T-10, T-11, T-12 | FX-TGT-11…13 |
| #19 T-13 | FX-TGT-14, FX-TGT-14a |
| #19 T-14, T-15 | FX-TGT-15, FX-TGT-15a, FX-TGT-16 |
| #19 T-16 | FX-TGT-17 |
| #19 T-17 | FX-TGT-18…20, FX-TGT-20a |
| #19 T-18, T-19 | FX-TGT-21, FX-TGT-22 |
| #19 T-20 | FX-TGT-23 |
| #19 T-21 | FX-TGT-24 |
| #19 T-22 | FX-TGT-25 |
| #19 T-23 | FX-TGT-26 |
| #19 T-24 | FX-TGT-27…29, FX-TGT-29a |
| #19 T-25 | FX-TGT-30 |
| #20 P-1…P-3 | FX-PRD-01…04 |
| #20 P-4 | FX-PRD-05 |
| #20 P-5 | FX-PRD-06, FX-PRD-07 |
| #20 P-6 | FX-PRD-08…12 |
| #20 P-6a | FX-PRD-13 |
| #20 P-7 | FX-PRD-14…17 |
| #20 P-8 | FX-PRD-18 |
| #20 P-9 | FX-PRD-19 |
| #20 P-10 | FX-PRD-20 |
| #20 (#18 A1 dependency) | FX-PRD-21 |
| #21 R-1 | FX-RPL-01, FX-RPL-02 |
| #21 R-2 | FX-RPL-03 |
| #21 R-3 | FX-RPL-04 |
| #21 R-4 | FX-RPL-05 |
| #21 R-5 | FX-RPL-06…13 (reseed case: see FX-RPL-07 note) |
| #21 R-6 | FX-RPL-14 |
| #21 R-7 | FX-RPL-15…18, FX-RPL-15a, FX-RPL-15b, FX-RPL-17a |
| #21 R-8 | FX-RPL-19, FX-RPL-20 |
| #21 R-9 | FX-RPL-21 |
| #21 R-10 | FX-RPL-22 |
| #21 R-11 | FX-RPL-23 |
| #21 R-12 | FX-RPL-24 |
| Gate O3 | FX-RPL-25 (PENDING-OWNER), FX-RPL-26 |
| #35 parameters | FX-SUP-01…14 |
| #37 parameters | FX-EVL-01…14 |
| Cross-component | FX-E2E-01…10 |

## Observation reconstruction (#18)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-OBS-01 | O-4 | SYN | C | `Started` at P = 3600 → exactly one `RACE_START` checkpoint, `completed_laps = 0`, boundary [3595, 3605] |
| FX-OBS-02 | O-4 | SYN | C | `Started` at 3600, `Aborted` at 5000, `Started` at 5600 → one `RACE_START` checkpoint (3600). The restart creates no second start checkpoint; lap checkpoints continue on the counter |
| FX-OBS-03 | O-5 | SYN | C | Driver 44: `NumberOfLaps` 1 @3700, 2 @3790, 2 @3791 (duplicate), 3 @3880 → checkpoints L1 @3700, L2 @3790, L3 @3880. The duplicate creates nothing |
| FX-OBS-04 | O-5 | SYN | C | Driver 44: 5 @4010, then 7 @4100 → L7 @4100. The L6 attempt record is `INDETERMINATE_CHECKPOINT` with reason `LAP_COUNT_JUMP` |
| FX-OBS-05 | O-5 | SYN | C | Driver 44: 8 @4300, 7 @4350 (regression), 8 @4400 → the L8 checkpoint stays at 4300. The 4350 record is preserved; 4400 creates no new checkpoint. Observations after 4350 (same stream) reflect count 7 until 4400, then 8 |
| FX-OBS-06 | O-6 | REAL((2025,12), S-RD) | C | All 8 streams → stored bytes reproduce the evidence SHA-256 values. `ArchiveRecordKey` ordinals are contiguous from 0 and prefixes are unchanged. No `SourceAvailabilityKey` exists without an authority-validation reference |
| FX-OBS-07 | O-12 | REAL((2025,12), S-RD) | C | Reconstruct twice from identical snapshot and configuration → identical observation digests and identical attempt-record lists |
| FX-OBS-08 | O-8 | SYN | C | Driver 44 counts 20 @4910. A malformed `TimingData` line follows @5000. The next valid driver-44 record is count 22 @5090 → the malformed line is counted in gap metadata and no fact is taken from it. L21 attempt: `INDETERMINATE_CHECKPOINT` (`LAP_COUNT_JUMP`). L22 checkpoint @5090 is valid |
| FX-OBS-09a | O-8 (recovery) | SYN | C | The **whole** `TimingData` stream has no records between P = 5000 and P = 5300, declared a continuity gap in the source manifest. Driver 44's next `Position` value arrives @5320 → observations whose trigger comes after the gap start in stream order, and before the 5320 record, carry driver 44's `Position` as **unknown** (omitted), not the stale value. Later observations carry the new value (#18: state unknown after a gap until reset) |
| FX-OBS-09 | O-9 | SYN | C | FastF1 `Laps.Time` differs from the raw advance prefix by 3 s → the boundary uses the raw prefix only. Processed values never become availability evidence |
| FX-OBS-10 | O-10 | SYN | C | Driver 1 `LastLapTime` for lap 10 is 1:32.5 @4000, corrected to 1:33.0 @4500 (`TimingData`, same stream as the lap triggers) → an observation whose trigger precedes 4500 in stream order shows 1:32.5. A trigger after the 4500 record in stream order shows 1:33.0 (same-stream rule, #35). The L10 artifact is unchanged after the correction |
| FX-OBS-11 | O-11 | SYN | C | Driver 44 L10 trigger @5000. Driver 1 sector update @4985 (same stream, earlier in order) → admitted. Driver 1 lap-12 advance @5003 (after the trigger in order) → excluded. No equal-lap alignment |
| FX-OBS-12 | O-14 | SYN | C | Session identity mismatch → one `SESSION` record `INDETERMINATE_IDENTITY`, no children |
| FX-OBS-13 | O-14 | SYN | C | Entry 16 with lap evidence up to 57 → one `DRIVER_ENTRY` (`ESTABLISHED`) and 58 `CHECKPOINT` records (L0…L57), all with unique `attempt_key` |
| FX-OBS-14 | O-14 | SYN | C | Two candidates share number 81 → two `DRIVER_ENTRY` records `INDETERMINATE_IDENTITY` with distinct `driver_alias` values (provider ID or roster ordinal), no checkpoints, unique keys |
| FX-OBS-15 | O-14 | SYN | C | (a) Established entry with no lap evidence → its `DRIVER_ENTRY` is `ENUMERATION_INCOMPLETE` (`LAP_COUNT_EVIDENCE_MISSING`), plus a `RACE_START` record. (b) Established identity, zero candidates → `SESSION` `ENUMERATION_INCOMPLETE` (`NO_ENTRY_CANDIDATES`). (c) Established identity, entry enumeration prevented by a missing `DriverList` and missing `TimingData` → `SESSION` `INDETERMINATE_SOURCE`, no children |
| FX-OBS-16 | O-14 | SYN | L | Stream tail truncated at count 40 (race ran 57) → `L_max` = 40 and 41 attempts. `L_max` appears in no observation content or boundary (dependency-closure inspection) |
| FX-OBS-17 | O-15 | SYN | C | `TotalLaps` 58 @6 → the start observation (`Started` 3600) has `SCHEDULED_RACE_DISTANCE_LAPS` = 58. Admitted because 6 + 300 < 3595 |
| FX-OBS-18 | O-15 | SYN | C | `TotalLaps` 58 @6, revised to 57 @3550 (aborted start) → the revision fails the #35 pre-race margin (3550 + 300 ≥ 3595). It is **not admissible for any in-race checkpoint**, so **every** in-race observation carries 58. (Consequence routed: see Routing R-A) |
| FX-OBS-19 | O-15 | SYN | C | Only a final-classification distance exists → fact omitted with `SCHEDULED_DISTANCE_UNAVAILABLE`, and #20 yields `REQUIRED_CONTEXT_MISSING` (FX-PRD-21) |
| FX-OBS-20 | O-3, O-4 | SYN | C | The same `SessionStatus` stream classified S-RG (rewritten archive) → no `RACE_START` checkpoint. The attempt record is `INDETERMINATE_CHECKPOINT` (`ARCHIVE_AVAILABILITY_UNVERIFIED`). A session whose archive request returns HTTP 403 (S-22, no bytes) → `SESSION` `INDETERMINATE_SOURCE` with reason `SOURCE_STREAM_MISSING`, and scope class `UNSUPPORTED` |
| FX-OBS-21 | O-3, O-5 | SYN | C | `TimingData` lap advances in an S-RG-classified source → every lap-checkpoint attempt is `INDETERMINATE_CHECKPOINT` (`ARCHIVE_AVAILABILITY_UNVERIFIED`), even though prefixes and counts look plausible (#18 rule 6) |
| FX-OBS-22 | O-10 (#35 F-A3) | SYN | C | Driver 63's lap-38 advance is published late @7248, while the other drivers' advances are normal. The lap-fixture residuals for driver 63 are +69.9 s on lap 38 and −69.9 s on lap 39; all other drivers are normal → the L38 checkpoint boundary is P = 7248 (the late prefix). No unhealthy window is created (single driver) |
| FX-OBS-23 | O-15 | SYN | C | S-RD observation → the `SCHEDULED_RACE_DISTANCE_LAPS` fact class is the streamed bounded-time class, not `STATIC_PRIOR`. The `DISTANCE_REVISION_CHANNEL_UNVERIFIED` reason code is absent |

## Target reconstruction (#19)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-TGT-01 | T-1 | SYN | U | Driver 16 `InPit` False→True @5000, True→False @5022 → one `PitVisitArtifact`, entry 5000, exit 5022 |
| FX-TGT-02 | T-1 | REAL(all 55 S-RD keys) | C | Jolpica stops (frozen responses, hashes as in `capabilities_raceday_scope_v2.json`) → each stop has exactly one visit with `c(E) + 1 ==` Jolpica lap. Total 1998/1998 |
| FX-TGT-03 | T-2 | SYN | C | `InPit` entry @1200 (before `Started`) → `OUTSIDE_RACE_PARTICIPATION`; no qualifying event |
| FX-TGT-03a | T-2 (first-lap edge) | SYN | C | `Started` @3600, bounded [3595, 3605]; entry @3602, bounded [3597, 3607] → overlap gives `INDETERMINATE_RACE_PARTICIPATION`. An entry @3612 ([3607, 3617]) → `IN_RACE_PARTICIPATION` |
| FX-TGT-04 | T-3 | SYN | C | Driver 31: last advance @5950, `Retired:true` @6000, entry @6100 ([6095, 6105] ≥ the terminal upper bound 6000) → `OUTSIDE_RACE_PARTICIPATION`. Any entry after the driver's finish terminal is likewise outside |
| FX-TGT-05 | T-4 | SYN | C | (b) `InPit:false` with no prior entry → segmentation anomaly flagged; no visit. (c) Entry with no exit before session end → exit-open visit retained. **(a) PENDING-OWNER:** a second `InPit:true` 0.4 s after the first, with no exit between. Whether it is a duplicate (one visit) or an anomaly depends on the source-lineage equivalence criterion. Routed (R-B) |
| FX-TGT-05a | T-4 (malformed) | SYN | C | A malformed `TimingData` line inside [entry, entry + 40] of a visit, before any exit record, so it could hide an exit and re-entry → the visit's `visit_segmentation_quality` is degraded. An episode for which this visit could be the earliest qualifying event is `TRUNCATED_INDETERMINATE` (#19 rule 9: a gap that can change visit identity). A malformed line after a proven earlier event does not change that episode |
| FX-TGT-06 | T-5 | SYN | C | Driver 4: entry @5000 (exit 5021), entry @5040 (exit 5062), both with c = 30 → two visits with distinct `visit_discriminator`, ordered by stream order |
| FX-TGT-08 | T-7 | SYN | U | Window updates: stint 2 `{TyresNotChanged:"1"}` @entry+1, then stint 2 `{TyresNotChanged:"0", New:"true", Compound:"HARD"}` @entry+6 → `CONFIRMED_TYRE_SERVICE` (last update) |
| FX-TGT-09 | T-8 | SYN | U | Last update `{TyresNotChanged:"0", New:"false", Compound:"MEDIUM", StartLaps:8}`, previous stint MEDIUM → `CONFIRMED_TYRE_SERVICE`. Compound equality is not a negative |
| FX-TGT-10 | T-9 | SYN | C | RCM "DRIVE THROUGH PENALTY FOR CAR 63" @7400. Driver 63's first in-race entry after it is @7647, and its last stint update has `TyresNotChanged:"1"`. RCM "PENALTY SERVED - DRIVE THROUGH PENALTY FOR CAR 63" @8950 (before `Finished`) → `CONFIRMED_NO_TYRE_SERVICE`. (A served-penalty visit with `TyresNotChanged:"0"` is a conflict: PENDING-OWNER, routed R-C) |
| FX-TGT-10a | T-9 (stop-and-go) | SYN | C | As FX-TGT-10, with "STOP-AND-GO PENALTY FOR CAR 20" issued and served → `CONFIRMED_NO_TYRE_SERVICE` |
| FX-TGT-11 | T-10 | REAL(S-RD) | C | The S-RD penalty test set (9 visits, `capabilities_raceday_scope_v2.json`) → all have last update `"1"`, none `"0"`. A visit with `"1"` and no penalty → `INDETERMINATE_TYRE_SERVICE` |
| FX-TGT-12 | T-11 | SYN | U | Drive-through opens stint 1 `{TyresNotChanged:"1", StartLaps:53}`, no penalty messages → `INDETERMINATE_TYRE_SERVICE`, despite the increment |
| FX-TGT-13 | T-12 | SYN | U | No stint update in [entry, next entry) → `INDETERMINATE_TYRE_SERVICE` |
| FX-TGT-14 | T-13 | SYN | U | T bounds [4995, 5005] → E @5011 ([5006, 5016]) is `STRICTLY_AFTER_T`. E @5009 is `INDETERMINATE_PREDICTION_RELATION`. E @4989 ([4984, 4994]) is `BEFORE_OR_AT_T`. E @4994 ([4989, 4999]) is indeterminate |
| FX-TGT-14a | T-13 (exact) | SYN | U | Relation function with **exact** times: E = T = 5000 → `BEFORE_OR_AT_T` (equality never promoted). E = 5000.001 → `STRICTLY_AFTER_T` |
| FX-TGT-15 | T-14 | SYN | U | B bounded (5950, 6000]. Entry [5935, 5945] → `STRICTLY_BEFORE_TERMINAL`. [6005, 6015] → `AT_OR_AFTER_TERMINAL`. [5955, 5965] → `INDETERMINATE_TERMINAL_RELATION` |
| FX-TGT-15a | T-14 (exact) | SYN | U | Exact E = B = 6000 → `AT_OR_AFTER_TERMINAL` |
| FX-TGT-16 | T-15 | SYN | C | Episode T bounds [4995, 5005]; finish terminal B = driver lap completion @9050 (bounded [9045, 9055]); confirmed-service in-scope entries @5600 and @7000 → `OBSERVED_EVENT` referencing the 5600 event. A confirmed-service entry @9100 never resolves any episode |
| FX-TGT-17 | T-16 | SYN | C | Episode T bounds [5495, 5505], finish B = 9050. Driver 22: entry @6000 (exit @6004), entry @6008, both confirmed service. Bounds [5995, 6005] and [6003, 6013] overlap, but `TimingData` stream order fixes entry 1 before entry 2 (RA-3) → `OBSERVED_EVENT` on the 6000 entry. Truncation for genuinely unorderable candidates cannot occur within one stream in S-RD, so this sub-case is not constructible there |
| FX-TGT-18 | T-17 | SYN | U | Driver 31: last advance @5950, `Retired:true` @6000 → terminal; B ∈ (5950, 6000] |
| FX-TGT-19 | T-17 | SYN | U | (i) `Stopped:true` @6000 after the last advance (5950) and before the last `Finished` → terminal. (ii) `Stopped:true` @5000 with advances after 5100 (red flag) → not terminal. (iii) In-race black flag: RCM "BLACK FLAG ... CAR 27" @7000, no further advances, `Stopped` @7020 → terminal. (iv) A post-race disqualification exists only in final results (no archive signal) → not a participation terminal |
| FX-TGT-20 | T-17 | REAL(S-RD) | C | Combined rule versus Jolpica non-finishers (disqualifications excluded) → 157/158 (`capabilities_raceday_scope_v2.json`); regression guard |
| FX-TGT-20a | T-17 (finish) | SYN | U | Leader `Finished` @9000. Driver 1 completes lap 57 @9000 → finish terminal B = 9000 (that completion). Lapped driver 18 completes lap 56 @9080, its first completion after `Finished` → B = 9080. Driver 20 completes nothing after 9000 and is not retired → coverage indeterminate; episodes needing B for no-event are `TRUNCATED_INDETERMINATE` |
| FX-TGT-21 | T-18 | SYN | C | Driver 10: episode T bounds [5795, 5805], finish B = 9050. A `TimingData` gap over [6000, 6200], no confirmed event before 6000 → `TRUNCATED_INDETERMINATE`. Same gap but a confirmed in-scope event @5900 → `OBSERVED_EVENT` |
| FX-TGT-22 | T-19 | SYN | C | Driver 16: episode T bounds [8195, 8205], no visits until its finish terminal B = 9050 ([9045, 9055]), complete coverage → `TERMINAL_NO_EVENT`. Same, but an `INDETERMINATE_TYRE_SERVICE` visit @8700 → `TRUNCATED_INDETERMINATE` |
| FX-TGT-23 | T-20 | SYN | C | L20 (T = 5000) and L21 (T = 5090), one confirmed event @5200 (c = 22) → two episodes, both `OBSERVED_EVENT`, same `event_key` |
| FX-TGT-24 | T-21 | SYN | C | Re-resolve under a second resolution run → two immutable artifacts; one selected per `resolution_run_ref`; the first is unchanged |
| FX-TGT-25 | T-22 | REAL((2025,12), S-RD) | C | Resolve twice with identical inputs → identical resolution digests |
| FX-TGT-26 | T-23 | REAL(all 55 S-RD keys) | C | The `c(E)` counter equals the #18 checkpoint counter. 0 jumps, 0 regressions (`capabilities_raceday_scope_v2.json`) |
| FX-TGT-27 | T-24 | SYN | U | Advances lap 30 @4900, lap 31 @5000. Entry record after the lap-31 record in stream order → `c_exact` = 31. Entry before it → 30. (Equal-instant completion counts as completed) |
| FX-TGT-28 | T-24 | SYN | U | Red flag after lap 40, classification countback to 39, as-raced counter 40 at entry → `c_exact` = 40 |
| FX-TGT-29 | T-24 | SYN | U | Driver count jumps 30 → 32 before the entry → no `EntryLapContext`; `entry_lap_context_absent_reason` is set; still `OBSERVED_EVENT` |
| FX-TGT-29a | T-24 (bounded formula) | SYN | U | #19 formula with bounded inputs: laps 1–29 certainly completed earlier; C₃₀ = [4895, 4905]; C₃₁ = [4995, 5005]; no further completions; E = [4998, 5008] → `c_lo` = 30, `c_hi` = 31. (In S-RD the order-based method is always exact, so this exercises the formula only) |
| FX-TGT-30 | T-25 | SYN | C | #18 run with 10 canonical observations (7 eligible, 2 ineligible, 1 indeterminate) → manifest has 10 records and 7 initializations; an initialization is present iff the decision is `ELIGIBLE` |

## Prediction contract (#20)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-PRD-01 | P-1 | SYN | U | L = 10, N_T = 57 → K_T = 47. c = 10 → R_0; c = 30 → R_20; c = 56 → R_46; c = 60 → R_46 |
| FX-PRD-02 | P-1 | SYN | U | Property test: L ∈ [0, 77], N_T ∈ [44, 78], c ≥ L → exactly one index in [0, K_T − 1] |
| FX-PRD-03 | P-2 | SYN | U | (L = 56, N_T = 57) → K_T = 1 and c = 56 → R_0. (L = 57, N_T = 57) → K_T = 1. A one-region distribution plus `q` is valid |
| FX-PRD-04 | P-3 | SYN | U | N_T = 71 at T, L = 60, so K_T = 11. Race shortened to 69. Event with c = 68 → R_8. Lapped finisher with c = 66 → R_6 |
| FX-PRD-05 | P-4 | SYN | C | Two paths. **(i) Canonical validator, invoked directly** with a `CanonicalDistribution`: `p₀ = NaN` → V1; `p₁ = −0.1` → V2; `len(p) = K_T − 1` → V3; `q` absent → V5. **(ii) Through the prediction procedure:** PMF with sum + q = 1.001 → V4; extra `"truncated"` outcome → V6; grid L ≠ observation L → V7. On path (ii), NaN → R3, −0.1 → R4, wrong length → R2, missing `q` → R2. Every failure yields a `PredictionFailureRecord` and no snapshot |
| FX-PRD-06 | P-5 | SYN | U | Hazard K_T = 3, λ = [0.2, 0.5], q_open = 0.25 → p = [0.2, 0.4, 0.3], q = 0.1 |
| FX-PRD-07 | P-5 | SYN | U | PMF with sum + q = 1 + 5e-7 → rescaled, `normalization_applied = true`. 1 + 2e-6 → V4 |
| FX-PRD-08 | P-6 | SYN | U | L = 10, K_T = 47, [c_lo, c_hi] = [12, 13] → `REALIZED_REGION_SET {2..3}` |
| FX-PRD-09 | P-6 | SYN | U | [9, 11] → c_lo' = 10 → `{0..1}`. [7, 9] → `MAPPING_CONFLICT`. Exact c = 9 → `MAPPING_CONFLICT` |
| FX-PRD-10 | P-6 | SYN | U | `OBSERVED_EVENT` with `entry_lap_context_absent_reason` → `MAPPING_UNAVAILABLE` |
| FX-PRD-11 | P-6 | SYN | U | `TRUNCATED_INDETERMINATE` → `NOT_REALIZED`. `TERMINAL_NO_EVENT` → `REALIZED_NO_EVENT` |
| FX-PRD-12 | P-6 | SYN | U | Countback context (FX-TGT-28) with L = 35 → index 5 |
| FX-PRD-13 | P-6a | SYN | C | Hazard λ = [1.0], q_open = 1.5 (K_T = 2) → R4 before conversion. Wrong form → R1. len(λ) ≠ K_T − 1 → R2. NaN → R3 |
| FX-PRD-14 | P-7 | SYN | U | p = [0.125, 0.5, 0.25, 0.0625], q = 0.0625, α = 0.8, L = 10 → window [1, 2], in-laps 12–13; masses: in 0.75, before 0.125, after 0.0625, q 0.0625 |
| FX-PRD-15 | P-7 | SYN | U | p = [0.25, 0.25, 0.25, 0.125], q = 0.125, α = 0.5 → [0, 1] (smallest a breaks the tie) |
| FX-PRD-16 | P-7 | SYN | U | q = 1, p = 0 → `NONE`, all masses 0 |
| FX-PRD-17 | P-7 | SYN | U | α = 1, p = [0.5, 0, 0.25, 0.25], q = 0 → [0, 3], last region labelled "L + K_T or later" |
| FX-PRD-18 | P-8 | SYN | L | A `TargetResolutionArtifact`, score or event offered to the request builder or input-view derivation → `FORBIDDEN_INPUT`. Static import check: prediction and input-view modules import no target-resolution or evaluation module |
| FX-PRD-19 | P-9 | SYN | C | FX-TGT-23 episodes → two snapshots with distinct `prediction_key`. Re-resolution leaves both `snapshot_id` and `content_digest` unchanged |
| FX-PRD-20 | P-10 | SYN | C | Same `request_digest` in a new run → identical distribution and `content_digest`; new `prediction_key` and `snapshot_id` |
| FX-PRD-21 | #18 A1 / #20 | SYN | C | Observation lacking `SCHEDULED_RACE_DISTANCE_LAPS` → `REQUIRED_CONTEXT_MISSING`; no snapshot |

## Replay and backtest (#21; gate O3)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-RPL-01 | R-1 | SYN | U | Attempt records: SESSION (ESTABLISHED); DE 1; DE 44; DE alias "cand-2"; CP 1 L0, CP 1 L1, CP 44 L0 → manifest order is SESSION, DE 1, DE 44, DE cand-2, CP 1 L0, CP 1 L1, CP 44 L0 |
| FX-RPL-02 | R-1 | SYN | U | (i) Exact tie: driver 44 L1 and driver 1 L1, both bounds [4995, 5005] → driver 1 first (manifest key). (ii) Differing bounds: driver 44 L1 [4995, 5005]; driver 1 L1 [4998, 5004] → driver 1 first (upper bound 5004 < 5005) |
| FX-RPL-03 | R-2 | SYN | L | A `TargetResolutionArtifact` as a direct replay input → run `ABORTED`. A model artifact whose provenance references development resolutions → allowed |
| FX-RPL-04 | R-3 | SYN | C | Replay R1; then a new resolution run, a backtest, and replay R2 → R1 snapshots byte-identical |
| FX-RPL-05 | R-4 | SYN | C | Races r1 < r2 < r3. Cutoff r2 predicting r2 → accepted. Cutoff r2 predicting r1 → refused. `PER_RACE` schedule {r2: cutoff r2, r3: cutoff r2} → accepted. {r3: cutoff after r3} → refused |
| FX-RPL-06 | R-5 | SYN | C | Final backtest without a lock → refused |
| FX-RPL-07 | R-5 | SYN | C | First `FINAL_EVALUATION` of r under L1 → `PRIMARY_FINAL`. Matching rerun under L1 → `REPRODUCTION`. Rerun with a different inference seed policy → **refused at replay** (seed must equal the lock's). *Note:* #21 R-5's "reseeded rerun under the same lock is `POST_HOC`" cannot be reached, because #21 refuses the mismatch earlier. The reachable reseed path is a new lock with different seeds (FX-RPL-09). Wording routed (R-E) |
| FX-RPL-08 | R-5 | SYN | C | Rerun under L1 with non-matching contents → `POST_HOC` |
| FX-RPL-09 | R-5 | SYN | C | New protocol and lock L2 (different seeds) evaluating already-opened r → `POST_HOC` |
| FX-RPL-10 | R-5 | SYN | C | New primary claim on {r (opened), r4 (fresh)} → rejected |
| FX-RPL-11 | R-5 | SYN | C | Registered `AD_HOC_OPENING` of r5, then the first `FINAL_EVALUATION` → `POST_HOC` |
| FX-RPL-12 | R-5 | SYN | C | `FINAL_REFIT_TRAINING` of r6 under abandoned L3, then L4 evaluates r6 → `POST_HOC`. A development join of r7 under another protocol, then a final evaluation → `POST_HOC` |
| FX-RPL-13 | R-5 | SYN | C | Non-protocol `resolution_run_ref` → refused. The same run declared as a correction → `RESOLUTION_REEVALUATION` |
| FX-RPL-14 | R-6 | SYN | C | Development join including a final race, pre-lock → refused. Post-lock `FINAL_REFIT` → accepted, with `FINAL_REFIT_TRAINING` openings written before the read |
| FX-RPL-15 | R-7 | SYN | U | One row per category, with these inputs. A0: observation without a decision. A1: attempt `INDETERMINATE_CHECKPOINT`. A2: `INELIGIBLE`. A3: `INDETERMINATE` decision. A4: `PredictionFailureRecord`. A5: no selected resolution. A6: `NOT_REALIZED`. A7: `MAPPING_CONFLICT`. A8: `MAPPING_UNAVAILABLE`. A9: `REALIZED_REGION`. A10: `REALIZED_REGION_SET`. A11: `REALIZED_NO_EVENT` → each lands in exactly its category |
| FX-RPL-15a | R-7 (order) | SYN | U | A record with a lineage mismatch (A0) **and** a `NOT_REALIZED` outcome → A0. A record with A4 **and** an available resolution → A4 |
| FX-RPL-15b | R-7 (development) | SYN | U | Development accounting: an observation with no legitimate `N_T` → `GRID_UNAVAILABLE` (replaces A4). Development rows carry no snapshot column. The other categories are as in backtest |
| FX-RPL-16 | R-7 | SYN | U | Key-less `SESSION` `INDETERMINATE_IDENTITY` and `DRIVER_ENTRY` alias failure → A1 rows, in manifest order |
| FX-RPL-17 | R-7 | SYN | U | Snapshot `target_episode_initialization_ref` ≠ the selected resolution's → A0 |
| FX-RPL-17a | R-7 | SYN | U | The resolution run's `target_initialization_run_ref` ≠ the replay's → A0 for every predicted record of that run |
| FX-RPL-18 | R-7 | SYN | U | `ESTABLISHED` SESSION and DRIVER_ENTRY rows → no category; not candidates |
| FX-RPL-19 | R-8 | SYN | C | Perturb the realized regions and prediction values of A9 units → cohort set unchanged |
| FX-RPL-20 | R-8 | SYN | C | One A8 (or A5, A7, A0) row in scope → `DEFECTIVE`; `PRIMARY` refused |
| FX-RPL-21 | R-9 | SYN | C | FX-TGT-23 units → both retained; same `eventual_event_key`; distinct `target_episode_key` |
| FX-RPL-22 | R-10 | SYN | C | Let τ be the declared deterministic tolerance (#20). Distributions differing by τ/2 → `REPRODUCTION`. By 2τ → not a reproduction. One differing category → not a reproduction. Either way a new run id |
| FX-RPL-23 | R-11 | SYN | C | Scorer with `supported_kinds = {A9, A10}` → `SECONDARY`. Subset "units with an observed event" → `RETROSPECTIVE_DIAGNOSTIC` |
| FX-RPL-24 | R-12 | SYN | C | Partition {r1, r2}, replays cover r1 only → `DEFECTIVE` |
| FX-RPL-25 | Gate O3 | SYN | C | **PENDING-OWNER.** In a development join, the episode's resolution comes from a different initialization run than the observation's initialization. #21's development join states no lineage rule. Routed to #21 as an optional addition (R-D). Until then, this fixture asserts only that the mismatch is detectable (logged) |
| FX-RPL-26 | Gate O3 | SYN | C | Replay whose `observation_reconstruction_run_ref` differs from the initialization run's observation run → current #21 behaviour: no decision is found for the replay's observations (replay step 2), so an upstream-linkage defect is recorded, then A0 rows, then the backtest is `DEFECTIVE` |

## Verification parameters (#35)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-SUP-01 | #35 (A) | REAL | C | Inputs: `headscan_v1.json` plus F-A5 evidence (`clock_fixture_races_v1.json`, `probe_races_v2.json`) → 55 S-RD; 110 `UNVERIFIED_ARCHIVE`; Bahrain 2018 (2018, 2) and Hungary 2018 (2018, 12) `UNSUPPORTED`; 22 races of 2022 `UNSUPPORTED`. The 7 races of 2026 R17–R23 (HTTP 403, not yet published) are **not classified** and stay outside scope until probed |
| FX-SUP-02 | #35 (A) | SYN | U | `Last-Modified` = race date + 2 days → `UNVERIFIED_ARCHIVE`. + 1 day → S-RD |
| FX-SUP-03 | #35 (A) | REAL+TAMPER((2024,10)) | C | Recorded hash altered by one hex digit, then `--verify` → difference reported; the race is removed from S-RD until re-validated |
| FX-SUP-04 | #35 (A) | SYN | C | `TrackStatus` facts in S-RD → omitted with reason `ARCHIVE_AVAILABILITY_UNVERIFIED`. The observation is `VALID_WITH_OMISSIONS` |
| FX-SUP-05 | #35 bounds | SYN | U | Cross-stream fact @989.9, trigger @1000 → admitted. @990.0 → omitted |
| FX-SUP-06 | #35 bounds | SYN | U | Same-stream record @999.9, before the trigger in stream order → admitted. Field inside the trigger record → admitted. Same-stream record after the trigger in stream order (equal prefix) → omitted |
| FX-SUP-07 | #35 health (a) | SYN | U | Driver 1 lap 46 spans [8530, 8622] with `LastLapTime` 90.0 s → r = +2.0. Driver 10 lap 46 spans [8540, 8640] with `LastLapTime` 98.2 s → r = +1.8 → common-mode anomaly. The illustrative extent [8530, 8640] is the union of the flagged laps; #35 does not define the extent, so it is not asserted. A trigger @8600 (inside both flagged laps) → `INDETERMINATE_CHECKPOINT` (`COARSE_TIME_AMBIGUITY`); facts inside are omitted. Driver 63 alone with r = +30, then −30 on the next lap → no window |
| FX-SUP-08 | #35 health (b) | SYN | U | In-race interval [6000, 6300] with no lap-fixture check. (i) No RCM anchor in [5940, 6360] → unhealthy. (iii) The only anchor @6150 has deviation +0.9 (outside [−1.2, +0.7]) → unhealthy. **(ii) PENDING-OWNER:** a single in-band anchor @6150. Whether one anchor heals the whole interval, or each point needs an anchor within ±60 s, is unresolved. Routed (R-F) |
| FX-SUP-09 | #35 pre-race | SYN | U | `Started` @3400. Pre-race fact @3094.9 → admitted. @3095.0 → omitted |
| FX-SUP-10 | #35 health (c) | SYN | U | A record after the last `Finished` → unhealthy; never a fact for in-race checkpoints |
| FX-SUP-11 | #35 (D) | SYN | U | `TotalLaps` [(5, 58), (47, 0), (453, 58)] → 58. [(9.9, 0), (13.6, 44)] → 44. [(5, 0)] → `SCHEDULED_DISTANCE_UNAVAILABLE` |
| FX-SUP-12 | #35 (C) | REAL(all 55 S-RD keys) | C | The `c(E)` method → 1998/1998 Jolpica in-lap matches |
| FX-SUP-13 | #35 (C) | SYN | U | All cars `Stopped:true` @5000, then advancing laps after 5600 → no terminal assigned |
| FX-SUP-14 | #35 provenance | SYN | C | A positive-rule `CONFIRMED_TYRE_SERVICE` carries a reference to the support record noting limited independent validation |

## Evaluation protocol (#37)

| ID | Source | Basis | Level | Given → Expected |
| --- | --- | --- | --- | --- |
| FX-EVL-01 | §1 | SYN | U | p_j = 0.25 → S = −ln 0.25. Set {1, 2} with p₁ = 0.5, p₂ = 0.25 → S = −ln 0.75. q = 0.0625 → S = −ln 0.0625 |
| FX-EVL-02 | §1 | SYN | U | Realized probability 0 → unit S = +∞; aggregate +∞; claim failed; accounting unchanged |
| FX-EVL-03 | §1 | SYN | U | K_T = 3, p = [1, 0, 0], q = 0 → p' = [1 − 3e-6, 1e-6, 1e-6], q' = 1e-6. Hazards λ_j = p'_j / S_j round-trip through `hazard/v1` to p' (1e-12) |
| FX-EVL-04 | §1 | SYN | C | A development snapshot with minimum probability 5e-7 → lock refused |
| FX-EVL-05 | §2 | SYN | U | Paired units (S_locked, S_ref) = (1.0, 1.2), (0.5, 0.4) → ΔS = −0.05 |
| FX-EVL-06 | §3 | SYN | U | Paired differences by race: g1 [0.1, 0.3]; g2 [−0.2, 0.0, 0.2]; g3 [0.4]; g4 [−0.1, 0.1] (n = 8, G = 4) → ΔS = 0.1. CR2 variance = (1/64)·Σ_g (Σ residuals_g)² / (1 − n_g/8) = 0.0055238095238095. SE = 0.0743223352957207. 95 % interval with t(3, 0.975) = 3.182446305284263 → [−0.1365268413619644, 0.3365268413619644]. G < 10 → flagged **descriptive only** |
| FX-EVL-07 | §3 | SYN | U | Wild cluster bootstrap (unrestricted, Webb six-point weights, B = 9,999, **percentile** interval): (i) if every unit difference equals 0.2, the interval is [0.2, 0.2] exactly; (ii) the same seed gives an identical interval |
| FX-EVL-08 | §4 | SYN | C | B1 at T falls back to B0 when the compound is omitted, when the latest admissible stint update has `TyresNotChanged:"1"`, or when there has been no admissible stint update since the last entry |
| FX-EVL-09 | §6 | SYN | U | A (rank 2, mean 1.000); C (rank 1, mean 1.020), with ΔS(C vs A) = 0.020: SE 0.030 → choose C. SE 0.010 → choose A |
| FX-EVL-10 | §6 | SYN | U | The chosen candidate's ΔS against B1 ≥ 0 → lock B1; primary comparison is B1 against B0 |
| FX-EVL-11 | §6 | SYN | C | An 11th candidate → refused. B0 and B1 are not counted |
| FX-EVL-12 | §7 | SYN | C | F2 inclusion check with an instrumented reader → no record content parsed. HTTP 200, race-day `Last-Modified`, and identical hashes 24 h apart → admitted. Hashes differ → excluded |
| FX-EVL-13 | §8 | SYN | U | A6 = 600 and A9 + A10 + A11 = 500 → share 600/1100 > 0.5 → `SECONDARY`; ledger role unchanged. A6 = 500 and A9 + A10 + A11 = 500 → share 0.5 → `PRIMARY` allowed (≤ 50 %) |
| FX-EVL-14 | §8.5 | SYN | U | A6 unit, indeterminate visit at v = 3, p = [0.1, 0.2, 0.1, 0.3, …] → S_a = −ln 0.3, S_b = −ln(1 − 0.4). With no visit lap context → "not computable" |

## Cross-component reference scenarios (end to end)

All scenarios are `SYN` (except E2E-09) and use the defaults.

- **Stub model (most scenarios):** emits the uniform distribution p_j = q = 1/(K_T + 1).
- **Stub model (FX-E2E-10):** a deterministic stub that depends on its input. It sets p_0 = 0.05 + 0.9·(1 − e^(−a/20)) for stint age a in the input view, then spreads the remaining mass uniformly over the other K_T − 1 regions and q. A difference in stint age therefore changes the distribution. Other input differences are caught by the input-view comparison.

| ID | Scenario | Expected end state |
| --- | --- | --- |
| FX-E2E-01 | **Observed event.** Driver 16: lap advances 20 @5000, 21 @5090, 22 @5180; entry @5200 (c = 22), confirmed service; finish B = 9050. Observation L20 (T = 5000, N_T = 57, so K_T = 37) | Snapshot; `OBSERVED_EVENT`; `REALIZED_REGION {2}`; A9; S = ln 38 |
| FX-E2E-02 | **Terminal no-event.** Driver 16, L50 at T = 8200 (K_T = 7); no visits; finish B = 9050; complete coverage | `TERMINAL_NO_EVENT`; `REALIZED_NO_EVENT`; A11; S = ln 8 |
| FX-E2E-03 | **Truncated.** As E2E-01, but the entry @5200 has last update `TyresNotChanged:"1"` and no penalty | `TRUNCATED_INDETERMINATE`; `NOT_REALIZED`; A6; not scored |
| FX-E2E-04 | **Ineligible (split slice, #41).** Driver 31's lap-30 advance record @6000 carries `Retired:true` **in the same payload**. The record lies in a healthy window and before `Finished`. Same-payload fields are available at T by construction (#35). The retirement establishes terminal participation under the #35 (C) membership rule (`Retired:true`). This satisfies the #19 eligibility clause "participation is already terminal" at T. **Only the L30 row is asserted.** Driver 31's earlier episodes (e.g. L29) get an empty terminal bound (6000, 6000]; that is routed as R-K | `INELIGIBLE`; no request and no snapshot; A2. *Note:* post-finish checkpoints are always clock-unhealthy (#35 rule (c)) and become A1. So "no future race progression" ineligibility cannot be reached **by the post-finish route** in S-RD (R-H). Whether L ≥ N_T at a trigger that is not after `Finished` establishes that condition is open (R-J) |
| FX-E2E-05 | **Defective.** As E2E-01, but driver 16's count jumps 21 → 23 before the entry | `MAPPING_UNAVAILABLE`; A8; run `DEFECTIVE`; no `PRIMARY` |
| FX-E2E-06 | **Leakage: future facts.** Rival pit entry @5003 (same stream, after the L20 trigger record) and RCM message @4993 (cross-stream, inside 10 s) | Neither appears in the L20 observation, input view or snapshot |
| FX-E2E-07 | **Successive checkpoints.** E2E-01 plus observation L21 (T = 5090) | Two units: `{2}` on L20's grid and `{1}` on L21's grid; same `eventual_event_key`; distinct episodes |
| FX-E2E-08 | **Clock anomaly.** Common-mode window [6000, 6200]; lap trigger @6100 | `INDETERMINATE_CHECKPOINT`; A1; no snapshot |
| FX-E2E-09 | **Real smoke test.** REAL((2024,10), S-RD), full chain | Every A9 `c(E)` agrees with Jolpica; category counts reproducible across two runs; no `MAPPING_CONFLICT` |
| FX-E2E-10 | **Counterfactual futures (cross-state leakage), split slice, #41.** Driver 16 has one identical record history up to and including its L20 trigger @5000: the same records, prefixes, within-stream ordinals and payload bytes. Five different futures follow. (a) A confirmed-service entry @5200 with c = 22 (observed event). (b) No visits until driver 16's finish terminal B = 9050 (terminal no-event). (c) The @5200 visit's last stint update has `TyresNotChanged:"1"` and there is no penalty (truncated). (d) No visits; driver 16's last advance is @5270 and it shows `Retired:true` @5300, giving retirement terminal B ∈ (5270, 5300] with complete coverage over (T, B). (e) Driver 16's count goes 21 @5090 → 23 @5180, with confirmed service @5200 (defective) | **Comparison projection Π (independent of the snapshot).** For every fact: kind, subject keys (session, driver entry), value, availability class and bounds, stream, prefix, within-stream ordinal, payload SHA-256. Π excludes `source_snapshot_id`, artifact ids, run refs and provenance. **Equal across all five:** Π(the L20 observation's `canonical_state`); the `prediction_boundary` (the validation-scoped `authority_validation_ref` is identical); the observation quality; the eligibility status, reason codes and Π(causal input facts); the initialization's target-definition and policy fields; and the input view's values, omissions and Π(`derivation_input_fact_refs`). Hence the stub's emitted distribution is identical. **`request_digest` and `content_digest` equality: PENDING-OWNER (R-I).** Both digests cover the fact refs, and whether those refs depend on the snapshot is not fixed. Until R-I is accepted, the fixture asserts equality of digests computed over the Π-projected request. **Excluded, because they legitimately differ:** artifact ids, `observation_artifact_ref`, `target_episode_key`, and other snapshot-scoped identifiers and provenance (#18). **Accounting:** (a) A9, region 2; (b) A11; (c) A6; (d) A11 (`TERMINAL_NO_EVENT` at retirement); (e) A8. Only resolution, mapping and accounting differ. Ineligibility is decided causally at T, so it cannot be a future; in (d), driver 16 has no checkpoints after the retirement. *Note (b):* (T, B) contains the post-`Finished` unhealthy window. `TERMINAL_NO_EVENT` still holds, because entries after `Finished` are outside participation (#35 (C)) and cannot hide a relevant event |

## Deferred items

| Item | Reason |
| --- | --- |
| #19 T-6 (`PitInTime` comparison) | Not used canonically (#35); optional diagnostic only |
| #19 T-4 reset/correction transitions | No source reset or correction semantics are validated for `InPit` (#35). Add fixtures when an endpoint behaviour is validated |
| #19 T-9 repair-only visits | No independent truth is available to establish a repair-only visit (#35 F-B2) |
| Real red-flag countback session | Not in the inspected samples. FX-TGT-28 and FX-PRD-12 are synthetic |
| Unorderable same-driver candidates (T-16) | Not constructible within one stream in S-RD (RA-3). See FX-TGT-17 |

## Routing (open clarifications; PENDING-OWNER entries)

| Ref | Question | Owner | Assumption used here | Status | Affected fixtures |
| --- | --- | --- | --- | --- | --- |
| R-A | A `TotalLaps` revision published within 300 s before the start is never admissible in-race, so `N_T` stays stale for the whole race. Keep this, or define a later admission route? Any relaxation must be checked against the conditions of the PO evidence exception (`DECISION_BOUNDARIES`) | #35 | Current #35 rule applies (no in-race admission) | Open | FX-OBS-18 (expects the current rule) |
| R-B | The source-lineage equivalence criterion for duplicate `InPit:true` records | #35 / #19 | None; fixture part (a) not asserted | Open | FX-TGT-05(a) |
| R-C | Precedence when a served-penalty visit has last update `TyresNotChanged:"0"` (none observed, 0/10) | #35 / #19 | Non-conflicting data only | Open | FX-TGT-10 note |
| R-D | Optional initialization-lineage check in the development join (gate O3) | #21 | Mismatch only logged | Open | FX-RPL-25 |
| R-E | R-5 wording: the "reseeded rerun under the same lock" case is unreachable | #21 | #21 refuses seed mismatch at replay | Open (wording) | FX-RPL-07 note |
| R-F | How health-window rule (b) is quantified (one anchor per interval, or per point within ±60 s) | #35 | Only unambiguous cases (i), (iii) asserted | Open | FX-SUP-08(ii) |
| R-G | Lap context for indeterminate visits (#37 §8.5) | #19 | Diagnostic "not computable" until provided | Open | FX-EVL-14 |
| R-H | Post-finish "no future race progression" ineligibility cannot be reached in S-RD **by the post-finish route** (post-finish checkpoints are unhealthy) | #19 / #35 | Information only | Informational | FX-E2E-04 note |
| R-I | Fact references that enter `input_view` (`derivation_input_fact_refs`) must not depend on the snapshot (projected keys only), so that `request_digest` and `content_digest` are invariant to the source snapshot when the content is identical | #20 / implementation | Digest equality is asserted over the Π-projected request only | Open | FX-E2E-10 |
| R-J | Does L ≥ N_T at a trigger that is not after `Finished` establish "no future race progression" (`INELIGIBLE`)? | #19 | Not asserted | Open | FX-E2E-04 note |
| R-K | When a lap advance and `Retired:true` share one record, the terminal bound (last advance, retirement] is empty for earlier episodes. How should B be bounded? | #35 | Only the L30 row of FX-E2E-04 is asserted | Open | FX-E2E-04 |

## Acceptance mapping (Issue #36)

- **Every handoff item mapped or explicitly deferred:** see the traceability index, *Deferred items*, and the PENDING-OWNER entries, which are routed.
- **Unambiguous, traceable expected results:** expected values are exact expressions, and every open interpretation is routed rather than decided.
- **End-to-end leakage and state distinctness:** FX-E2E-01…10. FX-E2E-10 proves the prediction side is identical across the five outcome states.
- **Independent review:** full review FAIL; rework complete; bounded re-review pending.

## Review record

### Full scoped review: FAIL, rework required

- PR: #40.
- Reviewer: an independent review agent, recorded on PR #40 as a `COMMENT` review through the connected account.
- Date: 2026-10-11. Reviewed head: `be241da`.
- Findings: 2 Blocking (FX-OBS-18 pre-race rule; FX-RPL-25/26 invented #21 behaviour), 12 Major, 9 Minor.
- Product Owner decision: none required.

### Rework

1. FX-OBS-18 now follows the #35 pre-race rule exactly (58 for every in-race observation), and the stale-distance question is routed as R-A.
2. FX-RPL-26 now expects current #21 behaviour (upstream-linkage defect → A0 → `DEFECTIVE`). FX-RPL-25 is PENDING-OWNER and routed as R-D.
3. FX-TGT-10 now has non-conflicting stint data and its "SERVED" message moved before `Finished`. The precedence question is routed as R-C.
4. Finish terminals are corrected (B = 9050, after `Finished`), and FX-TGT-20a adds the finish derivation, including the lapped-driver case.
5. FX-TGT-17 now uses same-stream order (RA-3). The unorderable sub-case is deferred as not constructible.
6. FX-TGT-05(a) is PENDING-OWNER (R-B). FX-TGT-05a adds the malformed case; reset/correction is deferred with its reason.
7. FX-PRD-05 now separates the direct-validator path (V1, V2, V3, V5) from the procedure path (V4, V6, V7, and R codes).
8. FX-OBS-20 and FX-OBS-21 add the fail-closed checks for S-RG and S-22.
9. FX-OBS-08 now has exact gap inputs and statuses. FX-OBS-09a adds gap recovery under #18's "unknown until reset" rule.
10. FX-E2E-10 adds the counterfactual-futures cross-state leakage scenario.
11. FX-E2E-04 is rebuilt on a post-finish checkpoint, with the #19 eligibility clause cited.
12. FX-RPL-15 now has concrete inputs per category. FX-RPL-15a adds the ordering cases, FX-RPL-15b the development categories, and FX-RPL-17a the second lineage condition.
13. Partial mappings are completed or deferred:
    - FX-TGT-03a (first-lap edge);
    - FX-TGT-10a (stop-and-go), with repair-only deferred;
    - FX-TGT-14a and FX-TGT-15a (exact-equality cases);
    - FX-TGT-29a (bounded formula);
    - FX-RPL-07 note (unreachable reseed case);
    - FX-OBS-23 (not-applicable checks for O-15).
14. FX-EVL-06 now has an exact CR2 dataset with SE and interval. FX-EVL-07 now has exact degenerate and reproducibility properties.
15. Minor findings:
    - FX-OBS-10 now applies the same-stream rule.
    - FX-SUP-08(ii) is routed as R-F.
    - FX-SUP-07 now gives concrete laps.
    - FX-SUP-01 now names its input sources and treats 2026 R17–R23 as unclassified.
    - Expected values use exact expressions.
    - Synthetic generator conventions are stated.
    - Underspecified inputs are filled: B values, the disqualification representation, lap records, the stub model, differing bounds, the τ cases, the 50 % boundary, and SUP-04's reason code.
    - Real sessions are cited by `RaceSessionKey`, and the REAL+TAMPER label is added.
    - The traceability labels are corrected.
    - The "no contradiction" statement is replaced by routing entries.
    - FX-OBS-22 adds a delayed-publication fixture.

### Bounded re-review: FAIL on the split section only

- PR: #40. Reviewer: the same independent review agent; recorded on PR #40 as a `COMMENT` review. Date: 2026-10-11. Reviewed head: `d2b15d5`.
- All 23 prior findings are resolved or acceptably routed, and the PENDING-OWNER routing is accepted under SPEC_PROCESS. The recomputed values are correct.
- Two Major regressions remain:
  - N1: FX-E2E-04 contradicted #35 health rule (c).
  - N2: FX-E2E-10 asserted identity for identifiers scoped to the snapshot.
- Seven Minor findings (N3–N9) were also raised.
- **Non-convergence handling:**
  - No third review cycle on this slice.
  - N1 and N2 were split into Issue #41, a new sub-slice with its own independent review.
  - N3–N9 were applied as Minor fixes.
  - All other entries stand as passed.

### Split sub-slice (#41) review

#### Full scoped review: FAIL, rework required

- PR: #40 (#41 sub-slice). Reviewer: a fresh independent review agent; recorded on PR #40 as a `COMMENT` review. Date: 2026-10-11. Reviewed head: `79b7df6`.
- Confirmed correct:
  - FX-E2E-04 can be built and gives `INELIGIBLE`/A2.
  - The accounting for futures (a)–(e) is right.
  - The identifier exclusions are right.
- Findings:
  1. Major: FX-E2E-10 still pulled in snapshot-scoped lineage indirectly, through facts, fact refs and digests.
  2. Minor: the R-H claim was overbroad.
  3. Minor: future (e) was inexact.
  4. Minor: one sentence was misleading.
- Observations O1–O4 were also raised.

#### Rework

1. FX-E2E-10 now uses an explicit snapshot-independent projection Π for every compared item. Digest equality is PENDING-OWNER (R-I, owner #20/implementation) and is asserted over the Π-projected request until R-I is accepted.
2. R-H is restricted to the post-finish route. A new R-J routes the L ≥ N_T question to #19 as Open.
3. Future (e) is now exact: driver 16, 21 @5090 → 23 @5180.
4. The misleading sentence is reworded.
5. O1: only the L30 row is asserted; the empty bound is routed as R-K.
6. O2: the #35 (C) membership rule is cited.
7. O3: FX-E2E-10 uses a deterministic stub model that depends on its input.
8. O4: a note on the post-`Finished` window is added.

#### Bounded re-review: PASS

- PR: #40 (#41 sub-slice). Reviewer: the same fresh independent review agent; recorded on PR #40 as a `COMMENT` review. Date: 2026-10-11. Reviewed head: `233fd83709c187a5ff1055563945801c5b9ce8d9`.
- Outcome: **PASS**. Prior findings 1–4 and observations O1–O4 are resolved, and the Issue #41 acceptance criteria are met.
- A follow-up commit fixed the Minor R1 (stub-sensitivity wording) and the observation (no checkpoints after the retirement).
- Product Owner decision: none required.
