"""Chronological multi-season comparison and full admitted pre-2026 refit."""
from __future__ import annotations
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import uuid
import numpy as np
import scipy
from . import comparison as c, comparison_data as data, development as d
from . import expanded_sources as e, expanded_models as m, practical_metrics as p

VERSION='expanded-comparison/v1'
RANKS={'B0':0,'PERCENT_AHEAD':1,'PERCENT_PROGRESS':2,'TYRE_RIDGE':3,'B1':4}


def open_race(dataset,race,ledger,kind,fold,cutoff=None):
    e.require_pre2026(race['season'],race['round'])
    if cutoff and race['date']>=cutoff:raise ValueError('Training cutoff violation')
    folder=dataset/f"{race['season']}-{race['round']:02d}";manifest=data.read_json(folder/'manifest.json')
    if any(manifest['race'][k]!=race[k] for k in ('season','round','date','session')) or manifest['status']!='RECONSTRUCTED':raise ValueError('Dataset identity mismatch')
    checkpoints=c.verified_file(folder,'checkpoints',manifest)
    ledger.parent.mkdir(parents=True,exist_ok=True)
    with ledger.open('a') as f:
        f.write(json.dumps(dict(race=[race['season'],race['round']],opening_kind=kind,protocol_id=VERSION,fold=fold,
            resolution_hash=manifest['hashes']['resolutions.json.gz'],recorded_at=dt.datetime.now(dt.timezone.utc).isoformat()))+'\n');f.flush()
    labels=c.verified_file(folder,'labels',manifest)
    if any(r.get('initialization_run_ref')!=manifest['initialization_run_ref'] or r.get('resolution_run_ref')!=manifest['resolution_run_ref'] for r in labels):raise ValueError('Target run lineage mismatch')
    if len({tuple(r['key']) for r in labels})!=len(labels):raise ValueError('Duplicate target keys')
    return checkpoints,{tuple(r['key']):r for r in labels},manifest


def forecasts(checkpoints,models,date,run):
    rows=[]
    for cp in checkpoints:
        for name in m.IDS:
            model=models[name]
            if model['cutoff']>date:raise ValueError('Model cutoff after inference race')
            row=dict(key=cp['key'],observation_ref=cp['observation_ref'],model=name,model_ref=model['artifact_id'],run_id=run,
                phase=c.phase(cp),tyre_fallback=cp.get('tyre',{}).get('fallback') if name in ('B1','TYRE_RIDGE') else None)
            if name=='TYRE_RIDGE' and 'levels' in model and cp.get('tyre',{}).get('compound') not in model['levels'] and not row['tyre_fallback']:
                row['tyre_fallback']='COMPOUND_NOT_IN_TRAINING'
            if 'grid' in cp:row['k_tercile']=int(np.searchsorted(model['k_terciles'],cp['grid']['K_T'],side='right'))
            if not cp['observation_ref']:row['category']='A1'
            elif cp.get('eligibility')=='INELIGIBLE':row['category']='A2'
            elif cp.get('eligibility')=='INDETERMINATE':row['category']='A3'
            elif cp.get('eligibility')!='ELIGIBLE' or 'episode_ref' not in cp:row['category']='A0'
            else:
                row.update({k:cp[k] for k in ('episode_ref','initialization_run_ref','target_episode_key')})
                try:
                    if 'grid' not in cp:raise ValueError(cp['grid_failure'])
                    distribution=m.predict(model,cp['grid'],cp['tyre'],models['B0'])
                    row['snapshot']=d.artifact('PredictionSnapshot',distribution=distribution,model_ref=model['artifact_id'],
                        observation_ref=cp['observation_ref'],episode_ref=cp['episode_ref'],initialization_run_ref=cp['initialization_run_ref'],
                        target_episode_key=cp['target_episode_key'],run_id=run,
                        request_digest=d.digest(dict(grid=cp['grid'],tyre=cp['tyre'] if name in ('B1','TYRE_RIDGE') else {},model_ref=model['artifact_id'])))
                except ValueError as ex:row.update(category='A4',failure=str(ex))
            rows.append(row)
    return rows


def selection(rows):
    stats={name:c.summarize([r for r in rows if r['model']==name]) for name in m.IDS}
    scored={name:{tuple(r['key']):r for r in rows if r['model']==name and 'score' in r} for name in m.IDS}
    expected={tuple(r['key']) for r in rows if r.get('expected_cohort')}
    defects=any(stats[n]['fit_or_forecast_defect'] for n in m.IDS)
    # Every core candidate must cover the exact cohort; B1's fitting failure is explicit.
    core=('B0','PERCENT_AHEAD','PERCENT_PROGRESS','TYRE_RIDGE')
    b1_supported=bool(expected) and scored['B1'].keys()==expected
    eligible=list(core)+(['B1'] if b1_supported else [])
    pairs={}
    for i,a in enumerate(m.IDS):
        for b in m.IDS[i+1:]:
            common=scored[a].keys()&scored[b].keys()
            pair=dict(common=len(common),unmatched_a=len(scored[a])-len(common),unmatched_b=len(scored[b])-len(common),
                expected_cohort=len(expected),analysis_class='PRIMARY_DEVELOPMENT' if common==expected and not defects else 'SECONDARY')
            if common:pair['difference_a_minus_b']=c.uncertainty([(key[0],scored[a][key]['score']-scored[b][key]['score']) for key in sorted(common)])
            pairs[a+' vs '+b]=pair
    chosen=None;reason='Full common cohort or valid run unavailable'
    if expected and not defects and all(scored[n].keys()==expected for n in core):
        best=min(eligible,key=lambda n:(stats[n]['mean_log_score'],RANKS[n]));options=[best]
        for n in eligible:
            if RANKS[n]>=RANKS[best]:continue
            delta=c.uncertainty([(key[0],scored[n][key]['score']-scored[best][key]['score']) for key in sorted(expected)])
            if delta['mean']<=delta.get('se',0):options.append(n)
        chosen=min(options,key=lambda n:RANKS[n]);reason='Full-cohort one-standard-error choice using registered complexity order'
    return dict(models=stats,pairs=pairs,selected=chosen,selection_reason=reason,reference='B1' if b1_supported else 'B0',
        reference_fallback_reason=None if b1_supported else 'B1 lacks a supported full-cohort fit; registered B0 reference fallback',
        truncation={n:c.truncation_diagnostics([r for r in rows if r['model']==n]) for n in m.IDS})


def practical(rows):
    result={}
    for name in m.IDS:
        rs=[r for r in rows if r['model']==name];train=[r for r in rs if r['season']<2025];later=[r for r in rs if r['season']==2025]
        try:threshold=p.select_threshold(rs)
        except ValueError as ex:threshold=dict(failure=str(ex))
        try:earlier=p.select_threshold(train)
        except ValueError as ex:earlier=dict(failure=str(ex))
        result[name]=dict(validation=p.distribution_summary(rs),final_threshold=threshold,
            in_sample_alert_metrics=p.alert_summary(rs,threshold['threshold']) if 'threshold' in threshold else None,
            earlier_threshold=earlier,diagnostic_2025=p.alert_summary(later,earlier['threshold']) if 'threshold' in earlier else None,
            year_2025=p.distribution_summary(later))
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',type=Path,default=e.ROOT/'dataset');ap.add_argument('--output',type=Path,default=e.ROOT/'evaluation');args=ap.parse_args()
    partition=data.read_json(args.dataset/'partition.json')
    for race in partition:e.require_pre2026(race['season'],race['round'])
    if partition!=sorted(partition,key=lambda r:r['date']) or len({(r['season'],r['round']) for r in partition})!=len(partition):raise ValueError('Invalid chronological partition')
    admission=data.read_json(e.ROOT/'admission/verify.json')
    if not admission.get('independent_review_pass'):raise ValueError('Admission review required')
    expected_partition=[r['race'] for r in admission['results'] if r['status']=='ADMITTED']
    if partition!=expected_partition:raise ValueError('Partition differs from independently admitted list')
    versions=dict(python=f'{sys.version_info.major}.{sys.version_info.minor}',numpy=np.__version__,scipy=scipy.__version__)
    if versions!=dict(python='3.12',numpy='2.3.5',scipy='1.17.0'):raise ValueError('Dependency lock mismatch')
    registration=e.ROOT/'REGISTRATION.md'
    if subprocess.check_output(['git','status','--porcelain','--',str(registration)],cwd=d.ROOT,text=True):raise ValueError('Commit registration before scoring')
    reg=hashlib.sha256(registration.read_bytes()).hexdigest()
    helpers=[Path(__file__),Path(m.__file__),Path(e.__file__),Path(c.__file__),Path(data.__file__),Path(d.__file__),Path(p.__file__),Path(c.m.__file__)]
    code=d.digest({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in helpers})
    years=sorted({r['season'] for r in partition});scores_all=[];practical_all=[];args.output.mkdir(parents=True,exist_ok=True)
    for year in years[1:]:
        validation=[r for r in partition if r['season']==year];cutoff=validation[0]['date'];training=[r for r in partition if r['date']<cutoff]
        folder=args.output/str(year);folder.mkdir(exist_ok=True)
        config=dict(year=year,cutoff=cutoff,training=training,validation=validation,registration_hash=reg,code_hash=code,dependencies=versions,
            admission_hash=hashlib.sha256((e.ROOT/'admission/verify.json').read_bytes()).hexdigest(),
            dataset_manifests=[hashlib.sha256((args.dataset/f"{r['season']}-{r['round']:02d}"/'manifest.json').read_bytes()).hexdigest() for r in training+validation])
        if (folder/'complete.json').exists():
            complete=data.read_json(folder/'complete.json')
            if complete['config']!=config:raise ValueError('Completed fold identity differs; choose new output')
            for name,h in complete['hashes'].items():
                if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=h:raise ValueError('Corrupt fold cache')
            scores_all.extend(data.read_json(folder/'scores.json.gz',True));practical_all.extend(data.read_json(folder/'practical.json.gz',True));print(f'{year}: cached verified',flush=True);continue
        units=[];refs=[]
        for race in training:
            cp,labels,manifest=open_race(args.dataset,race,args.output/'ledger.jsonl','DEVELOPMENT_JOIN',year,cutoff)
            if any(r['outcome']['kind']=='REALIZED_REGION_SET' for r in labels.values()):raise ValueError('Unregistered interval fitting required')
            units.extend(c.training_units(cp,labels));refs.append(manifest['hashes'])
        print(f'{year}: fitting {len(training)} races, {len(units)} resolved checkpoints',flush=True)
        models=m.fit(units,cutoff,refs,reg);data.write_json(folder/'models.json',models)
        forecasts_all=[];scores=[];practical_rows=[];run=str(uuid.uuid4())
        for race in validation:
            dataset_folder=args.dataset/f"{race['season']}-{race['round']:02d}";manifest=data.read_json(dataset_folder/'manifest.json')
            cp=c.verified_file(dataset_folder,'checkpoints',manifest);predicted=forecasts(cp,models,race['date'],run);forecasts_all.extend(predicted)
            data.write_json(folder/'predictions.partial.json.gz',forecasts_all,True)
            _,labels,_=open_race(args.dataset,race,args.output/'ledger.jsonl','DEVELOPMENT_VALIDATION',year)
            joined=c.join_scores(predicted,labels,manifest['resolution_run_ref']);scores.extend(joined);bycp={tuple(r['key']):r for r in cp}
            if any(r['category'] in ('A0','A5','A7','A8') for r in joined):raise ValueError('Invalid lineage/mapping in new run')
            for r in predicted:
                key=tuple(r['key']);row=p.adapt(r,labels.get(key),race)
                if r.get('category')=='A4' and key in labels and 'grid' in bycp[key]:row['y3']=p.binary_outcome(labels[key]['outcome'],bycp[key]['grid']['K_T'])
                practical_rows.append(row)
            print(f'{year}: validated R{race["round"]}',flush=True)
        data.write_json(folder/'predictions.json.gz',forecasts_all,True);data.write_json(folder/'scores.json.gz',scores,True);data.write_json(folder/'practical.json.gz',practical_rows,True)
        data.write_json(folder/'summary.json',selection(scores))
        names=('models.json','predictions.json.gz','scores.json.gz','practical.json.gz','summary.json')
        data.write_json(folder/'complete.json',dict(config=config,hashes={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in names},run_id=run,revision=d.revision()))
        (folder/'predictions.partial.json.gz').unlink(missing_ok=True);scores_all.extend(scores);practical_all.extend(practical_rows)
    summary=selection(scores_all);summary['practical']=practical(practical_all);summary['registration_hash']=reg;summary['code_hash']=code
    data.write_json(args.output/'summary.json',summary)
    if summary['selected'] is None:print('No supported selection; final refit withheld',flush=True);return
    # Freeze procedure selection and alert rules before full-data refit; no final read.
    selection_record=dict(version=VERSION,selected=summary['selected'],reference=summary['reference'],registration_hash=reg,
        code_hash=code,validation_evidence_hash=hashlib.sha256((args.output/'summary.json').read_bytes()).hexdigest(),
        thresholds={n:v['final_threshold'].get('threshold') for n,v in summary['practical'].items()},
        qualifier='DEVELOPMENT_ONLY; inherited PRIOR_EXPOSURE_DECLARED and RA-1..RA-6',final_outcomes_opened=False)
    data.write_json(args.output/'selection-freeze.json',selection_record)
    units=[];refs=[]
    for race in partition:
        cp,labels,manifest=open_race(args.dataset,race,args.output/'ledger.jsonl','PRE2026_FULL_REFIT',0,'2026-01-01')
        units.extend(c.training_units(cp,labels));refs.append(manifest['hashes'])
    print(f'Full refit: {len(partition)} races, {len(units)} resolved checkpoints',flush=True)
    models=m.fit(units,'2026-01-01',refs,reg);selected=models[summary['selected']]
    if 'fit_failure' in selected:raise ValueError('Selected all-data refit failed')
    payload=dict(selected=selected,B0=models['B0'],diagnostic_models=models,training_races=partition,selection_ref=d.digest(selection_record),
        dependency_lock=versions,admission_ref=selection_record['qualifier'],final_exposure='No 2026 source or outcome read',
        final_lock_status='NOT_CREATED: no final resolution run and F2 fixed metadata list; final execution remains separate')
    data.write_json(args.output/'all-pre2026-refit.json',payload)
    print('Expanded development and all-admitted-data refit complete; no final evaluation',flush=True)

if __name__=='__main__':main()
