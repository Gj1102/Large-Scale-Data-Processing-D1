from pathlib import Path
import fitz
from docx import Document
root=Path(__file__).resolve().parents[1]; root=root.parent if root.name == 'code' else root; p=root/'report'; d=Document(p/'D1实验报告.docx'); f=fitz.open(p/'D1实验报告.pdf'); txt=''.join(page.get_text().replace(' ','').replace('\n','') for page in f); word=''.join(x.text for x in d.paragraphs)+''.join(c.text for t in d.tables for r in t.rows for c in r.cells)
for x in ['55.4','56.7','54.6','132.2','134.9','140.5','203.3','174.0','3165.4','738.4']:
 print(x,'docx=',x in word,'pdf=',x in txt)
print('pdf pages',len(f))
