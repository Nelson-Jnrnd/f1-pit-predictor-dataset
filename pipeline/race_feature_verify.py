"""Bounded independent raw-update checks for issue 57's feature whitelist."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
from . import comparison as c, comparison_data as data, development as d, expanded_sources as e
from .race_features import ROOT,view


def verify(dataset=e.ROOT/'dataset',output=ROOT/'features'):
    results=[]
    for race in data.read_json(dataset/'partition.json'):
        e.require_pre2026(race['season'],race['round'])
        folder=dataset/f"{race['season']}-{race['round']:02d}";manifest=data.read_json(folder/'manifest.json')
        observations=c.verified_file(folder,'observations',manifest)['observations']
        source=c.verified_file(folder,'source',manifest);clock=c.verified_file(folder,'clock',manifest)
        sourcefolder=e.source_folder(race)
        feeds={};checks=Counter()
        for feed in ('TimingData','TimingAppData','SessionStatus','LapCount','DriverList'):
            raw=gzip.decompress((sourcefolder/(feed+'.jsonStream.gz')).read_bytes())
            assert hashlib.sha256(raw).hexdigest()==source['files'][feed]['sha256']
            feeds[feed]=[(d.seconds(line[:12]),json.loads(line[12:])) for line in raw.decode('utf-8-sig').splitlines()]
        ordered=sorted(observations,key=lambda o:(o['prediction_boundary']['prefix'],o['prediction_boundary']['ordinal']))
        selected=[ordered[int(q*(len(ordered)-1))] for q in (0,.25,.5,.75,1)]
        samples=[]
        for o in selected:
            boundary=o['prediction_boundary'];driver=o['semantic_observation_key'][1];timing={};leaves={}
            for ordinal,(prefix,payload) in enumerate(feeds['TimingData']):
                if prefix>boundary['prefix']:break
                healthy=prefix<=clock['end'] and not any(a<=prefix<=b for a,b in clock['unhealthy'])
                if prefix<clock['start']:admit=prefix+300<clock['start']-5
                elif boundary['stream']=='TimingData':admit=healthy and ordinal<=boundary['ordinal']
                else:admit=healthy and prefix+10<boundary['prefix']
                update=payload.get('Lines',{}).get(driver,{})
                for key in ('LastLapTime','BestLapTime','Position','GapToLeader','IntervalToPositionAhead','NumberOfLaps'):
                    if key not in update:continue
                    if not healthy and prefix>=clock['start']:
                        # Invalidation mirrors the contract's leaf-level retraction.
                        if isinstance(update[key],dict) and isinstance(timing.get(key),dict):
                            for sub in update[key]:timing[key].pop(sub,None)
                        else:timing.pop(key,None)
                        continue
                    if not admit:continue
                    value=update[key]
                    if isinstance(value,dict):timing.setdefault(key,{}).update(value)
                    else:timing[key]=value
                    leaves[key]=dict(ordinal=ordinal,prefix=prefix)
            original=o['canonical_state']['timing'].get(driver,{})
            for key in ('LastLapTime','BestLapTime','Position','GapToLeader','IntervalToPositionAhead','NumberOfLaps'):
                if timing.get(key)!=original.get(key):raise ValueError(f'Raw feature mismatch {race} {o["semantic_observation_key"]} {key}')
                checks[key]+=1
            # All original causal references must satisfy their own stream rule.
            hashfeed={v['sha256']:k for k,v in source['files'].items()}
            for ref in o['causal_input_fact_refs']:
                h,idx=ref.split(':');feed=hashfeed[h];prefix=feeds[feed][int(idx)][0]
                if prefix<clock['start']:
                    assert prefix+300<clock['start']-5
                elif feed==boundary['stream']:
                    assert prefix<=boundary['prefix'] and int(idx)<=boundary['ordinal']
                else:assert prefix+10<boundary['prefix']
                checks['reference_availability']+=1
            samples.append(dict(key=o['semantic_observation_key'],observation_ref=o['artifact_id'],boundary=boundary,
                                raw_leaf_updates=leaves,feature_values=view(o)['values']))
        results.append(dict(race=race,checks=dict(checks),samples=samples))
        print(f'Raw samples {len(results)}/133',flush=True)
    result=dict(version='race-feature-verification/v1',results=results,code_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                audit_hash=hashlib.sha256((output/'audit.json').read_bytes()).hexdigest(),
                limitation='Five raw-state samples per race; not independent trackside truth. Full extraction checks all parent hashes and references.')
    data.write_json(output/'source-verification.json',result)

if __name__=='__main__':verify()
