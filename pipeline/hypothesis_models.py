"""Four registered hypotheses using only the admitted checkpoint feature view."""
from __future__ import annotations
import hashlib
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from . import race_models as rf, comparison_models as m, development as d

IDS=('H1_PERCENT','H2_DETAIL','H3_BOOST','H4_RECENT')
BOOST=dict(loss='log_loss',learning_rate=.08,max_iter=150,max_leaf_nodes=15,max_depth=None,
           min_samples_leaf=100,l2_regularization=10,max_bins=255,early_stopping=False,
           class_weight=None,random_state=rf.SEED)


def scope(partition,cutoff,name):
    from .expanded_sources import require_pre2026
    for race in partition:require_pre2026(race['season'],race['round'])
    earlier=[r for r in partition if r['date']<cutoff]
    if name=='H4_RECENT':
        seasons=sorted({r['season'] for r in earlier})[-2:]
        earlier=[r for r in earlier if r['season'] in seasons]
    if not earlier:raise ValueError('Empty chronological training scope')
    return earlier


def design(row,h,name):
    if name not in IDS:raise ValueError('Unregistered hypothesis')
    values=rf.design(row,h,'RF_CONTEXT')
    if name=='H1_PERCENT':
        n=row['grid']['N_T'];lap=row['grid']['L']
        values=[lap/n,h/n,(lap+h)/n,1/n]+values[6:]
        if 'fallback' not in row['tyre']:values[4]/=n
    return values


def b0_subset(units,cutoff,training,registration):
    risk=np.zeros(41,dtype=int);events=risk.copy()
    for _,h,y in m.periods(units):risk[min(h,40)]+=1;events[min(h,40)]+=y
    finals=m.final_units(units)
    if not finals or not np.any(risk):raise ValueError('No B0 training population')
    return d.artifact('ModelArtifact',id='B0',cutoff=cutoff,registration_ref=registration,
        dataset_refs=training,hazards=[float(e/r) if r else None for e,r in zip(events,risk)],
        q_open=sum(y for _,y in finals)/len(finals),floor=1e-6,
        k_terciles=np.quantile([r['grid']['K_T'] for r,_ in units],[1/3,2/3]).tolist(),
        counts=dict(risk=risk.tolist(),events=events.tolist(),final_risk=len(finals),final_none=sum(y for _,y in finals)))


def fit(units,name,b0,folder,registration,training):
    if name not in IDS:raise ValueError('Unregistered hypothesis')
    positive=[];negative=[]
    for i,(_,_,y) in enumerate(m.periods(units)):(positive if y else negative).append(i)
    if not positive or not negative:raise ValueError('Both training classes required')
    chosen=np.sort(np.random.default_rng(rf.SEED).choice(negative,min(150000,len(negative)),replace=False))
    indices=set(positive)|set(chosen.tolist());weight=len(negative)/len(chosen)
    x=[];y=[];weights=[]
    for i,(row,h,event) in enumerate(m.periods(units)):
        if i in indices:x.append(design(row,h,name));y.append(event);weights.append(1. if event else weight)
    params=BOOST.copy() if name=='H3_BOOST' else rf.PARAMETERS.copy()
    if name=='H2_DETAIL':params.update(max_depth=20,min_samples_leaf=30)
    estimator=(HistGradientBoostingClassifier if name=='H3_BOOST' else RandomForestClassifier)(**params)
    estimator.fit(np.asarray(x,dtype=np.float32),y,sample_weight=weights)
    folder.mkdir(parents=True,exist_ok=True);path=folder/(name+'.joblib');joblib.dump(estimator,path,compress=3)
    model=d.artifact('ModelArtifact',id=name,cutoff=b0['cutoff'],registration_ref=registration,
        parameters=params,seed=rf.SEED,q_open=b0['q_open'],floor=1e-6,k_terciles=b0['k_terciles'],
        training_races=training,B0_ref=b0['artifact_id'],repository_revision=d.revision(),
        training_periods=dict(positive=len(positive),negative=len(negative),sampled_negative=len(chosen),negative_weight=weight),
        estimator_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    return model,estimator


def distributions(rows,name,model,estimator):
    x=[];lengths=[]
    for row in rows:
        length=row['grid']['K_T']-1;lengths.append(length)
        x.extend(design(row,h,name) for h in range(length))
    prob=estimator.predict_proba(np.asarray(x,dtype=np.float32))[:,list(estimator.classes_).index(1)] if x else []
    output=[];offset=0
    for row,length in zip(rows,lengths):
        output.append(m.canonical(list(prob[offset:offset+length]),model['q_open'],row['grid'],model['floor']))
        offset+=length
    return output
