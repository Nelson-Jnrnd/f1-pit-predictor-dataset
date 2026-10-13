# Decision: accept the synthetic Replay Explorer

Status: approved by Nelson Jeanrenaud on 13 October 2026 (Europe/Zurich).

The Product Owner accepted the implementation in PR #48 after receiving local testing instructions: “That's good I approve”. The synthetic viewer may be merged into main. Independent technical bounded re-review passed; 16 automated tests and the static production build passed, including GitHub Actions run 38390050521.

The approval is acceptance of this milestone, not evidence that every browser/accessibility scenario was exhaustively checked. Automated real-browser verification remains unperformed. No deployment, trained-model result or real/final data release is included.

Next milestone: verify causal export, full-field timing and matched position geometry for one permitted development race, then integrate it while preserving the approved UI and protected-final boundaries.
