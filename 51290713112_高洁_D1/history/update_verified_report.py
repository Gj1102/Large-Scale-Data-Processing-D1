from copy import deepcopy
from pathlib import Path
from docx import Document
from docx.text.paragraph import Paragraph

root = Path('51290713112_高洁_D1')
source = root/'report/51290713112_高洁_D1.docx'
doc = Document(source)
paragraphs = doc.paragraphs

def insert_after(paragraph, text, prototype):
    element = deepcopy(prototype._p)
    paragraph._p.addnext(element)
    result = Paragraph(element, paragraph._parent)
    if result.runs:
        result.runs[0].text = text
        for run in result.runs[1:]:
            run._element.getparent().remove(run._element)
    else:
        result.add_run(text)
    return result

insert_after(paragraphs[20], '图：A1/A2 全局样本集合一致性验证【待插入真实运行截图】', paragraphs[19])
insert_after(paragraphs[52], '图：K=1、2、4、8 数值正确性验证【待插入真实运行截图】', paragraphs[52])
insert_after(paragraphs[52], '采样检查显示，前三个 Epoch 中 A1 与 A2 每个完整参数更新批次的全局样本集合一致。四个 K 值下，同样样本的单进程参考与 DDP 的参数最大误差均为 1.1920929e-07。', paragraphs[52])
insert_after(paragraphs[54], '对固定输入的验证表明，K=1、2、4、8 时普通同步与延迟同步的梯度和更新参数在测试容差内一致，各 Rank 的参数最大误差为 0。', paragraphs[54])
table = doc.tables[5]
assert [row.cells[0].text for row in table.rows] == ['K', '1', '2', '4', '8']
values = [('0','0','0','1.1920929e-07'),('1.1920929e-07','1.49011612e-08','0','1.1920929e-07')]
for i, row in enumerate(table.rows[1:]):
    for cell, value in zip(row.cells[1:], values[0 if i==0 else 1]):
        p = cell.paragraphs[0]
        if p.runs:
            p.runs[0].text = value
            for run in p.runs[1:]: run.text = ''
        else: p.add_run(value)
doc.save(source)
doc.save(root/'report/D1实验报告.docx')
print('Updated',source)
