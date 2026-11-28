"""Add the user's separate reproduction results without changing historical data."""
import json
from pathlib import Path
from docx import Document

root = Path(__file__).resolve().parents[2]
folder = root / 'results/manual_20261125_223126'
rows = {x['name']: x for x in json.loads((folder / 'aggregate.json').read_text(encoding='utf-8'))}
path = root / 'report/51290713112_高洁_D1.docx'
doc = Document(path)
anchor = next(p for p in doc.paragraphs if p.text.strip() == '结论')
texts = [
    '复现实验记录',
    '另一次运行使用 PyTorch 2.15.0+cpu、torchvision 0.29.2+cpu 和 Gloo。按原实验配置，每组预热 2 次、测量 4 次更新，重复 3 轮；10 组共 30 次运行完成。结果与本报告前述 results/final 数据分开记录，不替换原实验统计。',
    '采样检查通过：A1 与 A2 在前三个 epoch 的每个完整更新批次中使用相同的全局样本集合。K=1、2、4、8 的普通同步和延迟同步验证均通过；K=1 的梯度和参数误差均为 0，K=2、4、8 的最大梯度误差为 1.1920929e-07、最大参数误差为 1.49011612e-08，各 Rank 参数误差为 0；单进程参考与 DDP 的最大参数误差为 1.1920929e-07。',
    f"复现实验的 A1 和 A2 平均吞吐量分别为 {rows['A1']['throughput_mean']:.2f} 和 {rows['A2']['throughput_mean']:.2f} 样本/秒；A2 仍低于 A1。K=4 时，普通同步和延迟同步分别为 {rows['C4_normal']['throughput_mean']:.2f} 和 {rows['C4_delayed']['throughput_mean']:.2f} 样本/秒，延迟同步约为普通同步的 {rows['C4_delayed']['speedup_vs_normal']:.2f} 倍。该结果与前述实验的方向一致，但两次运行的吞吐量数值并不相同。",
    '复现的独立 profiler 中，K=4 的 Gloo All-Reduce 事件数分别为普通同步 10 次、延迟同步 1 次。该计数来自合成输入下的独立采样，可能受梯度桶重建影响；事件累计时间不能视为正式训练的端到端通信开销。',
    '复现实验训练记录和汇总位于 results/manual_20261125_223126，通信采样位于 results/manual_20261125_223126_profiler，图表位于 figures/manual_20261125_223126；用户提供的终端输出保存在对应训练结果目录中。',
]
for i, text in enumerate(texts):
    p = anchor.insert_paragraph_before(text)
    p.style = doc.paragraphs[[x.text.strip() for x in doc.paragraphs].index('实验结果与分析')].style if i == 0 else next(x.style for x in doc.paragraphs if x.text.startswith('本实验通过单进程'))
doc.save(path)
