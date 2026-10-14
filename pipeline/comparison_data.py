"""Development-only acquisition and reconstruction for issue 53."""
from __future__ import annotations
import argparse
from collections import Counter
import datetime as dt
import gzip
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import development as d

VERSION = 'model-comparison-data/v1'
PARTITION = [(2024, r) for r in range(10,25)] + [(2025,r) for r in range(1,25)]
BASE = 'https://livetiming.formula1.com/static/'


def write_json(path, value, compressed=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    raw = d.encoded(value)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_bytes((lzma.compress(raw,preset=3) if path.suffix=='.xz' else gzip.compress(raw,mtime=0)) if compressed else raw)
    os.replace(tmp, path)


def read_json(path, compressed=False):
    raw = Path(path).read_bytes()
    return json.loads((lzma.decompress(raw) if Path(path).suffix=='.xz' else gzip.decompress(raw)) if compressed else raw)


def fetch(url, timeout=20, attempts=3):
    """Finite timeout and retries; no unbounded transport loop."""
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(urllib.parse.quote(url, safe=':/?=&'), headers={'User-Agent':'f1-development-comparison/1'})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
                return data, dict(status=response.status, last_modified=response.headers.get('Last-Modified'),
                                  etag=response.headers.get('ETag'), url=url,
                                  retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                                  sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        except (OSError, ValueError):
            if attempt + 1 == attempts: raise
            time.sleep(attempt+1)


def calendar(root):
    """Metadata only for 2024/25; independently reconcile round and session date."""
    root=Path(root); root.mkdir(parents=True,exist_ok=True)
    result=[]
    for year in (2024,2025):
        ap=root/f'archive-index-{year}.json'; jp=root/f'calendar-{year}.json'
        for path,url in ((ap,f'{BASE}{year}/Index.json'),
                         (jp,f'https://api.jolpi.ca/ergast/f1/{year}.json?limit=100')):
            if not path.exists():
                raw,meta=fetch(url); path.write_bytes(raw); write_json(path.with_suffix('.metadata.json'),meta)
            meta=read_json(path.with_suffix('.metadata.json'))
            if hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256']:
                raise ValueError('Calendar cache hash mismatch')
        idx=json.loads(ap.read_text(encoding='utf-8-sig'))
        races=json.loads(jp.read_text())['MRData']['RaceTable']['Races']
        sessions=[s for meeting in idx['Meetings'] for s in meeting['Sessions'] if s.get('Name')=='Race']
        for race in races:
            rnd=int(race['round'])
            if (year,rnd) not in PARTITION: continue
            d.require_development(year,rnd)
            date=dt.date.fromisoformat(race['date'])
            matches=[s for s in sessions if s.get('Path') and
                     abs((dt.date.fromisoformat(s['Path'].split('/')[-2][:10])-date).days)<=1]
            if len(matches)!=1: raise ValueError(f'Ambiguous archive session for {year} R{rnd}')
            s=matches[0]
            result.append(dict(season=year,round=rnd,date=race['date'],session='R',path=s['Path'],
                               provider_session_key=s['Key'],race_name=race['raceName'],
                               calendar_hashes=[read_json(p.with_suffix('.metadata.json'))['sha256'] for p in (ap,jp)]))
    if [(r['season'],r['round']) for r in result] != PARTITION:
        raise ValueError('Calendar does not cover exact development partition')
    write_json(root/'races.json',result)
    return result


def acquire_race(race, root):
    year,rnd=race['season'],race['round']; d.require_development(year,rnd)
    folder=Path(root)/f'{year}-{rnd:02d}'; folder.mkdir(parents=True,exist_ok=True)
    if (year,rnd) in ((2024,10),(2024,11)):
        # Preserve the already reviewed bytes and acquisition provenance.
        original=d.SOURCES/str(rnd)
        if not (folder/'manifest.json').exists():
            for p in original.iterdir(): shutil.copyfile(p,folder/p.name)
        d.read_source(year,rnd,folder)
        return dict(race=[year,rnd],status='FROZEN',reused=True)
    manifest={**race, 'provider':'F1 static archive','acquisition_mode':'historical_archive',
              'adapter':'archive-prefix/v1','files':{}}
    for feed in sorted(d.FEEDS):
        path=folder/(feed+'.jsonStream.gz'); mp=folder/(feed+'.metadata.json')
        if path.exists() and mp.exists():
            meta=read_json(mp); raw=gzip.decompress(path.read_bytes())
            if hashlib.sha256(raw).hexdigest()!=meta['sha256'] or len(raw)!=meta['bytes']:
                raise ValueError('Partial source cache hash mismatch')
        else:
            raw,meta=fetch(BASE+race['path']+feed+'.jsonStream')
            write_json(mp,meta)
            tmp=path.with_suffix('.tmp'); tmp.write_bytes(gzip.compress(raw,mtime=0)); os.replace(tmp,path)
        manifest['files'][feed]=meta
    write_json(folder/'manifest.json',manifest)
    d.read_source(year,rnd,folder) # verifies dates, hashes, records and endpoint completeness
    return dict(race=[year,rnd],status='FROZEN',reused=False)


class TyreReducer(d.CausalReducer):
    """Persist only metadata of admitted updates, for the protocol's B1 fallback."""
    def __init__(self,*args):
        super().__init__(*args); self.metadata={}; self.pit_state={}
    def at(self,boundary):
        old=self.index; state,refs=super().at(boundary)
        for r in self.rs[old:self.index]:
            if not d.admitted(r,boundary,self.clock):
                for driver,v in r['payload'].get('Lines',{}).items():
                    if 'Stints' in v or 'InPit' in v:
                        self.metadata.pop(driver,None); self.pit_state.pop(driver,None)
                continue
            for driver,v in r['payload'].get('Lines',{}).items():
                if 'Stints' in v:
                    self.metadata[driver]=dict(prefix=r['prefix'],ref=r['ref'])
                if 'InPit' in v:
                    if v['InPit'] is True and self.pit_state.get(driver) is not True:
                        self.metadata[driver]=dict(prefix=r['prefix'],ref=r['ref'])
                    self.pit_state[driver]=v['InPit']
        for driver,meta in self.metadata.items():
            if driver in state:
                field='_last_stint_update' if self.rs[0]['stream']=='TimingAppData' else '_last_pit_entry'
                state[driver][field]=meta
                refs.append(meta['ref'])
        return state, sorted(set(refs))


def tyre_view(o):
    _,driver,_=o['semantic_observation_key']; state=o['canonical_state']
    timing=state['timing'].get(driver,{})
    tyre=state['tyres'].get(driver,{})
    stints=tyre.get('Stints',{})
    if not stints: return dict(fallback='STINT_MISSING')
    current=stints[max(stints,key=int)]
    age=current.get('TotalLaps'); compound=current.get('Compound')
    if not isinstance(age,(int,float)) or not 0<=age<1000 or not compound:
        return dict(fallback='AGE_OR_COMPOUND_OMITTED')
    if current.get('TyresNotChanged')=='1': return dict(fallback='TYRES_NOT_CHANGED')
    entry=timing.get('_last_pit_entry'); update=tyre.get('_last_stint_update')
    if entry and (not update or update['prefix']<=entry['prefix']):
        return dict(fallback='NO_STINT_UPDATE_SINCE_ENTRY')
    if compound not in ('SOFT','MEDIUM','HARD','INTERMEDIATE','WET','OTHER'): compound='OTHER'
    return dict(age=age,compound=compound,causal_refs=[update['ref']] if update else [])



def resolve_with_event_coverage(initializations, observations, catalog, clock):
    """Later gaps cannot invalidate an already established earlier event (#19)."""
    by_id={o['artifact_id']:o for o in observations}
    rows=[]
    run_id=d.artifact('ResolutionRunIdentity',initialization_ref=initializations['artifact_id'],
                      version=VERSION)['artifact_id']
    for row in initializations['records']:
        if row['eligibility_status']!='ELIGIBLE': continue
        o=by_id[row['observation_artifact_ref']]; boundary=o['prediction_boundary']
        visits=catalog['visits'].get(row['initialization']['driver_entry_key'],[])
        future=[v for v in visits if not (
            boundary['stream']=='TimingData' and v['ordinal']<=boundary['ordinal'])
            and v['entry']+5>boundary['prefix']-5]
        horizon=future[0]['entry']+5 if future else float('inf')
        relevant={**clock,'unhealthy':[w for w in clock['unhealthy'] if w[0]<=horizon]}
        single={**initializations,'records':[row]}
        result=d.resolve(single,[o],catalog,relevant)['records'][0]
        result.pop('artifact_id'); result['resolution_run_ref']=run_id
        result['resolution_policy_version']=VERSION
        rows.append(d.artifact(result.pop('kind'),**result))
    return d.artifact('ResolutionRun',resolution_run_id=run_id,repository_revision=d.revision(),
                      target_initialization_run_ref=initializations['artifact_id'],records=rows)


def reconstruct_race(race,sources,output):
    year,rnd=race['season'],race['round']; d.require_development(year,rnd)
    folder=Path(output)/f'{year}-{rnd:02d}'; done=folder/'manifest.json'
    source,records=d.read_source(year,rnd,Path(sources)/f'{year}-{rnd:02d}')
    code_hash=d.digest({name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
                        for name in ('development.py','comparison_data.py')})
    if done.exists():
        manifest=read_json(done)
        if manifest['code_hash']!=code_hash or manifest['source_ref']!=source['artifact_id']:
            raise ValueError('Reconstruction cache belongs to different source/code; use a new output')
        for name,hash_value in manifest['hashes'].items():
            if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=hash_value: raise ValueError('Dataset hash mismatch')
        return manifest
    folder.mkdir(parents=True,exist_ok=True)
    clock=d.clock_evidence(records,allow_restarts=True)
    observations=d.reconstruct(source,records,clock,reducer_factory=TyreReducer)
    initializations=d.initialize(observations)
    catalog=d.retrospective_catalog(records,clock,source,allow_restarts=True)
    resolutions=resolve_with_event_coverage(initializations,observations['observations'],catalog,clock)
    # Outcome-independent checkpoint rows, with only canonical model inputs.
    byobs={o['artifact_id']:o for o in observations['observations']}
    byinit={r['observation_artifact_ref']:r for r in initializations['records']}
    rows=[]
    for attempt in observations['records']:
        ref=attempt.get('observation_artifact_ref')
        row=dict(key=attempt['attempt_key'],observation_ref=ref,attempt_status=attempt['status'],
                 reason_codes=attempt['reason_codes'])
        if ref:
            o=byobs[ref]; init=byinit[ref]; row['eligibility']=init['eligibility_status']
            row['initialization_run_ref']=initializations['artifact_id']
            row['tyre']=tyre_view(o)
            try: row['grid']=d.grid(o)
            except ValueError as e: row['grid_failure']=str(e)
            if 'initialization' in init:
                row['episode_ref']=init['initialization']['artifact_id']
                row['target_episode_key']=init['initialization']['target_episode_key']
        rows.append(row)
    labels=[]
    # Resolution output remains a separate file; no label enters the checkpoint table.
    for resolution in resolutions['records']:
        o=byobs[resolution['observation_artifact_ref']]
        try: outcome=d.map_outcome(o,resolution)
        except ValueError: outcome=dict(kind='GRID_UNAVAILABLE')
        labels.append(dict(key=o['semantic_observation_key'],observation_ref=o['artifact_id'],
                           initialization_run_ref=initializations['artifact_id'],
                           episode_ref=byinit[o['artifact_id']]['initialization']['artifact_id'],
                           target_episode_key=resolution['target_episode_key'],
                           resolution_run_ref=resolutions['artifact_id'],
                           resolution_ref=resolution['artifact_id'],outcome=outcome,
                           reasons=resolution['truncation_reason_codes'],
                           event_ref=resolution.get('qualifying_event_ref')))
    hashes={}
    for name,value in [('source',source),('clock',clock),('observations',observations),
                       ('initializations',initializations),('catalog',catalog),('resolutions',resolutions),
                       ('checkpoints',rows),('labels',labels)]:
        fn=name+('.json.xz' if name in ('observations','initializations') else '.json.gz')
        write_json(folder/fn,value,compressed=True)
        hashes[fn]=hashlib.sha256((folder/fn).read_bytes()).hexdigest()
    manifest=dict(race=race,version=VERSION,code_revision=d.revision(),code_hash=code_hash,source_ref=source['artifact_id'],
                  hashes=hashes,drivers=len(observations['drivers']),checkpoints=len(rows),labels=len(labels),
                  initialization_run_ref=initializations['artifact_id'],resolution_run_ref=resolutions['artifact_id'],
                  eligibility=dict(Counter(r.get('eligibility','NO_OBSERVATION') for r in rows)),
                  outcomes=dict(Counter(r['outcome']['kind'] for r in labels)),
                  reasons=dict(Counter(reason for r in labels for reason in r['reasons'])),
                  unique_events=len({r['event_ref'] for r in labels if r['event_ref']}),
                  starts=sum(r['payload'].get('Status')=='Started' for r in records['SessionStatus']),
                  status='RECONSTRUCTED',assumptions=d.ASSUMPTIONS)
    write_json(done,manifest)
    return manifest


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('stage',choices=['acquire','reconstruct'])
    ap.add_argument('--sources',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--workers',type=int,default=4); args=ap.parse_args()
    if not 1<=args.workers<=8: ap.error('workers must be 1..8')
    races=calendar(args.sources/'metadata') if args.stage=='acquire' else read_json(args.sources/'metadata/races.json')
    # Check entire manifest before opening any per-race source or target path.
    if [(r['season'],r['round']) for r in races]!=PARTITION: raise ValueError('Wrong development partition')
    results=[]
    def work(r):
        try:
            return acquire_race(r,args.sources) if args.stage=='acquire' else reconstruct_race(r,args.sources,args.output)
        except Exception as e:
            return dict(race=[r['season'],r['round']],status='FAILED',error=f'{type(e).__name__}: {e}')
    with ThreadPoolExecutor(max_workers=args.workers if args.stage=='acquire' else 1) as pool:
        futures={pool.submit(work,r):r for r in races}
        for future in as_completed(futures):
            result=future.result(); results.append(result)
            print(f"{len(results)}/39 {result.get('race')} {result['status']} {result.get('error','')}",flush=True)
            write_json(args.output/f'{args.stage}-progress.json',results)
    if any(r['status']=='FAILED' for r in results): raise SystemExit(1)

if __name__=='__main__': main()
