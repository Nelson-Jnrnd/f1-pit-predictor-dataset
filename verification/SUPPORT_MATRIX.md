# V2 Source Availability and Target-Reconstruction Support Matrix

## Status

Draft. Authored for Issue #35; independent full scoped review is required before approval.

## Abstraction level

Verification evidence. This artifact establishes which historical scopes satisfy:

- the availability-authority requirements of `design/OBSERVATION_RECONSTRUCTION.md` (#18);
- the target-reconstruction capabilities of `design/TARGET_RECONSTRUCTION.md` (#19, including Amendment A1);
- the scheduled-race-distance source rule (#18 Amendment A1).

It applies the rules of those designs. It does not change them; anything that looks like a design defect is routed to the design's owner below.

## Issue / branch

- Issue: #35. Parent: #34.
- Branch: `ccr-d8f3e250-t7uix3`.
- Evidence:
  - `verification/evidence/*.json`, retrieved 2026-10-10.
  - Each probe file records the HTTP `Last-Modified`, `ETag`, byte count and SHA-256 of every downloaded stream.
- Tools: `verification/tools/` (`lt_probe.py`, `lt_inrace_clock.py`, `lt_capabilities.py`, `lt_tyre_service.py`). These are verification tooling, not production code.
  - Raw stream caches are not committed.
  - Re-running the tools reproduces the evidence. Each file's SHA-256 shows whether the archive bytes have changed since 2026-10-10.

## Samples

| Sample | Sessions | Evidence files |
| --- | --- | --- |
| Era sample | Race sessions 2018–2026: first, middle and last race of each season, plus two 2022 races | `probe_races_v1.json`, `capabilities_v1.json`, `tyre_service_v1.json` |
| Race-day-written census | Every race session listed in the 2024–2026 archive indexes (55 races: 2024 R10–R24, 2025 R1–R24, 2026 R1–R16) | `probe_raceday_scope_v1.json`, `inrace_clock_raceday_v1.json`, `capabilities_raceday_v1.json`, `tyre_service_raceday_v1.json` |

The independent public record is the Jolpica (Ergast-compatible) API, `api.jolpi.ca`: race results/status and pit stops (lap and pit-lane duration). Jolpica is a secondary compilation, not ground truth. Its limits are noted where they matter.

## Key findings

### F-A1. Archive files before mid-2024 were rewritten in bulk; later files were written on race day

- Every race session through 2024 round 9 (9 June 2024) has `Last-Modified` dates between 14 and 20 June 2024, whatever the race date. Examples: Bahrain 2018 → 14 Jun 2024; Bahrain 2023 → 19 Jun 2024.
- From 2024 round 10 (Spanish GP, 23 June 2024) onward, every race's `TimingData` was last modified on race day, roughly 15–60 minutes after the session ended (see the HEAD scan in the probe evidence).
- The 2024 archive index also omits rounds 1–9, although their files can still be retrieved by path.
- 2022 race files return HTTP 403 (both sampled races).

### F-A2. During the race, the archive prefix tracks a contemporaneous wall clock

The archive prefix is the `HH:MM:SS.mmm` timestamp at the start of each record. Three endpoints carry a server-side UTC timestamp in their payload: `Heartbeat` (every ~15 s), `RaceControlMessages` (whole seconds) and `ExtrapolatedClock`. Comparing those UTC values with the prefix, inside the race window (SessionStatus `Started` → final `Finished`, including red-flag `Aborted` segments):

- **Heartbeat.** For 50 of the 55 race-day-written races, the deviation from a constant per-session offset stays within [−2.4 s, +4.2 s]; in most races it is within [−2.0 s, +0.5 s]. In other words, the prefix is about 0–2 s *after* the record's own server timestamp, consistent with receipt latency. This includes the red-flag races São Paulo 2024 and Dutch 2026.
- **RaceControlMessages.** The same offset holds within [−3.55 s, −1.41 s] across every race-day-written race. The UTC values are whole seconds, which explains the wider band.
- **Cross-stream.** `LapCount.CurrentLap` increments lead the leader's `TimingData` lap advance by 0.0–0.35 s in every race-day-written race.

### F-A3. The prefix clock sometimes stalls, and stalls are detectable

- **Mid-race stalls.** Five of 55 race-day races contain in-race intervals where the prefix lags the Heartbeat UTC by more than 5 s: Las Vegas 2024 (max 21.7 s), Australia 2025 (34.9 s), British 2025 (13.7 s), São Paulo 2025 (5.7 s) and Dutch 2026 (5.3 s). Records stamped during a stall carry a prefix *earlier* than when they were really received. Used naively, that would leak information.
- **Pre-race replays.** Before the start, some sessions contain bursts where many records share one prefix (one replay of missed records after the recorder reconnected, e.g. Azerbaijan 2024).
- **Post-session freeze.** After `Finalised`, the prefix stops advancing while UTC continues.

Each case is visible in the Heartbeat deviation series.

### F-A4. Early 2018 clocks are corrupt

In Bahrain 2018 and Hungary 2018, the Heartbeat and RaceControlMessages UTC values are inconsistent with the prefix by thousands to millions of seconds. Abu Dhabi 2018 is consistent.

### F-B1. Pit entries and lap at entry reconstruct exactly

For every in-race `TimingData` `InPit` False→True transition, the lap count at entry `c(E)` is the driver's `NumberOfLaps` value at that point **in stream order**.

- **Race-day census.** 1975 of 1975 Jolpica pit stops in 54 races (one race had no Jolpica round match) are matched one-to-one by an archive entry with `c(E) + 1 ==` Jolpica in-lap.
- **Era sample.** Every Jolpica stop in every sampled race from 2018 to 2026 is matched the same way.
- **Extra entries.** The archive has 71 race-day (and 49 era-sample) in-race entries with no Jolpica stop. Thirteen (eight) are followed by no further lap, i.e. the car entered the pits and retired. The rest are pit-lane traversals that Jolpica does not list, many under red flags or safety cars.
- **Jolpica includes drive-throughs.** Russell's lap-53 drive-through in Monaco 2025 appears in Jolpica as a 19.5 s "stop". Matching Jolpica therefore validates pit entries, not tyre service.

### F-B2. Tyre-service evidence: TimingAppData stints are provisional at entry and final per visit

- A pit traversal opens a new stint *at entry* even when no tyres are changed. Example: Monaco 2025 #63, after a drive-through, got `TyresNotChanged:"1"`, `StartLaps:53`, the old compound and `New:"false"`.
- A later genuine stop may **overwrite the same stint index** (the same #63 stint 1 was rewritten to `MEDIUM`, `New:"true"`, `TyresNotChanged:"0"`).
- Within a visit, the first update is often `TyresNotChanged:"1"`; the final update before the next entry is the meaningful one.

Classifying each in-race visit by its **last** stint update in the window [entry, next entry):

| Class | Race-day census (54 races) | Era sample (24 races) |
| --- | ---: | ---: |
| `TyresNotChanged:"0"` (POS) | 1738 | 790 |
| `TyresNotChanged:"1"` (NEG) | 221 | 111 |
| no stint update (NONE) | 87 | 47 |

- **POS** is never contradicted by independent evidence. Here "contradicted" means a drive-through/stop-and-go penalty issued beforehand together with a pit-lane time at or below the race's minimum POS duration.
- **NEG** is corroborated by such independent evidence (penalty issued before the visit, or Jolpica duration below the race's minimum POS duration) in 138/221 (62%) and 58/111 cases. The uncorroborated NEG visits concentrate in red-flag and safety-car pit traversals (e.g. Qatar 2024 laps 36–37, Tuscany 2020), where the truth is genuinely uncertain.
- **NONE** occurs in roughly 1–4 visits per race, and in up to 12 in Bahrain 2026.

### F-B3. Race participation and terminal evidence

- `TimingData` `Retired:true` / `Stopped:true` flags, compared with Jolpica non-finisher status, agree for 156/166 race-day driver-races.
- **Jolpica-only (5):** post-race disqualifications. These are not participation terminals.
- **Archive-only (5):** `Stopped` flags. These can be temporary, e.g. every car under the Tuscany 2020 red flag.

### F-C1. Scheduled race distance

- In every race-day-written race, `LapCount.TotalLaps` is first published within about 2–10 s of the stream opening, which is more than 50 minutes before the race start. One exception is Spain 2024, at 68 s.
- Genuine in-race revisions appear at their own prefix (aborted starts / shortened races): São Paulo 2024 71→70→69, Australia 2025 58→57, Austria 2025 71→70, Canada 2026 70→68, Bahrain 2026 56→55.
- Spurious `TotalLaps:0` records appear shortly after the stream opens in several 2026 races, followed by a restatement of the real value.

## Support matrix

### (A) Prediction-time availability authority

| Scope (FastF1/F1 static live-timing archive, historical retrieval) | Endpoints | Timestamp meaning | Revision fidelity | **Authority level** |
| --- | --- | --- | --- | --- |
| **S-RD:** race sessions whose `TimingData` `Last-Modified` falls on the race date or the next UTC day. At 2026-10-10 that is 2024 R10–R24, 2025 R1–R24 and 2026 R1–R16, and later races as they are published and pass the same check | `TimingData`, `SessionStatus`, `LapCount`, `TimingAppData`, `RaceControlMessages`, `TrackStatus`, `DriverList` (shared recorder clock, F-A2) | Contemporaneous receipt clock inside clock-healthy windows (F-A2); stalls detectable (F-A3) | Written on race day and unmodified since (F-A1); retrieval must re-verify the date and record the SHA-256 | **`VERIFIED_BOUNDED_TIME`**, under the bounds and exclusion rules below |
| **S-RG:** race sessions rewritten in June 2024 (2018–2021, 2023, 2024 R1–R9) | all | Prefix behaviour resembles S-RD inside the race (F-A2), except 2018 R2/R12 (F-A4) | **Unproven.** The bulk rewrite happened years after the event, and no contemporaneous copy was available to compare (the Internet Archive was unreachable from this environment) | **`UNVERIFIED_ARCHIVE`**. For 2018 R2 and R12, **`UNSUPPORTED`** (corrupt clock) |
| **S-22:** 2022 | all | n/a | n/a | **`UNSUPPORTED`** (HTTP 403: not retrievable) |
| Contemporaneous capture | — | — | — | None exists. It is the upgrade path (see *Upgrade paths*) |

**Bounds for S-RD** (the `VERIFIED_BOUNDED_TIME` parameters `availability_time_or_bound` under #18):

- In a clock-healthy window, a record with prefix `P` has availability in **[P − 4 s, P + 15 s]**.
  - The lower margin covers the observed maximum receipt-before-prefix offset (3.55 s).
  - The upper margin is the longest stall that a 15-second Heartbeat cadence cannot detect.
- **Clock-healthy window.** Compute the in-race Heartbeat offset base. A Heartbeat is healthy if its deviation lies within [−4 s, +5 s]. The interval between two consecutive healthy Heartbeats is healthy only if no unhealthy Heartbeat lies between them. Any interval touching an unhealthy Heartbeat, a same-prefix burst, or the post-`Finalised` freeze is **unhealthy**.
- **Consequences under the #18 rules:**
  - A checkpoint whose trigger record falls in an unhealthy interval is `INDETERMINATE_CHECKPOINT`, with reason `COARSE_TIME_AMBIGUITY`.
  - A fact whose record falls in an unhealthy interval is omitted.
  - A fact is admitted only if `P_fact + 15 s < P_trigger − 4 s`, i.e. it precedes the trigger by more than 19 s. This is the #18 bounded-time rule.
- **Same-stream order.** Within one endpoint, archive order equals receipt order (F-B1 relies on it retrospectively). The authority level nonetheless stays `VERIFIED_BOUNDED_TIME` rather than `VERIFIED_STREAM_ORDERED`, because `VERIFIED_STREAM_ORDERED` would need the bounds to be exact. Equal-prefix ties are therefore omitted.

### (B) Target-reconstruction capabilities (retrospective; scopes S-RD and S-RG, excluding 2022)

| Capability (#19) | Verdict | Rule / limitation |
| --- | --- | --- |
| Pit-entry transition reconstruction | **SUPPORTED** | `TimingData` `InPit` False→True after `Started` (F-B1) |
| Pit-exit / visit segmentation | **SUPPORTED** | `InPit` True→False closes a visit. A visit may stay exit-open at retirement |
| Driver lap-completion occurrence (Amendment A1) | **SUPPORTED, order-based** | `c(E)` comes from same-stream order of `NumberOfLaps` advances relative to the entry record. That is exact (F-B1), so `EntryLapContext.c_exact` is populated. Archive prefixes are not used as occurrence times |
| Tyre-service positive | **SUPPORTED** | Last `TimingAppData` stint update in [entry, next entry) has `TyresNotChanged:"0"` (F-B2) |
| Tyre-service negative | **SUPPORTED ONLY WITH CORROBORATION** | `TyresNotChanged:"1"` on the last update **and** (a drive-through/stop-and-go penalty issued for the car before the entry, **or** Jolpica pit-lane duration below the race's minimum POS duration). Otherwise `INDETERMINATE_TYRE_SERVICE`. `TyresNotChanged` alone is **not** validated as sole negative proof (#19 verification item 10) |
| Tyre-service with no stint update | **INDETERMINATE** | `INDETERMINATE_TYRE_SERVICE` |
| Race participation / terminal | **SUPPORTED WITH RULES** | Participation ends at `Retired:true` (bounded by that record's prefix) or at the driver's final lap completion after `Finished`. `Stopped` alone is not terminal. A post-race disqualification is not a participation terminal (F-B3) |
| Interval coverage for no-event claims | **SUPPORTED** | Replay bursts keep the records (only their prefixes are late), so retrospective coverage is not lost. A missing stream or a parse gap makes coverage indeterminate |
| Stint transition / compound equality as qualification | **REJECTED** | This confirms the #19 rule (F-B2 shows provisional stints opened at drive-throughs) |

### (C) Scheduled race distance (`SCHEDULED_RACE_DISTANCE_LAPS`)

| Scope | Source | Verdict |
| --- | --- | --- |
| S-RD | `LapCount.TotalLaps` | **Admissible as a streamed fact under S-RD authority** (not as `STATIC_PRIOR`). The first value precedes the race-start trigger by far more than the 19 s margin (F-C1). Revisions apply from their own bounded availability. **Rule:** `TotalLaps ≤ 0` is invalid and ignored. `DISTANCE_REVISION_CHANNEL_UNVERIFIED` does not apply, because the revision channel is inside the verified scope |
| S-RG, S-22 | none verified | `SCHEDULED_DISTANCE_UNAVAILABLE` (moot, since checkpoints there are already indeterminate) |

## Consequences for `supported_scope` and V2 feasibility

- **Prediction-capable scope** (observations, predictions, backtests): **S-RD only**. That is 55 races at 2026-10-10 (15 in 2024, 24 in 2025, 16 in 2026), rising to about 62 once the remaining 2026 races are published and pass the checks.
- **Target-only scope** (retrospective analysis, baselines, exploratory statistics): S-RD ∪ S-RG, minus 2018 R2/R12. It cannot produce V2 observations.
- **The V2 historical-replay ambition remains feasible** on a smaller, recent corpus. The thesis-era 2018–2023 corpus cannot support leakage-safe V2 predictions as specified, unless an upgrade path succeeds. No approved semantics are relaxed, so no Product Owner decision is required by this verdict.
- **Expected truncation pressure.** About 3 indeterminate tyre-service visits per race (uncorroborated NEG plus NONE) truncate the episodes that precede them for that driver. Clock-unhealthy windows make some checkpoints indeterminate in about 5 of 55 races. The exact cohort impact is measured during implementation through the #21 accounting.
- **Hand-off to #37 (statistical protocol).** S-RD spans fewer than three full seasons, so the protocol must use `ROLLING_RACE_BLOCK` or `PRESPECIFIED` with the `LOW_POWER` qualifier (#21). A 2026 final partition has **no thesis-era prior exposure**.

## Upgrade paths (not performed here)

1. **Contemporaneous capture of the remaining 2026 races** (from 2026 R17), paired against their later archive copy. This is #18's explicitly acceptable "paired contemporaneous captures" evidence. It would measure public-feed receipt time against the archive prefix directly, and could tighten the bounds or upgrade S-RD to `VERIFIED_STREAM_ORDERED`. It needs capture tooling, which is out of #35 scope.
2. **Revision-fidelity evidence for S-RG**: independent pre-June-2024 copies of the same files (third-party caches, Internet Archive captures) compared byte-for-byte or record-for-record. A match would let S-RG be re-evaluated, though not 2018 R2/R12.
3. **Re-retrieval monitoring**: re-hash S-RD files periodically. A changed hash or `Last-Modified` removes that race from S-RD until it is re-validated.

## Routing

| Item | Classification | Owner |
| --- | --- | --- |
| Bounds, health-window rule, `TotalLaps ≤ 0` rule, and order-based `c(E)` as concrete parameterisations of approved #18/#19 rules | Verification parameters (this artifact) | #35; consumed by the implementation and by #36 fixtures |
| Last-update stint classification and corroborated-negative rule | Verification parameters within #19's three-state qualification | #35; #36 fixtures |
| Actual cohort/truncation rates | Later phase | Implementation (#21 accounting) |
| Season allocation, fold rule, `LOW_POWER` | Cross-slice | #37 |
| Capture tooling and S-RG revision evidence | Later / optional | Future verification work |

No design defect was found. The findings stay within the #18/#19 rules, which anticipated unverified archives, provisional stints and unvalidated `TyresNotChanged`.

## Acceptance mapping (Issue #35)

- **Every authority item and capability has a verdict per scope, with evidence:** the matrix tables (A), (B) and (C) and the findings F-A1 to F-C1.
- **Consequences for `supported_scope` and feasibility stated:** see *Consequences*.
- **Scripts reproduce the evidence from recorded hashes:** see the tools and evidence files above.
- **Product Owner escalation if the ambition becomes infeasible:** not triggered. The ambition stays feasible on S-RD.
- **Independent review:** pending.

## Review record

Pending independent full scoped review under `governance/REVIEW_POLICY.md`.
