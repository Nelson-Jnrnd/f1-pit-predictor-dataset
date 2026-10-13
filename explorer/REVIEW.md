# Synthetic Replay Explorer implementation review

Scope: first approved synthetic end-to-end viewer, not real-race integration or public deployment. Independent reviewer: `/root/synthetic_explorer_restart/review_synthetic_explorer`, 13 October 2026.

Full scoped review: rework required. Corrected synthetic next-stop/terminal episodes, malformed consumed-field rejection, hash Back/Forward and missing-attempt restoration, zero-probability rendering, exact/bounded outcome-bin annotations, theoretical/Race timing comparison emphasis and integer tyre-age differences.

One bounded re-review: technical PASS on the final substantive tree following `44c84f7`, including the final outcome-bin correction and its regression test. Reviewer independently verified 16 passing tests and the TypeScript/static build. No outstanding Blocking, Major or required Minor technical findings.

Qualification: real-browser desktop/mobile layout, actual keyboard/focus behavior and visual readability are not verified. Local Chromium installs (project and runtime versions) returned invalid zero-byte archives; cloud browser could not reach the local development server (`ERR_CONNECTION_REFUSED`). DOM interaction tests are not a substitute for this visual gate. Keep the implementation PR draft until browser inspection is complete; no merge/deployment approval is claimed. GitHub review reference is to be appended after PR creation by the coordinating agent.

Next dependency: integrate exactly one permitted development race only after its canonical prediction/export provenance, causal race-wide timing coverage and matched position geometry are verified. This validator intentionally accepts synthetic data only and does not perform a real/final release.
