# Nadia lab: first real-material session

首个时段的实际采集准备，2026-10-20。建议预留5小时，以一块慢回弹开孔PU完成24条完整交叉条件及6条参考锚点；具体动作与时间全部来自预试验和实际设备配置。若复位太慢，按完整12条块续约，不删除条件。尚未采集任何实机数据。

## 直接交给实验员

- [一页英文执行卡 PDF](EXPERIMENTER_CARD_EN.pdf)；[可编辑文本](EXPERIMENTER_CARD_EN.md)。
- [英文首时段计划](FIRST_SESSION_PLAN_EN.md)：设备、5项最少确认信息、校准、预试验、操作顺序、时间估算与交接。
- [中文科学依据与第一批分析](实验设计与首批分析.md)：最新闭环结果如何改变判断、每组数据区分什么机制、数据到达后的处理顺序。
- [随机化30条总表](session_plan/run_order_30.csv)：原24条顺序不变，加入原6个锚点。
- [24条协议](session_plan/protocol_24.csv)；[参数填写表](session_plan/parameter_form.csv)。
- [数据目录模板](session_plan/data)：包括八个核心采样字段、全部尝试清单、元数据、控制/计划/事件及校准表。
- [最少待确认信息表](lab_confirmation.csv)：一次集中填写，不要求新增审批。

**本轮新增：** 时段预算、完整30条执行顺序、参数表到阶段时间与批次模板的生成、逐尝试CSV合并、一页打印卡、对无光学测量复位路线的兼容。原本构模型、单位/时间检查、拟合与绘图脚本从前一个采集包逐字复制；没有新拟合、训练或材料仿真。`source_manifest.json`记录来源哈希。

## 预试验后生成计划

按[安装指南](../../../SETUP.md)建立环境，按[运行手册](../../REPRODUCING.md#p1--prepare-a-material-session)创建工作副本。在副本目录打开 PowerShell：

```powershell
$sessionPython = '..\pilot\.venv\Scripts\python.exe'

# Fill the value and evidence columns first; retain every parameter key.
& $sessionPython session.py build `
  --parameters session_plan\parameter_form.csv `
  --output collection\day1
```

生成`protocol_24.csv`、`run_order_30.csv`、`motion_segments_relative.csv`、`time_budget.json`和`data/`。物理设定冻结为`pretest_frozen.json`；相对轨迹仅用于阶段/耗时核对，没有连接机器人或发送命令。实际设备程序应以本地控制API实现，并记录实际插值、加速度、阶段转换与偏差。

参数表中预约和准备预算已有可修改数值；幅度、速度、等待、复位、参考探针和设备限值全部留空。`reset_method`选择`optical_and_reference`或`reference_washout`；后者允许没有测量的`reset_height_band_m`为空。原始`prepare_collection.py`仍保存旧版接口，**本时段计划使用新的session.py入口**。

`data/metadata.json`另填真实测量单位、坐标变换、标定及时间链；`controller_schedule.csv`记录实际模式与可读参数。未知K/D不能补成仿真数值。`forecast_start_s`及状态栏不会自动使用计划值，必须记录实际撤离起点和实际运行状态。

## 采到即接入

每次实际尝试保存一个含原始列头的CSV，命名可用`session__episode.csv`。原设备文件单独留档。主`episodes.csv`已经列出24条core及6条anchor；重试在表中增加新ID，保留原planned_id。

```powershell
# A complete raw.csv dataset can go directly to inspect.
# Complete metadata and actual episode status before assembly.
& $sessionPython session.py assemble `
  --prepared collection\day1 `
  --recordings recordings\day1 `
  --output data\day1_batch

# Partial batches can be inspected before all 24 records are available.
& $sessionPython first_batch.py inspect data\day1_batch --output runs\day1_inspect
& $sessionPython plot_intake.py runs\day1_inspect --output figures\day1_raw
```

合并器验证字段、ID、试样、基本时间/单位；保留附加列、所有已记录尝试及原始CSV，**不自动判断复位、不自动标记合格、不排序修补样本、不伪造同步或计划可用时间**。未录到的计划条目保留为planned。控制时序表初始只有列头，按真实记录填写；不要用空白数值行充当已执行上下文。

完整24条及必要校准字段齐备后，先测实际拟合成本，再按预定家族比较：

```powershell
& $sessionPython first_batch.py fit runs\day1_inspect --output runs\day1_cost --models L2 --axes wait
& $sessionPython first_batch.py fit runs\day1_inspect --output runs\day1_full
& $sessionPython analysis_core\plot_analysis.py runs\day1_inspect\fit_dataset `
  --results runs\day1_full --output figures\day1_full
```

这一步是**给定实际运动的本构预测**；尚不是未标定机器人上的未来命令预测。不要用事后实际命令冒充提前已知计划。缺少实测数据时不运行拟合。

## 模板含义与保留范围

- `raw.csv`：SI优先；真实位姿、力、命令、阶段；附加原始时钟/序号/可选表面高度。
- `episodes.csv`：每次尝试一行；`include_in_fit`、`reset_verified`、`status`、实际撤离起点由记录填写。anchors已排除核心拟合。
- `planned_commands.csv`：仅填写当时确实已知的未来命令与版本；相对阶段参考表不能自动充当执行证据。
- `events.csv`：实际阶段事件、接触判定、覆盖命令、停止与误差来源。
- `metadata.json`、`calibration_records.csv`、`pretest_observations.csv`：单位、时钟、校准与选参依据。

所有生成目录必须在本项目内，非空目录不会被覆写。要保留不同实际时段/重跑结果，使用新的输出目录。跨日时更新会话与标定记录；若第二个重复块整体跨日，报告重复与日期部分混淆。

`verification/`只保存软件接口检查与复用的旧合成文件，没有新的材料结果。交付ZIP与运行所需源代码都保存在本目录。打印卡由`build_card.py`生成，使用已发现的文档运行环境中的reportlab/pypdf/pypdfium2；采集分析工具不依赖这些排版库。
