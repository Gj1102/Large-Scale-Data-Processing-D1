"""Revise the template-based report using the existing recorded results."""
from pathlib import Path
from docx import Document
from docx.shared import Pt

root = Path(__file__).resolve().parents[2]
path = root / 'report/51290713112_高洁_D1.docx'
doc = Document(path)

def insert_before(prefix, text):
    matches = [p for p in doc.paragraphs if p.text.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f'expected one paragraph beginning {prefix!r}, got {len(matches)}')
    p = matches[0].insert_paragraph_before(text)
    p.style = matches[0].style
    return p

insert_before('表 1  对照实验配置', 'DDP 在每个进程中维护一份模型副本，各进程处理不同的数据分片，反向传播时按梯度桶执行 All-Reduce。设进程数为 P、每进程微批大小为 b、累积步数为 K，则每次参数更新的有效全局批大小为 P × b × K。每个微批的损失除以 K 后再反向传播，使累积梯度对应这批样本的平均梯度。')
insert_before('表 1  对照实验配置', '资源使用方面，A1 运行一个训练进程，A2 运行两个训练进程；每个进程使用一个 OpenMP 线程。A2 的进程各持有模型和优化器状态，并通过本机 Gloo 通信。本实验未实测 CPU 利用率或内存峰值，因此不对实际资源用量作定量比较。')
insert_before('延迟同步适用于', '增大 K 并不意味着一定更好：它同时改变有效批大小和参数更新频率，可能影响梯度噪声与训练收敛。选择 K 时还需考虑模型、硬件互联、学习率和目标训练效果；本实验的短时吞吐量结果不能单独决定长期训练配置。')

heading = doc.add_paragraph('参考资料')
heading.style = doc.paragraphs[1].style
for text in (
    '[1] PyTorch. DistributedDataParallel. https://pytorch.org/docs/stable/generated/torch.nn.parallel.DistributedDataParallel.html',
    '[2] PyTorch. Distributed communication package. https://pytorch.org/docs/stable/distributed.html',
    '[3] Krizhevsky, A. Learning Multiple Layers of Features from Tiny Images. University of Toronto, 2009.',
):
    doc.add_paragraph(text)
doc.save(path)
