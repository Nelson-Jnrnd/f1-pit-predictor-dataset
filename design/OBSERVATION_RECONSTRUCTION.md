# V2 Point-in-Time Observation Reconstruction and Provenance

## Status

Draft — Issue #18, branch `design/observation-reconstruction`.

## Abstraction level

Detailed data design — historical source evidence, information-time reconstruction, canonical technical identities, normalized-fact boundaries, observation artifacts, correction handling, quality states, and provenance.

This artifact does not define target reconstruction, target-episode internals, model features, probability-output parameterization, metrics, temporal train/test policy, live ingestion, or production implementation.

## Issue / branch

- Issue: #18 — `Design — point-in-time observation reconstruction and provenance`
- Parent: #16
- Upstream architecture: #17 / `design/SYSTEM_ARCHITECTURE.md`
- Branch: `design/observation-reconstruction`

## Outcome

V2 reconstructs each historical observation from **source-ordered evidence**, not from a final lap row truncated by lap number.

For the historical FastF1-backed workflow, the preferred information-time evidence is the archived F1 live-timing `jsonStream` record envelope: source-stream timestamp plus record order. Processed FastF1 views and the repository's existing lap CSVs remain useful evidence and validation material, but they are not authoritative proof of what was available at a prediction instant when their construction has merged, aligned, corrected, or finalized information.

The canonical transformation is:

```text
immutable source snapshot
    -> raw source records with source order
    -> normalized facts with separate effective and availability evidence
    -> as-of reduction at one canonical checkpoint boundary
    -> immutable canonical observation + provenance/quality record
```

A fact is admitted only when its availability is defensible at or before the selected driver's prediction boundary. Ambiguous ties, final-only historical values, and later corrections are never silently backfilled.

## Upstream locks consumed unchanged

This design consumes and does not redefine:

- `contexts/RACE_OBSERVATION_STATE.md` — official start and driver-relative completed-lap checkpoints, prediction instant, availability-time information boundary, partial-lap legality, common-time race-wide alignment, correction semantics, and immutable observations;
- `design/SYSTEM_ARCHITECTURE.md` — observation reconstruction is causally upstream of target eligibility/resolution and produces immutable observation artifacts; retrospective target truth is outside its dependency closure;
- `contexts/WAVE1_SEMANTIC_INTEGRATION.md` — information-time reconstruction must establish defensible provider/source ordering and use conservative treatment where availability/correction history is ambiguous;
- `contexts/CONTEXT_MAP.md` — Race Observation / State remains the semantic owner of prediction-time availability; this design implements rather than changes that meaning;
- `decisions/2026-09-08-v2-project-direction.md` — predictive next-pit timing, historical replay/backtesting first, no strategy recommendation/optimization, and no initial live commitment;
- `legacy/THESIS_EVIDENCE.md` — thesis-era source behavior is evidence only and is not V2 authority.

No target truth, event qualification, future pit identity, resolved outcome, model result, or evaluation result is an input to observation reconstruction.

## Evidence inventory

### Repository evidence inspected

The current repository persists lap-level CSV files under `data/<year>/`. A representative current file contains fields such as `LapStartTime`, `LapNumber`, `LapTime`, `DriverNumber`, tyre/stint state, track status, driver-ahead/gap values, `PitStatus`, position/gaps, total laps, and weather. It does not preserve a raw source-record identity, cross-stream source order, correction/supersession history, or one availability timestamp that applies coherently to every value in the row.

The approved legacy evidence record documents the later visible extraction implementation on historical branch head `fe5abd65acd335c05a472db1e5a45bdbe8cac5b9`. That extractor:

- calls `fastf1.core.api.timing_data(session.api_path)` and merges parsed timing-lap and timing-stream values;
- joins the resulting timing values to `session.laps` by driver and lap number;
- samples `DriverAhead` / `DistanceToDriverAhead` from telemetry during a one-second window after `LapStartDate`;
- backward-as-of joins weather to `LapStartTime`;
- derives `PitStatus` from lap-level `PitOutTime` / `PitInTime`;
- carries completed-lap fields such as `LapTime` together with start-of-lap telemetry/weather;
- computes legacy `TotalLaps` from the maximum observed lap number for the extracted race.

Therefore the legacy CSV row intentionally mixes facts with different temporal meanings. It cannot be promoted to a V2 point-in-time observation merely by choosing or shifting a row.

Stable evidence reference:

- `f1_pit_predictor/extraction.py` at historical commit `fe5abd65acd335c05a472db1e5a45bdbe8cac5b9`.

### Current provider implementation evidence inspected

For this design, FastF1 upstream was inspected at commit `227cf301fb4bcf1705bcb1866de1fe5dbcef6071` (2026-08-28). This is provider implementation evidence, not a dependency version commitment.

FastF1's current source exposes F1 live-timing endpoints including:

- `SessionInfo.jsonStream`;
- `DriverList.jsonStream`;
- `SessionStatus.jsonStream`;
- `TimingData.jsonStream`;
- `TimingAppData.jsonStream`;
- `TrackStatus.jsonStream`;
- `WeatherData.jsonStream`;
- `RaceControlMessages.jsonStream`;
- `CarData.z.jsonStream`;
- `Position.z.jsonStream`;
- `LapCount.jsonStream`.

FastF1's `fetch_page` implementation preserves `jsonStream` line order and separates each line into the leading source timestamp and parsed payload. This provides stronger historical information-order evidence than a postprocessed lap dataframe.

FastF1's time documentation states that `SessionTime` is provided by the F1 live-timing API and shares a session-level reference across data streams. It also states that lap `Time` marks when a lap was set/finished, while `LapStartTime`, sector session times, and pit times are additional calculated timestamps whose millisecond accuracy cannot be verified.

Crucially, FastF1's processed lap construction may align driver lap timestamps using gap information, and `Session.load` may mix multiple endpoints to correct errors or add information. Therefore **processed `Session.laps.Time` is an effective/reconstructed lap-end timestamp, not the V2 availability authority**.

Stable upstream evidence references:

- `theOehrly/Fast-F1` `fastf1/_api.py` at `227cf301fb4bcf1705bcb1866de1fe5dbcef6071` — endpoint map, `fetch_page`, timing parsing, and lap alignment;
- `theOehrly/Fast-F1` `fastf1/core.py` at the same commit — `Session` source views and note that loaded data may be mixed/corrected;
- `theOehrly/Fast-F1` `docs/data_reference/time_explanation.rst` at the same commit — SessionTime and lap-time semantics.

## Source classes and V2 authority

| Source class | Concrete examples | What it proves | V2 use | Limitation |
| --- | --- | --- | --- | --- |
| Raw ordered live-timing stream | `TimingData.jsonStream`, `SessionStatus.jsonStream`, `WeatherData.jsonStream`, etc. | Source publication timestamp and within-stream record order; payload version observable at that source point | Preferred basis for mutable point-in-time facts and checkpoints | Historical archive is source-publication evidence, not local network-receipt latency; cross-stream ties do not have a shared sequence |
| Raw high-frequency streams | `CarData.z.jsonStream`, `Position.z.jsonStream` | Source record order plus telemetry/position sample content | Optional partial-lap/race-wide state when available | Large; provider parser may interpolate/merge if using processed views; raw record lineage must be retained |
| Processed FastF1 session views | `Session.laps`, `session.weather_data`, `session.track_status`, `session.race_control_messages`, telemetry objects | Useful effective/event values and validation against provider parser | Validation, normalization assistance where it does not destroy source lineage, and static metadata | May mix endpoints, calculate timestamps, align laps, or expose final corrected state; cannot alone prove earlier availability |
| Legacy repository CSVs | `data/<year>/*.csv` | Thesis-era derived lap-level values | Historical comparison, migration checks, evidence | Mixed temporal semantics; no raw record order/revision history; not canonical V2 observation input |
| Static acquisition/session metadata | requested year/round/session plus verified session metadata | Stable session addressing and descriptive aliases | Technical identity/provenance where not outcome-derived | Display names/track names are not canonical IDs; final race results cannot be used as dynamic state |
| Final-only or reconstructed historical value | final classification, postprocessed corrected lap row, legacy `TotalLaps=max(observed lap)` | Retrospective truth only | Audit/validation if explicitly separated | Not proof that the value was knowable at an earlier prediction instant |

## Historical source snapshot contract

A V2 reconstruction run starts by freezing the source evidence it uses. Re-fetching the same historical session later may return changed provider/archive content, so a URL or FastF1 call alone is not reproducibility.

The logical `SourceSnapshotManifest` must record, at minimum:

- canonical race-session key;
- provider/source family;
- acquisition mode, including `historical_archive` versus any future live capture;
- provider API path/session locator;
- each endpoint/stream included;
- exact payload/content hash or equivalent immutable content identity per endpoint;
- record count and first/last source timestamp where applicable;
- retrieval timestamp;
- FastF1/provider-adapter version or source revision used to obtain/parse the data;
- completeness status and known gaps/errors per endpoint;
- repository/code revision and reconstruction-run identity.

Exact serialization and hash algorithm belong to implementation. The design requirement is that source content used by a run is immutable and independently identifiable.

### Required versus optional source evidence

To emit an ordinary canonical observation, the reconstruction must be able to establish:

1. a stable race-session identity;
2. a stable driver-entry identity;
3. the canonical checkpoint occurrence as an observable source update; and
4. a defensible prediction information boundary for that checkpoint.

Race-wide, environmental, tyre, telemetry, or other state domains may be partially unavailable. Missing optional domains produce explicit omissions rather than causing the reconstruction to invent values or discard an otherwise valid checkpoint.

For the initial FastF1-backed design:

- the race-start checkpoint is sourced from the ordered `SessionStatus` stream transition that marks the official session start;
- driver lap-completion checkpoints are sourced from the ordered `TimingData` stream update in which that driver's official completed-lap count first advances to the checkpoint lap;
- `DriverList` and/or the timing stream provide driver-entry evidence;
- other streams enrich the as-of state only when their availability is admissible under this design.

The exact provider token used to identify the start-state transition and representative edge cases must be covered by the later verification baseline. Scheduled start time is not a fallback for an unobservable official-start update.

## Canonical technical identities

### Race session key

The canonical race-session identity is a structured key:

```text
RaceSessionKey = (
    series = "F1",
    season,
    round_number,
    session_kind = "RACE"
)
```

`season` and `round_number` come from the acquisition/session selection and must be cross-checked against provider session metadata. A provider meeting/session key and FastF1 `api_path` are retained as provenance aliases when available.

Event name, circuit/location, team name, and display strings are descriptive metadata only and must not be used as the canonical key.

If the selected year/round/session cannot be reconciled with the loaded provider session, reconstruction fails identity validation rather than falling back to a name match.

### Driver entry key

Within a race session:

```text
DriverEntryKey = (RaceSessionKey, racing_number)
```

The racing number must be evidenced as a unique entry in the selected session by the source roster/timing data. Provider-specific driver IDs may be stored as aliases. Abbreviation, surname, display name, or team name are never sufficient canonical keys.

Missing or non-unique racing-number evidence produces an identity failure.

### Checkpoint key

```text
CheckpointKey = (
    DriverEntryKey,
    checkpoint_kind,
    completed_laps
)
```

where:

- `checkpoint_kind = RACE_START` and `completed_laps = 0`; or
- `checkpoint_kind = LAP_COMPLETION` and `completed_laps = L > 0`.

A duplicate source update for the same completed-lap count does not create a second semantic checkpoint.

### Semantic observation key versus artifact identity

The stable semantic key identifies the driver's checkpoint. The persisted observation artifact has a separate immutable artifact identity tied to the exact source snapshot and reconstruction version.

This distinction permits a later corrected source snapshot or reconstruction policy to produce a new observation artifact for the same semantic checkpoint without overwriting historical runs.

Downstream consumers receive both the semantic checkpoint identity and the exact observation artifact reference.

## Information-time representation

### Source availability key

For an ordered `jsonStream` record, the historical availability evidence is represented logically as:

```text
SourceAvailabilityKey = (
    session_clock,
    stream_name,
    source_stream_time,
    record_ordinal
)
```

`source_stream_time` is the source timestamp prefix attached to the archived live-timing record. `record_ordinal` is its stable position within the exact frozen endpoint snapshot.

This represents **source publication order for historical replay**, not actual network receipt time at an F1 team or at a future live deployment.

The raw record itself is the evidence. A timestamp copied into a later processed dataframe does not retain the same proof unless its raw-record lineage is preserved.

### Effective/occurrence time remains separate

A normalized fact may also have an effective or occurrence time indicating when the described race event/sample applies. This is never substituted for availability.

Examples:

- a race-control message may contain an event/message UTC time while the containing raw stream record provides the source-availability evidence;
- a telemetry sample time describes the sample's effective point in the session, while the raw stream envelope/order establishes when that sample record appears in the source stream;
- a correction published later may have an effective time referring to an earlier event, but its availability remains the later correction record.

## Availability evidence classes

Every mutable normalized fact carries one of these logical availability classes:

| Class | Evidence | Admissibility rule |
| --- | --- | --- |
| `STREAM_ORDERED` | Source stream timestamp + stable ordinal in frozen raw stream | May be admitted using the full tie rules below |
| `TIMESTAMP_ONLY` | Availability/source-publication timestamp but no stable same-time order | Admit only when demonstrably earlier than the boundary; equal-time tie is ambiguous |
| `BOUNDED_TIME` | Conservative interval/bounds for availability | Admit only when the latest possible availability is before the boundary, or at the boundary with independent ordering proof |
| `EFFECTIVE_ONLY` | Event/sample time only; no availability evidence | Mutable fact is not admissible as point-in-time knowledge |
| `FINAL_SNAPSHOT_ONLY` | Final/corrected value with no historical version availability | Mutable fact is not admissible for an earlier observation |
| `STATIC_PRIOR` | Stable metadata independently proven available before race start | May be admitted from the initial checkpoint onward |
| `UNKNOWN` | No defensible timing evidence | Not admissible |

These classes describe evidence strength, not feature value or model quality.

## Prediction boundary reconstruction

### Race-start checkpoint

The first checkpoint is created when the ordered session-status source first makes the official race-start transition observable.

The checkpoint boundary is the availability key of that source record. The selected driver's completed-race-lap count is `0`.

Rules:

- scheduled session time is not sufficient to create the checkpoint;
- FastF1 `session_start_time` may validate the event/effective time but does not replace raw source-order evidence for V2;
- if the official start transition cannot be established from the frozen source evidence, the start observation is indeterminate and is not fabricated;
- a driver entry must be established for the session before emitting that driver's start observation.

### Driver lap-completion checkpoint

For selected driver `D`, checkpoint `L` is triggered by the **first ordered `TimingData` source record** that makes `D`'s official completed-lap count advance to `L`.

The prediction boundary is that raw record's source-availability key. V2 does not use FastF1's later aligned `Session.laps.Time` as this boundary.

Rules:

1. The first source update that establishes completed count `L` owns the checkpoint time.
2. Duplicate updates with count `L` do not create duplicate checkpoints.
3. A later correction does not move or rewrite the earlier observation boundary.
4. If source history jumps over one or more lap counts, no earlier checkpoint time is invented for the skipped counts. The skipped checkpoint(s) are recorded as unreconstructable from this source snapshot; the reported current count may still establish its own checkpoint.
5. If the source temporarily regresses or later retracts/corrects progression, raw history is preserved. The earlier observation remains the knowledge state actually observable then; the correction affects only later as-of state. Rare cases where the canonical official-lap identity itself becomes indeterminate are surfaced by a checkpoint-quality reason and routed to verification/evaluation handling rather than silently renumbered.

## Cross-stream ordering and tie rule

The selected driver's checkpoint record defines boundary `T` on the common live-timing session clock.

For a candidate fact with availability evidence `A`:

1. If `A.time < T.time`, the fact may be admitted.
2. If `A.time > T.time`, the fact is future and is excluded.
3. If `A.time == T.time` and the fact is from the **same raw stream**, its stable record ordinal is used. Facts in records at or before the trigger record are admissible; later same-time records are not.
4. If `A.time == T.time` and the fact is from a **different stream**, equality alone is not proof of cross-stream order. The fact is excluded unless an explicit cross-stream ordering witness/guarantee is recorded by the source adapter.
5. If either time is coarse or bounded and the ranges overlap so ordering cannot be proven, the candidate fact is omitted as an ambiguous tie.

The reconstruction must never invent a global sequence by sorting different streams alphabetically, by dataframe order, by fetch order, or by arbitrary stable-sort behavior.

This conservative tie rule operationalizes the approved inclusive boundary without treating timestamp equality as causal proof.

## Raw record -> normalized fact boundary

### Raw source record

A raw source record is immutable evidence. Its logical contract includes:

- source snapshot ID;
- session ID;
- endpoint/stream name;
- record ordinal;
- raw source timestamp/prefix if present;
- raw payload reference or content hash;
- parser/source-adapter version;
- parse status.

Raw records are never edited to contain corrected later values.

### Normalized fact

A normalized fact is a provider-neutral claim derived from one or more raw records. Its logical contract includes:

- fact identity;
- race-session identity;
- subject identity (driver entry, session, track/race scope, or environmental scope as applicable);
- fact kind and value/state;
- effective/occurrence time or range when meaningful;
- availability class and availability key/bounds;
- exact source-record lineage;
- revision/supersession relation when the source corrects a prior claim;
- normalization/source-adapter version;
- fact-level quality/reason codes.

Normalization may decode provider delta messages, map provider identifiers, and preserve explicit tombstones/retractions. It may not collapse a later correction into the earlier fact's source record or replace availability with effective time.

### Endpoint ownership for initial normalization

The initial provider adapter should keep one primary source family for each raw claim type instead of merging semantically similar final views by convenience:

- session lifecycle/start: `SessionStatus`;
- driver roster/aliases: `DriverList` plus session metadata cross-check;
- driver lap progression and timing/gap/position updates: raw `TimingData`;
- tyre/stint-related source updates when represented: raw `TimingAppData`;
- track-status changes: raw `TrackStatus`;
- weather samples: raw `WeatherData`;
- race-control messages: raw `RaceControlMessages`;
- car telemetry: raw `CarData`;
- position samples: raw `Position`.

This table establishes reconstruction ownership only. It does not require every domain to become a model input.

Processed FastF1 views may be used as validation aids or parser helpers if the adapter can still trace each admitted mutable fact to the raw ordered evidence that proves its availability.

## Delta streams and state reduction

Most live-timing feeds are update streams rather than independent full snapshots. Normalization therefore preserves update semantics and the canonical observation is produced by an as-of reducer.

For each canonical state key:

1. consider only normalized facts admissible at boundary `T`;
2. apply them in defensible source order within their owning stream/domain;
3. retain the latest legitimately available version at `T`;
4. apply explicit retraction/tombstone semantics when the source provides them;
5. treat a missing field in a delta record as "no new claim" only when the endpoint contract establishes delta semantics;
6. never translate an absent historical update into a known negative/default value without source evidence.

If a stream has a known gap that prevents continuity from being established, affected state becomes `unknown` after the gap until a defensible full-state/reset record or later evidence restores knowledge. The reducer does not carry a stale fact silently across an unknown interval.

## Corrections, supersession, and later confirmation

Corrections are represented append-only.

Example:

```text
T1: fact F1 published -> effective value V1
T2: correction F2 published -> supersedes F1, effective value V2
```

An observation at `T1` contains V1 if otherwise admissible. An observation at or after `T2` may contain V2. The effective time of V2 may refer to an earlier race event; that does not make V2 available before T2.

Rules:

- raw source evidence is never rewritten;
- normalized correction facts link to what they supersede when this can be established;
- earlier canonical observations are immutable;
- later source confirmation may improve later state but cannot backfill earlier certainty;
- when only a final corrected value survives and prior version history is absent, the mutable value is classified `FINAL_SNAPSHOT_ONLY` and excluded from earlier observations;
- improved source data or reconstruction logic creates a new source/reconstruction version and new observation artifact, not an in-place mutation of an artifact already used by a run.

## Partial-lap and race-wide alignment

Observation indexing is driver-relative, but state reduction is always time-relative.

At selected driver `D`'s checkpoint boundary `T`:

- `D.completed_laps` equals the checkpoint lap count;
- every other driver's state is reduced independently to information available by the same `T`;
- another driver may have completed fewer or more laps, be in a partial lap, be in the pit lane, or have no currently known state;
- a completed-lap summary for another driver is available only if that driver's completion update is admissible by `T`;
- telemetry/position/weather/race-control facts during `D`'s just-completed lap may be included if they became available by `T`;
- no race-wide join uses `other_driver.LapNumber == D.LapNumber` as an alignment rule.

This specifically replaces the legacy lap-row synchronization model.

### Weather

The legacy extractor backward-joined weather to each row's `LapStartTime`. V2 instead reduces the weather stream to the selected driver's actual prediction boundary `T`. A weather update that became available during the lap may therefore legitimately be present at the lap-completion checkpoint; a later update is excluded.

### Telemetry and position

The legacy extractor sampled driver-ahead state within one second after lap start. V2 does not give lap-start samples privileged status. If telemetry/position is included in a canonical observation, it is reduced/sampled only from records admissible by `T`, with the sampling/aggregation derivation carrying its own causal lineage.

Exact telemetry aggregation is a later feature/design choice; raw point-in-time admissibility is fixed here.

### Completed-lap facts

A selected driver's completed-lap `LapTime` or other official timing value may be included at checkpoint `L` only when the source update establishing that value is available at or before the checkpoint boundary under the tie rules above. The fact is not admitted merely because FastF1's final `Laps` row contains it.

## Deterministic derivations inside observation artifacts

This issue does not select features. It defines only the rule for any derived state that a later design may request.

A derivation persisted in an observation must carry:

- derivation identifier/version;
- exact input fact references;
- deterministic parameters/configuration;
- output quality;
- proof that every input fact is admissible at the same prediction boundary.

A derivation is invalid for that observation if it uses any input first available after `T`, a final race result, a future normalization statistic, a later source correction, or an unavailable value filled from hindsight.

Derived state may be omitted while retaining the underlying canonical observation.

## Canonical observation artifact contract

The canonical observation is an immutable as-of artifact. The logical schema is:

```text
CanonicalObservation
  artifact_id
  semantic_observation_key
    race_session_key
    driver_entry_key
    checkpoint_key
  prediction_boundary
    source_clock
    source_time
    trigger_stream
    trigger_record_ordinal
    timestamp_precision / ordering metadata
  selected_driver_completed_laps
  canonical_state
    session/race facts
    selected-driver facts
    competitor facts keyed by DriverEntryKey
    environmental facts
    optional causal derived facts
  provenance
    source_snapshot_manifest_ref
    observation_reconstruction_run_ref
    reconstruction_policy_version
    source_adapter/normalizer_version
    repository_revision
  quality
    status
    reason_codes
    omitted_domains/facts summary
```

The physical format, exact column types, and storage partitioning are intentionally not fixed here.

`canonical_state` is a provider-neutral as-of fact/state collection, not a model feature vector. A later model-facing design may select or derive predictors only from this artifact and may not reach around it to retrospective source truth.

## Reconstruction run manifest

Each observation reconstruction run must persist enough metadata to reproduce and audit the set of observations:

- run ID;
- source snapshot manifest IDs;
- exact repository/code revision;
- reconstruction policy version;
- provider/source adapter and normalizer versions;
- clock conversion/reference configuration;
- requested season/round/session scope and driver scope;
- endpoint completeness/gap summary;
- counts by emitted/omitted/indeterminate status and reason;
- observation artifact IDs emitted by the run;
- configuration inputs that can affect reconstruction;
- deterministic randomness seed only if a future reconstruction step genuinely needs randomness; the initial reconstruction should not.

A notebook session, local cache directory, current branch name, or file modification time is not sufficient provenance.

## Observation quality and reconstruction failure states

Quality is explicit at both observation and fact/domain level.

### Observation-level status

| Status | Meaning | Downstream use |
| --- | --- | --- |
| `VALID` | Identity and checkpoint boundary are defensible; every represented fact satisfies the availability contract | Ordinary downstream consumption |
| `VALID_WITH_OMISSIONS` | Core identity/checkpoint are defensible, but one or more optional domains/facts were conservatively omitted because source evidence is missing or ambiguous | Downstream may consume only represented/known state and must retain quality metadata |
| `INDETERMINATE_IDENTITY` | Session or driver-entry identity cannot be established unambiguously | No canonical prediction observation emitted |
| `INDETERMINATE_CHECKPOINT` | Official start/lap-completion availability boundary cannot be reconstructed | No canonical prediction observation emitted for that checkpoint |
| `INDETERMINATE_SOURCE` | Source gaps/corruption prevent the minimum required reconstruction from being established | No canonical prediction observation emitted |

Failure/indeterminate attempts are still recorded in the reconstruction-run accounting so dataset coverage is auditable.

### Standard reason codes

The design reserves at least these reason classes:

- `SESSION_ID_MISMATCH`;
- `DRIVER_ID_MISSING_OR_NONUNIQUE`;
- `START_TRIGGER_MISSING`;
- `LAP_TRIGGER_MISSING`;
- `LAP_COUNT_JUMP`;
- `CHECKPOINT_CORRECTED_LATER`;
- `SOURCE_STREAM_MISSING`;
- `SOURCE_STREAM_GAP`;
- `RAW_RECORD_PARSE_ERROR`;
- `CROSS_STREAM_TIE_OMITTED`;
- `COARSE_TIME_AMBIGUITY`;
- `FINAL_ONLY_VALUE_OMITTED`;
- `EFFECTIVE_ONLY_VALUE_OMITTED`;
- `CORRECTION_HISTORY_UNPROVEN`;
- `NORMALIZATION_CONFLICT`;
- `OPTIONAL_DOMAIN_UNAVAILABLE`.

Implementations may refine codes without weakening these distinctions.

## Legacy data handling

The existing CSV corpus remains historical evidence and may be used for comparison, QA, or migration checks, but it is not a canonical V2 observation store.

In particular:

- `LapStartTime` is an effective lap-start time, not the lap-completion prediction boundary;
- `LapTime` describes a completed lap and cannot be paired blindly with start-of-lap values;
- legacy weather is sampled/as-of joined to lap start rather than the V2 checkpoint boundary;
- legacy `DriverAhead`/distance is sampled around lap start;
- legacy `PitStatus` is a retrospective lap-level derivation and is not copied into V2 observations as a target/proxy field;
- legacy `TotalLaps` created as maximum observed lap count is retrospective race information, not proof of scheduled total laps known at an earlier checkpoint;
- final position/gap/stint/tyre values in a row are not assumed point-in-time legal without raw availability evidence.

V2 implementation should re-acquire/freeze the underlying historical source streams where available. A session for which the minimum source-order evidence cannot be obtained is reported as incomplete/indeterminate rather than reconstructed from hindsight.

The historical extractor's special skip of the first two 2018 races because telemetry was unavailable is not inherited as a V2 semantic filter. Telemetry is optional to the core observation contract; a race with valid identity/checkpoint timing may still yield observations with telemetry omitted.

## Provider-version and private-API boundary

FastF1 currently marks parts of its API layer as private/subject to change. #18 therefore does not make a specific private Python function a permanent architectural interface.

The implementation requirement is instead:

- isolate FastF1/F1-live-timing parsing behind the source adapter boundary;
- freeze raw source content;
- record FastF1/adapter version in provenance;
- test source semantics against representative historical fixtures before relying on a changed provider version.

Pinning exact package versions and implementing adapter code belong to implementation/verification work.

## Downstream contract

### #19 — target reconstruction

#19 receives:

- exact `CanonicalObservation` artifact identity;
- race-session and driver-entry keys;
- checkpoint key;
- prediction boundary;
- observation quality/provenance.

#19 may initialize target eligibility/episode identity from this causal observation contract but may not require #18 to expose retrospective target truth.

### #20 — prediction/model-facing contract

#20 may define a model-facing representation derived from canonical observation state. It may not use processed source values that bypass the observation artifact or change the information boundary.

### #21 — replay/backtest execution

#21 can order observations by their canonical checkpoint/prediction boundaries and retain exact artifact/provenance references. It must not rewrite observations after later corrections or target resolution.

## Verification handoff

The later verification baseline must test, at minimum:

1. representative `SessionStatus` start transitions across supported seasons;
2. raw `TimingData` lap-count progression and duplicate/jump/correction cases;
3. that archived `jsonStream` timestamps/order are preserved by the source adapter;
4. common session-clock alignment across streams and the conservative cross-stream tie behavior;
5. source gaps/corrupt records and recovery behavior;
6. examples where FastF1 processed lap alignment differs from raw timing-record publication time;
7. delayed/corrected facts proving that earlier observations do not change;
8. partial-lap/race-wide alignment where drivers are on different lap counts;
9. source-version/provenance replay yielding identical observation artifacts for identical frozen inputs;
10. coverage across the historical race set, with sessions lacking sufficient source evidence explicitly reported rather than silently backfilled.

These are verification obligations, not permission to change this design's point-in-time semantics.

## Decisions intentionally deferred

| Question | Owner |
| --- | --- |
| Pit-visit identity, tyre-service qualification, target eligibility materialization, target resolution | #19 |
| Model feature set, feature aggregation, timing-region/probability representation, model artifact | #20 / later model verification |
| Replay ordering beyond consuming observation boundaries, development/final-evaluation split, scoring/accounting protocol | #21 / verification |
| Exact metrics/statistical estimators and dependence treatment | Verification/statistical phase |
| Exact physical schemas, file formats, hash algorithm, package versions, CLI commands, cache implementation | Implementation unless a later design issue explicitly needs them |
| Live ingestion receipt-time clocks, network latency, intra-lap live triggers | Future bounded live design |

## Acceptance mapping

- **Concrete source/timing inventory:** repository CSV/extractor evidence and current FastF1 raw/processed source classes are explicitly separated.
- **Canonical identities:** race session, driver entry, checkpoint, semantic observation, and artifact identity are defined without display-name coincidence.
- **Transformation ownership:** raw source record -> normalized fact -> canonical observation boundaries are explicit.
- **Availability/order handling:** source availability classes, same-stream order, cross-stream tie exclusion, coarse/bounded times, and effective-only/final-only handling are explicit.
- **Corrections/supersession:** append-only revisions and no retroactive observation mutation are explicit.
- **Partial-lap/race-wide alignment:** all state is reduced by selected-driver prediction time, never by equal lap number.
- **Observation provenance:** source snapshot, adapter/reconstruction versions, repository revision, trigger lineage, and run accounting are required.
- **Failure/quality states:** valid-with-omission versus identity/checkpoint/source indeterminacy are distinguished.
- **Downstream consumability:** #19–#21 receive stable observation/provenance contracts without redefining point-in-time semantics.
- **Scope discipline:** no target algorithm, feature selection, model choice, output parameterization, metric, live runtime, or production code is selected.

## Product Owner decisions

None required. This design implements the already-approved availability-time and replay-first semantics with conservative source-order rules. It does not change which kind of information is legitimate in principle, the target meaning, prediction meaning, or product scope.

## Review

This artifact requires one independent full scoped review under `governance/REVIEW_POLICY.md` before approval. Review should judge the detailed observation-reconstruction/provenance design against Issue #18, `contexts/RACE_OBSERVATION_STATE.md`, and the approved #17 architecture boundary. Downstream target/model/evaluation details explicitly owned elsewhere are not defects unless this observation contract makes them impossible to consume coherently.
