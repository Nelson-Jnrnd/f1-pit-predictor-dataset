"""Restore aggregates and the frozen final fit; never rerun validation candidates.

Reconstructed metadata is not evidence of historical file-opening times.
"""
import argparse
import datetime as dt
import json
import os
import shutil
from pathlib import Path
import numpy as np
from pipeline import hypotheses as run, hypothesis_models as hm, comparison_data as data

OUTPUT=run.ROOT/'evaluation'
RECOVERY=OUTPUT/'recovery'
ORIGINAL_INPUTS='648f012d1c3894f5c22f347daca40ccc88a5910f76f0ddfde0a5c926fd15ecb2'
ORIGINAL_ESTIMATOR='e910da39d02513ee567bd1d7acdcaccaadd60f83cb0dbc448b7245a5dcdd40a1'
EXPECTED={'RF_CONTEXT':2.1692023028626046,'H1_PERCENT':2.1614642550615435,
          'H2_DETAIL':2.2935250431613055,'H3_BOOST':2.257590709435792,'H4_RECENT':2.2298884149641762}


def now():return dt.datetime.now(dt.timezone.utc).isoformat()


def check_inputs():
    config=data.read_json(OUTPUT/'inputs.json')
    if run.sha(OUTPUT/'inputs.json')!=ORIGINAL_INPUTS:raise ValueError('Reconstructed inputs differ')
    for path,h in config['code'].items():
        if run.sha(run.d.ROOT/path)!=h:raise ValueError('Numerical procedure changed')
    return config


def aggregate():
    if (RECOVERY/'aggregate-complete.json').exists():
        run.verify(OUTPUT,'recovery/aggregate-complete.json');return
    RECOVERY.mkdir(exist_ok=True)
    config,_=run.freeze_inputs(OUTPUT)
    check_inputs()
    records={};scores={};refs=[];practical=[];folds={}
    for year in run.YEARS:
        complete,_,rs,ps=run.reference(year);refs.extend(rs);practical.extend(ps)
        for name in hm.IDS:
            folder=OUTPUT/name/str(year);saved=run.verify(folder)
            cfg=saved['config'];training=hm.scope(config['partition'],cfg['cutoff'],name)
            if (cfg['inputs_sha256']!=ORIGINAL_INPUTS or cfg['training']!=training or
                cfg['reference_complete_sha256']!=run.sha(run.rc.ROOT/'evaluation'/str(year)/'complete.json')):
                raise ValueError('Saved fold binding mismatch')
            rows=data.read_json(folder/'scores.json.gz',True)
            if [r['key'] for r in rows]!=[r['key'] for r in rs]:raise ValueError('Attempt cohort mismatch')
            known={tuple(r['key']):r for r in rows if 'score' in r}
            if known.keys()!={tuple(r['key']) for r in rs if 'score' in r}:raise ValueError('Score cohort mismatch')
            scores.setdefault(name,{}).update(known)
            folds[f'{name}/{year}/complete.json']=run.sha(folder/'complete.json')
    scores[run.REF]={tuple(r['key']):r for r in refs if 'score' in r}
    for name in hm.IDS:
        record=data.read_json(OUTPUT/name/'summary.json')
        if record['inputs_sha256']!=ORIGINAL_INPUTS:raise ValueError('Summary input mismatch')
        for year,h in record['folds'].items():
            if run.sha(OUTPUT/name/year/'complete.json')!=h:raise ValueError('Summary fold mismatch')
        if abs(record['statistics']['mean_log_score']-EXPECTED[name])>1e-12:raise ValueError('Saved score changed')
        records[name]=record
    order=[run.REF]+list(hm.IDS)
    means={n:float(np.mean([r['score'] for r in scores[n].values()])) for n in order}
    if any(abs(means[n]-EXPECTED[n])>1e-12 for n in order):raise ValueError('Recomputed score changed')
    best=min(order,key=lambda n:(means[n],order.index(n)))
    pairs={n:run.c.uncertainty([(k[0],scores[n][k]['score']-scores[best][k]['score']) for k in sorted(scores[best])]) for n in order}
    chosen=next(n for n in order if pairs[n]['mean']<=pairs[n].get('se',0))
    if chosen!='H1_PERCENT':raise ValueError('Frozen recommendation differs')
    old=run.p.confusion;run.p.confusion=run.fast.confusion
    try:reference=dict(name=run.REF,statistics=run.c.summarize(refs),practical=run.diagnostics(practical))
    finally:run.p.confusion=old
    run.write(OUTPUT/'summary.json',dict(models=records,reference=reference,means=means,raw_best=best,recommended=chosen,
        difference_from_best=pairs,inputs_sha256=ORIGINAL_INPUTS,summaries={n:run.sha(OUTPUT/n/'summary.json') for n in hm.IDS},
        exposure='Development only; no new 2026 read',recorded_at=now(),metadata_status='Reconstructed aggregate after workspace reset; not original execution record'))
    run.write(RECOVERY/'selection-freeze.json',dict(recommended=chosen,summary_sha256=run.sha(OUTPUT/'summary.json'),
        inputs_sha256=ORIGINAL_INPUTS,recorded_at=now(),meaning='Reasserts published H1 selection before replacement final fit; not original selection timestamp',
        thresholds={n:records[n]['practical']['earlier_threshold'] for n in hm.IDS}))
    run.write(RECOVERY/'inventory.json',dict(recorded_at=now(),reconstructed=['inputs.json (exact original digest)','summary.json','selection freeze (new timestamp)'],
        surviving='Four immutable candidate archives, parent canonical/features/reference archives, GitHub source, presentation and PDF',
        lost=['Original hypothesis root label-opening ledger','Original root completion and supplemental delivery manifests',
              'Original selection-freeze and final selected-model payload','B0 supplements and supplementary ledgers',
              'Interruption partial files/parity evidence','Stdout-repair evidence','Execution source snapshots/local Git bundles','Independent reviewer scratch evidence'],
        prior_finding='Original final-fit ledger had132/133 entries, missing2020R13, established before outage. Do not reconstruct opening times.',
        limitation='Candidate fits/forecasts/scores retain fold hashes and input binding. Historical actual-read times, prediction-before-label ordering and interruption parity cannot be re-audited from lost root evidence.',
        review_history='Prior independent candidate-result checks recorded in conversation survive as conclusions, not restored scratch files.',
        original_estimator_recorded_sha256=ORIGINAL_ESTIMATOR,new_validation_fits=0,final_outcomes_opened=False))
    paths=[OUTPUT/'inputs.json',OUTPUT/'summary.json',RECOVERY/'selection-freeze.json',RECOVERY/'inventory.json']
    run.write(RECOVERY/'aggregate-complete.json',dict(files={str(p.relative_to(OUTPUT)):run.sha(p) for p in paths},folds=folds))
    print('Restored24folds; reconstructed aggregate; frozen H1; no validation fits',flush=True)


def read_units(training,ledger,kind,fold,cutoff,audit=None):
    config=check_inputs();units=[];expected=[]
    if ledger.exists():raise ValueError('Partial recovery read exists; preserve and review before retry')
    intent=ledger.with_name(ledger.stem+'-intent.jsonl')
    for race in training:
        name=f"{race['season']}-{race['round']:02d}";path=run.rc.e.ROOT/'dataset'/name/'manifest.json'
        if run.sha(path)!=config['manifests'][name]:raise ValueError('Training source changed')
        with intent.open('a') as handle:
            handle.write(json.dumps(dict(race=[race['season'],race['round']],recorded_at=now(),manifest_sha256=run.sha(path),
                selection_sha256=run.sha(RECOVERY/'selection-freeze.json'),kind=kind))+'\n');handle.flush();os.fsync(handle.fileno())
        causal=run.rc.causal_rows(run.rc.e.ROOT/'dataset',race,audit)[0] if audit is not None else None
        cp,labels,_=run.rc.ec.open_race(run.rc.e.ROOT/'dataset',race,ledger,kind,fold,cutoff)
        with ledger.open('a') as handle:handle.flush();os.fsync(handle.fileno())
        expected.append([race['season'],race['round']])
        reads=[json.loads(s) for s in ledger.read_text().splitlines()]
        if [r['race'] for r in reads]!=expected:raise ValueError('Actual-read ledger gap')
        for r in reads:
            manifest=data.read_json(run.rc.e.ROOT/'dataset'/f"{r['race'][0]}-{r['race'][1]:02d}"/'manifest.json')
            if r['resolution_hash']!=manifest['hashes']['resolutions.json.gz']:raise ValueError('Read hash mismatch')
            if r['recorded_at']<data.read_json(RECOVERY/'selection-freeze.json')['recorded_at']:raise ValueError('Read precedes recovery freeze')
        if any(l['outcome']['kind']=='REALIZED_REGION_SET' for l in labels.values()):raise ValueError('Undeclared interval fitting')
        units.extend(run.c.training_units(causal if causal is not None else cp,labels))
        print(kind,name,len(expected),flush=True)
    return units


def refit():
    run.verify(OUTPUT,'recovery/aggregate-complete.json');config=check_inputs();folder=RECOVERY/'selected-refit'
    if (folder/'complete.json').exists():run.verify(folder);return
    folder.mkdir(exist_ok=False)
    training=hm.scope(config['partition'],'2026-01-01','H1_PERCENT')
    if len(training)!=133:raise ValueError('Wrong final training scope')
    run.write(folder/'start.json',dict(recorded_at=now(),selection_sha256=run.sha(RECOVERY/'selection-freeze.json'),
        recovery_code_sha256=run.sha(__file__),original_payload_available=False,new_validation_fits=0))
    audit=data.read_json(run.rc.ROOT/'features/audit.json')
    units=read_units(training,folder/'ledger.jsonl','RECOVERED_SELECTED_REFIT',0,'2026-01-01',audit)
    b0=hm.b0_subset(units,'2026-01-01',training,config['registration_sha256']);run.write(folder/'B0.json',b0)
    model,_=hm.fit(units,'H1_PERCENT',b0,folder,config['registration_sha256'],training)
    if model['training_periods']['positive']!=55400 or model['training_periods']['negative']!=1239034:raise ValueError('Training periods changed')
    run.write(folder/'model.json',dict(selected=model,training_races=training,selection_sha256=run.sha(RECOVERY/'selection-freeze.json'),
        recorded_at=now(),actual_read_count=133,final_outcomes_opened=False,
        recorded_original_estimator_sha256=ORIGINAL_ESTIMATOR,matches_recorded_original_digest=model['estimator_sha256']==ORIGINAL_ESTIMATOR,
        comparison_limit='Original estimator bytes unavailable. Digest comparison does not restore original payload or historical ledger.'))
    files=[p for p in folder.iterdir() if p.is_file()]
    run.write(folder/'complete.json',dict(files={p.name:run.sha(p) for p in files}));run.verify(folder)
    print('Final refit complete;133 actual reads; recorded digest match:',model['estimator_sha256']==ORIGINAL_ESTIMATOR,flush=True)


def b0():
    config=check_inputs();folder=RECOVERY/'b0-supplements';folder.mkdir(exist_ok=True)
    for year in run.YEARS:
        dest=folder/str(year)
        if (dest/'complete.json').exists():run.verify(dest);continue
        dest.mkdir(exist_ok=False);model=data.read_json(OUTPUT/'H4_RECENT'/str(year)/'model.json')
        units=read_units(model['training_races'],dest/'ledger.jsonl','RECOVERED_B0_METADATA',year,model['cutoff'])
        artifact=hm.b0_subset(units,model['cutoff'],model['training_races'],config['registration_sha256'])
        if artifact['artifact_id']!=model['B0_ref'] or artifact['q_open']!=model['q_open'] or artifact['k_terciles']!=model['k_terciles']:raise ValueError('B0 identity mismatch')
        run.write(dest/'B0.json',artifact)
        run.write(dest/'complete.json',dict(files={p.name:run.sha(p) for p in dest.iterdir() if p.is_file()}));del units
        print(year,'B0 identity exactly reconstructed',flush=True)


def complete():
    path=OUTPUT/'recovery-complete.json'
    if path.exists():run.verify(OUTPUT,'recovery-complete.json');print('Recovery delivery verified; no writes');return
    run.verify(OUTPUT,'recovery/aggregate-complete.json');run.verify(RECOVERY/'selected-refit')
    for year in run.YEARS:run.verify(RECOVERY/'b0-supplements'/str(year))
    check_inputs();sources=RECOVERY/'source';sources.mkdir(exist_ok=False)
    for p in (run.d.ROOT/'pipeline').glob('*.py'):shutil.copyfile(p,sources/p.name)
    for name in ('REGISTRATION.md','PROTOCOL_REVIEW.md','recover_delivery.py'):shutil.copyfile(run.ROOT/name,sources/name)
    files=[p for p in OUTPUT.rglob('*') if p.is_file()]
    run.write(path,dict(files={str(p.relative_to(OUTPUT)):run.sha(p) for p in files},selected_model_path='recovery/selected-refit/model.json',
        historical_evidence_limitations='recovery/inventory.json',original_root_completion_available=False,final_outcomes_opened=False))
    run.verify(OUTPUT,'recovery-complete.json');print('New recovery delivery complete',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('aggregate','refit','b0','complete','verify'))
    stage=parser.parse_args().stage
    if (OUTPUT/'recovery-complete.json').exists():run.verify(OUTPUT,'recovery-complete.json');print('Recovery delivery verified; no writes')
    else:globals()[stage]() if stage!='verify' else run.verify(OUTPUT,'recovery-complete.json')
