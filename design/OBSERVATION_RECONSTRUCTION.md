# V2 Point-in-Time Observation Reconstruction and Provenance

## Status

Draft — reworked after the full scoped review on PR #24. Bounded re-review required before approval.

## Abstraction level

Detailed data design — historical source evidence, information-time reconstruction, canonical technical identities, normalized-fact boundaries, observation artifacts, correction handling, quality states, and provenance.

This artifact does not define target reconstruction, target-episode internals, model features, probability-output parameterization, metrics, temporal train/test policy, live ingestion, or production implementation.

## Issue / branch

- Issue: #18 — `Design — point-in-time observation reconstruction and provenance`
- Parent: #16
- Upstream architecture: #17 / `design/SYSTEM_ARCHITECTURE.md`
- Branch: `design/observation-reconstruction`
- PR: #24

## Outcome

V2 reconstructs each historical observation from evidence whose **historical availability semantics are defensible**, not from a final lap row truncated by lap number and not from archive timestamp/order alone.

For FastF1-backed historical work, archived F1 live-timing `jsonStream` files are valuable candidate evidence because the frozen archive preserves record prefixes and within-file order. However, those properties by themselves prove only the structure of the archive snapshot fetched later. They do **not** prove that a prefix is a contemporaneous publication/availability timestamp or that the archive preserves exactly the versions visible at that historical instant.

The canonical transformation is therefore:

```text
immutable source snapshot
    -> archive/source records with source structure
    -> availability-authority validation
    -> normalized facts with separate effective and proven availability evidence
    -> as-of reduction at one canonical checkpoint boundary
    -> immutable canonical observation + provenance/quality record
```

A mutable fact is admitted only when its source or acquisition mode has passed the required availability-authority validation for the relevant endpoint/era and the individual fact is defensibly available at or before the selected driver's prediction boundary. Unverified archives, ambiguous ties, final-only historical values, and later corrections are never silently backfilled.

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
- joins resulting timing values to `session.laps` by driver and lap number;
- samples `DriverAhead` / `DistanceToDriverAhead` from telemetry during a one-second window after `LapStartDate`;
- backward-as-of joins weather to `LapStartTime`;
- derives `PitStatus` from lap-level `PitOutTime` / `PitInTime`;
- carries completed-lap fields such as `LapTime` together with start-of-lap telemetry/weather;
- computes legacy `TotalLaps` from the maximum observed lap number for the extracted race.

Therefore the legacy CSV row intentionally mixes facts with different temporal meanings. It cannot be promoted to a V2 point-in-time observation merely by choosing or shifting a row.

Stable evidence reference:

- `f1_pit_predictor/extraction.py` at historical commit `fe5abd65acd335c05a472db1e5a45bdbe8cac5b9`.

### Current FastF1 implementation evidence inspected

FastF1 upstream was inspected at commit `227cf301fb4bcf1705bcb1866de1fe5dbcef6071` (2026-08-28). This is provider implementation evidence, not a dependency version commitment.

FastF1 exposes historical/static F1 live-timing endpoints including:

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

FastF1's `fetch_page` implementation preserves the line order present in the fetched `jsonStream` archive and separates each line into a leading timestamp prefix and parsed payload. This establishes the structure of the **fetched archive snapshot**.

FastF1's time documentation states that `SessionTime` is provided by the F1 live-timing API and shares a session-level reference across API data. It also states that lap `Time` marks when a lap was set/finished, while `LapStartTime`, sector session times, and pit times are additional calculated timestamps whose millisecond accuracy cannot be verified.

FastF1's processed lap construction may align driver lap timestamps using gap information, and `Session.load` may mix multiple endpoints to correct errors or add information. Therefore **processed `Session.laps.Time` is an effective/reconstructed lap-end timestamp, not availability authority**.

### Evidence limitation established by review

The inspected FastF1 implementation/documentation does **not** establish either of these stronger claims:

1. that the leading timestamp of a static archived `jsonStream` record is guaranteed to be the time at which that payload/version became observable to a contemporaneous consumer; or
2. that a static archive fetched later preserves the exact historical sequence of payload versions originally observable, without retrospective correction, replacement, or backfill.

Accordingly, archive prefix/order is not automatically promoted to historical availability evidence. Freezing a 2026 archive makes a reconstruction run reproducible against that 2026 snapshot; it does not by itself make the snapshot a faithful record of 2019/2020/etc. historical knowledge.

Stable upstream evidence references:

- `theOehrly/Fast-F1` `fastf1/_api.py` at `227cf301fb4bcf1705bcb1866de1fe5dbcef6071` — endpoint map, archive fetching/parsing, timing parsing, and lap alignment;
- `theOehrly/Fast-F1` `fastf1/core.py` at the same commit — `Session` source views and note that loaded data may be mixed/corrected;
- `theOehrly/Fast-F1` `docs/data_reference/time_explanation.rst` at the same commit — SessionTime and lap-time semantics.

## Source classes and authority

| Source class | Concrete examples | What the evidence proves without extra validation | Point-in-time use |
| --- | --- | --- | --- |
| Historical static live-timing archive | `TimingData.jsonStream`, `SessionStatus.jsonStream`, `WeatherData.jsonStream`, etc. fetched after the event | Record timestamp prefixes and line order in the exact frozen archive snapshot | **Not availability-authoritative by default.** May be upgraded only for validated endpoint/era/acquisition scopes. |
| Contemporaneous captured stream | Raw records captured while the session was occurring, with local receipt time and immutable capture provenance | What the capture process received and when it received it, subject to clock/capture validation | Can provide strong availability evidence for that capture; this is an evidence class, not an initial live-product commitment. |
| Raw high-frequency historical archive | `CarData.z.jsonStream`, `Position.z.jsonStream` | Sample content and archive structure/order in the frozen snapshot | Optional state only after the same historical-availability validation; otherwise omitted. |
| Processed FastF1 session views | `Session.laps`, weather/track-status/race-control dataframes, telemetry objects | Useful effective/event values and a provider's current reconstruction | Validation/normalization assistance only where lineage remains explicit; not availability authority. |
| Legacy repository CSVs | `data/<year>/*.csv` | Thesis-era derived lap-level values | Historical comparison, QA, migration evidence; never canonical availability authority. |
| Static acquisition/session metadata | requested season/round/session plus independently verified identifiers | Stable addressing/identity information | May be `STATIC_PRIOR` when independently proven available before race start. |
| Final-only/reconstructed historical value | final classification, corrected lap row, `TotalLaps=max(observed lap)` | Retrospective/final truth | Audit/validation only; not point-in-time knowledge. |

## Historical availability-authority validation

### Principle

`ArchiveRecordKey` and source order are **archive structure**. `SourceAvailabilityKey` is an **availability claim**. The second may be created from the first only after a validation record establishes that the relevant archive/acquisition mode is suitable for historical point-in-time use.

Validation is scoped, not global. A result applies to an explicit tuple such as:

```text
AvailabilityAuthorityScope = (
    provider/source family,
    acquisition_mode,
    endpoint/stream,
    season/era range,
    archive/provider revision where relevant
)
```

A validation for one endpoint or era does not silently authorize another.

### Validation requirements for historical archives

Before a historical static archive scope may be classified as availability-authoritative, the project must have a persisted `AvailabilityAuthorityValidation` with sufficient evidence for both:

1. **timestamp meaning** — evidence that the record prefix/order used as an availability key corresponds to source publication/observability ordering, not merely event/effective/log time; and
2. **revision fidelity** — evidence that later historical retrieval preserves the contemporaneous version sequence sufficiently for the claimed use, or a documented rule that bounds/identifies retrospective revisions so they cannot be mistaken for earlier knowledge.

Acceptable evidence can include provider/F1 archival documentation with an explicit guarantee, verified source implementation behavior where semantics are contractual, paired contemporaneous captures against later archives, or another independently reproducible validation fixture. Mere presence of timestamps in the archive, current parser behavior, or successful re-fetching is insufficient.

The validation record must identify:

- exact source/acquisition/endpoint/era scope;
- evidence references and dates;
- validation procedure/version;
- timestamp-semantics outcome;
- archive-revision/fidelity outcome;
- any known exceptions/gaps;
- resulting authority level;
- reviewer/verification artifact reference once the verification phase approves it.

### Authority levels

A validated scope receives one of these levels:

| Authority level | Meaning | Can create checkpoint boundary? | Can admit mutable facts? |
| --- | --- | ---: | ---: |
| `VERIFIED_STREAM_ORDERED` | Historical availability time and within-stream order are defensible for the scope | Yes | Yes, subject to tie/gap rules |
| `VERIFIED_TIMESTAMP_ONLY` | Historical availability timestamp is defensible but equal-time source order is not | Yes only when trigger is unambiguous at timestamp level | Yes only when strictly earlier or independently ordered |
| `VERIFIED_BOUNDED_TIME` | Only conservative availability bounds are defensible | Only if checkpoint boundary is unambiguous under bounds | Yes only when latest possible availability is safely before boundary |
| `UNVERIFIED_ARCHIVE` | Archive structure exists but historical availability semantics/revision fidelity are unproven | No | No |
| `UNSUPPORTED` | Evidence demonstrates the source cannot support the required historical availability claim | No | No |

No implementation may map `UNVERIFIED_ARCHIVE` to a verified class as a convenience fallback.

### Initial support boundary

At #18 design time, the inspected FastF1 static archive is classified **`UNVERIFIED_ARCHIVE` for historical availability authority** because the required publication-time and revision-fidelity guarantees have not yet been demonstrated.

Therefore this design does not claim that the existing 2018–2023 historical corpus is already reconstructable into ordinary V2 observations. Supported seasons/endpoints are established later by the required verification matrix. A session/endpoint remains fail-closed until its scope has a passing authority validation.

This limitation is deliberate: historical replay is the product ambition, but a reproducible hindsight snapshot is not equivalent to historically faithful knowledge.

## Historical source snapshot contract

A reconstruction run freezes the exact source evidence it uses. Re-fetching the same historical session later may return changed archive content, so a URL or FastF1 call alone is not reproducibility.

The logical `SourceSnapshotManifest` records, at minimum:

- canonical race-session key;
- provider/source family;
- acquisition mode, including `historical_archive` versus contemporaneous capture where available;
- provider API path/session locator;
- each endpoint/stream included;
- exact payload/content hash or equivalent immutable content identity per endpoint;
- record count and first/last archive/source timestamp where applicable;
- retrieval/capture timestamp;
- FastF1/provider-adapter version or source revision used to obtain/parse the data;
- completeness status and known gaps/errors per endpoint;
- `AvailabilityAuthorityScope` and validation reference/status per endpoint;
- repository/code revision and reconstruction-run identity.

Freezing and authority validation are separate requirements: freezing establishes reproducibility of the input; authority validation establishes whether that input can support historical availability claims.

Exact serialization and hash algorithm belong to implementation.

### Required versus optional source evidence

To emit an ordinary canonical observation, reconstruction must establish:

1. a stable race-session identity;
2. a stable driver-entry identity;
3. the canonical checkpoint occurrence as an observable source update; and
4. a **verified** prediction information boundary for that checkpoint.

For the FastF1-backed design, `SessionStatus` is the candidate source for race-start checkpoints and `TimingData` is the candidate source for driver lap-completion checkpoints. They may create V2 checkpoint boundaries only for scopes whose historical availability authority has been validated to the required level.

If the trigger source is `UNVERIFIED_ARCHIVE` or `UNSUPPORTED`, the checkpoint is `INDETERMINATE_CHECKPOINT`; scheduled time, processed FastF1 lap time, event/effective timestamp, legacy CSV rows, or a later final value are not fallbacks.

Race-wide, environmental, tyre, telemetry, or other state domains may be partially unavailable or unverified. Missing/unverified optional domains produce explicit omissions rather than fabricated facts or automatic rejection of an otherwise valid checkpoint.

## Canonical technical identities

### Race session key

```text
RaceSessionKey = (
    series = "F1",
    season,
    round_number,
    session_kind = "RACE"
)
```

`season` and `round_number` come from acquisition/session selection and must be cross-checked against provider session metadata. Provider meeting/session keys and FastF1 `api_path` are retained as provenance aliases where available.

Event name, circuit/location, team name, and display strings are descriptive metadata only and must not be canonical keys. If year/round/session cannot be reconciled with loaded provider metadata, reconstruction fails identity validation rather than falling back to a name match.

### Driver entry key

```text
DriverEntryKey = (RaceSessionKey, racing_number)
```

The racing number must be evidenced as a unique entry in the selected session by roster/timing evidence. Provider-specific driver IDs may be stored as aliases. Abbreviation, surname, display name, or team name are never sufficient canonical keys.

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

The stable semantic key identifies the driver's checkpoint. The persisted observation artifact has a separate immutable artifact identity tied to the exact source snapshot, authority-validation state, and reconstruction version.

A later corrected source snapshot, stronger validation, or reconstruction policy may produce a new observation artifact for the same semantic checkpoint without overwriting historical runs. Downstream consumers receive both the semantic checkpoint identity and exact observation artifact reference.

## Information-time representation

### Archive record key

Every raw historical archive record may have a structural key even when it is not availability-authoritative:

```text
ArchiveRecordKey = (
    source_snapshot_id,
    stream_name,
    archive_timestamp_prefix,
    record_ordinal
)
```

This key means only: this payload occupied this position with this prefix in this exact frozen archive snapshot.

### Source availability key

A `SourceAvailabilityKey` exists only when the record's source scope has a verified authority classification:

```text
SourceAvailabilityKey = (
    authority_validation_ref,
    session_clock,
    stream_name,
    availability_time_or_bound,
    record_ordinal_if_verified
)
```

For `VERIFIED_STREAM_ORDERED`, the validated mapping may use the archive/source timestamp and stable within-stream ordinal. For weaker verified classes, only the proven timestamp/bounds/order fields are populated.

An archive timestamp copied into a processed dataframe or normalized fact is not availability proof by itself.

### Effective/occurrence time remains separate

A normalized fact may have an effective or occurrence time indicating when the described event/sample applies. This is never substituted for availability.

Examples:

- race-control message UTC/event time may describe the message/event while the availability key, if validated, describes when the information became observable;
- telemetry sample time describes the sample's effective point in the session;
- a correction may refer to an earlier effective event while becoming available only later;
- a static archive record with an old prefix remains `UNVERIFIED_ARCHIVE` if historical publication semantics are not established.

## Availability evidence classes for normalized facts

Every mutable normalized fact carries one of these classes:

| Class | Required evidence | Admissibility rule |
| --- | --- | --- |
| `STREAM_ORDERED` | Source scope is `VERIFIED_STREAM_ORDERED` plus exact source-record lineage | May be admitted using full tie/order rules |
| `TIMESTAMP_ONLY` | Source scope is `VERIFIED_TIMESTAMP_ONLY` | Admit only when demonstrably earlier than boundary; equal-time tie is ambiguous unless independently ordered |
| `BOUNDED_TIME` | Source scope is `VERIFIED_BOUNDED_TIME` | Admit only when latest possible availability is before boundary, or boundary ordering is independently proven |
| `UNVERIFIED_ARCHIVE` | Frozen archive record exists but publication/revision semantics are unproven | Not admissible as mutable point-in-time knowledge |
| `EFFECTIVE_ONLY` | Event/sample time only | Not admissible as mutable point-in-time knowledge |
| `FINAL_SNAPSHOT_ONLY` | Final/corrected value with no historical version availability | Not admissible for earlier observation |
| `STATIC_PRIOR` | Stable metadata independently proven available before race start | May be admitted from initial checkpoint onward |
| `UNKNOWN` | No defensible timing evidence | Not admissible |

These classes describe evidence strength, not model or feature quality.

## Prediction boundary reconstruction

### Race-start checkpoint

The race-start checkpoint is created only when an availability-authoritative `SessionStatus` source first makes the official race-start transition observable.

The checkpoint boundary is the verified availability key of that source record. The selected driver's completed-race-lap count is `0`.

Rules:

- scheduled session time is not sufficient;
- FastF1 `session_start_time` may validate effective/event time but does not replace verified availability evidence;
- an `UNVERIFIED_ARCHIVE` `SessionStatus` record cannot create a V2 checkpoint;
- if official start availability cannot be established, the start observation is `INDETERMINATE_CHECKPOINT`;
- a driver entry must be established for the session before emitting that driver's start observation.

### Driver lap-completion checkpoint

For selected driver `D`, checkpoint `L` is triggered by the first **availability-authoritative** `TimingData` update that makes `D`'s official completed-lap count advance to `L`.

The prediction boundary is that update's verified `SourceAvailabilityKey`. V2 does not use FastF1's later aligned `Session.laps.Time` or an unverified archive prefix as this boundary.

Rules:

1. The first verified source update establishing completed count `L` owns the checkpoint boundary.
2. Duplicate updates with count `L` do not create duplicate checkpoints.
3. A later correction does not move or rewrite an earlier observation boundary.
4. If verified source history jumps over lap counts, skipped checkpoints are unreconstructable rather than assigned invented times.
5. If progression regresses/retracts, append-only source history is preserved and later knowledge affects later observations only.
6. If the relevant historical `TimingData` scope is unverified, the lap-completion checkpoint is indeterminate even if the current archive contains a plausible timestamp and count.

## Cross-stream ordering and tie rule

The selected driver's checkpoint record defines boundary `T` on a validated information clock.

For a candidate fact with verified availability evidence `A`:

1. If `A.time < T.time`, the fact may be admitted.
2. If `A.time > T.time`, it is future and excluded.
3. If `A.time == T.time` and both records are from the same `VERIFIED_STREAM_ORDERED` source, stable within-stream ordinal decides the tie.
4. If `A.time == T.time` across streams, equality alone is not proof of cross-stream order. Exclude unless an explicit validated cross-stream ordering witness/guarantee exists.
5. If either time is coarse/bounded and ranges overlap, omit unless ordering is independently proven.
6. If either source scope is `UNVERIFIED_ARCHIVE`, no timestamp comparison upgrades it into admissible knowledge.

The reconstruction must never invent a global sequence from stream names, dataframe order, fetch order, or stable-sort behavior.

## Raw record -> normalized fact boundary

### Raw source record

A raw source record is immutable evidence. Its logical contract includes:

- source snapshot ID;
- session ID;
- endpoint/stream name;
- record ordinal;
- raw timestamp/prefix if present;
- raw payload reference/content hash;
- acquisition mode;
- authority-validation scope/reference/status;
- parser/source-adapter version;
- parse status.

Raw records are never edited to contain corrected later values. A raw record may exist even when its availability authority is unverified.

### Normalized fact

A normalized fact is a provider-neutral claim derived from one or more raw records. Its logical contract includes:

- fact identity;
- race-session identity;
- subject identity;
- fact kind and value/state;
- effective/occurrence time or range when meaningful;
- availability class and key/bounds only when defensible;
- authority-validation reference/status;
- exact source-record lineage;
- revision/supersession relation when established;
- normalization/source-adapter version;
- fact-level quality/reason codes.

Normalization may decode provider delta messages, map identifiers, and preserve explicit tombstones/retractions. It may not convert archive structure into historical availability authority, collapse a later correction into an earlier fact, or replace availability with effective time.

### Endpoint ownership for initial normalization

Candidate primary source families are:

- session lifecycle/start: `SessionStatus`;
- driver roster/aliases: `DriverList` plus session metadata cross-check;
- driver lap progression and timing/gap/position updates: raw `TimingData`;
- tyre/stint-related source updates when represented: raw `TimingAppData`;
- track-status changes: raw `TrackStatus`;
- weather samples: raw `WeatherData`;
- race-control messages: raw `RaceControlMessages`;
- car telemetry: raw `CarData`;
- position samples: raw `Position`.

This table establishes normalization ownership, not availability authority. Each endpoint/era still requires its own authority-validation status before mutable facts can enter canonical observations.

Processed FastF1 views may be validation aids/parser helpers if exact raw lineage and authority status remain explicit.

## Delta streams and state reduction

Many feeds are update streams rather than full snapshots. For each canonical state key:

1. consider only normalized facts admissible at boundary `T`;
2. apply them in defensible verified order within the owning stream/domain;
3. retain the latest legitimately available version at `T`;
4. apply explicit retraction/tombstone semantics where defined;
5. treat missing delta fields as "no new claim" only when endpoint behavior is established;
6. never translate absent historical updates into known negative/default values;
7. never carry facts from an unverified source into state merely because the archive is chronologically sortable.

If a verified stream has a gap that breaks continuity, affected state becomes unknown after the gap until a defensible reset/full-state update restores knowledge. The reducer does not silently carry stale state across an unknown interval.

## Corrections, supersession, archive revisions, and later confirmation

Within an availability-authoritative history, corrections are append-only:

```text
T1: fact F1 becomes available -> value V1
T2: correction F2 becomes available -> supersedes F1 with V2
```

An observation at `T1` contains V1 if otherwise admissible. An observation at/after `T2` may contain V2. V2's effective time may refer to an earlier event; that does not make V2 historically available before T2.

Separate archive-level rule: if a later static archive may have replaced/backfilled the historical sequence and this revision behavior is unproven, the archive cannot be treated as append-only contemporaneous knowledge. Its affected scope remains `UNVERIFIED_ARCHIVE`, regardless of how internally ordered the current file appears.

Rules:

- raw source snapshots are immutable once frozen for a run;
- normalized correction facts link to superseded facts only when evidence supports that relation;
- earlier canonical observations are immutable;
- later confirmation improves later knowledge only;
- final corrected values without version history are `FINAL_SNAPSHOT_ONLY`;
- archive retrieval at a later date does not retroactively validate historical knowledge;
- improved source evidence, authority validation, or reconstruction logic creates new versioned observation artifacts, never in-place mutations.

## Partial-lap and race-wide alignment

Observation indexing is driver-relative; state reduction is time-relative.

At selected driver `D`'s checkpoint boundary `T`:

- `D.completed_laps` equals the checkpoint lap count;
- every other driver's state is reduced independently to **verified information available by the same `T`**;
- another driver may have completed fewer/more laps, be mid-lap, in the pit lane, or have unknown state;
- a completed-lap summary for another driver is available only if its availability is admissible by `T`;
- telemetry/position/weather/race-control facts may be included only from verified/admissible source evidence;
- no race-wide join uses `other_driver.LapNumber == D.LapNumber` as its alignment rule.

### Weather

The legacy extractor backward-joined weather to `LapStartTime`. V2 instead reduces verified weather information to prediction boundary `T`. If historical weather archive availability is unverified for the scope, weather is omitted rather than treated as available from archive sample time alone.

### Telemetry and position

The legacy extractor sampled driver-ahead state near lap start. V2 gives no privilege to that sample. Telemetry/position may enter a canonical observation only when availability authority for the source scope is verified and the chosen causal derivation uses records admissible by `T`.

Exact aggregation is a later feature/design choice.

### Completed-lap facts

A selected driver's completed-lap `LapTime` or other timing value may be included at checkpoint `L` only when the source update establishing that value has verified availability at or before the checkpoint boundary. FastF1's final `Laps` row is not sufficient proof.

## Deterministic derivations inside observations

This issue does not select features. Any persisted derivation must carry:

- derivation identifier/version;
- exact input fact references;
- deterministic parameters/configuration;
- output quality;
- proof that every input fact is admissible at the same prediction boundary.

A derivation is invalid if it uses input first available after `T`, an unverified historical archive fact, final race result, future normalization statistic, later correction, or hindsight-filled value.

## Canonical observation artifact contract

```text
CanonicalObservation
  artifact_id
  semantic_observation_key
    race_session_key
    driver_entry_key
    checkpoint_key
  prediction_boundary
    authority_validation_ref
    source_clock
    source_time_or_bound
    trigger_stream
    trigger_record_ordinal_if_verified
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
    authority_validation_refs
    repository_revision
  quality
    status
    reason_codes
    omitted_domains/facts summary
```

The physical format, exact column types, and storage partitioning are not fixed here.

`canonical_state` is a provider-neutral as-of collection, not a model feature vector. Later model-facing design may consume only this causal observation boundary and may not reach around it to retrospective source truth.

## Reconstruction run manifest

Each run persists:

- run ID;
- source snapshot manifest IDs;
- exact repository/code revision;
- reconstruction policy version;
- provider/source adapter and normalizer versions;
- availability-authority validation IDs/statuses and support matrix version;
- clock conversion/reference configuration;
- requested season/round/session/driver scope;
- endpoint completeness/gap summary;
- counts by emitted/omitted/indeterminate status and reason;
- observation artifact IDs emitted;
- configuration inputs affecting reconstruction.

A notebook state, cache directory, branch name, or file modification time is insufficient provenance.

## Observation quality and failure states

| Status | Meaning | Downstream use |
| --- | --- | --- |
| `VALID` | Identity/checkpoint boundary are defensible and every represented mutable fact satisfies verified availability rules | Ordinary downstream consumption |
| `VALID_WITH_OMISSIONS` | Core identity/checkpoint are defensible; optional domains/facts were omitted because evidence was missing, unverified, or ambiguous | Consume represented state and retain quality metadata |
| `INDETERMINATE_IDENTITY` | Session/driver identity cannot be established | No canonical prediction observation |
| `INDETERMINATE_CHECKPOINT` | Official start/lap-completion **availability** boundary cannot be reconstructed with verified authority | No canonical prediction observation for that checkpoint |
| `INDETERMINATE_SOURCE` | Source gaps/corruption/unsupported authority prevent minimum reconstruction | No canonical prediction observation |

Failure/indeterminate attempts remain in run accounting.

### Standard reason codes

At minimum:

- `SESSION_ID_MISMATCH`;
- `DRIVER_ID_MISSING_OR_NONUNIQUE`;
- `START_TRIGGER_MISSING`;
- `LAP_TRIGGER_MISSING`;
- `LAP_COUNT_JUMP`;
- `CHECKPOINT_CORRECTED_LATER`;
- `SOURCE_STREAM_MISSING`;
- `SOURCE_STREAM_GAP`;
- `RAW_RECORD_PARSE_ERROR`;
- `ARCHIVE_AVAILABILITY_UNVERIFIED`;
- `ARCHIVE_REVISION_BEHAVIOR_UNVERIFIED`;
- `SOURCE_AUTHORITY_UNSUPPORTED`;
- `CROSS_STREAM_TIE_OMITTED`;
- `COARSE_TIME_AMBIGUITY`;
- `FINAL_ONLY_VALUE_OMITTED`;
- `EFFECTIVE_ONLY_VALUE_OMITTED`;
- `CORRECTION_HISTORY_UNPROVEN`;
- `NORMALIZATION_CONFLICT`;
- `OPTIONAL_DOMAIN_UNAVAILABLE`.

Implementations may refine codes without weakening these distinctions.

## Legacy data handling

The existing CSV corpus remains historical evidence/QA material, not a canonical V2 observation store.

In particular:

- `LapStartTime` is effective lap-start time, not the lap-completion prediction boundary;
- `LapTime` cannot be paired blindly with start-of-lap values;
- legacy weather is joined to lap start, not V2 checkpoint time;
- legacy driver-ahead/distance is sampled around lap start;
- legacy `PitStatus` is retrospective lap-level derivation and is not copied as target/proxy state;
- legacy `TotalLaps=max(observed lap)` is retrospective race information;
- final position/gap/stint/tyre values are not assumed point-in-time legal.

V2 implementation may re-acquire/freeze historical source streams, but **freezing alone is insufficient**. Ordinary observations are emitted only for source scopes whose historical availability authority is validated. Unsupported/unverified sessions are reported explicitly rather than reconstructed from hindsight.

The historical extractor's skip of the first two 2018 races due to missing telemetry is not inherited. Telemetry is optional to the core observation contract.

## Provider-version/private-API boundary

FastF1 marks parts of its API layer as private/subject to change. The implementation requirement is therefore to:

- isolate FastF1/F1-live-timing parsing behind the source adapter;
- freeze exact source content;
- record FastF1/adapter version;
- keep archive structure separate from availability authority;
- require a versioned authority-validation result before an endpoint/era is used for historical checkpoint/fact availability;
- invalidate/re-run relevant validation when provider/archive behavior changes materially.

Pinning package versions and implementing adapter code belong to implementation/verification work.

## Downstream contract

### #19 — target reconstruction

#19 receives:

- exact `CanonicalObservation` artifact identity;
- race-session and driver-entry keys;
- checkpoint key;
- verified prediction boundary;
- observation quality/provenance.

#19 may initialize target eligibility/episode identity from this causal observation contract but may not require #18 to expose retrospective target truth.

### #20 — prediction/model-facing contract

#20 may define a model-facing representation derived from canonical observation state. It may not use processed/unverified source values that bypass the observation artifact or change the information boundary.

### #21 — replay/backtest execution

#21 can order observations by canonical verified checkpoint boundaries and retain exact artifact/provenance references. It must preserve unsupported/indeterminate coverage accounting and never rewrite observations after later corrections or target resolution.

## Verification handoff

The verification baseline must establish a **source-authority support matrix** before implementation/backtesting claims a historical scope. At minimum it must test/establish:

1. historical meaning of the archive record prefix for each relied-upon endpoint/era: publication/observability versus effective/event/log time;
2. archive revision behavior: whether later static retrieval preserves contemporaneous payload versions/order, including comparisons against contemporaneous captures or another authoritative record where available;
3. explicit downgrade to `UNVERIFIED_ARCHIVE`/`UNSUPPORTED` when either timestamp meaning or revision fidelity cannot be established;
4. representative `SessionStatus` start transitions only within validated authority scopes;
5. raw `TimingData` lap-count progression and duplicate/jump/correction cases only within validated authority scopes;
6. that the adapter preserves exact frozen archive bytes, prefixes, ordinals, hashes, and validation references without promoting them implicitly;
7. common-clock and cross-stream tie behavior for streams whose availability semantics are actually validated;
8. source gaps/corrupt records and recovery behavior;
9. cases where processed FastF1 lap alignment differs from raw/archive timing structure;
10. delayed/corrected facts proving earlier observations remain unchanged;
11. partial-lap/race-wide alignment with drivers on different progression states;
12. identical frozen inputs + identical validation/configuration yielding identical observation artifacts;
13. season/endpoint coverage reporting showing which historical sessions are supported, valid-with-omissions, or indeterminate because authority cannot be proven.

A verification result may validate only a subset of seasons/endpoints. The support matrix, not the existence of an archive file, defines the reconstructable historical scope.

These are verification obligations; they may not weaken the approved availability-time semantics.

## Decisions intentionally deferred

| Question | Owner |
| --- | --- |
| Pit-visit identity, tyre-service qualification, target eligibility materialization, target resolution | #19 |
| Model feature set, feature aggregation, timing-region/probability representation, model artifact | #20 / later model verification |
| Replay ordering beyond consuming observation boundaries, development/final-evaluation split, scoring/accounting protocol | #21 / verification |
| Exact metrics/statistical estimators and dependence treatment | Verification/statistical phase |
| Empirical source-authority support matrix by endpoint/season and fixtures proving archive publication/revision semantics | Verification baseline after #22 |
| Exact physical schemas, formats, hash algorithm, package versions, CLI/cache implementation | Implementation unless later design explicitly requires them |
| Live ingestion receipt-time clocks, network latency, intra-lap live triggers | Future bounded live design |

## Acceptance mapping

- **Concrete source/timing inventory:** repository CSV/extractor evidence and FastF1 raw/archive/processed source classes are separated, including the explicit limitation that archive prefix/order does not itself prove historical availability.
- **Canonical identities:** race session, driver entry, checkpoint, semantic observation, and artifact identity are unambiguous without display-name coincidence.
- **Transformation ownership:** source snapshot -> raw/archive record -> authority validation -> normalized fact -> canonical observation boundaries are explicit.
- **Availability/order handling:** validated source authority, unverified-archive fail-closed handling, same-stream order, cross-stream ties, coarse/bounded times, and effective/final-only distinctions are explicit.
- **Corrections/supersession:** fact revisions and archive-level revision uncertainty are separate; neither can rewrite earlier observations.
- **Partial-lap/race-wide alignment:** all represented state is reduced by selected-driver prediction time, never equal lap number.
- **Observation provenance:** source snapshot, adapter/reconstruction versions, authority validations, repository revision, trigger lineage, and run accounting are required.
- **Failure/quality states:** valid-with-omission versus identity/checkpoint/source indeterminacy are explicit, including unsupported/unverified availability authority.
- **Downstream consumability:** #19–#21 receive stable causal observation/provenance contracts without redefining point-in-time semantics.
- **Scope discipline:** empirical source validation is routed to verification; no target algorithm, feature/model choice, probability parameterization, metric, live runtime, or production code is selected.

## Product Owner decisions

None required. Failing closed when historical availability cannot be proven implements the already-approved availability-time semantic lock. It does not change the product, target, prediction meaning, or historical-replay ambition; it makes the empirically supportable historical scope explicit.

## Review record

### Full scoped review — FAIL, rework required

- PR: #24
- Review: `PRR_kwDOJBBaD88AAAABM_bHXQ`
- Date: 2026-09-10
- Outcome: **FAIL — rework required**
- Blocking finding: archived `jsonStream` timestamp/order was treated as proven historical availability evidence without establishing publication-time semantics or archive revision fidelity.
- Product Owner decision: none required.

### Rework

The design now:

1. separates `ArchiveRecordKey` (frozen archive structure) from `SourceAvailabilityKey` (validated historical availability claim);
2. introduces a scoped `AvailabilityAuthorityValidation` gate with explicit timestamp-meaning and archive-revision-fidelity requirements;
3. classifies the currently inspected historical FastF1 archive as `UNVERIFIED_ARCHIVE` until verification establishes stronger authority for a specific endpoint/era;
4. forbids unverified archives from creating prediction checkpoints or contributing mutable facts, while allowing optional unverified domains to be omitted explicitly;
5. makes source/era support a versioned verification matrix rather than an assumption that all archived seasons are reconstructable;
6. adds authority validation to source, fact, observation, run-provenance, failure-code, and downstream contracts;
7. adds explicit verification obligations for archive publication semantics and revision behavior, not merely parser preservation of current file order/timestamps.

### Bounded re-review

Required under `governance/REVIEW_POLICY.md`. It should verify the prior Blocking finding, regressions introduced by this rework, and the original #18 acceptance criteria. It is not a fresh unlimited review.
