import argparse,csv,json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser(); p.add_argument('--input',default='results/repeated'); p.add_argument('--output',default='figures/repeated'); p.add_argument('--profiler',default='results/profile_repeated'); a=p.parse_args()
root=Path(a.input); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
def pct(xs,q):
 xs=sorted(xs); x=(len(xs)-1)*q; lo=int(x); hi=min(lo+1,len(xs)-1); return xs[lo]+(xs[hi]-xs[lo])*(x-lo)
groups={}
for path in sorted(root.glob('*_r[123].csv')):
 with path.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
 if not rows: continue
 name=path.stem.rsplit('_r',1)[0]; ts=[float(r['update_time_ms']) for r in rows]; n=sum(int(r['effective_batch']) for r in rows)
 groups.setdefault(name,[]).append((rows,ts,n/(sum(ts)/1000)))
if not groups: raise SystemExit('No repeat CSV files found')
summary=[]
for name,runs in sorted(groups.items()):
 times=[t for rows,ts,thr in runs for t in ts]; throughputs=[thr for rows,ts,thr in runs]; losses=[float(r['loss']) for rows,ts,thr in runs for r in rows]
 r={'name':name,'repeats':len(runs),'updates_per_repeat':len(runs[0][1]),'samples_per_repeat':sum(int(row['effective_batch']) for row in runs[0][0]),'mean_update_ms':statistics.mean(times),'std_update_ms':statistics.stdev(times) if len(times)>1 else None,'p50_ms':pct(times,.5),'p95_ms':pct(times,.95),'throughput_mean':statistics.mean(throughputs),'throughput_std_between_repeats':statistics.stdev(throughputs) if len(throughputs)>1 else None,'repeat_throughputs':throughputs,'mean_loss':statistics.mean(losses),'profiler_count':None,'profiler_total_ms':None}
 if name.startswith('C'):
  k,strategy=name[1:].split('_'); f=Path(a.profiler)/f'K{k}_{strategy}_communication.json'
  if f.exists():
   ev=next((e for e in json.loads(f.read_text(encoding='utf-8')) if e['name']=='gloo:all_reduce'),None)
   if ev: r['profiler_count']=ev['count']; r['profiler_total_ms']=ev['cpu_total_us']/1000
 summary.append(r)
(root/'aggregate.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
with (root/'aggregate.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=summary[0].keys()); w.writeheader(); w.writerows(summary)
d={r['name']:r for r in summary}
def bars(names,metric,err,ylabel,title,file):
 rs=[d[n] for n in names]; fig,ax=plt.subplots(figsize=(7,4)); ax.bar(names,[r[metric] for r in rs],yerr=[r[err] or 0 for r in rs],capsize=4); ax.set(ylabel=ylabel,title=title); fig.tight_layout(); fig.savefig(out/file,dpi=160); plt.close(fig)
bars(['A1','A2'],'throughput_mean','throughput_std_between_repeats','Samples / second','A: mean throughput ± repeat SD','A_throughput.png')
bars(['C4_normal','C4_delayed'],'mean_update_ms','std_update_ms','Update time (ms)','B: pooled mean ± update SD','B_time.png')
fig,ax=plt.subplots(figsize=(7,4))
for strategy in ('normal','delayed'):
 rs=[d[f'C{k}_{strategy}'] for k in (1,2,4,8)]; ax.errorbar([1,2,4,8],[r['throughput_mean'] for r in rs],yerr=[r['throughput_std_between_repeats'] or 0 for r in rs],marker='o',capsize=3,label=strategy)
ax.set(xlabel='Accumulation steps K',ylabel='Samples / second',title='C: mean throughput ± repeat SD'); ax.set_xticks([1,2,4,8]); ax.legend(); fig.tight_layout(); fig.savefig(out/'C_throughput.png',dpi=160); plt.close(fig)
fig,ax=plt.subplots(figsize=(7,4))
for strategy in ('normal','delayed'):
 rows=groups[f'C4_{strategy}'][0][0]; ax.plot([int(r['update_step']) for r in rows],[float(r['loss']) for r in rows],marker='o',label=strategy)
ax.set(xlabel='Measured update',ylabel='Cross entropy',title='B loss, repeat 1 (performance run)'); ax.legend(); fig.tight_layout(); fig.savefig(out/'loss.png',dpi=160); plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(9,4)); labels=['normal','delayed']; rs=[d['C4_'+s] for s in labels]; axs[0].bar(labels,[r['profiler_count'] for r in rs]); axs[0].set(ylabel='Gloo calls / profiled update',title='Call count'); axs[1].bar(labels,[r['profiler_total_ms'] for r in rs]); axs[1].set(ylabel='Cumulative event time (ms)',title='Event time'); fig.suptitle('Independent synthetic CPU profiler, K=4'); fig.tight_layout(); fig.savefig(out/'communication.png',dpi=160); plt.close(fig)
print(json.dumps(summary,indent=2))
