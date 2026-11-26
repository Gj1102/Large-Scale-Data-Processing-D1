"""Validate and compare two recorded experiments, without changing their inputs."""
import csv, json, math, statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BATCHES = [('Original', ROOT/'results/final', ROOT/'results/final_profiler'),
           ('Reproduction', ROOT/'results/manual_20261125_223126', ROOT/'results/manual_20261125_223126_profiler')]
NAMES = ['A1','A2']+[f'C{k}_{s}' for k in (1,2,4,8) for s in ('normal','delayed')]
figdir=ROOT/'figures/comparison'; outdir=ROOT/'results/comparison'
figdir.mkdir(parents=True,exist_ok=True); outdir.mkdir(parents=True,exist_ok=True)
summaries={}; configs={}; communication={}
for label, folder, profiler in BATCHES:
    rows=json.loads((folder/'aggregate.json').read_text(encoding='utf-8'))
    summary={r['name']:r for r in rows}
    if len(rows)!=10 or set(summary)!=set(NAMES): raise ValueError(f'{label}: bad configurations')
    with (folder/'aggregate.csv').open(encoding='utf-8-sig',newline='') as f: aggregate_csv={r['name']:r for r in csv.DictReader(f)}
    if set(aggregate_csv)!=set(NAMES): raise ValueError(f'{label}: aggregate CSV configurations')
    if len(list(folder.glob('*_r[123].csv')))!=30: raise ValueError(f'{label}: expected 30 CSV files')
    for name in NAMES:
        times=[]; throughputs=[]
        for i in range(1,4):
            stem=f'{name}_r{i}'
            for suffix in ('.csv','.json','.log','_config.json'):
                p=folder/(stem+suffix)
                if not p.is_file() or not p.stat().st_size: raise ValueError(f'missing {p}')
            with (folder/(stem+'.csv')).open(encoding='utf-8-sig',newline='') as f: records=list(csv.DictReader(f))
            if len(records)!=4: raise ValueError(f'{stem}: expected four measured updates')
            t=[float(r['update_time_ms']) for r in records]; times.extend(t)
            throughput=sum(int(r['effective_batch']) for r in records)*1000/sum(t)
            throughputs.append(throughput)
            run_summary=json.loads((folder/(stem+'.json')).read_text(encoding='utf-8-sig'))
            if run_summary['updates']!=len(records) or not math.isclose(run_summary['mean_ms'],statistics.mean(t),rel_tol=1e-6) or not math.isclose(run_summary['throughput'],throughput,rel_tol=1e-10): raise ValueError(f'{stem}: per-run summary mismatch')
            cfg=json.loads((folder/(stem+'_config.json')).read_text(encoding='utf-8-sig'))
            command=cfg['command']; options={command[j]:command[j+1] for j in range(len(command)-1) if command[j] in ('--batch','--accum-steps','--strategy','--warmup','--steps','--seed')}
            signature=(Path(command[1]).name,tuple(sorted(options.items())),cfg['samples_measured'],cfg['measurement_mode'],cfg['warmup_updates'],cfg['repeat'])
            configs[label,stem]=signature
            if 'update 4:' not in (folder/(stem+'.log')).read_text(encoding='utf-8-sig'): raise ValueError(f'{stem}: incomplete log')
            expected={'world_size':1 if name=='A1' else 2,'micro_batch':int(options['--batch']),'accum_steps':int(options['--accum-steps'])}
            for record in records:
                if any(int(record[k])!=v for k,v in expected.items()) or record['sync_strategy']!=options['--strategy'] or int(record['effective_batch'])!=math.prod(expected.values()): raise ValueError(f'{stem}: CSV/config mismatch')
        for key,value in [('mean_update_ms',statistics.mean(times)),('std_update_ms',statistics.stdev(times)),('throughput_mean',statistics.mean(throughputs)),('throughput_std_between_repeats',statistics.stdev(throughputs))]:
            if not math.isclose(summary[name][key],value,rel_tol=1e-10) or not math.isclose(float(aggregate_csv[name][key]),value,rel_tol=1e-10): raise ValueError(f'{label} {name}: bad {key}')
    for k in (1,2,4,8):
        for strategy in ('normal','delayed'):
            stem=f'K{k}_{strategy}'; cp=profiler/(stem+'_communication.json'); tp=profiler/(stem+'_trace.json')
            for p in (cp,tp):
                if not p.is_file() or not p.stat().st_size: raise ValueError(f'missing {p}')
            events=json.loads(cp.read_text(encoding='utf-8')); trace=json.loads(tp.read_text(encoding='utf-8'))
            event=next(x for x in events if x['name']=='gloo:all_reduce')
            trace_count=sum(1 for e in trace.get('traceEvents',[]) if e.get('name')=='gloo:all_reduce' and e.get('ph')=='X')
            if trace_count!=event['count']: raise ValueError(f'{label} {stem}: trace {trace_count} != aggregate {event["count"]}')
            communication[label,k,strategy]=event['count']
    for name in NAMES:
        for key,value in summary[name].items():
            if isinstance(value,(int,float)) and value is not None:
                if not math.isclose(float(aggregate_csv[name][key]),value,rel_tol=1e-10,abs_tol=1e-12): raise ValueError(f'{label} {name}: aggregate CSV/JSON {key}')
    summaries[label]=summary
for name in NAMES:
    for i in range(1,4):
        stem=f'{name}_r{i}'
        if configs['Original',stem]!=configs['Reproduction',stem]: raise ValueError(f'{stem}: configuration differs')

comparison=[]
for name in NAMES:
    x,y=(summaries[b][name] for b in ('Original','Reproduction'))
    comparison.append({'name':name, **{f'{b}_{key}':row.get(key) for b,row in (('original',x),('reproduction',y)) for key in ('throughput_mean','throughput_std_between_repeats','mean_update_ms','std_update_ms','speedup_vs_normal')}})
(outdir/'comparison.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
with (outdir/'comparison.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=comparison[0].keys()); w.writeheader(); w.writerows(comparison)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
colors=['#235789','#e68a2e']; batches=['Original','Reproduction']
def save(fig,name): fig.tight_layout(); fig.savefig(figdir/name,dpi=200,bbox_inches='tight'); plt.close(fig)
names=['A1','A2','C4_normal','C4_delayed']; x=np.arange(4); fig,ax=plt.subplots(figsize=(7.5,4))
for i,b in enumerate(batches):
    rs=[summaries[b][n] for n in names]; ax.bar(x+(i-.5)*.36,[r['throughput_mean'] for r in rs],.36,yerr=[r['throughput_std_between_repeats'] for r in rs],capsize=3,label=b,color=colors[i])
ax.set_xticks(x,['A1','A2','B1 normal','B2 delayed']); ax.set_ylabel('Throughput (samples/s)'); ax.legend(); ax.set_title('Two runs: throughput (mean ± repeat SD)'); save(fig,'throughput_ab.png')
fig,ax=plt.subplots(figsize=(7.5,4)); ks=[1,2,4,8]
for i,b in enumerate(batches):
    for s,ls in [('normal','--'),('delayed','-')]:
        rs=[summaries[b][f'C{k}_{s}'] for k in ks]; ax.errorbar(ks,[r['throughput_mean'] for r in rs],yerr=[r['throughput_std_between_repeats'] for r in rs],marker='o',capsize=3,ls=ls,color=colors[i],label=f'{b} {s}')
ax.set(xticks=ks,xlabel='Accumulation steps K',ylabel='Throughput (samples/s)',title='Throughput (mean ± repeat SD)'); ax.legend(fontsize=8); save(fig,'throughput_k.png')
fig,ax=plt.subplots(figsize=(7,4))
for i,b in enumerate(batches): ax.plot(ks,[summaries[b][f'C{k}_delayed']['speedup_vs_normal'] for k in ks],marker='o',label=b,color=colors[i])
ax.axhline(1,color='gray',lw=.8); ax.set(xticks=ks,xlabel='Accumulation steps K',ylabel='Delayed / normal throughput',title='Delayed synchronization speedup'); ax.legend(); save(fig,'speedup.png')
fig,ax=plt.subplots(figsize=(7,4))
for i,(b,s) in enumerate([(b,s) for b in batches for s in ('normal','delayed')]): ax.plot(ks,[communication[b,k,s] for k in ks],marker='o',ls='--' if s=='normal' else '-',color=colors[batches.index(b)],label=f'{b} {s}')
ax.set(xticks=ks,xlabel='Accumulation steps K',ylabel='Gloo All-Reduce events',title='Independent synthetic profiler'); ax.legend(fontsize=8); save(fig,'events.png')
fig,ax=plt.subplots(figsize=(9,4)); x=np.arange(len(NAMES))
for i,b in enumerate(batches):
    rs=[summaries[b][n] for n in NAMES]; ax.bar(x+(i-.5)*.36,[r['mean_update_ms'] for r in rs],.36,yerr=[r['std_update_ms'] for r in rs],capsize=2,label=b,color=colors[i])
ax.set_xticks(x,[n.replace('_normal',' N').replace('_delayed',' D') for n in NAMES],rotation=35,ha='right'); ax.set(ylabel='Update time (ms)',title='Update time (mean ± update SD)'); ax.legend(); save(fig,'update_time.png')
fig,ax=plt.subplots(figsize=(8,4)); labels=[f'{b} {s}' for b in batches for s in ('normal','delayed')]; pos=np.arange(4); bottom=np.zeros(4)
for key,label,color in [('forward_mean_ms','Forward × K','#4e79a7'),('backward_mean_ms','Backward incl. sync × K','#f28e2b'),('optimizer_ms','Optimizer','#59a14f')]:
    vals=[summaries[b][f'C4_{s}'][key]*(4 if key!='optimizer_ms' else 1) for b in batches for s in ('normal','delayed')]; ax.bar(pos,vals,bottom=bottom,label=label,color=color); bottom+=np.array(vals)
ax.set_xticks(pos,labels,rotation=15); ax.set(ylabel='Rank 0 stage time per update (ms)',title='K=4 stage time; not max-rank total'); ax.legend(fontsize=8); save(fig,'stages.png')
print('PASS: 2 batches, 60 runs, 16 profiler captures, summaries, configurations and trace event counts')
print('Measurement note: short runs use the same seed; stage timing is Rank 0 and backward includes synchronization')
