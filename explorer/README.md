# Replay Explorer

Local historical preview: Austria 2024 R11, B0 fitted on Spain 2024 R10. This is an
engineering preview, not evidence of model quality. No public deployment is authorized.

```sh
npm ci
npm run dev
npm test
npm run build
```

If this environment cannot enumerate network interfaces, use
`node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173` instead.

The app verifies the release SHA-256 before accepting the static bundle. Forecasts
come from the offline Python pipeline; the browser never fits or predicts. Research
provenance, reproducible sources/artifacts and limitations are under
`research/development-race`. See `pipeline/README.md` to regenerate a fresh local run.
The early B0 training-support gaps remain selectable failures, not fabricated tails.

Position availability and matching coordinates are not established by the approved
source matrix: the map shows the 2024 Red Bull Ring outline with an unavailable notice
and no invented car markers. All 20 cars remain selectable in race timing. Sector/minis
values are explicitly unavailable. Missing tyre ages and pit states are not zero/false.

Clock navigation preserves equal-prefix source publication order as well as elapsed
race seconds. Subject switching retains the field-wide instant and selects its latest
recorded attempt, including failure. Comparison clicks never select the subject.
Outcomes default off and do not alter timing or forecasts. The previous approved
synthetic fixture remains for regression tests; it is not offered as a real race.

Images retain the credits and rights in `ASSETS.json` and
`design/REPLAY_EXPLORER_ASSETS.md`. Missing portraits use readable name/team fallbacks.
No photographic publication authorization is inferred. Browser visual/keyboard checks
remain unverified in this environment; see the implementation review record.
