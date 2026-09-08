# Decision: V2 project direction

- **Status:** Approved
- **Date:** 2026-09-08
- **Owner:** Product Owner
- **Affected artifacts:** `product/PROJECT_VISION.md`, `product/RESEARCH_PROBLEM.md`, `product/SYSTEM_SCOPE.md`, `contexts/CONTEXT_MAP.md`

## Question

What product/research direction should V2 use for its core prediction objective, predictive-versus-prescriptive boundary, and initial consumption ambition?

## Decision

V2 will estimate when a driver's next pit stop is likely to occur from information legitimately available at a declared race moment, expressed conceptually as a pit-window-style prediction.

The core project predicts likely team/driver behavior. It does not recommend or optimize race strategy.

Historical race replay/backtesting is the initial user-facing and evaluation ambition. Live inference is a possible later extension, not an initial product commitment.

## Rationale

This direction continues the thesis-era predictive pit-behavior thread while making the temporal prediction problem more informative and explicitly leakage-aware. Keeping recommendation/optimization outside the core preserves a clear behavioral-prediction scope, and historical replay provides a bounded first application without prematurely committing to live infrastructure.

## Consequences / semantic locks

- The V2 core objective is next-pit timing prediction rather than strategy recommendation or optimization.
- Predictions must respect point-in-time information availability.
- Historical replay/backtesting is the initial consumption ambition; live inference remains a later extension.
- Exact observation timing, pit-event/target construction, censoring, prediction horizon, mathematical formulation, uncertainty representation, metrics, model family, features, schemas, architecture, APIs, UI technology, live provider, and implementation remain undecided unless owned by a later bounded task.
- A material change to these approved product/research semantics requires a new bounded Product Owner decision and reconciliation of affected artifacts.

## Alternatives considered

- Retain the thesis-era next-lap binary pit classification as the primary V2 outcome.
- Make strategy recommendation/optimization part of the core V2 product.
- Treat live inference as an initial product commitment rather than a later extension.

## Follow-up

- Update the Wave 0 canonical artifacts to reference this decision and remove the Product Owner blocker.
- Submit Wave 0 for the required independent scoped review.
- After a passing review and merge, launch the bounded Wave 1 semantic slices defined in `contexts/CONTEXT_MAP.md`.
