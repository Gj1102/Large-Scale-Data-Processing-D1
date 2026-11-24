import argparse,csv,json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser(); p.add_argument('--input',default='results/course'); p.add_argument('--output',default='figures'); p.add_argument('--profiler',default='results/profiler'); a=p.parse_args()
root=Path(a.input); out=Path(a.output); out.mkdir(parents=True,exist_ok=True); records=[]
def percentile(values, q):
    ordered=sorted(values); position=(len(ordered)-1)*q; low=int(position); high=min(low+1,len(ordered)-1)
    return ordered[low]+(ordered[high]-ordered[low])*(position-low)
for path in sorted(root.glob('*.csv')):
    if path.name == 'summary.csv': continue
    with path.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    if not rows: continue
    ts=[float(r['update_time_ms']) for r in rows]; samples=sum(int(r['effective_batch']) for r in rows)
    records.append({'id':path.stem,'world_size':rows[0]['world_size'],'k':int(rows[0]['accum_steps']),'strategy':rows[0]['sync_strategy'],'samples':samples,'updates':len(rows),'mean_ms':statistics.mean(ts),'std_ms':statistics.stdev(ts) if len(ts)>1 else None,'p50_ms':percentile(ts,.5),'p95_ms':percentile(ts,.95),'throughput':samples/(sum(ts)/1000),'loss':float(rows[-1]['loss'])})
if not records: raise SystemExit('No experiment CSVs')
with (root/'summary.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=records[0].keys()); w.writeheader(); w.writerows(records)
(root/'summary.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
by={r['id']:r for r in records}
# These clean reruns replace measurements that overlapped another process.
for name in ('C2_normal','C2_delayed','C4_normal','C4_delayed'):
    if name+'_clean' in by: by[name+'_r1']=by[name+'_clean']
def bar(names,metric,title,ylabel,file):
    selected=[by[n] for n in names if n in by]
    if not selected:return
    fig,ax=plt.subplots(figsize=(7,4)); ax.bar([r['id'] for r in selected],[r[metric] for r in selected]); ax.set(ylabel=ylabel,title=title); fig.tight_layout(); fig.savefig(out/file,dpi=160); plt.close(fig)
bar(['A1_r1','A2_r1'],'throughput','Single process vs DDP','Samples / second','A_throughput.png')
bar(['C4_normal_r1','C4_delayed_r1'],'mean_ms','K=4 synchronization strategies','Update time (ms)','B_time.png')
fig,ax=plt.subplots(figsize=(7,4))
for strategy in ('normal','delayed'):
    rs=[by[f'C{k}_{strategy}_r1'] for k in (1,2,4,8) if f'C{k}_{strategy}_r1' in by]
    if rs: ax.plot([r['k'] for r in rs],[r['throughput'] for r in rs],marker='o',label=strategy)
ax.set(xlabel='Accumulation steps K',ylabel='Samples / second',title='K vs throughput, micro-batch 16'); ax.set_xticks([1,2,4,8]); ax.legend(); fig.tight_layout(); fig.savefig(out/'C_throughput.png',dpi=160); plt.close(fig)
fig,ax=plt.subplots(figsize=(7,4))
for name in ('C4_normal_r1','C4_delayed_r1'):
    clean=name.replace('_r1','_clean'); path=root/((clean if (root/(clean+'.csv')).exists() else name)+'.csv')
    if path.exists():
        with path.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
        ax.plot([int(r['update_step']) for r in rows],[float(r['loss']) for r in rows],marker='o',label=name)
ax.set(xlabel='Measured update',ylabel='Cross entropy',title='K=4 loss'); ax.legend(); fig.tight_layout(); fig.savefig(out/'loss.png',dpi=160); plt.close(fig)
comm=[]
for s in ('normal','delayed'):
    path=Path(a.profiler)/(s+'_communication.json')
    if path.exists():
        events=json.loads(path.read_text(encoding='utf-8')); e=next((x for x in events if x['name']=='gloo:all_reduce'),None)
        if e: comm.append((s,e))
if comm:
    fig,axs=plt.subplots(1,2,figsize=(8,4)); labels=[s for s,e in comm]
    axs[0].bar(labels,[e['count'] for s,e in comm]); axs[0].set(ylabel='Calls per update',title='Gloo all-reduce calls')
    axs[1].bar(labels,[e['cpu_total_us']/1000 for s,e in comm]); axs[1].set(ylabel='Event time (ms)',title='Cumulative event time')
    fig.suptitle('Separate synthetic-input profiler'); fig.tight_layout(); fig.savefig(out/'communication.png',dpi=160); plt.close(fig)
