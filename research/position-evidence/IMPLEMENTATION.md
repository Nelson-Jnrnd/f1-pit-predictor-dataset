# Austria 2024 R11 position implementation

PR #50 is stacked on open draft PR #49; neither is merged or deployed.
The existing race release, canonical predictions/model, timing and outcomes are
unchanged. Base release SHA-256:
`adee41e48e21c96240a66ecbc901c129aa158c6ac96e9ed2e2a4c04ed96227a7`.

The optional PositionContextBundle contains 1,405 exact time/order boundaries,
with coordinates in 1,205 frames. All coordinates at each boundary come from one
common reported UTC sample, defensibly published before T. Samples are older and
labelled approximately; maximum latest-possible age is 20 seconds. Invalid,
out-of-corridor, unavailable, unknown/sample-time pit or ambiguous-transition
coordinates are omitted. All participants remain in the tower. Geometry is fixed
from the preceding matching qualifying session, with no race-future fitting.

`pipeline.positions release` reproduces approved scoped evidence from frozen inputs,
verifies immutable base/observation owners and emits the sidecar and hash descriptor.
The browser verifies base and sidecar hashes, authority status and exact joins. It
does not predict or infer positions. Sidecar absence/error preserves base forecasts
and timing with a positions-unavailable notice.

Comparison clicks/keyboard selection remain separate from the prediction subject.
Subject switching and outcome toggles preserve the field clock and position frame.
Sector/minis and unsupported information remain unavailable. No CSS/layout change.

## Validation

- 32 Python tests pass, including causal margins/ties, future mutations, lapped
  timing, failed predictions, common samples, freshness, gap recovery, missing
  coordinates, sample-time pit transitions, protected guards and base isolation.
- 25 frontend tests pass, including historical marker coordinates, keyboard
  comparison, full tower, fixed clock/subject and outcome isolation, hash-bound
  exports and candidate/protected/future/stale/unavailable rejection.
- Frontend production build passes.
- Authority full review found one Major sample-time pit defect. Bounded re-review
  PASS after repair; all 116 affected points omitted. See scoped evidence document
  and PR #50 review 5509140470.
- Independent implementation review PASS at substantive 76d298d; final production
  byte binding is checked separately before recording completion.

Desktop/mobile visual presentation and native browser keyboard/dialog interaction
remain **unverified**. The available environment lacks a usable local Chromium;
prior installation returned an invalid archive and the cloud browser cannot access
localhost. DOM keyboard tests are automated interaction coverage, not a real-browser
claim. User testing is not required to publish this reviewable draft.

Authority is internal archive consistency under the existing RA-1–RA-4 exception,
not contemporaneous capture. This scope does not approve CarData, other races,
metric positional accuracy, live feeds, autoplay, tuning or public deployment.
