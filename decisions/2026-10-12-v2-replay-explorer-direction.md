# Decision: Replay Explorer is the initial user experience

- Status: Approved by the Product Owner in conversation on 2026-10-12.
- Scope: user-facing direction only; detailed UX and technology recommendations await report approval.
- Affected artifacts: `product/PROJECT_VISION.md`, `product/SYSTEM_SCOPE.md`, proposed `design/REPLAY_EXPLORER.md`.

## Decision

The Product Owner selected **Replay Explorer only** from Replay Explorer, Prediction Laboratory and Guided Race Story. Initial V2 includes an interactive historical race/driver/checkpoint exploration experience backed by the offline research pipeline's immutable artifacts.

The Explorer shows the prediction associated with a selected checkpoint and permits explicit retrospective comparison with what happened afterward. It does not become a model-development application, guided editorial story, live dashboard or strategy recommendation tool.

## Approval boundary

The Product Owner requested a detailed specification, mockups of each screen and recommended technologies, followed by a report for validation. That report approval is outstanding. Choosing Replay Explorer does not approve the proposed screen inventory, precise controls, technology stack, hosting destination or implementation start.

## Semantic continuity

Existing observation, target, distribution, replay and evaluation contracts remain authoritative. Presentation consumes saved results; it cannot recompute or mutate canonical predictions or access protected final outcomes before the permitted locked evaluation. The existing verification gate PASS covers the pipeline baseline; the new presentation/export specification needs its own review and acceptance coverage.

## Next step

Review `design/REPLAY_EXPLORER.md` and the visual validation report. Persist the resulting detail approval or requested changes before implementation. The user-facing design remains proposed until that approval.


## Subsequent detailed approval

On 2026-10-12 the Product Owner validated the revised mockups and race-timing supplement. The earlier pending boundary above is superseded by [the detailed design approval](2026-10-12-v2-replay-explorer-design-approval.md). Historical timing is included; a current-race feed remains excluded.
