from pathlib import Path
import argparse
import json
import re
from copy import deepcopy
from docx import Document
from docx.shared import Inches
from docx.text.paragraph import Paragraph

code = Path(__file__).resolve().parents[1]
root = code.parent if code.name == 'code' else code
parser = argparse.ArgumentParser()
parser.add_argument('--template', type=Path, default=code / 'templates' / '51290713112_高洁_D1.docx')
args = parser.parse_args()
template_path = args.template
if not template_path.is_file():
    raise SystemExit(f'模板不存在: {template_path}')
rows = json.loads((root / 'results/final/aggregate.json').read_text(encoding='utf-8'))
d = {r['name']: r for r in rows}
verification = (root / 'results/final/verification_all_k.log').read_text(encoding='utf-8-sig')
checks = re.findall(r'K=(\d+) PASS gradient max error=([^;]+); parameter max error=([^;]+); rank max error=([^\s]+)', verification)
references = re.findall(r'single vs DDP parameter max error=([^\s]+)', verification)
if [int(c[0]) for c in checks] != [1, 2, 4, 8] or len(references) != 4:
    raise SystemExit('正确性验证日志不完整')
doc = Document(template_path)
ps = doc.paragraphs
expected = {0:'题目名称', 1:'研究目的', 3:'研究内容', 5:'实验', 6:'实验环境', 10:'实验负载', 12:'实验步骤', 15:'实验结果与分析', 17:'结论', 19:'AI 使用情况', 21:'AI完成的工作', 23:'本人的修改与验证', 25:'本人独立完成的部分'}
if any(ps[i].text.strip() != text for i, text in expected.items()):
    raise SystemExit('模板章节与预期不符，请检查模板')

def fill(paragraph, text):
    # Keep the paragraph and the first run formatting from the template.
    runs = paragraph.runs
    if runs:
        runs[0].text = text
        for run in runs[1:]:
            run._element.getparent().remove(run._element)
    else:
        paragraph.add_run(text)

def after(paragraph, text, prototype=None):
    source = prototype or ps[16]
    element = deepcopy(source._p)
    paragraph._p.addnext(element)
    result = Paragraph(element, paragraph._parent)
    fill(result, text)
    return result

heading = after(ps[0], 'D1 分布式环境中的数据并行与同步开销', ps[2])
fill(ps[2], '本实验探究分布式数据并行训练中并行计算收益与梯度同步开销之间的关系，分析数据并行训练的适用条件。')
fill(ps[4], '必做主线比较单进程与双进程 DDP 训练，分析全局批大小、局部批大小和梯度同步之间的关系。方向③考察梯度累积和延迟同步对通信开销与吞吐量的影响。')
fill(ps[7], '本实验在单台 Windows 计算机上运行，分别采用单进程和两个 CPU 进程。双进程通过 Gloo 后端和 file:// 初始化进程组，每进程设置 OMP_NUM_THREADS=1。')
fill(ps[8], '实验机器具有 20 个逻辑 CPU 和 15.71 GiB 内存，进程间通过本机通信。物理核心数和存储类型未记录。')
fill(ps[9], '软件环境为 Windows、Python 3.11.18、PyTorch 2.15.0+cpu 和 torchvision 0.29.2+cpu。')
fill(ps[11], '实验使用 torchvision 获取的 CIFAR-10 数据集，训练集包含 50000 张图像，测试集包含 10000 张图像；图像尺寸为 32×32，分类数为 10。训练模型采用 GroupNorm ResNet-18，使用 FP32 和 SGD，学习率为 0.01，动量为 0.9，随机种子为 42。')
fill(ps[13], '在项目目录中激活 ddp-lab 环境，设置 PYTHONUTF8=1、OMP_NUM_THREADS=1 和 MKL_NUM_THREADS=1。运行 python src/check_sampler.py 检查采样，运行 python src/verify.py 验证数值一致性；运行 python scripts/run_experiments.py --steps 4 --warmup 2 --repeats 3 --output results/final 采集训练数据。对 K=1、2、4、8 分别运行 python src/profiler.py --k K --strategy normal 或 delayed --output results/final_profiler，随后运行 python src/analyze_repeated.py --input results/final --profiler results/final_profiler --output figures/final 汇总结果。')
fill(ps[14], '实验过程截图：［待插入环境配置、双进程训练、正确性验证及 profiler 运行截图］。')
a1, a2, n, l = d['A1'], d['A2'], d['C4_normal'], d['C4_delayed']
fill(ps[16], f'每组预热 2 次、测量 4 次参数更新，重复 3 轮。A1 和 A2 的全局批大小均为 128；两组每次更新的全局样本集合一致。A1 和 A2 的平均吞吐量分别为 {a1["throughput_mean"]:.2f} 和 {a2["throughput_mean"]:.2f} 样本/秒，双进程在该负载下没有取得吞吐收益。进程调度和梯度同步均可能影响结果，但本实验不能仅凭两组耗时差量化通信开销。')
p = after(ps[16], f'B1 与 B2 均为双进程、每进程微批大小 16、累积步数 K=4，有效全局批大小为 128，仅同步策略不同。两组平均吞吐量分别为 {n["throughput_mean"]:.2f} 和 {l["throughput_mean"]:.2f} 样本/秒，延迟同步的吞吐比为 {l["throughput_mean"]/n["throughput_mean"]:.2f}。普通同步在每个微批反向传播时触发梯度同步，延迟同步使用 no_sync 覆盖前 K−1 次前向与反向，只在最后一次反向传播时同步；每个微批损失除以 K，累积后执行一次参数更新。')
p = after(p, '表1 实验结果。更新耗时标准差按所有测量更新计算，吞吐量标准差按各轮结果计算。')
table = doc.add_table(rows=1, cols=4)
table.style = 'Table Grid'
p._p.addnext(table._tbl)
for cell, text in zip(table.rows[0].cells, ('实验组', '更新耗时均值±标准差/ms', 'P50/P95/ms', '吞吐均值±标准差/样本·秒⁻¹')):
    cell.text = text
for r in rows:
    values = (r['name'], f"{r['mean_update_ms']:.2f}±{r['std_update_ms']:.2f}", f"{r['p50_ms']:.2f}/{r['p95_ms']:.2f}", f"{r['throughput_mean']:.2f}±{r['throughput_std_between_repeats']:.2f}")
    for cell, value in zip(table.add_row().cells, values):
        cell.text = value
anchor = deepcopy(ps[16]._p)
table._tbl.addnext(anchor)
p = Paragraph(anchor, ps[16]._parent)
fill(p, 'C 组的 K=1、2、4、8 对应有效批大小 32、64、128、256；固定更新次数使各组处理样本数不同。微批、前向、反向和参数更新阶段耗时记录在 aggregate.csv 中，均为 Rank 0 计时。反向耗时包含梯度同步，不能视为纯计算时间。')
for k in (1, 2, 4, 8):
    x, y = d[f'C{k}_normal'], d[f'C{k}_delayed']
    p = after(p, f'K={k} 时，普通同步和延迟同步的平均吞吐量分别为 {x["throughput_mean"]:.2f} 和 {y["throughput_mean"]:.2f} 样本/秒，平均更新耗时分别为 {x["mean_update_ms"]:.2f} 和 {y["mean_update_ms"]:.2f} ms。')
p = after(p, f'独立 profiler 使用合成输入、每进程微批大小 1，只采集单个更新周期的反向传播。K=4 时普通同步观察到 {n["profiler_count"]} 个 Gloo All-Reduce 事件，累计 {n["profiler_total_ms"]:.2f} ms；延迟同步观察到 {l["profiler_count"]} 个事件，累计 {l["profiler_total_ms"]:.2f} ms。事件数受 DDP 梯度桶重建影响，累计事件耗时包含采样影响，不能直接作为端到端通信开销。训练中每次更新后的 Loss 统计和最大耗时统计各有一次额外 All-Reduce，验证时还使用广播和集合通信，这些均未包含在独立梯度 profiler 统计中。')
for i, (k, grad, param, rank) in enumerate(checks):
    p = after(p, f'数值验证 K={k}：普通与延迟同步的梯度最大误差为 {grad}，更新参数最大误差为 {param}，Rank 间参数最大误差为 {rank}；同样样本的单进程参考与 DDP 更新参数最大误差为 {references[i]}。')
for i, (name, caption) in enumerate([('A_throughput.png','图1 单进程与双进程吞吐量'), ('B_time.png','图2 两种同步策略的更新耗时'), ('C_throughput.png','图3 不同累积步数的吞吐量'), ('communication.png','图4 独立 profiler 的通信事件')], 1):
    p = after(p, '')
    p.add_run().add_picture(str(root / 'figures/final' / name), width=Inches(5.5))
    p = after(p, caption)
fill(ps[18], '本实验中，双进程 DDP 的吞吐量低于单进程；在 K=4 的相同负载下，延迟同步高于普通同步。延迟同步减少梯度同步频率，在同步开销较明显时可能提高吞吐量。受 CPU 计算资源限制，每组测量规模较小，三轮使用相同随机种子；本实验主要考察相同负载下的相对性能差异。不同 K 的有效批大小不同，不能将 Loss 差异直接归因于同步策略。本实验基于 CPU/Gloo 开展，未进一步测量 GPU/NCCL 性能或可靠量化计算与通信重叠。')
fill(ps[20], '实验使用了 AI 工具。')
fill(ps[22], '实验使用 ChatGPT 和 Codex 辅助理解 DDP、检查与调试训练和统计代码、运行实验、整理结果与图表，并辅助编写实验报告。')
fill(ps[24], '【待填写本人实际进行的检查、修改与验证】')
fill(ps[26], '【待填写本人独立完成的具体工作】')
out = root / 'report' / 'D1实验报告.docx'
out.parent.mkdir(parents=True, exist_ok=True)
doc.save(out)
print(f'模板: {template_path}\n报告: {out}')
