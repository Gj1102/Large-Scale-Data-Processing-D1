"""Check the current report against the recorded final experiment summary."""
import argparse
import json
from pathlib import Path
from docx import Document

code = Path(__file__).resolve().parents[1]
root = code.parent
parser = argparse.ArgumentParser()
parser.add_argument('--report', type=Path, default=root / 'report' / '51290713112_高洁_D1.docx')
args = parser.parse_args()
doc = Document(args.report)
rows = json.loads((root / 'results/final/aggregate.json').read_text(encoding='utf-8'))
text = '\n'.join(p.text for p in doc.paragraphs)
for heading in ('研究目的', '研究内容', '实验环境', '实验负载', '实验步骤', '实验结果与分析', '结论', 'AI 使用情况'):
    assert heading in text, f'缺少章节：{heading}'
header = doc.sections[0].header.paragraphs[0].text
assert '姓名：高洁' in header and '51290713112' in header
actual = {}
for table in doc.tables:
    for table_row in table.rows:
        cells = [cell.text for cell in table_row.cells]
        if len(cells) == 4 and cells[0] in ('A1', 'A2'):
            actual[cells[0]] = (cells[1], cells[2], cells[3])
        if len(cells) == 5 and cells[0] in ('1', '2', '4', '8') and cells[1] in ('普通', '延迟'):
            strategy = 'normal' if cells[1] == '普通' else 'delayed'
            actual[f'C{cells[0]}_{strategy}'] = (cells[2], cells[3], cells[4])
for row in rows:
    assert row['name'] in actual, f"缺少实验组：{row['name']}"
    mean, percentiles, throughput = actual[row['name']]
    for value, cell in ((row['mean_update_ms'], mean), (row['std_update_ms'], mean),
                        (row['p50_ms'], percentiles), (row['p95_ms'], percentiles),
                        (row['throughput_mean'], throughput), (row['throughput_std_between_repeats'], throughput)):
        assert f'{value:.2f}' in cell, f"{row['name']} 数据不一致：{value:.2f}"
assert len(doc.inline_shapes) >= 4
print(f'PASS: report sections, identity, figures and {len(rows)} groups of aggregate values')
