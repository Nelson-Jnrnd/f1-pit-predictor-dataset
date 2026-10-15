"""Owner-approved pre-2026 raw archive verification, never protected data."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import datetime as dt
import email.utils
import gzip
import hashlib
import json
from pathlib import Path
import re
import urllib.error
from . import development as d, comparison_data as data

EXECUTION_CODE_HASH=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
ROOT=d.ROOT/'research/expanded-pre2026'
AUTHORITY='verification/EXPANDED_SOURCE_ADMISSION.md'
ASSUMPTIONS=d.ASSUMPTIONS[:3]+['RA-5: rewritten archives retain contemporaneous record versions/order; not independently proven',
    'RA-6: healthy rewritten prefix windows have the same ±5s availability bound and shared clock, conditional on per-session checks']


def require_pre2026(year,rnd):
    if not isinstance(year,int) or not 2018<=year<=2025 or not isinstance(rnd,int) or not 1<=rnd<=24:
        raise ValueError('Protected or unsupported season/round refused before any source read')


def require_review(admission):
    if not admission.get('independent_review_pass'):raise ValueError('Independent admission review required')
    fields={k:v for k,v in admission.items() if k not in ('independent_review_pass','reviewer','reviewed_content_hash','review_ref')}
    if d.digest(fields)!=admission.get('reviewed_content_hash'):raise ValueError('Reviewed admission content changed')
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=admission.get('code_hash'):raise ValueError('Reviewed admission code changed')


def races():
    # Existing file contains HTTP/date/path metadata only. No source or target outcomes.
    rows=data.read_json(d.ROOT/'verification/evidence/headscan_v1.json')['rows']
    return [dict(season=r['season'],round=r['round'],date=r['race_date'],session='R',path=r['path'])
            for r in rows if r['season']<2026]


def validate_address(race):
    require_pre2026(race['season'],race['round'])
    parts=race.get('path','').strip('/').split('/')
    if len(parts)!=3 or parts[0]!=str(race['season']) or not parts[-1].endswith('_Race') or race.get('session')!='R':
        raise ValueError('Raw source address disagrees with pre-2026 race identity')
    session_date=dt.date.fromisoformat(parts[-1][:10]);date=dt.date.fromisoformat(race['date'])
    if session_date.year!=race['season'] or abs((session_date-date).days)>1:
        raise ValueError('Raw source date disagrees with race identity')


def fetch_raw(url):
    # 403/404 are terminal evidence, not transient retries.
    for attempt in range(3):
        try:return data.fetch(url,timeout=20,attempts=1)
        except urllib.error.HTTPError as e:
            if e.code in (403,404):raise
            if attempt==2:raise
        except OSError:
            if attempt==2:raise


def source_folder(race,sources=ROOT/'sources'):
    require_pre2026(race['season'],race['round'])
    if (race['season'],race['round']) in data.PARTITION:
        return d.ROOT/'research/model-comparison/sources'/f"{race['season']}-{race['round']:02d}"
    return sources/f"{race['season']}-{race['round']:02d}"


def acquire(race,sources=ROOT/'sources'):
    validate_address(race);folder=source_folder(race,sources)
    if (race['season'],race['round']) in data.PARTITION:
        d.read_source(race['season'],race['round'],folder)
        return dict(race=race,status='FROZEN_EXISTING',folder=str(folder.relative_to(d.ROOT)))
    folder.mkdir(parents=True,exist_ok=True);files={}
    try:
        for feed in sorted(d.FEEDS):
            path=folder/(feed+'.jsonStream.gz');mp=folder/(feed+'.metadata.json')
            if path.exists() and mp.exists():
                meta=data.read_json(mp);raw=gzip.decompress(path.read_bytes())
                if hashlib.sha256(raw).hexdigest()!=meta['sha256']:raise ValueError('Source cache hash mismatch')
            else:
                raw,meta=fetch_raw(data.BASE+race['path']+feed+'.jsonStream')
                path.write_bytes(gzip.compress(raw,mtime=0));data.write_json(mp,meta)
            files[feed]=meta
        data.write_json(folder/'manifest.json',{**race,'provider':'F1 static archive','acquisition_mode':'historical_archive',
            'adapter':'expanded-archive-prefix/v1','files':files})
        return dict(race=race,status='FROZEN',folder=str(folder.relative_to(d.ROOT)))
    except (OSError,ValueError) as e:
        return dict(race=race,status='UNAVAILABLE',error=f'{type(e).__name__}: {e}',partial_feeds=sorted(files))


def read_raw(race,sources=ROOT/'sources'):
    validate_address(race);folder=source_folder(race,sources)
    manifest=data.read_json(folder/'manifest.json')
    if any(manifest[k]!=race[k] for k in ('season','round','date','session')):raise ValueError('Raw race identity mismatch')
    if set(manifest['files'])!=d.FEEDS:raise ValueError('Missing required raw endpoint')
    records={}
    for feed,meta in manifest['files'].items():
        if meta.get('url')!=data.BASE+race['path']+feed+'.jsonStream':raise ValueError('Endpoint address mismatch')
        raw=gzip.decompress((folder/(feed+'.jsonStream.gz')).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=meta['sha256'] or len(raw)!=meta['bytes']:raise ValueError('Raw source hash mismatch')
        rs=[]
        for i,line in enumerate(raw.decode('utf-8-sig').splitlines()):
            p=d.seconds(line[:12]);payload=json.loads(line[12:])
            if p is None or (rs and p<rs[-1]['prefix']) or not isinstance(payload,dict):raise ValueError('Malformed/regressing raw record')
            rs.append(dict(stream=feed,ordinal=i,prefix=p,payload=payload,ref=f"{meta['sha256']}:{i}"))
        if not rs:raise ValueError('Empty required stream')
        records[feed]=rs
    return manifest,records


def conservative_clock(records,legacy):
    clock=d.clock_evidence(records,allow_restarts=True)
    if legacy:
        # Older revision fidelity is weaker: omit all anomalous lap spans,
        # including single-driver delays, and all out-of-band UTC anchor spans.
        previous={};last={};extra=[]
        for r in records['TimingData']:
            for driver,v in r['payload'].get('Lines',{}).items():
                if 'LastLapTime' in v and d.seconds(v['LastLapTime'].get('Value')) is not None:
                    last[driver]=(r['prefix'],d.seconds(v['LastLapTime']['Value']))
                n=v.get('NumberOfLaps')
                if isinstance(n,int):
                    if driver in previous and n==previous[driver][1]+1 and driver in last and abs(last[driver][0]-r['prefix'])<1:
                        a=previous[driver][0];b=r['prefix'];res=b-a-last[driver][1]
                        if abs(res)>1 and clock['start']<=b<=clock['end']:extra.append([max(a,clock['start']),b])
                    previous[driver]=(r['prefix'],n)
        anchors=[]
        for r in records['RaceControlMessages']:
            messages=r['payload'].get('Messages',{})
            for message in messages.values() if isinstance(messages,dict) else messages:
                if clock['start']<=r['prefix']<=clock['end'] and message.get('Utc'):
                    anchors.append((r['prefix'],d.utc(message['Utc'])-r['prefix']))
        import statistics
        base=statistics.median(offset for _,offset in anchors)
        extra += [[max(clock['start'],p-60),min(clock['end'],p+60)] for p,offset in anchors if not -1.2<=offset-base<=.7]
        windows=sorted(clock['unhealthy']+extra);merged=[]
        for a,b in windows:
            if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
            else:merged.append([a,b])
        clock.pop('artifact_id');clock.update(unhealthy=merged,validation_ref=AUTHORITY,residual_assumptions=ASSUMPTIONS,
            extra_anomaly_spans=len(extra),healthy_seconds=clock['end']-clock['start']-sum(b-a for a,b in merged))
        clock=d.artifact(clock.pop('kind'),**clock)
        if clock['healthy_seconds']<=120:raise ValueError('No sufficient healthy clock interval')
    return clock


def penalty_context(records,visits):
    issued={};served=set();penalty_tests=[]
    for r in records['RaceControlMessages']:
        messages=r['payload'].get('Messages',{})
        for msg in messages.values() if isinstance(messages,dict) else messages:
            text=msg.get('Message','');match=re.search(r'(DRIVE THROUGH|STOP-AND-GO|STOP AND GO|STOP/GO) PENALTY FOR CAR (\d+)',text)
            if match:
                if 'PENALTY SERVED' in text:served.add(match[2])
                else:issued.setdefault(match[2],[]).append(r['prefix'])
    for driver,times in issued.items():
        if driver not in served:continue
        for time in times:
            first=next((v for v in visits.get(driver,[]) if v['entry']>time),None)
            if first:penalty_tests.append(dict(driver=driver,**first))
    return penalty_tests


def verify(race,sources=ROOT/'sources'):
    require_pre2026(race['season'],race['round'])
    legacy=(race['season'],race['round']) not in data.PARTITION
    if (race['season'],race['round']) in ((2018,2),(2018,12)):
        return dict(race=race,status='EXCLUDED',reason='Existing SUPPORT_MATRIX marks this source UNSUPPORTED; no upgrade authorized')
    try:
        manifest,records=read_raw(race,sources);clock=conservative_clock(records,legacy)
        # Check all counter transitions and causal roster before admission.
        trigger=next(r for r in records['SessionStatus'] if r['payload']['Status']=='Started')
        roster,_=d.reduce_stream(records['DriverList'],trigger,clock,False)
        if not roster:raise ValueError('No causal driver roster')
        if any(not isinstance(v,dict) or v.get('RacingNumber')!=k or not v.get('Tla') or not v.get('TeamName') or not v.get('TeamColour') for k,v in roster.items()):raise ValueError('Incomplete causal roster identity')
        counts={key:0 for key in roster};entry_counts={};entry_starts={};pit={};visits={}
        for r in records['TimingData']:
            if r['prefix']<clock['start']:continue
            for driver,v in r['payload'].get('Lines',{}).items():
                if driver not in roster:raise ValueError('Unknown timing driver')
                n=v.get('NumberOfLaps')
                if isinstance(n,int):
                    if n<counts[driver] or n>counts[driver]+1:raise ValueError('Unsupported lap jump/regression')
                    counts[driver]=n
                if v.get('InPit') is True and not pit.get(driver,False) and r['prefix']<=clock['end']:
                    visits.setdefault(driver,[]).append(dict(entry=r['prefix'],lap=counts[driver]+1))
                if 'InPit' in v:pit[driver]=v['InPit']
        classes={'POS':0,'NEG':0,'NONE':0};corroborated=0;penalty_tests=[]
        for driver,vs in visits.items():
            for i,visit in enumerate(vs):
                hi=vs[i+1]['entry'] if i+1<len(vs) else clock['end']+5
                stints={}
                for r in records['TimingAppData']:
                    if visit['entry']<=r['prefix']<hi:
                        update=r['payload'].get('Lines',{}).get(driver,{}).get('Stints')
                        if update is not None:d.merge(stints,{str(j):v for j,v in enumerate(update)} if isinstance(update,list) else update)
                last=stints[max(stints,key=int)] if stints else {}
                cls='POS' if last.get('TyresNotChanged')=='0' else 'NEG' if last.get('TyresNotChanged')=='1' else 'NONE'
                classes[cls]+=1;visit['class']=cls
                if cls=='POS' and (str(last.get('New')).lower()=='true' or last.get('StartLaps')==0):corroborated+=1
        # Independent penalty context is only a QA test, never a negative target.
        penalty_tests=penalty_context(records,visits)
        if any(v['class']=='POS' for v in penalty_tests):raise ValueError('Positive tyre-service conflicts with served penalty test')
        # Prove usable scheduled distance from raw admissible updates, not CSV maximum.
        distances=[r for r in records['LapCount'] if isinstance(r['payload'].get('TotalLaps'),int) and r['payload']['TotalLaps']>0]
        if not any(d.admitted(r,trigger,clock) for r in distances):raise ValueError('No causal initial scheduled distance')
        result=dict(race=race,status='ADMITTED',legacy=legacy,source_manifest_hash=hashlib.sha256((source_folder(race,sources)/'manifest.json').read_bytes()).hexdigest(),
            endpoint_hashes={feed:v['sha256'] for feed,v in manifest['files'].items()},clock=clock,tyre_classes=classes,
            corroborated_positive=corroborated,penalty_test_set=penalty_tests,drivers=len(roster),
            assumptions=ASSUMPTIONS if legacy else d.ASSUMPTIONS,
            target_limit='Positive TyresNotChanged support is assumption-based; no independent tyre-change ground truth; negatives remain unknown')
        return result
    except (ValueError,OSError,KeyError,TypeError) as e:return dict(race=race,status='EXCLUDED',reason=f'{type(e).__name__}: {e}')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=('acquire','verify'));ap.add_argument('--sources',type=Path,default=ROOT/'sources');ap.add_argument('--output',type=Path,default=ROOT/'admission');ap.add_argument('--workers',type=int,default=6);args=ap.parse_args()
    if not 1<=args.workers<=8:raise ValueError('Workers 1..8 required')
    args.output.mkdir(parents=True,exist_ok=True);results=[];rs=races()
    for race in rs:require_pre2026(race['season'],race['round'])
    with ThreadPoolExecutor(max_workers=args.workers if args.stage=='acquire' else 1) as pool:
        tasks={pool.submit(acquire if args.stage=='acquire' else verify,r,args.sources):r for r in rs}
        for future in as_completed(tasks):
            result=future.result();results.append(result);results.sort(key=lambda r:(r['race']['season'],r['race']['round']))
            data.write_json(args.output/(args.stage+'.json'),dict(version='expanded-source-admission/v1',results=results,code_hash=EXECUTION_CODE_HASH))
            print(f"{len(results)}/{len(rs)} {result['race']['season']} R{result['race']['round']} {result['status']} {result.get('reason',result.get('error',''))}",flush=True)

if __name__=='__main__':main()
