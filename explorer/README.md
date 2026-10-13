# Synthetic Replay Explorer

Approved implementation milestone: `design/REPLAY_EXPLORER.md`, `design/REPLAY_TIMING.md`, and decision `2026-10-12-v2-replay-explorer-design-approval.md`.

Run `npm ci`, `npm run dev` in this directory. `npm test` verifies presentation semantics; `npm run build` checks TypeScript and the static build. No production deployment is authorized. Data in this milestone is exclusively synthetic; it provides no trained-model or performance evidence. Real-race integration requires the observation/export owner's causal timing and matched position-geometry verification and development-only release validation.

Images are cached reference assets from the registry in `design/REPLAY_EXPLORER_ASSETS.md`. Portraits retain their original F1 source rights. Circuit credit: Jules Roy / F1DB, CC BY 4.0. Flag credit: flag-icons, MIT. No photographic publication authorization is inferred.

## Current delivery boundary

The bundled JSON is an authored, versioned synthetic fixture for three drivers, including lap0, a missing initial attempt, failed lap18, an explicitly older forecast at fixed race time, lapped-driver timing, unavailable positions, exact/bounded/uncertain/no-event outcomes, and terminal participation. The validator accepts only `kind: synthetic`; it is deliberately not an exporter for real research artifacts. It checks consumed identities, unique time/attempt joins, full probability grids, all four masses and canonical window-rule conformance without repairing data. Genuine artifact digests, model/run lineage, release manifests and protected-final ledger rules belong to the next development-race export integration and must precede accepting any non-synthetic bundle.

Positions use fictional normalized progress on the exact same SVG path as the track drawing. Mini-sector performance is illustrative. Multiple-driver map sector shading is neutral because this fixture does not declare defensible official sector boundaries. Individual car selection is duplicated in a small driver chooser to resolve overlapping map markers.

No raw timing, prediction generation, target resolution, model fitting or remote data calls occur in the viewer. All requests load static app assets. Hash links retain bundle, subject, selected attempt and common race time; outcomes are excluded and default off. Browser Back/Forward restores state.

Automated verification covers contract mutations and interactive clock, selection, navigation, failure, outcome and tab behavior. Real browser screenshots and mobile/keyboard visual checks remain a release gate when a browser runtime is available. This branch is not deployed.
