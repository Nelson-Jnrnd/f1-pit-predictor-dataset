"""Registered expanded procedures. Ridge is separate from unchanged B1."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from . import comparison_models as m, development as d

IDS=('B0','B1','PERCENT_AHEAD','PERCENT_PROGRESS','TYRE_RIDGE')


def fit(units,cutoff,refs,registration):
    models=m.fit_models(units,cutoff,refs,registration)
    pp=[(r,h,y) for r,h,y in m.periods(units) if 'fallback' not in r['tyre']]
    levels=[c for c in m.COMPOUNDS if any(r['tyre'].get('compound')==c for r,_,_ in pp)]
    try:
        x=np.asarray([m.design(r,h,levels) for r,h,_ in pp]);y=np.asarray([y for _,_,y in pp])
        if len(set(y))<2:raise ValueError('Ridge hazard requires both outcome classes')
        unique,inverse,counts=np.unique(x,axis=0,return_inverse=True,return_counts=True)
        successes=np.bincount(inverse,weights=y,minlength=len(unique))
        def objective(beta):
            z=unique@beta;penalty=beta.copy();penalty[0]=0
            return np.sum(counts*np.logaddexp(0,z)-successes*z)/len(y)+.001*np.dot(penalty,penalty)/2,unique.T@(counts*expit(z)-successes)/len(y)+.001*penalty
        fitted=minimize(objective,np.zeros(x.shape[1]),jac=True,method='BFGS',options=dict(maxiter=2000,gtol=1e-8))
        if (not fitted.success and max(abs(fitted.jac))>1e-7) or not np.all(np.isfinite(fitted.x)) or max(abs(fitted.x))>1000:raise ValueError(str(fitted.message))
        candidate=dict(id='TYRE_RIDGE',levels=levels,beta=fitted.x.tolist(),q_open=models['B0']['q_open'],floor=1e-6,
            optimizer=dict(success=bool(fitted.success),gradient_max=float(max(abs(fitted.jac))),iterations=int(fitted.nit)),
            penalty=.001,training_periods=len(pp))
    except ValueError as e:candidate=dict(id='TYRE_RIDGE',fit_failure=str(e))
    models['TYRE_RIDGE']=d.artifact('ModelArtifact',**candidate,cutoff=cutoff,dataset_refs=refs,registration_ref=registration,
        k_terciles=models['B0']['k_terciles'],repository_revision=d.revision(),dependency_lock='Python3.12/NumPy2.3.5/SciPy1.17.0')
    return models


def predict(model,grid,tyre,b0):
    if model['id']!='TYRE_RIDGE':return m.predict(model,grid,tyre,b0)
    if 'fallback' in tyre or ('levels' in model and tyre.get('compound') not in model['levels']):return m.predict(b0,grid,tyre,b0)
    if 'fit_failure' in model:raise ValueError(model['fit_failure'])
    row=dict(grid=grid,tyre=tyre)
    hazards=[float(expit(np.dot(m.design(row,h,model['levels']),model['beta']))) for h in range(grid['K_T']-1)]
    return m.canonical(hazards,model['q_open'],grid,model['floor'])
