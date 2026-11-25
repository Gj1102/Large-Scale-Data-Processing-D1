"""Export the completed DOCX through Word or LibreOffice without redrawing it."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import tempfile

code = Path(__file__).resolve().parents[1]
root = code.parent if code.name == 'code' else code
parser = argparse.ArgumentParser()
parser.add_argument('--docx', type=Path, default=root / 'report' / 'D1实验报告.docx')
parser.add_argument('--output', type=Path, default=root / 'report' / 'D1实验报告.pdf')
args = parser.parse_args()
source = args.docx.resolve()
if not source.is_file():
    raise SystemExit(f'DOCX not found: {source}')
with tempfile.TemporaryDirectory(prefix='d1-pdf-') as tmp:
    tmp_path = Path(tmp)
    rendered = tmp_path / (source.stem + '.pdf')
    office = shutil.which('soffice') or shutil.which('libreoffice')
    if office:
        proc = subprocess.run([office, '--headless', '--convert-to', 'pdf', '--outdir', str(tmp_path), str(source)], capture_output=True, text=True)
    elif os.name == 'nt':
        env = os.environ.copy()
        env['D1_DOCX_SOURCE'] = str(source)
        env['D1_PDF_OUTPUT'] = str(rendered)
        command = "$ErrorActionPreference='Stop'; $w=$null; $d=$null; try { $w=New-Object -ComObject Word.Application; $w.Visible=$false; $d=$w.Documents.Open($env:D1_DOCX_SOURCE,$false,$true); $d.ExportAsFixedFormat($env:D1_PDF_OUTPUT,17) } finally { if ($d) {$d.Close(0)}; if ($w) {$w.Quit()} }"
        proc = subprocess.run(['powershell', '-NoProfile', '-Command', command], env=env, capture_output=True, text=True, errors='replace')
    else:
        raise SystemExit('未找到 Word 或 LibreOffice；请使用文字处理软件将 DOCX 导出为 PDF。')
    if proc.returncode or not rendered.is_file():
        raise SystemExit(f'Word/LibreOffice 导出失败，请手动导出 DOCX。\n{proc.stderr or proc.stdout}')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(rendered, args.output)
    print(f'PDF: {args.output.resolve()}')
