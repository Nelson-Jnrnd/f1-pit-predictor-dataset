# Decision: approve Replay Explorer design and race timing

- Status: Approved by Nelson Jeanrenaud on 2026-10-12 (Europe/Zurich).
- Approval: “Perfect I valdiate that”, following the revised UI and race-timing proposal.
- Canonical artifacts: design/REPLAY_EXPLORER.md and design/REPLAY_TIMING.md.
- Independent evidence: PR #47 reviews 5490099069 and 5494958391; bounded re-reviews PASS.

## Approved scope

Race catalogue, replay workspace, Full forecast and About; restrained content and user vocabulary; season-correct portraits/circuits/flags/tyres; compact prediction band above synchronized historical timing tower and track-position map. Preserve shared row/map comparison selection, zero/one/multiple selection modes, replacement timing tabs, separate prediction subject and explicit older-forecast labels. Continuous playback and current-race feeds remain excluded.

Approve the proposed React/TypeScript/Vite static viewer, SVG charts/map and validated exports from the existing Python pipeline. No change to prediction meaning, causal availability, research disclosure or protected-final evaluation/export rules.

## Delivery

Proceed first with a synthetic end-to-end viewer and relevant unavailable/selection/mobile states, then verify and integrate one permitted development race. Real timing/position coverage requires causal evidence; illustrative mockups do not establish it. Existing final evaluation locks remain. Public deployment, hosting provider/domain and broader publication require their own authorization.
