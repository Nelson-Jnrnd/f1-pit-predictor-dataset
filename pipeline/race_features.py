"""Outcome-free, whitelisted views of frozen canonical observations for issue 57."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import math
from pathlib import Path
from . import comparison as c, comparison_data as data, development as d, expanded_sources as e

ROOT=d.ROOT/'research/race-context'
FIELDS=('last_lap','best_lap','pace_delta','position','gap','interval')


def numeric(value,lo,hi):
    try:value=float(value)
    except (ValueError,TypeError):return None
    return value if math.isfinite(value) and lo<=value<=hi else None


def view(observation):
    """Only one canonical observation; no source, label or future observation input."""
    driver=observation['semantic_observation_key'][1]
    lap=observation['selected_driver_completed_laps']
    timing=observation['canonical_state']['timing'].get(driver,{})
    last=None;best=None
    if lap>0 and timing.get('_last_time_completed_lap')==lap:
        last=numeric(d.seconds(timing.get('LastLapTime',{}).get('Value')),20,600)
    best_lap=timing.get('BestLapTime',{}).get('Lap')
    if isinstance(best_lap,int) and 1<=best_lap<=lap:
        best=numeric(d.seconds(timing.get('BestLapTime',{}).get('Value')),20,600)
    position=numeric(timing.get('Position'),1,30)
    if position is not None and not position.is_integer():position=None
    gap=numeric(d.seconds(timing.get('GapToLeader')),0,3600)
    interval=numeric(d.seconds(timing.get('IntervalToPositionAhead',{}).get('Value')),0,3600)
    values=dict(last_lap=last,best_lap=best,pace_delta=last-best if last is not None and best is not None else None,
                position=position,gap=gap,interval=interval)
    return dict(version='race-features/v1',values=values,omissions=[k for k,v in values.items() if v is None],
                observation_ref=observation['artifact_id'],input_fact_refs=observation['causal_input_fact_refs'])


def audit(dataset,output):
    partition=data.read_json(dataset/'partition.json');results=[]
    for race in partition:e.require_pre2026(race['season'],race['round'])
    for race in partition:
        folder=dataset/f"{race['season']}-{race['round']:02d}";manifest=data.read_json(folder/'manifest.json')
        checkpoints=c.verified_file(folder,'checkpoints',manifest)
        observations=c.verified_file(folder,'observations',manifest)
        source=c.verified_file(folder,'source',manifest)
        known={v['sha256']:k for k,v in source['files'].items()}
        records={o['artifact_id']:o for o in observations['observations']}
        rows=[];missing=Counter();available=Counter();guards=Counter()
        for cp in checkpoints:
            if not cp['observation_ref']:continue
            o=records[cp['observation_ref']]
            if o['semantic_observation_key']!=cp['key']:raise ValueError('Observation/checkpoint mismatch')
            if o['source_snapshot_manifest_ref']!=source['artifact_id']:raise ValueError('Observation source mismatch')
            b=o['prediction_boundary'];bh,bo=b['ref'].split(':')
            if known.get(bh)!=b['stream'] or int(bo)!=b['ordinal']:raise ValueError('Boundary identity mismatch')
            for ref in o['causal_input_fact_refs']:
                h,ordinal=ref.split(':')
                if h not in known or int(ordinal)<0:raise ValueError('Unrecognized causal stream reference')
                if h==bh and int(ordinal)>int(bo):raise ValueError('Future same-stream reference')
            v=view(o);missing.update(v['omissions']);available.update(k for k in FIELDS if k not in v['omissions'])
            guards['observations_checked']+=1
            rows.append(dict(key=cp['key'],**v))
        dest=output/f"{race['season']}-{race['round']:02d}.json.gz"
        data.write_json(dest,rows,True)
        results.append(dict(race=race,attempts=len(checkpoints),observations=len(rows),missing=dict(missing),available=dict(available),
            guards=dict(guards),parent_manifest_hash=hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest(),
            observations_hash=next(v for k,v in manifest['hashes'].items() if k.startswith('observations.')),
            source_hash=manifest['hashes']['source.json.gz'],features_hash=hashlib.sha256(dest.read_bytes()).hexdigest()))
        print(f"Features {len(results)}/133 {race['season']} R{race['round']}",flush=True)
    result=dict(version='race-features/v1',results=results,partition_hash=d.digest(partition),
        extractor_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        limitation='Parent evidence and reference-order checks, not independent timing/rank ground truth; RA1..RA6 apply')
    data.write_json(output/'audit.json',result)
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',type=Path,default=e.ROOT/'dataset');ap.add_argument('--output',type=Path,default=ROOT/'features')
    args=ap.parse_args();audit(args.dataset,args.output)

if __name__=='__main__':main()
