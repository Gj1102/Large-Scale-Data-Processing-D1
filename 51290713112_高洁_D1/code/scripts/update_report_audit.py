from docx import Document
from pathlib import Path
p=next(Path('report').glob('51290713112_*_D1.docx'))
d=Document(p)
def replace(prefix, text):
    hits=[x for x in d.paragraphs if x.text.startswith(prefix)]
    assert len(hits)==1, (prefix,len(hits))
    x=hits[0]
    x.runs[0].text=text
    for run in x.runs[1:]: run.text=''
replace('延迟同步的平均吞吐量', 'B 组仅改变同步策略。延迟同步的平均吞吐量为普通同步的约 2.33 倍，平均更新耗时下降约 57.1%。普通同步在每个微批的反向传播中都要等待梯度归约；延迟同步将前 3 次归约推迟到最后一次反向传播，减少了同步频率。该结果与这一机制一致，但由于测试时间较短且通信和计算可能重叠，不能将全部差异定量归因于通信。')
replace('不同 K 对应的有效全局批大小', 'C 组固定每进程微批大小为 16，K=1、2、4、8 时有效全局批大小分别为 32、64、128、256。每轮固定测量 4 次更新，因此处理的样本总数随 K 改变。C 组反映累积步数和有效批大小组合的影响，吞吐变化不能完全归因于 K；B 组固定有效批大小和 K，是隔离同步策略的主要对照。不同批大小下的 Loss 差异也不能直接归因于同步策略。')
replace('普通同步每个微批均触发梯度同步', '普通同步每个微批均触发梯度同步，延迟同步只在累积周期末触发一次。采样没有预热，首次反向传播及梯度桶重建可能影响事件数量；All-Reduce 事件数还受桶划分影响，不能等同于同步轮数。采样使用合成负载，事件累计耗时受插桩影响，不是完整训练的端到端通信耗时。训练中更新结束后还有 Loss 和最大耗时统计通信，未计入独立梯度通信采样。')
replace('延迟同步适用于', '延迟同步适用于同步开销明显、允许多个微批累积后再更新参数的场景，收益取决于模型、批大小、硬件和通信后端。本实验每轮预热 2 次、测量 4 次更新，重复 3 轮且使用相同随机种子；计划的 20/200/3 长时间实验未完成。没有实测 CPU 利用率和内存峰值，也未可靠量化计算与通信重叠。独立 profiler 使用合成负载，其时间不代表完整训练端到端通信耗时。CPU/Gloo 的结果不能直接推广到 GPU/NCCL 或长期收敛过程。')
replace('本次由我负责确定选题方向', '【待本人填写：独立完成的工作；如无，请据实说明。】')
replace('我在实验过程中重点检查', '【待本人填写：实际修改、运行和验证的内容。】')
for para in d.paragraphs:
    if para.text.startswith('每个配置预热 2 次'):
        para.insert_paragraph_before('每次更新的总耗时从读取数据前开始，包含数据读取、前向传播、反向传播（含梯度同步）和优化器更新；结束后的 Loss 汇总、各 Rank 耗时汇总通信以及 CSV 写入不计入。阶段耗时取 Rank 0，反向阶段并非纯计算时间。')
        break
else: raise RuntimeError('timing insertion point missing')
d.save(p)
