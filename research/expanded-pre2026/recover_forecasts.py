from pipeline import expanded_comparison as e,comparison_data as data,comparison as c,practical_metrics as p
from pathlib import Path
import hashlib
base=Path('research/expanded-pre2026')
for year in (2019,2020):
 folder=base/'evaluation'/str(year);complete=data.read_json(folder/'complete.json');models=data.read_json(folder/'models.json');run=complete['run_id'];pred=[];scores=[];practical=[]
 for race in complete['config']['validation']:
  df=base/'dataset'/f"{race['season']}-{race['round']:02d}";manifest=data.read_json(df/'manifest.json');cp=c.verified_file(df,'checkpoints',manifest)
  ps=e.forecasts(cp,models,race['date'],run);pred.extend(ps);data.write_json(folder/'predictions.partial.json.gz',pred,True)
  _,labels,_=e.open_race(base/'dataset',race,base/'evaluation/ledger.jsonl','DEVELOPMENT_VALIDATION_RECOVERY',year)
  scores.extend(c.join_scores(ps,labels,manifest['resolution_run_ref']));bycp={tuple(r['key']):r for r in cp}
  for row in ps:
   key=tuple(row['key']);q=p.adapt(row,labels.get(key),race)
   if row.get('category')=='A4' and key in labels and 'grid' in bycp[key]:q['y3']=p.binary_outcome(labels[key]['outcome'],bycp[key]['grid']['K_T'])
   practical.append(q)
  print(year,race['round'],flush=True)
 for name,value in [('predictions.json.gz',pred),('scores.json.gz',scores),('practical.json.gz',practical)]:
  data.write_json(folder/name,value,True);assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==complete['hashes'][name],(year,name)
 (folder/'predictions.partial.json.gz').unlink(missing_ok=True)
 print(year,'Exact saved fold payload hashes recovered',flush=True)
