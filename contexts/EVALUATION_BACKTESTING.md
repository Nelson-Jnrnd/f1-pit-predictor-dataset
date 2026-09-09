# Evaluation / Historical Backtesting Semantics

## Status

Approved — full independent scoped review passed on PR #13 with no Blocking, Major, or Minor findings.

## Abstraction level

Wave 1 — semantic specification.

## Outcome

Define what constitutes a valid V2 historical replay/backtest and how immutable point-in-time predictions are compared with canonical next-pit target outcomes without future-information leakage, outcome conflation, or premature commitment to metrics, split algorithms, statistical estimators, or implementation.

## Scope

### In scope

- semantic meaning of a valid historical replay and backtest;
- the canonical evaluation unit and the relationship between prediction instances, target episodes, and eventual pit events;
- which prediction instances are eligible to be evaluated and which realized target states can support scoring;
- leakage-safe evaluation guarantees from observation reconstruction through prediction generation and retrospective comparison;
- semantic treatment of observed-event, terminal no-event/domain-censoring, truncated/indeterminate, and target-ineligible cases;
- interpretation of multiple successive predictions within one race without target leakage or accidental event/episode conflation;
- separation between model-development/model-selection evidence and final backtest evidence sufficient to prevent optimistic final claims;
- requirements that later verification/design must satisfy for leakage, temporal ordering, reproducibility, and semantic compatibility.

### Explicitly out of scope

- redefining prediction-point timing, point-in-time information availability, or observation reconstruction semantics;
- redefining qualifying pit events, event occurrence, target eligibility, target lifecycle, terminal boundaries, censoring, or truncation;
- redefining prediction probability, complete remaining-race coverage, terminal no-event probability, pit-window meaning, or replay immutability;
- choosing headline metrics, scoring rules, loss functions, confidence intervals, hypothesis tests, calibration methods, or statistical estimators;
- choosing train/validation/test seasons, folds, rolling-window algorithms, exact cutoffs, sampling ratios, weighting formulas, or aggregation formulas;
- choosing model families, features, target encodings, schemas, APIs, storage, packages, architecture, UI, or implementation;
- live production monitoring or live inference infrastructure.

## Upstream inputs / semantic locks

- `decisions/2026-09-08-v2-project-direction.md` — historical replay/backtesting is the initial V2 consumption/evaluation ambition; predictions are descriptive next-pit behavior estimates and must remain point-in-time legitimate.
- `product/PROJECT_VISION.md` — V2 should support reproducible leakage-aware historical replay/backtesting and compare a point-in-time pit prediction with what subsequently happened.
- `product/RESEARCH_PROBLEM.md` — the primary problem is next-pit timing from legitimately available information; point-in-time correctness applies to evaluation as well as prediction.
- `product/SYSTEM_SCOPE.md` — historical replay/backtesting is core; future information must not influence a prediction that purports to have been made earlier.
- `contexts/CONTEXT_MAP.md` — this slice owns valid replay/backtest meaning, evaluation units/comparison semantics, leakage-safe guarantees, and judgment of approved outputs against approved target outcomes.
- `contexts/RACE_OBSERVATION_STATE.md` — every prediction is tied to one canonical driver-specific observation and prediction instant `T`; the observation is an immutable as-of knowledge state governed by availability time, not retrospective final truth.
- `contexts/PIT_EVENT_TARGET.md` — each target-eligible observation creates one distinct prediction-target pair and target episode; the target is the first qualifying tyre-service pit entry strictly after that observation's `T`; terminal no-event/domain censoring is a known race-bounded outcome, while truncated/indeterminate follow-up is unresolved evidence rather than an ordinary negative.
- `contexts/PREDICTION_OUTPUT_REPLAY.md` — each eligible observation receives a complete remaining-target-scope probability distribution over mutually exclusive next-pit timing regions plus explicit terminal no-event probability; prediction snapshots are immutable; successive observations create distinct target episodes even when they resolve to the same eventual pit event.
- `decisions/2026-09-09-v2-prediction-output-semantics.md` — the canonical prediction is the complete remaining-race probability distribution with explicit terminal no-event probability; a displayed pit window is only a summary of that distribution.
- `decisions/2026-09-08-v2-pit-event-scope.md` — qualifying target events require tyre service and occur semantically at pit-lane entry.
- Issue #4 / `legacy/THESIS_EVIDENCE.md`, when useful — historical baseline evidence only; legacy validation behavior is not normative V2 evaluation semantics.

## Canonical ownership

This slice owns:

- the semantic conditions under which a historical replay/backtest is valid for V2;
- the evaluation unit and mapping from one immutable prediction snapshot to one canonical target outcome;
- evaluation interpretation of target eligibility, observed events, terminal no-event/domain censoring, and truncated/indeterminate follow-up;
- how repeated predictions within a race enter evaluation without being mistaken for one shared target episode or for independent races;
- the minimum separation between development/model selection and final evaluation required for defensible backtest claims;
- semantic leakage, chronology, reproducibility, and compatibility obligations placed on later verification/design.

This slice does not own:

- observation, target, event, censoring, or prediction-output meaning;
- exact statistical scoring or estimation;
- exact data partitioning, training cadence, retraining policy, weighting, or aggregation algorithms;
- technical dataset/model representations or implementation.

## Semantics / findings

### 1. Historical replay and backtest are related but distinct

A **historical replay** is a chronological reconstruction of canonical race observations and their immutable prediction snapshots as the race progresses. At each replayed prediction instant `T`, the prediction must be interpreted only from the information legitimately available by that instant under `contexts/RACE_OBSERVATION_STATE.md`.

A **historical backtest** is the retrospective evaluation of such prediction snapshots against their canonical target outcomes under a declared evaluation protocol. Retrospective target truth may be used to judge a prediction after the fact, but it must never be inserted into the observation or prediction that existed at `T`.

A replay can exist without producing an aggregate performance claim. A backtest adds comparison, cohort definition, and aggregation/analysis rules around replayed prediction instances. Exact metrics and aggregation formulas remain later-phase choices.

### 2. Canonical evaluation unit: one prediction-target pair

The atomic V2 evaluation unit is one **evaluated prediction instance** corresponding to:

- one target-eligible canonical observation;
- one immutable prediction snapshot issued for that observation at prediction instant `T`; and
- that observation's own canonical target episode and retrospectively resolved target status.

The atomic unit is therefore not "one race", "one driver race", "one pit event", "one lap", or "one eventual stop". Those may later be grouping or aggregation levels, but they do not replace the per-observation prediction-target pair.

Two observations for the same driver in the same race remain two distinct evaluation units even if their target episodes later resolve to the same eventual qualifying pit event.

### 3. Conditions for a prediction instance to enter canonical evaluation

A prediction instance is semantically eligible for canonical V2 evaluation only when all of the following hold:

1. its observation is valid under `contexts/RACE_OBSERVATION_STATE.md` and unambiguously identifies the race session, driver entry, checkpoint, and prediction instant;
2. that observation is target-eligible under `contexts/PIT_EVENT_TARGET.md`;
3. the prediction is the immutable output actually associated with that observation under the approved prediction-output semantics;
4. the prediction was generated without using information outside the legitimate boundary for that observation or outside the declared evaluation training/development boundary;
5. retrospective evidence can classify the target follow-up as an observed qualifying event, terminal no-event/domain censoring, or explicitly truncated/indeterminate.

Only observed-event and known terminal no-event outcomes provide complete canonical target truth for ordinary scoring against the approved complete-distribution output. Truncated/indeterminate cases remain part of backtest accounting but are not silently promoted into complete outcomes.

An observation that is target-ineligible does not have a canonical next-pit target episode and therefore is not an ordinary V2 next-pit evaluation unit. Technical systems may record such observations for other purposes, but evaluation may not manufacture an ordinary negative target for them.

### 4. Point-in-time legitimacy must hold end to end

A backtest is not leakage-safe merely because final target columns are withheld from a feature table.

For each evaluated prediction at `T`, the entire prediction-producing path must respect the legitimate-information boundary. This includes any race-state reconstruction, deterministic derivation, learned transformation, model input, and intra-race update used to produce the prediction snapshot.

Retrospective records may be used to reconstruct what was actually knowable at `T`, but later-confirmed values, final corrected race facts, future normalization, future event identity, or later outcomes may not be backfilled into the earlier prediction state merely because they are available in the historical dataset today.

The target outcome is intentionally retrospective truth. Using it to score the already-fixed prediction is evaluation; using it to construct, alter, select, or retroactively improve that prediction is leakage.

### 5. Comparison semantics for an observed next-pit event

If a target episode closes on an observed qualifying pit event, evaluation compares the immutable complete-distribution prediction from `T` with the realized timing of that canonical first qualifying tyre-service pit entry after `T`.

Later technical design may choose the timing-region representation and a proper or otherwise approved scoring rule, but the semantic comparison must preserve these facts:

- the realized event is exactly the event owned by `contexts/PIT_EVENT_TARGET.md`;
- its pit-lane-entry occurrence, not a convenient lap label or later service timestamp, determines the realized target timing;
- the full approved probability output remains the prediction being judged;
- a consumer-facing pit-window summary may support secondary descriptive analysis but must not silently replace the complete canonical distribution or imply zero probability outside the displayed window.

This slice does not require an exact numeric metric or prescribe how a continuous/discrete timing representation is scored.

### 6. Comparison semantics for terminal no-event/domain censoring

If a target episode reaches its canonical terminal boundary without a later qualifying event, the realized target state is the known race-bounded **terminal no-event/domain-censoring outcome** defined by `contexts/PIT_EVENT_TARGET.md`.

Because `contexts/PREDICTION_OUTPUT_REPLAY.md` assigns explicit probability to terminal no-event, ordinary evaluation of a complete target outcome must compare this realized terminal outcome with that explicit prediction probability rather than:

- converting it into an event on an artificial final lap;
- treating it as an ordinary timing-region negative repeated across every future region;
- pretending that an unobserved event occurred after race end; or
- discarding the terminal no-event component of the prediction.

Exact scoring mathematics remain a later verification/modeling decision.

### 7. Truncation/indeterminate follow-up is not a normal scored outcome

A truncated/indeterminate target episode lacks enough evidence to establish either the next qualifying event or a defensible terminal no-event boundary.

Such a case must not be silently encoded or interpreted as:

- an observed pit event;
- terminal no-event;
- a generic negative; or
- evidence that the prediction was correct or incorrect in the same sense as a completely resolved target.

A valid backtest must account for truncated/indeterminate cases explicitly. Later verification/statistical design may define exclusion, partial-information methods, or sensitivity analysis, but any method must preserve the distinction between missing follow-up evidence and known target truth.

Backtest reporting must make the existence and handling of these cases inspectable so that performance cannot be improved silently by outcome-dependent omission.

### 8. Successive predictions within one race are distinct forecasts

Canonical prediction points can create many eligible predictions for one driver race. These are legitimate repeated forecasts, not accidental duplicate rows, provided each prediction is tied to its own observation and target episode.

If no qualifying pit event occurs between `T1` and `T2`, distinct target episodes opened at those observations may resolve to the same eventual next qualifying event. Evaluation may judge both immutable forecasts against that same eventual event because each forecast asked the next-pit question from a different legitimate information state.

If a qualifying pit event occurs between `T1` and `T2`, the later prediction's target is the next distinct qualifying event after `T2`, not the event already targeted from `T1`.

A backtest must therefore preserve both **prediction-episode identity** and **event identity**. It must not deduplicate predictions merely because they share an eventual event, and it must not conflate them into one target episode.

### 9. Repeated within-race forecasts must not be mistaken for independent races

Although each eligible prediction-target pair is an atomic evaluation unit, many such units can be strongly related because they come from the same driver, race, and evolving event trajectory.
A valid backtest claim must state the evaluation population and grouping/aggregation level clearly enough that repeated checkpoints cannot silently dominate the interpretation. In particular:

- reporting every checkpoint is semantically valid when the claim concerns per-checkpoint forecast quality;
- race-, driver-, event-, or phase-level summaries may also be useful later;
- no semantic default assumes that repeated observations are statistically independent;
- exact weighting, clustering, dependence-aware uncertainty, and aggregation formulas are deferred to later verification/statistical design.

This requirement prevents repeated forecasts of one eventual event from being confused with an equal number of independent races while preserving their legitimate value as sequential forecasts.

### 10. Primary backtest instance selection must not peek at realized target timing

The primary evaluation cohort must be determined by declared rules that do not inspect the realized event timing or prediction error to decide whether an otherwise valid prediction instance is included.

Canonical target eligibility and explicit truncation/resolvability rules are permitted because they define whether the target question exists and whether complete outcome truth is available. Beyond those semantic gates, selectively retaining predictions because they were near an eventual stop, easy to predict, correct, or favorable to a chosen metric would create outcome-conditioned evaluation.

Retrospective diagnostic slices may intentionally group results by eventual distance-to-pit, race phase, observed-event/no-event status, or other outcome-derived facts when analytically useful, but they must be labeled as retrospective analyses and must not be substituted silently for the primary backtest population.

### 11. Development/model selection and final backtest evidence are different roles

Data used to choose among models, features, transformations, hyperparameters, calibration procedures, prediction representations permitted by the approved semantics, or other prediction-producing choices is **development/model-selection evidence**.

A **final backtest** is intended to provide evidence about a prediction-producing procedure after those choices are fixed for the relevant evaluation boundary. Outcomes in the final evaluation population must not be used to choose or tune the procedure whose final performance is then claimed on those same outcomes.

If final-evaluation results cause a substantive prediction-producing choice to change, those results have become development evidence. A later final claim must be based on evaluation data/outcomes not used for that revised choice.

This semantic separation does not prescribe a particular train/validation/test split, fold count, season cutoff, nested-validation algorithm, or rolling-origin procedure. Later verification/design chooses the mechanism while preserving the separation.

### 12. Historical backtest claims require temporal ordering, not only row separation

For a backtest presented as historical replay/deployment-like evidence, the prediction-producing procedure at an evaluated historical point must respect a declared temporal training/development boundary. It may not rely on race outcomes or learned artifacts that would only exist after the applicable training cutoff for that prediction protocol.

The exact chronology policy is deferred: later work may choose fixed historical cutoffs, forward-chaining, rolling retraining, season-based holdouts, or another defensible temporal design. Whatever mechanism is chosen must make clear what historical data was permitted to influence each evaluated prediction and must prevent future evaluation races/outcomes from leaking into earlier replayed predictions through training, preprocessing, calibration, or selection.

Non-temporal resampling may still be useful as development evidence when explicitly labeled and when it answers an appropriate development question, but it must not be presented as the final leakage-safe historical replay/backtest if it violates the historical information boundary being claimed.

### 13. A valid backtest has a declared evaluation protocol

At semantic level, a backtest must declare enough about its protocol to make the claim interpretable and reproducible, including:

- which races/drivers/observations constitute the candidate evaluation population;
- the canonical prediction-instance inclusion rule;
- how target-ineligible and truncated/indeterminate cases are accounted for;
- the temporal/development boundary under which prediction-producing choices and learned artifacts were fixed;
- what grouping or aggregation level a reported result represents;
- which approved prediction-output and target semantics/version apply.

Exact file formats, configuration schemas, metadata fields, metrics, formulas, and implementation are later-phase decisions.

### 14. Reproducibility means semantic replayability, not a frozen software stack

A defensible V2 backtest must be reproducible enough that an independent later run under the same declared semantic/data/model policy can reconstruct the same evaluated prediction instances, their point-in-time observation boundaries, their target-resolution states, and the prediction snapshots being judged.

When randomness or learned artifacts affect the produced predictions, later implementation/verification must record or control enough provenance to reproduce or equivalently audit the evaluated outputs. This requirement does not freeze a library, seed field, artifact store, schema, or execution framework at this semantic phase.

Historical predictions must remain immutable: rerunning a model later with revised data or code does not retroactively replace the prediction snapshot that a specific backtest claims to evaluate. A new run is a new prediction/evaluation artifact unless it demonstrably reproduces the original snapshot under the declared policy.

### 15. Later verification requirements

The verification baseline must demonstrate, with suitable tests/fixtures/audits chosen later, at least the following properties:

1. **Observation legitimacy:** every evaluated prediction maps to the canonical observation/checkpoint and contains no information first available after its prediction instant.
2. **Temporal reconstruction:** delayed, corrected, later-confirmed, and ambiguous-order information is handled consistently with `contexts/RACE_OBSERVATION_STATE.md` rather than retrospective final truth.
3. **Target compatibility:** each evaluated prediction maps to exactly one target episode owned by `contexts/PIT_EVENT_TARGET.md`, and observed pit events use the approved tyre-service qualification and pit-entry occurrence anchor.
4. **Eligibility/censoring integrity:** target-ineligible observations are not converted into ordinary negatives; terminal no-event outcomes remain distinct from truncation/indeterminate follow-up.
5. **Output compatibility:** evaluated predictions preserve the complete remaining-target-scope distribution and explicit terminal no-event probability required by `contexts/PREDICTION_OUTPUT_REPLAY.md`; any displayed pit-window summary is not silently substituted for the canonical output.
6. **Episode/event identity:** successive predictions remain distinct episodes even when they resolve to the same eventual event; an intervening qualifying pit event advances the later target to the next distinct event.
7. **Prediction immutability:** later race knowledge, corrections, target truth, or reruns do not overwrite the historical prediction snapshot being evaluated.
8. **Training/development leakage control:** learned transformations, models, calibration, selection, and other prediction-producing choices respect the declared training/development and temporal boundaries for final evaluation.
9. **Final-evaluation isolation:** final-backtest outcomes are not reused to select the procedure whose final performance is claimed on those same outcomes.
10. **Selection transparency:** primary evaluation inclusion/exclusion is reproducible and not conditioned on favorable realized timing/error beyond canonical eligibility and resolvability rules; retrospective outcome-stratified diagnostics are clearly identified.
11. **Repeated-observation accounting:** evaluation can identify grouping by race/driver/event/episode so repeated checkpoints are not accidentally interpreted as independent races.
12. **Reproducibility/provenance:** the evaluated population, semantic versions, target resolutions, prediction snapshots, and applicable model/data policy can be reconstructed or audited consistently.

These are verification obligations, not prescriptions for exact test frameworks, fixtures, metrics, schemas, or algorithms.

### 16. What this semantic contract intentionally does not decide

This slice does not choose what numeric score should be optimized or reported. It also does not decide how many seasons belong in training or final evaluation, how often a model retrains, how observations are weighted, how dependence is estimated, whether confidence intervals are bootstrap-based, what calibration diagnostic is used, or which statistical model represents the approved probability distribution.

Those choices can materially affect empirical conclusions, so later verification/experimentation must declare and justify them. They may refine measurement of the approved semantics but may not change the semantics themselves.

## Unknown routing

| Question | Classification | Owner / next artifact | Status |
| --- | --- | --- | --- |
| What constitutes one canonical evaluated prediction instance? | Current-scope decision | Evaluation / Backtesting | **Resolved here — one target-eligible observation's immutable prediction + its own target episode** |
| How are observed-event, terminal no-event, truncated, and target-ineligible cases interpreted in evaluation? | Current-scope decision | Evaluation / Backtesting consuming Target + Output contracts | **Resolved here at semantic level** |
| How are multiple within-race predictions interpreted when they share an eventual event? | Current-scope decision | Evaluation / Backtesting consuming Prediction Output / Replay | **Resolved here — distinct episodes/forecasts; shared event identity does not collapse them** |
| What minimum development-vs-final-evaluation separation is required? | Current-scope decision | Evaluation / Backtesting | **Resolved here — final outcomes cannot choose the procedure evaluated on those same outcomes** |
| What exact headline metrics/scoring rules evaluate the complete distribution and terminal no-event outcome? | Later-phase decision | Verification / experimentation / model evaluation | Deferred |
| What exact train/validation/test seasons, rolling-origin design, folds, or temporal cutoffs are used? | Later-phase decision | Verification / experimentation | Deferred; must preserve declared temporal and final-evaluation isolation guarantees |
| How are repeated checkpoints weighted/aggregated and how is within-race dependence handled statistically? | Later-phase decision | Verification / statistical design | Deferred; no independence assumption is made here |
| How are truncated outcomes handled statistically beyond the semantic prohibition on treating them as complete outcomes? | Later-phase decision | Verification / statistical design | Deferred |
| What exact reconstruction rules/provider fields prove availability time, pit entry, tyre service, terminal state, or ambiguous ordering? | Later-phase decision | Data/design + verification | Deferred; must satisfy approved upstream semantics |
| What schemas, IDs, metadata, model registry/provenance representation, packages, APIs, storage, or runtime implement the protocol? | Later-phase decision | Architecture / implementation | Deferred |
| How would future live monitoring or online evaluation differ from historical backtesting? | Later-phase decision | Future product/semantic extension | Deferred; outside current V2 core |

There are no unresolved Current-scope decisions in this slice and no Product Owner-reserved change is required. The artifact preserves the approved historical-replay ambition, target meaning, prediction meaning, and information philosophy.

## Acceptance criteria

- [x] A valid V2 historical replay/backtest is defined clearly at semantic level.
- [x] Every evaluated prediction is tied to the canonical observation point and legitimate-information boundary.
- [x] Prediction outputs are compared only against outcomes defined by the canonical pit-event/target contract.
- [x] Eligibility and censoring are carried into evaluation without silently converting censored/truncated cases into observed events or ordinary negatives.
- [x] Multiple observations/predictions within a race have coherent evaluation semantics that do not create future-information leakage or conflate distinct target episodes.
- [x] Model-selection versus final-evaluation concerns are separated sufficiently to prevent optimistic final backtest claims without freezing a split algorithm.
- [x] Later verification receives explicit leakage, temporal-ordering, reproducibility, and semantic-compatibility requirements.
- [x] Exact metrics, split algorithms, models, features, schemas, architecture, and implementation remain outside scope.
- [x] Every unresolved question is classified as Current-scope, Cross-slice, or Later-phase; no unresolved Current-scope question remains.
- [x] No human-reserved change to the intended replay/evaluation ambition is required; approved Product Owner semantics are preserved.
- [x] Required independent review is completed before approval.

## Review record

- Full scoped review: **PASS** — independent scoped reviewer; GitHub review recorded by `Nelson-Jnrnd` on PR #13, review `pullrequestreview-5154583807`, against head `f134d0ef666938d6d4b6b836e3a8e14263c18fa6` on 2026-09-09. No Blocking, Major, or Minor findings.
- Rework: none required; only review metadata/traceability was updated after the passing review, as explicitly requested by the reviewer.
- Bounded re-review: not applicable because no substantive rework was required.
- Approval evidence: passing PR #13 review `pullrequestreview-5154583807`; artifact transitioned to `Approved` without semantic changes.