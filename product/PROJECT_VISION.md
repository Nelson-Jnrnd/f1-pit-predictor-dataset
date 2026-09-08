# V2 Project Vision

## Status

Draft — Product Owner direction approved on 2026-09-08; pending independent review.

## Abstraction level

Wave 0 — product / research direction.

## Durable direction

See `decisions/2026-09-08-v2-project-direction.md`.

## Concise project statement

Continue the thesis-era F1 pit-prediction work by estimating when a driver's next pit stop is likely to occur from information legitimately available at a declared race moment, producing a pit-window style prediction for replay/evaluation rather than prescribing an optimal strategy.

## Why this project exists

The thesis-era repository established a useful data and modeling base around F1 pit behavior. The legacy README describes the data as intended for machine-learning prediction of when a driver will pit, and the legacy training notebook constructs a binary `is_pitting` target from pit status and evaluates classifiers.

V2 exists to make the prediction problem more temporally informative, better specified, and easier to evaluate without leaking future race information. Instead of treating the legacy implementation as authoritative semantics, V2 will define those semantics explicitly before technical redesign.

## Continuity with the BSc thesis

V2 is a continuation, not a rewrite of history:

- thesis-era datasets, notebooks, models, and branches remain evidence and baseline material;
- the historical modeling thread is predictive pit behavior;
- exact legacy target details are evidence to be documented by the Wave 1 Legacy Thesis Evidence slice, not copied automatically into V2;
- the repository also contains a separate strategy-calculator experiment aimed at minimizing race time, demonstrating that prediction and strategy optimization were distinct exploratory threads.

Historical evidence references:

- thesis-era `README.md` at pre-V2 commit `2d143361d2a4721f88665bea540ef418707a3ac5`;
- thesis-era `model_training.ipynb` at the same historical state;
- thesis-era `strategy_calculator.ipynb` at the same historical state;
- historical branches `training_rf`, `training_svm`, and `cleaning`.

## Value V2 should add

V2 should add:

1. a prediction outcome that communicates likely pit timing over more than a single binary instant;
2. explicit point-in-time information rules so replay predictions are causally legitimate;
3. clear ownership of observation, pit-event/target, prediction-output, and evaluation semantics;
4. reproducible historical replay/backtesting suitable for research and portfolio demonstration;
5. a semantic baseline that could later support live inference without designing live infrastructure now.

## Research and portfolio value

The project should demonstrate disciplined temporal ML problem definition, leakage-aware evaluation, uncertainty-aware prediction semantics, and traceable evolution from a thesis prototype to a specification-driven V2.

The value is not tied to a particular model family, feature set, library, API, dashboard, or deployment architecture.

## User-facing outcome

The first user-facing outcome is a historical race replay/backtesting experience in which a point-in-time race state can be associated with a pit-window prediction for a driver and compared with what subsequently happened.

Live inference is a possible later extension, not an initial product commitment.

## Explicit boundary

V2 predicts what a team/driver is likely to do. It does not recommend what they should do and does not optimize race strategy.

## Unknown routing

| Question | Classification | Owner / next artifact | Status |
| --- | --- | --- | --- |
| V2 objective, predictive-vs-prescriptive boundary, and historical-replay-first ambition | Current-scope | Product Owner | Satisfied — `decisions/2026-09-08-v2-project-direction.md` |
| Exact observation moment and information available then | Cross-slice | Race Observation / State | Wave 1 |
| Exact pit-event identity, target construction, and censoring | Cross-slice | Pit Event / Target Semantics | Wave 1 |
| Exact pit-window / uncertainty representation and prediction horizon | Cross-slice | Prediction Output / Replay Semantics | Wave 1 |
| Metrics, backtest split design, and evaluation procedure | Cross-slice | Evaluation / Backtesting | Wave 1 |
| Features, models, schemas, package/runtime structure, live provider, UI, persistence | Later-phase | Design / verification / implementation | Deferred |

## Acceptance state

- Project direction: approved by Product Owner on 2026-09-08 and persisted in the durable decision record.
- Thesis continuity: established at Wave 0 level.
- Independent Wave 0 review: pending.
- No technical implementation choices are frozen here.
