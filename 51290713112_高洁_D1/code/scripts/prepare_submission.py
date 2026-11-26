"""Build a separate submission copy without removing project or historical data."""
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[2]
dest=root.parent/'D1_submission'
project=dest/root.name
dest.mkdir(exist_ok=True); project.mkdir(exist_ok=True)
for rel in ('code/src','code/configs','code/templates','results/final','results/final_profiler',
            'results/manual_20261125_223126','results/manual_20261125_223126_profiler',
            'results/comparison','figures/final','figures/manual_20261125_223126','figures/comparison','report'):
    source=root/rel; target=project/rel
    shutil.copytree(source,target,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.bak','*.pyc','audit_render'))
for rel in ('code/README.md','code/requirements.txt','FINAL_AUDIT.md','SUBMISSION_NOTES.md'):
    target=project/rel; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/rel,target)
scripts=('run_experiments.py','compare_runs.py','check_final.py','check_report.py','final_audit.py','check_encoding.py','make_report.py','make_pdf.py')
for name in scripts:
    target=project/'code/scripts'/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/'code/scripts'/name,target)
shutil.copy2(root.parent/'README.md',dest/'README.md')
print('Prepared:',dest)
print('MANUAL: screenshots, visual report check, PDF if required, and course submission rules.')
