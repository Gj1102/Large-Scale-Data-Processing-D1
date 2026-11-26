# 实验运行与复现

以下命令在 `51290713112_高洁_D1` 项目目录的 PowerShell 中执行。

## 环境与数据

已记录的实验环境为 Windows、Python 3.11.18、PyTorch 2.15.0+cpu、torchvision 0.29.2+cpu、Gloo。项目使用 `ddp-lab` Conda 环境，每进程一个 OpenMP 线程。依赖版本见 `code/requirements.txt`；PyTorch CPU 版本需从提供对应版本的安装源获取。

```powershell
conda activate ddp-lab
$env:PYTHONUTF8='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -c "import torch, torchvision; print(torch.__version__, torchvision.__version__, torch.distributed.is_gloo_available())"
```

训练使用 CIFAR-10，默认读取项目目录下的 `data/`。若尚未下载，可运行：

```powershell
python -c "from torchvision.datasets import CIFAR10; CIFAR10('./data', train=True, download=True)"
```

## 实验参数

模型为 GroupNorm ResNet-18，FP32、SGD、学习率 0.01、动量 0.9、随机种子 42。有效全局批大小为进程数 × 每进程微批大小 × K。

| 配置 | 进程数 | 每进程微批 | K | 同步方式 | 有效全局批 |
|---|---:|---:|---:|---|---:|
| A1 | 1 | 128 | 1 | 无 DDP | 128 |
| A2 | 2 | 64 | 1 | 普通 | 128 |
| B1 / C4 normal | 2 | 16 | 4 | 普通 | 128 |
| B2 / C4 delayed | 2 | 16 | 4 | 延迟 | 128 |
| C | 2 | 16 | 1、2、4、8 | 普通、延迟 | 32、64、128、256 |

原始实验和本人复现实验均为每配置预热 2 次、测量 4 次更新、重复 3 轮。`configs/default.yaml` 是说明性配置，运行脚本不读取它；20/200/3 是未执行的长实验计划。运行脚本不带参数时使用其他短测默认值。

## 复现命令

为避免覆盖已有结果，先创建新的时间戳目录；以下命令在同一 PowerShell 会话中依次执行。训练和 profiler 应顺序运行。

```powershell
$run = 'reproduction_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
$results = "results/$run"
$profiler = "results/${run}_profiler"
$figures = "figures/$run"
New-Item -ItemType Directory -Force $results,$profiler,$figures | Out-Null

python code/src/check_sampler.py
python code/src/verify.py
python code/scripts/run_experiments.py --steps 4 --warmup 2 --repeats 3 --output $results
foreach ($k in 1,2,4,8) {
    foreach ($strategy in 'normal','delayed') {
        python code/src/profiler.py --k $k --strategy $strategy --output $profiler
    }
}
python code/src/analyze_repeated.py --input $results --profiler $profiler --output $figures
```

只分析已保存的两批数据，不运行训练：

```powershell
python code/scripts/compare_runs.py
```

原始结果在 `results/final/` 和 `results/final_profiler/`，本人复现结果在 `results/manual_20261125_223126/` 及对应 `_profiler` 目录；复现终端文本为该训练结果目录中的 `terminal_user.txt`。对比数据和图表分别输出至 `results/comparison/`、`figures/comparison/`。
