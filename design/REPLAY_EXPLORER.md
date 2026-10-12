# Replay Explorer - proposed UX and delivery specification

## Status and scope

**Proposed - awaiting Product Owner validation.** Replay Explorer as the sole interface direction is already approved in `decisions/2026-10-12-v2-replay-explorer-direction.md`. Screens, interactions and recommended technologies below remain proposals. No production implementation or deployment is authorized by this artifact.

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
| S3 | Prediction-details drawer | Explain the selected snapshot and data gaps | S2 Details; Close/Escape returns to unchanged S2 |
| S4 | Methodology and replay-context panel | Explain target meaning, published model and evidence limits | About in S1/S2; Close/Escape returns to invoking view |

S3 and S4 are overlays, not extra dashboard pages. Mobile layouts and no-forecast/error states are variants of these four surfaces, not additional features. The catalogue is the landing page; do not add an introductory home page or guided story.

### S1 - Race catalogue

- Header: application name, short purpose statement, About.
- One Season selector; only seasons with published bundles appear. Within a season, rows ordered by official round. No search field or additional filters in V1.
- Each row: race name, date, number of driver entries, published-model label and Open replay. A single caption explains that only published replay sessions are listed.
- No fake availability for all supported raw-data races: the verified 55-race scope is not a promise that 55 replays already exist. Unsupported or protected sessions are absent from the public catalogue and build, not disabled rows with downloadable hidden data.
- Opening selects the first canonical roster entry (numeric racing-number order) at race-start checkpoint L0. If that checkpoint has no forecast, show its explicit state; do not jump silently to the first successful forecast. Driver names are display labels; stable session/racing-number keys identify entries.
- Empty catalogue: no published replays yet; no invented sample result. Fetch failure: plain error and Retry.

### S2 - Replay workspace

**Top-level hierarchy:** race/driver context; checkpoint navigation; next-stop forecast; optional prediction-history expansion. Keep repository identifiers and caveats in S3/S4.

Header: Back to races, race name, Driver selector, published-model label, About. If a driver is absent in the same race URL, explain the unavailable selection rather than substitute another silently.

Checkpoint navigation: selected driver's completed-lap count, Previous, Next, full driver checkpoint slider and a keyboard-operable lap value. L0 is Race start; L20 means information available at lap-20 completion, forecasting entry in lap21 onward. The slider enumerates recorded CHECKPOINT attempts, including attempts without valid forecasts; it neither interpolates nor synthesizes missing snapshots. Explicit enumeration gaps are visible and not filled. SESSION/DRIVER_ENTRY failures are race/entry-level notices and are not fabricated lap checkpoints. Previous/Next stop at the ends.

At race changes, driver and checkpoint reset explicitly to the default roster entry/L0; outcome visibility resets off. At driver changes, choose that driver's same completed-lap ordinal if it exists. Otherwise use its closest earlier recorded ordinal (or L0 if none earlier), announce the actual checkpoint chosen, and retain outcome visibility off. Driver laps are independent; never label this operation as common-time race-wide alignment.

**Forecast panel:**

- Window label uses exported `PitWindowSummary`: e.g. Likely next-stop window: laps24-27. If it includes the open final region, show the final bound as 'lap57 or later', never a closed interval.
- Four directly labelled masses are always available: before window, inside window, after window, no further qualifying stop. Display absolute probabilities; identify the default window as containing at least 80% of event probability, not an unconditional 80% chance.
- Complete canonical event distribution in a bar chart, x axis = selected-driver in-lap, y axis = probability %. No-event is a separately labelled bar/quantity. Full remaining scope is available by default, ending with the open final bin. Long grids use readable ticks; any optional presentation grouping preserves summed mass and exposes constituent bins on inspection. No silent fixed-horizon crop, normalized event-only curve, tail loss or invented final lap.
- Native-focusable chart targets or an equivalent numeric table make values accessible without hover; touch selection gives the same value. Colour does not carry meaning alone.
- Compact state facts: compound, tyre age and track status, only if legitimately present in the selected canonical observation. Unavailable optional fields show Not available at this checkpoint. Do not source them from processed final lap rows. Historical truth from #19 never fills this area.
- q=1 / P_event=0: No future qualifying stop predicted; Window none; preserve zero event masses. This is valid output, not a missing prediction. Any zero-probability display allowed by the contract is distinguished from the evaluation protocol's floor requirement.

**Retrospective outcome comparison:** off by default. Toggle Show eventual outcome reveals only the selected episode's published resolution from the permitted backtest projection: observed tyre-service entry (exact in-lap or supported range), terminal no-event, or unresolved outcome. Truncated truth remains 'Outcome cannot be established', with no stop/no-stop guess and no score. Mapping defects are labelled 'Comparison unavailable' and never evaluated as an ordinary miss. The forecast and as-of state remain byte/content-identical when toggled.

The outcome is labelled Retrospective and separated from the causal state. When exact, its chart marker is at the matching exported region, not at an inferred rounded clock time. Set-valued mapping shows the full range. For comparison with a window, label it Fully inside, Fully outside, or Partly overlapping according to set containment/intersection; partial overlap is not a definite hit or miss. An exact entry outside the window, or a supported range entirely disjoint from it, is outside the window. A range contained in it is within the window. Partial overlap says: Outcome range overlaps the window; hit/miss cannot be established. A window miss is not a failed normalized forecast. No 'correct prediction' badge or strategy-optimality wording.

**Prediction evolution (collapsible):** show saved window intervals for the same driver and model at earlier checkpoints up to the selected checkpoint only. Each is its own immutable target episode, even when several resolve to the same stop. No line across unavailable checkpoints; use gaps and status labels. Clicking a row selects that exact checkpoint. Outcome annotations appear only while retrospective visibility is enabled. After a stop, later eligible snapshots can concern a new next-stop question; do not align their windows to the old event or infer a single episode across all laps.

No per-race model score, calibration dashboard or cross-model chart in S2. S4 may link to an existing published evaluation report without inventing a new report UI.

### S3 - Prediction details

Drawer header: driver, completed-lap checkpoint, Close. Groups:

1. Forecast interpretation: complete distribution, window rule/alpha and before/inside/after/no-event masses.
2. State availability: displayed fields and omissions with plain-language reasons; as-of reconstruction boundary and quality state. Technical availability bounds can be expanded, not presented as exact acquisition time.
3. Identity: immutable snapshot id, observation id, target episode id and published model/version, using shortened display and full copyable values.
4. Comparison: resolution/mapping state and its lineage only when Show eventual outcome is on. No future information leaks through closed details or hidden state areas before the user opts into retrospective viewing.

For a missing forecast, Details shows the attempt/failure reason and available provenance, never a fabricated snapshot id. No raw-file explorer, edits or recomputation. Escape closes; focus returns to opener; content is scrollable; narrow screens use a full-width sheet.

### S4 - Methodology and replay context

- What is predicted: next tyre-service pit entry after the checkpoint, with explicit probability of no further qualifying stop before participation ends.
- How to read the window and full distribution; definition of completed-lap checkpoint and final open bin.
- Selected race bundle, model/procedure label, replay id, observation/target/prediction contract versions, export schema version and source snapshot references; if opened from catalogue, only app-level context is shown.
- Evidence-exception reference and residual assumptions RA-1..RA-4; state that archive availability authority rests on the approved exception. Exact details and repository references expand on demand.
- Publication role: Development replay or Completed final evaluation, carrying actual `ledger_role`, `analysis_class` and qualifiers whenever evaluation results are linked. A development replay is not advertised as final evidence.
- Reproducibility links to the repository revision and existing published evaluation report only if available. No training controls or editable methodological settings.

## 3. Exceptional and responsive states

| State | Viewer behavior |
| --- | --- |
| Bundle loading / failed download | Skeleton then Retry; preserve selection; no sample result substitution |
| Unknown URL race/driver/checkpoint | Specific unavailable-selection message; Back to races; offer recorded checkpoints without silently changing the request |
| No canonical observation / uncertain eligibility / ineligible | No forecast panel; reason and Details; checkpoint remains selectable |
| Prediction failure, including missing scheduled distance | Forecast unavailable; reason; never carry the previous forecast forward |
| Valid prediction, indeterminate target | Forecast remains visible; opted-in outcome panel says unresolved; not scored |
| Defective comparison / missing mapping | Forecast visible if valid; comparison unavailable; no success/miss score |
| Optional state omission | Not available at this checkpoint; never blank=zero |
| Retired/finished driver | Render recorded checkpoint states only; no artificial forecasts after terminal participation |
| Invalid schema/hash/probability normalization | Refuse affected bundle with a data-error message; do not repair probabilities in the browser |

Responsive proposal: desktop >=1024px uses forecast + narrow context column; tablet 640-1023px stacks context; mobile <640px stacks controls/forecast/state and uses full-width details sheets. At 360px the chart retains readable labels and all information, using an accessible numeric table when needed. Controls have useful touch targets; charts are not shrunk until labels become illegible. Prefer light appearance with system dark support; colour mapping remains consistent. Respect reduced-motion; essential information never depends on animation.

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
- Driver change: preserve ordinal only if recorded; otherwise announce fallback; no claim of shared race time.
- Evolution: no later snapshots before their selected checkpoint, no joins across gaps, no conflation of episodes/events after a stop.
- S3/S4 preserve context, keyboard focus, exception assumptions and technical identities without crowding S2.
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
- GitHub review reference: to be attached to the draft specification PR.
