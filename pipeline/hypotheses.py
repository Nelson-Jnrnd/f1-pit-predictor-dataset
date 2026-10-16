"""Finite chronological hypothesis loop. Original experiments remain immutable."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time
import uuid
import joblib
import numpy as np
import scipy
import sklearn
from . import hypothesis_models as hm, race_context as rc, race_integrity as ri
from . import comparison as c, comparison_data as data, development as d, practical_metrics as p, race_finish as fast

ROOT=d.ROOT/'research/hypotheses'
YEARS=(2019,2020,2021,2023,2024,2025)
REF='RF_CONTEXT'
sha=ri.sha


def write(path,value):
    data.write_json(path,json.loads(json.dumps(value,default=lambda v:v.item())),path.suffix=='.gz')


def verify(folder,manifest='complete.json',config=None):
    record=data.read_json(folder/manifest)
    if config is not None and record['config']!=config:raise ValueError('Completed configuration changed')
    for filename,h in record['files'].items():
        path=folder/filename
        if not path.resolve().is_relative_to(folder.resolve()) or sha(path)!=h:raise ValueError('Completed payload changed: '+filename)
    return record


def freeze_inputs(output):
    reg=ROOT/'REGISTRATION.md';review=ROOT/'PROTOCOL_REVIEW.md'
    if subprocess.check_output(['git','status','--porcelain','--',str(reg)],cwd=d.ROOT,text=True):raise ValueError('Commit registration first')
    if 'PASS' not in review.read_text() or sha(reg) not in review.read_text():raise ValueError('Independent current protocol review required')
    versions=dict(python=f'{__import__("sys").version_info.major}.{__import__("sys").version_info.minor}',numpy=np.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,joblib=joblib.__version__)
    if versions!=dict(python='3.12',numpy='2.3.5',scipy='1.17.0',sklearn='1.8.0',joblib='1.5.3'):raise ValueError('Dependency lock mismatch')
    partition=data.read_json(rc.e.ROOT/'dataset/partition.json')
    for race in partition:rc.e.require_pre2026(race['season'],race['round'])
    audit=data.read_json(rc.ROOT/'features/audit.json');attest=data.read_json(rc.ROOT/'FEATURE_REVIEW.json')
    if not attest['pass'] or sha(rc.ROOT/'features/audit.json')!=attest['audit_sha256'] or sha(rc.ROOT/'features/source-verification.json')!=attest['source_verification_sha256']:raise ValueError('Feature evidence changed')
    if d.digest(partition)!=audit['partition_hash'] or audit['extractor_hash']!=sha(d.ROOT/'pipeline/race_features.py'):raise ValueError('Feature parent scope changed')
    admission=data.read_json(rc.e.ROOT/'admission/verify.json');rc.e.require_review(admission)
    if partition!=[r['race'] for r in admission['results'] if r['status']=='ADMITTED']:raise ValueError('Admission scope mismatch')
    ri.verify_completed_output(rc.ROOT/'evaluation')
    config=dict(partition=partition,registration_sha256=sha(reg),protocol_review_sha256=sha(review),dependencies=versions,
        code={str(path.relative_to(d.ROOT)):sha(path) for path in sorted((d.ROOT/'pipeline').glob('*.py'))},
        feature_review_sha256=sha(rc.ROOT/'FEATURE_REVIEW.json'),audit_sha256=sha(rc.ROOT/'features/audit.json'),
        source_verification_sha256=sha(rc.ROOT/'features/source-verification.json'),admission_sha256=sha(rc.e.ROOT/'admission/verify.json'),
        manifests={f"{r['season']}-{r['round']:02d}":sha(rc.e.ROOT/'dataset'/f"{r['season']}-{r['round']:02d}"/'manifest.json') for r in partition},
        reference_completion_sha256=sha(rc.ROOT/'evaluation/delivery-complete.json'))
    output.mkdir(parents=True,exist_ok=True);path=output/'inputs.json'
    if path.exists():
        if data.read_json(path)!=config:raise ValueError('Changed experiment identity; use new output path')
    else:write(path,config)
    return config,audit


def forecasts(rows,name,model,estimator,date,run):
    if model['cutoff']>date:raise ValueError('Inference cutoff violation')
    eligible=[r for r in rows if r.get('eligibility')=='ELIGIBLE' and 'episode_ref' in r and 'grid' in r]
    distributions=dict(zip((tuple(r['key']) for r in eligible),hm.distributions(eligible,name,model,estimator)))
    out=[]
    for cp in rows:
        r=dict(key=cp['key'],observation_ref=cp['observation_ref'],model=name,model_ref=model['artifact_id'],run_id=run,phase=c.phase(cp),model_fit_failure=None)
        if 'grid' in cp:r['k_tercile']=int(np.searchsorted(model['k_terciles'],cp['grid']['K_T'],side='right'))
        if not cp['observation_ref']:r['category']='A1'
        elif cp.get('eligibility')=='INELIGIBLE':r['category']='A2'
        elif cp.get('eligibility')=='INDETERMINATE':r['category']='A3'
        elif cp.get('eligibility')!='ELIGIBLE' or 'episode_ref' not in cp:r['category']='A0'
        else:
            r.update({k:cp[k] for k in ('episode_ref','initialization_run_ref','target_episode_key')})
            if 'grid' not in cp:r.update(category='A4',failure=cp['grid_failure'])
            else:r['snapshot']=d.artifact('PredictionSnapshot',distribution=distributions[tuple(cp['key'])],
                model_ref=model['artifact_id'],observation_ref=cp['observation_ref'],episode_ref=cp['episode_ref'],
                initialization_run_ref=cp['initialization_run_ref'],target_episode_key=cp['target_episode_key'],run_id=run,
                request_digest=d.digest(dict(grid=cp['grid'],tyre=cp['tyre'],features=cp['race_features'],model_ref=model['artifact_id'])))
        out.append(r)
    return out


def load_units(training,audit,ledger,year,cutoff):
    units=[]
    for race in training:
        if race['date']>=cutoff:raise ValueError('Training cutoff violation')
        cp,_=rc.causal_rows(rc.e.ROOT/'dataset',race,audit)
        _,labels,_=rc.ec.open_race(rc.e.ROOT/'dataset',race,ledger,'HYPOTHESIS_TRAIN',year,cutoff)
        if any(l['outcome']['kind']=='REALIZED_REGION_SET' for l in labels.values()):raise ValueError('Undeclared interval fitting')
        units.extend(c.training_units(cp,labels))
    return units


def reference(year):
    folder=rc.ROOT/'evaluation'/str(year);complete=data.read_json(folder/'complete.json')
    for name,h in complete['hashes'].items():
        if sha(folder/name)!=h:raise ValueError('Reference fold changed')
    models=data.read_json(folder/'models.json')
    scores=[r for r in data.read_json(folder/'scores.json.gz',True) if r['model']==REF]
    practical=[r for r in data.read_json(folder/'practical.json.gz',True) if r['model']==REF]
    return complete,models,scores,practical


def evaluate(name,output,config,audit):
    parent=output/name;scores_all=[];practical_all=[];ref_all=[]
    for year in YEARS:
        start=time.monotonic();validation=[r for r in config['partition'] if r['season']==year];cutoff=validation[0]['date']
        training=hm.scope(config['partition'],cutoff,name);old,models,refs,_=reference(year)
        if old['config']['validation']!=validation:raise ValueError('Reference validation scope mismatch')
        cfg=dict(name=name,year=year,cutoff=cutoff,training=training,validation=validation,inputs_sha256=sha(output/'inputs.json'),reference_complete_sha256=sha(rc.ROOT/'evaluation'/str(year)/'complete.json'))
        folder=parent/str(year);folder.mkdir(parents=True,exist_ok=True)
        if (folder/'complete.json').exists():verify(folder,config=cfg)
        else:
            fitpath=folder/'fit-complete.json'
            if fitpath.exists():
                verify(folder,'fit-complete.json',cfg);model=data.read_json(folder/'model.json');estimator=joblib.load(folder/(name+'.joblib'))
            else:
                units=load_units(training,audit,output/'ledger.jsonl',year,cutoff)
                b0=hm.b0_subset(units,cutoff,training,config['registration_sha256']) if name=='H4_RECENT' else models['B0']
                print(f'{name} {year}: fit {len(training)} races / {len(units)} resolved checkpoints',flush=True)
                model,estimator=hm.fit(units,name,b0,folder,config['registration_sha256'],training);del units
                write(folder/'model.json',model);write(fitpath,dict(config=cfg,files={'model.json':sha(folder/'model.json'),name+'.joblib':sha(folder/(name+'.joblib'))}))
            scores=[];practical=[];prediction_files=[]
            for race in validation:
                cp,manifest=rc.causal_rows(rc.e.ROOT/'dataset',race,audit)
                predicted=forecasts(cp,name,model,estimator,race['date'],str(uuid.uuid4()))
                predpath=folder/f"predictions-R{race['round']}.json.gz";write(predpath,predicted);prediction_files.append(predpath.name)
                _,labels,_=rc.ec.open_race(rc.e.ROOT/'dataset',race,output/'ledger.jsonl','HYPOTHESIS_VALIDATE',year)
                joined=c.join_scores(predicted,labels,manifest['resolution_run_ref'])
                if any(r['category'] in ('A0','A4','A5','A7','A8') for r in joined):raise ValueError('Invalid or missing forecast/target mapping')
                scores.extend(joined);practical.extend(p.adapt(r,labels.get(tuple(r['key'])),race) for r in predicted)
            if [r['key'] for r in scores]!=[r['key'] for r in refs] or {tuple(r['key']) for r in scores if 'score' in r}!={tuple(r['key']) for r in refs if 'score' in r}:raise ValueError('Reference cohort mismatch')
            write(folder/'scores.json.gz',scores);write(folder/'practical.json.gz',practical)
            files=prediction_files+['model.json',name+'.joblib','fit-complete.json','scores.json.gz','practical.json.gz']
            write(folder/'complete.json',dict(config=cfg,files={fn:sha(folder/fn) for fn in files},elapsed_seconds=time.monotonic()-start))
            del estimator
        scores_all.extend(data.read_json(folder/'scores.json.gz',True));practical_all.extend(data.read_json(folder/'practical.json.gz',True));ref_all.extend(refs)
        print(f'{name} {year}: complete',flush=True)
    stats=c.summarize(scores_all);current={tuple(r['key']):r for r in scores_all if 'score' in r};ref={tuple(r['key']):r for r in ref_all if 'score' in r}
    if current.keys()!=ref.keys() or len(current)!=stats['scored']:raise ValueError('Duplicate or unmatched scored keys')
    result=dict(name=name,statistics=stats,improvement_over_reference=c.uncertainty([(k[0],ref[k]['score']-current[k]['score']) for k in sorted(current)]),
        by_season={str(y):c.summarize([r for r in scores_all if r['key'][0].startswith(str(y)+'-')]) for y in YEARS},
        truncation=c.truncation_diagnostics(scores_all),practical=diagnostics(practical_all),inputs_sha256=sha(output/'inputs.json'),
        folds={str(y):sha(parent/str(y)/'complete.json') for y in YEARS})
    path=parent/'summary.json';write(path,result)
    print(f"{name}: score {stats['mean_log_score']:.6f}; improvement {result['improvement_over_reference']['mean']:.6f}",flush=True)
    return result


def diagnostics(rows):
    earlier=[r for r in rows if r['season']<2025];later=[r for r in rows if r['season']==2025]
    threshold=p.select_threshold(earlier);pooled=p.select_threshold(rows)
    return dict(validation=p.distribution_summary(rows),earlier_threshold=threshold,pooled_threshold=pooled,
        diagnostic_2025=rc.alerts(later,threshold['threshold']),year_2025=p.distribution_summary(later),
        in_sample_alert_metrics=rc.alerts(rows,pooled['threshold']),precision_recall_tradeoff=[dict(threshold=t,**p.confusion(rows,t)) for t in p.THRESHOLDS])


def finish(output,config,audit):
    records={n:data.read_json(output/n/'summary.json') for n in hm.IDS}
    scores={};refs=[];practical_ref=[]
    for year in YEARS:
        _,_,rs,ps=reference(year);refs.extend(rs);practical_ref.extend(ps)
    scores[REF]={tuple(r['key']):r for r in refs if 'score' in r}
    for name in hm.IDS:
        rows=[]
        for year in YEARS:
            verify(output/name/str(year));rows.extend(data.read_json(output/name/str(year)/'scores.json.gz',True))
        scores[name]={tuple(r['key']):r for r in rows if 'score' in r}
        if scores[name].keys()!=scores[REF].keys():raise ValueError('Final recommendation cohort mismatch')
    order=[REF]+list(hm.IDS);means={n:float(np.mean([r['score'] for r in scores[n].values()])) for n in order}
    best=min(order,key=lambda n:(means[n],order.index(n)));pairs={}
    for name in order:
        pairs[name]=c.uncertainty([(k[0],scores[name][k]['score']-scores[best][k]['score']) for k in sorted(scores[best])])
    chosen=next(n for n in order if pairs[n]['mean']<=pairs[n].get('se',0))
    summary=dict(models=records,reference=dict(name=REF,statistics=c.summarize(refs),practical=diagnostics(practical_ref)),means=means,
        raw_best=best,recommended=chosen,difference_from_best=pairs,inputs_sha256=sha(output/'inputs.json'),
        summaries={n:sha(output/n/'summary.json') for n in hm.IDS},exposure='Development only; no new 2026 read',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat())
    write(output/'summary.json',summary);write(output/'selection-freeze.json',dict(recommended=chosen,summary_sha256=sha(output/'summary.json'),inputs_sha256=sha(output/'inputs.json'),recorded_at=dt.datetime.now(dt.timezone.utc).isoformat()))
    training=hm.scope(config['partition'],'2026-01-01',chosen)
    if chosen==REF:
        original=data.read_json(rc.ROOT/'evaluation/all-pre2026-refit.json')
        if original['training_races']!=training:raise ValueError('Reference full refit scope mismatch')
        selected=original['selected'];source=rc.ROOT/'evaluation/refit/RF_CONTEXT.joblib'
        if sha(source)!=selected['estimator_sha256']:raise ValueError('Reference selected forest changed')
        import shutil
        (output/'refit').mkdir(exist_ok=True);shutil.copyfile(source,output/'refit/RF_CONTEXT.joblib')
        reused=True
    else:
        units=load_units(training,audit,output/'ledger.jsonl',0,'2026-01-01')
        b0=hm.b0_subset(units,'2026-01-01',training,config['registration_sha256'])
        selected,_=hm.fit(units,chosen,b0,output/'refit',config['registration_sha256'],training);reused=False
    write(output/'all-pre2026-refit.json',dict(selected=selected,training_races=training,reused_reference=reused,
        selection_sha256=sha(output/'selection-freeze.json'),final_outcomes_opened=False))
    files=[v for v in output.rglob('*') if v.is_file() and v.name!='completion.json']
    write(output/'completion.json',dict(files={str(v.relative_to(output)):sha(v) for v in files},final_outcomes_opened=False))
    print(f'Completed four hypotheses; recommended {chosen}; no final evaluation',flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',choices=hm.IDS);ap.add_argument('--finish',action='store_true');ap.add_argument('--output',type=Path,default=ROOT/'evaluation');args=ap.parse_args()
    if (args.output/'completion.json').exists():verify(args.output,'completion.json');print('Completed output verified; no writes',flush=True);return
    config,audit=freeze_inputs(args.output)
    old=p.confusion;p.confusion=fast.confusion
    try:
        if args.candidate:evaluate(args.candidate,args.output,config,audit)
        elif args.finish:finish(args.output,config,audit)
        else:raise ValueError('Choose one candidate or --finish')
    finally:p.confusion=old

if __name__=='__main__':main()
