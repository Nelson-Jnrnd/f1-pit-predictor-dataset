"""Fixed Random Forest subdistribution hazards; no retrospective inference inputs."""
from __future__ import annotations
import hashlib
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from . import comparison_models as m, development as d
from .race_features import FIELDS

IDS=('RF_GRID','RF_TYRE','RF_CONTEXT')
SEED=5702026
PARAMETERS=dict(n_estimators=64,max_depth=12,min_samples_leaf=100,max_features='sqrt',
    bootstrap=True,criterion='log_loss',class_weight=None,random_state=SEED,n_jobs=2)


def design(row,h,name):
    g=row['grid'];lap,n=g['L'],g['N_T']
    values=[lap,n,lap/n,h,h/n,(lap+h)/n]
    if name!='RF_GRID':
        tyre=row['tyre'];missing='fallback' in tyre
        values.extend([-1. if missing else tyre['age']+h,float(missing)])
        values.extend(float(not missing and tyre['compound']==level) for level in m.COMPOUNDS)
    if name=='RF_CONTEXT':
        context=row['race_features']['values']
        for field in FIELDS:
            v=context[field];values.extend([-1. if v is None else v,float(v is None)])
    return values


def fit(units,name,b0,folder,registration):
    if name not in IDS:raise ValueError('Unregistered candidate')
    # Sampling indices refer only to training periods and are independent of features.
    positive=[];negative=[]
    for i,(_,_,y) in enumerate(m.periods(units)):
        (positive if y else negative).append(i)
    if not positive or not negative:raise ValueError('Forest requires both classes')
    rng=np.random.default_rng(SEED)
    chosen=np.sort(rng.choice(negative,min(150000,len(negative)),replace=False))
    indices=set(positive)|set(chosen.tolist());negative_weight=len(negative)/len(chosen)
    x=[];y=[];weights=[]
    for i,(row,h,event) in enumerate(m.periods(units)):
        if i in indices:
            x.append(design(row,h,name));y.append(event);weights.append(1. if event else negative_weight)
    estimator=RandomForestClassifier(**PARAMETERS)
    estimator.fit(np.asarray(x,dtype=np.float32),y,sample_weight=weights)
    path=folder/(name+'.joblib');joblib.dump(estimator,path,compress=3)
    metadata=d.artifact('ModelArtifact',id=name,cutoff=b0['cutoff'],registration_ref=registration,
        parameters=PARAMETERS,seed=SEED,q_open=b0['q_open'],floor=1e-6,k_terciles=b0['k_terciles'],
        dataset_refs=b0['dataset_refs'],repository_revision=d.revision(),
        training_periods=dict(positive=len(positive),negative=len(negative),sampled_negative=len(chosen),negative_weight=negative_weight),
        estimator_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),dependency_lock='Python3.12/NumPy2.3.5/SciPy1.17.0/sklearn1.8.0/joblib1.5.3')
    return metadata,estimator


def distributions(rows,name,metadata,estimator):
    """Batched inference from causal checkpoint rows only, preserving ragged grids."""
    x=[];lengths=[]
    for row in rows:
        length=row['grid']['K_T']-1;lengths.append(length)
        x.extend(design(row,h,name) for h in range(length))
    probability=estimator.predict_proba(np.asarray(x,dtype=np.float32))[:,list(estimator.classes_).index(1)] if x else []
    output=[];offset=0
    for row,length in zip(rows,lengths):
        output.append(m.canonical(list(probability[offset:offset+length]),metadata['q_open'],row['grid'],metadata['floor']))
        offset+=length
    return output
