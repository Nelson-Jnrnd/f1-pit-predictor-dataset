# Scoped historical position evidence: Austria 2024 R11

Status: Approved after independent bounded re-review PASS. Review: [PR #50
review 5509140470](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/pull/50#pullrequestreview-5509140470),
reviewer `/root/review_position_authority`, reviewed candidate digest
`17047e13041c218d4bd1d6d566f52378b8cbe98d9130a71e687f79cf3a948efb`.
Prior sample-time pit finding resolved; all 116 affected points omitted. This verifies only Position.z for race session 9550 (meeting 1239,
circuit 19). All other position scopes, CarData, sectors and minis stay unverified.
Consumes SUPPORT_MATRIX S-RD, OBSERVATION_RECONSTRUCTION, REPLAY_TIMING and the existing
10 October race-day archive evidence exception. This adds scoped evidence under that
exception; it does not widen the exception or change availability semantics.

## Timestamp and revision evidence

The frozen race Position.z archive retains 30 June 2024 Last-Modified. Parsing all
batches preserves publication prefixes, record ordinal and embedded UTC sample keys.
Race-time batches contain 19,356 monotonically ordered common samples, each with the
same 20 racing numbers. The maximum common-sample gap is 1.320 seconds. Prefix-derived
receipt time minus reported sample UTC lies between -0.079 and +1.941 seconds, median
0.321 seconds, against the independently validated RaceControlMessages UTC anchor.

This is supporting evidence for the common prefix recorder clock. It does not prove
contemporaneous public capture or turn sample time into availability time. RA-1 and
RA-4 remain assumptions accepted under the existing exception. Race-day revision
metadata, frozen bytes/hashes, endpoint internal clock consistency and prior-clock
health exclusions together support a scoped VERIFIED_BOUNDED_TIME verdict after
independent review. No undocumented same-stream ordering across endpoints is assumed.

Preserve the existing availability interval [P-5,P+5]. Position is cross-stream from
both timing and session-start triggers: require P_position+5 < P_trigger-5. Pre-race
facts retain the 300-second margin. Existing clock-unhealthy windows and post-Finished
boundaries are excluded. Never use the sample UTC as a substitute publication key.

## Common sample and freshness

At a recorded prediction boundary, choose the latest defensibly published common
sample, including same-sample corrections only after their own publication. All
positioned cars come from that sample's UTC key. Missing/invalid entries do not borrow
coordinates from another sample. No future/nearest-point interpolation or extrapolation.

Require latest possible sample age <=20 seconds, including the selected-boundary's
5-second bound. This policy limits historical sample staleness, not geometric accuracy.
The normal 10-second cross-stream separation necessarily makes the displayed sample
older than the timing boundary. The map labels this age approximately; it does not
claim exact car motion at T. After a clock gap, require a new admissible full sample.
No per-driver alignment by lap number or map-derived race order/gaps is permitted.

## Geometry and registration

The fixed trace comes from the preceding 29 June qualifying session, whose circuit
and meeting keys exactly match the race. Every geometry-source endpoint has a
pre-race Last-Modified timestamp. This is a static prior asset, not qualifying-time
availability authority and not a mutable qualifying field admitted into predictions.

Use the first defensibly closed flying-lap trajectory in numeric driver/lap order;
no race-future fitting, normalization or reference selection. The selected trace is
driver 1 lap 3. It retains its native points and source references. Closure is 1.336%
of traced length, under the prespecified 1.5% completeness rule. The map uses a fixed
aspect-preserving affine display transform, derived from this trace alone.

Coordinate registration is checked with race Position points published before the
strict pre-race cutoff P_start-305. Of 20,276 distinct prior-race native points, 20,150
fall within 350 native coordinate units of the qualifying trace. The matching spans
are recorded so the registration is spatial evidence, not a single arbitrary anchor.
The 350-unit corridor is a fixed display-omission tolerance, not a metric accuracy
claim. Coordinates remain in the source's native frame; no claimed metre calibration.

OnTrack is reported for all 387,120 in-race car entries and therefore does not prove
track membership. Zero/nonfinite/out-of-corridor/out-of-view coordinates and known
pit entries are omitted. Pit membership must be defensibly false at the common
sample under the cross-stream bounds; unknown or overlapping transitions are
omitted, including an entry that was followed by an exit before the later boundary.
Current-boundary known pit state provides additional omission. Facts published
after the selected boundary cannot affect the projection; gap-carried pit state
cannot establish membership. The timing tower retains every participant. Static F1DB
Spielberg-3 imagery remains catalogue identity imagery; it is not the coordinate map.

## Immutable boundaries and validation

Existing predictions, eligibility, targets, timing frames and release bytes remain
unchanged. A separately versioned observation-owned PositionContextBundle binds the
original release SHA and exact (time, publication-order) boundary set. It contains
positions, their common sample and fixed geometry only. Export refuses final scopes,
unknown authority, mismatched source/boundary owners and invalid evidence digests.

Reproduce with `python -m pipeline.positions evidence --output /tmp/evidence.json`.
The command produces candidate research evidence, not a product release. The release
mode requires an independently APPROVED evidence record reproducing from frozen inputs.
Tests exercise strict margins, ties/corrections, unhealthy continuity, common-sample
missing cars, invalid coordinates, stale samples, timezone-independent UTC, prior
geometry provenance, base-byte isolation and release gating. Browser checks are a
separate implementation gate and do not strengthen archive authority.
