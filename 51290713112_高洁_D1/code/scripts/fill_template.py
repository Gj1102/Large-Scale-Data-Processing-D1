from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
import json
root=Path(__file__).resolve().parents[1]; root=root.parent if root.name=='code' else root; data=root/'results/final'; figs=root/'figures/final'
rows=json.loads((data/'aggregate.json').read_text(encoding='utf-8')); d={r['name']:r for r in rows}
template=next(root.parent.parent.glob('51290713112*.docx')); doc=Document(template); ps=doc.paragraphs
ps[0].insert_paragraph_before('') if False else None
# Preserve the headings, template section properties, headers, footers and styles.
def after(p,text):
 node=OxmlElement('w:p'); p._p.addnext(node); q=Paragraph(node,p._parent); q.style=doc.styles['Normal']; q.add_run(text); return q
def fill(p,text):
 p.clear(); p.add_run(text)
a1,a2=d['A1'],d['A2']; n,l=d['C4_normal'],d['C4_delayed']
after(ps[0],'D1 分布式环境中的数据并行与同步开销')
fill(ps[2],'探究分布式数据并行训练中并行计算收益与梯度同步开销之间的关系，分析数据并行训练的适用条件。')
fill(ps[4],'必做主线：比较单进程训练与双进程 DDP，理解全局批大小、局部批大小与梯度同步的关系。所选方向③：研究梯度累积与延迟同步对通信开销的影响。')
fill(ps[7],'单机 Windows，单进程或两个 CPU 进程，DDP 使用 Gloo 与 file:// 初始化；每进程 OMP_NUM_THREADS=1。')
fill(ps[8],'节点数 1，逻辑 CPU 20，内存 15.71 GiB；单机本地进程通信。物理核心、存储类型等未核实。')
fill(ps[9],'Windows 10，Python 3.11.18，PyTorch 2.15.0+cpu，torchvision 0.29.2+cpu。')
fill(ps[11],'CIFAR-10：训练集 50000 张、测试集 10000 张，32×32 RGB、10 类；通过 torchvision 下载。模型为 GroupNorm ResNet-18，FP32，SGD 学习率 0.01、动量 0.9，seed 42。固定更新数时 K=1/2/4/8 的有效批为 32/64/128/256。')
fill(ps[13],'在 D1-DDP 目录执行：$env:PYTHONUTF8="1"; $env:OMP_NUM_THREADS="1"。使用 ddp-lab 的 Python 运行 scripts/run_experiments.py --steps 4 --warmup 2 --repeats 3 --output results/final；运行 src/profiler.py --k K --strategy normal 或 delayed --output results/final_profiler，K 取 1、2、4、8；运行 src/analyze_repeated.py --input results/final --profiler results/final_profiler --output figures/final。详细命令见 README。')
fill(ps[14],'【待本人插入真实截图】环境、双进程运行、验证输出、Profiler 输出；可使用 README 中对应命令。不得以图表代替运行过程截图。')
fill(ps[16],f'本次固定每轮 4 次测量更新、预热 2 次、重复 3 轮，缩减自建议的 20/200/3：CPU 耗时较高。A1/A2 全局批 128，使用同一随机排列的相同每步样本集合；每 rank 的样本顺序不同。A1 平均吞吐 {a1["throughput_mean"]:.2f}，A2 {a2["throughput_mean"]:.2f} 样本/秒。B1/B2 是 C4 normal/delayed：分别为 {n["throughput_mean"]:.2f}、{l["throughput_mean"]:.2f} 样本/秒，吞吐比 {l["throughput_mean"]/n["throughput_mean"]:.2f}。')
p=after(ps[16], '?1 ????????????????????????????????')
table=doc.add_table(rows=1, cols=4); table.style='Table Grid'; p._p.addnext(table._tbl)
for cell, value in zip(table.rows[0].cells, ('??','?? ms ?? ? ???','P50 / P95 ms','??? ?? ? ???')): cell.text=value
for row in rows:
 cells=table.add_row().cells
 for cell, value in zip(cells, (row['name'], f"{row['mean_update_ms']:.2f} ? {row['std_update_ms']:.2f}", f"{row['p50_ms']:.2f} / {row['p95_ms']:.2f}", f"{row['throughput_mean']:.2f} ? {row['throughput_std_between_repeats']:.2f}")): cell.text=value
node=OxmlElement('w:p'); table._tbl.addnext(node); p=Paragraph(node,ps[16]._parent); p.add_run('????????????????? Rank 0 ???????? aggregate.csv?')
for k in (1,2,4,8):
 x=d[f'C{k}_normal']; y=d[f'C{k}_delayed']; p=after(p,f'K={k}：普通/延迟同步吞吐 {x["throughput_mean"]:.2f}/{y["throughput_mean"]:.2f} 样本/秒；平均更新耗时 {x["mean_update_ms"]:.2f}/{y["mean_update_ms"]:.2f} ms；每更新梯度同步反向次数 {k}/1。')
p=after(p,'DDP 反向传播按桶归约梯度，loss 除以 K，累积 K 个微批后更新一次；no_sync 覆盖前 K−1 次前向及反向。每步额外执行的 Loss 和计时 all-reduce 不计入梯度通信事件。独立 profiler 只捕获梯度反向段，使用合成微批 1、单更新和 Rank 0；桶重建会影响事件数，累计事件时间不等于端到端额外通信开销。不能用 A2 与 A1 耗时之差推算通信成本。')
p=after(p,'数值验证 K=1、2、4、8 均通过；单进程参考参数最大误差 1.1920929e-7，Rank 间误差为 0。分阶段计时为 Rank 0 测量，反向含同步；不将其与跨 Rank 最大更新耗时直接相加。计算通信重叠未可靠量化。')
for name,caption in [('A_throughput.png','图1 单进程与双进程吞吐量'),('B_time.png','图2 K=4 两种同步策略更新耗时'),('C_throughput.png','图3 累积步数与吞吐量'),('communication.png','图4 独立合成负载通信事件')]:
 p=after(p,''); p.add_run().add_picture(str(figs/name),width=Inches(5.5)); p=after(p,caption)
fill(ps[18],'本机 CPU/Gloo 的并行收益取决于计算量、进程调度和同步开销。延迟同步减少梯度同步频率，可在通信占比较大时改善吞吐，但收益依赖模型与环境。本次测量较短，不能推断长期稳定性；不同 K 改变有效批与处理样本数，Loss 差异不能直接归因于同步策略。未测 GPU/NCCL 和可靠的计算通信重叠。课程题目及验收 PDF 尚待核对。')
fill(ps[20],'使用 OpenAI Codex 辅助。')
fill(ps[22],'Codex 参与代码检查与修改、采样对齐、阶段计时、实验运行与统计、绘图、报告整理；具体见训练代码、实验脚本和结果目录。')
fill(ps[24],'【待本人补充：本人实际执行的检查、修改和验证】')
fill(ps[26],'【待本人补充：本人独立完成的具体工作】')
out=root/'report'/'D1实验报告.docx'; doc.save(out); print(out)
