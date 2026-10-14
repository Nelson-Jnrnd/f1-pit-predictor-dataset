"""Separate pre-2026 fitting investigation. Emits diagnostics, never a model."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from . import comparison as c, comparison_data as data, comparison_models as m, development as d
from .practical_metrics import verified_saved_fold


def component(x,y):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    result=dict(rows=len(y),classes=dict(Counter(map(int,y))))
    if not len(y):return {**result,'failure':'No rows'}
    result.update(columns=x.shape[1],rank=int(np.linalg.matrix_rank(x)),
                  condition_number=float(np.linalg.cond(x)))
    try:
        _,check=m.logistic_fit(x,y);result['registered_fit']=check
    except ValueError as e:result['registered_failure']=str(e)
    if len(set(y))<2:
        result['diagnosis']='No finite unpenalized logistic maximum: all outcomes in one class'
        result['boundary_probability']=float(y[0]);return result
    # Investigative objective scaling only. This is not a candidate or forecast fit.
    unique,inverse,counts=np.unique(x,axis=0,return_inverse=True,return_counts=True)
    successes=np.bincount(inverse,weights=y,minlength=len(unique))
    def objective(beta):
        z=unique@beta
        return float(np.sum(counts*np.logaddexp(0,z)-successes*z)/len(y)),unique.T@(counts*expit(z)-successes)/len(y)
    fit=minimize(objective,np.zeros(x.shape[1]),jac=True,method='BFGS',options=dict(maxiter=2000,gtol=1e-10))
    result['mean_loss_scaling_probe']=dict(success=bool(fit.success),message=str(fit.message),iterations=int(fit.nit),
        mean_gradient_max=float(np.max(np.abs(fit.jac))),sum_gradient_max=float(np.max(np.abs(fit.jac))*len(y)),
        max_abs_coefficient=float(np.max(np.abs(fit.x))),purpose='Numerical investigation only, no fitted model emitted')
    return result


def run(dataset,saved,output):
    output.mkdir(parents=True,exist_ok=True);folds=[]
    for fold in range(1,5):
        complete=verified_saved_fold(saved/f'fold-{fold}');units=[]
        for race in complete['config']['training']:
            cp,labels,_=c.open_race(dataset,race,output/'ledger.jsonl','DEVELOPMENT_FIT_DIAGNOSTIC',fold,complete['config']['cutoff'])
            units.extend(c.training_units(cp,labels))
        pp=[(r,h,y) for r,h,y in m.periods(units) if 'fallback' not in r['tyre']]
        final=[(r,y) for r,y in m.final_units(units) if 'fallback' not in r['tyre']]
        levels=[level for level in m.COMPOUNDS if any(r['tyre']['compound']==level for r,_,_ in pp)]
        hazard=component([m.design(r,h,levels) for r,h,_ in pp],[y for _,_,y in pp])
        tail=component([m.design(r,0,levels,True) for r,_ in final],[y for _,y in final])
        # Condition number can be infinite; JSON explicitly records this as text.
        for part in (hazard,tail):
            if 'condition_number' in part and not np.isfinite(part['condition_number']):part['condition_number']='INFINITE'
        folds.append(dict(fold=fold,cutoff=complete['config']['cutoff'],training_races=complete['config']['training'],
            compounds=levels,hazard=hazard,final_component=tail))
        print(f'Fold {fold}: hazard and final component inspected separately',flush=True)
    result=dict(version='tyre-fit-diagnostic/v1',folds=folds,code_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        final_exposure='No 2026 read',policy='No baseline coefficients, forecasts, registration or frozen results changed')
    data.write_json(output/'summary.json',result);return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',type=Path,required=True);ap.add_argument('--saved',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();run(args.dataset,args.saved,args.output)

if __name__=='__main__':main()
