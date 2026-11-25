"""Compare the report structure with the retained template and final results."""
import json
from pathlib import Path
from docx import Document

code = Path(__file__).resolve().parents[1]
root = code.parent if code.name == 'code' else code
template = Document(code / 'templates' / '51290713112_高洁_D1.docx')
report = Document(root / 'report' / 'D1实验报告.docx')
headings = ['题目名称','研究目的','研究内容','实验','实验环境','实验负载','实验步骤','实验结果与分析','结论','AI 使用情况','AI完成的工作','本人的修改与验证','本人独立完成的部分']
assert len(template.sections) == len(report.sections) == 1
assert template.sections[0]._sectPr.xml == report.sections[0]._sectPr.xml
assert template.sections[0].header._element.xml == report.sections[0].header._element.xml
assert template.sections[0].footer._element.xml == report.sections[0].footer._element.xml
for heading in headings:
    original = [p for p in template.paragraphs if p.text == heading]
    actual = [p for p in report.paragraphs if p.text == heading]
    assert len(original) == len(actual) == 1 and original[0]._p.xml == actual[0]._p.xml, heading
rows = json.loads((root / 'results/final/aggregate.json').read_text(encoding='utf-8'))
assert len(report.tables) == 1 and len(report.inline_shapes) == 4
actual = {r.cells[0].text: r.cells for r in report.tables[0].rows[1:]}
assert len(actual) == len(rows)
for row in rows:
    cells = actual[row['name']]
    assert f"{row['mean_update_ms']:.2f}" in cells[1].text
    assert f"{row['throughput_mean']:.2f}" in cells[3].text
print('PASS: template structure and report table match final data')
