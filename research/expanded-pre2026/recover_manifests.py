from pathlib import Path
from collections import Counter
import hashlib,shutil
from pipeline import development as d,comparison_data as data,expanded_sources as e
root=e.ROOT;ad=data.read_json(root/'admission/verify.json');e.require_review(ad)
code=d.digest({n:hashlib.sha256((Path('pipeline')/n).read_bytes()).hexdigest() for n in ('development.py','comparison_data.py','expanded_sources.py','expanded_data.py')})
count=0
for evidence in ad['results']:
 if evidence['status']!='ADMITTED':continue
 race=evidence['race'];folder=root/'dataset'/f"{race['season']}-{race['round']:02d}";done=folder/'manifest.json'
 if (race['season'],race['round']) in data.PARTITION:
  original=d.ROOT/'research/model-comparison/dataset-2'/folder.name/'manifest.json'
  if done.exists():assert done.read_bytes()==original.read_bytes()
  else:shutil.copyfile(original,done)
  m=data.read_json(done)
 else:
  source=data.read_json(folder/'source.json.gz',True);obs=data.read_json(folder/'observations.json.xz',True)
  init=data.read_json(folder/'initializations.json.xz',True);res=data.read_json(folder/'resolutions.json.gz',True)
  cp=data.read_json(folder/'checkpoints.json.gz',True);labels=data.read_json(folder/'labels.json.gz',True)
  raw,records=e.read_raw(race,root/'sources')
  m=dict(race=race,version='expanded-data/v1',code_revision=obs['repository_revision'],code_hash=code,source_ref=source['artifact_id'],hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.suffix in ('.gz','.xz')},drivers=len(obs['drivers']),checkpoints=len(cp),labels=len(labels),initialization_run_ref=init['artifact_id'],resolution_run_ref=res['artifact_id'],eligibility=dict(Counter(r.get('eligibility','NO_OBSERVATION') for r in cp)),outcomes=dict(Counter(r['outcome']['kind'] for r in labels)),reasons=dict(Counter(reason for r in labels for reason in r['reasons'])),unique_events=len({r['event_ref'] for r in labels if r['event_ref']}),starts=sum(r['payload'].get('Status')=='Started' for r in records['SessionStatus']),status='RECONSTRUCTED',assumptions=evidence['assumptions'],admission_evidence_ref=d.digest(evidence))
  if done.exists():assert data.read_json(done)==m, folder
  else:data.write_json(done,m);count+=1
 for name,h in m['hashes'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==h
 print(folder.name,'verified',flush=True)
print('Recovered metadata:',count)
