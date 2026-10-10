# V2 Source Availability and Target-Reconstruction Support Matrix

## Status

Draft. Reworked after the full scoped review on PR #38 and under the Product Owner decision `decisions/2026-10-10-v2-race-day-archive-evidence-exception.md`. A bounded re-review is required before approval.

## Abstraction level

This is a verification evidence artifact. It establishes which historical scopes satisfy each of the following:

- The availability-authority requirements of `design/OBSERVATION_RECONSTRUCTION.md` (#18), as modified **only** by the documented evidence-standard exception.
- The target-reconstruction capabilities of `design/TARGET_RECONSTRUCTION.md` (#19, including Amendment A1).
- The scheduled-race-distance rule (#18 Amendment A1).

It sets verification parameters within those rules. It does not change the rules.

## Issue / branch / decision

- Issue: #35. Parent issue: #34.
- Branch: `ccr-d8f3e250-t7uix3`. PR: #38.
- Product Owner decision: `decisions/2026-10-10-v2-race-day-archive-evidence-exception.md`.
  - **Option B was approved.** Race-day-written archives may be classified `VERIFIED_BOUNDED_TIME` on reproducible internal-consistency evidence.
  - The conditions are: residual assumptions stated explicitly, conservative bounds derived from a validated error model, clock-unhealthy windows excluded, and independent review.

## Evidence and reproduction

All evidence lives in `verification/evidence/`, retrieved on 2026-10-10. Tools are in `verification/tools/`. They are verification tooling, not production code. Each tool runs as `python -I <tool> …`, and every output JSON records the exact command line (`argv`).

| File | Produced by | Content |
| --- | --- | --- |
| `headscan_v1.json` | `lt_headscan.py --cache C --out … 2018 … 2026` | HTTP status, `Last-Modified`, `ETag` and race-day flag for the `TimingData` file of **every** Jolpica-calendar race 2018–2026 (199 rows) |
| `probe_raceday_scope_v1.json` / `_v2.json` | `lt_probe.py` (v2 = `--verify` re-fetch of v1) | Race-day-written census (55 races): per-stream SHA-256, bytes, `Last-Modified`, `ETag`; session status; `TotalLaps` series |
| `probe_races_v1.json` / `_v2.json` | as above | Era sample: first, middle and last race of each season 2018–2026, plus two 2022 races (26 sessions) |
| `clock_fixture_raceday_scope_v1.json`, `clock_fixture_races_v1.json` | `lt_clock_fixture.py` | Lap-time clock fixture, common-mode anomaly windows, RCM anchor, Heartbeat comparison, entry→stint lag |
| `capabilities_raceday_scope_v2.json`, `capabilities_races_v2.json` | `lt_capabilities.py` | Pit entries, lap at entry versus Jolpica, exits, lap progression, tyre-service classes, penalty test set, terminal rules |

- **Reproducibility.** The v2 probes re-fetched all 81 sessions (8 streams each) about 4.5 hours after v1. They report **0 SHA-256 or `Last-Modified` differences** (`verify_differences: []`).
- **Jolpica.** Jolpica responses are frozen under the cache's `jolpica/` directory, and their SHA-256 is recorded per race in the capability evidence.
- **Downstream tools.** These read only the cached bytes whose hashes the probe recorded.
- **Raw caches** (about 0.5 GB) are not committed. Re-running `lt_probe.py --verify <v2>` re-downloads them and checks them against the recorded hashes.

The **independent public record** used for comparison is the Jolpica (Ergast-compatible) API. It is a secondary compilation, not ground truth. In particular, its pit-stop list includes drive-throughs; for example, Monaco 2025 #63 lap 53 appears as a 19.5 s "stop". Jolpica is **not** used in any target-reconstruction rule below. It serves only as comparison evidence.

## Key findings

### F-A1. Archive files written on race day versus rewritten in bulk (complete census)

Source: `headscan_v1.json`, all 199 calendar races 2018–2026.

| Seasons / rounds | `TimingData` status | `Last-Modified` | Count |
| --- | --- | --- | --- |
| 2018–2021, 2023, 2024 R1–R9 | 200 | 14–20 June 2024 (bulk rewrite) | 112 |
| 2022 (all) | 403 | — | 22 |
| 2024 R10 – 2026 R16 | 200 | race date or next UTC day | 55 |
| 2026 R17–R23 | 403 | not yet held / published | 7 |

There are no exceptions in either direction: no race-day-written file before 2024 R10, and no rewritten file from 2024 R10 onward.

### F-A2. The archive prefix clock is validated directly for `TimingData` and `RaceControlMessages`

Here the "prefix" means the `HH:MM:SS.mmm` timestamp in front of each archive record.

- **Lap-time fixture (`TimingData`; dense; relative clock).**
  - For each driver lap, the residual is r = (prefix of the lap-L advance − prefix of the lap-(L−1) advance) − official `LastLapTime(L)`. The official lap time comes from the trackside timing loops, independently of the recorder.
  - Across the race-day census there are **59,641** checks. **98.46 %** have |r| ≤ 0.25 s, **99.69 %** ≤ 0.5 s, **99.90 %** ≤ 1 s and **99.955 %** ≤ 2 s.
  - The median gap between consecutive checks is ≤ 3.3 s in every race.
  - The prefix clock therefore advances faithfully with real elapsed time.
- **RaceControlMessages anchor (absolute clock).**
  - The payload `Utc` is server time in whole seconds.
  - Within each race, the deviation of `Utc − prefix` from its per-race median lies in **[−1.12 s, +0.68 s]** across all 55 race-day races. This range includes the ≤ 1 s truncation.
- **Heartbeat is not a valid reference.**
  - In Las Vegas 2024 and Australia 2025, Heartbeat `Utc − prefix` drifts by up to +21.7 s and +34.9 s.
  - Over the same windows, the lap fixture stays within ±0.25 s and RCM stays within its band.
  - The Heartbeat source clock drifts, not the prefix clock. Heartbeat is excluded from the error model.

### F-A3. Clock anomalies are rare, short and detectable

- **Common-mode anomalies.** These are lap-fixture residuals with |r| > 1 s for two or more drivers in overlapping laps. Only **3 of 55** race-day races contain one, each 3–4 minutes long:

  | Race | Window | Drivers affected | Max |r| |
  | --- | --- | --- | --- |
  | British 2025 | [8623.7 s, 8820.3 s] | 6 | 11.8 s |
  | Dutch 2025 | [8902.5 s, 9096.4 s] | 7 | 2.0 s |
  | Monaco 2026 | [11180 s, 11429 s] | 4 | 1.4 s |

- **Why detection does not depend on check density.** Each driver's lap spans about 75–120 s. A prefix-clock stall or jump of s seconds at any point in the race therefore appears as a residual of about s in the laps of every driver whose lap spans it.
- **Single-driver paired residuals** (+x then −x on the next lap, while other drivers stay ≤ 0.4 s):
  - Bahrain 2025 #63 (−69.9 s);
  - Japan 2026 #30 (±59.8 s, ±28.2 s, ±22.3 s, ±20.5 s);
  - Dutch 2026 #41 (−55.6 s).
  - These are **per-driver delayed publications** of a lap advance, not clock faults. The delayed record's prefix is genuinely when that lap completion became observable, so the checkpoint boundary stays truthful.

### F-A4. Supporting cross-stream evidence for endpoints without their own UTC

- `TimingAppData`'s first stint update after each `TimingData` pit entry never precedes the entry. The lag is at least 1.04 s, the median across races is 5.6 s, and the maximum race q99 is 66 s.
- Race-day streams contain **0 malformed records** out of about 3.3 million (`TimingData` 3,243,640; `TimingAppData` 53,755; `SessionStatus` 283; `LapCount` 3,326; RCM 6,576; `DriverList` 8,627).
- `SessionStatus` holds exactly one `Started` record in 51 races, and two in 4 races (red-flag restarts).

### F-A5. Rewritten-era clocks are worse

Era sample, for information only, since that scope is unverified anyway:

- Lap-fixture outliers reach about 104 s.
- Lap-count jumps or regressions occur in 2018 Bahrain, 2019 Abu Dhabi, 2020 Austria and 2021 Belgium.
- Bahrain 2018 and Hungary 2018 have Heartbeat and RCM values that are inconsistent by thousands to millions of seconds.

### F-B1. Pit entries and lap at entry

Census: 55 races, including Las Vegas 2025.

- **Every Jolpica stop matched.** 1,998 of 1,998 Jolpica stops are matched one-to-one by an in-race archive entry (`TimingData` `InPit` False→True between the first `Started` and the last `Finished`) with `c(E) + 1 ==` the Jolpica lap. `c(E)` is the driver's `NumberOfLaps` at the entry record, in stream order. The era sample gives 899 of 899.
- **Extra entries.** There are 73 extra in-race entries with no Jolpica stop. 13 of them are followed by no further lap, meaning the car entered the pits and retired. The rest are not explained here (no claim is made about their cause).
- **Exits.** Every Jolpica-matched entry has a following exit (1,998).
- **Post-finish movements.** No `InPit` transition was observed after the last `Finished` record.
- **Lap progression.** There are **0** lap-count jumps or regressions in the race-day census.

### F-B2. Tyre-service evidence (`TimingAppData` stints)

- **Stints are provisional at entry.** A pit traversal opens a stint at entry even when no tyres are changed. Example: Monaco 2025 #63 after a drive-through had `TyresNotChanged:"1"`, the old compound and `StartLaps:53`. A later real stop can **overwrite the same stint index**.
- **Classification rule.** Each visit is classified by the **last** stint update in [entry, next entry):

  | Class | Race-day census | Era sample |
  | --- | ---: | ---: |
  | `TyresNotChanged:"0"` (POS) | 1,761 | 790 |
  | … of which also `New:"true"`, `StartLaps:0`, or a compound differing from the previous stint | 1,640 (93 %) | 744 |
  | `TyresNotChanged:"1"` (NEG) | 221 | 111 |
  | no stint update (NONE) | 89 | 47 |

- **Penalty test set (independent negatives).** This set is the first in-race entry of a car after RCM issued a drive-through or stop-and-go penalty for that car, where a matching "PENALTY SERVED" message exists. No tyre work is permitted while serving these penalties. All **10 of 10** such visits (9 race-day, 1 era) are NEG, and **0** are POS.
- **What was not available.** No independent ground truth for tyre changes was available in this environment (for example FIA pit-stop or tyre-usage documents). Jolpica durations proved unreliable as a discriminator: minimum POS durations overlap with drive-through and safety-car traversals, and some values are corrupt (Monaco 2026 #11: 2,026.9 s). Duration is therefore **not** used.

### F-B3. Race participation and terminal evidence

- The `Retired:true` flag alone identifies only 82 of the 158 race-day Jolpica non-finishers (disqualifications excluded).
- **Combined rule:** `Retired:true`, **or** `Stopped:true` observed after the driver's last lap advance and before the last `Finished`.
  - It agrees with Jolpica for **157 of 158**.
  - In 4 further cases the rule flags a retirement that Jolpica classifies as a finish: cars that stopped in the final laps and were still classified. In those cases the physical participation end is the relevant fact.
  - 1 Jolpica non-finisher (Azerbaijan 2026 #77) is not flagged.
- Era sample: 80 of 81. The rule also flags 10 classified finishers at Tuscany 2020, a race with two red flags. Those flags are **not explained** by this analysis. The terminal rule must therefore be exercised on red-flag races; a fixture for this is routed to #36, and red-flag `Stopped` before a restart must not count as terminal.

### F-C1. Scheduled race distance

- In every race-day race, the first **positive** `LapCount.TotalLaps` is published within 75 s of the stream opening. The earliest it precedes the race start is **3,217 s** (53.6 min) before `Started`.
- Genuine revisions are published at their own prefix: São Paulo 2024 71→70→69, Australia 2025 58→57, Austria 2025 71→70, Canada 2026 70→68, Bahrain 2026 56→55.
- Spurious `TotalLaps:0` records occur in several 2026 races. Each was restated by a positive value: Australia 2026 had a zero at 47 s, restated at 453 s; Belgium 2026 had a zero at 9.9 s, with the first positive value at 13.6 s.

## Error model and bounds for scope S-RD

**Residual assumptions** (accepted under the Product Owner exception; carried into provenance):

- **RA-1 (recorder ≈ public).** Public observability of a record differs from the archive recorder's receipt time by at most 3 s. Supporting evidence: the RCM and lap fixtures show the recorder clock tracking server time within about 2 s. This cannot be proven without contemporaneous capture.
- **RA-2 (shared recorder clock).** `SessionStatus`, `LapCount`, `TimingAppData` and `DriverList` share the prefix clock that is validated for `TimingData` and RCM. Supporting evidence: F-A4 ordering consistency.
- **RA-3 (in-order delivery within a stream).** Archive order within one endpoint equals public delivery order. Supporting evidence: monotone prefixes and lap residuals of about 0.25 s.
- **RA-4 (race-day files equal the live sequence).** Race-day files, unmodified since race day, contain the contemporaneously delivered record sequence. Supporting evidence: F-A1, reproduced hashes, and outage behaviour consistent with live recording.

**Derivation.**

1. Clock error of the prefix relative to per-race server time: ≤ 1.2 s, from RCM deviation [−1.12, +0.68] after taking the in-race lap fixture into account.
2. Recorder versus public difference: ≤ 3 s (RA-1).
3. Margin: 0.8 s.

Total: **availability ∈ [P − 5 s, P + 5 s]** for any record with prefix P in a clock-healthy window.

**Clock-healthy windows.** A window is unhealthy if any of the following holds:

- (a) It falls inside a common-mode anomaly window (F-A3).
- (b) It is an in-race interval longer than 120 s with no lap-fixture check **and** no RCM anchor within ±60 s whose deviation is within the per-race band. Red-flag stoppages are typically anchored by dense RCM traffic.
- (c) It lies after the last `Finished`.

**Pre-race records** (before the first `Started`) have no lap fixture. They are admissible for in-race checkpoints only with a **300 s margin**: P_fact + 300 s < P_Started − 5 s. This covers recorder start-up replays.

**Admission rules** (#18 bounded-time rule, made concrete):

- **Cross-stream facts:** admitted only if P_fact + 5 s < P_trigger − 5 s, i.e. a **10 s** separation.
- **Same-stream facts** (for example rival updates in `TimingData` before a lap trigger): admitted if they precede the trigger record in stream order (RA-3, "boundary ordering independently proven").
- **Fields carried in the trigger record itself:** available at T by construction (same payload), so admitted.
- **Checkpoints:** a checkpoint whose trigger record lies in an unhealthy window is `INDETERMINATE_CHECKPOINT` (reason `COARSE_TIME_AMBIGUITY`). Facts in unhealthy windows are omitted.

**Consequences for observation content, stated plainly:**

- Cross-stream facts published within 10 s before a checkpoint are omitted. Examples: a race-control message, a tyre-stint update, or a `LapCount` change in that window.
- Checkpoints in about 3–4 minutes of 3 of 55 races are indeterminate.
- Same-stream `TimingData` content, which carries most race state, is **not** affected by the margin.

## Support matrix

### (A) Prediction-time availability authority

| Scope | Endpoints | Authority level | Basis |
| --- | --- | --- | --- |
| **S-RD:** race sessions whose `TimingData` `Last-Modified` is on the race date or the next UTC day (2024 R10–R24, 2025 R1–R24, 2026 R1–R16 at 2026-10-10; later races when they pass the same check) | `TimingData`, `RaceControlMessages` (directly validated); `SessionStatus`, `LapCount`, `TimingAppData`, `DriverList` (RA-2) | **`VERIFIED_BOUNDED_TIME`** under the PO exception, with the bounds and rules above | F-A1–F-A4; RA-1–RA-4 |
| S-RD, other endpoints (e.g. `TrackStatus`, `WeatherData`, `ExtrapolatedClock`, `CarData`, `Position`) | — | **`UNVERIFIED_ARCHIVE`** (not probed) | Omitted as optional domains under #18 |
| **S-RG:** files rewritten in June 2024 (2018–2021, 2023, 2024 R1–R9) | all | **`UNVERIFIED_ARCHIVE`**. Bahrain 2018 and Hungary 2018: **`UNSUPPORTED`** | Revision fidelity unproven (F-A1); the exception explicitly excludes rewritten files; F-A5 |
| **S-22:** 2022 | all | **`UNSUPPORTED`** | HTTP 403 |

### (B) #18 verification items

| # | Item | S-RD verdict | Evidence / note |
| --- | --- | --- | --- |
| 1 | Prefix meaning (publication versus effective time) | Receipt clock, validated within bounds under RA-1 | F-A2, F-A3 |
| 2 | Archive revision behaviour | Race-day files, unmodified; hashes reproduced (RA-4) | F-A1; v2 `--verify` |
| 3 | Downgrade when unproven | Applied: S-RG and unprobed endpoints are `UNVERIFIED`; 2022 is `UNSUPPORTED` | (A) |
| 4 | `SessionStatus` start transitions | Present in 55/55 races; restarts in 4 | F-A4 |
| 5 | Lap-count progression, duplicates, jumps, corrections | 0 jumps and 0 regressions | F-B1 |
| 6 | Byte preservation / no implicit promotion | SHA-256 recorded and reproduced | Evidence table |
| 7 | Common clock and cross-stream ties | 10 s cross-stream rule; same-stream ordering under RA-3 | Error model |
| 8 | Gaps and corrupt records | 0 malformed out of about 3.3M; uncovered windows are unhealthy | F-A4, rule (b) |
| 9 | Processed FastF1 versus raw | Not used: raw streams only | — |
| 10 | Delayed/corrected facts keep earlier observations unchanged | Per-driver delayed advances keep their late prefix (F-A3). Behavioural fixtures are routed to #36 | — |
| 11 | Partial-lap and race-wide alignment | Routed to #36 / implementation; no source constraint found | — |
| 12 | Determinism | Hashes reproduced; deterministic tools | Evidence table |
| 13 | Coverage reporting | Complete census of all 199 races | `headscan_v1.json` |
| 14 | Attempt-record completeness | Implementation behaviour; routed to #36 | — |
| 15 | Scheduled race distance | `LapCount.TotalLaps` under S-RD authority; `STATIC_PRIOR` **not applicable** for S-RD | (D) |

### (C) #19 target-reconstruction capabilities

Scope: S-RD and S-RG, excluding 2022. Retrospective use is not subject to availability authority.

| Capability / #19 item | Verdict | Rule / evidence |
| --- | --- | --- |
| Pit-entry transitions (item 1) | **SUPPORTED** | `InPit` False→True between the first `Started` and the last `Finished`; 1998/1998 and 899/899 Jolpica stops matched (F-B1) |
| Pre-race/grid and post-finish movements (items 2–3) | **SUPPORTED (rule)** | Entries before `Started` and after the last `Finished` are outside participation; none were observed after `Finished` |
| Duplicates / malformed / resets (item 4) | **SUPPORTED** in S-RD | 0 malformed records, 0 lap jumps or regressions |
| Same-lap multiple visits (item 5) | **Not observed**; routed to a #36 synthetic fixture | — |
| Visit segmentation / exit | **SUPPORTED** | Exit after every matched entry; exit-open retirements allowed |
| Lap-completion occurrence, `EntryLapContext` (items 23–24) | **SUPPORTED (validated method)** | Implements #19's `c(E) = #{k : C_k ≤ E}` by **stream order** of `NumberOfLaps` advances relative to the entry record. Assumptions: no missing completions (0 jumps observed) and same-stream order equal to occurrence order (RA-3). The result is exact, so `c_exact` is populated. Validated by 1998/1998 and 899/899 exact Jolpica in-lap matches. The countback case (item 24) is not present in the samples and is routed to #36 |
| Tyre-service positive (items 7–8) | **SUPPORTED, provisional** (limited independent validation) | **Rule:** the last stint update in [entry, next entry) has `TyresNotChanged:"0"`. Validation: 0/10 penalty visits classified POS; 93 % carry corroborating fields in the same payload; the remaining 7 % are consistent with a used same-compound set (item 8). No independent positive truth was available |
| Tyre-service negative (items 9–10) | **SUPPORTED only for penalty visits** | **Rule:** `CONFIRMED_NO_TYRE_SERVICE` only for the first in-race entry after an issued drive-through or stop-and-go penalty with a matching "PENALTY SERVED" message (10/10 consistent). `TyresNotChanged:"1"` alone is **not** validated as negative proof (item 10) and gives `INDETERMINATE_TYRE_SERVICE` |
| Stint increment or compound equality as qualification (item 11) | **REJECTED** | F-B2: provisional stints open at drive-throughs |
| Sparse tyre evidence (item 12) | **INDETERMINATE** | Visits with no stint update give `INDETERMINATE_TYRE_SERVICE` |
| Pit-entry occurrence representation (items 13, 15) | **SUPPORTED** | The entry record's prefix, under the S-RD bounds [P − 5 s, P + 5 s], on the same clock as T. In S-RG, retrospective ordering relative to T is not needed, because T does not exist there |
| Race-participation terminal (items 14, 17) | **SUPPORTED with rules** | Membership: the combined rule (F-B3: 157/158). Terminal instant B is bounded, (last lap-advance prefix, first qualifying `Retired`/`Stopped` prefix], which is compared conservatively under #19. A finish terminal is the driver's lap completion after the leader's `Finished`. Red-flag `Stopped` before a restart is **not** terminal. A post-race disqualification is not a participation terminal |
| Interval coverage for no-event (items 18–19) | **SUPPORTED where clock-healthy and record-complete** | 0 malformed records. Windows marked unhealthy, or any missing stream, make coverage indeterminate |
| Items 6, 16, 20–22, 25 | Implementation and fixture behaviour, not source-support questions | Routed to #36 (`PitInTime` comparison is not used) |

### (D) Scheduled race distance (`SCHEDULED_RACE_DISTANCE_LAPS`)

| Scope | Source and rule | Verdict |
| --- | --- | --- |
| S-RD | `LapCount.TotalLaps` | **Admissible under S-RD authority** as a pre-race streamed fact, subject to the 300 s pre-race margin. Every race clears the margin with at least 3,217 s to spare. Revisions apply from their own bounded availability. Rules: `TotalLaps ≤ 0` is invalid and ignored. If no positive value is admissible before a trigger, the result is `SCHEDULED_DISTANCE_UNAVAILABLE` (and #20 fails closed). `DISTANCE_REVISION_CHANNEL_UNVERIFIED` does not apply, because the revision channel is inside the scope. `STATIC_PRIOR` is not applicable |
| S-RG, S-22 | none | `SCHEDULED_DISTANCE_UNAVAILABLE` (moot) |

## Consequences for `supported_scope` and V2 feasibility

- **Prediction-capable scope: S-RD only.** That is 55 races at 2026-10-10 (15 in 2024, 24 in 2025, 16 in 2026), rising to about 62 as the remaining 2026 races are published and pass the checks.
- **This rests on the Product Owner evidence exception.** All results built on S-RD must cite the decision and RA-1–RA-4. If a later contemporaneous capture contradicts them, the exception is void for the affected scope.
- **Target-only scope:** S-RD ∪ S-RG, minus Bahrain 2018 and Hungary 2018. It cannot produce V2 observations.
- **Tyre-service indeterminacy is the dominant expected coverage loss.** In the race-day census, about 301 of 2,071 in-race visits (14.5 %) are `INDETERMINATE_TYRE_SERVICE`: 212 NEG visits without a penalty, plus 89 NONE. That is about 5.5 per race. Each one truncates the episodes that precede it for that driver, back to the previous confirmed event or the race start.
  - A sizeable share of episodes may resolve as `TRUNCATED_INDETERMINATE`.
  - The exact rate is measured through the #21 accounting during implementation.
  - The main remedy is an independent tyre-change truth source (see *Upgrade paths*).
- **Clock-unhealthy windows** make checkpoints indeterminate only in 3 of 55 races, each for about 3–4 minutes.
- **Hand-off to #37.** S-RD spans fewer than three full seasons, so `ROLLING_RACE_BLOCK` or `PRESPECIFIED` with `LOW_POWER` applies (#21). A 2026 final partition has no thesis-era exposure. However, 2024–2026 race-day data (pit, stint and penalty statistics in aggregate) was inspected for this verification. #37 must decide whether to declare that as prior exposure.
- **No further Product Owner decision is needed.** The exception covers the authority question, and the scope consequences follow from approved rules.

## Upgrade paths (not performed here)

1. **Contemporaneous capture** of upcoming races, paired with their later archive copies. This would test RA-1 and RA-4 directly and could void or confirm the exception.
2. **Independent tyre-change truth**, such as FIA pit-stop or tyre documents. It would validate `TyresNotChanged` and reduce the indeterminate visits.
3. **Pre-June-2024 independent copies** of S-RG files, to evaluate revision fidelity for that scope.
4. **Periodic `--verify` re-hashing.** If a race's hash or `Last-Modified` changes, that race leaves S-RD until it is re-validated.

## Routing

| Item | Classification | Owner |
| --- | --- | --- |
| Bounds, health windows, admission rules, `TotalLaps ≤ 0`, tyre and terminal rules, order-based `c(E)` | Verification parameters (this artifact) | #35; consumed by #36 fixtures and by the implementation |
| Fixture-level behaviours (#18 items 10, 11, 14; #19 items 5, 6, 16, 20–22, 24, 25) | Cross-slice | #36 |
| Cohort and truncation rates | Later phase | Implementation (#21 accounting) |
| Season allocation, prior-exposure declaration, `LOW_POWER` | Cross-slice | #37 |
| Capture tooling and independent tyre truth | Optional later work | Future verification |

No design defect was found. The findings fit inside the #18/#19 rules, which anticipated unverified archives, provisional stints and unvalidated `TyresNotChanged`.

## Acceptance mapping (Issue #35)

- **Per-scope verdicts with evidence for every #18 authority item and every #19 capability:** tables (A)–(D), with per-item rows.
- **Consequences for `supported_scope` and feasibility:** stated above, including the expected truncation pressure.
- **Reproduction from recorded hashes:** hashes for all streams and Jolpica responses are recorded; the v2 `--verify` run showed 0 differences; commands are recorded in `argv`.
- **Product Owner escalation:** done. Option B was approved and persisted in `decisions/2026-10-10-v2-race-day-archive-evidence-exception.md`.
- **Independent review:** the full review failed; this is the rework; a bounded re-review is pending.

## Review record

### Full scoped review: FAIL, rework required

- PR: #38. Reviewer: an independent review agent; recorded on PR #38 as a `COMMENT` review through the connected account. Date: 2026-10-10. Reviewed head: `d195460`.
- **Blocking findings:**
  - (1) S-RD authority evidence did not meet the #18 standard, and the Heartbeat "stall" model was contradicted.
  - (2) The [P − 4, P + 15] bound was not conservative.
- **Major findings:**
  - (3) Misreported or unevidenced claims.
  - (4) The tyre verdicts were not independently validated.
  - (5) Jolpica data was neither frozen nor hashed.
  - (6) Consequences were understated and the authority-level reasoning was inconsistent.
  - (7) There was no per-item verdict mapping.
- **Minor findings:**
  - (8) The `c(E)` framing needed to state its assumptions.
  - (9) Tool invocation and hash verification were missing.
  - (10) The distance rule had gaps.
- Product Owner decision: escalated. **Option B was approved** (`decisions/2026-10-10-v2-race-day-archive-evidence-exception.md`).

### Rework

1. Authority rests on the PO exception, with explicit residual assumptions RA-1–RA-4.
   - Heartbeat is replaced by two validated references: the dense lap-time fixture for the `TimingData` clock, and the RCM `Utc` absolute anchor.
   - Unprobed endpoints are excluded.
2. The bounds are re-derived from an explicit error model as [P − 5 s, P + 5 s]. They come with health-window rules: common-mode anomalies, uncovered windows with no RCM anchor, and post-finish periods.
   - Admission margins: 10 s cross-stream, a same-stream ordering route, a same-payload rule, and a 300 s pre-race margin.
3. All numbers were recomputed from the regenerated evidence.
   - A complete `Last-Modified` census was added.
   - Unevidenced claims (the LapCount lag, the cause of the extra entries, ExtrapolatedClock) were removed.
   - The `TotalLaps` timings were corrected.
4. The tyre rules were narrowed.
   - Negative evidence now comes only from visit-specific served penalties (10/10).
   - The positive rule is marked provisional, with its validation limits stated.
   - Jolpica durations were dropped.
5. Jolpica responses are frozen and hashed, and Jolpica is no longer used in any rule.
6. Consequences are stated plainly: the effect of the margins on observation content, the share of indeterminate tyre-service visits, and the prior-exposure hand-off. The authority-level reasoning was made consistent.
7. Per-item verdict tables were added for #18 items 1–15 and #19 items 1–25, with fixture items routed to #36.
   - Participation is restricted to the race window.
   - A combined terminal rule (157/158) is defined.
   - Las Vegas 2025 is now included.
8. `c(E)` is framed as a validated method implementing #19's formula, with its assumptions stated; the countback case is routed to #36.
9. The tools work under `python -I`, record `argv`, provide `--verify`, and read only cached bytes whose hashes were recorded.
10. The distance rule now covers the no-positive-value case and marks `STATIC_PRIOR` as not applicable.

### Bounded re-review

Required under `governance/REVIEW_POLICY.md`.
