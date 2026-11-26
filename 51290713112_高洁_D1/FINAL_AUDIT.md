# D1 最终验收报告

生成时间：2026-11-26 12:04:49 +0800。运行环境：`D:\software\Conda\envs\ddp-lab\python.exe`。

## 本次修改

- `report/51290713112_高洁_D1.docx`：在模板基础上补充实现原理、两批比较、架构与同步流程、六幅统计图。保留用户提供的个人说明及真实截图占位。
- `code/configs/default.yaml`：区分实际 2/4/3 和未执行的计划 20/200/3；配置仅供说明，运行脚本不读取它。
- `code/requirements.txt`：按 ddp-lab 中 pip freeze 的直接依赖固定版本；CPU 版 PyTorch 的可用安装源取决于环境。
- `code/README.md`：说明实际配置、计划配置、资源差异和同步计数口径。
- `code/scripts/check_report.py`：检查章节、身份、统计、图表、占位、README Markdown 链接和关键数据；原脚本及配置、依赖文件分别保留 .bak 备份。
- `code/scripts/compare_runs.py`、`diagrams.py`、`enrich_report.py`：核对两批原始文件并生成对比数据、图和报告内容；后两者不应对已有报告重复执行。
- `code/scripts/final_audit.py`：运行静态检查并生成本报告；本轮未重新运行训练或验证。
- 未修改训练算法、既有实验原始数据、日志、profiler 记录或汇总；未删除历史材料，也未提交或推送 Git。

## 本次自动检查

### PASS：两批数据、配置和通信记录

命令：`python code/scripts/check_final.py`

```text
PASS: 2 batches, 60 runs, 16 profiler captures, summaries, configurations and trace event counts
WARNING: timings are short and same-seed; stage timing is Rank 0 and backward includes synchronization
PASS: 30 CSV files and 10 summary rows match
```
### PASS：报告、路径和文件完整性

命令：`python code/scripts/check_report.py`

```text
PASS: 报告章节：齐全
PASS: 报告姓名和学号
PASS: 报告与汇总数值：10 组
PASS: 两批报告对照数据：10 组一致
PASS: 图表嵌入：12 个，媒体文件 12 个；ZIP 错误 None，空文件 []；清晰度需视觉检查
MANUAL: 报告含未完成标记：待插入（3 处）
MANUAL: 报告保留真实运行截图占位，须本人插入
PASS: 已检查 Markdown 链接：README.md (code)
PASS: 已检查 Markdown 链接：README.md (project-01)
PASS: 已检查 README 中列出的项目路径
PASS: 关键实验文件 149 项：齐全且非空
```
### PASS：编码

命令：`python code/scripts/check_encoding.py`

```text
text files: 457 invalid UTF-8: [] question sequences: []
```

## WARNING：技术限制

- 实验每组预热 2 次、测量 4 次、重复 3 轮，使用相同随机种子；未完成计划中的 20/200/3 长时间实验。未测量 CPU 利用率和内存峰值，CPU/Gloo 结果不能直接推广到 GPU/NCCL。
- 独立 profiler 使用合成负载且没有预热，梯度桶重建影响事件数；事件累计时间不是完整训练的端到端通信耗时，也未可靠量化计算与通信重叠。本次没有重采样，保留历史数据。
- 本次 Word COM 导出失败：HRESULT 0x80070520（指定的登录会话不存在）；未发现可用 LibreOffice。文档渲染器因缺少 pdf2image 未能启动，页面排版、图片清晰度、空白页及页眉页脚未完成视觉检查。未生成 PDF。
- 本人复现终端日志记录采样及 K=1、2、4、8 验证通过；这些是历史执行记录，本轮未重新运行验证。原始日志和原始实验材料保留。

## MANUAL：本人需要完成

- 插入真实运行截图：采样一致性、K=1/2/4/8 数值验证，以及报告占位要求的环境、双进程训练和 profiler 输出；截图应来自实际运行。
- 核对已根据本人提供材料填写的个人工作和 AI 使用说明。
- 使用 Word 检查标题、表格、图表、分页、页眉页脚与符号；按课程要求导出 PDF。
- 核对老师完整的提交规范、文件格式和是否需要视频或其他材料，再整理提交包。保留的 CIFAR-10 和历史文件是否随包提交由课程规定决定。

## 当前提交状态

自动检查通过，但截图、个人事实和版式检查尚未完成；暂不建议直接提交。
