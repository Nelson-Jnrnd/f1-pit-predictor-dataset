# V2 Research Problem

## Status

Draft — Product Owner direction approved on 2026-09-08; pending independent review.

## Abstraction level

Wave 0 — product / research direction. This file defines what is being predicted conceptually, not its statistical formulation.

## Durable direction

See `decisions/2026-09-08-v2-project-direction.md`.

## Primary problem

Given the race information legitimately available at a declared prediction moment for a driver, estimate when that driver's next pit stop is likely to occur, expressed conceptually as a pit window / likelihood over future race progression.

This wording deliberately does not decide:

- exact observation timing;
- exact pit-event definition;
- exact prediction horizon;
- discrete survival, hazard, multiclass, regression, or other mathematical formulation;
- exact probability representation or calibration method.

Those decisions belong to bounded Wave 1 or later work.

## Prediction versus recommendation

### Prediction

Prediction asks: **What is the team/driver likely to do next, and when?**

Its output is descriptive/probabilistic behavior modeling based on information available at the prediction moment.

### Recommendation / optimization

Recommendation asks: **What should the team/driver do to improve an objective such as race time, position, or expected result?**

That requires counterfactual assumptions, objective functions, action alternatives, and optimization semantics that are materially different from behavior prediction.

**V2 boundary:** recommendation/optimization is not part of the core V2 prediction problem.

## Point-in-time correctness principle

A V2 prediction must use only information that would legitimately have been available at its declared prediction moment.

This is a project-level semantic principle and applies to data construction, replay, evaluation, and eventual live use.

The exact prediction moment, availability rules, treatment of partially observed laps, and similar details are not decided here. They are owned by Race Observation / State.

## Conceptual use flow

```text
historical or eventual live race information
    -> point-in-time race state
    -> pit-window prediction
    -> historical replay / evaluation
    -> possible later live consumption
```

This is a semantic flow, not a component or package architecture.

## Research questions enabled by this direction

At later phases, the project should be able to ask questions such as:

- how well can future pit timing be anticipated from legitimate point-in-time race information?;
- how does prediction quality vary with distance from the eventual pit event?;
- how stable and interpretable is the model's uncertainty over future laps?;
- how does V2 compare with the thesis-era binary classification baseline under leakage-safe replay evaluation?

These are research motivations, not commitments to specific metrics or algorithms.

## Unknown routing

| Question | Classification | Owner / next artifact | Status |
| --- | --- | --- | --- |
| Pit-window-style next-pit timing prediction as the primary V2 objective | Current-scope | Product Owner | Satisfied — `decisions/2026-09-08-v2-project-direction.md` |
| Prediction rather than strategy recommendation/optimization as the core intent | Current-scope | Product Owner | Satisfied — `decisions/2026-09-08-v2-project-direction.md` |
| Define the legal prediction moment and information boundary | Cross-slice | Race Observation / State | Wave 1 |
| Define the pit event, target relation, and censoring semantics | Cross-slice | Pit Event / Target Semantics | Wave 1 |
| Define exact output semantics, uncertainty representation, and horizon | Cross-slice | Prediction Output / Replay Semantics | Wave 1 |
| Define evaluation units, splits, metrics, and backtest protocol | Cross-slice | Evaluation / Backtesting | Wave 1 |
| Select model family, features, calibration method, or technical pipeline | Later-phase | Design / experimentation | Deferred |
