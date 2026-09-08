# Decision: V2 pit-event scope

- **Status:** Approved
- **Date:** 2026-09-08
- **Owner:** Product Owner
- **Affected artifact:** `contexts/PIT_EVENT_TARGET.md`
- **Issue:** #6

## Question

What should count as the canonical V2 pit event?

## Decision

A relevant V2 pit event is restricted to a race pit visit for the selected driver in which tyre service occurs.

Pit-lane visits without tyre service are not relevant V2 pit events for this target, including drive-through/pass-through visits, repair-only visits, and stationary penalties served without tyre service. Pre-race/grid movements and movements after the driver's race participation has ended are also outside the target scope.

This decision defines event qualification only. The exact semantic occurrence anchor within a qualifying tyre-service visit (for example, pit-lane entry versus the service/stop instant) remains unresolved and must be decided in Issue #6 before the event-timing contract can be approved.

## Rationale

The Product Owner selected option `C — Tyre-service stop only` from the Issue #6 decision card. This intentionally narrows the V2 next-pit target to tyre-service behavior rather than every pit-lane visit or every genuine stop/service visit.

## Consequences / semantic locks

- A pit visit qualifies only if tyre service occurs during that visit.
- Drive-through/pass-through visits do not qualify.
- Repair-only or penalty-only stops without tyre service do not qualify.
- Motivation does not otherwise matter: a qualifying tyre-service stop can occur under green flag, Safety Car/VSC, red flag-related race continuation, damage response, or another race context, provided it remains within the driver's race participation.
- Legacy `InLap`, `PitInTime`, tyre-change fields, or other provider representations are evidence/implementation inputs only; no single field becomes normative merely from this decision.
- The exact occurrence anchor and technical event-reconstruction rules remain unresolved at their proper semantic/later-phase levels.
- A material change to this tyre-service-only scope requires a new Product Owner decision and reconciliation of downstream semantic artifacts.

## Alternatives considered

- A qualifying pit-stop/service visit, including tyre service, repairs/adjustments, or a stationary penalty.
- Any pit-lane entry, including drive-through/pass-through visits.

## Follow-up

- Update `contexts/PIT_EVENT_TARGET.md` to consume this decision.
- Resolve the remaining event occurrence anchor before independent review.
- After the full event/target contract is semantically complete, submit PR #11 for the required independent scoped review.
