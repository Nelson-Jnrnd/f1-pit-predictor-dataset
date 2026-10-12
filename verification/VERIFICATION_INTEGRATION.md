# V2 Verification Integration Gate

## Status

**PASS** (single bounded re-check, 2026-10-12; reviewed `main` at `aa316a7bcd16d3c53d54a55a1698d2405c51f979`). This outcome supersedes the initial CHANGES REQUIRED verdict below.

V1-V6 are resolved by the independently reviewed amendments in PR #45 (review `5489060100`). O1 now has an explicit implementation requirement and fixture. R-A..R-K retain their routed, non-blocking defaults and their pre-registration conditions. The technical implementation gate passes. **The Product Owner has requested a concise visual overview for approval before implementation; implementation remains paused for that requested overview approval.** No production work or final-resolution opening was performed by this re-check.

The initial composition checks, findings and outcome are preserved as the historical review record. Current closure evidence is recorded in *Bounded re-check* below.

## Abstraction level

Verification integration only. This is a bounded review of how the three approved verification artifacts compose with each other and with the approved designs, contexts and decisions.

This artifact does not re-review any slice internally and does not patch any slice. It does not reopen approved semantics or designs unless a contradiction is demonstrated, and it selects no metric, estimator, fixture value, model or implementation.

## Issue / branch

- Issue: #43, `Verification — integration gate (#34 work package 4)`
- Parent: #34
- Branch: `ccr-d8f3e250-t7uix3`, the session task branch. It equalled `origin/main` at `1117d6d` for this review.

## Reviewed canonical artifacts

All three verification slices are approved, with a passing bounded re-review recorded in each one. All are merged to `main`:

| Slice | Artifact | Merge PR | Merge commit |
| --- | --- | --- | --- |
| #35 | `verification/SUPPORT_MATRIX.md`: scopes S-RD / S-RG / S-22, error model, health windows, admission rules, #18 items 1–15, #19 capabilities, scheduled distance (plus `verification/tools/`, `verification/evidence/`) | #38 | `4ba76a8` |
| #37 | `verification/EVALUATION_PROTOCOL.md`: log score, floor, estimand, CR2 uncertainty, baselines B0/B1, selection rule, protocols P-F1 / P-F2, truncation sensitivity | #39 | `b26d5bd` |
| #36, #41 | `verification/FIXTURE_CATALOG.md`: FX-OBS, FX-TGT, FX-PRD, FX-RPL, FX-SUP, FX-EVL, FX-E2E, routing R-A..R-K | #40 | `1117d6d` |

Locks consumed unchanged:

- `design/SYSTEM_ARCHITECTURE.md` (#17), `design/OBSERVATION_RECONSTRUCTION.md` (#18, with A1), `design/TARGET_RECONSTRUCTION.md` (#19, with A1), `design/PREDICTION_CONTRACT.md` (#20), `design/REPLAY_BACKTEST.md` (#21, with A1), and the PASS gate `design/DESIGN_INTEGRATION.md` (#22), including its observation O3;
- `contexts/*.md`, in particular `contexts/EVALUATION_BACKTESTING.md` §§6, 7, 10–12;
- `decisions/2026-09-08-v2-project-direction.md`, `decisions/2026-09-08-v2-pit-event-scope.md`, `decisions/2026-09-09-v2-prediction-output-semantics.md`, and `decisions/2026-10-10-v2-race-day-archive-evidence-exception.md` (the PO exception).

Open clarifications considered: Issue #42 (R-A..R-H in the body, R-I..R-K in its comment). These match the routing table in `verification/FIXTURE_CATALOG.md` *Routing*.

## Initial integration result (2026-10-11, superseded)

Most of the verification baseline composes into one chain:

```text
#35 scope verdicts (S-RD = VERIFIED_BOUNDED_TIME under the PO exception; S-RG UNVERIFIED_ARCHIVE; S-22 UNSUPPORTED)
  -> #18/#19 reconstruction parameters (bounds, health windows, admission, tyre, terminal, c(E) method)
  -> #36 fixtures (reference #35 rules by name; expected values traced to #18–#21 handoffs)
  -> #37 protocols: supported_scope = S-RD only; P-F1 dev 2024 R10–2025 R24, final 2026 R1–R16
  -> #21 lock / ledger / accounting A0–A11 -> #37 scorer (log score on A9 ∪ A10 ∪ A11)
```

The following compose as written:

- scope;
- availability authority, and the conditions of the PO exception;
- the #20 outcome kinds and the #21 categories;
- coverage of the design handoffs.

The final-evaluation segment of the chain does not compose:

- **V1.** #37's primary final claim is a paired difference against a reference procedure. #21's lock, ledger and scorer contracts cannot produce it as a `PRIMARY_FINAL` result.
- **V2.** Several #36 regression fixtures run #19 retrospective reconstruction over P-F1 final-partition races. This conflicts with #21's final-partition access rule and with #37's own prior-exposure declaration.

Both problems fail closed: neither leaks information into a prediction. They do mean, however, that the primary claim as specified cannot be produced, and that a natural implementation order could irreversibly cost 2026 R1–R16 their `PRIMARY_FINAL` eligibility.

## Initial composition checks (2026-10-11, superseded)

### 1. Season allocation uses only supported scope — PASS (Minor V4 for P-F2)

- **P-F1** `supported_scope` is exactly the 55 S-RD races of `SUPPORT_MATRIX.md` *Support matrix (A)* and *Consequences for `supported_scope`*: 2024 R10–R24, 2025 R1–R24 and 2026 R1–R16. The development partition (39 races) and the final partition (16 races) are subsets of it, and every development race precedes every final race. This satisfies #21 *Protocol* constraint 1.
- The allocation follows the #21 constraint 5 default: the final partition is a supported season absent from thesis-era data (2026). No S-RG or S-22 race appears in any partition, and the target-only scope S-RD ∪ S-RG is never used for prediction.
- `ROLLING_RACE_BLOCK`, `LOW_POWER` and `PRIOR_EXPOSURE_DECLARED` match the #35 hand-off to #37 (*Consequences*, last bullets) and #21 *Development folds*. The development partition covers two seasons (part of 2024, and 2025), which is fewer than three.
- **P-F2.** The F2 inclusion rule (`EVALUATION_PROTOCOL.md` §7) is stricter than the #35 S-RD membership test ("`Last-Modified` on the race date or the next UTC day … later races when they pass the same check"). It adds HTTP 200 and a hash that is stable for at least 24 h. Its races are therefore S-RD by #35's definition. One gap remains in #35's per-race capability qualifier for `EntryLapContext`: see V4.

### 2. Fixtures reference #35 and #37 rules without redefining them — PASS (Minor V5)

- **#35 rules consumed exactly:**

  | #35 rule | Fixtures |
  | --- | --- |
  | Bounds [P − 5 s, P + 5 s] | Synthetic defaults; FX-OBS-01; FX-TGT-03a, -14 |
  | Cross-stream 10 s rule | FX-SUP-05: 989.9 admitted, 990.0 omitted, exactly at `P_fact + 5 < P_trigger − 5` |
  | Same-stream and same-payload rules | FX-SUP-06; FX-OBS-10, -11; FX-E2E-04 |
  | Pre-race 300 s margin | FX-SUP-09; FX-OBS-17, -18 |
  | Health rule (a) | FX-SUP-07: the extent is explicitly not asserted, because #35 does not define it |
  | Health rule (b) | FX-SUP-08: the ambiguous case (ii) is routed as R-F |
  | Health rule (c) | FX-SUP-10 |
  | `TotalLaps ≤ 0` | FX-SUP-11 |
  | Tyre positive rule | FX-TGT-08, -09 |
  | Tyre negative (penalty) rule | FX-TGT-10, -10a, -11 |
  | Terminal combined rule | FX-TGT-18, -19, -20, -20a; FX-SUP-13 |
  | Order-based `c(E)` | FX-TGT-27, -29; FX-SUP-12 |

  Where #35 is silent, the catalog marks the case PENDING-OWNER (R-A, R-B, R-C, R-F, R-K) rather than deciding it.
- **#37 rules consumed exactly:**

  | #37 rule | Fixtures |
  | --- | --- |
  | §1 log score by kind | FX-EVL-01 |
  | §1 infinite scores | FX-EVL-02 |
  | §1 floor and hazard round-trip | FX-EVL-03: the PMF mixture and `λ_j = p'_j / S_j`, consistent with the #20 `hazard/v1` example FX-PRD-06 |
  | Lock floor check | FX-EVL-04 |
  | §2 paired ΔS | FX-EVL-05 |
  | §3 CR2 with t(G−1) and the G < 10 rule | FX-EVL-06: the closed form for an intercept-only CR2 is correct |
  | B1 omission rule | FX-EVL-08 |
  | §6 selection steps 3–4 and budget | FX-EVL-09, -10, -11 |
  | F2 metadata-only inclusion | FX-EVL-12 |
  | §8.2 50 % condition | FX-EVL-13: the boundary is inclusive, as in "≤ 50 %" |
  | §8.5 scenarios and not-computable status | FX-EVL-14 |

- **One exception:** FX-EVL-07 fixes the wild-bootstrap variant ("unrestricted", "percentile"), which #37 §3 does not specify. See V5.

### 3. Single canonical owner per concept — PASS (V5 is the only slip)

| Concept | Owner | Consumers | Composition |
| --- | --- | --- | --- |
| Scope classes S-RD / S-RG / S-22, authority levels per endpoint | #35 (A), under #18 *Authority levels* and the PO exception | #37 `supported_scope`; #36 FX-SUP-01…04, FX-OBS-20, -21 | consistent |
| Error model, health windows, admission margins | #35 *Error model* | #36 FX-SUP-05…10; #37 B1 inputs ("RA-2 and the #35 10 s cross-stream margin") | consistent; #37 cites, does not restate |
| Tyre, terminal, `c(E)`, `TotalLaps` rules | #35 (C), (D) | #36 FX-TGT-*, FX-SUP-11…14; #37 §2 (truncation mechanism) | consistent |
| Scoring rule, floor, aggregates, uncertainty, selection, protocol values | #37 | #36 FX-EVL-* | consistent except V5 |
| Outcome kinds, mapping | #20 | #37 §1; #36 FX-PRD-* | consistent |
| Accounting A0–A11, cohort, lock, ledger labels, analysis class, qualifiers | #21 | #37 §§1, 2, 7, 8; #36 FX-RPL-* | consistent except V1 and V3 |

### 4. #20 and #21 terms used exactly in the protocol — PASS (Major V3)

- **Outcome kinds.** #37 §1 maps `REALIZED_REGION`, `REALIZED_REGION_SET` and `REALIZED_NO_EVENT` to A9, A10 and A11. This is identical to #20 *Realized-target mapping* and the #21 *Backtest categories*. A6 (`NOT_REALIZED`) and the run defects A0, A5, A7 and A8 are never scored, which matches #21 *Primary cohort*. Terminal no-event is scored through `q`, which matches `contexts/EVALUATION_BACKTESTING.md` §6 and #21 scorer rule 2.
- **Analysis class.** #37 §8.2 adds a further necessary condition for `PRIMARY`: a truncation share of at most 50 %. #21 scorer rule 2 lists necessary conditions ("requires all of"), and rule 6 delegates metrics and aggregation to verification. A stricter condition therefore composes. `ledger_role` is left untouched, as #21 rule 5 requires.
- **Qualifiers and ledger roles.** `LOW_POWER` and `PRIOR_EXPOSURE_DECLARED` are used in the #21 sense. `PRIMARY_FINAL` and `AD_HOC_OPENING` are named as #21 ledger outputs. The #37 §7 *Claims* use of `PRIMARY_FINAL`, however, is not producible: see V1.
- **Retrospective grouping keys.** #37 §2 labels the "event-trajectory-weighted mean" `SECONDARY`. #21 *Grouping metadata* restricts `event_trajectory_key` to dependence-aware clustering and `RETROSPECTIVE_DIAGNOSTIC` analyses. See V3.
- **Floor.** #20 *Invariants* leaves the probability floor to verification or experimentation, and #20 *Unknown routing* agrees. #37 §1 exercises that delegation inside the forecaster, so the #20 contract invariants are unchanged.

### 5. `supported_scope`, `UNVERIFIED_ARCHIVE` and the PO exception — PASS (Minor V6)

- **#18 *Authority levels*.** "No implementation may map `UNVERIFIED_ARCHIVE` to a verified class." This is honoured:
  - S-RG and the unprobed S-RD endpoints stay `UNVERIFIED_ARCHIVE`, and 2022 plus Bahrain and Hungary 2018 are `UNSUPPORTED` (#35 (A));
  - the fixtures enforce fail-closed behaviour (FX-OBS-20, FX-OBS-21, FX-SUP-04);
  - P-F1 and P-F2 contain only S-RD races.
- **PO exception conditions 1–4.**
  1. Residual assumptions are stated (#35 RA-1–RA-4).
  2. Conservative bounds come from a validated error model (#35 *Derivation*).
  3. Clock-unhealthy windows are excluded: #35 rules (a)–(c), with checkpoints falling into A1 through FX-E2E-08.
  4. Independent review is recorded (#35 *Review record*).

  The exception's limits are respected: it does not cover rewritten archives, 403 seasons, unevidenced endpoints or unhealthy windows.
- **Provenance condition.** The exception requires that "results built on this scope must carry the residual assumptions in their provenance, and reports must state that the authority rests on this exception". #35 *Consequences* and #37 §§7, 9 restate this, but no fixture asserts it. See V6.
- **Void condition.** The exception is void if a later capture contradicts it. #35 *Upgrade path* 4 and FX-SUP-03 cover hash or `Last-Modified` changes.

### 6. Design verification handoffs covered or routed — PASS

| Handoff | Catalog entries | Status |
| --- | --- | --- |
| #18 item 14 (attempt-record completeness) | FX-OBS-12…16 (session, entry, checkpoint, alias, zero-candidate, no-lap-evidence, truncated `L_max`, closure inspection) | covered |
| #18 item 15 (scheduled distance) | FX-OBS-17…19, -23, FX-SUP-11, FX-PRD-04, -21 (`STATIC_PRIOR` marked not applicable for S-RD per #35 (D); aborted-start revision; final-only value rejected) | covered |
| #19 items 14–15 (terminal relation; event inside `(T, B)`) | FX-TGT-15, -15a, -16 | covered |
| #19 item 23 (lap-completion support vs #18 counter) | FX-TGT-26 | covered (see V2 for its basis) |
| #19 item 24 (`EntryLapContext` exact, bounded, same instant, countback, gap) | FX-TGT-27, -28, -29, -29a | covered; the real countback session is deferred, with its reason given |
| #19 item 25 (initialization-run exhaustiveness) | FX-TGT-30 | covered |
| #20 items 1–10 and 6a | FX-PRD-01…20 | covered |
| #21 items 1–12 | FX-RPL-01…24 | covered; the unreachable reseed case is routed as R-E |
| Gate O3 (development-join lineage; replay/initialization observation-run agreement) | FX-RPL-25 (PENDING-OWNER, R-D), FX-RPL-26 (current #21 behaviour) | covered and routed |

### 7. Lock, selection rule and lock-before-final ordering against the #21 `EvaluationLock` and `FinalEvaluationLedger` — FAIL (V1, V2; O1)

These parts compose:

- **Selection rule.** #37 §6 uses only `VALID` development-fold evidence, which matches the #21 `selection_evidence_refs` constraint. It is pre-registered before the first fold is scored, so the lock's `procedure_id` comes from development evidence only.
- **B1 as the locked procedure.** Rule 4, "lock B1", gives a lock whose `procedure_id` is B1's `ProcedureSpec`, which #21 permits.
- **Lock floor check.** It is an added precondition for lock eligibility and does not alter the lock contract.
- **P-F1.** With `final_refit_cadence = NONE`, one `ModelArtifact` with cutoff 2026 R1 is fitted on development races only. It is a `DEVELOPMENT_FIT` run, so #21 development-join rule 2 needs no lock for it. `t(c) ≤ t(r)` holds for every final race.
- **P-F2.** It is a separate `BacktestProtocol` with its own `EvaluationLock`, which reuses P-F1's procedure, seeds and artifact. Its final partition is unopened, so #21 constraint 3 holds. Its commitment precedes every P-F1 final opening. All of this is expressible in #21.

These parts do not compose:

- **V1.** The primary claim needs reference-procedure snapshots and outcomes on the final partition. #21 admits no such run under the lock.
- **V2.** The #36 regression fixtures, and the #35 routing of truncation-rate measurement to implementation, touch final-partition target truth outside the joins.
- **O1.** The protocol identity changes after the initial commitment, and the lineage of that change should be recorded.

### 8. Leakage and final-evaluation isolation — PASS for the causal path; FAIL for final isolation (V2)

- **Causal path.** The causal path stays closed:
  - FX-E2E-06 and FX-E2E-10 prove that the prediction side is identical across five outcome futures, using a projection that does not depend on the snapshot (R-I covers digest equality);
  - FX-PRD-18 and FX-RPL-03 cover dependency closure;
  - B1 uses only canonical facts at `T` (#37 §4).
- **Final isolation (`contexts/EVALUATION_BACKTESTING.md` §§11–12; #21 *Ledger* rules).** This is affected by V2.

### 9. Routed clarifications R-A..R-K — PASS (none blocks implementation)

See *Routed clarifications* below.

## Initial findings (preserved; V1-V6 resolved at bounded re-check)

### Blocking

**V1: #37's primary final claim (paired ΔS against a reference procedure) cannot be produced under #21's lock, ledger and scorer contracts.**

- **What is wrong.**
  - `EVALUATION_PROTOCOL.md` §2 defines the primary skill as `ΔS = mean(S_locked − S_ref)` on the identical unit set. The reference is B1, or B0 when B1 is locked.
  - §7 *Claims* states: "The primary final claim is `ΔS` on P-F1, labelled `PRIMARY_FINAL` by the ledger."
  - §9 also requires final results for B1 and B0.
  - Computing these needs reference-procedure snapshots for 2026 R1–R16, joined to final-partition resolutions. `design/REPLAY_BACKTEST.md` admits no such run:
    - *ReplayRun* rule "Final evaluation": `model_schedule` must equal the lock's `final_model_schedule`. *BacktestRun* rule 2: every replay of a `FINAL_EVALUATION` backtest must carry the lock's schedule and seed policy. A reference replay therefore cannot enter the locked final backtest.
    - *Ledger* labels: any other evaluation of an opened race is `POST_HOC`. If a reference evaluation of race `r` were run **before** the locked evaluation, by any route (including a registered `AD_HOC_OPENING`), the locked evaluation of `r` would itself become `POST_HOC`. 2026 R1–R16 would then be permanently ineligible for `PRIMARY_FINAL`.
    - *Scorer plug-in boundary*: a `ScoreRun` reads **one** `BacktestRun`, and rule 5 makes a run that mixes labels report per-label results. A paired difference between a `PRIMARY_FINAL` run and a `POST_HOC` run has no defined ledger role.
- **Why Blocking.**
  - Two approved normative statements contradict each other: #37 §7 *Claims* and #21 *Final gating*, *Ledger* labels and *Scorer* rules 1 and 5.
  - The project's headline final claim cannot be implemented without silently changing one of them: either the claim's label, or the lock and backtest contract.
  - Neither slice states the ordering hazard (reference evaluated before locked evaluation).
  - The lock, backtest and score contracts are implementation targets, so building them before this is resolved would build the wrong contract.
- **Owner.** `design/REPLAY_BACKTEST.md` (#21), as a bounded additive amendment with its own independent scoped review. `verification/EVALUATION_PROTOCOL.md` (#37) makes a consequential edit.
- **Required change.** Make the final paired comparison expressible, so that the reference never constitutes a separate or earlier opening. For example:
  - the `EvaluationLock` pre-declares `reference_procedures[]`, each with its `procedure_id`, seeds and `final_model_schedule`, fixed under the same development-only rules;
  - their final replays are admitted into the same `FINAL_EVALUATION` backtest, under the same ledger openings;
  - a paired `ScoreRun` over that one backtest carries the race labels unchanged.

  #37 then names B1 and B0 as the lock's declared references, covering the case where B1 is locked.

  **Alternative acceptable resolution, owned by #37 alone:** restate the `PRIMARY_FINAL` claim as the locked procedure's own score. ΔS against the references then becomes a non-primary comparison, with explicitly declared ledger roles, and an explicit rule that reference evaluations run only after the locked evaluation of each race.

  Choosing between the two is a delegated design and verification choice.
- **No Product Owner decision.** The evaluation semantics (`contexts/EVALUATION_BACKTESTING.md` §§11–12) do not change.

### Major

**V2: #36 regression fixtures exercise #19 retrospective target reconstruction on P-F1 final-partition races before the lock.**

- **What is wrong.**
  - These fixtures are `REAL(all 55 S-RD keys)` or `REAL(S-RD)` regression guards. Each covers 2026 R1–R16, the P-F1 `final_partition`:

    | Fixture | What it builds and asserts |
    | --- | --- |
    | FX-TGT-02 | visits with `c(E)` |
    | FX-TGT-26 | `c(E)` counter equals the #18 counter |
    | FX-SUP-12 | `c(E)` method |
    | FX-TGT-20 | combined terminal rule against Jolpica non-finishers |
    | FX-TGT-11 | S-RD penalty test set |

  - The penalty test set is concentrated in the final partition. In `capabilities_raceday_scope_v2.json`, 7 of its 9 visits are in 2026 races: Australia, Miami, Canada, Monaco ×2 and Dutch ×2.
  - These fixtures build and read #19 retrospective artifacts for final races during implementation, which comes before any lock:
    - `EntryLapContext` exists only inside a resolution run (#19 *Entry lap context* rule 1);
    - also `TerminalBoundary` and the tyre-service classification.
  - This conflicts with `design/REPLAY_BACKTEST.md` *Ledger* rules: "Final-partition resolution artifacts are accessed only through the backtest and development joins. Any other read … must be registered as an `AD_HOC_OPENING` …; unregistered access is a protocol violation, and the affected races must be treated as opened."
  - It also conflicts with the P-F1 declaration in `EVALUATION_PROTOCOL.md` §7: "No model was fitted to those races, and no V2 resolution artifact was read."
  - The same exposure arises through `SUPPORT_MATRIX.md` *Routing* ("Cohort and truncation rates → Implementation (#21 accounting)") and *Consequences* ("The exact rate is measured through the #21 accounting during implementation"), if that measurement includes final races.
- **Why Major.**
  - Followed literally, the conflict either forces registered `AD_HOC_OPENING`s, which make every P-F1 final race `POST_HOC`, or it makes the P-F1 declaration inaccurate.
  - It fails closed rather than leaking into predictions.
  - It must be settled before implementation runs these fixtures.
- **Owner.** `verification/FIXTURE_CATALOG.md` (#36). Consequential edits go to #37 (§7 declaration) and to the #35 *Routing* row for cohort and truncation rates.
- **Required change.** Choose one:
  - (a) Restrict the REAL regression fixtures that reconstruct target truth to races outside every declared final partition (2024 R10–2025 R24). Re-derive their expected totals from the per-race evidence. Have #35 route truncation-rate measurement to development-partition races only.
  - (b) Specify that these fixtures run as source-level functions that create no #19 resolution-run artifacts and are not ledger openings, and extend the P-F1 `prior_exposure` declaration to name them explicitly.

  Either way, the #37 declaration must stay accurate.

**V3: The event-trajectory-weighted aggregate is classed `SECONDARY` although its weights depend on the outcome.**

- **What is wrong.** `EVALUATION_PROTOCOL.md` §2, *Secondary aggregates*, labels the "event-trajectory-weighted mean" `SECONDARY`. Its weights depend on `event_trajectory_key`, which is `(driver_race_key, eventual_event_key)` or `(driver_race_key, TERMINAL)`, so each unit's weight depends on which event it eventually resolves to.
- **The lock.** `design/REPLAY_BACKTEST.md` *Grouping metadata* says that `eventual_event_key` and `event_trajectory_key` "are retrospective. They may be used for dependence-aware clustering and for `RETROSPECTIVE_DIAGNOSTIC` analyses, never for primary inclusion". *Scorer* rule 3 reserves `SECONDARY` for outcome-free rules. `contexts/EVALUATION_BACKTESTING.md` §10 requires outcome-derived analyses to be labelled retrospective.
- **Why Major.** An outcome-dependent analysis carrying an outcome-free class label is exactly what the two-dimensional analysis class exists to prevent. The report would mislead. It does not affect the primary aggregate.
- **Owner.** `verification/EVALUATION_PROTOCOL.md` (#37).
- **Required change.** Relabel the event-trajectory-weighted mean `RETROSPECTIVE_DIAGNOSTIC`, or drop it. The driver-race-weighted mean, which uses a causal key, remains `SECONDARY`.

### Minor

**V4: The P-F2 inclusion rule cannot establish #35's per-race `EntryLapContext` support condition before the lock.**

- **What is wrong.** Three statements combine:
  - `SUPPORT_MATRIX.md` (C) supports the order-based `c(E)` method only "in races with no lap-count jumps or regressions". `design/REPLAY_BACKTEST.md` *Protocol* requires `supported_scope` to include `EntryLapContext` support. #21 *Primary cohort* says resulting A8 defects are removed only through scope, never per record.
  - `EVALUATION_PROTOCOL.md` §7 forbids parsing any F2 record content before the P-F2 lock, so the no-jump condition cannot be checked.
  - An F2 race with a jump before a confirmed stop produces A8 (FX-E2E-05), which makes P-F2 `DEFECTIVE` with no compliant remedy.
- **Why Minor.** It fails closed: no leakage occurs, and P-F2 is a descriptive-only confirmatory claim (G < 10). The S-RD census found 0 jumps. Still, the protocol does not state this consequence.
- **Owner.** #37, cross-referencing #35 (C).
- **Required change.** Choose one:
  - state explicitly that P-F2 accepts the risk of being `DEFECTIVE` from in-race lap-count anomalies, and how such a run is reported;
  - or pre-register an outcome-blind structural check and declare it as exposure under the existing §7 exposure rule.

**V5: FX-EVL-07 fixes a wild-bootstrap variant that #37 does not specify.**

- **What is wrong.** `FIXTURE_CATALOG.md` FX-EVL-07 asserts an "unrestricted" bootstrap with a "**percentile** interval". `EVALUATION_PROTOCOL.md` §3 says only "a wild cluster bootstrap (Webb six-point weights, B = 9,999) interval for ΔS".
- **Why Minor.** The catalog decides a parameter that #37 owns, contrary to its own rule ("the catalog never decides such a case itself"). The statistic is co-reported, not primary, and both of its asserted properties hold for any variant.
- **Owner.** #37 (preferred: state the variant), or #36 (mark the variant PENDING-OWNER).

**V6: No fixture asserts the provenance condition of the PO exception.**

- **What is wrong.** `decisions/2026-10-10-v2-race-day-archive-evidence-exception.md` *Consequences* requires that "results built on this scope must carry the residual assumptions in their provenance, and reports must state that the authority rests on this exception". #35 and #37 §§7, 9 restate this. No FX entry checks either of the following:
  - that an S-RD `AvailabilityAuthorityValidation`, and the observations derived from it, reference the decision and RA-1–RA-4;
  - that a `ScoreArtifact` report carries the evidence-exception reference.

  FX-SUP-14 covers the tyre support record only.
- **Why Minor.** The condition is stated normatively; only its acceptance test is missing.
- **Owner.** #36.
- **Required change.** Add one contract fixture for the validation and observation provenance, and one for the score-report fields that #37 §9 requires.

### Observations

**O1: The protocol identity changes after the initial commitment.**

- **The two late fields.**
  - P-F1's `resolution_run_ref` is "declared by reference before the lock" (§7).
  - P-F2's final partition "is resolved to a fixed list of races, recorded in P-F2 before its lock", while P-F2's rule and digest are committed before any P-F1 final opening.
- **Consequence.** Under #21 *Protocol* constraint 2, filling either field creates a new `protocol_id`. Development runs, and the P-F2 pre-commitment, will then reference an earlier digest than the locked one.
- **Why no change is required.** Nothing contradicts: the later content is deterministic (a declared run, or a metadata-only rule), and no final race is opened in between.
- **Suggested handling.** Implementation records the lineage from the committed digest to the locked `protocol_id`. The lock check verifies that the later fields are the deterministic resolution of the committed rule.

## Routed clarifications

None of R-A..R-K blocks implementation. Each has an approved fail-closed default, or affects only a diagnostic or wording:

| Ref | Owner | Default implementation follows until resolved | Blocking? | Condition |
| --- | --- | --- | --- | --- |
| R-A | #35 | The current pre-race 300 s rule: no in-race admission of a late pre-race revision (FX-OBS-18). Staleness affects grid resolution only (#20 *Coverage proof*). | No | Any relaxation must be checked against the PO exception |
| R-B | #35 / #19 | #19 *Visit state-machine* rules 3–4: a duplicate is ignored only when equivalence is demonstrated, otherwise it is a segmentation anomaly | No | — |
| R-C | #35 / #19 | #19 *Ambiguity and conservative handling*: no convenience choice, so a conflict gives `INDETERMINATE_TYRE_SERVICE` (none observed, 0/10) | No | — |
| R-D | #21 | Mismatch logged (FX-RPL-25). Replay-side mismatch already fails closed (FX-RPL-26) | No | Optional #21 wording |
| R-E | #21 | #21 refuses a seed mismatch at replay | No | Wording only |
| R-F | #35 | The stricter reading, which marks the interval unhealthy unless integrity is shown. PO exception condition 3 requires excluding windows "where clock integrity cannot be shown" | No | The lenient reading must not be implemented before #35 decides |
| R-G | #19 | §8.5 diagnostic reported as "not computable" | No | — |
| R-H | #19 / #35 | Informational | No | — |
| R-I | #20 / implementation | Digest equality asserted over the Π-projected request | No | — |
| R-J | #19 | Not asserted. #19 *Eligibility states*: missing or ambiguous causal state is `INDETERMINATE`, never a convenient value | No | Resolve before the P-F1 pre-registration note (§6), because the answer changes the A2/A3 versus unit composition of the candidate population |
| R-K | #35 | #19 *Terminal no-event*: no-event requires a defensible `B`, otherwise `TRUNCATED_INDETERMINATE` | No | Resolve before the P-F1 pre-registration note if the case occurs in S-RD |

## Unknown routing

| Question | Classification | Owner / next phase | Status |
| --- | --- | --- | --- |
| Does the verification baseline compose with the designs? | Current-scope integration decision | #43 | **PASS** at bounded re-check; V1-V6 resolved |
| Final paired comparison under lock and ledger | Cross-slice dependency | #21 amendment (or #37 alone; see V1) | Resolved by #21 A2 / #37, PR #45 |
| Final-partition exposure through REAL fixtures and implementation truncation-rate measurement | Cross-slice dependency | #36; consequential #37, #35 | Resolved by #36 final-isolation convention / #37 declaration / #35 routing, PR #45 |
| Analysis class of the event-trajectory-weighted mean | Cross-slice consistency | #37 | Resolved by #37 section 2, PR #45 |
| P-F2 per-race `EntryLapContext` support before the lock | Cross-slice consistency | #37 (with #35 (C)) | Resolved by #37 F2 structural-risk policy, PR #45 |
| Wild-bootstrap variant | Ownership | #37 or #36 | Resolved by #37 section 3, PR #45 |
| PO-exception provenance fixture | Verification coverage | #36 | Resolved by FX-SUP-15 / FX-EVL-15, PR #45 |
| Protocol-id lineage after late fields | Later-phase decision | Implementation | Requirement specified in #37 Protocol lineage and FX-RPL-31; implementation deferred |
| R-A..R-K | Cross-slice clarifications | As listed above | Open; non-blocking |
| Candidate procedures, scorer code, schemas, storage, access control for the joins | Later-phase decision | Implementation / experimentation | Deferred |

There are no Product Owner-reserved decisions in this gate.

## Acceptance criteria (Issue #43)

- [x] The cross-artifact composition checks are recorded with exact references (checks 1–9).
- [x] The initial verdict **CHANGES REQUIRED** and superseding bounded re-check **PASS** are recorded. V1-V6 are closed with exact evidence; O1 and R-A..R-K remain routed.
- [x] One full integration review and exactly one bounded re-check after the provider fixes are complete, per `governance/REVIEW_POLICY.md`. No fresh slice review was performed.
- [x] R-A..R-K are confirmed non-blocking (*Routed clarifications*).

## Initial gate outcome (2026-10-11, superseded)

**CHANGES REQUIRED** (initial review, 2026-10-11, `main` at `1117d6d`).

A bounded reconciliation is required before implementation is unblocked:

1. **#21 amendment (V1).** Additive: make the final paired comparison against declared reference procedures expressible under the lock and ledger. This needs an independent scoped review of the amendment only. The consequential #37 edit names B1 and B0 as the lock's references. Alternatively, #37 alone restates the claim as described in V1.
2. **#36 rework (V2, V6).** Restrict the REAL target-truth regression fixtures to non-final races, or redefine them as non-resolution source-level checks (V2). Add the PO-exception provenance fixtures (V6). Optionally settle V5. The consequential edits are #37's §7 declaration and the #35 *Routing* row for truncation rates.
3. **#37 rework (V3, V4, V5).** Relabel the event-trajectory-weighted mean (V3). State the P-F2 consequence for in-race lap anomalies (V4). Specify the bootstrap variant (V5).
4. **Bounded #43 re-check.** After items 1–3 merge, verify V1–V6 and any regressions they cause. This is not a fresh review of the slices.

None of these items reopens an approved semantic lock or needs a Product Owner decision.

## Review record

- Reviewer: independent integration agent, Issue #43. It did not author any of the reviewed verification artifacts or designs.
- Date: 2026-10-11
- Reviewed state: `main` at `1117d6d`, which includes the merges of PR #38 (`4ba76a8`), PR #39 (`b26d5bd`) and PR #40 (`1117d6d`).
- Scope: cross-artifact composition only, per `governance/REVIEW_POLICY.md` *Integration review* and the Issue #43 scope. No slice was re-reviewed internally. The evidence was consulted only to confirm the scope of V2 (`verification/evidence/capabilities_raceday_scope_v2.json`, penalty test set by race).
- Outcome: **CHANGES REQUIRED**.
  - Blocking: V1.
  - Major: V2, V3.
  - Minor: V4, V5, V6.
  - Observation: O1.
- Routed clarifications R-A..R-K: confirmed non-blocking.
- Product Owner decision: none required.


### Bounded re-check (2026-10-12)

- Reviewer: independent integration agent `/root/integration_recheck`. This agent authored none of the reviewed designs, verification slices or PR #45 amendments.
- Reviewed state: `main` at exact SHA `aa316a7bcd16d3c53d54a55a1698d2405c51f979`, containing the initial gate record in PR #44 (`ce1652d`) and reconciliation PR #45 (`aa316a7`). The substantive delta is `git diff ce1652d..aa316a7`.
- Provider approval evidence: PR #45, passing independent scoped review `5489060100`, reviewer `/root/review_reconciliation`, substantive head `f44c37b7190dc118b65a80c16b10bb85024cc0e3`; two Minor wording clarifications applied without another cycle, as that reviewer permitted.
- Scope: prior V1-V6, regressions introduced by their fixes, and Issue #43 acceptance only. The approved designs, #22 PASS, Wave 1 contracts and durable Product Owner decisions were consumed as locks. No fresh internal slice review, production implementation, target-resolution read or model experiment was performed. Only already-committed support evidence was read to check revised fixture totals.

| Prior item | Bounded resolution evidence | Result |
| --- | --- | --- |
| V1: final paired comparison | #21 A2: *Protocol*, *ReplayRun*, *Backtest join* rules 1-2, *Reference registration*, *Comparison opening*, *Reproduction rule*, scorer rule 7; #37 sections 2 and 7; FX-RPL-27..30 | Resolved. B1/B0 are predeclared and frozen with the selected procedure, complete slot coverage is checked before opening, one BacktestRun opens each race once, paired scores inherit its label. If B1 is selected its slot aliases SELECTED; the primary comparison is B1 versus B0. Full identical cohorts and a VALID comparison are required for PRIMARY; differing cohorts permit only a visible SECONDARY intersection. |
| V2: pre-lock final exposure | #36 *Final isolation* convention, FX-TGT-02/-11/-20/-26, FX-SUP-12, FX-RPL-32; #35 *Consequences* and *Routing*; #37 P-F1 reserved resolution identity and prior-exposure declaration | Resolved. REAL target reconstruction and exploratory cohort/truncation measurement are development-only. Final resolutions are first consumed in the locked ledger-gated join. Recomputed frozen evidence for the 39 development races gives 1334/1334 stop/lap matches, two penalty visits, 84/84 combined-terminal matches, zero jumps and zero regressions, matching the catalog. Existing raw-source inspection remains explicitly declared. |
| V3: outcome-derived weighting | #37 section 2; #21 *Grouping metadata* and scorer rule 3 | Resolved. Event-trajectory weighting is RETROSPECTIVE_DIAGNOSTIC; driver-race weighting remains SECONDARY. Primary unit weighting is unchanged. |
| V4: F2 structural support risk | #37 section 7 *F2 structural-risk policy*; #35 (C) EntryLapContext support; FX-EVL-16 | Resolved. Metadata-only inclusion does not upgrade lap support. A post-lock anomaly makes the affected run DEFECTIVE, with no primary/confirmatory claim, all declared races and defects reported, and no selective race removal or replacement claim. |
| V5: bootstrap ownership | #37 section 3; FX-EVL-07 | Resolved. The protocol owns the unrestricted Webb six-point, 9999-replicate percentile variant, residual construction, quantiles and predeclared seed; the fixture consumes it. CR2 remains the primary interval. |
| V6: exception provenance coverage | FX-SUP-15; FX-EVL-15; #35 residual assumptions; #37 sections 7 and 9; 2026-10-10 decision *Consequences* | Resolved. Acceptance covers the exception and RA-1..RA-4 through authority validation, derived observations and score reports, and rejects missing lineage/report disclosures. |
| O1: commitment-to-lock identity | #37 section 7 *Protocol lineage*, P-F1 reserved identity and P-F2 fixed-list rule; FX-RPL-31 | Explicitly routed to implementation. Retain committed and locked digests, verify only deterministic predeclared fields were resolved, and refuse intervening final openings or changed choices. |

**Regression check.** The added comparison slots refine #21's delegated orchestration without changing #18 observation ownership, #19 causal initialization versus retrospective resolution, #20 forecast dependency closure or mapping, checkpoint/episode/event meaning, category precedence or ledger labels. Every slot shares observation, initialization and resolution selection. #21 *Record-level accounting table* makes accounting per procedure slot and explicitly states that reference rows are not additional temporal checkpoints: candidate/checkpoint totals are therefore compared per slot, rather than summed across SELECTED/B1/B0. Undeclared/mutated/incomplete slots fail before opening, reproduction checks every slot, and any A0/A5/A7/A8 makes the whole comparison DEFECTIVE. The final holdout remains outcome-isolated during development. No cross-slice regression was found in the amended composition.

**R-A..R-K confirmation.** All eleven stay with the owners and conservative defaults in *Routed clarifications*. In particular R-F excludes clock windows whose integrity cannot be shown; R-G remains not computable; R-I asserts projected digest equality; R-J uses INDETERMINATE for ambiguous causal eligibility and must resolve before P-F1 pre-registration; R-K cannot assert no-event without a defensible terminal boundary and must resolve before pre-registration if the case occurs in S-RD. The amendments neither silently settle nor relax these handoffs. They do not block starting bounded implementation.

**Issue #43 acceptance.** Exact composition references and finding closures are recorded above; no unresolved required gate finding remains; the single allowed bounded re-check is complete. No new Product Owner-reserved decision or semantic change is introduced.

**Outcome: PASS.** The technical verification integration gate passes for the reviewed SHA. Implementation is technically unblocked, subject to the Product Owner's current request to approve the concise visual overview before implementation begins. Remaining work is that overview approval, then bounded implementation and experimentation under the approved contracts and routed conditions.

- GitHub review / PR record: PR #46, review `5489127342`, recorded through the connected account from the independent reviewer outcome. This entry is the independent passing outcome for the exact reviewed main state above.
