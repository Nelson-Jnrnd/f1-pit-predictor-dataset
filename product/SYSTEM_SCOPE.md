# V2 System Scope

## Status

Blocked — core scope depends on Product Owner approval of the proposed project direction.

## Abstraction level

Wave 0 — product / research scope. This file does not define architecture or implementation.

## Core scope

**Proposed, pending Product Owner approval:**

V2 core scope is a leakage-aware F1 pit-timing prediction project that:

- derives a point-in-time race state from historical race information;
- predicts the likely timing of a driver's next pit stop in pit-window form;
- supports historical replay and backtesting against what happened later in the race;
- treats prediction as descriptive behavior modeling rather than strategy recommendation;
- preserves thesis-era work as comparison evidence rather than V2 semantic authority.

## Initial user ambition

**Proposed:** historical race replay/backtesting is the first consumption mode.

The project should be able to reconstruct a historical prediction point, show or expose the prediction associated with that state, and evaluate it against subsequent race events. This statement does not define a UI.

## Likely future extensions

These are explicitly outside the initial core unless separately approved:

- live inference during an ongoing race;
- live race dashboard / richer interactive replay experience;
- next-compound prediction;
- richer multi-event or multi-stint forecasting;
- counterfactual strategy analysis;
- strategy recommendation / optimization;
- integration with additional live or commercial data providers.

A future extension is not an implicit requirement for current semantics or architecture.

## Explicit non-goals for the initial core

The initial core does not include:

- recommending when a driver should pit;
- optimizing tyre strategy, race time, finishing position, or another strategic objective;
- predicting the next tyre compound;
- counterfactual simulation of alternative strategy actions;
- a production live-data pipeline;
- a committed live dashboard;
- automated race engineering decisions.

## Technical choices deliberately not frozen

Wave 0 does not choose:

- exact observation timing;
- exact pit-event/target construction;
- censoring rules;
- prediction horizon;
- mathematical formulation;
- feature set;
- dataframe/schema fields;
- train/validation/test seasons;
- model family;
- calibration method;
- storage format;
- API shape;
- package/component structure;
- frontend framework;
- live-data provider;
- deployment model.

## Information philosophy

Every prediction and evaluation must respect point-in-time availability: future information must not influence a prediction that purports to have been made earlier in the race.

Exact data-availability semantics are delegated to the Race Observation / State slice.

## Unknown routing

| Question | Classification | Owner / next artifact | Status |
| --- | --- | --- | --- |
| Core V2 scope and prediction-vs-optimization boundary | Current-scope | Product Owner | Blocking |
| Historical replay first, live later | Current-scope | Product Owner | Blocking |
| Exact state available at a prediction point | Cross-slice | Race Observation / State | Wave 1 |
| Exact event/target/censoring scope | Cross-slice | Pit Event / Target Semantics | Wave 1 |
| Exact replay/output contract | Cross-slice | Prediction Output / Replay Semantics | Wave 1 |
| Exact evaluation protocol | Cross-slice | Evaluation / Backtesting | Wave 1 |
| Models, data structures, APIs, runtime, UI, live provider, persistence | Later-phase | Design / verification / implementation | Deferred |
