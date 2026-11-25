"""Run local acceptance checks and write FINAL_AUDIT.md without changing experiment data."""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

root = Path(__file__).resolve().parents[2]
env = os.environ.copy()
env.update(PYTHONUTF8='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
checks = [('正确性验证', 'code/src/verify.py', 180),
          ('采样一致性', 'code/src/check_sampler.py', 90),
          ('原始数据与汇总', 'code/scripts/check_final.py', 60),
          ('报告、路径和文件完整性', 'code/scripts/check_report.py', 60),
          ('编码', 'code/scripts/check_encoding.py', 90)]
sections = []
failed = False
for name, script, timeout in checks:
    print('RUN:', name, flush=True)
    try:
        p = subprocess.run([sys.executable, script], cwd=root, env=env, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=timeout)
        output = (p.stdout + p.stderr).strip()
        status = 'PASS' if p.returncode == 0 else 'FAIL'
        failed |= p.returncode != 0
    except subprocess.TimeoutExpired as e:
        output = f'超过 {timeout} 秒，未完成。'
        status = 'WARNING'
        failed = True
    sections.append(f'### {status}：{name}\n\n命令：`python {script}`\n\n```text\n{output}\n```')
    print(status, name, flush=True)

body = f'''# D1 最终验收报告

生成时间：{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}。运行环境：`{sys.executable}`。

## 本次修改

- `report/51290713112_高洁_D1.docx`：补充计时口径、B/C 组解释与限制；个人经历保留待本人填写。原报告备份为 `history/51290713112_高洁_D1.before_audit.docx`。
- `code/configs/default.yaml`：区分实际 2/4/3 和未执行的计划 20/200/3；配置仅供说明，运行脚本不读取它。
- `code/requirements.txt`：按 ddp-lab 中 pip freeze 的直接依赖固定版本；CPU 版 PyTorch 的可用安装源取决于环境。
- `code/README.md`：说明实际配置、计划配置、资源差异和同步计数口径。
- `code/scripts/check_report.py`：检查章节、身份、统计、图表、占位、README Markdown 链接和关键数据；原脚本及配置、依赖文件分别保留 .bak 备份。
- `code/scripts/final_audit.py`：运行检查并生成本报告；`update_report_audit.py` 记录报告修改方法，不应在当前报告上重复运行。
- 未修改训练算法、既有实验原始数据、日志、profiler 记录或汇总；未删除历史材料，也未提交或推送 Git。

## 本次自动检查

{chr(10).join(sections)}

## WARNING：技术限制

- 实验每组预热 2 次、测量 4 次、重复 3 轮，使用相同随机种子；未完成计划中的 20/200/3 长时间实验。未测量 CPU 利用率和内存峰值，CPU/Gloo 结果不能直接推广到 GPU/NCCL。
- 独立 profiler 使用合成负载且没有预热，梯度桶重建影响事件数；事件累计时间不是完整训练的端到端通信耗时，也未可靠量化计算与通信重叠。本次没有重采样，保留历史数据。
- 本次 Word COM 导出失败：HRESULT 0x80070520（指定的登录会话不存在）；未发现可用 LibreOffice。文档渲染器因缺少 pdf2image 未能启动，页面排版、图片清晰度、空白页及页眉页脚未完成视觉检查。未生成 PDF。
- 历史验证记录 `results/final/verification_all_k.log` 和 `results/sampler_verification.log` 保持不变。上面的检查输出是本次执行结果；历史记录并不代表本次运行。

## MANUAL：本人需要完成

- 插入真实运行截图：采样一致性、K=1/2/4/8 数值验证，以及报告占位要求的环境、双进程训练和 profiler 输出；截图应来自实际运行。
- 在报告中据实填写本人修改与验证、独立完成的工作，核对 AI 使用说明。
- 使用 Word 检查标题、表格、图表、分页、页眉页脚与符号；按课程要求导出 PDF。
- 核对老师完整的提交规范、文件格式和是否需要视频或其他材料，再整理提交包。保留的 CIFAR-10 和历史文件是否随包提交由课程规定决定。

## 当前提交状态

{'自动检查有失败或超时，需先处理。' if failed else '自动检查通过，但截图、个人事实和版式检查尚未完成；暂不建议直接提交。'}
'''
(root/'FINAL_AUDIT.md').write_text(body, encoding='utf-8')
print('Wrote FINAL_AUDIT.md', flush=True)
raise SystemExit(1 if failed else 0)
