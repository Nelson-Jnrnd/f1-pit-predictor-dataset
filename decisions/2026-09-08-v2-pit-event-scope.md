# Decision: V2 pit-event scope and occurrence anchor

- **Status:** Approved
- **Date:** 2026-09-08
- **Owner:** Product Owner
- **Affected artifact:** `contexts/PIT_EVENT_TARGET.md`
- **Issue:** #6

## Question

What should count as the canonical V2 pit event, and at what semantic instant does that event occur?

## Decision

A relevant V2 pit event is restricted to a race pit visit for the selected driver in which tyre service occurs.

Pit-lane visits without tyre service are not relevant V2 pit events for this target, including drive-through/pass-through visits, repair-only visits, and stationary penalties served without tyre service. Pre-race/grid movements and movements after the driver's race participation has ended are also outside the target scope.

For a qualifying tyre-service visit, the event occurrence is anchored to the driver's **pit-lane entry** for that visit. Whether the visit qualifies is established retrospectively from eventual evidence that tyre service occurred; the prediction made before that event does not know or receive that future qualification truth.

FastF1 `PitInTime`, or another defensible reconstruction of the same pit-entry occurrence, is an expected implementation/evidence candidate rather than a normative provider-field requirement. Later data/design and verification work must establish that the chosen source reconstructs pit entry and tyre-service qualification reliably enough to implement this semantic contract.

## Rationale

The Product Owner first selected `C — Tyre-service stop only`, intentionally narrowing the V2 next-pit target to tyre-service behavior rather than every pit-lane visit or every genuine stop/service visit.

The Product Owner then approved the pit-entry occurrence anchor after repository and FastF1 evidence showed that an exact pit-box/tyre-service-start timestamp is not part of the current stored dataset and is not an explicit FastF1 lap field, while FastF1 does expose a reconstructed pit-entry time (`PitInTime`). Anchoring the semantic event to pit entry keeps the target reconstructable without pretending that tyre service is knowable at that instant: tyre service qualifies the visit retrospectively, while pit entry supplies the occurrence time.

## Consequences / semantic locks

- A pit visit qualifies only if tyre service occurs during that visit.
- Drive-through/pass-through visits do not qualify.
- Repair-only or penalty-only stops without tyre service do not qualify.
- Motivation does not otherwise matter: a qualifying tyre-service stop can occur under green flag, Safety Car/VSC, red-flag-related race continuation, damage response, or another race context, provided it remains within the driver's race participation.
- The occurrence of a qualifying event is the pit-lane entry for that visit, not the later pit-box arrival, service start, service completion, or pit exit.
- Event qualification may use eventual post-event truth during retrospective target construction; that future truth must not enter the point-in-time observation used to make the prediction.
- Legacy `InLap`, FastF1 `PitInTime`, tyre/stint fields, or other provider representations are evidence/implementation inputs only; no single field is normative merely from this decision.
- Exact provider reconstruction rules, tolerances, handling of missing/ambiguous pit timestamps, and proof that tyre-service transitions can be reconstructed robustly are later data/design and verification decisions.
- A material change to the tyre-service-only scope or pit-entry occurrence anchor requires a new Product Owner decision and reconciliation of downstream semantic artifacts.

## Alternatives considered

Event scope:
- a qualifying pit-stop/service visit, including tyre service, repairs/adjustments, or a stationary penalty;
- any pit-lane entry, including drive-through/pass-through visits.

Occurrence anchor:
- pit-box arrival / tyre-service start. Rejected because the current repository data do not preserve such a timestamp and FastF1 does not expose an explicit tyre-service-start lap field.

## Follow-up

- Update `contexts/PIT_EVENT_TARGET.md` to consume the complete approved event definition.
- Route provider-specific event reconstruction and tyre-change-detection reliability to later data/design + verification work.
- Submit PR #11 for the required independent scoped review.