from pathlib import Path
import json
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml.ns import qn
root=Path(__file__).resolve().parents[1]; root=root.parent if root.name == 'code' else root; out=root/'report'; out.mkdir(exist_ok=True)
rs=json.loads((root/'results/repeated/aggregate.json').read_text(encoding='utf-8')); d={r['name']:r for r in rs}
env=json.loads((root/'results/environment.json').read_text(encoding='utf-8-sig'))
doc=Document(); style=doc.styles['Normal']; style.font.name='Arial'; style._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); style.font.size=Pt(10.5)
doc.add_heading('D1 分布式环境中的数据并行与同步开销',0)
doc.add_paragraph('课程：大规模数据处理系统\n姓名：待填写　学号：待填写\n选题：梯度累积与延迟同步对通信开销的影响')
def sec(title, text): doc.add_heading(title,level=1); doc.add_paragraph(text)
sec('研究目的','比较单进程与双进程数据并行，研究梯度累积与延迟同步对同步开销和吞吐量的影响，并检查训练计算的正确性。')
sec('研究内容','必做主线为单进程和双进程 DDP 对照；方向③为普通同步累积与 no_sync 延迟同步，以及 K=1、2、4、8 的影响。')
sec('实验环境',f"单机 Windows CPU 和两个 Gloo 进程，逻辑 CPU {env['logical_cpus']}，内存 {env['memory_gib']} GiB，PyTorch {env['torch']}、torchvision {env['torchvision']}、Python 3.11。每进程 OMP_NUM_THREADS=1。Windows 使用 spawn 与 file://；Linux CUDA/NCCL 代码路径未在本实验验证。")
sec('实验负载','CIFAR-10 训练集 50000 张、测试集 10000 张；ResNet-18、GroupNorm、10 分类、FP32、SGD 学习率 0.01、动量 0.9、种子 42。受单机 CPU 时间限制，本次采用缩减测量：每组 2 个预热更新、512 个测量样本、重复 3 次。A 每轮 4 次测量更新；C 的 K=1、2、4、8 每轮分别为 16、8、4、2 次。测量长度小于建议的 20/200，结果不能视为充分的长期性能统计。')
sec('实验步骤','依次运行 python scripts/run_experiments.py --samples 512 --warmup 2 --repeats 3 --output results/repeated；分别运行 src/profiler.py 的四个 K 和两种策略；使用 src/analyze_repeated.py 汇总并绘图，运行 src/verify.py 验证。results/repeated 保存每轮命令、CSV、JSON 和原始控制台日志，可直接打开作为截图素材。桌面截图尚未采集。')
sec('原理与控制变量','DDP 在反向传播时按桶 All-Reduce 梯度并取平均。每个微批 loss 除以 K，K 次反向传播后仅执行一次更新；no_sync 同时覆盖前 K−1 次前向与反向。B1/B2 每 rank 微批 16、K=4、有效全局批 128；模型初始化、随机种子、分布式采样顺序、优化器与更新次数一致。A1/A2 的全局批均为 128，但单进程随机采样与 DistributedSampler 的样本顺序没有逐样本对齐。C 固定微批与测量样本数，K 不同时有效批和更新次数不同，故不比较不同 K 的收敛质量。')
doc.add_heading('实验结果与分析',level=1)
doc.add_paragraph('表中时间为合并所有测量更新得到的均值和 P50/P95；吞吐量为每轮总样本数除以该轮更新时间之和，再对三轮求均值；± 为三轮吞吐量的样本标准差。完整指标和各轮值见 aggregate.csv 与 aggregate.json。')
t=doc.add_table(rows=1,cols=5); t.style='Table Grid'
for c,x in zip(t.rows[0].cells,['配置','更新数/轮','均值 ms','P50 / P95 ms','样本/秒 ± 标准差']): c.text=x
for key in ['A1','A2','C1_normal','C1_delayed','C2_normal','C2_delayed','C4_normal','C4_delayed','C8_normal','C8_delayed']:
 r=d[key]; vals=[key,str(r['updates_per_repeat']),f"{r['mean_update_ms']:.1f}",f"{r['p50_ms']:.1f} / {r['p95_ms']:.1f}",f"{r['throughput_mean']:.1f} ± {r['throughput_std_between_repeats']:.1f}"]
 for c,v in zip(t.add_row().cells,vals): c.text=v
n=d['C4_normal']; l=d['C4_delayed']; speed=d['A2']['throughput_mean']/d['A1']['throughput_mean']
doc.add_paragraph(f"A2/A1 吞吐比 {speed:.3f}，双进程在该 CPU 实验中未加速。B1 三轮吞吐分别为 {', '.join(f'{x:.1f}' for x in n['repeat_throughputs'])}，B2 为 {', '.join(f'{x:.1f}' for x in l['repeat_throughputs'])} 样本/秒；三轮方向一致，B2/B1 的平均吞吐比约 {l['throughput_mean']/n['throughput_mean']:.2f}。每轮只有 4 个测量更新，因此不能称为长期稳定的普适结论。")
for image,caption in [('A_throughput.png','图1 单进程与双进程吞吐量'),('B_time.png','图2 B1 与 B2 更新耗时'),('C_throughput.png','图3 K 与吞吐量'),('communication.png','图4 独立 profiler 通信事件'),('loss.png','图5 B 组第一轮性能测量 Loss')]:
 doc.add_picture(str(root/'figures/repeated'/image),width=Inches(5.6)); doc.add_paragraph(caption)
doc.add_paragraph(f"独立 profiler 使用 CPU Gloo、合成输入、每 rank 微批 1、单个更新周期，K=4 时普通同步观察到 {n['profiler_count']} 次 Gloo 事件、累计 {n['profiler_total_ms']:.1f} ms；延迟同步 {l['profiler_count']} 次、累计 {l['profiler_total_ms']:.1f} ms。桶重建会影响调用数量，采样及 profiler 开销使这些事件不能直接视为 CIFAR-10 基准或端到端额外通信开销，也不能用 DDP 减单进程的耗时估算通信成本。各 K 事件见 aggregate.csv；A 的通信事件未单独采集，留空。")
sec('正确性验证','确定性 FP32 输入、K=4：两种同步策略梯度最大误差 1.1920929e−7，更新参数最大误差 1.49011612e−8，Rank 间最大误差 0；相同样本的单进程参考与 DDP 参数最大误差 1.1920929e−7。训练检查 loss 有限。单进程训练两步后，完整 CIFAR-10 测试集 1138/10000（11.38%），只验证评估流程，不作为收敛或最终模型质量结论。')
sec('结论','本机短时三轮测量中，普通同步在 K=4 时吞吐低于延迟同步；单进程高于双进程。可能涉及梯度桶通信、CPU 进程调度、数据读取与计算重叠等，不能仅凭通信事件时间量化端到端成本。测量更新步数有限，微批独立耗时、计算通信重叠和 CUDA/NCCL 未测；A 采样顺序未逐样本对齐。')
sec('AI 使用情况','Codex 参与训练和启动代码的生成与调试、实验执行、统计、绘图和报告整理。本人检查、修改与验证的内容：待本人如实填写。本人独立完成的部分：待本人如实填写。')
doc.save(out/'D1实验报告.docx')
