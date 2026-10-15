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

Historical coordinates are a separate hash-bound sidecar for Austria 2024 R11.
All displayed cars share one defensibly published common sample; the map explicitly
labels its age. Matching geometry comes from the preceding qualifying session,
fixed before race start. No interpolation or race-future fitting is used. Unknown,
invalid, off-corridor and sample-time pit positions are omitted; all 20 cars remain
selectable in race timing. Sector/minis remain unavailable. See
`verification/POSITION_AUSTRIA_2024.md` and `research/position-evidence` for the scoped
archive authority, inherited assumptions and limitations. Missing or rejected
position exports leave the original timing and forecast bundle usable.

Clock navigation preserves equal-prefix source publication order as well as elapsed
race seconds. Subject switching retains the field-wide instant and selects its latest
recorded attempt, including failure. Comparison clicks never select the subject.
Outcomes default off and do not alter timing or forecasts. The previous approved
synthetic fixture remains for regression tests; it is not offered as a real race.

Images retain the credits and rights in `ASSETS.json` and
`design/REPLAY_EXPLORER_ASSETS.md`. Missing portraits use readable name/team fallbacks.
No photographic publication authorization is inferred. Browser visual/keyboard checks
remain unverified in this environment; see the implementation review record.

### Windows checkout

Hash-addressed JSON releases preserve their published bytes via `.gitattributes`.
Git CRLF conversion changes the SHA-256 even when JSON values are identical, so an
older Windows checkout can reject the positions or entire replay. Keep integrity
checks enabled. To refresh only the shipped JSON fixtures from Git, run from the
repository root (this overwrites local changes to these generated files):

```sh
git -c core.autocrlf=false checkout-index --force -- explorer/public/development.json explorer/public/release.json explorer/public/positions.json explorer/public/positions-release.json explorer/public/synthetic.json research/position-evidence/candidate.json
```

Then run `npm test` and `npm run build` from `explorer`. No global Git configuration
change, source refresh or prediction regeneration is required.

### User-review refinements

All20 Austria2024 portraits are bundled with source/hash credits. Image failure
uses a readable fallback and cannot hide a different driver's next portrait.
Timing leads the race-context layout; comparisons, prediction actions and the
single race clock remain separate. Early failures are frozen training-support
limitations; genuine forecasts first appear at lap33 in this release.

On Windows with Edge installed, `npm run test:browser` runs the real-browser checks
against private localhost and writes desktop/mobile captures to browser-checks.
See research/replay-readability/REPORT.md for validated head, CI/review references,
immutable-data checks and remaining physical-device/browser limitations.
