# User review repair: 14 October 2026

Bounded scope: explain existing pre-lap33 prediction failures without changing the
model or release; complete Austria2024 portrait coverage and fix stale hidden image
state; improve race-context legibility using Formula Timer as visual inspiration.
User review authorizes presentation refinement. Preserve approved information tabs,
comparison/subject separation, shared clock, probability/outcome isolation, source
bounds and omissions. No reference layout code/assets/data copied, tuning, protected
final reads, merge or deployment.

Reference inspected: https://formula-timer.com/livetiming. Useful principles:
strong row/column alignment, readable tabular numbers, clear driver color rails,
timing-led hierarchy and a secondary map. Retain this viewer's existing light/dark
palette and information tabs; do not import the reference's additional telemetry.

Diagnosis: the frozen model has empirical risk at offsets0–36 only. Austria's
71-lap full forecast requires offsets0–(69-L), so L32 still requires unsupported37
and L33 fits supported0–36. No early forecasts can be invented; research records
and all failed attempts remain unchanged. Exactly659 attempts fail training support,
20 fail timing availability,746 succeed. First success is lap33 for all20 drivers.

Only HAM/NOR/VER portraits were bundled. Others404; onError sets persistent hidden
on the reused img node, hiding later successful pictures. Complete the season2024
roster from the previously approved pinned cache, retain SHA/source credits, and
use source-keyed image/fallback state. Explicit readable fallback remains required.

Validation: all roster PNGs decode and match pinned source; failure→successful driver
switch; baseline explanation at unchanged failed attempt; timing tab/selection/clock
regressions; frontend tests/build and native Windows CI. Independent bounded-scope
review under AGENTS; report visual browser checks actually completed or unavailable.
