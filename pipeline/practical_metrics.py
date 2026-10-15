"""Additional diagnostics on frozen development forecasts; never changes a fit."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import hashlib
import math
from pathlib import Path
import numpy as np
from . import comparison as c, comparison_data as data, comparison_models as m, development as d

VERSION='practical-metrics/v1'
THRESHOLDS=tuple(i/100 for i in range(1,100))


def binary_outcome(outcome,k):
    """Unknown and horizon-crossing region sets have no binary label."""
    kind=outcome['kind']
    if kind=='REALIZED_NO_EVENT':return 0
    if kind=='REALIZED_REGION':return int(outcome['j']<min(3,k))
    if kind=='REALIZED_REGION_SET':
        if outcome['b']<min(3,k):return 1
        if outcome['a']>=min(3,k):return 0
    return None


def window_hit(outcome,a,b):
    kind=outcome['kind']
    if kind=='REALIZED_NO_EVENT':return 0
    if kind=='REALIZED_REGION':return int(a<=outcome['j']<=b)
    if kind=='REALIZED_REGION_SET':
        if a<=outcome['a']<=outcome['b']<=b:return 1
        if outcome['b']<a or outcome['a']>b:return 0
    return None


def confusion(rows,threshold):
    if not math.isfinite(threshold) or not 0<=threshold<=1:raise ValueError('Invalid threshold')
    scored=[r for r in rows if r.get('y3') in (0,1) and r.get('p3') is not None]
    counts=Counter(('TP' if r['p3']>=threshold else 'FN') if r['y3']==1 else
                   ('FP' if r['p3']>=threshold else 'TN') for r in scored)
    tp,fp,fn,tn=(counts[k] for k in ('TP','FP','FN','TN'))
    ratio=lambda a,b:a/b if b else None
    return dict(n=len(scored),TP=tp,FP=fp,FN=fn,TN=tn,precision=ratio(tp,tp+fp),
        recall=ratio(tp,tp+fn),f1=ratio(2*tp,2*tp+fp+fn),prevalence=ratio(tp+fn,len(scored)),
        unknown_binary=sum(r.get('eligible',True) and r.get('y3') is None for r in rows),
        excluded_attempts=sum(not r.get('eligible',True) for r in rows),
        missing_forecast_known_binary=sum(r.get('y3') is not None and r.get('p3') is None for r in rows))


def select_threshold(rows):
    eligible=[r for r in rows if r.get('y3') is not None and r.get('p3') is not None]
    if {r['y3'] for r in eligible}!={0,1}:raise ValueError('Threshold selection requires both classes')
    results=[(threshold,confusion(eligible,threshold)) for threshold in THRESHOLDS]
    best=max(item['f1'] for _,item in results if item['f1'] is not None)
    threshold,metrics=max((t,v) for t,v in results if v['f1'] is not None and abs(v['f1']-best)<=1e-12)
    return dict(threshold=threshold,selection=metrics,rule='Maximum F1, ties choose highest threshold',grid=list(THRESHOLDS))


def chronological_threshold(selection,holdout):
    sr={r['race'] for r in selection};hr={r['race'] for r in holdout}
    if sr&hr or not selection or not holdout or max(r['date'] for r in selection)>=min(r['date'] for r in holdout):
        raise ValueError('Threshold cohorts must be nonempty, disjoint and chronological')
    for r in selection+holdout:d.require_development(r['season'],r['round'])
    return select_threshold(selection)


def unique_stops(rows,threshold):
    events=defaultdict(list)
    for r in rows:
        if r.get('event_ref'):events[r['event_ref']].append(r)
    horizon={event:[r for r in rs if r.get('y3')==1] for event,rs in events.items()}
    horizon={event:rs for event,rs in horizon.items() if rs}
    alerts={event:sum(r.get('p3') is not None and r['p3']>=threshold for r in rs) for event,rs in horizon.items()}
    detected=sum(n>0 for n in alerts.values())
    return dict(identified_stops=len(events),with_known_horizon_checkpoint=len(horizon),detected=detected,
        recall=detected/len(horizon) if horizon else None,
        without_known_horizon_checkpoint=len(events)-len(horizon),
        missing_all_horizon_forecasts=sum(all(r.get('p3') is None for r in rs) for rs in horizon.values()),
        positive_checkpoint_alerts=sum(alerts.values()),repeated_positive_alerts=sum(max(0,n-1) for n in alerts.values()),
        analysis_class='RETROSPECTIVE_DIAGNOSTIC',denominator='Identified stops with a known in-horizon checkpoint')


def reliability(rows,probability,outcome):
    rs=sorted([r for r in rows if r.get(probability) is not None and r.get(outcome) is not None],key=lambda r:r[probability])
    return [dict(n=len(part),predicted=float(np.mean([r[probability] for r in part])),
                 observed=float(np.mean([r[outcome] for r in part])))
            for part in np.array_split(np.asarray(rs,dtype=object),10) if len(part)]


def distribution_summary(rows):
    forecast=[r for r in rows if r.get('p3') is not None]
    known=[r for r in forecast if r.get('y3') is not None]
    scored=[r for r in rows if r.get('score') is not None]
    window_known=[r for r in forecast if r.get('window_hit') is not None]
    event=[r for r in window_known if r.get('event_ref')]
    widths=[r['window_regions'] for r in forecast]
    ratio=lambda a,b:a/b if b else None
    return dict(attempts=len(rows),eligible=sum(r['eligible'] for r in rows),forecasts=len(forecast),
        forecast_availability=ratio(len(forecast),sum(r['eligible'] for r in rows)),
        known_binary_with_forecast=len(known),unknown_with_forecast=len(forecast)-len(known),
        short_grids=sum(r['k']<3 for r in forecast),
        forecast_failures=dict(Counter(r.get('failure','unavailable') for r in rows if r['eligible'] and r.get('p3') is None)),
        log_score=c.uncertainty([(r['race'],r['score']) for r in scored]) if scored else None,
        brier_p3=float(np.mean([(r['p3']-r['y3'])**2 for r in known])) if known else None,
        calibration_p3=reliability(rows,'p3','y3'),
        conditional_window_coverage=dict(n=len(event),observed=float(np.mean([r['window_hit'] for r in event])) if event else None,
            expected=float(np.mean([r['window_conditional_mass'] for r in event])) if event else None,
            ambiguous_hits=sum(r.get('event_ref') is not None and r.get('window_hit') is None for r in forecast)),
        absolute_window_calibration=reliability(rows,'window_mass','window_hit'),
        absolute_window_coverage=dict(n=len(window_known),observed=float(np.mean([r['window_hit'] for r in window_known])) if window_known else None,
            expected=float(np.mean([r['window_mass'] for r in window_known])) if window_known else None),
        window_width=dict(unit='canonical region count',quantiles=dict(zip(('min','p25','median','p75','max'),
            np.quantile(widths,[0,.25,.5,.75,1]).tolist())) if widths else None,
            open_ended_share=ratio(sum(r['window_open'] for r in forecast),len(forecast)),
            note='Open final-region windows have no finite lap-width upper bound'))


def alert_summary(rows,threshold):
    known=[r for r in rows if r.get('y3') is not None and r.get('p3') is not None]
    result=dict(threshold=threshold,checkpoint=confusion(rows,threshold),unique_stops=unique_stops(rows,threshold),
        always_alert=confusion([{**r,'p3':1.} for r in known],.5),
        never_alert=confusion([{**r,'p3':0.} for r in known],.5))
    result['race_uncertainty']={name:c.uncertainty([(r['race'],float(fn(r))) for r in known]) if known else None
        for name,fn in [('alert_share',lambda r:r['p3']>=threshold),
                        ('true_positive_share',lambda r:r['y3']==1 and r['p3']>=threshold),
                        ('positive_prevalence',lambda r:r['y3']==1),
                        ('brier_p3',lambda r:(r['p3']-r['y3'])**2)]}
    # Precision/recall are ratios. Do not label share intervals as ratio intervals.
    groups=defaultdict(list)
    for r in rows:groups[r['race']].append(r)
    result['by_race']={race:confusion(rs,threshold) for race,rs in groups.items()}
    result['leave_one_race_out']={race:confusion([r for r in rows if r['race']!=race],threshold)
                                    for race in groups}
    return result


def verified_saved_fold(folder):
    complete=data.read_json(folder/'complete.json')
    # Validate the full race list before opening a target-bearing result.
    for race in complete['config']['training']+complete['config']['validation']:
        d.require_development(race['season'],race['round'])
    cutoff=complete['config']['cutoff']
    if any(r['date']>=cutoff for r in complete['config']['training']):raise ValueError('Saved training cutoff violation')
    for filename,h in complete['hashes'].items():
        if hashlib.sha256((folder/filename).read_bytes()).hexdigest()!=h:raise ValueError('Frozen result hash mismatch')
    return complete


def adapt(record,label,race):
    out=dict(key=record['key'],race=record['key'][0],date=race['date'],season=race['season'],round=race['round'],
        model=record['model'],eligible=record.get('category') not in ('A0','A1','A2','A3'),
        event_ref=label.get('event_ref') if label else None,y3=None,p3=None)
    if label:
        out['y3']=binary_outcome(label['outcome'],max(1,record.get('snapshot',{}).get('distribution',{}).get('region_grid',{}).get('K_T',0))) if 'snapshot' in record else None
    if 'snapshot' not in record:
        out['failure']=record.get('failure',record.get('category','unavailable'));return out
    dist=record['snapshot']['distribution'];p=dist['event_region_probabilities'];q=dist['terminal_no_event_probability'];k=dist['region_grid']['K_T']
    if len(p)!=k or any(not math.isfinite(v) or v<1e-6 for v in p+[q]) or abs(sum(p)+q-1)>1e-9:raise ValueError('Invalid frozen PMF')
    out.update(p3=sum(p[:3]),k=k)
    win=d.window(p);out.update(window_regions=win['b']-win['a']+1,window_open=win['b']==k-1,
        window_mass=win['inside'],window_conditional_mass=win['inside']/sum(p))
    if not label:return out
    kind=label['outcome']['kind'];outcome=label['outcome']
    out.update(y3=binary_outcome(outcome,k),window_hit=window_hit(outcome,win['a'],win['b']))
    if kind=='REALIZED_REGION':probability=p[outcome['j']]
    elif kind=='REALIZED_REGION_SET':probability=sum(p[outcome['a']:outcome['b']+1])
    elif kind=='REALIZED_NO_EVENT':probability=q
    else:return out
    out['score']=-math.log(probability)
    return out


def run(dataset,saved,output):
    output.mkdir(parents=True,exist_ok=True)
    registration=d.ROOT/'research/full-pre2026/REGISTRATION.md'
    import subprocess
    if subprocess.check_output(['git','status','--porcelain','--',str(registration)],cwd=d.ROOT,text=True):raise ValueError('Commit registration first')
    all_rows=[];identities=[]
    for fold in range(1,5):
        folder=saved/f'fold-{fold}';complete=verified_saved_fold(folder)
        predictions=data.read_json(folder/'predictions.json.gz',True)
        allowed={f"{r['season']}-R{r['round']}-R":r for r in complete['config']['validation']}
        if any(r['key'][0] not in allowed for r in predictions):raise ValueError('Forecast race outside declared validation')
        labels={};checkpoints={}
        actual_manifests=[hashlib.sha256((dataset/f"{race['season']}-{race['round']:02d}"/'manifest.json').read_bytes()).hexdigest()
                          for race in complete['config']['training']+complete['config']['validation']]
        if actual_manifests!=complete['config']['dataset_manifests']:raise ValueError('Frozen dataset manifest mismatch')
        for race in allowed.values():
            cp,ls,manifest=c.open_race(dataset,race,output/'ledger.jsonl','DEVELOPMENT_DIAGNOSTIC',fold)
            labels.update(ls);checkpoints.update({tuple(r['key']):r for r in cp})
        expected={(tuple(row['key']),model) for row in checkpoints.values() for model in m.IDS}
        actual=[(tuple(row['key']),row['model']) for row in predictions]
        if len(actual)!=len(set(actual)) or set(actual)!=expected:raise ValueError('Incomplete or duplicate frozen forecast cohort')
        # Existing lineage checker must succeed before the extra metrics use labels.
        for race_id,race in allowed.items():
            ps=[r for r in predictions if r['key'][0]==race_id]
            manifest=data.read_json(dataset/f"{race['season']}-{race['round']:02d}"/'manifest.json')
            joined=c.join_scores(ps,labels,manifest['resolution_run_ref'])
            if any(r['category'] in ('A0','A5','A7','A8') for r in joined):raise ValueError('Frozen run lineage/mapping defect')
            for p in ps:
                key=tuple(p['key']);row=adapt(p,labels.get(key),race)
                # Missing forecasts still retain known binary labels on the causal grid.
                if p.get('category')=='A4' and key in labels and 'grid' in checkpoints[key]:
                    row['y3']=binary_outcome(labels[key]['outcome'],checkpoints[key]['grid']['K_T'])
                all_rows.append(row)
        identities.append(dict(fold=fold,complete_hash=hashlib.sha256((folder/'complete.json').read_bytes()).hexdigest(),config=complete['config']))
    result=dict(version=VERSION,analysis_class='EXPLORATORY_DEVELOPMENT_DIAGNOSTIC',
        registration_hash=hashlib.sha256(registration.read_bytes()).hexdigest(),code_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        saved_folds=identities,final_exposure='No 2026 source or outcome opened',models={})
    for model in m.IDS:
        rs=[r for r in all_rows if r['model']==model]
        selection=[r for r in rs if r['round']<=18];holdout=[r for r in rs if r['round']>18]
        try:chosen=chronological_threshold(selection,holdout)
        except ValueError as e:chosen=dict(failure=str(e))
        result['models'][model]=dict(full_saved_validation=distribution_summary(rs),threshold_selection=chosen,
            later_six_races=distribution_summary(holdout),
            later_alerts=alert_summary(holdout,chosen['threshold']) if 'threshold' in chosen else None)
    data.write_json(output/'summary.json',result)
    print('Frozen forecasts reused; practical diagnostics complete. No fitting or final opening.')
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',type=Path,required=True);ap.add_argument('--saved',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();run(args.dataset,args.saved,args.output)

if __name__=='__main__':main()
