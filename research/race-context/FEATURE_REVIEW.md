# Independent feature-admission review

Outcome: PASS. The registered TimingData feature extension may feed the fixed
Random Forest experiment. This approves feature admission only; implementation,
results, publication, merge, viewer replacement and final testing remain separate.

Reviewer: `/root/review_protocol`, 15 October 2026.
Reference: issue #57, PR [#58](https://github.com/Nelson-Jnrnd/f1-pit-predictor-dataset/pull/58).
Exact audit and source-verification hashes are bound in `FEATURE_REVIEW.json`.

## Evidence checked

Reviewed `pipeline/race_features.py`, `pipeline/race_feature_verify.py`, the
completed audit and metadata supplement, and all 133 feature payloads. The fixed
race list exactly matches the admitted pre-2026 partition. Independently checked
every feature payload digest, parent manifest identity, source/observation hash
reference, unique checkpoint key, row count and missing/available count.

The source verifier checked five raw-state samples per race: 665 samples total.
It independently reduces the six relevant TimingData leaves, compares them with
the immutable canonical state, verifies raw stream digests and checks each sampled
observation's causal references against same-stream order or the conservative
cross-stream availability margin. Its code and audit digests match current files.
All sampled feature values and observation identities match the derived payloads.

Three feature-boundary tests pass: unfinished/future lap values remain omitted,
future and target fields do not affect features, and lapped/invalid gaps remain
missing. No forest was fitted or scored by the reviewer. No protected 2026 source,
outcome or capability evidence was read.

There are 137,822 represented observations. Missing feature counts remain visible:

| Feature | Missing observations |
| --- | ---: |
| Latest completed lap time | 41,964 |
| Best completed lap time | 9,214 |
| Difference between those times | 43,752 |
| Timing position | 5,475 |
| Gap to leader | 27,668 |
| Interval ahead | 12,304 |

## Boundary and limitations

Feature values come exclusively from one selected immutable observation. Raw
updates are verification evidence only. The audit supplement explicitly reconciles
the broad historical positions omission with this narrow timing-tower whitelist.
Original quality is retained through immutable parent identities; no old
observation is rewritten. Coordinates, telemetry, sectors, speed, track status and
weather remain outside this extension.

All-race extraction checks are complete; raw-state checks are bounded samples,
not an exhaustive independent reconstruction of every leaf. They provide no
independent trackside truth for timing rank/gap correctness. Historical version
fidelity remains an accepted source assumption: RA-1 through RA-4 for the 39
race-day sessions, and RA-1 through RA-3 plus RA-5/RA-6 for 94 older sessions.
These limitations must accompany results. Detailed evidence remains private under
the repository's existing data-release boundary.

No Blocking or Major findings remain in this feature-admission slice.
