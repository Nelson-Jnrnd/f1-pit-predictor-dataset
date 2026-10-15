"""Preserve missing B0 metadata without changing any fitted model or forecast."""
from pathlib import Path
from pipeline import hypotheses as run, hypothesis_models as hm, comparison_data as data, comparison as c, development as d


def main():
    output=run.ROOT/'evaluation';run.verify(output,'completion.json')
    config=data.read_json(output/'inputs.json');items=[]
    tasks=[(output/'H4_RECENT'/str(y)/'model.json',f'H4-{y}') for y in run.YEARS]
    refit=data.read_json(output/'all-pre2026-refit.json')
    if not refit['reused_reference']:tasks.append((output/'all-pre2026-refit.json','selected-refit'))
    for path,label in tasks:
        record=data.read_json(path);model=record['selected'] if label=='selected-refit' else record
        training=model['training_races'];units=[]
        for race in training:
            name=f"{race['season']}-{race['round']:02d}"
            if run.sha(run.rc.e.ROOT/'dataset'/name/'manifest.json')!=config['manifests'][name]:raise ValueError('Parent manifest changed')
            cp,labels,_=run.rc.ec.open_race(run.rc.e.ROOT/'dataset',race,output/'b0-supplement-ledger.jsonl','B0_METADATA_RECOVERY',label,model['cutoff'])
            units.extend(c.training_units(cp,labels))
        b0=hm.b0_subset(units,model['cutoff'],training,config['registration_sha256'])
        if b0['artifact_id']!=model['B0_ref'] or b0['q_open']!=model['q_open'] or b0['k_terciles']!=model['k_terciles']:raise ValueError('Reconstructed B0 differs from original model reference')
        d.verify_artifact(b0);dest=output/'b0-supplements'/(label+'.json');run.write(dest,b0)
        items.append(dict(original_model_path=str(path.relative_to(output)),model_sha256=run.sha(path),b0_path=str(dest.relative_to(output)),b0_sha256=run.sha(dest)))
        print(label,'B0 exact identity recovered',flush=True)
    run.write(output/'b0-supplement.json',dict(items=items,original_completion_sha256=run.sha(output/'completion.json'),
        code_sha256=run.sha(__file__),meaning='Deterministic metadata recovery only. Original fits, model IDs and forecasts unchanged.'))
    files=[p for p in output.rglob('*') if p.is_file() and p.name!='delivery-complete.json']
    run.write(output/'delivery-complete.json',dict(files={str(p.relative_to(output)):run.sha(p) for p in files},original_completion_sha256=run.sha(output/'completion.json'),final_outcomes_opened=False))
    run.verify(output,'delivery-complete.json')

if __name__=='__main__':main()
