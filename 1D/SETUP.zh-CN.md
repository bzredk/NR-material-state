# 安装与运行

这个仓库用来复现实验：读取已保存的数据和权重，计算预测、统计结果并生成图。下载后在本地或计算服务器上运行 Python 脚本即可，没有需要启动的网页服务，也不需要端口、数据库或 API key。

第一次接手，建议先用 CPU 跑通检查，再决定是否重新训练。[英文安装指南](SETUP.md)和[逐实验运行手册](REPRODUCING.md)提供了完整命令。

## 先看目录

| 路径 | 内容 |
| --- | --- |
| `1D/experiments/pilot` | 最初的先导实验 |
| `1D/experiments/history_dependence` | history dependence：当前观测相同，不同历史能否解释后续响应差异 |
| `1D/experiments/controller_transfer/v2` | controller transfer：同一个状态估计能否用于不同的未来控制参数 |
| `1D/experiments/shared_feedback` | shared feedback：加入共同反馈后，历史估计还有多少动作收益 |
| `1D/experiments/lab` | material collection：实物采集计划、参数表、记录合并与分析入口 |
| `1D/experiments/controller` | shared feedback 使用过的控制器和物理代码快照 |
| `1D/experiments/acquisition` | 早期采集工具，供追溯 material collection 的分析代码来源 |
| `1D/diagrams/workflow` | 原实验设计流程图、矢量版本和绘图源码 |
| `1D/presentation` | 10 月 22 日的 12 页汇报 PPT 和 PDF |
| `plans/2d_contact` | 下一步二维接触实验设计，尚未实现 |

日期和原目录名保留在实验记录与来源清单里。`controller_transfer` 顶层保存早期 `transfer_v1`，汇报使用的是 `v2` 子目录里的结果。`lab/verification` 中的样例是合成接口测试数据；目前没有实物测量数据。

## 机器需要什么

使用 64 位 Python 3.11。原实验环境是 Python 3.11.9、PyTorch 2.9.1 + CUDA 12.8、RTX 5070 Ti，显存约 16 GiB。这是当时的配置，没有据此测定最低显存要求。

| 想做的事 | 是否需要 NVIDIA GPU |
| --- | --- |
| 看 PPT、图、CSV 和 JSON 结果 | 不需要，也不用装 Python |
| 校验文件、核对已有结论 | 不需要；这两项只用 Python 标准库 |
| 加载 24 个主要模型做小样本重放、运行正确性测试 | 不需要，CPU 可以运行 |
| 重新训练 history dependence/controller transfer，或运行它们的完整评估入口 | 需要，当前脚本使用 CUDA |
| 根据已有轨迹重算 shared feedback 统计和图片 | 不需要 |
| 从头重算 shared feedback 的冻结编码和轨迹 | 编码准备阶段需要 CUDA，后续动力学在 CPU/Numba 上运行 |
| material collection 排计划、合并记录、检查和拟合材料数据 | 不需要 |

仓库工作文件约 650 MB，数据和权重随 Git 一起下载。建议先留约 10 GB 空间给 Git、环境、下载缓存和工作副本；这是使用上的预留量，并非实测最低要求。多次训练会继续占用空间。训练耗时和显存以自己机器生成的 `profile.json` 为准。

## Windows：从下载到跑通检查

先安装 [Git](https://git-scm.com/downloads/win) 和 [64 位 Python 3.11](https://www.python.org/downloads/release/python-3119/)，再打开一个新的 PowerShell 窗口。下面的命令在你打算存放项目的父目录执行。如果已经下载，直接进入仓库，跳过 `git clone`。

### 1. 建立项目环境

```powershell
git --version
py -3.11 --version
git clone https://github.com/bzredk/NR-material-state.git
Set-Location NR-material-state
py -3.11 -m venv .venv
$env:Path = (Join-Path (Get-Location) '.venv\Scripts') + ';' + $env:Path
python -c "import sys; print(sys.executable); print(sys.version)"
python -m pip install --upgrade pip
python -m pip install -r '1D/requirements.txt'
```

打印出的 Python 路径应以 `NR-material-state\.venv\Scripts\python.exe` 结尾。如果机器没有 `py` 命令，但 `python --version` 显示 3.11，可以用 `python -m venv .venv` 创建环境。

这里把环境路径加入当前终端的 PATH，后续进入实验目录仍能使用同一个 `python`。这个修改只影响当前终端，不需要改变全局 PATH 或 PowerShell 执行策略。[Python 文档](https://docs.python.org/3.11/library/venv.html)也说明了直接使用虚拟环境解释器的方式。

### 2. 选择 CPU 或 CUDA

只查看和检查结果，安装 CPU 版：

```powershell
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu
```

准备跑完整实验，先确认显卡驱动正常，再安装 CUDA 版：

```powershell
nvidia-smi
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
```

这两组命令选择一组。GPU 路线需要对应 wheel 支持的显卡和可用驱动；如果 `nvidia-smi` 都不能识别设备，先处理驱动或计算节点的 GPU 分配。安装来源是 [PyTorch 官方 2.9.1 版本表](https://pytorch.org/get-started/previous-versions/#v291)，项目不使用 `torchvision` 或 `torchaudio`。

如果已经装了 CPU 版，后来需要切换到 GPU，显式替换：

```powershell
python -m pip uninstall -y torch
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
```

### 3. 检查环境

回到仓库根目录执行：

```powershell
python -m pip check
python '1D/tools/check_environment.py'
```

应看到 `No broken requirements found` 和 `"status": "passed"`。检查脚本会导入依赖，执行一个小型张量计算和 Numba 计算，并打印解释器路径与包版本。CPU 环境的 `cuda.available` 为 `false` 是正常结果。

使用 GPU 时再加一项：

```powershell
python '1D/tools/check_environment.py' --require-cuda
```

这里通过才说明当前 Python 环境能完成 CUDA 计算。安装完成不等于程序一定能访问 GPU。

以后重新开终端，先进入仓库根目录，再执行下面两行，无需重复安装：

```powershell
$env:Path = (Join-Path (Get-Location) '.venv\Scripts') + ';' + $env:Path
python -c "import sys; print(sys.executable)"
```

## Linux 或远程计算服务器

先在服务器准备 Git、64 位 Python 3.11 和匹配的 `venv` 支持。如果创建环境时提示缺少 `ensurepip`，安装该发行版中对应 Python 3.11 的 venv 包。包名由发行版决定。

在 Bash 中执行：

```bash
git clone https://github.com/bzredk/NR-material-state.git
cd NR-material-state
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r '1D/requirements.txt'
```

接着选择 CPU 版：

```bash
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu
```

或者 NVIDIA CUDA 版：

```bash
nvidia-smi
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
```

无图形界面的服务器设置 Matplotlib 后端，再检查环境：

```bash
export MPLBACKEND=Agg
python -m pip check
python '1D/tools/check_environment.py'
```

GPU 作业还要执行 `python '1D/tools/check_environment.py' --require-cuda`。集群上应在已经分配 GPU 的作业中检查，登录节点可能看不到显卡。每次重新 SSH 连接，都需要在仓库根目录重新执行 `source .venv/bin/activate`。长任务使用所在平台的作业调度器或已有的终端会话管理工具，并保留控制台日志。

本次安装验证使用 Windows 的全新 CPU 环境；原实验使用 Windows/CUDA。Linux 命令对应同一套脚本，但本次没有在 Linux 上重新训练。当前说明不覆盖 macOS/MPS 或 ROCm 训练。

## 先核对已有结果

在仓库根目录执行，路径中的空格必须保留引号：

```sh
python "1D/tools/verify_bundle.py"
python "1D/tools/check_results.py"
python "1D/tools/replay_checkpoints.py"
```

第一项应报告 `passed`、12 页幻灯片和 PNG/SVG/PDF 三种流程图格式；它核对当前文件的 SHA-256。第二项核对 24 次主要训练的收敛记录、shared feedback 使用的六个冻结模型及 history dependence/controller transfer/shared feedback 的保存结果。第三项分 history dependence、controller transfer 输出，每组应显示 `checkpoints_replayed: 12`，预测形状正确且没有非有限值。

CPU 重放用于确认权重能加载、前向计算能执行，并报告它与 CUDA 存档的差异。递归预测会积累不同后端的数值误差；本次小样本检查中，history dependence 最大力差约 0.00252 N。因此 CPU 输出标记为 `cpu_diagnostic_only`，不能据此声称与原结果数值一致。CUDA 模式仍执行原来的严格容差；需要强制设备时使用 `--device cpu` 或 `--device cuda`，也可用 `--device cpu --strict-archive` 明确要求 CPU 满足同一严格容差。

正确性测试分三次执行：

```sh
python -m pytest -q "1D/experiments/pilot/test_pilot.py"
python -m pytest -q "1D/experiments/history_dependence/test_round2.py" "1D/experiments/history_dependence/test_intake.py"
python -m pytest -q "1D/experiments/controller_transfer/v2/test_core.py"
```

预期分别通过 5、9、8 项，共 22 项。几个独立实验使用了相同模块名，不能在一个 pytest 进程中收集整个仓库。

## 从哪一步开始复现

运行脚本前先复制相应实验。以 history dependence 为例，在仓库根目录执行：

```sh
python "1D/tools/workcopy.py" --experiment history-dependence --destination reproductions/history-dependence
cd reproductions/history-dependence
python experiment.py evaluate --output runs/round2_v1
```

最后一行需要 CUDA，会在副本中重新评估已保存的模型。输出位于副本的 `runs/round2_v1`。如果要从头训练，在副本中使用新的输出名：

```sh
python experiment.py prepare --output runs/replication
python experiment.py train --output runs/replication
python experiment.py evaluate --output runs/replication
python numerical_audit.py --output runs/replication
```

每步成功结束后再运行下一步。训练中断后使用 `python experiment.py train --resume --output runs/replication`，无需重新生成数据。

其他实验的完整流程见[运行手册](REPRODUCING.md)：

- **controller transfer：** 工作副本进入 `v2` 后运行。输出固定为 `runs/transfer_v2`，修改配置里的名称不会改变目录。开始新训练前必须按手册移走副本中的旧运行，否则已收敛模型会被跳过。
- **shared feedback：** `analyze.py`、`plot_results.py`、`finalize.py` 可以在 CPU 上利用现成轨迹重算统计和图；完整重算先运行 `bridge.py prepare/profile/actions/diagnostic` 四个阶段，其中准备阶段需要 CUDA。不要重新运行历史初始化工具 `bootstrap.py`。
- **material collection：** 复制为 `reproductions/lab`，先运行 `verify_session.py` 检查合成接口，再用 `session.py init` 建立空表。实际设备参数来自校准和预试验，填表后才运行 `session.py build`。采集后按 `assemble → inspect → plot → fit` 的顺序处理，先检查数据是否适合拟合。

`reproductions/` 和 `.venv/` 都在 Git 忽略列表里。保留原存档作为参照，新运行另外保存 Git commit、`pip freeze`、配置、随机种子、控制台日志和结果。更改训练预算、数据规模或物理设置后，应把它作为一项新的运行记录。

## 常见问题

| 现象 | 处理方法 |
| --- | --- |
| 装完仍提示缺少模块 | 打印 `sys.executable`，确认正在使用仓库 `.venv`；安装统一使用这个解释器的 `python -m pip`。 |
| 提示需要 CUDA | history dependence/controller transfer 完整入口依赖 GPU，history dependence 的 `evaluate` 也一样。CPU 检查使用 `tools/replay_checkpoints.py`。 |
| 有显卡但 CUDA 不可用 | 依次检查 `nvidia-smi`、PyTorch 是否为 CPU 版、作业是否分配了 GPU。 |
| 依赖冲突或找不到 wheel | 确认 Python 3.11、64 位、独立环境，按固定版本安装；不要只升级现有环境里的 NumPy。 |
| controller transfer 训练很快结束 | 检查旧模型是否已标记 `converged`，按新训练流程处理副本中的旧输出。 |
| 评估拒绝运行 | 查看 `logs/*_meta.json`，达到步数上限不等于达到验证收敛标准；按记录续训或报告未收敛。 |
| 目标目录已存在 | 换一个工作副本或输出名，避免混入上一次记录。 |
| 文件哈希不匹配 | 检查是否在原存档内运行或修改过文件；使用新克隆恢复参照，不要修改哈希掩盖差异。 |
| 找不到文件或输出路径被拒绝 | 核对当前目录、路径引号；history dependence 和 material collection 要求输出留在各自的工作副本里。 |
| 服务器绘图失败 | 设置 `MPLBACKEND=Agg`；若只是字体样式不同，检查 Arial 是否存在。 |

需要别人协助排查时，附上运行命令、起始目录、完整错误、Git commit 和 `check_environment.py` 输出。重新导出 material collection 打印卡才需要额外安装 `reportlab`、`pypdfium2`；查看仓库里的 PDF 不需要这些依赖。
