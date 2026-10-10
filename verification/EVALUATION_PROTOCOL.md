# V2 Statistical Evaluation Protocol

## Status

Draft. Authored for Issue #37. Independent full scoped review is required before approval.

## Abstraction level

Verification and statistical design. This artifact fixes the following, which `design/REPLAY_BACKTEST.md` (#21) and `contexts/EVALUATION_BACKTESTING.md` routed to the verification phase:

- scoring rules;
- baselines;
- the model-selection objective;
- aggregation;
- dependence-aware uncertainty;
- truncation sensitivity;
- the probability-floor policy;
- the concrete `BacktestProtocol` configuration.

It does not change any of the following: the evaluation unit, the accounting categories, the cohort rules, prediction or target semantics, or the scope verdicts in `verification/SUPPORT_MATRIX.md`. It does not choose the production model family.

## Issue / branch

- Issue: #37. Parent: #34.
- Branch: `ccr-d8f3e250-t7uix3`.
- Consumes:
  - `design/PREDICTION_CONTRACT.md` (#20): canonical distribution, `RealizedOutcome`, pit-window rule;
  - `design/REPLAY_BACKTEST.md` (#21): protocol, folds, lock and ledger, cohort `cohort/v2`, scorer boundary;
  - `verification/SUPPORT_MATRIX.md` (#35): S-RD scope and its residual assumptions;
  - `decisions/2026-10-10-v2-race-day-archive-evidence-exception.md`.

## 1. Primary scoring rule

**Logarithmic score on the realized outcome**, in nats per evaluation unit; lower is better.

For an evaluation unit with canonical distribution `p[0..K_T−1], q` and #20 realized outcome:

| `RealizedOutcome.kind` | #21 category | Score `S` |
| --- | --- | --- |
| `REALIZED_REGION {j}` | A9 | `−ln p_j` |
| `REALIZED_REGION_SET {a..b}` | A10 | `−ln (p_a + … + p_b)` |
| `REALIZED_NO_EVENT` | A11 | `−ln q` |

Rationale:

- **Strictly proper.** The log score is strictly proper on the K_T + 1 outcome partition. For a set-valued outcome it is the log score of the *coarsened* event `{a..b}`. That is proper for the information actually observed: the event is known to lie in the set, and its position within the set is unknown. No interpolation within the set is assumed.
- **Local.** It depends only on the probability of what happened. So it is well defined across observations whose grid size `K_T` differs, without rescaling.
- **Terminal no-event is scored through `q`,** exactly as `contexts/EVALUATION_BACKTESTING.md` §6 requires. There is no artificial final lap.
- **Truncation (A6) and run defects (A0/A5/A7/A8) are never scored.** They remain in the accounting (#21).

**Probability floor policy.**

- Every procedure eligible for a lock must guarantee `p_j ≥ 10⁻⁶` and `q ≥ 10⁻⁶` for every snapshot. The floor is applied inside the frozen procedure, before #20 validation, and declared in the `ProcedureSpec`.
- The lock check verifies this on all development-validation snapshots.
- The scorer never clips. A realized outcome with probability 0 makes the score infinite, and the run is reported as a procedure failure.
- 10⁻⁶ per outcome costs at most about 79 × 10⁻⁶ of mass even at the largest `K_T`, which is negligible.

## 2. Primary aggregate and skill

- **Primary aggregate:** the mean log score over all units of the primary cohort (A9 ∪ A10 ∪ A11 of a `VALID` backtest run), with equal weight per unit. This answers the per-checkpoint forecast-quality question (#21 grouping level `unit`).
- **Primary skill:** the paired difference `ΔS = mean(S_procedure − S_B1)` against baseline B1 (§4), computed on the **identical** unit set. Negative values mean the procedure beats B1.
  - Pairing removes most cohort-composition effects, including those from truncation, because both forecasts are scored on the same units.
- **Required secondary aggregates** (analysis class `SECONDARY`):
  - **Driver-race-weighted mean:** each driver-race has total weight 1. This prevents long stints with many checkpoints from dominating.
  - **Event-trajectory-weighted mean:** each `event_trajectory_key` has total weight 1.
  - Breakdowns by outcome kind (A9, A10, A11) and by `K_T` tercile. These are labelled `RETROSPECTIVE_DIAGNOSTIC` where they condition on the outcome.

## 3. Dependence-aware uncertainty

Evaluation units are strongly dependent within a race. Safety cars, weather and strategy phases are shared by all drivers, and repeated checkpoints forecast the same eventual stop.

- **Cluster bootstrap with the race as the cluster.**
  - Resample race sessions with replacement, B = 10,000 times.
  - Recompute every aggregate, including the paired `ΔS`, using all units of each resampled race.
  - Report the 95 % percentile interval.
  - Driver-races and event trajectories are nested within races, so race-level resampling captures their dependence without further modelling.
- **Sensitivity:** a leave-one-race-out jackknife on `ΔS`, reporting the most influential race.
- **Power statement.** The effective sample size is the number of races: the F1 partition has 16 races and F2 has up to 7 (§7). Intervals will be wide, and every claim carries the `LOW_POWER` qualifier (#21). No hypothesis test with a fixed α is pre-registered. The primary claim is the point estimate of `ΔS` with its bootstrap interval.

## 4. Baselines (pre-specified)

All baselines:

- are fitted on exactly the development data a procedure would see, with the same cutoff rules;
- use the observation's own `RegionGrid`;
- emit through the #20 `DISCRETE_HAZARD` adapter;
- apply the §1 floor;
- use only causal inputs from the canonical observation (#20 input boundary).

| ID | Definition | Inputs at T |
| --- | --- | --- |
| **B0 (climatology)** | Pooled discrete hazard by lap offset: `λ(h)` for `h = 0..H_max` (the last bin pools `h ≥ H_max` with `H_max = 40`), plus `q_open` as the pooled empirical share of terminal no-event among episodes surviving into the final region | `RegionGrid` only |
| **B1 (tyre-age hazard)** | Logistic discrete-time hazard: `logit λ = β0 + β1·age + β2·age² + β3·compound + β4·frac_remaining`, where `age = stint_age_at_T + h` and `frac_remaining = (N_T − (L + h)) / N_T`. `q_open` is fitted as a logistic function of `frac_remaining` at the final region and the current compound | Current stint age and compound (#18 `TimingAppData` facts admissible at T), `L`, `N_T` |
| **B-thesis (secondary)** | The `p_0` component of B1, compared with the thesis-era binary "pit next lap" framing using the Brier score on the event "entry in `R_0`". This is for continuity only | as B1 |

- **Fitting.** Hazard models are fitted by maximum likelihood on person-period data built from development episodes: each region `h` of each A9 episode until the event region, and every region for A11 episodes. A10 episodes contribute interval-censored likelihood over `{a..b}`. A6 episodes are excluded from fitting. This is the same treatment the primary cohort gets, and it is the documented B-fitting rule.
- **Role.** B1 is the **reference** for the primary skill. B0 gives context on how much any state information helps.

## 5. Secondary diagnostics (analysis class `SECONDARY` or `RETROSPECTIVE_DIAGNOSTIC`)

1. **Ranked probability score** over the ordered outcomes `R_0 < R_1 < … < R_{K_T−1} < no-event`, normalized by `K_T`. It is sensitive to distance in timing. A10 outcomes take the minimum and maximum RPS over the set; both are reported.
2. **Calibration:**
   - reliability tables (10 equal-count bins) for `P(entry in R_0)`, `P(entry in R_0 ∪ R_1 ∪ R_2)` and `q`;
   - a randomized probability integral transform of the realized offset (uniform within the realized region and within sets), shown as a histogram with a χ² uniformity statistic, reported descriptively.
3. **Sharpness:** the mean entropy of the forecast distribution.
4. **Pit-window faithfulness** (#20 `pit-window/v1`, α = 0.8):
   - the empirical frequency with which the realized event falls inside the window, among event outcomes, compared with α (conditional coverage);
   - calibration of the window's absolute `mass_in_window`.
   - These are `SECONDARY`, and never a substitute for §1.
5. **Brier score** for "entry within the next lap" (`R_0`), as a comparison with B-thesis.

## 6. Model-selection objective (development folds)

- **Objective:** the primary aggregate (mean log score) pooled over all development-validation units of the `VALID` fold backtests, with the §3 race-cluster bootstrap standard error computed over development races.
- **Candidate budget:** at most **10** `ProcedureSpec`s may be evaluated on the development folds. They are listed, with digests, in a pre-registration note before the first fold is scored. Each counts toward the budget, including hyperparameter variants. Adding a candidate after seeing fold results consumes budget and is recorded.
- **Rule:**
  1. Choose the candidate with the lowest pooled mean log score.
  2. If another candidate lies within **one bootstrap SE** of it and has fewer free parameters, choose the simpler one.
  3. If no candidate beats B1 on the pooled development objective, the locked procedure is **B1 itself**. That still allows a final claim of "B1 versus B0".
- **Fold-level defects:** fold runs that are `DEFECTIVE` (#21) are not selection evidence. Defective races are re-scoped through `supported_scope` before scoring.

## 7. `BacktestProtocol` configuration (declared values)

| Field | Value | Justification |
| --- | --- | --- |
| `supported_scope` | S-RD per `verification/SUPPORT_MATRIX.md`: 2024 R10–R24, 2025 R1–R24 and 2026 R1–R16, plus 2026 R17–R23 if each passes the S-RD check (race-day `Last-Modified`, `--verify` clean) when retrieved | The only prediction-capable scope |
| `development_partition` | 2024 R10–R24 + 2025 R1–R24 (39 races) | All S-RD races before 2026 |
| `final_partition` | **F1:** 2026 R1–R16 (16 races). **F2:** 2026 R17–R23 (up to 7 races), as a separately ledgered second final partition | F2 races had not happened when this protocol was written. They carry no exposure of any kind and allow an untouched confirmatory claim |
| `development_fold_rule` | `ROLLING_RACE_BLOCK`. Minimum training block: 2024 R10–R24 (15 races). Validation blocks of `b = 6` races: 2025 R1–6, R7–12, R13–18, R19–24 (4 folds). Each block is fitted with cutoff = its first race (expanding window) | S-RD spans fewer than 3 full seasons (#21 fallback). Six-race blocks give about 4 folds while keeping each fit's training set ≥ 15 races |
| `final_refit_cadence` | `NONE`. One model is fitted on all 39 development races (cutoff = 2026 R1) and used for both F1 and F2 | Simplest leakage-free option; no final outcomes enter any fit |
| `resolution_run_ref` | The first complete #19 resolution run over S-RD produced by the implementation, declared (by reference) before the lock | Fixed before any final opening |
| `primary_cohort_rule_version` | `cohort/v2` (#21) | Unchanged |
| `candidate_scope_rule` | All race sessions in the partitions; all driver entries; no further restriction | Pre-race attributes only |
| `prior_exposure` | **F1:** "Aggregate pit-entry, stint and penalty statistics and archive clock behaviour of 2026 R1–R16 (and 2024–2025 races) were inspected during #35 verification (`verification/evidence/`). No model fitting, feature selection or procedure choice used them." **F2:** none | Honest declaration. F1 claims carry `PRIOR_EXPOSURE_DECLARED` |
| Qualifiers | `LOW_POWER` on all claims; `PRIOR_EXPOSURE_DECLARED` on F1 | #21 rules |

**Claim structure.**

- The primary final claim is `ΔS` (locked procedure versus B1) on **F1**, with its bootstrap interval. Its labels are `PRIMARY_FINAL`, `PRIOR_EXPOSURE_DECLARED` and `LOW_POWER`.
- When F2 is complete, the same locked procedure (no refit) is evaluated on **F2** as an independent confirmatory `PRIMARY_FINAL` claim, labelled `LOW_POWER` only.
- Both claims cite the evidence exception and RA-1–RA-4.

## 8. Truncation (A6) and defect sensitivity

Truncation is expected to be substantial, because about 14.5 % of visits are `INDETERMINATE_TYRE_SERVICE` (#35). It is handled as follows:

1. **Accounting report** (#21 record-level table): A6 share overall, by race, by driver-race, by `K_T` tercile and by checkpoint lap phase. Every claim reports this table alongside its score.
2. **Paired skill as primary:** truncation affects procedure and baseline identically, so `ΔS` is insensitive to cohort composition to first order.
3. **Reweighting sensitivity** (`SECONDARY`): inverse-probability weights equal to 1 / (resolvable share) within strata of race × `K_T` tercile. Report the reweighted mean log score and `ΔS`.
4. **Restriction sensitivity** (`SECONDARY`): repeat the primary analyses on races whose A6 share is below the median.
5. **Stop rule:** if the A6 share exceeds **50 %** of eligible checkpoints in F1, the F1 claim is still computed but labelled `RETROSPECTIVE_DIAGNOSTIC`, not `PRIMARY_FINAL`. Too much of the population would then be missing for a primary claim. This threshold is fixed here, before any final opening.

## 9. Reporting requirements

Every score report states:

- partition and ledger role;
- analysis class;
- qualifiers;
- unit count and race count;
- the accounting table;
- the evidence-exception reference;
- the scorer version.

It includes §1–§3 results for the locked procedure, B1 and B0, and the §8 sensitivities.

## Routing

| Item | Owner |
| --- | --- |
| Concrete candidate procedures (model family, features) | Implementation / experimentation, within the §6 budget |
| Scorer implementation and bootstrap code | Implementation; fixtures in #36 |
| `resolution_run_ref` value | Implementation, declared before the lock |
| Inclusion of 2026 R17–R23 | Re-run of the #35 probe and `--verify` when each race is published |

## Acceptance mapping (Issue #37)

- **Proper primary score, terminal no-event scored through `q`, set-valued outcomes defined:** §1.
- **Dependence-aware uncertainty:** §3.
- **Pre-specified baselines and selection objective:** §4 and §6.
- **Declared protocol values, consistent with the support matrix:** §7.
- **Independent review:** pending.

## Product Owner decisions

None required. Scoring, baselines and protocol values are delegated verification choices within the approved evaluation semantics and the Product Owner's evidence exception.

## Review record

Pending independent full scoped review under `governance/REVIEW_POLICY.md`.
