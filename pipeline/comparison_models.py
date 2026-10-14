"""Registered estimators. Prediction accepts causal grid and tyre view only."""
from __future__ import annotations
from collections import Counter
import math
import numpy as np
from scipy.optimize import minimize, linprog
from scipy.special import expit
from . import development as d

IDS=('B0','B1','PERCENT_AHEAD','PERCENT_PROGRESS')
COMPOUNDS=('SOFT','MEDIUM','HARD','INTERMEDIATE','WET','OTHER')


def periods(units):
    for row,outcome in units:
        g=row['grid']; j=outcome.get('j',g['K_T'])
        for h in range(min(j+1,g['K_T']-1)):
            yield row,h,int(h==j)


def final_units(units):
    return [(row,int(outcome['kind']=='REALIZED_NO_EVENT')) for row,outcome in units
            if outcome.get('j',row['grid']['K_T'])>=row['grid']['K_T']-1]


def exposure(g,h,progress=False):
    lo=((g['L'] if progress else 0)+h)/g['N_T']; hi=lo+1/g['N_T']
    return np.maximum(0,np.minimum(hi,np.arange(1,11)/10)-np.maximum(lo,np.arange(10)/10))


def logistic_fit(x,y):
    x=np.asarray(x,dtype=float); y=np.asarray(y,dtype=float)
    if not len(y) or not np.any(y==0) or not np.any(y==1): raise ValueError('Logistic fit lacks both outcome classes')
    # Compress repeated covariate vectors without changing the likelihood.
    unique,inverse,counts=np.unique(x,axis=0,return_inverse=True,return_counts=True)
    successes=np.bincount(inverse,weights=y,minlength=len(unique))
    signed=np.vstack((unique[successes>0],-unique[successes<counts]))
    separation=linprog(-signed.sum(axis=0),A_ub=-signed,b_ub=np.zeros(len(signed)),
                       bounds=[(-1,1)]*x.shape[1],method='highs')
    if not separation.success:
        raise ValueError('Separation check failed')
    if -separation.fun>1e-7:
        raise ValueError('Unsupported separated logistic maximum likelihood fit')
    def objective(beta):
        z=unique@beta
        return np.sum(counts*np.logaddexp(0,z)-successes*z), unique.T@(counts*expit(z)-successes)
    fit=minimize(objective,np.zeros(x.shape[1]),jac=True,method='BFGS',
                 options=dict(maxiter=2000,gtol=1e-7))
    if (not fit.success and np.max(np.abs(fit.jac))>1e-5) or not np.all(np.isfinite(fit.x)) or np.max(np.abs(fit.x))>1000:
        raise ValueError(f'Unsupported logistic maximum likelihood fit: {fit.message}')
    return fit.x.tolist(),dict(success=bool(fit.success),gradient_max=float(np.max(np.abs(fit.jac))),iterations=int(fit.nit))


def design(row,h,levels,final=False):
    tyre=row['tyre']; compound=tyre['compound']; g=row['grid']
    if compound not in levels: raise ValueError('Compound has no training support')
    indicators=[float(compound==c) for c in levels[1:]]
    f=(g['N_T']-(g['L']+(0 if final else h)))/g['N_T']
    if final: return [1.,f]+indicators
    a=(tyre['age']+h)/100
    return [1.,a,a*a]+indicators+[f]


def fit_models(units,cutoff,dataset_refs,registration_ref):
    risk=np.zeros(41,dtype=int); events=risk.copy(); pp=list(periods(units))
    for _,h,y in pp: risk[min(h,40)]+=1; events[min(h,40)]+=y
    finals=final_units(units)
    if not finals or not np.any(risk): raise ValueError('No supported B0 training population')
    b0=dict(id='B0',hazards=[float(e/r) if r else None for e,r in zip(events,risk)],
            q_open=sum(y for _,y in finals)/len(finals),floor=1e-6,
            counts=dict(risk=risk.tolist(),events=events.tolist(),final_risk=len(finals),final_none=sum(y for _,y in finals)))
    models={'B0':b0}
    for name in IDS[2:]:
        progress=name=='PERCENT_PROGRESS'
        # Aggregation avoids millions of duplicate rows in the optimizer.
        counts=Counter((r['grid']['L'] if progress else 0,r['grid']['N_T'],h,y) for r,h,y in pp)
        xs=[]; ys=[]; ws=[]
        for (lap,n,h,y),w in counts.items(): xs.append(exposure(dict(L=lap,N_T=n),h,progress)); ys.append(y); ws.append(w)
        x=np.asarray(xs); y=np.asarray(ys); w=np.asarray(ws)
        supported=np.sum(x*w[:,None],axis=0)>0
        def objective(rates):
            z=x@rates
            # Events have positive rate at every optimizer start. 0 event-risk
            # yields infinite likelihood, never a clipped guessed probability.
            event=y==1
            if np.any(z[event]<=0): return math.inf,np.full(10,math.nan)
            loss=np.sum(w[~event]*z[~event])-np.sum(w[event]*np.log(-np.expm1(-z[event])))
            factor=np.ones(len(z)); factor[event]=-1/np.expm1(z[event])
            return loss,x.T@(w*factor)
        fit=minimize(objective,np.ones(10),jac=True,method='L-BFGS-B',bounds=[(0,None)]*10,
                     options=dict(maxiter=2000,ftol=1e-12,gtol=1e-7))
        if not fit.success or not np.all(np.isfinite(fit.x)):
            models[name]=dict(id=name,fit_failure=str(fit.message))
        else:
            models[name]=dict(id=name,rates=[float(v) if s else None for v,s in zip(fit.x,supported)],
                              q_open=b0['q_open'],floor=1e-6,iterations=int(fit.nit),objective=float(fit.fun))
    levels=[c for c in COMPOUNDS if any(r['tyre'].get('compound')==c for r,_,_ in pp)]
    tyre_pp=[(r,h,y) for r,h,y in pp if 'fallback' not in r['tyre']]
    tyre_final=[(r,y) for r,y in finals if 'fallback' not in r['tyre']]
    try:
        beta,check=logistic_fit([design(r,h,levels) for r,h,_ in tyre_pp],[y for _,_,y in tyre_pp])
        gamma,gcheck=logistic_fit([design(r,0,levels,True) for r,_ in tyre_final],[y for _,y in tyre_final])
        models['B1']=dict(id='B1',levels=levels,beta=beta,gamma=gamma,floor=1e-6,optimizer=[check,gcheck],
                          training_periods=len(tyre_pp),training_final=len(tyre_final))
    except ValueError as e: models['B1']=dict(id='B1',fit_failure=str(e))
    k_terciles=np.quantile([row['grid']['K_T'] for row,_ in units],[1/3,2/3]).tolist()
    return {name:d.artifact('ModelArtifact',**model,cutoff=cutoff,dataset_refs=dataset_refs,k_terciles=k_terciles,
                            registration_ref=registration_ref,repository_revision=d.revision(),
                            dependency_lock='Python3.12/NumPy2.3.5/SciPy1.17.0') for name,model in models.items()}


def canonical(hazards,q_open,g,floor=1e-6):
    if len(hazards)!=g['K_T']-1 or any(not math.isfinite(v) or not 0<=v<=1 for v in hazards+[q_open]):
        raise ValueError('Invalid raw hazard distribution')
    survival=1.; p=[]
    for rate in hazards: p.append(survival*rate); survival*=1-rate
    p.append(survival*(1-q_open)); q=survival*q_open
    scale=1-(g['K_T']+1)*floor
    if scale<0: raise ValueError('Grid too large')
    p=[v*scale+floor for v in p]; q=q*scale+floor
    if abs(sum(p)+q-1)>1e-9 or any(not math.isfinite(v) or v<floor for v in p+[q]): raise ValueError('Invalid canonical PMF')
    return dict(region_grid=g,event_region_probabilities=p,terminal_no_event_probability=q)


def predict(model,grid,tyre,b0):
    """No labels, source records, or other observations are accepted."""
    name=model['id']
    if name=='B1' and 'fallback' in tyre:
        return predict(b0,grid,tyre,b0)
    if 'fit_failure' in model: raise ValueError(model['fit_failure'])
    if name=='B0': return d.distribution(model,grid)
    hazards=[]
    row=dict(grid=grid,tyre=tyre)
    for h in range(grid['K_T']-1):
        if name=='B1': rate=float(expit(np.dot(design(row,h,model['levels']),model['beta'])))
        else:
            widths=exposure(grid,h,name=='PERCENT_PROGRESS')
            if any(width>1e-14 and rate is None for width,rate in zip(widths,model['rates'])):
                raise ValueError('Percentage interval has no training exposure')
            integral=sum(width*rate for width,rate in zip(widths,model['rates']) if rate is not None)
            rate=-math.expm1(-integral)
        hazards.append(rate)
    q=float(expit(np.dot(design(row,0,model['levels'],True),model['gamma']))) if name=='B1' else model['q_open']
    return canonical(hazards,q,grid,model['floor'])
