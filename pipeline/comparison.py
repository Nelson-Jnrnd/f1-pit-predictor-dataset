"""Chronological development comparison; never opens the final partition."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import uuid
import sys
import numpy as np
import scipy
from scipy.stats import t as student_t
from . import development as d
from . import comparison_data as data
from . import comparison_models as m

VERSION='model-comparison/v1'


def verified_file(folder,name,manifest):
    matches=[fn for fn in manifest['hashes'] if fn in (name+'.json.gz',name+'.json.xz')]
    if len(matches)!=1: raise ValueError('Ambiguous or missing dataset artifact')
    path=folder/matches[0]
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['hashes'][path.name]:
        raise ValueError('Dataset file hash mismatch')
    return data.read_json(path,compressed=True)


def open_race(dataset,race,ledger,kind,fold,cutoff=None):
    year,rnd=race['season'],race['round']; d.require_development(year,rnd)
    if cutoff and race['date']>=cutoff: raise ValueError('Training race reaches or exceeds fold cutoff')
    folder=dataset/f'{year}-{rnd:02d}'; manifest=data.read_json(folder/'manifest.json')
    if manifest['race']!=race or manifest['status']!='RECONSTRUCTED': raise ValueError('Dataset identity mismatch')
    checkpoints=verified_file(folder,'checkpoints',manifest)
    # Persist opening before any target-bearing read. All outcomes stay development.
    ledger.parent.mkdir(parents=True,exist_ok=True)
    with ledger.open('a') as file:
        file.write(json.dumps(dict(race=[year,rnd],opening_kind=kind,protocol_id='P-F1-development/#53',
                                   fold=fold,resolution_hash=manifest['hashes']['resolutions.json.gz'],
                                   recorded_at=dt.datetime.now(dt.timezone.utc).isoformat()))+'\n'); file.flush()
    labels=verified_file(folder,'labels',manifest)
    if any(r.get('initialization_run_ref')!=manifest['initialization_run_ref'] or
           r.get('resolution_run_ref')!=manifest['resolution_run_ref'] for r in labels):
        raise ValueError('Dataset target run lineage mismatch')
    return checkpoints,{tuple(r['key']):r for r in labels},manifest


def training_units(checkpoints,labels):
    units=[]
    for row in checkpoints:
        if row.get('eligibility')!='ELIGIBLE' or 'grid' not in row: continue
        label=labels.get(tuple(row['key']))
        if label is None: raise ValueError('Missing training resolution')
        if label['observation_ref']!=row['observation_ref']: raise ValueError('Training lineage mismatch')
        if any(label.get(field)!=row.get(field) for field in ('episode_ref','initialization_run_ref','target_episode_key')):
            raise ValueError('Training initialization lineage mismatch')
        outcome=label['outcome']
        if outcome['kind'] in ('REALIZED_REGION','REALIZED_NO_EVENT'): units.append((row,outcome))
        elif outcome['kind'] in ('MAPPING_CONFLICT','MAPPING_UNAVAILABLE'): raise ValueError('Defective training target mapping')
    return units


def phase(row):
    if 'grid' not in row: return 'UNKNOWN'
    return str(min(3,int(4*row['grid']['L']/row['grid']['N_T'])))


def forecasts(checkpoints,models,race_date,run_id):
    """This function has no label argument and never opens a file."""
    records=[]
    for row in checkpoints:
        for name in m.IDS:
            model=models[name]
            if model['cutoff']>race_date: raise ValueError('Inference cutoff after race')
            record=dict(key=row['key'],observation_ref=row['observation_ref'],model=name,
                        model_ref=model['artifact_id'],run_id=run_id,phase=phase(row),
                        tyre_fallback=row.get('tyre',{}).get('fallback') if name=='B1' else None)
            if 'grid' in row:
                record['k_tercile']=int(np.searchsorted(model['k_terciles'],row['grid']['K_T'],side='right'))
            if not row['observation_ref']: record['category']='A1'
            elif row.get('eligibility')=='INELIGIBLE': record['category']='A2'
            elif row.get('eligibility')=='INDETERMINATE': record['category']='A3'
            elif row.get('eligibility')!='ELIGIBLE' or 'episode_ref' not in row: record['category']='A0'
            else:
                record['episode_ref']=row['episode_ref']
                record['initialization_run_ref']=row['initialization_run_ref']
                record['target_episode_key']=row['target_episode_key']
                try:
                    if 'grid' not in row: raise ValueError(row['grid_failure'])
                    distribution=m.predict(model,row['grid'],row['tyre'],models['B0'])
                    record['snapshot']=d.artifact('PredictionSnapshot',distribution=distribution,
                        model_ref=model['artifact_id'],observation_ref=row['observation_ref'],
                        episode_ref=row['episode_ref'],initialization_run_ref=row['initialization_run_ref'],
                        target_episode_key=row['target_episode_key'],run_id=run_id,
                        request_digest=d.digest(dict(grid=row['grid'],tyre=row['tyre'] if name=='B1' else {},model_ref=model['artifact_id'])))
                except ValueError as e: record.update(category='A4',failure=str(e))
            records.append(record)
    return records


def join_scores(forecast,labels,resolution_run_ref=None):
    result=[]
    for row in forecast:
        out={k:v for k,v in row.items() if k!='snapshot'}
        label=labels.get(tuple(row['key']))
        # Co-report uncertain labels even when A4 takes precedence.
        if label:
            out.update(label_kind=label['outcome']['kind'],label_reasons=label['reasons'],
                       expected_cohort=row.get('category') not in ('A0','A1','A2','A3') and
                           label['outcome']['kind'] in ('REALIZED_REGION','REALIZED_REGION_SET','REALIZED_NO_EVENT'))
        if label and 'episode_ref' in row and (label['observation_ref']!=row['observation_ref'] or
            label.get('episode_ref')!=row.get('episode_ref') or
            label.get('initialization_run_ref')!=row.get('initialization_run_ref') or
            label.get('target_episode_key')!=row.get('target_episode_key') or
            resolution_run_ref is None or label.get('resolution_run_ref')!=resolution_run_ref):
            out['category']='A0'; result.append(out); continue
        if 'category' in row: result.append(out); continue
        if label is None: out['category']='A5'; result.append(out); continue
        outcome=label['outcome']; kind=outcome['kind']
        if kind=='NOT_REALIZED': out['category']='A6'
        elif kind=='MAPPING_CONFLICT': out['category']='A7'
        elif kind in ('MAPPING_UNAVAILABLE','GRID_UNAVAILABLE'): out['category']='A8'
        else:
            dist=row['snapshot']['distribution']; p=dist['event_region_probabilities']; q=dist['terminal_no_event_probability']
            if kind=='REALIZED_NO_EVENT': probability=q; out['category']='A11'; j=len(p)
            elif kind=='REALIZED_REGION': j=outcome['j']; probability=p[j]; out['category']='A9'
            elif kind=='REALIZED_REGION_SET':
                probability=sum(p[outcome['a']:outcome['b']+1]); out['category']='A10'; j=outcome['a']
            else: raise ValueError('Unknown realized outcome')
            out.update(score=-math.log(probability),p0=p[0],p3=sum(p[:3]),q=q,
                       y0=float(j==0),y3=float(j<min(3,len(p))),ynone=float(kind=='REALIZED_NO_EVENT'),
                       entropy=-sum(v*math.log(v) for v in p+[q]),
                       rps=sum((sum(p[:k+1])-float(j<=k))**2 for k in range(len(p)))/len(p),
                       event_ref=label.get('event_ref'))
            if kind=='REALIZED_REGION':
                seed=int(d.digest(row['key'])[:16],16)^5302027
                uniform=float(np.random.default_rng(seed).random())
                out['event_pit']=(sum(p[:j])+uniform*p[j])/sum(p)
            win=d.window(p)
            out.update(window_mass=win['inside'],window_event_mass=win['inside']/sum(p),
                       window_hit=float(win['a']<=j<=win['b']) if kind!='REALIZED_NO_EVENT' else 0.,
                       event_window_hit=float(win['a']<=j<=win['b']) if kind!='REALIZED_NO_EVENT' else None)
        result.append(out)
    return result


def uncertainty(differences):
    """CR2 for intercept-only OLS, Webb unrestricted bootstrap, race jackknife."""
    groups=defaultdict(list)
    for race,value in differences: groups[race].append(value)
    n=sum(len(v) for v in groups.values()); g=len(groups)
    mean=sum(sum(v) for v in groups.values())/n
    if g<2: return dict(mean=mean,races=g,descriptive_only=True)
    ns=np.array([len(v) for v in groups.values()],dtype=float)
    residual=np.array([sum(v)-len(v)*mean for v in groups.values()])
    # The cluster residual sum is inflated by (1-n_g/n)^(-1/2).
    se=float(np.sqrt(np.sum(residual**2/(1-ns/n)))/n)
    critical=float(student_t.ppf(.975,g-1))
    rng=np.random.default_rng(5302026)
    webb=np.array([-math.sqrt(1.5),-1.,-math.sqrt(.5),math.sqrt(.5),1.,math.sqrt(1.5)])
    draws=mean+(webb[rng.integers(0,6,size=(9999,g))]@residual)/n
    deleted=(n*mean-(residual+ns*mean))/(n-ns)
    most=int(np.argmax(np.abs(deleted-mean)))
    return dict(mean=mean,se=se,races=g,cr2_95=[mean-critical*se,mean+critical*se],
                webb_95=np.quantile(draws,[.025,.975]).tolist(),bootstrap_seed=5302026,
                descriptive_only=g<10,most_influential_race=list(groups)[most],
                largest_leave_one_out_change=float(np.max(np.abs(deleted-mean))),qualifier='LOW_POWER')


def summarize(rows):
    accounts=dict(Counter(r['category'] for r in rows)); scored=[r for r in rows if 'score' in r]
    missing=Counter(r.get('failure') for r in rows if r['category']=='A4')
    eligible=sum(r['category'] not in ('A1','A2','A3') for r in rows)
    summary=dict(attempts=len(rows),accounting=accounts,forecast_count=sum('category' not in r or r['category'] in ('A5','A6','A7','A8','A9','A10','A11') for r in rows),
                 scored=len(scored),eligible=eligible,forecast_failures=dict(missing),
                 uncertain_labels=sum(r.get('label_kind')=='NOT_REALIZED' for r in rows),
                 fit_or_forecast_defect=any(accounts.get(c,0) for c in ('A0','A5','A7','A8')),
                 scored_races=len({r['key'][0] for r in scored}),
                 b1_fallbacks=sum(r.get('tyre_fallback') is not None for r in rows))
    if not scored: return summary
    summary.update(mean_log_score=sum(r['score'] for r in scored)/len(scored),
                   brier_p0=sum((r['p0']-r['y0'])**2 for r in scored)/len(scored),
                   ranked_probability_score=sum(r['rps'] for r in scored)/len(scored),
                   entropy=sum(r['entropy'] for r in scored)/len(scored))
    bydriver=defaultdict(list)
    for r in scored: bydriver[tuple(r['key'][:2])].append(r['score'])
    summary['driver_race_weighted_log_score']=sum(np.mean(v) for v in bydriver.values())/len(bydriver)
    trajectories=defaultdict(list)
    for r in scored: trajectories[r.get('event_ref') or tuple(r['key'][:2])].append(r['score'])
    summary['event_trajectory_log_score']=dict(value=float(np.mean([np.mean(v) for v in trajectories.values()])),analysis_class='RETROSPECTIVE_DIAGNOSTIC')
    pit=[r['event_pit'] for r in scored if 'event_pit' in r]
    counts=np.histogram(pit,bins=np.linspace(0,1,11))[0]
    summary['event_only_randomized_pit']=dict(n=len(pit),counts=counts.tolist(),seed=5302027,
        chi_squared=float(np.sum((counts-len(pit)/10)**2/(len(pit)/10))) if pit else None,
        analysis_class='RETROSPECTIVE_DIAGNOSTIC')
    calibration={}
    for probability,outcome in [('p0','y0'),('p3','y3'),('q','ynone'),('window_mass','window_hit')]:
        ordered=sorted(scored,key=lambda r:r[probability])
        calibration[probability]=[dict(n=len(binrows),predicted=float(np.mean([r[probability] for r in binrows])),
                                       observed=float(np.mean([r[outcome] for r in binrows])))
                                  for binrows in np.array_split(np.array(ordered,dtype=object),10) if len(binrows)]
    summary['calibration']=calibration
    event=[r for r in scored if r['event_window_hit'] is not None]
    summary['window_event_coverage']=dict(n=len(event),observed=float(np.mean([r['event_window_hit'] for r in event])) if event else None,
                                       expected=float(np.mean([r['window_event_mass'] for r in event])) if event else None,
                                       analysis_class='RETROSPECTIVE_DIAGNOSTIC')
    return summary


def truncation_diagnostics(rows):
    population=[r for r in rows if r['category'] in ('A6','A9','A10','A11')]
    def share(rs):
        truncated=sum(r['category']=='A6' for r in rs)
        return dict(n=len(rs),truncated=truncated,share=truncated/len(rs) if rs else None)
    result={'overall':share(population)}
    for name,key in [('race',lambda r:r['key'][0]),('driver_race',lambda r:':'.join(r['key'][:2])),
                     ('k_tercile',lambda r:str(r.get('k_tercile','UNKNOWN'))),('phase',lambda r:r['phase'])]:
        groups=defaultdict(list)
        for r in population: groups[key(r)].append(r)
        result['by_'+name]={group:share(rs) for group,rs in sorted(groups.items())}
    strata=defaultdict(list)
    for r in population: strata[(r['key'][0],r.get('k_tercile'))].append(r)
    numerator=denominator=0.; empty=[]
    for key,rs in strata.items():
        scored=[r for r in rs if 'score' in r]
        if not scored: empty.append(list(key)); continue
        weight=len(rs)/len(scored)
        numerator+=weight*sum(r['score'] for r in scored); denominator+=weight*len(scored)
    result['inverse_resolvable_share']=dict(mean_log_score=numerator/denominator if denominator else None,
        empty_strata=empty,analysis_class='SECONDARY',assumption='Missing at random within race x K tercile; known indeterminate visits violate this. Indicative only.')
    shares=[v['share'] for v in result['by_race'].values() if v['share'] is not None]
    median=float(np.median(shares)) if shares else None
    selected=[race for race,v in result['by_race'].items() if median is not None and v['share']<median]
    subset=[r for r in population if r['key'][0] in selected and 'score' in r]
    result['below_median_races']=dict(median_share=median,races=selected,n=len(subset),
        mean_log_score=float(np.mean([r['score'] for r in subset])) if subset else None,analysis_class='RETROSPECTIVE_DIAGNOSTIC')
    result['mechanism_targeted']='NOT_COMPUTABLE: target-owned entry-lap contexts for indeterminate visits are not supplied (#19 dependency).'
    return result


def comparison_summary(rows):
    permodel={name:[r for r in rows if r['model']==name] for name in m.IDS}
    summary={name:{**summarize(rs),'truncation':truncation_diagnostics(rs)} for name,rs in permodel.items()}
    scored={name:{tuple(r['key']):r for r in rs if 'score' in r} for name,rs in permodel.items()}
    expected={tuple(r['key']) for r in rows if r.get('expected_cohort')}
    defects=any(summary[name]['fit_or_forecast_defect'] for name in m.IDS)
    pairs={}
    for i,a in enumerate(m.IDS):
        for b in m.IDS[i+1:]:
            common=scored[a].keys()&scored[b].keys()
            item=dict(common=len(common),unmatched_a=len(scored[a])-len(common),unmatched_b=len(scored[b])-len(common),
                      expected_cohort=len(expected),
                      analysis_class='PRIMARY' if scored[a].keys()==expected==scored[b].keys() and common
                          and not defects else 'SECONDARY')
            if common: item['difference_a_minus_b']=uncertainty([(key[0],scored[a][key]['score']-scored[b][key]['score']) for key in sorted(common)])
            pairs[a+' vs '+b]=item
    same=all(scored[name].keys()==expected for name in m.IDS)
    selected=None; selection_reason='Full identical scored cohorts unavailable; secondary comparisons only.'
    if same and scored['B0'] and not defects:
        ranks={'B0':0,'PERCENT_AHEAD':1,'PERCENT_PROGRESS':2,'B1':3}
        candidates=list(m.IDS[2:]); best=min(candidates,key=lambda name:summary[name]['mean_log_score'])
        options=[best]
        for name in candidates:
            if ranks[name]>=ranks[best]: continue
            diff=uncertainty([(key[0],scored[name][key]['score']-scored[best][key]['score']) for key in sorted(scored[name])])
            if diff['mean']<=diff.get('se',0): options.append(name)
        chosen=min(options,key=lambda name:ranks[name])
        selected=chosen if summary[chosen]['mean_log_score']<summary['B1']['mean_log_score'] else 'B1'
        selection_reason='Protocol one-standard-error choice; development result only, no lock or viewer change.'
    return dict(models=summary,pairs=pairs,selected=selected,selection_reason=selection_reason,
                by_race={race:{name:summarize([r for r in permodel[name] if r['key'][0]==race]) for name in m.IDS}
                         for race in sorted({r['key'][0] for r in rows})},
                by_phase={ph:{name:summarize([r for r in permodel[name] if r['phase']==ph]) for name in m.IDS}
                          for ph in ('0','1','2','3','UNKNOWN')})


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dataset',type=Path,required=True)
    ap.add_argument('--sources',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); races=data.read_json(args.sources/'metadata/races.json')
    dependencies=dict(python=f'{sys.version_info.major}.{sys.version_info.minor}',numpy=np.__version__,scipy=scipy.__version__)
    if dependencies!=dict(python='3.12',numpy='2.3.5',scipy='1.17.0'): raise ValueError('Runtime does not match declared dependency lock')
    if [(r['season'],r['round']) for r in races]!=data.PARTITION: raise ValueError('Exact development partition required')
    registration=d.ROOT/'research/model-comparison/REGISTRATION.md'; reg_hash=hashlib.sha256(registration.read_bytes()).hexdigest()
    # Reject uncommitted registration before scoring; declaration must be reviewable.
    import subprocess
    if subprocess.check_output(['git','status','--porcelain','--',str(registration)],cwd=d.ROOT,text=True):
        raise ValueError('Registration must be committed before scoring')
    args.output.mkdir(parents=True,exist_ok=True); all_scores=[]
    for fold in range(4):
        validation=[r for r in races if r['season']==2025 and fold*6<r['round']<=(fold+1)*6]
        cutoff=validation[0]['date']; training=[r for r in races if r['date']<cutoff]
        folder=args.output/f'fold-{fold+1}'; folder.mkdir(exist_ok=True)
        code_hash=d.digest({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                            (Path(__file__),Path(m.__file__),Path(d.__file__),Path(data.__file__))})
        config=dict(fold=fold+1,cutoff=cutoff,training=training,validation=validation,registration_hash=reg_hash,code_hash=code_hash,dependencies=dependencies,
                    dataset_manifests=[hashlib.sha256((args.dataset/f"{r['season']}-{r['round']:02d}"/'manifest.json').read_bytes()).hexdigest() for r in training+validation])
        if (folder/'complete.json').exists():
            complete=data.read_json(folder/'complete.json')
            if complete['config']!=config: raise ValueError('Completed fold has different inputs; choose a new output')
            for file,h in complete['hashes'].items():
                if hashlib.sha256((folder/file).read_bytes()).hexdigest()!=h: raise ValueError('Fold cache hash mismatch')
            all_scores.extend(data.read_json(folder/'scores.json.gz',True)); print(f'Fold {fold+1}: verified cached result',flush=True); continue
        units=[]; refs=[]
        for race in training:
            checkpoints,labels,manifest=open_race(args.dataset,race,args.output/'ledger.jsonl','DEVELOPMENT_JOIN',fold+1,cutoff)
            units.extend(training_units(checkpoints,labels)); refs.append(manifest['hashes'])
        print(f'Fold {fold+1}: fitting {len(training)} races, {len(units)} resolved checkpoints',flush=True)
        models=m.fit_models(units,cutoff,refs,reg_hash); data.write_json(folder/'models.json',models)
        forecasts_all=[]; scores=[]; run_id=str(uuid.uuid4())
        for race in validation:
            # Read causal checkpoints and forecast before the separate outcome opening.
            d.require_development(race['season'],race['round'])
            dataset_folder=args.dataset/f"{race['season']}-{race['round']:02d}"
            manifest=data.read_json(dataset_folder/'manifest.json')
            checkpoints=verified_file(dataset_folder,'checkpoints',manifest)
            predicted=forecasts(checkpoints,models,race['date'],run_id)
            forecasts_all.extend(predicted)
            data.write_json(folder/'predictions.partial.json.gz',forecasts_all,True)
            _,labels,_=open_race(args.dataset,race,args.output/'ledger.jsonl','DEVELOPMENT_VALIDATION',fold+1)
            scores.extend(join_scores(predicted,labels,manifest['resolution_run_ref']))
            print(f"Fold {fold+1}: scored {race['season']} R{race['round']}",flush=True)
        data.write_json(folder/'predictions.json.gz',forecasts_all,True)
        data.write_json(folder/'scores.json.gz',scores,True)
        data.write_json(folder/'summary.json',comparison_summary(scores))
        hashes={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in
                ('models.json','predictions.json.gz','scores.json.gz','summary.json')}
        data.write_json(folder/'complete.json',dict(config=config,hashes=hashes,run_id=run_id,revision=d.revision()))
        (folder/'predictions.partial.json.gz').unlink(missing_ok=True)
        all_scores.extend(scores)
    data.write_json(args.output/'summary.json',comparison_summary(all_scores))
    print('Four development folds complete. No final evaluation or viewer change.',flush=True)

if __name__=='__main__': main()
