"""Remove duplicated prose while retaining template, evidence and figures."""
from pathlib import Path
from docx import Document

path=Path(__file__).resolve().parents[1]/'report/51290713112_高洁_D1.docx'
doc=Document(path)
prefixes=('DDP 在每个进程中维护一份模型副本',
          '复现实验记录', '另一次运行使用 PyTorch', '采样检查通过：A1 与 A2',
          '复现实验的 A1 和 A2', '复现的独立 profiler 中',
          '对固定输入的验证表明，K=1、2、4、8',
          '增大 K 并不意味着一定更好')
for prefix in prefixes:
    matches=[p for p in doc.paragraphs if p.text.startswith(prefix)]
    if len(matches)!=1: raise ValueError(f'{prefix}: {len(matches)}')
    el=matches[0]._element; el.getparent().remove(el)
labels={'图 5  实验系统与数据处理流程':'图 1  实验系统与数据处理流程',
        '图 6  K=4 时普通同步与延迟同步的执行流程':'图 2  K=4 时普通同步与延迟同步的执行流程',
        '图 6 描述的是同步反向传播的轮数':'图 2 描述的是同步反向传播的轮数',
        '图 1  单进程与双进程吞吐量':'图 3  单进程与双进程吞吐量',
        '图 2  两种同步策略的更新耗时':'图 4  两种同步策略的更新耗时',
        '图 3  不同梯度累积步数的吞吐量':'图 5  不同梯度累积步数的吞吐量',
        '图 4  K=4 普通同步与延迟同步的独立通信采样':'图 6  K=4 普通同步与延迟同步的独立通信采样'}
paras=list(doc.paragraphs)+[p for t in doc.tables for row in t.rows for cell in row.cells for p in cell.paragraphs]
for old,new in labels.items():
    matches=[p for p in paras if old in p.text]
    if len(matches)!=1: raise ValueError(f'caption {old}: {len(matches)}')
    p=matches[0]
    if len(p.runs)==1 and old in p.runs[0].text:
        p.runs[0].text=p.runs[0].text.replace(old,new)
    elif old.startswith('图 ') and len(p.runs)>1 and p.runs[0].text=='图':
        p.runs[1].text=p.runs[1].text.replace(old.split()[1],new.split()[1],1)
    else:
        raise ValueError(f'caption runs: {old}')
doc.save(path)
