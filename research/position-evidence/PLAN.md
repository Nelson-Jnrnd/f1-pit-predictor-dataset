# Bounded position milestone

Base: PR #49, published head ccace34f08461958a708074345d4949bf771526f.
Main still contains only the approved synthetic viewer. This task is stacked;
no merge, deployment, browser-verification claim, tuning or final-partition reads.

Scope: verify historical Position.z endpoint for Austria 2024 R11 under the existing
race-day archive evidence exception. Preserve the original prediction/timing bundle
and all model artifacts. No Position facts enter existing predictions or observations.
Implement a separately versioned, observation-owned race-context projection after
its scoped authority/geometry evidence passes independent review.

Use the latest defensibly published common Position sample by each existing race
boundary, never nearest/future interpolation, per-driver clock stitching, map-derived
timing order or final-race backfill. Preserve source and sample timestamps, unhealthy
windows, freshness and omissions. All marker coordinates share one sample clock and
are explicitly older when applicable.

Geometry must be independently matched to the circuit/source coordinate system and
established before race start. Inspect Austria's preceding qualifying session as a
possible static-prior source; no race-future geometry fitting or normalization.
Fail closed if authority, common samples or geometry cannot be established. Do not
expand the existing governance exception without a Product Owner decision.

Verification first: frozen source hashes and modification metadata, embedded UTC vs
validated RCM/prefix clock, sample/publication ordering, gaps and coordinate integrity,
pre-race geometry provenance, causal mutations and unchanged base predictions. Then
export/schema/map integration, appropriate tests/build and bounded independent review.
