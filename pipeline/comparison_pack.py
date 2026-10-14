"""Lossless dataset packing and additive join-lineage projection for issue 53."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import lzma
from pathlib import Path
from . import development as d
from . import comparison_data as data


def pack_race(race,source_root,output_root):
    year,rnd=race['season'],race['round']; d.require_development(year,rnd)
    old=source_root/f'{year}-{rnd:02d}'; out=output_root/old.name
    manifest=data.read_json(old/'manifest.json')
    if manifest['race']!=race or manifest['status']!='RECONSTRUCTED': raise ValueError('Wrong imported dataset identity')
    code_hash=d.digest({name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
                        for name in ('development.py','comparison_data.py')})
    packing_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if (out/'manifest.json').exists():
        saved=data.read_json(out/'manifest.json')
        if saved['import_manifest_hash']!=d.digest(manifest) or saved['packing_hash']!=packing_hash:
            raise ValueError('Imported dataset changed')
        for name,h in saved['hashes'].items():
            if hashlib.sha256((out/name).read_bytes()).hexdigest()!=h: raise ValueError('Packed artifact corrupted')
        return saved
    out.mkdir(parents=True,exist_ok=True); hashes={}
    # Hash verification happens before reading any artifact as JSON.
    for name,h in manifest['hashes'].items():
        if hashlib.sha256((old/name).read_bytes()).hexdigest()!=h: raise ValueError('Import artifact hash mismatch')
    init=data.read_json(old/'initializations.json.gz',True)
    resolution=data.read_json(old/'resolutions.json.gz',True)
    d.verify_artifact(init); d.verify_artifact(resolution)
    if resolution['target_initialization_run_ref']!=init['artifact_id']: raise ValueError('Resolution initialization mismatch')
    initialized={r['observation_artifact_ref']:r for r in init['records']}
    labels=data.read_json(old/'labels.json.gz',True)
    checkpoints=data.read_json(old/'checkpoints.json.gz',True)
    for row in checkpoints:
        ref=row['observation_ref']
        if ref:
            r=initialized[ref]; row['initialization_run_ref']=init['artifact_id']
            if 'initialization' in r:
                row['episode_ref']=r['initialization']['artifact_id']
                row['target_episode_key']=r['initialization']['target_episode_key']
    resolutions={r['observation_artifact_ref']:r for r in resolution['records']}
    for row in labels:
        r=initialized[row['observation_ref']]['initialization']; label=resolutions[row['observation_ref']]
        if r['target_episode_key']!=label['target_episode_key']: raise ValueError('Imported episode identity mismatch')
        row.update(episode_ref=r['artifact_id'],initialization_run_ref=init['artifact_id'],
                   target_episode_key=r['target_episode_key'],resolution_run_ref=resolution['artifact_id'])
    for name in manifest['hashes']:
        raw=gzip.decompress((old/name).read_bytes())
        base=name.removesuffix('.json.gz')
        dest=base+('.json.xz' if base in ('observations','initializations') else '.json.gz')
        if base in ('checkpoints','labels'):
            data.write_json(out/dest,checkpoints if base=='checkpoints' else labels,True)
        elif base in ('observations','initializations'):
            # Same uncompressed canonical bytes; only the storage codec changes.
            (out/dest).write_bytes(lzma.compress(raw,preset=3))
        else: (out/dest).write_bytes((old/name).read_bytes())
        hashes[dest]=hashlib.sha256((out/dest).read_bytes()).hexdigest()
    result={**manifest,'hashes':hashes,'code_hash':code_hash,'import_manifest_hash':d.digest(manifest),
            'import_manifest':manifest,'packing_hash':packing_hash,'packing_revision':d.revision(),
            'initialization_run_ref':init['artifact_id'],'resolution_run_ref':resolution['artifact_id']}
    data.write_json(out/'manifest.json',result)
    return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dataset',type=Path,required=True)
    ap.add_argument('--sources',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); races=data.read_json(args.sources/'metadata/races.json')
    if [(r['season'],r['round']) for r in races]!=data.PARTITION: raise ValueError('Exact development partition required')
    for i,race in enumerate(races):
        pack_race(race,args.dataset,args.output)
        print(f"Packed {i+1}/39 {race['season']} R{race['round']}",flush=True)

if __name__=='__main__': main()
