# Replay Explorer: race timing extension

Status: proposed detailed design for Product Owner validation. User requested timing tower and car positions at the prediction lap on 12 October 2026. Historical Replay Explorer remains the product; no current-race feed, implementation or publication is authorized.

## Source decisions

Reference: F1_Telemetry_Charts, chatbot branch at ae3485d695f07137f6778e03c3437ca1464fb7df, SPEC-007 and its implemented amendments 014-025; current PlaybackTimingTower and map selection behavior. The earlier timing-tower handoff is historical planning, not authority where later amendments supersede it. This imports interaction decisions, not layout code, private API access or that project's data assumptions.

## Layout and information

Extend S2, rather than add a second dashboard with another clock. On desktop: compact driver/prediction band above a circuit map and timing tower. Lap controls remain shared. Preserve the four absolute probabilities next to the window; Full forecast, Earlier predictions and Show actual stop remain deliberate actions. No duplicate permanent driver-state sidebar. The map and tower can be collapsed; the forecast remains visible.

Race is the initial timing tab. Columns: position, three-letter driver code, interval to the car ahead, gap to leader, tyre icon with age, last completed lap. Thin team/driver color rail; pit indicator only when relevant. All released participants remain in the tower, even without map coordinates; race order never comes from physical map order. Final classification is never substituted for position at the selected instant. Last-known timing positions may order rows only when admitted under the canonical freshness rules; unknown positions are unranked.

Other tabs replace columns rather than append them: Laps (last/best), Last sectors (S1/S2/S3/lap), Best sectors (S1/S2/S3/theoretical), Minis (qualitative state strip). Race-control, penalties and track-limit text appear only when relevant and supported. No permanent empty event columns, source ages, internal status codes or provenance tables. Missing values read Not available or a dash with an accessible explanation.

Map: circuit trace, cars in their season colors and three-letter labels. Zoom, pan, rotate and fit/reset; compact controls. Keep all cars visible when comparing a subset. Nearby markers need distinct hit targets or a small driver chooser; no oversized marker rings. Static circuit imagery alone does not establish a coordinate system for car positions: use a validated matching geometry/projection.

## Shared interaction decisions

Timing rows and map markers toggle membership in one shared comparison selection. Clicking a selected driver removes only that driver. Clearing all returns to absolute timing; no extra All button.

- Zero selected: absolute field-wide timing.
- One selected: that driver is the shared reference; comparable timing, tyre age and lap/sector values use signed deltas. Position, compound, pit state remain absolute. Interval is blank in relative mode because intervals to different cars ahead are not comparable. Equal tyre age is neutral.
- Two or more selected: absolute values; highlight the fastest selected comparable lap/sector cells, including ties. Do not rank position, interval, gap or tyre age.
- A single selection colors map minisectors with the approved performance states. Multiple selections color supported official sectors by the selected latest-sector winner; absent defensible boundaries/comparisons leave a neutral circuit rather than imply precise sector ownership. Minis show states, not times. Session best is purple, personal best green, slower muted yellow, unavailable grey; text/table access supplements color.

The prediction subject is a separate single-driver choice, shown by portrait/name. Comparison clicks never silently change it or the race clock. A selected-row action View prediction explicitly changes subject. At the fixed clock choose that driver's latest recorded prediction attempt no later than the clock, including failed attempts rather than resurrecting an older success. Show its own prediction lap/time; never label an older forecast as current. If older, show a short Prediction from lap N notice, with Go to prediction lap as an explicit clock change. If no attempt is available, show No prediction available yet. No same-numbered-lap alignment across drivers.

## Clock and data boundary

Selecting a prediction lap supplies the race boundary T from that recorded attempt (owner: observation reconstruction). After changing the prediction subject at fixed race time, its displayed attempt has a separate boundary T_p <= T. The map and tower stay at T; the forecast and its own input context remain immutable at T_p, visibly labelled when older. Timing at T is race context, never represented as the older forecast's input. The timing/map projection aligns the full field to that same boundary, including publication order at tied timestamps. Other drivers may be on different laps. Selecting a prediction lap changes T and updates map/tower together. This extension supersedes same-lap-ordinal subject switching in REPLAY_EXPLORER.md: subject changes retain race time and identify an older or missing attempt. Race changes still reset to the canonical roster entry/L0; comparison selection is reset on race change. Previous/Next or a selected-subject lap choice selects that subject's exact recorded attempt and moves T to its boundary.

Timing context admits only facts defensibly available at T under existing observation-reconstruction authority/freshness/correction rules. Best lap and best sectors mean best known by T, never session-final best. Mini-sector references include only eligible completed evidence by T; no future reference lap. Gap/interval come from admitted timing relations, never map distance. Missing/sparse/stale positions are omitted with a short Positions unavailable notice; the tower can remain usable. No future-point interpolation, final lap-row backfill, telemetry from after T, or unverified source added merely for presentation. Past-only reconstruction requires an approved provider rule and recorded limitations. No UI click fetches new raw data or alters the prediction inputs.

The new race-wide presentation projection is a named dependency on observation reconstruction/export design. Availability of positions, full-field timing, sectors/minis and their references is not established by their existence in the reference repository. Validate and extend provider/export coverage before promising those fields for a real race. If unsupported, ship explicit unavailable states rather than fabricate a complete dashboard. Export validation and protected-final exclusion in REPLAY_EXPLORER.md apply equally to timing and position bundles.

For V1, lap navigation remains the clock; no independent free-running time slider or Play/Pause. Car markers update only when a recorded prediction instant is selected. Continuous playback and smooth movement are deferred; SPEC-007's player controls/pacing are not imported. Track-position display is included by the user request, superseding the parent's exclusion of that display; continuous track animation remains excluded.

## Mobile and technology

Compact forecast stays above one Race timing / Track map switch, sharing clock and selection. Every other timing tab remains reachable; controls use useful touch targets and keyboard focus. Avoid simultaneous tiny map and twenty tiny rows. Forecast details/outcomes/history remain available on request.

React/TypeScript/Vite recommendation unchanged. Use SVG for validated geometry, markers and comparison overlays; browser-local view state and static precomputed projection files. No FastF1 calls in browser. Export size/downsampling, time indexing and performance budget are implementation-design tasks; data fidelity and causality gates precede optimization.

## Acceptance and validation

1. Same T for the tower and all positioned cars; a selected exact attempt shares that T. When switching subjects at fixed T, verify T_p <= T, label older predictions, preserve their original input context, and demonstrate both older-prediction and lapped-driver fixtures.
2. Row/map selection synchronizes, deselects independently, preserves full field and correctly transitions zero/one/multiple comparison modes.
3. Prediction subject does not change on comparison click. View prediction explicitly distinguishes an older or unavailable prediction and does not move time without an action.
4. No future best laps, sector references, positions, race-control events or final classification. Outcome toggle changes no timing/context values.
5. Sparse positions leave timing usable; a driver without coordinates remains selectable from the tower.
6. Readable desktop/mobile, accessible values, all tabs, no raw implementation vocabulary. Export rejects protected data.

Detailed design remains proposed. Review status: independent scoped review initially identified two clock/parent-spec conflicts; corrected and bounded re-review PASS by /root/review_ui_restraint. Stale acceptance wording and report clock phrasing also corrected. All three mockup pages visually inspected. GitHub record: draft PR #47, passing review to be attached to this revision. User-facing mockup supplement uses synthetic timing/car positions, not race results.
