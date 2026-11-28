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
for rel in ('code/README.md','code/requirements.txt','SUBMISSION_NOTES.md'):
    target=project/rel; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/rel,target)
scripts=('run_experiments.py','compare_runs.py')
for name in scripts:
    target=project/'code/scripts'/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/'code/scripts'/name,target)
shutil.copy2(root.parent/'README.md',dest/'README.md')
# Remove only known copies of internal review and document-generation tools from
# the submission copy. Their originals and development history remain intact.
for rel in ('FINAL_AUDIT.md','code/scripts/check_final.py','code/scripts/check_report.py',
            'code/scripts/final_audit.py','code/scripts/check_encoding.py',
            'code/scripts/make_report.py','code/scripts/make_pdf.py'):
    stale=project/rel
    if stale.is_file(): stale.unlink()
print('Prepared:',dest)
print('MANUAL: screenshots, visual report check, PDF if required, and course submission rules.')
