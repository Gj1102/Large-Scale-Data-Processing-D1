"""Check report, data and documented paths; manual items remain visible."""
import json, re, zipfile
from pathlib import Path
from urllib.parse import unquote
from docx import Document
root = Path(__file__).resolve().parents[2]
report = root / 'report/51290713112_高洁_D1.docx'
checks = []
def add(status, message): checks.append((status, message))
try:
    doc = Document(report)
    text = '\n'.join(p.text for p in doc.paragraphs) + '\n' + '\n'.join(c.text for t in doc.tables for r in t.rows for c in r.cells)
    headings = ('研究目的','研究内容','实验环境','实验负载','实验步骤','实验结果与分析','结论','AI 使用情况','本人的修改与验证','本人独立完成的部分')
    missing = [h for h in headings if h not in text]
    add('FAIL' if missing else 'PASS', '报告章节：' + (', '.join(missing) if missing else '齐全'))
    header = '\n'.join(p.text for s in doc.sections for p in s.header.paragraphs)
    add('PASS' if '高洁' in header and '51290713112' in header else 'FAIL', '报告姓名和学号')
    rows = json.loads((root/'results/final/aggregate.json').read_text(encoding='utf-8'))
    actual = {}
    for table in doc.tables:
        for r in table.rows:
            c = [x.text for x in r.cells]
            if len(c)==4 and c[0] in ('A1','A2','B1 普通','B2 延迟'): actual[{'B1 普通':'B1','B2 延迟':'B2'}.get(c[0],c[0])] = c[1:]
            if len(c)==5 and c[0] in ('1','2','4','8') and c[1] in ('普通','延迟'): actual[f"C{c[0]}_{'normal' if c[1]=='普通' else 'delayed'}"] = c[2:]
    problems=[]
    for row in rows:
        cells=actual.get(row['name'])
        if not cells: problems.append(row['name']+' 缺失'); continue
        for val, cell in ((row['mean_update_ms'],cells[0]),(row['std_update_ms'],cells[0]),(row['p50_ms'],cells[1]),(row['p95_ms'],cells[1]),(row['throughput_mean'],cells[2]),(row['throughput_std_between_repeats'],cells[2])):
            if f'{val:.2f}' not in cell: problems.append(row['name']+' '+f'{val:.2f}')
    for b, name in (('B1','C4_normal'),('B2','C4_delayed')):
        expected=actual.get(name); found=actual.get(b)
        if not found or found != expected: problems.append(b+' 与 '+name+' 不一致')
    add('FAIL' if problems or len(rows)!=10 else 'PASS', '报告与汇总数值：' + (', '.join(problems) if problems else f'{len(rows)} 组'))
    comparison=json.loads((root/'results/comparison/comparison.json').read_text(encoding='utf-8'))
    compare_cells={}
    for table in doc.tables:
        for r in table.rows:
            c=[cell.text for cell in r.cells]
            if len(c)==3 and c[0] in {x['name'] for x in comparison}: compare_cells[c[0]]=c[1:]
    errors=[r['name'] for r in comparison if compare_cells.get(r['name'])!=[f"{r['original_throughput_mean']:.2f}",f"{r['reproduction_throughput_mean']:.2f}"]]
    add('FAIL' if len(comparison)!=10 or errors else 'PASS','两批报告对照数据：'+(', '.join(errors) if errors else '10 组一致'))
    with zipfile.ZipFile(report) as z:
        bad=z.testzip(); media=[n for n in z.namelist() if n.startswith('word/media/') and not n.endswith('/')]; empty=[n for n in media if not z.getinfo(n).file_size]
    add('PASS' if len(doc.inline_shapes)>=4 and len(media)>=4 and not bad and not empty else 'FAIL', f'图表嵌入：{len(doc.inline_shapes)} 个，媒体文件 {len(media)} 个；ZIP 错误 {bad}，空文件 {empty}；清晰度需视觉检查')
    for term in ('待插入','待填写','待本人填写','待核实','TODO'):
        if term in text: add('MANUAL', f'报告含未完成标记：{term}（{text.count(term)} 处）')
    if '截图' in text and '待插入' in text: add('MANUAL','报告保留真实运行截图占位，须本人插入')
    else: add('WARNING','未检测到截图占位；请人工核实是否已插入真实截图')
except Exception as e: add('FAIL', f'报告检查异常：{e}')
for readme in (root/'code/README.md',root.parent/'README.md'):
    if not readme.exists(): add('WARNING',f'README 不存在：{readme}'); continue
    s=readme.read_text(encoding='utf-8-sig')
    for link in re.findall(r'\]\(([^)]+)\)',s):
        if re.match(r'\w+://|#',link): continue
        target=(readme.parent/unquote(link.split('#')[0])).resolve()
        if not target.exists(): add('FAIL',f'README 链接不存在：{link}')
    add('PASS',f'已检查 Markdown 链接：{readme.name} ({readme.parent.name})')
required=[root/'results/final/aggregate.json',root/'results/final/verification_all_k.log']
required.extend([root/'results/manual_20261125_223126/terminal_user.txt',root/'results/comparison/comparison.json',root/'results/comparison/comparison.csv'])
required.extend(root/'figures/comparison'/n for n in ('architecture.png','sync_flow.png','throughput_ab.png','throughput_k.png','speedup.png','events.png','update_time.png','stages.png'))
for relative in ('code/src/train.py','code/src/launch.py','code/src/check_sampler.py',
                 'code/src/verify.py','code/src/profiler.py','code/src/analyze_repeated.py',
                 'code/scripts/run_experiments.py','code/scripts/check_report.py',
                 'code/scripts/make_report.py','code/scripts/make_pdf.py',
                 'code/configs','code/templates','code/requirements.txt',
                 'results/final','results/final_profiler',
                 'figures/final','report'):
    if not (root/relative).exists(): add('FAIL', f'README 项目路径不存在：{relative}')
add('PASS', '已检查 README 中列出的项目路径')
for relative in ('data','results/repeated','figures/repeated'):
    if not (root/relative).exists(): add('WARNING',f'可选本地数据或历史记录未包含：{relative}')
for name in ['A1','A2']+[f'C{k}_{s}' for k in (1,2,4,8) for s in ('normal','delayed')]:
    for i in range(1,4):
        required.extend(root/f'results/final/{name}_r{i}{suffix}' for suffix in ('.csv','.json','.log','_config.json'))
for k in (1,2,4,8):
    for s in ('normal','delayed'):
        required.extend(root/f'results/final_profiler/K{k}_{s}_{suffix}.json' for suffix in ('trace','communication'))
missing=[str(p.relative_to(root)) for p in required if not p.is_file() or p.stat().st_size==0]
add('FAIL' if missing else 'PASS', f'关键实验文件 {len(required)} 项：'+(', '.join(missing) if missing else '齐全且非空'))
for status, msg in checks: print(f'{status}: {msg}')
raise SystemExit(1 if any(x[0]=='FAIL' for x in checks) else 0)

