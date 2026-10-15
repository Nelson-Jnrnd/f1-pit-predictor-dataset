"""Bounded B0 preview: frozen 2024 Spain -> Austria, Python standard library.

Owners remain separate functions: source/authority, observation, initialization,
resolution, development join/fit, replay, retrospective join, export. Resolution
objects are never passed to reconstruction, initialization, or replay.
"""
from __future__ import annotations
import argparse
import copy
import datetime as dt
import email.utils
import gzip
from functools import cache
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'research/development-race/sources'
VERSION = 'development-preview/v1'
AUTHORITY = 'verification/SUPPORT_MATRIX.md#Error model and bounds for scope S-RD'
ASSUMPTIONS = ['RA-1 recorder approximately public receipt (3 s)',
               'RA-2 shared recorder clock for admitted endpoints',
               'RA-3 in-stream delivery and occurrence order',
               'RA-4 race-day files retain delivered versions']
SEMANTICS = ['decisions/2026-09-08-v2-pit-event-scope.md', 'decisions/2026-09-09-v2-prediction-output-semantics.md']
DEPENDENCY_LOCK = 'Python-3.12-standard-library/v1'

@cache
def revision():
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()

FEEDS = {'TimingData', 'SessionStatus', 'TimingAppData', 'LapCount',
         'DriverList', 'RaceControlMessages'}
# Fixed reviewed protocol partitions; deny before opening any path or record.
def require_development(season, rnd):
    if not ((season == 2024 and 10 <= rnd <= 24) or
            (season == 2025 and 1 <= rnd <= 24)):
        raise ValueError('Protected or unsupported race: development-only operation refused')


def encoded(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(x):
    return hashlib.sha256(encoded(x)).hexdigest()


def artifact(kind, **values):
    x = {'kind': kind, **values}
    return {'artifact_id': digest(x), **x}


def merge(a, b):
    # Indexed delta dictionaries and arrays are merged, never replaced by a sparse update.
    for k, v in b.items():
        if isinstance(v, list):
            v = {str(i): s for i, s in enumerate(v)}
        if isinstance(v, dict):
            if not isinstance(a.get(k), dict):
                a[k] = {}
            merge(a[k], v)
        else:
            a[k] = v


def seconds(v):
    if not isinstance(v, str) or not v.strip():
        return None
    try:
        s = 0.0
        for part in v.lstrip('+').split(':'):
            s = s * 60 + float(part)
        return s if math.isfinite(s) and s >= 0 else None
    except ValueError:
        return None


def utc(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()


def read_source(season, rnd, directory=None):
    require_development(season, rnd)
    d = Path(directory) if directory is not None else SOURCES / str(rnd)
    m = json.loads((d / 'manifest.json').read_text())
    if (m['season'], m['round'], m['session']) != (season, rnd, 'R'):
        raise ValueError('Source identity mismatch')
    if set(m['files']) != FEEDS:
        raise ValueError('Missing or unvalidated endpoint')
    result = {}
    for feed, meta in m['files'].items():
        last = email.utils.parsedate_to_datetime(meta['last_modified']).date()
        date = dt.date.fromisoformat(m['date'])
        if last not in (date, date + dt.timedelta(days=1)):
            raise ValueError('Rewritten archive has no availability authority')
        raw = gzip.decompress((d / (feed + '.jsonStream.gz')).read_bytes())
        if hashlib.sha256(raw).hexdigest() != meta['sha256'] or len(raw) != meta['bytes']:
            raise ValueError('Source bytes disagree with frozen manifest')
        records = []
        for i, line in enumerate(raw.decode('utf-8-sig').splitlines()):
            p = seconds(line[:12])
            if p is None or (records and p < records[-1]['prefix']):
                raise ValueError('Malformed or regressing source prefix')
            records.append({'stream': feed, 'ordinal': i, 'prefix': p,
                            'payload': json.loads(line[12:]),
                            'ref': f"{meta['sha256']}:{i}"})
        if not records:
            raise ValueError('Empty required source')
        result[feed] = records
        meta.update(record_count=len(records), first_prefix=records[0]['prefix'],
                    last_prefix=records[-1]['prefix'], authority='VERIFIED_BOUNDED_TIME',
                    validation_ref=AUTHORITY)
    return artifact('SourceSnapshotManifest', **m, residual_assumptions=ASSUMPTIONS), result


def clock_evidence(records, allow_restarts=False):
    status = records['SessionStatus']
    starts = [r['prefix'] for r in status if r['payload']['Status'] == 'Started']
    ends = [r['prefix'] for r in status if r['payload']['Status'] == 'Finished']
    if not starts or not ends or (not allow_restarts and (len(starts) != 1 or len(ends) != 1)):
        raise ValueError('Preview provider has no validated restart implementation')
    start, end = starts[0], ends[-1]
    if allow_restarts and (any(p >= end for p in starts) or any(p < start for p in ends)):
        raise ValueError('Unsupported lifecycle ordering')
    advance, last, checks, flagged = {}, {}, [], []
    for r in records['TimingData']:
        p = r['prefix']
        for d, v in r['payload'].get('Lines', {}).items():
            if 'LastLapTime' in v and seconds(v['LastLapTime'].get('Value')) is not None:
                last[d] = (p, seconds(v['LastLapTime']['Value']))
            n = v.get('NumberOfLaps')
            if isinstance(n, int):
                if d in advance and n == advance[d][1] + 1 and d in last and abs(last[d][0] - p) < 1:
                    err = p - advance[d][0] - last[d][1]
                    if start <= p <= end:
                        checks.append((p, err))
                    if abs(err) > 1:
                        flagged.append((advance[d][0], p, d, abs(err)))
                advance[d] = (p, n)
    windows = []
    for a, b, d, e in sorted(flagged):
        if windows and a <= windows[-1][1]:
            w = windows[-1]; w[1] = max(w[1], b); w[2].add(d); w[3] = max(w[3], e)
        else:
            windows.append([a, b, {d}, e])
    unhealthy = [[a, b] for a, b, ds, _ in windows if len(ds) >= 2]
    anchors = []
    for r in records['RaceControlMessages']:
        messages = r['payload'].get('Messages', {})
        for m in messages.values() if isinstance(messages, dict) else messages:
            if start <= r['prefix'] <= end and 'Utc' in m:
                anchors.append((r['prefix'], utc(m['Utc']) - r['prefix']))
    if not anchors or not checks:
        raise ValueError('Missing clock evidence')
    base = statistics.median(o for _, o in anchors)
    valid = [p for p, o in anchors if -1.2 <= o - base <= .7]
    ts = sorted(p for p, _ in checks)
    # Sparse intervals are unhealthy except where a qualifying RCM anchor is within 60 s.
    for a, b in zip([start] + ts, ts + [end]):
        if b - a <= 120:
            continue
        pieces = [[a, b]]
        for p in valid:
            nxt = []
            for lo, hi in pieces:
                if p + 60 < lo or p - 60 > hi:
                    nxt.append([lo, hi]); continue
                if lo < p - 60:
                    nxt.append([lo, p - 60])
                if p + 60 < hi:
                    nxt.append([p + 60, hi])
            pieces = nxt
        unhealthy.extend(pieces)
    return artifact('AvailabilityAuthorityValidation', start=start, end=end,
                    unhealthy=sorted(unhealthy), lap_checks=len(checks),
                    max_lap_residual=max(abs(e) for _, e in checks),
                    rcm_deviation=[min(o-base for _, o in anchors), max(o-base for _, o in anchors)],
                    bounds_seconds=5, cross_stream_margin=10, prerace_margin=300,
                    validation_ref=AUTHORITY, residual_assumptions=ASSUMPTIONS,
                    unsupported_domains=['positions', 'telemetry', 'weather', 'track_status', 'minis'])


def healthy(p, clock):
    return p <= clock['end'] and not any(a <= p <= b for a, b in clock['unhealthy'])


def admitted(r, boundary, clock):
    p, t = r['prefix'], boundary['prefix']
    if p < clock['start']:
        return p + 300 < clock['start'] - 5
    if not healthy(p, clock) or not healthy(t, clock):
        return False
    if r['stream'] == boundary['stream']:
        return p <= t and r['ordinal'] <= boundary['ordinal']
    return p + 5 < t - 5


def reduce_stream(rs, boundary, clock, lines=True):
    state, refs = {}, []
    for r in rs:
        if admitted(r, boundary, clock):
            payload = r['payload'].get('Lines', {}) if lines else r['payload']
            # Nonpositive distance updates are invalid facts, not retractions.
            if not lines and 'TotalLaps' in payload and payload['TotalLaps'] <= 0:
                payload = {k: v for k, v in payload.items() if k != 'TotalLaps'}
            merge(state, payload); refs.append(r['ref'])
    return state, refs


class CausalReducer:
    """Single forward pass per source with leaf-level lineage, no future interpolation."""
    def __init__(self, rs, clock, lines):
        self.rs, self.clock, self.lines = rs, clock, lines
        self.index, self.state, self.refs = 0, {}, {}

    def at(self, boundary):
        while self.index < len(self.rs):
            r = self.rs[self.index]
            # Do not let a future unhealthy update change current omissions.
            if r['prefix'] > boundary['prefix'] or (r['stream']==boundary['stream'] and r['ordinal']>boundary['ordinal']):
                break
            if r['prefix'] >= self.clock['start'] and not healthy(r['prefix'], self.clock):
                payload=r['payload'].get('Lines',{}) if self.lines else r['payload']
                def invalidate(dst,value,path=()):
                    if isinstance(value,list): value={str(i):v for i,v in enumerate(value)}
                    if isinstance(value,dict):
                        for k,v in value.items():
                            if isinstance(v,(dict,list)) and isinstance(dst.get(k),dict):
                                invalidate(dst[k],v,path+(k,))
                            else:
                                dst.pop(k,None)
                                for old in list(self.refs):
                                    if old[:len(path)+1]==path+(k,): self.refs.pop(old)
                            if k in ('NumberOfLaps','LastLapTime'): dst.pop('_last_time_completed_lap',None)
                invalidate(self.state,payload)
                self.index += 1
                continue
            if not admitted(r, boundary, self.clock):
                if r['prefix'] < self.clock['start']:
                    self.index += 1
                    continue
                break
            payload = r['payload'].get('Lines', {}) if self.lines else r['payload']
            if not self.lines and 'TotalLaps' in payload and payload['TotalLaps'] <= 0:
                payload = {k:v for k,v in payload.items() if k != 'TotalLaps'}
            merge(self.state,payload)
            if r['stream']=='TimingData':
                for driver, update in payload.items():
                    if 'LastLapTime' in update:
                        self.state[driver]['_last_time_completed_lap'] = self.state[driver].get('NumberOfLaps',0)
            def lineage(value, path=()):
                if isinstance(value,list): value={str(i):v for i,v in enumerate(value)}
                if isinstance(value,dict):
                    for k,v in value.items(): lineage(v,path+(k,))
                else: self.refs[path]=r['ref']
            lineage(payload)
            self.index += 1
        return copy.deepcopy(self.state), sorted(set(self.refs.values()))


def reconstruct(source, records, clock, reducer_factory=CausalReducer):
    observation_run_id = str(uuid.uuid4())
    race = f"{source['season']}-R{source['round']}-R"
    start_trigger = next(r for r in records['SessionStatus'] if r['payload']['Status'] == 'Started')
    roster, roster_refs = reduce_stream(records['DriverList'], start_trigger, clock, lines=False)
    drivers = []
    for key, d in roster.items():
        if not isinstance(d, dict) or d.get('RacingNumber') != key or not d.get('Tla'):
            raise ValueError('Driver identity not established before start')
        drivers.append(dict(id=key, code=d['Tla'], name=d.get('FirstName', '') + ' ' + d.get('LastName', ''),
                            team=d['TeamName'], color='#' + d['TeamColour']))
    drivers.sort(key=lambda d: int(d['id']))
    triggers = {d['id']: {0: start_trigger} for d in drivers}
    counts = {d['id']: 0 for d in drivers}
    for r in records['TimingData']:
        if r['prefix'] < clock['start']:
            continue
        for d, v in r['payload'].get('Lines', {}).items():
            if d not in counts:
                raise ValueError('Timing driver absent in causal roster')
            n = v.get('NumberOfLaps')
            if not isinstance(n, int):
                continue
            if n < counts[d] or n > counts[d] + 1:
                raise ValueError('Lap jump/regression: bounded preview refuses unsupported session')
            if n > counts[d]:
                triggers[d].setdefault(n, r)
            counts[d] = n
    attempts, observations = [], []
    states = {}
    all_triggers = {r['ref']:r for ds in triggers.values() for r in ds.values()}
    for trigger_stream in ('SessionStatus','TimingData'):
        reducers = {feed:reducer_factory(records[feed],clock,feed not in ('SessionStatus','LapCount'))
                    for feed in ('TimingData','TimingAppData','SessionStatus','LapCount')}
        for trigger in sorted((r for r in all_triggers.values() if r['stream']==trigger_stream),key=lambda r:r['ordinal']):
            if healthy(trigger['prefix'],clock):
                states[trigger['ref']]={feed:reducer.at(trigger) for feed,reducer in reducers.items()}
    # Enumerate using frozen counter maximum; never use it as a state input.
    for d in drivers:
        for lap in range(counts[d['id']] + 1):
            trigger = triggers[d['id']].get(lap)
            key = [race, d['id'], lap]
            attempt = dict(attempt_key=key, attempt_level='CHECKPOINT', driver=d['id'], lap=lap,
                           trigger=trigger, status='INDETERMINATE_CHECKPOINT')
            if trigger and healthy(trigger['prefix'], clock):
                timing, tr = states[trigger['ref']]['TimingData']
                tyres, yr = states[trigger['ref']]['TimingAppData']
                session, sr = states[trigger['ref']]['SessionStatus']
                distance, nr = states[trigger['ref']]['LapCount']
                obs = artifact('CanonicalObservation', semantic_observation_key=key,
                    prediction_boundary={k: trigger[k] for k in ('stream', 'ordinal', 'prefix', 'ref')},
                    selected_driver_completed_laps=lap,
                    canonical_state=dict(timing=timing, tyres=tyres, session=session, distance=distance),
                    causal_input_fact_refs=tr+yr+sr+nr+roster_refs,
                    source_snapshot_manifest_ref=source['artifact_id'], authority_validation_ref=clock['artifact_id'],
                    quality=dict(status='VALID_WITH_OMISSIONS', omitted_domains=clock['unsupported_domains']),
                    reconstruction_policy_version=VERSION,
                    provenance=dict(observation_reconstruction_run_ref=observation_run_id, repository_revision=revision(),
                                    source_adapter_version='archive-prefix/v1', semantic_refs=SEMANTICS))
                attempt.update(status='VALID_WITH_OMISSIONS', observation_artifact_ref=obs['artifact_id'])
                observations.append(obs)
            attempt['reason_codes'] = [] if 'observation_artifact_ref' in attempt else ['COARSE_TIME_AMBIGUITY']
            attempts.append(attempt)
    manifest = artifact('ObservationReconstructionRun', observation_reconstruction_run_id=observation_run_id, repository_revision=revision(), dependency_lock_ref=DEPENDENCY_LOCK, source_snapshot_manifest_ref=source['artifact_id'],
        authority_validation_ref=clock['artifact_id'], drivers=drivers,
        non_checkpoint_records=[dict(attempt_level='SESSION', race_session_key=race, status='ESTABLISHED')] +
            [dict(attempt_level='DRIVER_ENTRY', race_session_key=race, driver_entry_key=d['id'], status='ESTABLISHED') for d in drivers],
        records=attempts, observations=observations)
    return manifest


def initialize(observation_run):
    initialization_run_id = str(uuid.uuid4())
    records = []
    for o in observation_run['observations']:
        race, d, lap = o['semantic_observation_key']
        v = o['canonical_state']['timing'].get(d, {})
        # A stopped car alone is not proof of permanent retirement.
        status = 'INELIGIBLE' if v.get('Retired') is True else 'ELIGIBLE'
        if v.get('Stopped') and status == 'ELIGIBLE':
            status = 'INDETERMINATE'
        # Known finished session plus this driver's new completion: causal terminal proof.
        if o['canonical_state']['session'].get('Status') in ('Finished', 'Finalised', 'Ends'):
            status = 'INELIGIBLE'
        decision = artifact('EligibilityDecision', observation_artifact_ref=o['artifact_id'], status=status,
                            causal_input_fact_refs=o['causal_input_fact_refs'], target_definition_version='tyre-service-entry/v1',
                            initialization_policy_version=VERSION, semantic_observation_key=o['semantic_observation_key'],
                            provenance=dict(target_initialization_run_ref=initialization_run_id, repository_revision=revision()))
        row = dict(observation_artifact_ref=o['artifact_id'], eligibility_decision=decision,
                   eligibility_status=status)
        if status == 'ELIGIBLE':
            row['initialization'] = artifact('TargetEpisodeInitialization',
                observation_artifact_ref=o['artifact_id'], eligibility_decision_ref=decision['artifact_id'],
                target_episode_key=[o['artifact_id'], 'tyre-service-entry/v1'],
                prediction_boundary_ref=o['prediction_boundary'], driver_entry_key=d,
                semantic_observation_key=o['semantic_observation_key'], target_definition_version='tyre-service-entry/v1',
                initialization_policy_version=VERSION)
        records.append(row)
    return artifact('TargetInitializationRun', target_initialization_run_id=initialization_run_id, repository_revision=revision(), observation_reconstruction_run_ref=observation_run['artifact_id'], records=records)


def retrospective_catalog(records, clock, source, allow_restarts=False):
    """Target-owned retrospective traversal. No output enters causal observations."""
    visits, laps, state, advance = {}, {}, {}, {}
    for r in records['TimingData']:
        p = r['prefix']
        for d, v in r['payload'].get('Lines', {}).items():
            old = state.setdefault(d, {})
            merge(old, v)
            if 'NumberOfLaps' in v:
                advance[d] = r
                laps.setdefault(d, []).append((p, v['NumberOfLaps'], r['ordinal'], r['ref']))
            if v.get('InPit') is True and not old.get('_previous_pit', False) and clock['start'] <= p <= clock['end']:
                visits.setdefault(d, []).append(dict(entry=p, ordinal=r['ordinal'], completed=old.get('NumberOfLaps', 0),
                    entry_ref=r['ref'], service='INDETERMINATE_TYRE_SERVICE'))
            if 'InPit' in v:
                old['_previous_pit'] = v['InPit']
    # Determine terminal bounds: finishing completion after Finished; retire/stopped after last advance.
    terminal = {}
    for d, seq in laps.items():
        finishing = next((x for x in seq if x[0] >= clock['end']), None)
        if finishing is not None:
            terminal[d] = artifact('TerminalBoundary', bounds=[finishing[0]-5,finishing[0]+5], driver_entry_key=d,
                terminal_kind='DRIVER_PARTICIPATION_TERMINAL', method_version='finish-crossing-after-leader/v1',
                evidence_refs=[finishing[3]]+[r['ref'] for r in records['SessionStatus'] if r['payload']['Status']=='Finished'],
                support_validation_ref=AUTHORITY)
            continue
        last_advance = seq[-1][0]
        end_flag = next((r for r in records['TimingData'] if last_advance <= r['prefix'] <= clock['end']
                        and any(v.get('Retired') is True or v.get('Stopped') is True
                                for k, v in r['payload'].get('Lines', {}).items() if k == d)
                        and (not allow_restarts or
                             not any(s['payload'].get('Status') == 'Started' and s['prefix'] > r['prefix']
                                     for s in records['SessionStatus']) or
                             r['payload'].get('Lines', {}).get(d, {}).get('Retired') is True)), None)
        terminal[d] = artifact('TerminalBoundary',bounds=[last_advance-5,end_flag['prefix']+5],driver_entry_key=d,
            terminal_kind='DRIVER_PARTICIPATION_TERMINAL',method_version='last-advance-to-terminal-flag/v1',
            evidence_refs=[seq[-1][3],end_flag['ref']],support_validation_ref=AUTHORITY) if end_flag is not None else None
    for d, vs in visits.items():
        for i, v in enumerate(vs):
            hi = vs[i+1]['entry'] if i+1 < len(vs) else clock['end'] + 5
            stints, refs = {}, []
            for r in records['TimingAppData']:
                if v['entry'] <= r['prefix'] < hi:
                    update = r['payload'].get('Lines', {}).get(d, {}).get('Stints')
                    if update is not None:
                        merge(stints, {str(j): s for j, s in enumerate(update)} if isinstance(update, list) else update)
                        refs.append(r['ref'])
            if stints:
                last = stints[max(stints, key=int)]
                if last.get('TyresNotChanged') == '0':
                    v['service'] = 'CONFIRMED_TYRE_SERVICE'
            # NEG alone is not proof. Penalty visits conservatively remain indeterminate.
            v['service_evidence_refs'] = refs
            v['kind']='ReconstructedPitVisitArtifact'
            v['source_snapshot_manifest_ref']=source['artifact_id']
            v['source_lineage']=[v['entry_ref']]+refs
            v['support_validation_ref']=AUTHORITY
            v['pit_entry_occurrence']=dict(lower_bound=v['entry']-5,upper_bound=v['entry']+5,source_evidence_refs=[v['entry_ref']])
            v['visit_artifact']=artifact('ReconstructedPitVisitArtifact',**{k:value for k,value in v.items() if k!='kind'})
            term=terminal.get(d)
            if v['service']=='CONFIRMED_TYRE_SERVICE' and term and v['entry']+5<term['bounds'][0]:
                v['qualifying_event']=artifact('QualifyingPitEventArtifact', pit_visit_ref=v['visit_artifact']['artifact_id'],
                    driver_entry_key=d,pit_entry_occurrence=v['pit_entry_occurrence'],
                    service_qualification='CONFIRMED_TYRE_SERVICE',source_lineage=v['source_lineage'],
                    race_participation_scope='RACE_PARTICIPATION',terminal_boundary_ref=term['artifact_id'],
                    visit_terminal_relation='STRICTLY_BEFORE_TERMINAL',support_validation_ref=AUTHORITY)
            # The enclosing catalog binds the visit and its independently typed event.

    return artifact('RetrospectiveCatalog', visits=visits, terminal=terminal, source_snapshot_manifest_ref=source['artifact_id'],
                    coverage=dict(source_record_integrity='PASS', streams={f:dict(record_count=len(rs),first_prefix=rs[0]['prefix'],last_prefix=rs[-1]['prefix']) for f,rs in records.items()},
                                  unsupported_windows=clock['unhealthy'],validated_capabilities=['pit-entry','service-positive','lap-counter','terminal-bounds'],
                                  support_validation_ref=AUTHORITY),
                    method_version=VERSION, validation_ref=AUTHORITY,
                    limitations=['No independent tyre-change ground truth', 'Penalty negatives conservatively indeterminate'])


def resolve(initializations, observations, catalog, clock):
    resolution_run_id = str(uuid.uuid4())
    by_id = {o['artifact_id']: o for o in observations}
    resolutions = []
    for row in initializations['records']:
        if row['eligibility_status'] != 'ELIGIBLE':
            continue
        init = row['initialization']; o = by_id[init['observation_artifact_ref']]
        boundary = o['prediction_boundary']; p = boundary['prefix']; d = init['driver_entry_key']
        terminal_artifact = catalog['terminal'].get(d)
        terminal = terminal_artifact['bounds'] if terminal_artifact else None
        gaps=[w for w in clock['unhealthy'] if terminal and w[0]<=terminal[1] and w[1]>=p-5]
        reasons=['TERMINAL_EVIDENCE_MISSING'] if not terminal else ['TERMINAL_BOUNDARY_OVERLAPS_PREDICTION'] if terminal[0]<=p+5 else ['CLOCK_UNHEALTHY_COVERAGE_GAP'] if gaps else []
        status, event = 'TRUNCATED_INDETERMINATE', None
        if terminal and terminal[0] > p + 5 and not any(a <= terminal[1] and b >= p-5 for a, b in clock['unhealthy']):
            status = 'TERMINAL_NO_EVENT'
            for v in catalog['visits'].get(d, []):
                if boundary['stream'] == 'TimingData' and v['ordinal'] <= boundary['ordinal']:
                    continue
                if v['entry'] + 5 <= p - 5:
                    continue
                if v['entry'] - 5 >= terminal[1]:
                    continue
                ordered = boundary['stream'] == 'TimingData' and v['ordinal'] > boundary['ordinal']
                if (not ordered and v['entry'] - 5 <= p + 5) or v['entry'] + 5 >= terminal[0] or v['service'] != 'CONFIRMED_TYRE_SERVICE':
                    reasons=['INDETERMINATE_TYRE_SERVICE'] if v['service']!='CONFIRMED_TYRE_SERVICE' else ['ENTRY_BOUNDARY_OVERLAP']
                    status = 'TRUNCATED_INDETERMINATE'; break
                status, event = 'OBSERVED_EVENT', v
                break
        fields = dict(target_episode_key=init['target_episode_key'], observation_artifact_ref=o['artifact_id'],
                      resolution_state=status, terminal_boundary=terminal_artifact,
                      evidence_coverage=dict(at_risk_interval=[p-5,terminal[1] if terminal else None],gaps=gaps,
                          status='COMPLETE' if not reasons else 'INDETERMINATE',catalog_coverage_ref=catalog['artifact_id'],
                          source_snapshot_manifest_ref=catalog['source_snapshot_manifest_ref'],required_capabilities=catalog['coverage']['validated_capabilities']),
                      truncation_reason_codes=reasons if status=='TRUNCATED_INDETERMINATE' else [],
                      catalog_ref=catalog['artifact_id'], resolution_policy_version=VERSION, resolution_run_ref=resolution_run_id)
        if event:
            fields.update(qualifying_event_ref=event['qualifying_event']['artifact_id'], entry_lap_context=artifact('EntryLapContext',
                qualifying_event_ref=event['qualifying_event']['artifact_id'], c_exact=event['completed'], entry_ref=event['entry_ref'],
                derivation_version='stream-counter/v1', validation_ref=AUTHORITY))
        resolutions.append(artifact('TargetResolutionArtifact', **fields))
    return artifact('ResolutionRun', resolution_run_id=resolution_run_id, repository_revision=revision(), target_initialization_run_ref=initializations['artifact_id'], records=resolutions)


def grid(o):
    n = o['canonical_state']['distance'].get('TotalLaps')
    lap = o['selected_driver_completed_laps']
    if not isinstance(n, int) or n <= 0:
        raise ValueError('REQUIRED_CONTEXT_MISSING')
    return dict(L=lap, N_T=n, K_T=max(1, n-lap), region_representation_version='driver-lap-offset/v1')


def map_outcome(o, resolution):
    g = grid(o)
    state = resolution['resolution_state']
    if state == 'TRUNCATED_INDETERMINATE':
        return dict(kind='NOT_REALIZED')
    if state == 'TERMINAL_NO_EVENT':
        return dict(kind='REALIZED_NO_EVENT')
    c = resolution.get('entry_lap_context', {}).get('c_exact')
    if c is None:
        return dict(kind='MAPPING_UNAVAILABLE')
    if c < g['L']:
        return dict(kind='MAPPING_CONFLICT')
    return dict(kind='REALIZED_REGION', j=min(c-g['L'], g['K_T']-1), in_lap=c+1)


def fit_b0(observation_run, initializations, resolutions, source, cutoff, ledger):
    require_development(source['season'], source['round'])
    if dt.date.fromisoformat(source['date']) >= dt.date.fromisoformat(cutoff):
        raise ValueError('Training race must conclude before cutoff')
    ledger.append(dict(race=[source['season'], source['round']], opening='DEVELOPMENT_JOIN',
                       resolution_run_ref=resolutions['artifact_id']))
    by_id = {o['artifact_id']: o for o in observation_run['observations']}
    risk, events, final_risk, final_none, accounting = [0]*41, [0]*41, 0, 0, []
    for r in resolutions['records']:
        o = by_id[r['observation_artifact_ref']]
        try:
            g = grid(o); outcome = map_outcome(o, r)
        except ValueError:
            accounting.append(dict(observation=o['artifact_id'], category='REQUIRED_CONTEXT_MISSING')); continue
        accounting.append(dict(observation=o['artifact_id'], outcome=outcome, resolution_ref=r['artifact_id']))
        if outcome['kind'] not in ('REALIZED_REGION', 'REALIZED_NO_EVENT'):
            continue
        j = outcome.get('j', g['K_T'])
        for h in range(min(j+1, g['K_T']-1)):
            risk[min(h,40)] += 1
            if h == j:
                events[min(h,40)] += 1
        if j >= g['K_T']-1:
            final_risk += 1
            final_none += outcome['kind'] == 'REALIZED_NO_EVENT'
    if not final_risk or not any(risk):
        raise ValueError('B0 fit lacks empirical support; no invented hazards allowed')
    development_run_id = str(uuid.uuid4())
    procedure = artifact('ProcedureSpec', estimator='B0', input_view_version='grid-only/v1', output_form='PMF',
                         fitting_rule='pooled-offset-hazard-0..39+40-tail', floor=1e-6,
                         missing_risk_rule='prediction-failure', truncated_handling='excluded',
                         selection_evidence_refs=[], inference_seed_policy='deterministic')
    model = artifact('ModelArtifact', model_family_label='B0 climatology',
        output_form='PMF', hazards=[e/r if r else None for e,r in zip(events,risk)], q_open=final_none/final_risk,
        region_representation_version='driver-lap-offset/v1', input_view_version='grid-only/v1',
        prediction_contract_version='prediction/v1', development_temporal_boundary_ref=cutoff,
        fitting_counts=dict(risk=risk, events=events, final_risk=final_risk, final_none=final_none),
        source_snapshot_manifest_ref=source['artifact_id'], selection_evidence_refs=[],
        floor=1e-6, randomness='deterministic', normalization_applied=False,
        development_run_ref=development_run_id, development_dataset_refs=[observation_run['artifact_id'],resolutions['artifact_id']],
        procedure_id=procedure['artifact_id'], repository_revision=revision(), dependency_lock_ref=DEPENDENCY_LOCK)
    return artifact('DevelopmentRun', development_run_id=development_run_id, procedure_spec=procedure, repository_revision=revision(), dependency_lock_ref=DEPENDENCY_LOCK, protocol_id='B0-prespecified-preview/v1',
        partition_role='DEVELOPMENT_FIT', cutoff=cutoff, accounting=accounting,
        observation_run_ref=observation_run['artifact_id'], initialization_run_ref=initializations['artifact_id'],
        resolution_run_ref=resolutions['artifact_id'], model=model)


def distribution(model, g):
    k = g['K_T']; s = 1.; p = []
    for h in range(k-1):
        rate = model['hazards'][min(h,40)]
        if rate is None:
            raise ValueError('ESTIMATOR_ERROR: B0 offset has no training support')
        p.append(s*rate); s *= 1-rate
    p.append(s*(1-model['q_open'])); q = s*model['q_open']
    f = model['floor']; scale = 1 - (k+1)*f
    if scale < 0:
        raise ValueError('Grid too large for declared floor')
    p = [v*scale+f for v in p]; q = q*scale+f
    if not all(math.isfinite(v) and 0 <= v <= 1 for v in p+[q]) or abs(sum(p)+q-1)>1e-9:
        raise ValueError('Invalid canonical distribution')
    return dict(region_grid=g, event_region_probabilities=p, terminal_no_event_probability=q)


def window(p):
    total = sum(p)
    if total == 0:
        return None
    target = .8*total; candidates = []
    for a in range(len(p)):
        mass = 0.
        for b in range(a,len(p)):
            mass += p[b]
            if mass >= target-1e-12:
                candidates.append((b-a+1,-mass,a,b))
    _, _, a, b = min(candidates)
    return dict(a=a,b=b,before=sum(p[:a]),inside=sum(p[a:b+1]),after=sum(p[b+1:]))


def replay(observation_run, initialization_run, model, date, run_id):
    if (model.get('region_representation_version'),model.get('input_view_version'),model.get('prediction_contract_version')) != ('driver-lap-offset/v1','grid-only/v1','prediction/v1'):
        raise ValueError('MODEL_INCOMPATIBLE')
    if initialization_run['observation_reconstruction_run_ref'] != observation_run['artifact_id']:
        raise ValueError('Initialization lineage mismatch')
    if dt.date.fromisoformat(model['development_temporal_boundary_ref']) > dt.date.fromisoformat(date):
        raise ValueError('Model cutoff after replay race')
    # No resolutions, catalog, raw sources, or outcome reference is an argument.
    observations = {o['artifact_id']: o for o in observation_run['observations']}
    initialized = {r['observation_artifact_ref']:r for r in initialization_run['records']}
    records = []
    for attempt in observation_run['records']:
        ref = attempt.get('observation_artifact_ref'); row = dict(attempt_key=attempt['attempt_key'],
            attempt_status=attempt['status'], observation_artifact_ref=ref)
        if ref:
            o = observations[ref]; init = initialized[ref]; row['eligibility_status']=init['eligibility_status']
            if init['eligibility_status'] == 'ELIGIBLE':
                ep = init['initialization']; row['target_episode_initialization_ref']=ep['artifact_id']
                try:
                    g = grid(o); dist = distribution(model,g)
                    request = dict(region_grid=g, input_view={}, model_artifact_ref=model['artifact_id'], inference_seed=None)
                    row['snapshot'] = artifact('PredictionSnapshot', prediction_run_ref=run_id,
                        observation_artifact_ref=ref, target_episode_key=ep['target_episode_key'],
                        target_episode_initialization_ref=ep['artifact_id'], eligibility_decision_ref=init['eligibility_decision']['artifact_id'],
                        model_artifact_ref=model['artifact_id'], prediction_boundary_ref=o['prediction_boundary'],
                        prediction_key=[ep['target_episode_key'],model['artifact_id'],run_id], semantic_observation_key=o['semantic_observation_key'],
                        prediction_contract_version='prediction/v1', input_view_version='grid-only/v1', input_view_digest=digest({}),
                        semantic_refs=SEMANTICS, prediction_procedure_revision=revision(), recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                        distribution=dist, request_digest=digest(request), content_digest=digest([digest(request),dist]),
                        validation='PASS', adapter_version='b0-floored-pmf/v1', normalization_applied=False)
                    row['window'] = artifact('PitWindowSummary', snapshot_id=row['snapshot']['artifact_id'],
                        window_rule_version='pit-window/v1', alpha=.8, window=window(dist['event_region_probabilities']))
                except ValueError as e:
                    row['prediction_failure'] = artifact('PredictionFailureRecord', observation_artifact_ref=ref,
                        failure_codes=[str(e)], prediction_run_ref=run_id, target_episode_initialization_ref=ep['artifact_id'])
        records.append(row)
    return artifact('ReplayRunManifest', replay_run_id=run_id, status='COMPLETED',
        repository_revision=revision(), dependency_lock_ref=DEPENDENCY_LOCK, protocol_id='B0-prespecified-preview/v1',
        partition_role='DEVELOPMENT_VALIDATION', observation_run_ref=observation_run['artifact_id'],
        initialization_run_ref=initialization_run['artifact_id'], model_artifact_ref=model['artifact_id'], records=records,
        non_checkpoint_records=observation_run['non_checkpoint_records'])


def retrospective_join(source, observations, replay_run, resolutions, ledger):
    require_development(source['season'], source['round'])
    ledger.append(dict(race=[source['season'],source['round']], opening='DEVELOPMENT_JOIN',
                       resolution_run_ref=resolutions['artifact_id']))
    by_id = {o['artifact_id']:o for o in observations}
    by_res = {r['observation_artifact_ref']:r for r in resolutions['records']}
    result = []
    for r in replay_run['records']:
        ref = r.get('observation_artifact_ref'); res = by_res.get(ref)
        mapped = map_outcome(by_id[ref],res) if res and 'snapshot' in r else dict(kind='MAPPING_UNAVAILABLE')
        snapshot=r.get('snapshot',{})
        if snapshot and res and (res['target_episode_key']!=snapshot['target_episode_key'] or res['observation_artifact_ref']!=snapshot['observation_artifact_ref']):
            raise ValueError('Retrospective episode/observation mismatch')
        result.append(dict(attempt_key=r['attempt_key'],resolution_ref=res['artifact_id'] if res else None,
                           observation_ref=ref,target_episode_key=snapshot.get('target_episode_key'),
                           initialization_ref=snapshot.get('target_episode_initialization_ref'),
                           snapshot_ref=snapshot.get('artifact_id'),mapped=mapped))
    return artifact('DevelopmentRetrospectiveProjection', replay_run_ref=replay_run['artifact_id'],
                    resolution_run_ref=resolutions['artifact_id'], records=result, ledger_role='DEVELOPMENT')


def tyre_context(state, d):
    stints = state['tyres'].get(d,{}).get('Stints', {})
    if not stints:
        return dict(compound=None,age=None)
    s = stints[max(stints,key=int)]
    compound = s.get('Compound','').title()
    if compound not in ('Soft','Medium','Hard','Intermediate','Wet'):
        compound = None
    age = s.get('TotalLaps')
    return dict(compound=compound,age=age if isinstance(age,int) and age>=0 else None)


def timing_rows(state, drivers, race_start=False):
    rows=[]
    for d in drivers:
        key=d['id']; v=state['timing'].get(key,{})
        position=v.get('Position'); position=int(position) if str(position).isdigit() else None
        gap=v.get('GapToLeader'); inter=v.get('IntervalToPositionAhead',{}).get('Value')
        rows.append(dict(driver=key,position=position,gap=seconds(gap),interval=seconds(inter),
            gapText=gap if isinstance(gap,str) and 'LAP' in gap.upper() else None,
            intervalText=inter if isinstance(inter,str) and 'LAP' in inter.upper() else None,
            completed=v.get('NumberOfLaps',0 if race_start else None),**tyre_context(state,key),
            last=seconds(v.get('LastLapTime',{}).get('Value')) if v.get('_last_time_completed_lap')==v.get('NumberOfLaps',0) else None,best=seconds(v.get('BestLapTime',{}).get('Value')),
            sectors=[None]*3,bestSectors=[None]*3,mini=['unavailable']*6,progress=None,pit=v.get('InPit')))
    return sorted(rows,key=lambda r:(r['position'] is None,r['position'] or 999,int(r['driver'])))


def verify_artifact(x):
    if not isinstance(x,dict) or x.get('artifact_id') != digest({k:v for k,v in x.items() if k!='artifact_id'}):
        raise ValueError('Artifact content digest mismatch')


def export(source, observation_run, replay_run, retro, model, clock, ledger):
    require_development(source['season'],source['round'])
    for x in (source, observation_run, replay_run, retro, model, clock):
        verify_artifact(x)
    if observation_run['source_snapshot_manifest_ref'] != source['artifact_id'] or replay_run['observation_run_ref'] != observation_run['artifact_id'] or replay_run['model_artifact_ref'] != model['artifact_id']:
        raise ValueError('Export upstream lineage mismatch')
    if replay_run['status']!='COMPLETED' or retro['replay_run_ref']!=replay_run['artifact_id']:
        raise ValueError('Incomplete or mismatched export inputs')
    if not any(e['race']==[source['season'],source['round']] and e['opening']=='DEVELOPMENT_JOIN' and e['resolution_run_ref']==retro['resolution_run_ref'] for e in ledger):
        raise ValueError('Missing development opening')
    by_id={o['artifact_id']:o for o in observation_run['observations']}
    by_retro={tuple(r['attempt_key']):r for r in retro['records']}
    expected_keys={tuple(r['attempt_key']) for r in replay_run['records']}
    if len(by_retro)!=len(retro['records']) or len(expected_keys)!=len(replay_run['records']) or set(by_retro)!=expected_keys:
        raise ValueError('Retrospective attempt set/cardinality mismatch')
    attempts=[]; frames={}; boundaries={}
    for attempt,row in zip(observation_run['records'],replay_run['records'],strict=True):
        if attempt['attempt_key']!=row['attempt_key']:
            raise ValueError('Replay attempt set mismatch')
        retrospective=by_retro[tuple(row['attempt_key'])]
        snapshot=row.get('snapshot',{})
        if (retrospective['snapshot_ref']!=snapshot.get('artifact_id') or
            retrospective.get('observation_ref')!=row.get('observation_artifact_ref') or
            retrospective.get('target_episode_key')!=snapshot.get('target_episode_key') or
            retrospective.get('initialization_ref')!=snapshot.get('target_episode_initialization_ref') or
            snapshot and not retrospective.get('resolution_ref')):
            raise ValueError('Retrospective snapshot/observation/episode/resolution join mismatch')
        trigger=attempt['trigger']
        if trigger is None:
            raise ValueError('Missing boundary cannot be fabricated for viewer')
        t=round(trigger['prefix']-clock['start'],3)
        order=trigger['ordinal']
        boundary=(t,order)
        if boundary in boundaries and boundaries[boundary]!=trigger['stream']:
            raise ValueError('Ambiguous cross-stream equal-time boundary')
        boundaries[boundary]=trigger['stream']
        o=by_id.get(row['observation_artifact_ref'])
        if o:
            frames[boundary]=dict(time=t,order=order,rows=timing_rows(o['canonical_state'],observation_run['drivers'],attempt['lap']==0))
        else:
            # Unhealthy checkpoint: no represented timing, and no repaired source context.
            frames[boundary]=dict(time=t,order=order,rows=timing_rows(dict(timing={},tyres={}),observation_run['drivers']))
        mapped=by_retro[tuple(row['attempt_key'])]['mapped']
        outcome=dict(kind='unavailable')
        if mapped['kind']=='NOT_REALIZED': outcome=dict(kind='uncertain')
        if mapped['kind']=='REALIZED_NO_EVENT': outcome=dict(kind='none')
        if mapped['kind']=='REALIZED_REGION': outcome=dict(kind='exact',start=mapped['in_lap'],end=mapped['in_lap'])
        a=dict(id=digest(attempt['attempt_key']),driver=attempt['driver'],lap=attempt['lap'],time=t,order=order,
            episode=digest([o['artifact_id'],'tyre-service-entry/v1']) if o else digest(attempt['attempt_key']),
            context=tyre_context(o['canonical_state'],attempt['driver']) if o else dict(compound=None,age=None),outcome=outcome,
            sourceAttemptRef=digest(attempt),observationRef=o['artifact_id'] if o else None,
            boundaryAvailable=o is not None)
        if 'snapshot' in row:
            s=row['snapshot']; dist=s['distribution']
            if s['model_artifact_ref']!=model['artifact_id'] or s['observation_artifact_ref']!=o['artifact_id']:
                raise ValueError('Snapshot lineage mismatch')
            validate_distribution(dist,grid(o))
            if row['window']['snapshot_id']!=s['artifact_id'] or row['window']['window']!=window(dist['event_region_probabilities']):
                raise ValueError('Window mismatch')
            a.update(state='ok',p=dist['event_region_probabilities'],q=dist['terminal_no_event_probability'],
                     window=row['window']['window'],scheduledDistance=dist['region_grid']['N_T'],snapshotRef=s['artifact_id'])
        else:
            reason=('Historical timing is uncertain at this lap.' if o is None else
                    'The driver has finished or retired.' if row.get('eligibility_status')=='INELIGIBLE' else
                    'The driver’s participation is uncertain.' if row.get('eligibility_status')=='INDETERMINATE' else
                    'The historical baseline has insufficient training evidence for this lap.' if 'prediction_failure' in row and any('ESTIMATOR_ERROR' in c for c in row['prediction_failure']['failure_codes']) else
                    'Required race information is missing.')
            a.update(state='failed',reason=reason)
        attempts.append(a)
    bundle=dict(schema=1,id='development-austria-2024-b0-v1',kind='development',race='Austrian Grand Prix',season=2024,date=source['date'],
        distance=71,drivers=observation_run['drivers'],attempts=attempts,frames=sorted(frames.values(),key=lambda f:(f['time'],f['order'])),
        raceMetadata=dict(round=11,country='Austria',circuit='Red Bull Ring',flag='austria-flag.svg',circuitAsset='austria-circuit.svg'),
        provenance=dict(sourceManifest=source['artifact_id'],observationRun=observation_run['artifact_id'],replayRun=replay_run['artifact_id'],
            retrospectiveProjection=retro['artifact_id'],publishedModel=model['artifact_id'],modelLabel='B0-only preview',
            cutoff=model['development_temporal_boundary_ref'],authorityValidation=clock['artifact_id'],residualAssumptions=ASSUMPTIONS,
            finalData=False,positionsAvailable=False,geometryValidated=False,protocol='B0-prespecified-preview/v1'))
    return bundle


def validate_distribution(dist,g):
    p=dist['event_region_probabilities'];q=dist['terminal_no_event_probability']
    if dist['region_grid']!=g or len(p)!=g['K_T'] or not all(math.isfinite(v) and 0<=v<=1 for v in p+[q]) or abs(sum(p)+q-1)>1e-9:
        raise ValueError('Malformed canonical distribution')


def write_gz(path,x):
    path.write_bytes(gzip.compress(encoded(x),mtime=0))


class DevelopmentLedger(list):
    """Durable ledger-first openings. A failed join leaves its opening on disk."""
    def __init__(self, path):
        super().__init__()
        self.path = path

    def append(self, entry):
        with self.path.open('ab') as f:
            f.write(encoded(entry)+b'\n')
            f.flush()
            os.fsync(f.fileno())
        super().append(entry)


def run(output, bundle_path):
    output.mkdir(parents=True,exist_ok=False)
    ledger=DevelopmentLedger(output/'ledger-openings.jsonl'); inputs={}
    for rnd in (10,11):
        source,rs=read_source(2024,rnd);clock=clock_evidence(rs)
        obs=reconstruct(source,rs,clock);init=initialize(obs)
        catalog=retrospective_catalog(rs,clock,source);resolution=resolve(init,obs['observations'],catalog,clock)
        inputs[rnd]=(source,clock,obs,init,catalog,resolution)
    source,clock,obs,init,catalog,res=inputs[10]
    development=fit_b0(obs,init,res,source,'2024-06-30',ledger);model=development['model']
    source,clock,obs,init,catalog,res=inputs[11]
    replay_run=replay(obs,init,model,source['date'],str(uuid.uuid4()))
    retro=retrospective_join(source,obs['observations'],replay_run,res,ledger)
    bundle=export(source,obs,replay_run,retro,model,clock,ledger)
    for rnd, artifacts in inputs.items():
        for name,x in zip(('source','clock','observation','initialization','catalog','resolution'),artifacts):
            write_gz(output/f'{rnd}-{name}.json.gz',x)
    for name,x in [('development',development),('replay',replay_run),('retrospective',retro),('ledger',ledger)]:
        write_gz(output/f'{name}.json.gz',x)
    bundle_path.write_bytes(encoded(bundle)+b'\n')
    release = dict(schema=1,file=bundle_path.name,sha256=hashlib.sha256(bundle_path.read_bytes()).hexdigest())
    (bundle_path.parent/'release.json').write_text(json.dumps(release,indent=2)+'\n')
    report=dict(version=VERSION,repository_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        python_version=__import__('sys').version,dependency_lock='Python standard library only',
        bundle_sha256=hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.gz')},
        race='2024 R11 Austria',training='2024 R10 Spain',model='B0-only preview',
        predictions=sum(a['state']=='ok' for a in bundle['attempts']),failed=sum(a['state']=='failed' for a in bundle['attempts']),
        attempts=len(bundle['attempts']),frames=len(bundle['frames']),drivers=len(bundle['drivers']),
        outcomes={k:sum(a['outcome']['kind']==k for a in bundle['attempts']) for k in ('exact','none','uncertain','unavailable')},
        limitations=['No B1, model tuning, P-F1 fold score or model-quality claim', 'No validated positions/coordinate geometry',
                     'Sectors/minis omitted; no future reference or backfill','Tyre-service evidence lacks independent ground truth',
                     'Unhealthy and post-Finished checkpoints remain recorded without predictions'],
        residual_assumptions=ASSUMPTIONS)
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--bundle',type=Path,required=True)
    args=ap.parse_args();run(args.output,args.bundle)
