from pathlib import Path
import fitz
from docx import Document
root=Path(__file__).resolve().parents[1]; root=root.parent if root.name == 'code' else root; doc=Document(root/'report/D1实验报告.docx'); pdf=fitz.open(); page=None; y=0

def newline(text, size=10):
 global page,y
 text=text.replace('\t',' ')
 while text:
  part,text=text[:52],text[52:]
  if page is None or y>795: page=pdf.new_page(width=595,height=842); y=48
  page.insert_text((45,y),part,fontname='china-s',fontsize=size); y+=16
for p in doc.paragraphs:
 if p.text.strip():
  for line in p.text.splitlines(): newline(line,12 if p.style.name.startswith(('Heading','Title')) else 10)
  y+=4
for table in doc.tables:
 newline('实验结果汇总',12)
 for row in table.rows:
  newline('  '.join(c.text for c in row.cells),9)
for name in ['A_throughput.png','B_time.png','C_throughput.png','communication.png','loss.png']:
 page=pdf.new_page(width=595,height=842); page.insert_text((45,50),name,fontname='helv',fontsize=12); page.insert_image(fitz.Rect(45,80,550,390),filename=str(root/'figures/repeated'/name),keep_proportion=True)
pdf.save(root/'report/D1实验报告.pdf')
