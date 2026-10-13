"""Scoped, offline, observation-owned position context for Austria 2024 R11.

The base replay is immutable. Positions are a separate, hash-bound projection at
its recorded boundaries, not model inputs, timing order, or exact-at-T motion.
"""
from __future__ import annotations
import argparse
import base64
import bisect
import datetime as dt
import email.utils
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import zlib
from . import development as d

ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/'research/position-evidence/sources'
REPORT=ROOT/'research/position-evidence/evidence.json'
POLICY='common-position-sample/v1'
MAX_AGE=20.0
CORRIDOR=350.0
TIMING_FIELDS=('NumberOfLaps','LastLapTime','InPit')


def utc(value):
    date=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if date.tzinfo is None: date=date.replace(tzinfo=dt.timezone.utc)
    return date.timestamp()


def load_source(role,feed):
    d.require_development(2024,11)
    if role not in ('race','qualifying') or feed not in ('Position.z','TimingData','SessionStatus','SessionInfo'):
        raise ValueError('Unsupported source role/endpoint')
    directory=SOURCES/role
    manifest=json.loads((directory/'manifest.json').read_text())
    if (manifest['season'],manifest['round'],manifest['date'],manifest['session'])!=(2024,11,'2024-06-30' if role=='race' else '2024-06-29','R' if role=='race' else 'Q'):
        raise ValueError('Position source identity mismatch')
    meta=manifest['files'][feed]
    date=dt.date.fromisoformat(manifest['date'])
    modified=email.utils.parsedate_to_datetime(meta['last_modified']).date()
    if modified not in (date,date+dt.timedelta(days=1)):
        raise ValueError('Rewritten source refused')
    raw=gzip.decompress((directory/(feed+'.jsonStream.gz')).read_bytes())
    if len(raw)!=meta['bytes'] or hashlib.sha256(raw).hexdigest()!=meta['sha256']:
        raise ValueError('Frozen source mismatch')
    records=[]
    for ordinal,line in enumerate(raw.decode('utf-8-sig').splitlines()):
        prefix=d.seconds(line[:12])
        if prefix is None or (records and prefix<records[-1]['prefix']):
            raise ValueError('Malformed or regressing prefix')
        payload=json.loads(line[12:])
        if feed=='Position.z':
            payload=json.loads(zlib.decompress(base64.b64decode(payload,validate=True),-zlib.MAX_WBITS))
        records.append(dict(prefix=prefix,ordinal=ordinal,payload=payload,ref=f"{meta['sha256']}:{ordinal}"))
    return manifest,records


def samples(records):
    result=[];previous=None
    for record in records:
        ps=record['payload'].get('Position')
        if not isinstance(ps,list):raise ValueError('Position batch missing')
        for i,item in enumerate(ps):
            epoch=utc(item['Timestamp'])
            if previous is not None and epoch<previous:raise ValueError('Sample clock regressed')
            entries=item['Entries']
            if not isinstance(entries,dict):raise ValueError('Missing entries')
            result.append(dict(epoch=epoch,timestamp=item['Timestamp'],prefix=record['prefix'],ordinal=record['ordinal'],
                               sample_ordinal=i,ref=record['ref']+f':{i}',entries=entries))
            previous=epoch
    return result


def info(role):
    _,records=load_source(role,'SessionInfo')
    if len(records)!=1:raise ValueError('Session metadata needs reconciliation')
    return records[0]['payload']


def clock_base():
    path=ROOT/'research/development-race/sources/11/RaceControlMessages.jsonStream.gz'
    manifest=json.loads((path.parent/'manifest.json').read_text())
    raw=gzip.decompress(path.read_bytes())
    if hashlib.sha256(raw).hexdigest()!=manifest['files']['RaceControlMessages']['sha256']:
        raise ValueError('Race-control source mismatch')
    clock=json.loads(gzip.decompress((ROOT/'research/development-race/run-1/11-clock.json.gz').read_bytes()))
    offsets=[]
    for line in raw.decode('utf-8-sig').splitlines():
        prefix=d.seconds(line[:12]);messages=json.loads(line[12:]).get('Messages',{})
        if clock['start']<=prefix<=clock['end']:
            for message in messages.values() if isinstance(messages,dict) else messages:
                if 'Utc' in message:offsets.append(utc(message['Utc'])-prefix)
    if not offsets:raise ValueError('No RCM anchors')
    base=statistics.median(offsets)
    return base,clock,manifest['files']['RaceControlMessages']['sha256']


def valid_coord(v):
    return isinstance(v,dict) and all(isinstance(v.get(k),(int,float)) and not isinstance(v.get(k),bool) and math.isfinite(v[k]) for k in ('X','Y','Z')) and (v['X']!=0 or v['Y']!=0)


def segment_distance(point,a,b):
    x,y=point;ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay
    t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
    return math.hypot(x-ax-t*dx,y-ay-t*dy)


def distance(point,trace):
    return min(segment_distance(point,a,b) for a,b in zip(trace,trace[1:]+trace[:1]))


def geometry(qsamples,race_info):
    qinfo=info('qualifying')
    if (qinfo['Meeting']['Key'],qinfo['Meeting']['Circuit']['Key'])!=(race_info['Meeting']['Key'],race_info['Meeting']['Circuit']['Key']):
        raise ValueError('Circuit identity mismatch')
    offset=qinfo['GmtOffset']
    qend=utc(qinfo['EndDate']+'+'+offset)
    rstart=utc(race_info['StartDate']+'+'+race_info['GmtOffset'])
    qmanifest=json.loads((SOURCES/'qualifying/manifest.json').read_text())
    if qend>=rstart or any(email.utils.parsedate_to_datetime(m['last_modified']).timestamp()>=rstart for m in qmanifest['files'].values()):
        raise ValueError('Geometry was not established before race')
    _,timing=load_source('qualifying','TimingData')
    # First defensible completed flying lap in numeric driver order, not future race normalization.
    advances={};state={};candidates=[]
    for record in timing:
        for driver,update in record['payload'].get('Lines',{}).items():
            v=state.setdefault(driver,{})
            d.merge(v,update)
            n=update.get('NumberOfLaps');lap=d.seconds(update.get('LastLapTime',{}).get('Value'))
            if isinstance(n,int):
                if driver in advances and n==advances[driver]['n']+1 and lap is not None and 50<=lap<=90 and not v.get('InPit'):
                    candidates.append((int(driver),n,advances[driver],record))
                advances[driver]=dict(n=n,prefix=record['prefix'],ref=record['ref'])
    for driver,n,start,end in sorted(candidates,key=lambda c:(c[0],c[1])):
        selected=[s for s in qsamples if start['prefix']<s['prefix']<=end['prefix'] and valid_coord(s['entries'].get(str(driver)))]
        if len(selected)<150 or max(b['epoch']-a['epoch'] for a,b in zip(selected,selected[1:]))>1:
            continue
        trace=[[s['entries'][str(driver)]['X'],s['entries'][str(driver)]['Y']] for s in selected]
        length=sum(math.dist(a,b) for a,b in zip(trace,trace[1:]))
        closure=math.dist(trace[0],trace[-1])
        if length<=0 or closure/length>.015:continue
        xs,ys=zip(*trace);span=max(max(xs)-min(xs),max(ys)-min(ys))
        if span<=0:continue
        return d.artifact('CircuitGeometry',coordinate_system='F1-Position-native-XYZ/2024-AUT',
            circuit_key=19,meeting_key=1239,prior_session_key=qinfo['Key'],prior_session_date='2024-06-29',
            prior_session_scheduled_end_utc=qend,prior_evidence_last_modified_utc=max(email.utils.parsedate_to_datetime(m['last_modified']).timestamp() for m in qmanifest['files'].values()),available_before=rstart,
            qualifying_source_manifest_digest=d.digest(qmanifest),
            source_refs=[start['ref'],end['ref']]+[s['ref'] for s in selected],
            driver=str(driver),lap=n,trace=trace,native_length=length,closure_ratio=closure/length,
            transform=dict(minX=min(xs),maxY=max(ys),scale=460/span),corridor_native=CORRIDOR,
            method='first-complete-flying-lap-native-coordinate-trace/v1')
    raise ValueError('No independently closed prior-session trace')


def verify():
    manifest,records=load_source('race','Position.z');race=info('race')
    if (race['Key'],race['Meeting']['Key'],race['Meeting']['Circuit']['Key'])!=(9550,1239,19):raise ValueError('Wrong race metadata')
    rs=samples(records);_,qrecords=load_source('qualifying','Position.z');qs=samples(qrecords)
    base,clock,rcm=clock_base();g=geometry(qs,race)
    active=[s for s in rs if clock['start']<=s['prefix']<=clock['end']]
    delays=[s['prefix']+base-s['epoch'] for s in active]
    gaps=[b['epoch']-a['epoch'] for a,b in zip(active,active[1:])]
    roster={driver['id'] for driver in json.loads((ROOT/'explorer/public/development.json').read_text())['drivers']}
    if not active or min(delays)<-1.2 or max(delays)>5 or max(gaps)>2 or any(set(s['entries'])!=roster for s in active):
        raise ValueError('Position clock/cohort consistency not established')
    # Independent native coordinate registration check uses only sufficiently early pre-race points.
    early=[s for s in rs if s['prefix']+300<clock['start']-5]
    early_points=[(v['X'],v['Y']) for s in early for v in s['entries'].values() if valid_coord(v)]
    if not early_points:raise ValueError('No admissible pre-race coordinate evidence')
    # Coordinate observations within the same fixed qualifying track frame; no race-future fit.
    unique=sorted(set(early_points))
    hits=[p for p in unique if distance(p,g['trace'])<=CORRIDOR]
    if len(hits)<100:raise ValueError('Prior geometry coordinate frame not supported pre-race')
    evidence=d.artifact('PositionAvailabilityAuthorityValidation', status='CANDIDATE',
        scope=dict(season=2024,round=11,session_key=9550,endpoint='Position.z',source_manifest_digest=d.digest(manifest)),
        source_sha256=manifest['files']['Position.z']['sha256'],race_last_modified=manifest['files']['Position.z']['last_modified'],
        parser='f1-deflate-position-batches/v1',authority_level='VERIFIED_BOUNDED_TIME',
        exception='decisions/2026-10-10-v2-race-day-archive-evidence-exception.md',
        assumptions=d.ASSUMPTIONS,
        timestamp_meaning='Embedded UTC is the reported common sample clock, not publication time; prefix is recorder receipt under RA-1/RA-4.',
        shared_clock_evidence=dict(rcm_sha256=rcm,base_epoch=base,delay_min=min(delays),delay_max=max(delays),delay_median=statistics.median(delays),
                                   samples=len(active),max_common_sample_gap=max(gaps),sample_regressions=0,roster_count=20),
        error_model=dict(availability_bound_seconds=5,cross_stream_separation_seconds=10,prerace_margin_seconds=300,
                         clock_validation_ref=clock['artifact_id'],unhealthy_windows=clock['unhealthy'],healthy_end=clock['end']),
        projection_policy=dict(version=POLICY,max_latest_sample_age=MAX_AGE,common_sample_only=True,interpolation=False,coordinate_transform='fixed-prior-geometry',pit_membership='definite-false-at-common-sample-and-not-true-at-boundary/v1'),
        geometry=g,native_registration=dict(pre_race_unique_points=len(unique),prior_trace_matches=len(hits),pre_race_cutoff=clock['start']-305,matching_span_x=max(p[0] for p in hits)-min(p[0] for p in hits),matching_span_y=max(p[1] for p in hits)-min(p[1] for p in hits)),
        limitations=['Internal-consistency evidence under the existing exception, not contemporaneous capture.',
                     'Up to 20 seconds old; displayed samples are not exact car motion at T.',
                     'OnTrack is not reliable track-membership proof; omit invalid/off-corridor/known-pit coordinates.',
                     'No approval for CarData, other races, sectors, minis or final evaluation.'])
    return evidence,rs,clock


def project(samples_,boundary,clock,evidence,drivers):
    if not d.healthy(boundary['prefix'],clock):return dict(sample=None,points=[],reason='BOUNDARY_UNAVAILABLE')
    base=evidence['shared_clock_evidence']['base_epoch'];g=evidence['geometry']
    candidates=[]
    last_gap_end=max((b for a,b in clock['unhealthy'] if a<=boundary['prefix']),default=clock['start'])
    for s in samples_:
        record=dict(stream='Position.z',prefix=s['prefix'],ordinal=s['ordinal'])
        if s['prefix']>last_gap_end and d.admitted(record,boundary,clock) and s['epoch']<=boundary['prefix']+base-5 and boundary['prefix']+base+5-s['epoch']<=MAX_AGE:
            candidates.append(s)
    if not candidates:return dict(sample=None,points=[],reason='NO_FRESH_ADMISSIBLE_COMMON_SAMPLE')
    s=max(candidates,key=lambda s:(s['epoch'],s['ordinal'],s['sample_ordinal']))
    points=[]
    for driver in drivers:
        v=s['entries'].get(driver)
        if not valid_coord(v) or distance((v['X'],v['Y']),g['trace'])>CORRIDOR:
            continue
        tr=g['transform'];x=20+(v['X']-tr['minX'])*tr['scale'];y=20+(tr['maxY']-v['Y'])*tr['scale']
        if not (0<=x<=500 and 0<=y<=500):continue
        points.append(dict(driver=driver,x=x,y=y))
    return dict(sample=dict(time=s['epoch']-base-clock['start'],timestamp=s['timestamp'],publicationPrefix=s['prefix'],sourceRef=s['ref']),
                points=points,reason=None if points else 'NO_VALID_COORDINATES')


def pit_context(records):
    """Retain changes only; repeated deltas do not create fictitious transitions."""
    result={};state={}
    for r in records:
        for driver,v in r['payload'].get('Lines',{}).items():
            if isinstance(v.get('InPit'),bool) and state.get(driver)!=v['InPit']:
                result.setdefault(driver,[]).append({**r,'pit':v['InPit']})
                state[driver]=v['InPit']
    return result


def sample_pit_safe(events,sample_prefix,boundary,clock):
    """Prove false at the common sample, ignoring facts unavailable at T.

    Cross-stream bounds apply at S too. Any admitted transition overlapping S's
    uncertainty interval makes membership ambiguous. Unknown/gap-carried state
    cannot establish on-track membership.
    """
    sample_boundary=dict(prefix=sample_prefix,stream='Position.z',ordinal=-1)
    gap_end=max((b for a,b in clock['unhealthy'] if a<=sample_prefix),default=None)
    known=None
    for e in events:
        if not d.admitted(e,boundary,clock):continue
        if gap_end is not None and e['prefix']<=gap_end:continue
        if d.admitted(e,sample_boundary,clock):known=e['pit']
        elif abs(e['prefix']-sample_prefix)<=10:return False
    return known is False


def export(evidence,rs,clock,approved=False):
    d.require_development(2024,11);d.verify_artifact(evidence)
    if approved and evidence.get('status')!='APPROVED':raise ValueError('Independent authority review required before release')
    base_path=ROOT/'explorer/public/development.json';raw=base_path.read_bytes();base=json.loads(raw)
    release=json.loads((base_path.parent/'release.json').read_text())
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=release['sha256'] or base['season']!=2024 or base['raceMetadata']['round']!=11 or base['provenance']['finalData'] is not False:
        raise ValueError('Base release identity/protected-scope mismatch')
    obs=json.loads(gzip.decompress((ROOT/'research/development-race/run-1/11-observation.json.gz').read_bytes()))
    d.verify_artifact(obs)
    if obs['artifact_id']!=base['provenance']['observationRun'] or clock['artifact_id']!=base['provenance']['authorityValidation']:
        raise ValueError('Boundary owner lineage mismatch')
    boundaries={}
    for attempt in obs['records']:
        trigger=attempt['trigger'];key=(round(trigger['prefix']-clock['start'],3),trigger['ordinal'])
        boundaries[key]=(trigger,'observation_artifact_ref' in attempt)
    _,sources=d.read_source(2024,11)
    pit_events=pit_context(sources['TimingData'])
    ids=[d_['id'] for d_ in base['drivers']];frames=[]
    for frame in base['frames']:
        key=(frame['time'],frame['order']);boundary,available=boundaries[key]
        p=project(rs,boundary,clock,evidence,ids) if available else dict(sample=None,points=[],reason='BOUNDARY_UNAVAILABLE')
        # Never present stationary garage/pit points as racing-car track locations.
        pits={r['driver'] for r in frame['rows'] if r['pit'] is True}
        sample_prefix=p['sample']['time']+clock['start'] if p['sample'] else None
        p['points']=[point for point in p['points'] if point['driver'] not in pits and
                     sample_pit_safe(pit_events.get(point['driver'],[]),sample_prefix,boundary,clock)]
        if p['sample'] and not p['points']:p['reason']='NO_VALID_COORDINATES'
        frames.append(dict(time=frame['time'],order=frame['order'],boundaryPrefix=boundary['prefix'],**p))
    g=evidence['geometry'];tr=g['transform']
    trace=[[20+(x-tr['minX'])*tr['scale'],20+(tr['maxY']-y)*tr['scale']] for x,y in g['trace']]
    return d.artifact('PositionContextBundle',schema=1,id=base['id']+'-positions-v1',baseBundleId=base['id'],baseBundleSha256=sha,
        season=2024,round=11,finalData=False,authorityRef=evidence['artifact_id'],authorityStatus=evidence['status'],
        geometryRef=g['artifact_id'],geometry=trace,clockStart=clock['start'],maxAge=MAX_AGE,availabilityBounds=5,
        frames=frames,policy=POLICY)


def run(mode,output):
    evidence,rs,clock=verify()
    if mode=='evidence':
        output.write_text(json.dumps(evidence,indent=2)+'\n')
        candidate=export(evidence,rs,clock)
        (output.parent/'candidate.json').write_bytes(d.encoded(candidate)+b'\n')
        print(json.dumps({k:evidence[k] for k in ('artifact_id','shared_clock_evidence','native_registration')},indent=2))
        print('Geometry lap',evidence['geometry']['lap'],'closure',evidence['geometry']['closure_ratio'])
        print('Candidate frames',len(candidate['frames']),'positioned',sum(bool(f['points']) for f in candidate['frames']))
    else:
        approved=json.loads(REPORT.read_text());d.verify_artifact(approved)
        if approved['status']!='APPROVED':raise ValueError('Authority not independently approved')
        comparable={k:v for k,v in approved.items() if k not in ('artifact_id','status','review')}
        candidate={k:v for k,v in evidence.items() if k not in ('artifact_id','status')}
        if comparable!=candidate:raise ValueError('Approved evidence does not reproduce against frozen sources')
        bundle=export(approved,rs,clock,approved=True);output.write_bytes(d.encoded(bundle)+b'\n')
        print('Released',len(bundle['frames']),'frames')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('evidence','release'));parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.mode,args.output)
