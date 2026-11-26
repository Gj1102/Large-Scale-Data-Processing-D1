"""Update environment facts in the screenshot-equipped report only."""
from pathlib import Path
from docx import Document
path=Path(__file__).resolve().parents[1]/'report/51290713112_高洁_D1.docx'
doc=Document(path)
replacements={
 '部署方式：': '部署方式：单机多进程、1 个节点。A1 使用 1 个训练进程，A2、B、C 组使用 2 个训练进程；双进程通过 Windows spawn 启动，使用本机临时文件（file://）初始化 Gloo 进程组，进程间本机通信，不涉及跨物理节点。每进程设置 1 个 OpenMP 线程，未使用 GPU。',
 '硬件配置：': '本机硬件查询：Intel Core i7-13650HX，14 个物理核心、20 个逻辑处理器；物理内存 15.71 GiB。项目所在 D 盘位于 GAMMIX S20 NVMe SSD。2026 年 11 月 26 日查询时可用物理内存约 2.52 GiB，该值随负载变化，不能代表历史实验运行时的可用内存。上述 CPU 逻辑核数和内存容量与已有实验环境记录一致。',
 '软件环境：': '软件环境：Windows 11 家庭版中文版 64 位（版本 10.0.26300），Python 3.11.18，PyTorch 2.15.0+cpu，torchvision 0.29.2+cpu，Gloo，Conda 环境 ddp-lab。实验不涉及 Java，无需 JDK。'
}
for prefix,text in replacements.items():
    matches=[p for p in doc.paragraphs if p.text.startswith(prefix)]
    if len(matches)!=1: raise ValueError(f'{prefix}: {len(matches)}')
    p=matches[0]; p.runs[0].text=text
    for r in p.runs[1:]: r.text=''
doc.save(path)
