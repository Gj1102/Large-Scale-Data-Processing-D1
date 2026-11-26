"""Build the pre-submission zip and report current byte budgets."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root=Path(__file__).resolve().parents[2]
source=root/'D1_submission'/'51290713112_高洁_D1'
target=root/'D1_submission'/'51290713112_高洁_D1.zip'
def total(p): return sum(f.stat().st_size for f in p.rglob('*') if f.is_file()) if p.exists() else 0
with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=6) as z:
    for f in sorted(source.rglob('*')):
        if f.is_file(): z.write(f,f.relative_to(source.parent))
with ZipFile(target) as z:
    error=z.testzip()
    if error: raise RuntimeError(error)
size=target.stat().st_size
for label,path in [('code',source/'code'),('results',source/'results'),('profiler original',source/'results/final_profiler'),('profiler reproduction',source/'results/manual_20261125_223126_profiler'),('figures',source/'figures'),('pdf',source/'51290713112.pdf')]:
    n=path.stat().st_size if path.is_file() else total(path)
    print(label, n, f'{n/1_000_000:.2f} MB')
print('zip',size,f'{size/1_000_000:.2f} MB')
print('video budget upper bound (decimal 100 MB, before ZIP overhead)',max(0,100_000_000-size-1),f'{max(0,100_000_000-size-1)/1_000_000:.2f} MB')
print('PRE-SUBMISSION only: final video absent' if not (source/'51290713112.mp4').exists() else 'Video present: verify playback, duration and face visibility manually')
