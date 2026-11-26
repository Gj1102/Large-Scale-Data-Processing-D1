"""Add comparison and implementation analysis to the course-template report."""
import json
from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

root=Path(__file__).resolve().parents[2]
path=root/'report/51290713112_高洁_D1.docx'; doc=Document(path)
if any(p.text=='本人复现实验与结果一致性分析' for p in doc.paragraphs): raise SystemExit('Already enriched')
body_style=next(p.style for p in doc.paragraphs if p.text.startswith('本实验通过单进程'))
head_style=next(p.style for p in doc.paragraphs if p.text.strip()=='实验结果与分析')
def para(anchor,text,heading=False):
 p=anchor.insert_paragraph_before(text); p.style=head_style if heading else body_style; return p
def fig(anchor,name,caption):
 p=anchor.insert_paragraph_before(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(str(root/'figures/comparison'/name),width=Inches(5.7)); p.paragraph_format.keep_with_next=True
 c=anchor.insert_paragraph_before(caption); c.alignment=WD_ALIGN_PARAGRAPH.CENTER; c.style=body_style
anchor=next(p for p in doc.paragraphs if p.text.strip()=='实验步骤')
para(anchor,'数据并行实现与梯度累积原理',True)
para(anchor,'各进程持有一份模型和优化器状态。DistributedSampler 按 rank 划分同一随机排列；DDP 在反向传播时按梯度桶归约并平均各进程梯度。对于等大小微批，每个进程累积 K 次、损失每次除以 K，DDP 的跨进程平均使一次更新对应 P×b×K 个样本的平均梯度。All-Reduce 同步的是梯度，不是输入数据。')
para(anchor,'实现中使用 GroupNorm(32, channels) 替换 ResNet-18 的 BatchNorm。GroupNorm 按样本的通道组归一化，不依赖批内统计量；这有助于比较不同进程分片和微批划分下的梯度，而不能消除浮点运算顺序差异。每次更新先清空梯度，累积 K 次反向传播后才执行一次 SGD 更新。')
para(anchor,'核心实现（节选）：ctx = model.no_sync() if world > 1 and strategy == "delayed" and micro < K-1 else nullcontext()；with ctx: loss = cross_entropy(model(x), y); (loss / K).backward()。no_sync() 覆盖对应的前向和反向：DDP 在前向阶段建立同步相关状态，因此仅包围 backward 不能可靠地关闭该微批的同步。')
fig(anchor,'architecture.png','图 5  实验系统与数据处理流程')
fig(anchor,'sync_flow.png','图 6  K=4 时普通同步与延迟同步的执行流程')
para(anchor,'图 6 描述的是同步反向传播的轮数；每轮可能包含多个梯度桶，因而不能把同步轮数等同于 profiler 观察到的 All-Reduce 事件数。')
anchor=next(p for p in doc.paragraphs if p.text.strip()=='结论')
para(anchor,'本人复现实验与结果一致性分析',True)
para(anchor,'两批实验使用相同的 10 种配置，各配置测量 4 次更新并重复 3 轮，合计 60 次训练运行；独立 profiler 每批采样 8 次。表 6 的单位为样本/秒，吞吐量取三轮吞吐量的算术平均；两批数据独立保存，并非 20 种不同配置。')
comparison=json.loads((root/'results/comparison/comparison.json').read_text(encoding='utf-8'))
table=doc.add_table(rows=1,cols=3); table.style='Table Grid'; table.rows[0].cells[0].text='配置'; table.rows[0].cells[1].text='原始实验'; table.rows[0].cells[2].text='本人复现实验'
for r in comparison:
 cells=table.add_row().cells; cells[0].text=r['name']; cells[1].text=f"{r['original_throughput_mean']:.2f}"; cells[2].text=f"{r['reproduction_throughput_mean']:.2f}"
para(anchor,'表 6  两批实验的平均吞吐量（样本/秒）'); anchor._p.addprevious(table._element)
para(anchor,'两批实验中 A2 的吞吐量都低于 A1，说明本机 CPU 下并行计算收益未抵消梯度同步、进程调度及资源竞争等开销；无法将总耗时差直接归为通信时间。K=1 时普通同步与延迟同步都在每次反向传播时同步，实测小幅差异可能来自运行波动。K=2、4、8 时延迟同步均有吞吐优势：K=4 的加速比分别约为 2.33 和 2.40，K=8 分别约为 3.11 和 3.29。')
para(anchor,'这两批结果的整体趋势一致，但绝对值不同。调度、系统负载及短测量窗口都可能造成波动；两批在同一环境、使用相同随机种子，不能视为跨硬件或多种随机种子的独立稳健性验证。由于 K 改变时有效批大小也改变，跨 K 的差异不能完全归因于同步频率。')
for name,cap,explanation in [
 ('throughput_ab.png','图 7  两批 A/B 组吞吐量对照','误差棒为三轮吞吐量的样本标准差。B 组保持 K 和有效批大小不变，更适合观察同步策略变化。'),
 ('throughput_k.png','图 8  两批不同 K 与同步策略的吞吐量','误差棒为三轮吞吐量标准差；跨 K 时有效全局批大小同时变化。'),
 ('speedup.png','图 9  两批延迟同步相对普通同步的吞吐量比','加速比是各批次对应配置的平均吞吐量之比，K=1 时理论同步频率相同。'),
 ('events.png','图 10  两批独立 profiler 的 Gloo All-Reduce 事件数','两批各自的 K=1、2、4、8 普通同步事件数为 1、4、10、22，延迟同步均为 1；通信 JSON 与 trace 中的事件计数一致。桶划分和首次桶重建会影响事件数，因此事件数不能直接等同于 K；采样采用合成负载、没有预热，事件累计耗时不代表端到端额外通信耗时。'),
 ('update_time.png','图 11  两批每次参数更新耗时','误差棒为每批 12 次测量更新的样本标准差；更新总耗时取各 Rank 的最大值。'),
 ('stages.png','图 12  K=4 两批 Rank 0 阶段耗时','前向和反向微批均值乘以 K，优化器时间按每次更新计。图中仅统计 Rank 0，反向含同步；阶段之和不等于各 Rank 最大总耗时，也不表示纯计算或可靠的计算通信重叠比例。')]:
 fig(anchor,name,cap); para(anchor,explanation)
para(anchor,'复现正确性检查中，K=1 的普通与延迟同步梯度及更新参数误差为 0；K=2、4、8 的最大梯度误差为 1.1920929e-07、最大参数误差为 1.49011612e-08，Rank 间参数误差均为 0。单进程参考最大参数误差为 1.1920929e-07。微小差异与 FP32 运算顺序及归约顺序有关，在验证容差内；这支持固定输入和对应批大小下两种累积方式的一致性，但不证明长期收敛轨迹完全相同。')
doc.save(path)
