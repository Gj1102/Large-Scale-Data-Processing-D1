"""Copy user-supplied personal-work statements into the template report."""
from pathlib import Path
from docx import Document

root = Path(__file__).resolve().parents[2]
source = Path.home() / 'Desktop' / '51290713112_高洁_D1_补全个人工作说明.docx'
target = root / 'report' / '51290713112_高洁_D1.docx'
src, dst = Document(source), Document(target)
for heading in ('本人的修改与验证', '本人独立完成的部分'):
    def following(doc):
        hits = [i for i, p in enumerate(doc.paragraphs) if p.text.strip() == heading]
        if len(hits) != 1 or hits[0] + 1 >= len(doc.paragraphs):
            raise ValueError(f'Cannot uniquely locate {heading}')
        return doc.paragraphs[hits[0] + 1]
    source_paragraph, target_paragraph = following(src), following(dst)
    if not source_paragraph.text.strip():
        raise ValueError(f'Empty statement: {heading}')
    if not target_paragraph.text.startswith('【待本人填写'):
        raise ValueError(f'Target is not the expected placeholder: {heading}')
    if target_paragraph.runs:
        target_paragraph.runs[0].text = source_paragraph.text
        for run in target_paragraph.runs[1:]:
            run.text = ''
    else:
        target_paragraph.add_run(source_paragraph.text)
dst.save(target)
print('Imported both personal statements.')
