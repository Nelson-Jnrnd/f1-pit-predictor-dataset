# One development race: Austria 2024 R11

Implementation milestone, not deployment or a model-quality claim. B0-only preview:
Spain 2024 R10 is the sole fitting race, concluded before cutoff 30 June 2024.
B1 is not implemented. The existing P-F1 and P-F2 final partitions are unchanged.
No protected-final source or resolution was read for this implementation.

## Verified and integrated

Six raw race-day archive endpoints per race are frozen with SHA-256, retrieval time,
ETag and Last-Modified. Both actual TimingData files and the other five endpoints
retain race-day Last-Modified dates. The initial Canada candidate was rejected
because it is R9 and has a June bulk-rewrite date; it is not retained or fitted.

The approved SUPPORT_MATRIX availability exception and RA-1 through RA-4 apply.
The per-run clock artifacts reproduce lap residual and RCM anchor checks and record
clock-unhealthy intervals. This is an assumption-based historical reconstruction,
not independently captured contemporaneous availability evidence.

The pipeline produces causal canonical observations, eligibility and separate
retrospective targets, development fitting/accounting, frozen B0, replay snapshots
and failures, retrospective mappings and validated local-only release projection.
All 20 participants remain in the timing tower at one common source boundary.
Within-prefix source ordering is retained. Lapped cars keep independent completed
counts, lap gaps remain textual, comparison selection remains separate from the
prediction subject, and changing the subject retains the race clock and the latest
attempt including failures. All event-bin masses and no-event mass are exported.

The exact counts and hashes are in `run-1/manifest.json`. Expected first run:
1,425 attempts, 1,405 distinct boundaries, 746 successful full-distribution forecasts,
679 failed/indeterminate attempts. Early unsupported B0 offsets fail explicitly;
the model does not invent empirical rates for empty-risk bins. Outcomes are separately
projected and never input to observations or replay.

## Precise remaining dependencies

- Historical Position/CarData availability is `UNVERIFIED_ARCHIVE` under SUPPORT_MATRIX.
  Owner: observation/provider verification. It requires a scoped, independently
  reviewed timestamp/revision validation and a causal past-only reconstruction rule.
- Matching car-coordinate geometry has not been established. Owner: timing/export
  implementation after the provider gate. The verified 2024 Spielberg-3 F1DB outline
  identifies the Red Bull Ring layout; it does not establish a coordinate projection.
  All exported positions are null. No fictitious map markers are integrated.
- Sector/minis comparisons are omitted pending reliable completion association and
  reference/boundary coverage. Timing tabs remain usable with unavailable values.
- B1 and the full P-F1 development training block remain separate implementation work.
  This preview fits one prespecified baseline without selection or scoring. It cannot
  establish predictive quality or satisfy the final-lock experiment prerequisites.
- The target evidence does not have independent tyre-change ground truth. Unsupported
  negative visits and ambiguous terminal intervals remain indeterminate. A leader's
  finish whose cross-stream ordering is not defensible is not guessed.

## Validation and review

See `REVIEW.md` for final test counts, independent review and its bounded re-review.
Automated checks cover causal margins/ties, future corrections, complete probability
coverage/floor, cutoff and final-data refusal, immutable replay, export lineage and
content consistency, outcome isolation, lapped/older/failed attempts and no coordinates.
Frontend build is required. DOM checks do not establish actual desktop/mobile layout,
keyboard focus or native dialog behavior.

Real-browser inspection remains unverified: Chromium download returned invalid
zero-byte ZIP responses; the cloud browser returned `ERR_CONNECTION_REFUSED` for
the local server. No external deployment or tunnel was used as a workaround.
