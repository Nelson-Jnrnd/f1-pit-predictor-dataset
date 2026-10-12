# Replay Explorer - approved UX and delivery specification

## Status and scope

**Approved by the Product Owner on 2026-10-12**, following independent review PASS. Approval covers the revised screens, information restraint, motorsport imagery, race timing extension and React/TypeScript/Vite static viewer architecture. See `decisions/2026-10-12-v2-replay-explorer-design-approval.md`. Implementation may proceed through the synthetic viewer then one verified development-race milestone; public deployment remains separately authorized.

Baseline: `main` at `4d47e9f552796f68919db4c6e951c408cb03bd17`, including the verification integration PASS. Consume `design/SYSTEM_ARCHITECTURE.md`, `OBSERVATION_RECONSTRUCTION.md`, `TARGET_RECONSTRUCTION.md`, `PREDICTION_CONTRACT.md`, `REPLAY_BACKTEST.md`, `verification/EVALUATION_PROTOCOL.md`, and all approved decisions. This artifact owns presentation behavior and a read-only export boundary; it does not redefine any prediction or evaluation semantics.

## 1. Product outcome

A visitor opens the Explorer in a browser, selects a published race and driver, moves through that driver's completed-lap checkpoints, and understands what the saved model predicted at each point. They can reveal the eventual outcome without changing the forecast or its historical inputs.

Initial scope: one driver and one frozen published model per race bundle; catalogue, replay, prediction details, methodology/context. The first end-to-end milestone is one development race with B1 as the published model, or an explicitly identified B0-only preview if B1 is not yet implemented. Baseline-first availability must not imply that an advanced model has been trained.

Excluded from V1: Prediction Laboratory, Guided Race Story, separate model-comparison/evaluation dashboard, training controls, model tuning, uploads, accounts, live feeds, track-position animation, strategy recommendations and next-compound forecasts. No play/pause or autoplay in V1: previous/next and slider navigation are sufficient. Reference-model comparison and multiple published model versions can be separately specified later.

## 2. Screens and navigation

| ID | Surface | Primary purpose | Entry / exit |
| --- | --- | --- | --- |
| S1 | Race catalogue | Find a published replay | App entry; Open replay leads to S2 |
| S2 | Replay workspace | Inspect one driver's checkpoint forecast and optionally its outcome | S1 or shared URL; Back to races returns to S1 |
| S3 | Full forecast drawer | Show the full forecast and relevant missing race information | S2 Full forecast / Why unavailable; Close/Escape returns to unchanged S2 |
| S4 | About the prediction panel | Explain the prediction in motorsport vocabulary and provide image credits | About in S1/S2; Close/Escape returns to invoking view |

S3 and S4 are overlays, not extra dashboard pages. Mobile layouts and no-forecast/error states are variants of these four surfaces, not additional features. The catalogue is the landing page; do not add an introductory home page or guided story.

### S1 - Race catalogue

- Header: Replay Explorer, Season selector, About. No purpose paragraph or marketing hero. The first task is choosing a race.
- One Season selector; only seasons with published bundles appear. Within a season, rows ordered by official round. No search field or additional filters in V1.
- Each row: season-correct circuit outline, country flag, race name/date and one Open action. Remove driver counts, model labels, repeated explanation and availability badges. Flags accompany readable names.
- No fake availability for all supported raw-data races: the verified 55-race scope is not a promise that 55 replays already exist. Unsupported or protected sessions are absent from the public catalogue and build, not disabled rows with downloadable hidden data.
- Opening selects the first canonical roster entry (numeric racing-number order) at race-start checkpoint L0. If that checkpoint has no forecast, show its explicit state; do not jump silently to the first successful forecast. Driver names are display labels; stable session/racing-number keys identify entries.
- Empty catalogue: no published replays yet; no invented sample result. Fetch failure: plain error and Retry.

### S2 - Replay workspace

**Top-level hierarchy:** race/driver identity; lap navigation; likely pit window. Earlier predictions and Full forecast are requested expansions. Internal identifiers/provenance stay in research artifacts and are absent from all product screens, including S3/S4.

Header: Back to races, race name with a small country flag/circuit outline, Driver selector and About. Selected-driver portrait, full name and season-correct team identify the subject. No model code, B0/B1 label, version or run badge. If a driver is absent in the same race URL, explain the unavailable selection rather than substitute another silently.

Checkpoint navigation: selected driver's completed-lap count, Previous, Next, full driver checkpoint slider and a keyboard-operable lap value. L0 is Race start; L20 means information available at lap-20 completion, forecasting entry in lap21 onward. The slider enumerates recorded CHECKPOINT attempts, including attempts without valid forecasts; it neither interpolates nor synthesizes missing snapshots. Explicit enumeration gaps are visible and not filled. SESSION/DRIVER_ENTRY failures are race/entry-level notices and are not fabricated lap checkpoints. Previous/Next stop at the ends.

At race changes, driver and checkpoint reset explicitly to the default roster entry/L0; outcome visibility resets off. The proposed race-timing extension in [REPLAY_TIMING.md](REPLAY_TIMING.md) supersedes same-lap-ordinal driver switching: changing the prediction subject retains the race clock, shows its latest recorded attempt at or before that clock (including failure), and labels an older prediction. Previous/Next or choosing its prediction lap explicitly moves the race clock to that attempt. Comparison selection is independent. Race changes retain roster/L0 reset and outcomes off. Driver laps remain independent.

**Forecast panel:**

- Window label uses exported `PitWindowSummary`: e.g. Likely next-stop window: laps24-27. If it includes the open final region, show the final bound as 'lap57 or later', never a closed interval.
- Four masses stay visible in one compact strip, not four metric cards: Before lap24, Laps24-27, After lap27, No more stops, using actual bounds. Display absolute probabilities. Explain conditional window coverage in Full forecast/About when requested, without alpha or normalization terminology.
- The complete distribution is accessible through Full forecast (S3): x axis = selected-driver pit-entry lap, y axis = probability %. The default main view shows only the compact before/window/after/no-more-stops strip alongside the window. No-event is separately labelled. Full forecast opens the complete remaining scope, ending with the open final bin. Long grids use readable ticks; any optional presentation grouping preserves summed mass and exposes constituent bins on inspection. No silent fixed-horizon crop, normalized event-only curve, tail loss or invented final lap.
- Native-focusable chart targets or an equivalent numeric table make values accessible without hover; touch selection gives the same value. Colour does not carry meaning alone.
- Compact context: a labelled tyre graphic with compound/age (Medium, 10 laps), only from the canonical observation. Track status appears when relevant, such as Safety car, not as a permanent Clear row. No State at checkpoint panel. Additional helpful context is on request in Full forecast. Unavailable optional fields show Not available for this lap. Do not source them from processed final lap rows. Historical truth from #19 never fills this area.
- q=1 / P_event=0: No further stop predicted; no highlighted window; preserve zero event masses. This is valid output, not a missing prediction. Any zero-probability display allowed by the contract is distinguished from the evaluation protocol's floor requirement.

**Retrospective outcome comparison:** off by default. Toggle Show actual stop reveals only the selected episode's published resolution from the permitted backtest projection: observed tyre-service entry (exact in-lap or supported range), terminal no-event, or unresolved outcome. Truncated truth remains 'Actual stop uncertain', with no stop/no-stop guess and no score. Mapping defects are labelled 'Actual stop unavailable' and never evaluated as an ordinary miss. The forecast and as-of state remain byte/content-identical when toggled.

The outcome is labelled Actual stop or Did not stop again and remains separate from the current-lap forecast/context. Retrospective is specification terminology, not UI copy. When exact, its chart marker is at the matching exported region, not at an inferred rounded clock time. Set-valued mapping shows the full range. For comparison with a window, label it Fully inside, Fully outside, or Partly overlapping according to set containment/intersection; partial overlap is not a definite hit or miss. An exact entry outside the window, or a supported range entirely disjoint from it, is outside the window. A range contained in it is within the window. Partial overlap says: The actual stop may have been inside or outside this window. A window miss is not a failed normalized forecast. No 'correct prediction' badge or strategy-optimality wording.

**Earlier predictions (closed by default):** show saved window intervals for the same driver and model at earlier checkpoints up to the selected checkpoint only. Each is its own immutable target episode, even when several resolve to the same stop. No line across unavailable checkpoints; use gaps and status labels. Clicking a row selects that exact checkpoint. Outcome annotations appear only while retrospective visibility is enabled. After a stop, later eligible snapshots can concern a new next-stop question; do not align their windows to the old event or infer a single episode across all laps.

No per-race model score, calibration dashboard or cross-model chart in S2. S4 may link to an existing published evaluation report without inventing a new report UI.

### S3 - Full forecast

Drawer header: Full forecast, selected driver, Lap20, Close. Complete remaining-lap distribution is the primary content, with explicit No more stops probability. One short explanation translates the highlighted window. Optional context includes only facts that help interpret the forecast and important omissions. Use Pit-entry lap, Chance of a stop and Some race information is missing; never canonical grid, reconstruction quality or availability bounds.

No visible identity table, model version, copyable snapshot/observation/episode/run ids, lineage, JSON or protocol fields, even in expanded details. They remain in technical research artifacts. Actual-stop marks appear only while Show actual stop is enabled; future truth never enters the current-lap context. Missing forecasts have no fabricated chart or id. Escape closes, focus returns to opener; mobile uses a full-width sheet.

### S4 - About the prediction

Short panel in user vocabulary: the forecast estimates when this driver may next enter the pits for a tyre change; it can be wrong, and missing race information can prevent a prediction. Explain No more stops and the highlighted window in two short paragraphs. Keep project/authorship and image credits here, with links to a published research report if available.

No model codes, contract/schema versions, artifact ids, decision numbers, RA-1..RA-4 codes or evidence-exception terminology in product copy. Mandatory detailed evidence/provenance disclosure remains in every affected research score report and technical artifact; this panel does not replace it. A concise user explanation may say historical timing data is reconstructed and has limitations. The Explorer presents no primary-performance claim of its own.

## 2a. Information selection and visual-review rules

User feedback on 2026-10-12 is authoritative: select information by the visitor's immediate task, use motorsport vocabulary and real domain imagery. This replaces the information-dense mockups, not upstream prediction semantics.

- Default screen answers which race/driver/lap, which pit window, how likely, and how to change lap. Secondary content requires an explicit action; it does not fill unused space.
- One compact strip preserves the four mandatory masses. Complete distribution and earlier forecasts are distinct, closed-by-default expansions. Minimalism must not remove uncertainty or conceal failure states.
- Use whitespace and ruled structure. Avoid equal-weight metric cards, a pale rounded panel around every group, decorative pills, generic SaaS heroes, ornamental gradients/shadows and purposeless animation. Retain focus, loading, empty and error behavior.
- Circuit outlines identify races; country flags aid recognition; driver portraits identify the subject; tyre graphics encode compound with text. Match season/layout and roster identity. Images are static metadata, not a reason to add car/track animation or extra telemetry. Do not generate a circuit outline or driver likeness.
- Missing imagery uses a text/initial fallback and does not block replay. Picture selection is separate from model input. Avoid unrelated stock or promotional imagery.
- Sources inspected: driver portraits and tyres on F1_Telemetry_Charts branch chatbot, commit ae3485d695f07137f6778e03c3437ca1464fb7df; F1DB circuit SVG layouts; flag-icons country SVGs. Credits/original source references are retained. A repository code license is not assumed to grant photographic rights. Mockups do not authorize publication.
- Anti-slop checklists are review aids, not product features, numerical quality scores or prescriptions to add decoration. Apply task hierarchy, restrained content and real motorsport identity.
- Product-copy acceptance: no checkpoint, snapshot, immutable identity, canonical, artifact, resolution, protocol, B0/B1, schema or RA codes in visible labels/help/errors. Internal specifications/research reports intentionally retain technical vocabulary.

## 3. Exceptional and responsive states

| State | Viewer behavior |
| --- | --- |
| Bundle loading / failed download | Skeleton then Retry; preserve selection; no sample result substitution |
| Unknown URL race/driver/checkpoint | Specific unavailable-selection message; Back to races; offer recorded checkpoints without silently changing the request |
| No canonical observation / uncertain eligibility / ineligible | No forecast panel; concise reason and Why unavailable; lap remains selectable |
| Prediction failure, including missing scheduled distance | No prediction for this lap; a concise user reason; never carry the previous forecast forward |
| Valid prediction, indeterminate target | Forecast remains visible; opted-in actual-stop panel says uncertain; not scored |
| Defective comparison / missing mapping | Forecast visible if valid; comparison unavailable; no success/miss score |
| Optional state omission | Not available for this lap; never blank=zero |
| Retired/finished driver | Render recorded checkpoint states only; no artificial forecasts after terminal participation |
| Invalid schema/hash/probability normalization | Refuse affected bundle with a data-error message; do not repair probabilities in the browser |

Responsive proposal: desktop >=1024px uses forecast + compact driver/tyre context; tablet 640-1023px stacks context; mobile <640px stacks controls/forecast/state and uses full-width details sheets. At 360px the chart retains readable labels and all information, using an accessible numeric table when needed. Controls have useful touch targets; charts are not shrunk until labels become illegible. Prefer light appearance with system dark support; colour mapping remains consistent. Respect reduced-motion; essential information never depends on animation.

Keyboard: native selectors/slider; explicit previous/next buttons; focusable interactive chart/table rows; overlays trap focus and restore it on close. Share replay links preserve race, driver, checkpoint and bundle version. Use hash-based routing for simple static hosting. Retrospective visibility is excluded from shared links and defaults off when a link opens.

## 4. Recommended technologies (proposed)

| Layer | Recommendation | Reason / trade-off |
| --- | --- | --- |
| Research / reconstruction / prediction | Existing modular Python pipeline; no ML in browser | Preserves approved canonical ownership and reproducibility |
| Frontend | React + TypeScript + Vite | Suits precise checkpoint interactions; typed view contracts; static production build. Adds a TS toolchain alongside Python |
| Charts | React-rendered SVG with small D3 scale/shape modules | Explicit lap axes, intervals, gaps and outcome markers; React owns DOM. More chart work than a generic chart template |
| Styling / controls | Small CSS design system; native inputs/buttons; accessible drawer primitives where justified | Restrained interface; avoid a dashboard kit and large permanent toolbars |
| Canonical tables / archive artifacts | Existing source manifests; Parquet via PyArrow where useful for new tabular run outputs | Research-efficient columnar files, kept separate from public JSON. Exact canonical serialization remains implementation-owned |
| Public export | Versioned JSON, small catalogue + per-race/per-driver files; Pydantic schema/validation and matching TS runtime validation | Portable presentation projection, no Python execution or database at visitor runtime. Types alone are not runtime validation |
| Testing | pytest for exporter/contracts; Vitest for view functions; Playwright for user journeys | Tests probability conservation, identities, fallback states, keyboard/touch and protected-scope exclusion |
| Deployment | Static hosting for app + released JSON files; provider/domain selected later | No always-running inference/API server. Ordinary HTTP serving needed locally; no file:// support promised |

Recommendation is architectural judgment, supported by official capabilities below; no dependency version is frozen. Pin compatible versions/lockfiles at implementation kickoff. Hosting vendor and domain are not selected and deployment is not authorized.

Alternative: standalone Blazor WebAssembly can also serve a static C# interface and fits the Product Owner's C# experience; its browser runtime payload and potential chart interoperability are trade-offs. React is recommended for this focused chart-heavy public viewer. Blazor Server would introduce a runtime service for otherwise read-only artifacts. Streamlit can suit internal Python exploration but does not match the proposed static public presentation as directly. Do not build multiple frontends.

## 5. Presentation/export boundary

Flow: completed canonical replay/backtest artifacts -> validated export projection -> explicitly released static catalogue/driver bundles -> read-only Explorer. Browser selection changes presentation only.

Logical export content (physical layout/schema to be finalized during implementation): catalogue race/driver/model labels and bundle version; driver CHECKPOINT attempts and race/entry-level notices; per-checkpoint observation projection, eligibility/failure state, full canonical distribution, exported PitWindowSummary, snapshot/episode/observation/model identity; retrospective resolution/mapping/accounting if permitted; evidence-exception/protocol/run provenance. Exported values reference their exact creators; the exporter never creates predictions, resolves target truth, computes a replacement score, repairs a distribution or selects a different resolution.

All fields must come from already-permitted artifacts. Exported observation projections contain only canonical as-of facts; separate retrospective fields are labelled and shown only on explicit opt-in. The browser may format/aggregate display values; full precision remains available. For rounded masses, show enough precision or a rounding note so a 99.9/100.1% displayed sum is not treated as an invalid canonical vector.

Export validation checks schema version, all identity joins, complete region arrays and sum(p)+q, four-mass accounting, final open-bin semantics, omission/failure distinctions, per-driver attempt ordering, provenance, published model identity and consistency with the upstream manifest. Any local window-rule computation is only a contract-conformance check of the exported summary, not its new canonical owner.

**Final-data protection is an export/release boundary, not a UI hide switch.** Only development races or completed, ledger-permitted final evaluations may be exported. Protected final/F2 artifacts, raw target truth and model weights are not packaged into public builds, preload caches or downloadable assets. The retrospective toggle is a viewing preference for already-released outcomes, not access control and not a new ledger opening. New final outcome reads/exports must occur only after the approved join and retain the ledger history; they cannot reset a race's label. Frozen F2 metadata-only rules stay unchanged.

Manual release is deliberate: a completed run alone does not automatically publish a portfolio result. First releases can be local only. Exact release gates are tested before any public deployment; external publication remains a separate authorized action.

## 6. Delivery and acceptance

1. Review/approve this UX + stack proposal. Existing pipeline verification PASS does not automatically approve the new export/UI slice.
2. Build one synthetic bundle and working S1-S4 viewer. Clearly label synthetic data and keep it out of performance claims. Test the export/view contract and no-forecast states.
3. Integrate one development race from canonical B0/B1 pipeline artifacts, with valid provenance and no protected-final reads. Verify a regenerated bundle is reproducible and browser state matches artifacts.
4. Extend to more published development races and optional selected learned-model artifacts, preserving the same Explorer UX. Final evaluations remain locked until their separate protocol requirements are met.
5. Review and authorize public publication separately. No complete 55-race catalogue, advanced-model result or performance benefit is promised before evidence exists.

Acceptance scenarios:

- S1 lists only released sessions; correct race/driver/L0 selection, back navigation and empty/retry behavior.
- Select L20: display future in-laps starting at21, exact exported window/masses/full distribution; current compound/age/status remain as-of facts.
- Toggle eventual outcome: snapshot and as-of-state identities/digests unchanged; exact/bounded/no-event/indeterminate/defective outcomes clearly differentiated; partially overlapping bounded outcomes never receive a definite window hit/miss.
- Traverse failed checkpoint: no carry-forward forecast, interpolated probability or missing gap concealment.
- Driver change: retain race time, select latest recorded attempt no later than that time, and label an older or unavailable forecast; tower/map share race time while the forecast retains its own boundary.
- Evolution: no later snapshots before their selected checkpoint, no joins across gaps, no conflation of episodes/events after a stop.
- S3/S4 preserve context and keyboard focus in user language. Required evidence assumptions and technical identities remain in research reports/artifacts, not product fields.
- Export rejects malformed/unsupported bundles and any protected final data; a UI-only hidden asset cannot pass the release gate.
- Shared URLs restore the exact immutable bundle and checkpoint; outcome visibility defaults off; missing version gives a precise error.
- Desktop/tablet/mobile inspection: no clipping, readable charts, accessible value alternative, touch/keyboard operation and dark/reduced-motion support.

## 7. Review and validation

Independent scoped review required under `governance/REVIEW_POLICY.md`; record findings and at most one bounded re-review if needed. Product Owner validation still required for the proposed experience and stack. Mockups in the accompanying PDF are synthetic illustrations, not live or trained-model results. Until both review and validation are complete this artifact is not an implementation approval.

## 8. Technical sources

Official documentation checked 2026-10-12. These support capability descriptions; the recommended combination is project-specific judgment.

- React with TypeScript: https://react.dev/learn/typescript
- Vite static deployment: https://vite.dev/guide/static-deploy.html
- D3/React integration: https://d3js.org/getting-started
- PyArrow/Parquet: https://arrow.apache.org/docs/python/parquet.html
- Pydantic JSON Schema: https://docs.pydantic.dev/latest/concepts/json_schema/
- Blazor WebAssembly hosting: https://learn.microsoft.com/en-us/aspnet/core/blazor/host-and-deploy/webassembly/
- Vitest: https://vitest.dev/guide/
- pytest: https://docs.pytest.org/en/stable/
- Playwright: https://playwright.dev/docs/writing-tests
- Streamlit client/server architecture: https://docs.streamlit.io/develop/concepts/architecture/architecture

## Independent review record

- Reviewer: `/root/review_explorer_spec`, independent of authoring.
- Date: 2026-10-12.
- Full scoped review: PASS with one Minor clarification on bounded outcome/window overlap.
- Bounded re-review: PASS after explicit contained/disjoint/partially overlapping treatment and acceptance coverage. No Blocking, Major or outstanding Minor findings.
- Scope: the Replay Explorer specification and product/decision amendments, against the approved pipeline semantics and user-selected direction. Rendered PDF layout is separately verified.
- Detailed UX and technology choices remain proposed for Product Owner validation; this review does not authorize implementation or deployment.
- GitHub review reference: draft PR #47, review `5490099069`, on substantive remote head `faef2ac9a3633d74c50961b3e749f81af95e10cb`.


## 9. Visual/copy revision, 2026-10-12 - review status

Independent review PASS after two localized copy/navigation corrections; bounded re-review and all eight rendered mockup pages passed. Reviewer: /root/review_ui_restraint. No Blocking, Major or required Minor findings remain. Non-blocking About wording and mobile-control-caption observations were incorporated. Default replay is reduced to driver/lap identity, a pit window and one compact strip preserving all four required masses. The full distribution stays available on request. Internal copy and implementation identities are removed from product surfaces; research provenance/report obligations remain unchanged. The previous review record covers the original draft, not this delta.

Review aids: https://standoutmcp.io/guides/fix-vibe-coded-ui-checklist and https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c . No checklist score or aesthetic guarantee is claimed.

Asset registry: [REPLAY_EXPLORER_ASSETS.md](REPLAY_EXPLORER_ASSETS.md). Rendered PDF checked on all eight pages; no clipping or off-page characters. Review is design validation only; Product Owner approval remains required before implementation.


## 10. Requested race-timing extension

The Product Owner requested timing tower and track-position context on 12 October 2026, using existing F1_Telemetry_Charts information/interaction decisions. [REPLAY_TIMING.md](REPLAY_TIMING.md) proposes the detailed extension and owns its shared-clock/selection behavior. It supersedes earlier exclusions of track-position display and same-lap driver alignment; continuous animation and automatic playback remain excluded. S2 gains a map/tower with replacement timing tabs; the four surfaces remain. New provider/export coverage requires causal verification and protected-final gates. Detailed design remains proposed. Acceptance now includes fixed-clock subject switching with an explicitly older or missing forecast, distinct comparison selection and whole-field common-time alignment.


Product Owner validated the complete revised design and timing supplement on 2026-10-12: “Perfect I valdiate that”. Earlier proposed/approval-pending statements in historical review notes describe their review-time state and are superseded by this approval.
