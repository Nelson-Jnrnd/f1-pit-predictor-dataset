"""Bounded orchestration only; registered procedures and parameters never change."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/hypotheses/evaluation'


def wait_summary(name):
    deadline=time.monotonic()+3600
    path=OUT/name/'summary.json'
    while not path.exists():
        if time.monotonic()>deadline:raise TimeoutError('Summary deadline: '+name)
        time.sleep(5)
    return json.loads(path.read_text())


def main():
    env={**os.environ,'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'}
    for previous,name,rationale in [('H2_DETAIL','H3_BOOST','A different tree-fitting method may improve transfer.'),('H3_BOOST','H4_RECENT','Recent-history training may reduce dilution by older behaviour.')]:
        result=wait_summary(previous);score=result['statistics']['mean_log_score']
        print(f'{previous} result {score:.6f}. Next fixed hypothesis: {name}. {rationale}',flush=True)
        with (OUT/'loop.jsonl').open('a') as f:
            f.write(json.dumps(dict(previous=previous,score=score,next=name,rationale=rationale,parameters_changed=False))+'\n')
        if not (OUT/name/'summary.json').exists():
            with (OUT/(name+'.log')).open('w') as log:
                subprocess.run([sys.executable,'-u','-m','pipeline.hypotheses','--candidate',name],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=3600)
    wait_summary('H4_RECENT')
    print('All four candidate summaries ready for final recommendation',flush=True)

if __name__=='__main__':main()
