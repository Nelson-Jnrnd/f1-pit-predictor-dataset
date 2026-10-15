"""Explicit provenance repair for the original issue57 execution; never alters fits."""
from __future__ import annotations
import argparse
import ast
import datetime as dt
import hashlib
from pathlib import Path
import subprocess
import time
from . import comparison_data as data, development as d, expanded_sources as e
from . import race_features as features

ROOT=features.ROOT
EXECUTION='d132510'
# Any runner change requires fresh explicit review of original-cache equivalence.
APPROVED_RUNNER_SHA='6363bcc9cba3f6989413a5b1213403f68544926195558feceaaf09e642674b37'
MODULES=('race_context.py','race_models.py','race_features.py','comparison.py','comparison_data.py',
         'comparison_models.py','expanded_models.py','expanded_comparison.py','expanded_sources.py','development.py','practical_metrics.py')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identities():return {n:sha(d.ROOT/'pipeline'/n) for n in MODULES}


def verify_original_numerics():
    """Fail rather than upgrade if any original numerical helper has changed."""
    if sha(d.ROOT/'pipeline/race_context.py')!=APPROVED_RUNNER_SHA:
        raise ValueError('Runner differs from reviewed identity-only upgrade')
    result={}
    saved=data.read_json(ROOT/'execution/modules.json')
    for name in MODULES:
        current=(d.ROOT/'pipeline'/name).read_bytes()
        original=(ROOT/'execution/race_context.py.txt').read_bytes() if name=='race_context.py' else current
        if hashlib.sha256(original).hexdigest()!=saved['modules'][name]:raise ValueError('Original numerical module digest mismatch: '+name)
        if name=='race_context.py':
            def core(raw):
                return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body
                    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name not in ('main',)}
            if core(original)!=core(current):raise ValueError('Numerical runner functions changed; refuse identity upgrade')
        elif original!=current:raise ValueError('Original numerical helper changed: '+name)
        result[name]=dict(execution_sha256=hashlib.sha256(original).hexdigest(),current_sha256=hashlib.sha256(current).hexdigest())
    return result


def verify_original_cache(folder,current_config):
    proof=verify_original_numerics()
    original_names=[n for n in MODULES if n!='comparison_models.py']
    original_code=d.digest({n:proof[n]['execution_sha256'] for n in original_names})
    complete=data.read_json(folder/'complete.json')
    old=complete['config']
    if old['code_hash']!=original_code or {k:v for k,v in old.items() if k!='code_hash'}!={k:v for k,v in current_config.items() if k!='code_hash'}:
        raise ValueError('Original cache does not match exact verified execution/input identity')
    data.write_json(folder/'identity-upgrade.json',dict(original_complete_sha256=sha(folder/'complete.json'),
        original_code_hash=original_code,current_tooling_code_hash=current_config['code_hash'],numerical_code=proof,
        interpretation='Explicit metadata-only acceptance; original configs and model identities remain unchanged'))


def verified_full_refit(partition):
    delivery=data.read_json(e.ROOT/'DELIVERY.json');path=e.ROOT/'evaluation/all-pre2026-refit.json'
    if sha(path)!=delivery['evidence']['evaluation/all-pre2026-refit.json']:raise ValueError('Saved full baseline refit hash mismatch')
    refit=data.read_json(path)
    if refit['training_races']!=partition:raise ValueError('Saved full baseline training scope differs')
    if refit['B0']['cutoff']!='2026-01-01':raise ValueError('Saved baseline refit cutoff mismatch')
    d.verify_artifact(refit['B0'])
    return refit,dict(path=str(path.relative_to(d.ROOT)),sha256=sha(path),delivery_sha256=sha(e.ROOT/'DELIVERY.json'),training_races=len(partition),cutoff='2026-01-01')


def input_freeze(dataset,output):
    partition=data.read_json(dataset/'partition.json')
    for r in partition:e.require_pre2026(r['season'],r['round'])
    audit=data.read_json(ROOT/'features/audit.json');_,baseline=verified_full_refit(partition)
    payload=dict(partition=partition,manifest_sha256={f"{r['season']}-{r['round']:02d}":sha(dataset/f"{r['season']}-{r['round']:02d}"/'manifest.json') for r in partition},
        feature_sha256={f"{r['race']['season']}-{r['race']['round']:02d}":r['features_hash'] for r in audit['results']},
        audit_sha256=sha(ROOT/'features/audit.json'),source_verification_sha256=sha(ROOT/'features/source-verification.json'),feature_review_sha256=sha(ROOT/'FEATURE_REVIEW.json'),
        registration_sha256=sha(ROOT/'REGISTRATION.md'),execution_commit=EXECUTION,numerical_code=verify_original_numerics(),baseline_refit=baseline,
        dependency_lock=dict(python='3.12',numpy='2.3.5',scipy='1.17.0',sklearn='1.8.0',joblib='1.5.3'),
        recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),stage='BEFORE_POOLED_SELECTION_AND_FULL_REFIT')
    if (output/'input-freeze.json').exists():(output/'input-freeze.json').rename(output/'input-freeze-initial.json')
    data.write_json(output/'input-freeze.json',payload)


def watch(output):
    deadline=time.monotonic()+900
    years=(2019,2020,2021,2023,2024,2025)
    while not all((output/str(y)/'complete.json').exists() for y in years):
        if time.monotonic()>deadline:raise TimeoutError('Bounded fold-identity watch expired')
        time.sleep(1)
    data.write_json(output/'fold-input-binding.json',dict(input_freeze_sha256=sha(output/'input-freeze.json'),
        folds={str(y):sha(output/str(y)/'complete.json') for y in years},
        numerical_code=verify_original_numerics(),recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        selection_existed_at_binding=(output/'selection-freeze.json').exists(),
        qualifier='External identity supplement; original execution configs remain unchanged'))
    print('All fold/input identities bound without modifying original execution artifacts',flush=True)


def completion(output):
    # Never rewrite the original execution configs, code hashes, model IDs or fits.
    binding=data.read_json(output/'fold-input-binding.json')
    if binding['input_freeze_sha256']!=sha(output/'input-freeze.json'):raise ValueError('Input freeze changed')
    for year,h in binding['folds'].items():
        if sha(output/year/'complete.json')!=h:raise ValueError('Original fold changed')
    freeze=data.read_json(output/'selection-freeze.json');refit=data.read_json(output/'all-pre2026-refit.json')
    if refit['selection_ref']!=d.digest(freeze):raise ValueError('Refit selection linkage mismatch')
    partition=data.read_json(output/'input-freeze.json')['partition']
    if refit['training_races']!=partition:raise ValueError('New refit scope mismatch')
    verified_full_refit(partition);code=verify_original_numerics()
    for model in ('selected','B0'):d.verify_artifact(refit[model])
    files=[p for p in output.rglob('*') if p.is_file() and p.name!='delivery-complete.json' and '.partial.' not in p.name]
    data.write_json(output/'delivery-complete.json',dict(version='race-context-completion/v1',
        files={str(p.relative_to(output)):sha(p) for p in sorted(files)},numerical_code=code,
        execution_identity='Original fold config.code_hash and model IDs retained; missing dependency bound explicitly',
        tooling_sha256=sha(__file__),final_outcomes_opened=False))
    print('Original execution and explicit identity supplements verified and bound',flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['freeze-inputs','watch-folds','complete']);ap.add_argument('--output',type=Path,default=ROOT/'evaluation');args=ap.parse_args()
    if args.command=='freeze-inputs':input_freeze(e.ROOT/'dataset',args.output)
    elif args.command=='watch-folds':watch(args.output)
    else:completion(args.output)

if __name__=='__main__':main()
