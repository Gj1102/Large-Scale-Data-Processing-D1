from pathlib import Path
from docx import Document
root=Path(__file__).resolve().parents[2]
path=root/'report/51290713112_高洁_D1.docx'; doc=Document(path)
anchor=next(p for p in doc.paragraphs if p.text.strip()=='本人独立完成的部分')
p=anchor.insert_paragraph_before('本人复现的终端记录显示，已检查 PyTorch、torchvision 与 Gloo，执行采样和四种 K 的数值验证，完成 30 次训练运行及 8 次 profiler 采样，并运行统计和图表生成脚本。终端文本保存在 results/manual_20261125_223126/terminal_user.txt；上述记录是文本日志，不是运行截图。')
p.style=next(x.style for x in doc.paragraphs if x.text.startswith('本实验通过单进程'))
doc.save(path)
