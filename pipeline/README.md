# Offline development replay

This implements the bounded B0-only engineering preview approved by
`design/REPLAY_EXPLORER.md`. Python 3.12, standard library only. No live feed,
model selection, tuning, score, final evaluation or public deployment support.
The preview is not a P-F1 validation fold; that protocol requires 15 training races.

From repository root:

```sh
python -m pipeline.development --output /tmp/new-replay-run --bundle /tmp/development.json
python -m unittest discover -s pipeline/tests -v
```

The output directory must not exist. Each execution gets a new replay identity.
The regenerated bundle and `release.json` can be copied into `explorer/public` for
local viewing after review. Artifact references and the bundle hash change across
runs; the frozen model's request digests and probability vectors reproduce exactly.
No raw acquisition occurs during execution: the two frozen source snapshots under
`research/development-race/sources` are checked against their acquisition manifests.

Boundary ownership is explicit in `development.py`:

- `read_source`, `clock_evidence`, `reconstruct`: approved S-RD endpoint authority,
  ±5 s bounds, strict cross-stream separation, same-stream ordinal, pre-race margin,
  clock-health omissions and complete recorded-attempt enumeration.
- `initialize`: causal eligibility only; a stopped car is uncertain, not a retirement
  inferred from the future. No retrospective input is accepted.
- `retrospective_catalog`, `resolve`: separate target-owned tyre-service and terminal
  evidence. Only confirmed positives qualify. Unsupported negative/penalty visits,
  gaps and ambiguous terminal relations truncate. No eventual event is an input
  to initialization or prediction.
- `fit_b0`: ledger-first development join and pooled B0 hazards, fitted only on Spain
  2024 R10 before the Austria cutoff. Empty-risk offsets remain unsupported and
  cause prediction failures, not arbitrary tail probabilities. PMF floor is 1e-6.
- `replay`: canonical observation/initialization/frozen-model inputs only, exhaustive
  attempts, immutable distributions and failures, no outcome references.
- `retrospective_join`: separately permitted development mappings for opt-in display.
- `export`: content digests and exact joins, canonical grid/full PMF/window checks,
  development-only allowlist before any source read or release, null unverified
  coordinates, preserved missing facts and no model weights in the viewer bundle.

All clocks are source-prefix seconds relative to official start. Equal prefix times
retain source publication ordinals in the exported `order` and shared-link field.
They are not rounded into one instant or ordered by driver position. All frame rows
come from the same boundary's canonical state. Invalid-clock attempts retain the
recorded source time for navigation with `boundaryAvailable: false`, no represented
race state and an explicit uncertainty notice; it is not a prediction-time assertion.

Per-source manifests preserve hashes, URL, retrieval metadata, adapter and revision
scope. Per-run manifests preserve code revision, artifacts and release hash. Durable
`ledger-openings.jsonl` records openings before joins; failures do not erase them.
The implementation is intentionally bounded to the two frozen sources. Unsupported
restart histories, lap jumps, roster mismatches, corrupt inputs and ambiguous
cross-stream boundaries fail closed, rather than imply general corpus coverage.

Historical positions are optional observation context, never model inputs. Generate
research evidence with `python -m pipeline.positions evidence --output /tmp/evidence.json`.
Only independently approved, reproducing evidence permits
`python -m pipeline.positions release --output explorer/public/positions.json`.
The sidecar binds the unchanged base release and exact boundary keys. Common-sample
pit membership must be defensibly false; uncertain transitions and gap-carried
states are omitted. No CarData authority or additional race coverage is implied.
