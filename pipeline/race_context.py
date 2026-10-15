"""Issue 57 chronological comparison. Never reads protected seasons."""
from __future__ import annotations
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import uuid
import joblib
import numpy as np
import scipy
import sklearn
from . import comparison as c, comparison_data as data, development as d
from . import expanded_sources as e, expanded_models as baseline, expanded_comparison as ec, practical_metrics as p
from . import race_models as rf, race_features as features, comparison_models as contract_models
from . import race_integrity as integrity

ROOT=features.ROOT
IDS=('B0','PERCENT_PROGRESS','TYRE_RIDGE')+rf.IDS
RANK={n:i for i,n in enumerate(IDS)}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def causal_rows(dataset,race,audit):
    e.require_pre2026(race['season'],race['round'])
    folder=dataset/f"{race['season']}-{race['round']:02d}";manifest=data.read_json(folder/'manifest.json')
    evidence=next(r for r in audit['results'] if r['race']==race)
    if sha(folder/'manifest.json')!=evidence['parent_manifest_hash']:raise ValueError('Feature parent mismatch')
    path=ROOT/'features'/f"{race['season']}-{race['round']:02d}.json.gz"
    if sha(path)!=evidence['features_hash']:raise ValueError('Feature payload mismatch')
    sidecar={tuple(r['key']):r for r in data.read_json(path,True)}
    rows=c.verified_file(folder,'checkpoints',manifest)
    for row in rows:
        if row['observation_ref']:
            feature=sidecar[tuple(row['key'])]
            if feature['observation_ref']!=row['observation_ref']:raise ValueError('Feature observation mismatch')
            row['race_features']={k:feature[k] for k in ('values','omissions','observation_ref','version')}
            row['race_features']['payload_ref']=evidence['features_hash']
    return rows,manifest


def open_labels(dataset,race,ledger,kind,fold):
    # Existing checked reader persists the actual opening before the outcome read.
    return ec.open_race(dataset,race,ledger,kind,fold)[1]


def forecasts(rows,models,estimators,date,run):
    eligible=[r for r in rows if r.get('eligibility')=='ELIGIBLE' and 'episode_ref' in r and 'grid' in r]
    distributions={n:dict(zip((tuple(r['key']) for r in eligible),rf.distributions(eligible,n,models[n],estimators[n]))) for n in rf.IDS}
    result=[]
    for cp in rows:
        for name in IDS:
            model=models[name]
            if model['cutoff']>date:raise ValueError('Inference cutoff violation')
            r=dict(key=cp['key'],observation_ref=cp['observation_ref'],model=name,model_ref=model['artifact_id'],run_id=run,
                phase=c.phase(cp),model_fit_failure=model.get('fit_failure'))
            if 'grid' in cp:r['k_tercile']=int(np.searchsorted(model['k_terciles'],cp['grid']['K_T'],side='right'))
            if not cp['observation_ref']:r['category']='A1'
            elif cp.get('eligibility')=='INELIGIBLE':r['category']='A2'
            elif cp.get('eligibility')=='INDETERMINATE':r['category']='A3'
            elif cp.get('eligibility')!='ELIGIBLE' or 'episode_ref' not in cp:r['category']='A0'
            else:
                r.update({k:cp[k] for k in ('episode_ref','initialization_run_ref','target_episode_key')})
                try:
                    if 'grid' not in cp:raise ValueError(cp['grid_failure'])
                    dist=distributions[name][tuple(cp['key'])] if name in rf.IDS else baseline.predict(model,cp['grid'],cp['tyre'],models['B0'])
                    r['snapshot']=d.artifact('PredictionSnapshot',distribution=dist,model_ref=model['artifact_id'],
                        observation_ref=cp['observation_ref'],episode_ref=cp['episode_ref'],initialization_run_ref=cp['initialization_run_ref'],
                        target_episode_key=cp['target_episode_key'],run_id=run,
                        request_digest=d.digest(dict(grid=cp['grid'],tyre=cp['tyre'],features=cp.get('race_features'),model_ref=model['artifact_id'])))
                except ValueError as ex:r.update(category='A4',failure=str(ex))
            result.append(r)
    return result


def selection(rows):
    stats={n:c.summarize([r for r in rows if r['model']==n]) for n in IDS}
    scored={n:{tuple(r['key']):r for r in rows if r['model']==n and 'score' in r} for n in IDS}
    expected={tuple(r['key']) for r in rows if r.get('expected_cohort')}
    defects=any(stats[n]['fit_or_forecast_defect'] for n in IDS)
    pairs={}
    for i,a in enumerate(IDS):
        for b in IDS[i+1:]:
            common=scored[a].keys()&scored[b].keys()
            pair=dict(common=len(common),unmatched_a=len(scored[a])-len(common),unmatched_b=len(scored[b])-len(common))
            if common:pair['difference_a_minus_b']=c.uncertainty([(k[0],scored[a][k]['score']-scored[b][k]['score']) for k in sorted(common)])
            pairs[a+' vs '+b]=pair
    chosen=None;best=None
    if expected and not defects and all(scored[n].keys()==expected for n in IDS):
        best=min(IDS,key=lambda n:(stats[n]['mean_log_score'],RANK[n]));options=[best]
        for n in IDS:
            if RANK[n]>=RANK[best]:continue
            delta=c.uncertainty([(k[0],scored[n][k]['score']-scored[best][k]['score']) for k in sorted(expected)])
            if delta['mean']<=delta.get('se',0):options.append(n)
        chosen=min(options,key=RANK.get)
    return dict(models=stats,pairs=pairs,selected=chosen,raw_best=best,expected_cohort=len(expected),
        truncation={n:c.truncation_diagnostics([r for r in rows if r['model']==n]) for n in IDS})


def alerts(rows,threshold):
    result=p.alert_summary(rows,threshold)
    groups={(r['race'],r['key'][1]) for r in rows if r['eligible']}
    result['eligible_driver_races']=len(groups)
    result['false_alerts_per_driver_race']=result['checkpoint']['FP']/len(groups) if groups else None
    return result


def practical(rows):
    result={}
    for name in IDS:
        rs=[r for r in rows if r['model']==name];earlier=[r for r in rs if r['season']<2025];later=[r for r in rs if r['season']==2025]
        threshold=p.select_threshold(rs);previous=p.select_threshold(earlier)
        result[name]=dict(validation=p.distribution_summary(rs),final_threshold=threshold,
            in_sample_alert_metrics=alerts(rs,threshold['threshold']),earlier_threshold=previous,
            diagnostic_2025=alerts(later,previous['threshold']),year_2025=p.distribution_summary(later),
            precision_recall_tradeoff=[dict(threshold=t,**p.confusion(rs,t)) for t in p.THRESHOLDS])
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',type=Path,default=e.ROOT/'dataset');ap.add_argument('--output',type=Path,default=ROOT/'evaluation');ap.add_argument('--resume-original-execution',action='store_true');args=ap.parse_args()
    if (args.output/'delivery-complete.json').exists() or (args.output/'completion.json').exists():
        integrity.verify_completed_output(args.output)
        print('Completed run verified; original model and result identities retained',flush=True)
        return
    audit=data.read_json(ROOT/'features/audit.json');attest=data.read_json(ROOT/'FEATURE_REVIEW.json')
    if not attest.get('pass') or attest['audit_sha256']!=sha(ROOT/'features/audit.json') or attest['source_verification_sha256']!=sha(ROOT/'features/source-verification.json'):
        raise ValueError('Independent current feature review required')
    if audit['extractor_hash']!=sha(Path(features.__file__)):raise ValueError('Extractor changed after audit')
    verification=data.read_json(ROOT/'features/source-verification.json')
    if verification['code_hash']!=sha(Path(__file__).with_name('race_feature_verify.py')):raise ValueError('Verifier changed after review')
    versions=dict(python=f'{__import__("sys").version_info.major}.{__import__("sys").version_info.minor}',numpy=np.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,joblib=joblib.__version__)
    if versions!=dict(python='3.12',numpy='2.3.5',scipy='1.17.0',sklearn='1.8.0',joblib='1.5.3'):raise ValueError('Dependency lock mismatch')
    if subprocess.check_output(['git','status','--porcelain','--',str(ROOT/'REGISTRATION.md')],cwd=d.ROOT,text=True):raise ValueError('Commit registration before scoring')
    reg=sha(ROOT/'REGISTRATION.md');code=d.digest({f.name:sha(f) for f in [Path(__file__),Path(rf.__file__),Path(features.__file__),Path(c.__file__),Path(p.__file__),Path(baseline.__file__),Path(ec.__file__),Path(data.__file__),Path(d.__file__),Path(e.__file__),Path(contract_models.__file__),Path(integrity.__file__)]})
    partition=data.read_json(args.dataset/'partition.json')
    for race in partition:e.require_pre2026(race['season'],race['round'])
    if d.digest(partition)!=audit['partition_hash']:raise ValueError('Partition audit mismatch')
    admission=data.read_json(e.ROOT/'admission/verify.json');e.require_review(admission)
    if partition!=[r['race'] for r in admission['results'] if r['status']=='ADMITTED']:raise ValueError('Partition differs from admitted list')
    args.output.mkdir(parents=True,exist_ok=True);scores_all=[];practical_all=[]
    for year in sorted({r['season'] for r in partition})[1:]:
        validation=[r for r in partition if r['season']==year];cutoff=validation[0]['date'];training=[r for r in partition if r['date']<cutoff]
        folder=args.output/str(year);folder.mkdir(exist_ok=True)
        config=dict(year=year,cutoff=cutoff,training=training,validation=validation,registration_hash=reg,code_hash=code,dependencies=versions,
            audit_hash=sha(ROOT/'features/audit.json'),feature_review_hash=sha(ROOT/'FEATURE_REVIEW.json'),
            manifests=[sha(args.dataset/f"{r['season']}-{r['round']:02d}"/'manifest.json') for r in training+validation])
        if (folder/'complete.json').exists():
            complete=data.read_json(folder/'complete.json')
            if complete['config']!=config:
                if not args.resume_original_execution:raise ValueError('Changed completed fold; use new output or explicit verified original-execution resume')
                integrity.verify_original_cache(folder,config)
            for fn,h in complete['hashes'].items():
                if sha(folder/fn)!=h:raise ValueError('Completed fold corrupt')
            scores_all.extend(data.read_json(folder/'scores.json.gz',True));practical_all.extend(data.read_json(folder/'practical.json.gz',True));print(f'{year}: cached',flush=True);continue
        units=[]
        for race in training:
            cp,_=causal_rows(args.dataset,race,audit);labels=open_labels(args.dataset,race,args.output/'ledger.jsonl','DEVELOPMENT_JOIN',year)
            if any(l['outcome']['kind']=='REALIZED_REGION_SET' for l in labels.values()):raise ValueError('Unregistered interval fitting')
            units.extend(c.training_units(cp,labels))
        saved=e.ROOT/'evaluation'/str(year);baseline_complete=data.read_json(saved/'complete.json')
        if sha(saved/'models.json')!=baseline_complete['hashes']['models.json']:raise ValueError('Frozen baseline models changed')
        if baseline_complete['config']['training']!=training or baseline_complete['config']['validation']!=validation:raise ValueError('Baseline fold scope mismatch')
        old=data.read_json(saved/'models.json');models={n:old[n] for n in IDS if n not in rf.IDS};estimators={}
        print(f'{year}: {len(training)} training races, {len(units)} resolved checkpoints',flush=True)
        for name in rf.IDS:
            models[name],estimators[name]=rf.fit(units,name,models['B0'],folder,reg)
            print(f'{year}: {name} fitted',flush=True)
        data.write_json(folder/'models.json',models);del units
        predictions=[];scores=[];practical_rows=[];run=str(uuid.uuid4())
        for race in validation:
            cp,manifest=causal_rows(args.dataset,race,audit)
            predicted=forecasts(cp,models,estimators,race['date'],run)
            # Persist predictions before opening the validation labels.
            data.write_json(folder/'predictions.partial.json.gz',predicted,True)
            labels=open_labels(args.dataset,race,args.output/'ledger.jsonl','DEVELOPMENT_VALIDATION',year)
            joined=c.join_scores(predicted,labels,manifest['resolution_run_ref'])
            if any(r['category'] in ('A0','A4','A5','A7','A8') for r in joined):raise ValueError('Invalid or incomplete forecast run')
            scores.extend(joined);predictions.extend(predicted)
            practical_rows.extend(p.adapt(r,labels.get(tuple(r['key'])),race) for r in predicted)
            print(f'{year}: validated R{race["round"]}',flush=True)
        for name,values in [('predictions',predictions),('scores',scores),('practical',practical_rows)]:data.write_json(folder/(name+'.json.gz'),values,True)
        data.write_json(folder/'summary.json',selection(scores))
        names=['models.json','predictions.json.gz','scores.json.gz','practical.json.gz','summary.json']+[n+'.joblib' for n in rf.IDS]
        data.write_json(folder/'complete.json',dict(config=config,hashes={n:sha(folder/n) for n in names},run_id=run,revision=d.revision()))
        (folder/'predictions.partial.json.gz').unlink(missing_ok=True);scores_all.extend(scores);practical_all.extend(practical_rows)
    summary=selection(scores_all);summary['by_season']={str(year):selection([r for r in scores_all if r['key'][0].startswith(str(year)+'-')]) for year in sorted({r['season'] for r in partition})[1:]}
    summary['practical']=practical(practical_all);summary.update(registration_hash=reg,code_hash=code,dependencies=versions)
    # NumPy comparison/sum scalars carry the same value but need native JSON types.
    summary=json.loads(json.dumps(summary,default=lambda value:value.item()))
    data.write_json(args.output/'summary.json',summary)
    if summary['selected'] is None:raise ValueError('No supported selection')
    input_identity=dict(partition_sha256=d.digest(partition),audit_sha256=sha(ROOT/'features/audit.json'),
        source_verification_sha256=sha(ROOT/'features/source-verification.json'),feature_review_sha256=sha(ROOT/'FEATURE_REVIEW.json'),
        manifest_sha256=[sha(args.dataset/f"{r['season']}-{r['round']:02d}"/'manifest.json') for r in partition],
        folds={str(year):sha(args.output/str(year)/'complete.json') for year in sorted({r['season'] for r in partition})[1:]})
    verified_baseline,baseline_identity=integrity.verified_full_refit(partition)
    freeze=dict(input_identity=input_identity,baseline_identity=baseline_identity,selected=summary['selected'],registration_hash=reg,code_hash=code,summary_sha256=sha(args.output/'summary.json'),
        thresholds={n:s['final_threshold']['threshold'] for n,s in summary['practical'].items()},
        qualifier='DEVELOPMENT_ONLY; RA1..RA6; PRIOR_EXPOSURE_DECLARED',final_outcomes_opened=False)
    data.write_json(args.output/'selection-freeze.json',freeze)
    units=[]
    for race in partition:
        cp,_=causal_rows(args.dataset,race,audit);labels=open_labels(args.dataset,race,args.output/'ledger.jsonl','PRE2026_FULL_REFIT',0)
        units.extend(c.training_units(cp,labels))
    old=verified_baseline;b0=old['B0'];chosen=freeze['selected'];folder=args.output/'refit';folder.mkdir(exist_ok=True)
    if chosen in rf.IDS:selected,_=rf.fit(units,chosen,b0,folder,reg)
    else:selected=old['diagnostic_models'][chosen]
    data.write_json(args.output/'all-pre2026-refit.json',dict(selected=selected,B0=b0,training_races=partition,
        selection_ref=d.digest(freeze),reused_baseline_refit=chosen not in rf.IDS,dependency_lock=versions,
        final_lock_status='NOT_CREATED; final evaluation remains gated',final_exposure='No new 2026 source/outcome read'))
    files=[p for p in args.output.rglob('*') if p.is_file() and p.name!='completion.json' and '.partial.' not in p.name]
    data.write_json(args.output/'completion.json',dict(files={str(p.relative_to(args.output)):sha(p) for p in files},
        code_hash=code,selection_freeze_sha256=sha(args.output/'selection-freeze.json'),refit_sha256=sha(args.output/'all-pre2026-refit.json'),final_outcomes_opened=False))
    print('Completed development comparison and full training-scope refit; no final evaluation',flush=True)

if __name__=='__main__':main()
