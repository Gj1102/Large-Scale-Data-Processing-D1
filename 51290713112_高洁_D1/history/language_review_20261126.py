"""Revise selected prose without altering embedded evidence or results."""
from pathlib import Path
from docx import Document

path=Path(__file__).resolve().parents[1]/'report/51290713112_高洁_D1.docx'
doc=Document(path)
changes={
    '资源使用方面，A1 运行一个训练进程': 'A2 的两个进程各持有模型和优化器状态，并通过 Gloo 交换梯度。本实验未实测 CPU 利用率或内存峰值，因此不对这些资源的实际用量作定量比较。',
    'ChatGPT 用于梳理 DDP 梯度同步': 'ChatGPT 用于学习 DDP 梯度同步、梯度累积和 no_sync() 的原理，辅助讨论对照实验设计，并检查和整理实验分析与报告。Codex 辅助编写与调试 train.py、launch.py、verify.py、check_sampler.py 和 profiler.py，完善实验运行与统计脚本，并根据两批实际实验数据生成图表和复现对照分析。',
    '本人在 Windows 的 ddp-lab 环境中': '我在 Windows 的 ddp-lab 环境中设置 UTF-8 编码及线程参数，检查 Python、PyTorch、torchvision 和 Gloo，并运行采样一致性检查、K=1、2、4、8 数值验证及 A/B/C 组实验。我结合实际输出检查实验配置、梯度和参数误差、Rank 间一致性、更新耗时与吞吐量，并通过独立 profiler 采集通信事件。',
    '本人复现共完成 30 次训练运行': '复现实验完成了 30 次训练运行和 8 次独立通信采样，并执行了统计和图表生成脚本。实验过程见运行截图 1—7，完整终端记录见 results/manual_20261125_223126/terminal_user.txt。',
    '本人独立完成的部分为本机终端': '我独立完成了本机终端操作、实验截图采集和运行记录保存。实验方案、代码实现、调试、结果分析和报告整理均有 AI 辅助，这些工作不作为完全独立完成的部分。',
}
for prefix,text in changes.items():
    hits=[p for p in doc.paragraphs if p.text.startswith(prefix)]
    if len(hits)!=1: raise ValueError(f'{prefix}: {len(hits)}')
    p=hits[0]
    if not p.runs: p.add_run(text)
    else:
        p.runs[0].text=text
        for run in p.runs[1:]: run.text=''
doc.save(path)
