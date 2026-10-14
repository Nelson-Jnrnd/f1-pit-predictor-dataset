# User review implementation: 14 October2026

Delivered on draft PR52, stacked on PR51/50/49. No merge or deployment.

## Early forecasts

The frozen Spain2024 R10 baseline has empirical at-risk support at offsets0–36;
offset37 and the40-tail have no training support. An Austria forecast at lapL has
K=71−L regions and needs closed offsets0 through69−L. L32 requires37; L33 requires
only0–36. Every released driver has its first successful forecast at lap33.

659 attempts fail training support;20 fail timing availability;746 are genuine
successful forecasts. These states remain selectable and unchanged. No crop, extra
floor, guessed hazard, browser prediction or future-outcome backfill was introduced.
The main unavailable state explains the single-earlier-race training limitation.
Earlier forecast coverage requires separately approved development/training work.

## Portraits and context

Only VER/NOR/HAM were originally bundled. All20 Austria2024 images now decode and
match the previously approved reference cache at ae3485d695f07137f6778e03c3437ca1464fb7df.
ASSETS.json records hashes/pinned paths and About retains Formula1 credits. Source-keyed
portrait/fallback state replaces sticky DOM hiding; failed image→new driver works
without refreshing. Missing images still have a readable fallback.

Timing precedes the secondary map in reading/keyboard order and receives more width.
Rows use aligned tabular figures, m:ss lap durations, readable code/colour rails,
compact named forecast actions, sticky headers and local mobile scrolling. All tabs
and participant rows remain. A canonical position1 is labelled Leader in absolute
mode; no zero gap is inferred, and relative null values remain unavailable. Race
clock stays visible on mobile. Comparison never selects the prediction subject.

Native testing exposed an inherited pan bug: queued React updates read a drag ref
that the handler had already changed/cleared. Stable captured deltas, an explicit
background surface and marker exclusion now preserve both pan and comparison.

## Validation and review

Substantive validated head:713b704e0e55032762f63709fea5098be5758507.
CI run:[38535453980](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/actions/runs/38535453980).
32 Python tests;30 frontend tests;frontend build pass. Native Windows and Linux
frontend jobs pass. The added batched-pointer test checks cumulative pan and marker
exclusion; portrait tests cover failed→successful source changes and full roster.

Actual Edge153.0.4234.48 passed private-localhost browser checks: all20 images,
forced missing-image recovery, table Enter comparison, independent forecast action,
modal Escape/focus return, unchanged clock/coordinates on outcome toggle, zoom,
rotate, fit, pointer panning, desktop table fit and390px viewport without page
overflow. Captures are in browser-checks: desktop light/dark and mobile timing/map.
The report and screenshots are unedited outputs from CI artifact11879078846,
ZIP SHA256cdf66b80cafabeec37b2e9836236be0df8291901259dafbd536e4e2da23ebd94.

Independent review by /root/review_development_replay: bounded completion PASS;
[review5515182322](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/pull/52#pullrequestreview-5515182322).

Canonical public release, positions, source/model and outcome artifacts are byte
identical to PR51. No protected-final opening, model tuning, live feed or deployment.
Physical handset/touch behavior and other browser engines remain unverified;390px
mobile captures are emulation in a real Edge browser.
