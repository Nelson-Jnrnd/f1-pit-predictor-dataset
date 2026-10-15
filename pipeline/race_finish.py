"""Recover aggregate diagnostics/refit from immutable completed issue57 forecasts."""
from __future__ import annotations
import argparse
import datetime as dt
from pathlib import Path
import numpy as np
from . import race_context as rc, race_integrity as integrity, comparison_data as data, practical_metrics as p, development as d

_last_rows=None
_last_arrays=None


def confusion(rows,threshold):
    """Same confusion policy; cache immutable input arrays across threshold grid."""
    global _last_rows,_last_arrays
    if not np.isfinite(threshold) or not 0<=threshold<=1:raise ValueError('Invalid threshold')
    if _last_rows is not rows:
        valid=[];ys=[];ps=[];unknown=excluded=missing=0
        for row in rows:
            y=row.get('y3');prob=row.get('p3');eligible=row.get('eligible',True)
            valid.append(y in (0,1) and prob is not None)
            ys.append(y==1);ps.append(0. if prob is None else prob)
            unknown+=bool(eligible and y is None);excluded+=not eligible;missing+=bool(y is not None and prob is None)
        _last_rows=rows
        _last_arrays=(np.asarray(valid,dtype=bool),np.asarray(ys,dtype=bool),np.asarray(ps,dtype=float),unknown,excluded,missing)
    valid,y,prob,unknown,excluded,missing=_last_arrays
    alert=prob>=threshold
    tp=int(np.count_nonzero(valid&y&alert));fp=int(np.count_nonzero(valid&~y&alert))
    fn=int(np.count_nonzero(valid&y&~alert));tn=int(np.count_nonzero(valid&~y&~alert));n=tp+fp+fn+tn
    ratio=lambda a,b:a/b if b else None
    return dict(n=n,TP=tp,FP=fp,FN=fn,TN=tn,precision=ratio(tp,tp+fp),recall=ratio(tp,tp+fn),
        f1=ratio(2*tp,2*tp+fp+fn),prevalence=ratio(tp+fn,n),unknown_binary=unknown,
        excluded_attempts=excluded,missing_forecast_known_binary=missing)


def practical(rows):
    # Temporary substitution changes computation cost only; exact output policy is tested.
    old=p.confusion
    try:
        p.confusion=confusion
        return rc.practical(rows)
    finally:
        p.confusion=old
        global _last_rows,_last_arrays
        _last_rows=_last_arrays=None


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=rc.ROOT/'evaluation');args=ap.parse_args();output=args.output
    if (output/'delivery-complete.json').exists():integrity.verify_completed_output(output);return
    inputs=data.read_json(output/'input-freeze.json');partition=inputs['partition']
    original_proof=integrity.verify_original_numerics()
    original_code=d.digest({n:v['execution_sha256'] for n,v in original_proof.items() if n!='comparison_models.py'})
    scores=[];practical_rows=[];years=(2019,2020,2021,2023,2024,2025)
    for year in years:
        folder=output/str(year);complete=data.read_json(folder/'complete.json')
        if complete['config']['code_hash']!=original_code:raise ValueError('Not the original reviewed forecast execution')
        for race in complete['config']['training']+complete['config']['validation']:rc.e.require_pre2026(race['season'],race['round'])
        for fn,h in complete['hashes'].items():
            if rc.sha(folder/fn)!=h:raise ValueError('Completed forecast payload changed')
        scores.extend(data.read_json(folder/'scores.json.gz',True));practical_rows.extend(data.read_json(folder/'practical.json.gz',True))
    config=data.read_json(output/'2019/complete.json')['config']
    summary=rc.selection(scores);summary['by_season']={str(y):rc.selection([r for r in scores if r['key'][0].startswith(str(y)+'-')]) for y in years}
    print('Immutable fold aggregation complete; computing saved-forecast practical diagnostics',flush=True)
    summary['practical']=practical(practical_rows)
    summary.update(registration_hash=config['registration_hash'],code_hash=original_code,dependencies=config['dependencies'],
        analysis_code_hash=d.digest({n:rc.sha(d.ROOT/'pipeline'/n) for n in ('race_finish.py','race_context.py','race_integrity.py','practical_metrics.py','comparison.py')}),
        recovery='Original aggregate save failed on NumPy integer serialization; regenerated from byte-verified saved forecasts; no model tuning or retraining')
    data.write_json(output/'summary.json',summary);print('Recovered summary saved',flush=True)
    old,baseline_identity=integrity.verified_full_refit(partition)
    freeze=dict(selected=summary['selected'],registration_hash=summary['registration_hash'],code_hash=original_code,
        analysis_code_hash=summary['analysis_code_hash'],summary_sha256=rc.sha(output/'summary.json'),
        input_freeze_sha256=rc.sha(output/'input-freeze.json'),fold_input_binding_sha256=rc.sha(output/'fold-input-binding.json'),baseline_identity=baseline_identity,
        thresholds={n:v['final_threshold']['threshold'] for n,v in summary['practical'].items()},
        recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),qualifier='DEVELOPMENT_ONLY; inherited prior exposure and archive assumptions',final_outcomes_opened=False)
    if not freeze['selected']:raise ValueError('No supported selection')
    data.write_json(output/'selection-freeze.json',freeze);units=[];audit=data.read_json(rc.ROOT/'features/audit.json')
    for race in partition:
        cp,_=rc.causal_rows(rc.e.ROOT/'dataset',race,audit)
        labels=rc.open_labels(rc.e.ROOT/'dataset',race,output/'ledger.jsonl','PRE2026_FULL_REFIT',0)
        units.extend(rc.c.training_units(cp,labels))
    print(f'Frozen selection; refitting {freeze["selected"]} on all{len(partition)} races',flush=True)
    folder=output/'refit';folder.mkdir(exist_ok=True)
    selected,_=rc.rf.fit(units,freeze['selected'],old['B0'],folder,summary['registration_hash'])
    data.write_json(output/'all-pre2026-refit.json',dict(selected=selected,B0=old['B0'],training_races=partition,
        selection_ref=d.digest(freeze),reused_baseline_refit=True,dependency_lock=config['dependencies'],
        final_lock_status='NOT_CREATED; final testing remains gated',final_exposure='No new 2026 source/outcome read'))
    integrity.completion(output)
    print('Recovered aggregates and selected full-data refit complete',flush=True)

if __name__=='__main__':main()
