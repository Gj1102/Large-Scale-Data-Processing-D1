# D1 分布式数据并行与同步开销

课程必做比较单进程和双进程 DDP；方向③比较梯度累积普通同步与 no_sync 延迟同步。DDP 每次反向传播按桶 All-Reduce 并平均梯度；每微批 loss 除以 K、每个周期只 zero_grad 和 optimizer.step 各一次。no_sync 必须覆盖前 K−1 次前向和反向。

## 实际环境与结果

本次使用 Windows、Python 3.11、PyTorch 2.15.0+cpu、torchvision 0.29.2+cpu、CPU/Gloo、逻辑 CPU 20、内存 15.71 GiB、OMP_NUM_THREADS=1。双进程使用 spawn 和唯一 file:// 存储；没有 GPU 测试。CIFAR-10、GroupNorm ResNet-18、SGD lr=0.01、momentum=0.9、FP32、seed=42。

为控制 CPU 运行时间，本次每组预热 2 更新，测量 512 样本，重复 3 次。A1/A2 每轮 4 更新；C 的 K=1/2/4/8 分别为 16/8/4/2 更新，微批 16、双进程；B1/B2 即 C4 normal/delayed。A1/A2 全局批 128，但样本顺序未逐样本对齐；B 的初始化、数据顺序、参数和更新次数一致。不同 K 的有效批和更新次数变化，不能将收敛质量视为相同条件。

三轮平均吞吐量：A1 203.3、A2 174.0、B1 55.6、B2 135.9 样本/秒。B1 三轮 55.4/56.7/54.6，B2 为 132.2/134.9/140.5。每轮 B 只有 4 更新，方向一致但不足以支持长期稳定性结论。独立合成输入 profiler、K=4、每进程微批 1、一个更新周期下，普通同步 10 个 Gloo all-reduce 事件，累计 3165.4 ms；延迟同步 1 个事件，累计 738.4 ms。该事件耗时包括 profiler 影响，不能当作端到端额外通信成本；不能用 DDP 减单进程时间推算通信成本。A 的通信事件未单独采集。

每步耗时含数据读取、前向、反向和更新；CUDA synchronize 后计时，DDP 用各 rank 时间 MAX；样本吞吐量为总样本/总更新耗时。汇总文件中 update 标准差和百分位数使用合并的更新记录，吞吐量标准差在三轮之间计算。GPU/NCCL、微批独立计算时间和计算通信重叠尚未实测。性能运行的 Loss 并非收敛测试。

## Windows PowerShell

在含数据的项目目录中：

```powershell
conda activate ddp-lab
$env:OMP_NUM_THREADS='1'
python src/verify.py
python scripts/run_experiments.py --samples 512 --warmup 2 --repeats 3 --output ../results/reproduction
foreach ($k in 1,2,4,8) { foreach ($strategy in 'normal','delayed') { python src/profiler.py --k $k --strategy $strategy --output ../results/reproduction_profiler } }
python src/analyze_repeated.py --input ../results/reproduction --profiler ../results/reproduction_profiler --output ../figures/reproduction
```

数据下载：`python src/train.py --download --batch 128 --accum-steps 1 --warmup 0 --steps 1`；数据集不包含在提交包中。所有 K 的 profiler 可将 `--k` 分别设为 1、2、4、8。合成输入只用于验证和 profiler，不作为基准。`--samples` 必须可被 256 整除；每组样本相同，K 不同更新数不同。正式更长测量可增大样本与预热，但本次并未执行默认建议的 20/200/3。

## Linux CUDA（未在本机验证）

```bash
python src/train.py --batch 128 --accum-steps 1 --warmup 20 --steps 200
torchrun --standalone --nproc-per-node=2 src/train.py --batch 64 --accum-steps 1 --warmup 20 --steps 200
torchrun --standalone --nproc-per-node=2 src/train.py --batch 16 --accum-steps 4 --strategy delayed --warmup 20 --steps 200
```

## 结果与正确性

`results/repeated/` 包含每组配置、原始 CSV、摘要和日志；aggregate.csv/json 汇总三轮及单独 profiler。`figures/repeated/` 是报告使用的图；历史结果只能作历史记录。验证固定输入得到梯度最大误差 1.19e-7、参数更新误差 1.49e-8、rank 误差 0、单进程参考误差 1.19e-7。训练两步的测试集准确率 11.38% 仅用于验证评估流程。

截图素材：打开 `results/repeated/verification.log`、各组 `.log` 与 `_config.json`、`results/environment.json`、`results/profile_repeated/*_communication.json` 和图表；这些是真实输出，尚非桌面截图。需自行截图并补全姓名、学号、本人核验情况及本人出镜视频。DOCX 和 PDF 的关键结果已核对；PDF 已渲染检查，DOCX 无法在当前环境原生渲染检查。

依赖 `requirements.txt`；报告生成还需 python-docx、PyMuPDF。Windows base Conda 若出现 OpenMP 冲突，请使用可正常导入的 ddp-lab 环境，勿通过不受支持的兼容开关掩盖问题。

??????? seed=42 ?????????????????????????????????????????Profiler ? synthetic ???????? 1??????????? rank 0 ???A1/A2 ??????????

## 2026 最终实验（CPU/Gloo）

在 D1-DDP 目录使用 `conda activate ddp-lab`，再执行 `$env:PYTHONUTF8='1'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'`。中文路径要求 UTF-8 模式。下列目录应事先创建，避免覆盖历史结果。

```powershell
New-Item -ItemType Directory -Force results/final,results/final_profiler,figures/final | Out-Null
python scripts/run_experiments.py --steps 4 --warmup 2 --repeats 3 --output results/final
foreach ($k in 1,2,4,8) { foreach ($strategy in 'normal','delayed') { python src/profiler.py --k $k --strategy $strategy --output results/final_profiler } }
python src/analyze_repeated.py --input results/final --profiler results/final_profiler --output figures/final
```

本次固定更新次数：每轮预热 2、测量 4 更新，3 轮。K 不同因有效批不同而样本数不同。原 512 样本固定样本短测保留在 `results/repeated`；完整 20/200/3 在本机运行时间较长，本次未运行。A1/A2 采用同一 `DistributedSampler` 随机排列，每更新全局样本集合相同；多进程各 rank 分片顺序不同。各阶段耗时为 rank 0：微批不含数据加载，反向包含梯度同步；更新总耗时为各 rank 最大值且含数据加载。阶段耗时不是跨 rank 最大值，不可直接与总耗时相加；GPU 路径为同步计时，会影响性能且未验证。每个更新的梯度同步反向次数记录于 CSV；额外的 Loss 和时间统计 all-reduce 位于计时区间外，独立 profiler 只捕获模型反向。事件累计耗时不能代表端到端通信开销，不能可靠量化计算通信重叠。

复现时请将 `results/final`、`results/final_profiler` 和 `figures/final` 换成新的空目录：脚本按实验 ID 写文件，重用已有目录会覆盖同名文件。A1/A2 采样检查：`python src/check_sampler.py`；数值一致性检查：`python src/verify.py`。B1/B2 分别对应 `C4_normal` 和 `C4_delayed`。历史数据与新采集数据不可直接混合统计，因为历史版本未逐步对齐 A 组样本，也没有阶段计时。
如需更长的固定更新数实验，可使用新目录运行 `python scripts/run_experiments.py --steps 200 --warmup 20 --repeats 3 --output results/long_run`。这会对每个 K 使用不同总样本数，运行前应确认机器可承受长时间 CPU 负载。

提交目录使用说明：在 `51290713112_高洁_D1` 目录下，以 `python code/scripts/run_experiments.py ...` 运行自动化，数据放在该目录的 `data`（提交包未附数据集）；分析与 profiler 分别使用 `python code/src/analyze_repeated.py ...` 和 `python code/src/profiler.py ...`。上面的命令以开发目录 D1-DDP 为工作目录。
