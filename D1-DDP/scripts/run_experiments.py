import argparse, json, os, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--samples',type=int,default=256); p.add_argument('--warmup',type=int,default=1); p.add_argument('--repeats',type=int,default=1); p.add_argument('--output',default='results/course'); p.add_argument('--steps',type=int,default=None,help='fixed measured optimizer updates per group'); a=p.parse_args()
if a.samples%256: p.error('samples must be divisible by 256')
code=Path(__file__).resolve().parents[1]; root=code.parent if code.name=='code' else code; out=(root/a.output).resolve(); out.mkdir(parents=True,exist_ok=True)
env=os.environ.copy(); env['OMP_NUM_THREADS']='1'; env['MKL_NUM_THREADS']='1'
configs=[('A1','train.py',128,1,'normal'),('A2','launch.py',64,1,'normal')]+[(f'C{k}_{strategy}','launch.py',16,k,strategy) for k in (1,2,4,8) for strategy in ('normal','delayed')]
for repeat in range(a.repeats):
    for name,entry,batch,k,strategy in configs:
        world=1 if entry=='train.py' else 2; steps=a.steps if a.steps is not None else a.samples//(world*batch*k)
        exp=f'{name}_r{repeat+1}'; cmd=[sys.executable,str(code/'src'/entry),'--data',str(root/'data'),'--output',str(out),'--experiment-id',exp,'--batch',str(batch),'--accum-steps',str(k),'--strategy',strategy,'--warmup',str(a.warmup),'--steps',str(steps),'--seed','42']
        (out/(exp+'_config.json')).write_text(json.dumps({'command':cmd,'samples_measured':steps*world*batch*k, 'measurement_mode':'fixed_updates' if a.steps is not None else 'fixed_samples','warmup_updates':a.warmup,'repeat':repeat+1},indent=2),encoding='utf-8')
        print('RUN',exp,flush=True)
        with (out/(exp+'.log')).open('w',encoding='utf-8') as log:
            subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
print('completed',flush=True)
