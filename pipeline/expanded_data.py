"""Canonical reconstruction from independently admitted pre-2026 raw sources."""
import argparse
import hashlib
from collections import Counter
from pathlib import Path
import shutil
from . import development as d, comparison_data as data, expanded_sources as e

def reconstruct_race(race,sources,output,admission):
    year,rnd=race['season'],race['round']; e.require_pre2026(year,rnd)
    e.require_review(admission)
    evidence=next((r for r in admission['results'] if r['race']==race and r['status']=='ADMITTED'),None)
    if evidence is None:raise ValueError('Session has no admitted evidence')
    folder=Path(output)/f'{year}-{rnd:02d}'; done=folder/'manifest.json'
    raw,records=e.read_raw(race,sources)
    manifest_path=e.source_folder(race,sources)/'manifest.json'
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest()!=evidence['source_manifest_hash']:raise ValueError('Admission source changed')
    source=d.artifact('SourceSnapshotManifest',**raw,availability_validation_ref=e.AUTHORITY,
        admission_evidence_ref=d.digest(evidence),residual_assumptions=evidence['assumptions'])
    code_hash=d.digest({name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
                        for name in ('development.py','comparison_data.py','expanded_sources.py','expanded_data.py')})
    if done.exists():
        manifest=data.read_json(done)
        if manifest['code_hash']!=code_hash or manifest['source_ref']!=source['artifact_id']:
            raise ValueError('Reconstruction cache belongs to different source/code; use a new output')
        for name,hash_value in manifest['hashes'].items():
            if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=hash_value: raise ValueError('Dataset hash mismatch')
        return manifest
    folder.mkdir(parents=True,exist_ok=True)
    clock=evidence['clock']
    observations=d.reconstruct(source,records,clock,reducer_factory=data.TyreReducer)
    initializations=d.initialize(observations)
    catalog=d.retrospective_catalog(records,clock,source,allow_restarts=True)
    resolutions=data.resolve_with_event_coverage(initializations,observations['observations'],catalog,clock)
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
            row['tyre']=data.tyre_view(o)
            try: row['grid']=d.grid(o)
            except ValueError as error: row['grid_failure']=str(error)
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
        data.write_json(folder/fn,value,compressed=True)
        hashes[fn]=hashlib.sha256((folder/fn).read_bytes()).hexdigest()
    manifest=dict(race=race,version='expanded-data/v1',code_revision=d.revision(),code_hash=code_hash,source_ref=source['artifact_id'],
                  hashes=hashes,drivers=len(observations['drivers']),checkpoints=len(rows),labels=len(labels),
                  initialization_run_ref=initializations['artifact_id'],resolution_run_ref=resolutions['artifact_id'],
                  eligibility=dict(Counter(r.get('eligibility','NO_OBSERVATION') for r in rows)),
                  outcomes=dict(Counter(r['outcome']['kind'] for r in labels)),
                  reasons=dict(Counter(reason for r in labels for reason in r['reasons'])),
                  unique_events=len({r['event_ref'] for r in labels if r['event_ref']}),
                  starts=sum(r['payload'].get('Status')=='Started' for r in records['SessionStatus']),
                  status='RECONSTRUCTED',assumptions=evidence['assumptions'],admission_evidence_ref=d.digest(evidence))
    data.write_json(done,manifest)
    return manifest


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sources',type=Path,default=e.ROOT/'sources');ap.add_argument('--output',type=Path,default=e.ROOT/'dataset');ap.add_argument('--admission',type=Path,default=e.ROOT/'admission/verify.json');args=ap.parse_args()
    admission=data.read_json(args.admission)
    if not admission.get('independent_review_pass'):raise ValueError('Independent admission review required before reconstruction')
    for item in admission['results']:e.require_pre2026(item['race']['season'],item['race']['round'])
    results=[]
    for item in admission['results']:
        if item['status']!='ADMITTED':continue
        race=item['race'];year,rnd=race['season'],race['round']
        if (year,rnd) in data.PARTITION:
            source=d.ROOT/'research/model-comparison/dataset-2'/f'{year}-{rnd:02d}'
            destination=args.output/source.name
            manifest=data.read_json(source/'manifest.json')
            for name,h in manifest['hashes'].items():
                if hashlib.sha256((source/name).read_bytes()).hexdigest()!=h:raise ValueError('Frozen dataset payload mismatch')
            if destination.exists():
                if (destination/'manifest.json').read_bytes()!=(source/'manifest.json').read_bytes():raise ValueError('Existing imported manifest mismatch')
            else:shutil.copytree(source,destination)
            result=dict(race=race,status='IMPORTED_UNCHANGED',manifest_hash=hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest())
        else:
            manifest=reconstruct_race(race,args.sources,args.output,admission)
            result=dict(race=race,status='RECONSTRUCTED',checkpoints=manifest['checkpoints'],labels=manifest['labels'],outcomes=manifest['outcomes'])
        results.append(result);data.write_json(args.output/'progress.json',results)
        print(f"{len(results)} {year} R{rnd} {result['status']}",flush=True)
    data.write_json(args.output/'partition.json',[r['race'] for r in admission['results'] if r['status']=='ADMITTED'])

if __name__=='__main__':main()
