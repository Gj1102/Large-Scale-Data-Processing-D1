import csv,json,math,statistics
from pathlib import Path
root=Path(__file__).resolve().parents[1]; root=root.parent if root.name=='code' else root; folder=root/'results/final'
summary=json.loads((folder/'aggregate.json').read_text(encoding='utf-8'))
assert len(summary)==10
for row in summary:
 runs=[]; times=[]
 for i in range(1,4):
  with (folder/f"{row['name']}_r{i}.csv").open(encoding='utf-8',newline='') as f: records=list(csv.DictReader(f))
  assert len(records)==4
  ts=[float(x['update_time_ms']) for x in records]; times.extend(ts)
  runs.append(sum(int(x['effective_batch']) for x in records)*1000/sum(ts))
 assert math.isclose(row['mean_update_ms'],statistics.mean(times),rel_tol=1e-12)
 assert math.isclose(row['throughput_mean'],statistics.mean(runs),rel_tol=1e-12)
print('PASS: 30 CSV files and 10 summary rows match')
