# V2 Statistical Evaluation Protocol

## Status

Approved. The bounded re-review passed on PR #39 for substantive head `eca220a5d96ae71c0a276169bc6485e8fd8e218c`. A follow-up commit applies only the reviewer's three Minor clarifications.

## Abstraction level

This is a verification and statistical design artifact. It fixes the following choices, which `design/REPLAY_BACKTEST.md` (#21) and `contexts/EVALUATION_BACKTESTING.md` routed to verification:

- scoring rules and baselines;
- the model-selection objective;
- aggregation and dependence-aware uncertainty;
- truncation sensitivity;
- the probability-floor policy;
- the concrete `BacktestProtocol` declarations.

It does not change the following: the evaluation unit, the accounting categories, `cohort/v2`, ledger labels or their ownership, the lock mechanics, prediction or target semantics, or the scope verdicts in `verification/SUPPORT_MATRIX.md`. It does not choose the production model family.

## Issue / branch

- Issue: #37. Parent: #34.
- Branch: `ccr-d8f3e250-t7uix3`. PR: #39.
- Consumes:
  - #20 `design/PREDICTION_CONTRACT.md`;
  - #21 `design/REPLAY_BACKTEST.md`;
  - #35 `verification/SUPPORT_MATRIX.md`;
  - `decisions/2026-10-10-v2-race-day-archive-evidence-exception.md`.

## 1. Primary scoring rule

This protocol uses the **logarithmic score on the realized outcome**, in nats per evaluation unit. Lower is better.

| `RealizedOutcome.kind` | #21 category | Score `S` |
| --- | --- | --- |
| `REALIZED_REGION {j}` | A9 | `−ln p_j` |
| `REALIZED_REGION_SET {a..b}` | A10 | `−ln (p_a + … + p_b)` |
| `REALIZED_NO_EVENT` | A11 | `−ln q` |

- **Propriety.**
  - The log score is strictly proper on singleton outcomes (A9, A11).
  - For A10 it is the log score of the coarsened event `{a..b}`. It is proper under coarsening at random: which set is observed must not depend on where the event lies inside the set. That assumption is stated here.
  - #35 established that `c(E)` is exact in S-RD (table C), so A10 is expected to be empty or negligible in every protocol below. Its count is reported.
- **Terminal no-event** is scored through `q`, as `contexts/EVALUATION_BACKTESTING.md` §6 requires.
- **Never scored.** Truncation (A6) and run defects (A0, A5, A7, A8) remain in #21 accounting only.
- **Infinite scores.** If any unit has probability 0 on its realized outcome, that unit scores +∞ and so does the aggregate. The claim is then reported as **failed**. Accounting categories are unchanged (#21 scorer rule 1).

**Probability floor policy.** The floor is part of the forecaster, not the scorer, so the score stays proper.

- Every procedure eligible for a lock, including B0 and B1, must emit canonical distributions with `p_j ≥ 10⁻⁶` and `q ≥ 10⁻⁶`.
- The floor is applied at the **PMF level** as the mixture `p' = (1 − (K_T + 1)·10⁻⁶)·p + 10⁻⁶` over all `K_T + 1` outcomes.
- A hazard-form estimator then re-expresses `p'` as hazards for the #20 `hazard/v1` adapter: `λ_j = p'_j / S_j`, and `q_open = q' / S_{K_T−1}`. Alternatively it emits PMF form directly.
- The lock check verifies the floor on all development-validation snapshots.

## 2. Estimand, aggregate and skill

- **Estimand.** Forecast quality on the **resolvable primary cohort**: A9 ∪ A10 ∪ A11 of a `VALID` backtest run under `cohort/v2`.
  - Truncation is outcome-linked: an indeterminate visit truncates the episodes that precede it (#35).
  - Results therefore describe the resolvable population and are **not** claimed to generalize to truncated episodes. Section 8 quantifies this limitation; it does not remove it.
- **Primary aggregate.** The mean log score over cohort units, each unit weighted equally (#21 grouping level `unit`).
- **Primary skill.**
  - `ΔS = mean(S_locked − S_ref)` on the identical unit set. Negative values favour the locked procedure.
  - The reference is B1 (section 4).
  - If section 6 rule 3 locks B1 itself, the primary comparison becomes **B1 against B0**.
- **Secondary aggregates** (analysis class `SECONDARY`, full cohort):
  - the driver-race-weighted mean, where each driver-race carries total weight 1;
  - the event-trajectory-weighted mean.
- **Outcome-conditioned breakdowns** are labelled `RETROSPECTIVE_DIAGNOSTIC` (#21 scorer rule 3). They cover breakdowns by A9/A10/A11, and breakdowns by `K_T` tercile, where the tercile cut-points are fixed from **development** data.

## 3. Dependence-aware uncertainty (few clusters)

Units are dependent within a race. The cluster is therefore the race session. With G = 16 (F1) or G ≤ 7 (F2) clusters, a percentile bootstrap would under-cover.

- **Primary interval.** Treat the unit-level paired differences `d_i = S_locked,i − S_ref,i` as a regression of `d` on an intercept.
  - The intercept is the unit-weighted `ΔS`.
  - Use a **CR2 (bias-reduced) cluster-robust standard error** by race.
  - Use the **t distribution with G − 1 degrees of freedom**.
  - Report the 95 % interval.
- **Co-reported.**
  - A wild cluster bootstrap (Webb six-point weights, B = 9,999) interval for `ΔS`.
  - A leave-one-race-out jackknife. This is an influence check only, naming the most influential race.
- **Minimum cluster count.** With **G < 10** races, intervals are reported as **descriptive only**, and the claim is limited to the point estimate and its sign. This applies to F2 unless it reaches 10 races, which it cannot in 2026.
- **Qualifiers and caveats.** Every claim carries `LOW_POWER` (#21). No fixed-α hypothesis test is pre-registered. All intervals are conditional on the fitted, locked models. They do not include training variability.

## 4. Baselines (pre-specified)

All baselines share these rules:

- They are fitted on exactly the development data a procedure would see, with the same cutoff rules.
- They use the observation's own `RegionGrid`.
- They apply the section 1 PMF-level floor.
- They use only causal inputs from the canonical observation (#20 input boundary).
- They never impute omitted facts retrospectively (#20 rule 5).

| ID | Definition | Inputs at T |
| --- | --- | --- |
| **B0** (climatology) | Pooled discrete hazard by lap offset `λ(h)` for `h = 0..39`, with the last bin pooling `h ≥ 40`. `q_open` is the pooled empirical share of terminal no-event among episodes that survive into the final region | `RegionGrid` only |
| **B1** (tyre-age hazard) | `logit λ_h = β0 + β1·a + β2·a² + β_c[compound] + β4·f_h`, where `a = stint_age_at_T + h` and `f_h = (N_T − (L + h)) / N_T`. Compound levels are `SOFT`, `MEDIUM`, `HARD`, `INTERMEDIATE`, `WET` and `OTHER`. `q_open = logit⁻¹(γ0 + γ1·f_T + γ_c[compound])`, with `f_T = (N_T − L) / N_T` | Current stint age and compound (#18 `TimingAppData` facts admissible at T, under RA-2 and the #35 10 s cross-stream margin), plus `L` and `N_T` |
| **B-thesis** (secondary) | The `p_0` of B1, scored by Brier on the event "entry in `R_0`", for continuity with the thesis-era binary framing | as B1 |

- **B1 omission rule.** B1 emits B0's distribution for an observation when the canonical state at T shows **any** of the following:
  - stint age or compound is omitted, i.e. not admissible;
  - the latest admissible stint update carries `TyresNotChanged:"1"`;
  - there has been no admissible stint update since the driver's last pit entry.

  The trigger uses only facts in the canonical state at T, never #19's retrospective service classification. It is deterministic and involves no imputation.
- **Fitting.**
  - Maximum likelihood on person-period data built from development episodes.
  - A9 episodes contribute through their event region. A11 episodes contribute through all regions.
  - A10 episodes contribute an interval-censored likelihood over `{a..b}`.
  - A6 episodes are excluded, the same as in the cohort.
- **Alternatives.** Candidate procedures may instead censor A6 episodes at their first indeterminate visit, or use a lap-level person-period construction that avoids repeating the same driver-lap across successive checkpoints. Such a choice is declared in the `ProcedureSpec`.

## 5. Secondary diagnostics

| Diagnostic | Class |
| --- | --- |
| Ranked probability score over `R_0 < … < R_{K_T−1} <` no-event, normalized by `K_T`. A10 reports the minimum and maximum over the set | `SECONDARY` |
| Reliability tables (10 equal-count bins) for `P(R_0)`, `P(R_0 ∪ R_1 ∪ R_2)` and `q`, over the full cohort | `SECONDARY` |
| Sharpness: mean forecast entropy | `SECONDARY` |
| Brier score for "entry in `R_0`", for the locked procedure, B1 and B-thesis | `SECONDARY` |
| Randomized probability integral transform of the realized offset, over **event outcomes only** (A9/A10), uniform within the region or set, with a descriptive χ² | `RETROSPECTIVE_DIAGNOSTIC` |
| Pit-window (`pit-window/v1`, α = 0.8) conditional coverage among event outcomes, compared with the mean of `mass_in_window / P_event`, not with α, because discrete windows hold at least α of the event mass | `RETROSPECTIVE_DIAGNOSTIC` |
| Calibration of the window's absolute `mass_in_window`, over the full cohort | `SECONDARY` |

## 6. Model-selection objective (development folds)

- **Objective.** The primary aggregate (mean log score) pooled over all development-validation units of the `VALID` fold backtests. Defective folds are re-scoped through `supported_scope` and are never used as evidence.
- **Pre-registration note.** It is committed before the first fold is scored and lists, for every candidate:
  - its `ProcedureSpec` digest;
  - a **complexity rank**: a strict total order declared by the author, for example by effective number of parameters. Ties are broken by registration order.
- **Budget.** At most **10** candidates. B0 and B1 are **not** counted. Any candidate added after fold results are seen consumes budget and is recorded as a late addition.
- **Selection rule.**
  1. `best` = the candidate with the lowest pooled mean log score.
  2. For each other candidate `c`, compute `ΔS_c,best` and its race-cluster CR2 standard error over development races.
  3. If `ΔS_c,best ≤ 1·SE` for some candidates with a **lower complexity rank**, choose the lowest-ranked among them. Otherwise keep `best`.
  4. If the chosen candidate does not beat B1 on the pooled development objective (`ΔS < 0`), lock **B1**.

## 7. Protocol declarations

Two `BacktestProtocol`s are declared. Each conforms to #21 as written: one final partition, one digest, one lock, coverage-checked.

### P-F1 (primary)

| Field | Value |
| --- | --- |
| `supported_scope` | The 55 S-RD races of `verification/SUPPORT_MATRIX.md`: 2024 R10–R24, 2025 R1–R24, 2026 R1–R16 (fixed list) |
| `development_partition` | 2024 R10–R24 and 2025 R1–R24 (39 races) |
| `final_partition` | 2026 R1–R16 (16 races) |
| `development_fold_rule` | `ROLLING_RACE_BLOCK`. Minimum training block: 2024 R10–R24 (15 races). Blocks of `b = 6`: 2025 R1–6, R7–12, R13–18, R19–24 (4 folds), each with cutoff equal to the block's first race |
| `final_refit_cadence` | `NONE`. One `ModelArtifact` fitted on all 39 development races, with cutoff 2026 R1 |
| `resolution_run_ref` | The first complete #19 resolution run over S-RD produced by the implementation, declared by reference before the lock |
| `primary_cohort_rule_version` | `cohort/v2` |
| `candidate_scope_rule` | All race sessions and driver entries in the partitions; no further restriction |
| `prior_exposure` | See below |
| Qualifiers | `LOW_POWER`, `PRIOR_EXPOSURE_DECLARED` |

**P-F1 prior exposure (declaration).**

- During #35 verification, the raw archive streams of 2026 R1–R16 (and of 2024–2025 races) were downloaded and processed, together with Jolpica results and pit-stop responses.
- The committed evidence includes **per-race, per-driver facts** for those races: pit entries with laps, tyre-service classes, penalty visits, retired and stopped drivers, `TotalLaps` series and clock behaviour. These are in `verification/evidence/capabilities_raceday_scope_v2.json`, `probe_raceday_scope_v*.json` and `clock_fixture_raceday_scope_v1.json`.
- **This protocol, including the B0 and B1 specifications, the 50 % truncation threshold and the expected truncation share, was authored after that inspection.** B1 can become the locked procedure (section 6, rule 4).
- No model was fitted to those races, and no V2 resolution artifact was read. This is therefore a declaration, not a ledger opening (#21).
- F1 claims carry `PRIOR_EXPOSURE_DECLARED`.

### P-F2 (confirmatory)

| Field | Value |
| --- | --- |
| `supported_scope` | P-F1's 55 races, plus the F2 races admitted by the inclusion rule below |
| `development_partition` | As P-F1 |
| `final_partition` | **Rule:** every 2026 Formula 1 championship race held after 2026 R16 and before 2027-01-01 that passes the F2 inclusion rule. The rule is resolved to a **fixed list of races**, recorded in P-F2 before its lock and before any F2 opening; #21 coverage checks against that list |
| Lock | A separate `EvaluationLock` with the **same** `procedure_id`, seeds and `ModelArtifact` as P-F1, and no refit |
| Commitment | P-F2 (rule and digest) is committed **before any P-F1 final opening** |
| `prior_exposure` | None, provided the inclusion rule is followed |
| Qualifiers | `LOW_POWER`. With fewer than 10 races, intervals are descriptive only (section 3) |

**F2 inclusion rule (fixed now; metadata only).** A race is admitted if and only if all of the following hold:

1. HTTP 200 for its archive `TimingData` file.
2. `Last-Modified` on the race date or the next UTC day.
3. The SHA-256 of the raw downloaded bytes, computed **without parsing**, is identical across two retrievals at least 24 h apart.

No record content may be parsed or analysed before the P-F2 lock. A failing race is excluded through scope, never record by record. Any capability, pit or tyre analysis of an F2 race before its lock is an exposure. It must be registered as an `AD_HOC_OPENING` (#21), which makes that race `POST_HOC`, or declared in P-F2's `prior_exposure`.

**Claims.** The primary final claim is `ΔS` on P-F1, labelled `PRIMARY_FINAL` by the ledger. P-F2 then gives an independent confirmatory claim with the same locked artifact. The P-F2 claim is **reported whatever the P-F1 result**, so confirmation is never selective. Both claims cite the evidence exception and RA-1–RA-4 (#35).

## 8. Truncation (A6) handling and sensitivity

**Definition.** The truncation share of a `VALID` run is `A6 / (A6 + A9 + A10 + A11)`.

1. **Accounting.** Every claim reports the #21 record-level accounting summary: the A6 share overall, by race, by driver-race, by development-fixed `K_T` tercile, and by checkpoint lap phase.
2. **Primary-class condition (all final claims, P-F1 and P-F2).** `analysis_class = PRIMARY` additionally requires a truncation share of **≤ 50 %**. Above that, the scores are computed and reported with `analysis_class = SECONDARY`. The ledger-assigned `ledger_role` is unchanged.
3. **Reweighting sensitivity (`SECONDARY`).**
   - Weights are the inverse of the resolvable share within strata of race × `K_T` tercile.
   - Report the reweighted mean log score and `ΔS`.
   - **Assumption:** truncation is missing at random given the strata. The known mechanism, truncation caused by an indeterminate visit, violates this. The result is therefore indicative only.
4. **Restriction sensitivity (`RETROSPECTIVE_DIAGNOSTIC`).** Repeat the analyses on races with a truncation share below the median.
5. **Mechanism-targeted sensitivity (`RETROSPECTIVE_DIAGNOSTIC`).**
   - Scope: each A6 unit whose truncation reason is an indeterminate tyre-service visit `V`, where `V` lies at region index `v` on that unit's grid. `v` is computed with the #20 mapping from `V`'s pit-entry lap count.
   - **Cross-slice dependency (#19).** `V`'s lap count requires a retrospective lap context for visits that cause truncation. #19 currently produces `EntryLapContext` only for selected qualifying events, and the backtest join may not read source evidence. Until #19 provides an additive artifact for these visits, this diagnostic is reported as **not computable**.
   - Score the unit under both resolutions of `V`:
     - **(a) `V` qualifies:** the realized outcome is region `v`, so `S_a = −ln p_v`.
     - **(b) `V` does not qualify:** only the coarsened event "no qualifying entry before region `v`" is known, so `S_b = −ln (1 − (p_0 + … + p_{v−1}))`.
   - Report `ΔS` over cohort ∪ A6 under scenario (a) and under scenario (b). These are two scenarios, **not bounds**: (b) scores only a coarsened event.
   - These scores are diagnostic. They never alter accounting and never convert `NOT_REALIZED` (#20, #21).

## 9. Reporting requirements

Every score report states:

- the protocol (P-F1 or P-F2) and the ledger role;
- the analysis class and qualifiers;
- unit and race counts;
- the accounting summary and truncation share;
- the evidence-exception reference;
- the scorer version.

It includes the section 1–3 results for the locked procedure, B1 and B0, and the section 8 sensitivities.

## Routing

| Item | Owner |
| --- | --- |
| Candidate procedures (within the section 6 budget and pre-registration) | Implementation / experimentation |
| Scorer, CR2 / wild-bootstrap code, metadata-only F2 inclusion check | Implementation; fixtures in #36 |
| `resolution_run_ref` value | Implementation, declared before each lock |
| Visit lap count for section 8.5 | Cross-slice dependency on #19 (additive lap context for visits that cause truncation); until then the diagnostic is not computable |

## Acceptance mapping (Issue #37)

- **Proper primary score:** section 1, with the coarsening-at-random assumption stated. Terminal no-event is scored through `q`, and the set-valued treatment is defined.
- **Dependence-aware, few-cluster-valid uncertainty:** section 3.
- **Pre-specified baselines and a deterministic selection objective:** sections 4 and 6.
- **Declared protocol values consistent with #21 and #35, including an accurate prior-exposure declaration:** section 7.
- **Truncation sensitivity:** section 8.
- **Independent review:** full review FAIL, then bounded re-review PASS, on PR #39.

## Product Owner decisions

None required. These are delegated verification choices within the approved evaluation semantics and the Product Owner's evidence exception.

## Review record

### Full scoped review — FAIL, rework required

- PR: #39. Reviewer: an independent review agent; recorded on PR #39 as a `COMMENT` review through the connected account. Date: 2026-10-10. Reviewed head: `b7159209`.
- **Major findings:**
  1. F2 was not expressible as a #21 protocol.
  2. The F2 inclusion rule was outcome-bearing.
  3. The F1 prior-exposure declaration was inaccurate.
  4. The stop rule overrode ledger and analysis-class semantics.
  5. The truncation reasoning and sensitivities were invalid.
  6. Uncertainty estimates were unreliable with few clusters.
  7. The selection rule was not deterministic.
- **Minor findings:**
  8. The coarsening-at-random assumption and infinite scores were not addressed.
  9. The floor did not work with hazard-form output.
  10. The B1 specification had gaps.
  11. The diagnostic classes and definitions were wrong.
- Product Owner decision: none required.

### Rework

1. P-F1 now has a fixed scope and partition. P-F2 is a separate protocol with its own lock (same procedure, seeds and artifact), committed before any F1 opening.
2. F2 inclusion is now metadata-only (status, race-day `Last-Modified`, hash stable over at least 24 h, no parsing). Pre-lock analysis counts as registered or declared exposure.
3. The F1 prior-exposure declaration is now itemized and states that the protocol and baselines postdate the inspection.
4. The stop rule is now a `PRIMARY` analysis-class condition with a defined denominator, applied to all final claims. The ledger role is untouched.
5. The estimand is stated as the resolvable cohort. The first-order claim was removed. The missing-at-random assumption is stated. The restriction analysis is relabelled `RETROSPECTIVE_DIAGNOSTIC`. A mechanism-targeted bounding diagnostic was added.
6. Uncertainty now uses a CR2 + t(G−1) primary interval, a co-reported wild cluster bootstrap, a jackknife influence check, and a G < 10 descriptive-only rule.
7. Selection now uses the SE of the paired difference, a declared complexity rank with deterministic tie-breaks, a budget that excludes baselines, and B1 against B0 when B1 is locked.
8. The coarsening-at-random assumption is stated, and infinite aggregates are reported as failures with accounting unchanged.
9. The floor is applied as a PMF-level mixture, re-expressed as hazards.
10. B1 now has omission fallback to B0, listed compound levels, and an `f_T` covariate for `q_open`.
11. Diagnostic classes are corrected, coverage is compared with the window mass, PIT is restricted to event outcomes, and tercile cut-points come from development data.

Observations adopted: the alternative censoring and lap-level construction, and intervals that are conditional on the fitted models.

### Bounded re-review — PASS

- PR: #39. Reviewer: the same independent review agent; recorded on PR #39 as a `COMMENT` review through the connected account. Date: 2026-10-10.
- Reviewed substantive head: `eca220a5d96ae71c0a276169bc6485e8fd8e218c`.
- Outcome: **PASS**. All prior findings 1–11 are resolved, and no Blocking or Major findings remain.
- Minor findings fixed in the follow-up commit:
  - R1: the section 8.5 lap context is routed to #19 as a cross-slice dependency, the diagnostic is not computable until then, and (a) and (b) are called scenarios, not bounds.
  - R2: the B1 fallback trigger uses only facts at T.
  - R3: the P-F2 rule is resolved to a fixed list before its lock, and P-F2 is reported whatever P-F1 shows.
- Product Owner decision: none required.
