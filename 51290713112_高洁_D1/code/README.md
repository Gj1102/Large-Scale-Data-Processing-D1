# D1 分布式数据并行与同步开销

本实验使用 PyTorch DistributedDataParallel（DDP），比较单进程与双进程训练，并研究梯度累积和延迟同步对 CPU/Gloo 训练吞吐量的影响。

## 实验原理

DDP 在反向传播时按梯度桶执行 All-Reduce，使各进程使用一致的平均梯度。每个参数更新包含 K 个微批，微批损失除以 K 后累积梯度，再执行一次优化器更新。普通同步在每个微批反向传播时同步梯度；延迟同步通过 `no_sync()` 包围前 K−1 次前向与反向传播，在最后一个微批同步。有效全局批大小为进程数 × 每进程微批大小 × K。

## 项目目录

- `code/src/`：训练、双进程启动、采样与数值检查、通信采样和数据分析。
- `code/scripts/`：实验自动化、报告生成和结果核对。
- `code/configs/`：实验配置。
- `results/final/`：本轮原始 CSV、配置、日志及汇总；`results/final_profiler/`：独立通信事件与 trace。
- `figures/final/`：本轮统计图；`report/`：实验报告。
- `results/repeated/` 和 `figures/repeated/`：先前固定样本数实验结果。
- `code/templates/`：报告原始模板备份。

源码位于 `code/`，数据、图表和报告位于项目目录顶层。以下命令均在 `51290713112_高洁_D1` 目录运行。

## 环境配置

本次实验在单机 Windows 上使用 Python 3.11.18、PyTorch 2.15.0+cpu、torchvision 0.29.2+cpu、Gloo，逻辑 CPU 20，内存 15.71 GiB。每进程使用一个 OpenMP 线程。已使用 Conda 环境 `ddp-lab`；依赖列于 `requirements.txt`，报告生成还需要 `python-docx`；如环境未安装，可执行 `python -m pip install python-docx`。

```powershell
conda activate ddp-lab
$env:PYTHONUTF8='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
```

训练使用 CIFAR-10。数据集位于项目目录的 `data/`；如需重新获取，可在项目目录运行 `python code/src/train.py --download --data ./data --batch 128 --accum-steps 1 --warmup 0 --steps 1` 获取数据。报告生成脚本使用 `code/templates/51290713112_高洁_D1.docx` 的备份，不修改模板。

## 运行方法

为避免覆盖已有数据，以下示例写入新的 `reproduction` 目录。首次运行前创建目录。实验和 profiler 应顺序运行，避免相互干扰。

```powershell
New-Item -ItemType Directory -Force results/reproduction,results/reproduction_profiler,figures/reproduction | Out-Null
python code/src/check_sampler.py
python code/src/verify.py
python code/scripts/run_experiments.py --steps 4 --warmup 2 --repeats 3 --output results/reproduction
foreach ($k in 1,2,4,8) {
    foreach ($strategy in 'normal','delayed') {
        python code/src/profiler.py --k $k --strategy $strategy --output results/reproduction_profiler
    }
}
python code/src/analyze_repeated.py --input results/reproduction --profiler results/reproduction_profiler --output figures/reproduction
```

`--samples 512` 且不指定 `--steps` 时，每组按固定样本数测量；`--steps 200 --warmup 20 --repeats 3` 可指定较长的固定更新数实验，输出目录应使用新目录。当前课程报告为 `report/51290713112_高洁_D1.docx`，可用 `python code/scripts/check_report.py` 核对其中的实验统计。`python code/scripts/make_report.py` 从模板和 `results/final` 生成另一份基础报告 `report/D1实验报告.docx`，不包含对当前课程报告的后续编辑；`python code/scripts/make_pdf.py` 通过已安装的 Word 或 LibreOffice 导出当前课程报告。

## 实验设计

采用 CIFAR-10、GroupNorm ResNet-18、FP32、SGD，学习率 0.01、动量 0.9、随机种子 42。

| 组别 | 进程数 | 每进程微批 | K | 同步策略 | 有效全局批 |
|---|---:|---:|---:|---|---:|
| A1 | 1 | 128 | 1 | 无 DDP | 128 |
| A2 | 2 | 64 | 1 | 普通 | 128 |
| B1 / C4 normal | 2 | 16 | 4 | 普通 | 128 |
| B2 / C4 delayed | 2 | 16 | 4 | 延迟 | 128 |
| C | 2 | 16 | 1、2、4、8 | 普通、延迟 | 32、64、128、256 |

A1/A2 使用同一随机排列，每次更新的全局样本集合一致。B 组除同步策略外保持配置一致。C 组固定每轮测量更新次数，因此 K 改变时样本总数也改变；历史固定样本数实验采用不同统计口径。

## 实验结果

本轮每组预热 2 次、测量 4 次更新，重复 3 轮。平均吞吐量：A1 为 191.72，A2 为 156.22；B1 为 54.08，B2 为 125.80 样本/秒。每更新总耗时使用各 Rank 的最大值，阶段耗时为 Rank 0 测量值；反向阶段包含梯度同步。完整统计、逐步记录和实际命令见 `results/final/`。

K=1、2、4、8 的数值验证通过：普通同步与延迟同步的梯度、更新参数及各 Rank 参数在测试容差内一致；单进程参考的参数最大误差见 `results/final/verification_all_k.log`。独立合成负载 profiler 的 K=4 普通同步和延迟同步分别记录 10 和 1 个 Gloo All-Reduce 事件。

## 实验局限性

每组测量规模较小，三轮使用相同随机种子，结果主要用于比较本机相同负载下的相对性能。训练中每更新还有 Loss 和计时统计通信，独立 profiler 仅覆盖梯度反向阶段；梯度桶重建会影响事件数，事件累计耗时不能直接视为端到端额外通信开销。计算与通信重叠未可靠量化。本实验使用 CPU/Gloo，未测量 GPU/NCCL。




## 提交材料

`report/` 保存课程报告，`results/final/`、`results/final_profiler/` 和 `figures/final/` 分别保存本轮测量记录、通信采样与图表。`history/` 是开发阶段的历史备份，`data/` 是本地 CIFAR-10 数据集；是否随作业提交以课程要求为准。数据集约 357 MB、历史备份约 25 MB，整理提交材料时应检查体积。报告中的真实运行截图位置需要使用实际截图填写。

根目录 `.gitignore` 已包含当前数据集路径；已被 Git 跟踪的文件不会因新增忽略规则而自动取消跟踪。


## 正确性验证记录

在 `ddp-lab` 环境中运行 `python code/src/check_sampler.py`，前三个 Epoch 的每个完整更新批次中，A1 与 A2 的全局样本集合一致，实际输出保存在 `results/sampler_verification.log`。运行 `python code/src/verify.py`，K=1、2、4、8 均通过；实际输出保存在 `results/verification_new.log`。K=1 的梯度与参数误差均为 0，K=2、4、8 的梯度最大误差为 1.1920929e-07、参数最大误差为 1.49011612e-08；各 Rank 参数误差均为 0，单进程参考与 DDP 参数最大误差均为 1.1920929e-07。报告中的两处验证截图仍待插入。
