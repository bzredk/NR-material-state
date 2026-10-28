import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../../..');
const SKILL = 'C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/presentations/26.1017.22136/skills/presentations';
const PYTHON = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
process.env.RUNTIME_NODE_MODULES = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const { finalizePresentation, applyPresentationChartFont } = await import(pathToFileURL(path.join(SKILL, 'container_tools/artifact_tool_utils.mjs')));
const D = JSON.parse(await fs.readFile(path.join(HERE, 'assets/slide_data.json'), 'utf8'));
const OUT = path.join(HERE, 'output');
const BUILD = path.join(HERE, '.build');
await fs.mkdir(path.join(BUILD, 'slides'), { recursive: true });
await fs.mkdir(OUT, { recursive: true });
const p = Presentation.create({ slideSize: { width: 1600, height: 900 } });
p.theme.defaultFont = 'Arial';
const C = { ink: '#222426', gray: '#656A70', light: '#DADDE0', blue: '#2866AB', orange: '#C27838', teal: '#178479', pale: '#F3F5F6', black: '#111111' };
const RUN = '2D/runs/information/channels_contact_20261026';
const S = [];

function text(s, value, x, y, w, h, size = 28, color = C.ink, bold = false) {
  const t = s.shapes.add({ geometry: 'textbox', position: { left: x, top: y, width: w, height: h }, fill: 'none', line: { fill: 'none', width: 0 } });
  t.text = value;
  t.text.style = { typeface: 'Arial', fontSize: size, color, bold, insets: 0, verticalAlignment: 'top', wrap: 'square' };
  return t;
}
function slide(title, caption = '') {
  const s = p.slides.add(); s.background.fill = '#FFFFFF';
  text(s, title, 96, 60, 1410, 60, 32, C.ink, true);
  if (caption) text(s, caption, 96, 132, 1410, 65, 25, C.gray);
  text(s, String(p.slides.items.length).padStart(2, '0'), 1488, 856, 44, 24, 14, C.gray);
  return s;
}
function notes(s, title, zh, evidence) {
  const n = p.slides.items.indexOf(s) + 1;
  const source = `Sources (relative to the repository):\n${evidence.join('\n')}`;
  s.speakerNotes.text = `${zh}\n\n${source}`;
  S.push({ number: n, title, speaking_notes_zh: zh, sources: evidence });
}
function footer(s, value) { text(s, value, 96, 817, 1360, 31, 18, C.gray); }
function table(s, values, x, y, widths, rowHeight = 92, size = 26) {
  const t = s.tables.add({ rows: values.length, columns: values[0].length, left: x, top: y, width: widths.reduce((a,b) => a+b,0), height: values.length * rowHeight, columnWidths: widths, values });
  t.borders.assign({ fill: '#FFFFFF', width: 0 });
  for (let r=0;r<values.length;r++) {
    t.rows[r].height = rowHeight;
    for (let c=0;c<values[0].length;c++) {
      const cell=t.getCell(r,c); cell.fill='#FFFFFF';
      cell.text.style={ typeface:'Arial',fontSize:size,color:r===0?C.gray:C.ink,bold:r===0,insets:{top:8,bottom:8,left:10,right:18},verticalAlignment:'middle'};
    }
  }
  return t;
}
function series(name, xs, ys, color, marker='none', width=3) {
  // Eight significant digits preserve the plot while fitting Excel's numeric precision.
  const chartNumber=v=>Number(v.toPrecision(8));
  return {name, xValues:xs.map(chartNumber), values:ys.map(chartNumber), smooth:false, fill:color, line:{fill:color,width,style:'solid'}, marker:{symbol:marker,size:7,fill:color}};
}
function scatter(s, pos, lines, options={}) {
  const ch=s.charts.add('scatter',{
    position:pos,series:lines,scatterOptions:{style:'lineWithMarkers'},hasLegend:false,
    chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',chartLine:{fill:'none',width:0},
    xAxis:{min:0,max:1,majorUnit:.2,numberFormatCode:'0.0',tickLabelPosition:'low',textStyle:{fontSize:21,fill:C.gray},line:{fill:C.gray,width:1},majorGridlines:null,...options.xAxis},
    yAxis:{textStyle:{fontSize:21,fill:C.gray},line:{fill:C.gray,width:1},majorGridlines:{fill:'#ECEEEF',width:1},...options.yAxis},
    ...options.config,
  });
  applyPresentationChartFont(ch,{fontFamily:'Arial'}); return ch;
}
const mean=(m,a='Slow press')=>D.summary.means.find(x=>x.method===m&&x.action===a).mean_force_rmse_mN;
const contrast=(b,a)=>D.summary.contrasts.find(x=>x.before===b&&x.after===a&&x.action==='Slow press');
const mNames={'basic_0.0':'Current motion + force','lateral_0.0':'Current + lateral shape','basic_0.8':'0.8 s motion + force','lateral_0.8':'0.8 s + lateral shape','truth':'True response'};
const mColors={'basic_0.0':C.gray,'lateral_0.0':C.blue,'basic_0.8':C.orange,'lateral_0.8':C.teal,'truth':C.black};

// 01. Minimal cover, matching the reference's white canvas and type.
{
 const s=slide('Object state between contacts');
 text(s,'Second-week research report',96,166,1100,48,28,C.gray);
 text(s,'What does current shape reveal,\nand what does interaction history add?',96,276,1390,140,44,C.ink,true);
 text(s,'Spatial 2D contact with fast and slow internal relaxation',96,474,1320,55,30);
 text(s,'The current shape carries substantial information.\nContact and recovery history reduce the remaining prediction error.',96,593,1310,104,30,C.gray);
 footer(s,'28 October 2026');
 notes(s,'Object state between contacts','这周我把上次的一维接触扩展成了真正的空间二维模型。研究主题仍然是物体隐藏状态，而不是材料本构本身。本轮集中回答两个问题：当前侧向形变已经告诉了我们多少信息，以及历史的价值来自多长时间，还是来自其中的接触与恢复过程。',[
 `${RUN}/RESULTS.md`, 'Reference design: 10_1.pdf, 12 pages, Arial, 1600 x 900 px equivalent. Source PDF is retained unchanged.'
 ]);
}
// 02. Continuity and exact limits of the earlier work.
{
 const s=slide('What changed since the first report');
 table(s,[['First report','This week'],
 ['1D motion with two internal variables','Spatial 2D FEM with lateral deformation'],
 ['History predicts different future responses','Separate current shape from additional history'],
 ['A short classical observer can already work well','Separate waiting time from informative contact data'],
 ['Shared feedback gave little extra action benefit','Keep action benefit as a separate, unfinished test']],96,174,[640,768],100,28);
 text(s,'The meeting feedback motivated the 2D contact and lateral-response test.',96,713,1390,46,28,C.ink,true);
 footer(s,'The 2D-to-3D and lateral-response feedback comes from the recorded meeting recap.');
 notes(s,'What changed since the first report','上周的三个判断保留：历史能帮助预测，状态可以用于不同未来控制，但共同反馈下的动作收益很小。经典估计器也已经很强。这周没有假设长历史或者神经网络必须获胜，而是把空间形变和传感信息加进去。关于老师反馈，2D到3D和侧向变化来自会后中文录音复述，现场英文片段只支持回到网格图和单指例子，不能说老师指定了某个算法。',[
 '1D/RESULTS.md','1D/PRESENTATION_MAP.md',`${RUN}/RESULTS.md`,
 'Meeting source: D:/capp/NR/Documents/Codex/2026-10-23-project-feedback/项目反馈总结与转录.md (A 00:00.5-00:06; C 00:08-00:15.8).'
 ]);
}
// 03. Reuse the actual solver figure, not a schematic of a soft object.
{
 const s=slide('A spatial body produces the force and lateral response','Fixed bottom, free sides, one round rigid indenter. The deformation comes from the FEM solution.');
 s.images.add({blob:await fs.readFile(path.join(ROOT,'2D/runs/2d_contact/pilot_c9dd23016896/figures/01_spatial_process.png')),contentType:'image/png',alt:'Recorded spatial FEM mesh, contact reaction, commanded and actual tool motion, and lateral marker motion',fit:'contain',position:{left:92,top:196,width:1416,height:600}});
 footer(s,'Recorded 2D pilot. Synthetic material. Quasistatic body with a dynamic tool. Deformation shown at 1x scale.');
 notes(s,'A spatial body produces the force and lateral response','先看物理过程。底边固定，侧边自由，压头加载、保持、释放、等待，再接触。右侧分别记录实际接触力、命令与实际运动、两侧标记点。脱离接触后力回到零，但侧向形变仍在恢复。这里沿用已经验证过的空间2D演示图，后面统计来自新的24条历史。材料参数是合成参数，物体采用准静态平衡，压头保留动力学，尚未做真实材料标定。',[
 '2D/runs/2d_contact/pilot_c9dd23016896/figures/01_spatial_process.json',`${RUN}/physics.json`,'2D/src/nr2d/physics.py'
 ]);
}
// 04. State, observation, and inference are different objects.
{
 const s=slide('The physical state contains more than the current measurement');
 text(s,'Physical state',96,176,600,50,30,C.ink,true);
 text(s,'Fast and slow internal strain fields\nTool position and velocity',96,245,640,108,31);
 text(s,'Relaxation times: 0.12 s and 0.90 s\nEquilibrium determines deformation and contact.',96,393,640,96,26,C.gray);
 text(s,'Available observation',824,176,680,50,30,C.ink,true);
 text(s,'Tool position, velocity and total force\nOptional left/right lateral displacement',824,245,680,108,31);
 text(s,'During detached waiting, force is zero.\nLateral shape still changes during recovery.',824,393,680,96,26,C.gray);
 text(s,'Classical state estimate',96,568,1250,50,30,C.ink,true);
 text(s,'Fit six nonnegative coefficients for the two internal fields.\nPropagate the estimate with the same FEM and a future command.',96,635,1370,110,30);
 footer(s,'The estimate is a restricted physical representation. Current shape alone is not a sufficiency proof.');
 notes(s,'The physical state contains more than the current measurement','完整状态包括快慢内部应变场和压头位置速度。在已知参数的模型中，这些状态足以向前推进。机器人获得的瞬时测量只是位置、速度、总力和可选的两侧位移。我们用同一个经典观察器，在三个弹性基底上拟合快慢两个场，共六个非负系数。它是完整内部场的近似。当前形变很有信息，但还不能直接把它等同于对未来充分的状态。',[
 '2D/src/nr2d/estimators.py',`${RUN}/physics.json`,`${RUN}/test/test_5000/repeat_0/result.json`
 ]);
}
// 05. Native table for information conditions.
{
 const s=slide('The comparison changes only the available information','Same physical histories, prediction time, future solver and observed noise draw.');
 table(s,[['Information','Motion + force','Motion + force + lateral shape'],
 ['Current sample','Position, velocity, total force','The same sample plus two lateral markers'],
 ['Recent history','The same channels over 0.2 or 0.8 s','The same window plus lateral history']],96,218,[300,500,608],108,26);
 text(s,'24 independent loading histories',96,606,680,46,30,C.ink,true);
 text(s,'Three noise draws per history.\nHistory, rather than noise draw, is the statistical unit.',96,664,680,92,26);
 text(s,'Three separate calibration histories',824,606,680,46,30,C.ink,true);
 text(s,'Equal tuning budgets select one shared preset.\nEstimate once, then predict Slow and Fast press.',824,664,680,92,26);
 footer(s,'Prediction starts at 1.40 s. Disabled channels are absent from both initialization and fitting.');
 notes(s,'The comparison changes only the available information','所有方法使用相同的物理历史和同一份噪声观测，只屏蔽通道，关闭侧向后它不能继续用于初始化或拟合。三条校准历史选超参数，24条新测试历史各有三次独立噪声。统计单位是完整历史，不能把72次噪声重复当72个独立物体。同一状态估计直接用于慢压和快压，快压不参与调参。真实内部场和已知松弛初态的完整重放只作为特权参考。',[
 `${RUN}/study.json`,`${RUN}/calibration.json`,`${RUN}/verification/data_contract.json`,'2D/tests/test_observer_config.py'
 ]);
}
// 06. Editable time-series charts from a prespecified example.
{
 const s=slide('The same future command exposes different prediction errors','First prespecified test history, noise draw 0, Slow press. History conditions use the recent 0.8 s.');
 const a=D.example.actions[0];
 const keys=['basic_0.0','lateral_0.0','basic_0.8','lateral_0.8','truth'];
 keys.forEach((m,i)=>text(s,mNames[m],96+i*282,207,270,42,22,mColors[m],true));
 text(s,'Contact force (mN)',96,276,640,37,25,C.ink,true);
 text(s,'Prediction error (mN)',824,276,640,37,25,C.ink,true);
 scatter(s,{left:84,top:329,width:690,height:406},keys.map(m=>series(mNames[m],a.seconds,a.methods[m].force_mN,mColors[m], 'none',m==='truth'?2:3)),{yAxis:{min:0,max:220,majorUnit:50}});
 scatter(s,{left:812,top:329,width:690,height:406},keys.filter(m=>m!=='truth').map(m=>series(mNames[m],a.seconds,a.methods[m].error_mN,mColors[m])),{yAxis:{min:-5,max:20,majorUnit:5}});
 text(s,'Time after prediction start (s)',220,753,480,38,23,C.gray);
 text(s,'Time after prediction start (s)',948,753,480,38,23,C.gray);
 footer(s,'All predictions start from the same observed tool state. Future achieved motion is not supplied to the estimator.');
 notes(s,'The same future command exposes different prediction errors','左图是同一慢压命令下的力曲线，右图把预测减去真实响应。当前运动和总力最容易失去恢复信息，加上侧向形变后已经明显改善。0.8秒历史进一步靠近真实曲线。这个例子固定取测试编号5000的第一次噪声，不按未来误差挑选。总体结论要看后面的24条完整历史。',[
 `${RUN}/test/test_5000/repeat_0/curves.npz`,`${RUN}/figures/01_information_curves.json`
 ]);
}
// 07. Current lateral information, with an explicit paired effect.
{
 const s=slide('Current lateral shape carries substantial predictive information','Force RMSE for Slow press, averaged within history and then across 24 histories.');
 const ch=s.charts.add('bar',{
   position:{left:100,top:249,width:820,height:456},categories:['Current motion + force','Current + lateral shape'],
   series:[{name:'Force RMSE',values:[mean('basic_0.0'),mean('lateral_0.0')].map(v=>Number(v.toFixed(7))),fill:C.blue,points:[{idx:0,fill:C.gray},{idx:1,fill:C.blue}]}],
   hasLegend:false,barOptions:{direction:'column',grouping:'clustered',gapWidth:160},chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',
   xAxis:{textStyle:{fontSize:24,fill:C.ink},majorGridlines:null,line:{fill:C.gray,width:1}},
   yAxis:{min:0,max:14,majorUnit:2,numberFormatCode:'0',textStyle:{fontSize:22,fill:C.gray},majorGridlines:{fill:'#ECEEEF',width:1}},
   dataLabels:{showValue:true,numberFormatCode:'0.00',position:'outEnd',textStyle:{fontSize:27,bold:true,fill:C.ink}},
 }); applyPresentationChartFont(ch,{fontFamily:'Arial'});
 text(s,'Force RMSE (mN)',110,206,720,40,25,C.ink,true);
 text(s,'9.31 mN',1010,310,480,74,52,C.blue,true);
 text(s,'paired reduction in error',1010,405,470,46,29);
 text(s,'95% interval: 7.06 to 11.57 mN',1010,474,460,80,27,C.gray);
 text(s,'Shape exposes recovery\nwhile contact force is zero.',1010,605,470,105,29,C.ink,true);
 footer(s,'Both lateral markers share one underlying mode in this symmetric model. Their measurement noise is independent.');
 notes(s,'Current lateral shape carries substantial predictive information','24条历史上，只有当前运动和力的误差是11.50毫牛，加上当前侧向形变后降到2.20毫牛。配对改善9.31毫牛，按完整历史bootstrap的95%区间是7.06到11.57。它说明当前侧向信息不能忽略。不过对称模型的左右标记实际上反映同一个形变模式，不能把两个标记当成两个独立物理自由度。',[
 `${RUN}/summary.json`,`${RUN}/metrics.csv`,'Intervals: 2,000 whole-history bootstrap resamples, pointwise exploratory 95% intervals.'
 ]);
}
// 08. Exact update and propagation intervals, shown as a native data chart.
{
 const s=slide('The recent 0.2 s contains waiting, while earlier data contain contact','Example history: load to 0.36 s, hold to 0.84 s, release to 1.10 s, wait to 1.40 s.');
 text(s,'Observed contact force (mN)',96,210,1000,40,25,C.ink,true);
 scatter(s,{left:84,top:265,width:1412,height:242},[
   series('Observed force',D.history.seconds,D.history.force_mN,C.gray),
   series('Contact threshold',[0,1.4],[4.5,4.5],C.orange,'none',2),
 ],{xAxis:{max:1.4,majorUnit:.2},yAxis:{min:-10,max:200,majorUnit:50}});
 table(s,[['Estimator input','Observation update','Propagation','Contact duration'],
 ['Recent wait','1.20-1.40 s','None','0 s'],
 ['Recent 0.8 s','0.60-1.40 s','None','0.32 s'],
 ['Earlier contact','0.72-0.92 s','0.92-1.40 s','0.20 s']],96,543,[380,350,350,328],58,23);
 footer(s,'Contact selection uses observed force > 4.5 mN and scans prior force. The contact method spans 0.68 s of motion here.');
 notes(s,'The recent 0.2 s contains waiting, while earlier data contain contact','这是本轮最重要的设计修正。最后0.2秒全是脱离接触后的等待，不能和一维里的接触窗口直接作同条件解释。我们另外找更早的连续0.2秒接触片段，仅由观测力超过4.5毫牛识别，拟合后用实际运动记录传播到当前。以这条历史为例，0.72到0.92秒更新，再传播0.48秒，总运动跨度0.68秒。选择片段还扫描了之前的力，因此不能叫只使用0.2秒历史。',[
 `${RUN}/coverage.json`,`${RUN}/histories/test_5000.npz`,`${RUN}/test/test_5000/repeat_0/curves.npz`
 ]);
}
// 09. Window length and contact content, sharing the physical model.
{
 const s=slide('History helps when it includes informative observations','Mean Slow-press force RMSE. The nominal-noise result uses all 24 independent histories.');
 text(s,'Recent window',96,207,630,40,27,C.ink,true);
 text(s,'Earlier contact plus propagation',824,207,660,40,27,C.ink,true);
 scatter(s,{left:84,top:280,width:690,height:398},[
   series('Without lateral',[0,.2,.8],[mean('basic_0.0'),mean('basic_0.2'),mean('basic_0.8')],C.gray,'circle'),
   series('With lateral',[0,.2,.8],[mean('lateral_0.0'),mean('lateral_0.2'),mean('lateral_0.8')],C.blue,'circle'),
 ],{xAxis:{max:.8,majorUnit:.2},yAxis:{min:0,max:14,majorUnit:2}});
 text(s,'Force RMSE (mN)',110,253,520,32,23,C.gray);
 text(s,'Window duration (s)',280,701,400,35,24,C.gray);
 text(s,'Without lateral',105,754,320,36,25,C.gray,true);
 text(s,'With lateral',465,754,290,36,25,C.blue,true);
 table(s,[['Channels','Recent wait','Earlier contact'],['Without lateral','12.75 mN','0.48 mN'],['With lateral','1.29 mN','0.39 mN']],824,284,[250,210,210],100,24);
 text(s,'Current lateral: 2.20 mN\nRecent lateral wait: 1.29 mN\nRecent 0.8 s with lateral: 0.23 mN',834,642,655,118,27,C.blue);
 footer(s,'Recovery dynamics and noise averaging both may help. Contact and duration are not completely disentangled.');
 notes(s,'History helps when it includes informative observations','只看力的等待窗口没有有效更新，误差仍然很大。加入侧向后，0.2秒等待也有增益，说明恢复过程有信息，同时重复测量降噪也可能贡献。0.8秒包含接触，误差降到0.23毫牛。更早的接触片段再传播，也明显优于近期等待。我们还不能把全部改善都归因于接触，因为它使用了更长运动跨度。新批次里带侧向短历史的改善，也限制了旧8条测试中“噪声使短窗变差”的适用范围。',[
 `${RUN}/summary.json`,`${RUN}/RESULTS.md`,`${RUN}/coverage.json`,'2D/runs/2d_contact/pilot_c9dd23016896/RESULTS.md'
 ]);
}
// 10. Same estimate across actions, not policy performance.
{
 const s=slide('The same estimate also predicts a faster press','No refitting on the future action. Slow press alone selects the calibration preset.');
 table(s,[['Information used','Slow press','Fast press'],
 ['Current + lateral shape',mean('lateral_0.0').toFixed(2),mean('lateral_0.0','Fast press').toFixed(2)],
 ['Recent 0.2 s + lateral shape',mean('lateral_0.2').toFixed(2),mean('lateral_0.2','Fast press').toFixed(2)],
 ['Earlier contact + propagation, with lateral',mean('lateral_contact').toFixed(2),mean('lateral_contact','Fast press').toFixed(2)],
 ['Recent 0.8 s + lateral shape',mean('lateral_0.8').toFixed(2),mean('lateral_0.8','Fast press').toFixed(2)]],96,213,[900,254,254],101,29);
 text(s,'The estimate transfers across these two future commands.',96,748,1400,49,31,C.ink,true);
 footer(s,'Units: mN force RMSE. This is prediction reuse. The 2D study has not yet tested improvement in closed-loop actions.');
 notes(s,'The same estimate also predicts a faster press','每次历史估计只做一次，慢压和快压使用完全相同的估计状态，运行记录用哈希核对过。快压没有参与校准。两种动作下的排序接近，0.8秒侧向历史的误差分别约0.23和0.21毫牛。这支持在这两种命令之间复用估计，但不能把它解释成跨任务普遍充分，也不能解释成闭环动作收益。',[
 `${RUN}/summary.json`,`${RUN}/verification/data_contract.json`,'Estimated-state hashes are identical across the two future branches.'
 ]);
}
// 11. Negative results and gaps drive the next mechanism.
{
 const s=slide('The classical observer is accurate, but repeated fitting is costly');
 table(s,[['Recorded result','What it changes'],
 ['0.23 mN with the recent 0.8 s and lateral sensing','A neural model has no demonstrated accuracy gap to fill.'],
 ['27.24 s median inference for that window','A recursive update should avoid refitting the same past.'],
 ['201 of 576 fits reached the evaluation limit','Optimization status and update cost need separate checks.'],
 ['All 72 force-only wait fits retained the initial coefficients','Waiting force cannot supply the missing state information.']],96,177,[740,668],100,27);
 text(s,'The current estimate has no uncertainty and uses a restricted six-coefficient basis.',96,713,1400,72,29,C.ink,true);
 footer(s,'Timing is measured during an eight-worker CPU batch. Accurate simulation prediction does not imply real-time control.');
 notes(s,'The classical observer is accurate, but repeated fitting is costly','经典方法在接触数据足够时已经很准，所以这轮不能自然推出必须上RNN或JEPA。真正显露的问题是每次从头拟合很慢，0.8秒带侧向窗口在八进程批量下中位耗时27.24秒，而且没有不确定性。201次有限窗拟合触及七次函数评估上限。没有侧向的等待拟合全部停在初值附近，因此当前和短窗的误差差异还混合了先验放在哪个时刻、如何传播的影响，不能说历史本身有害。',[
 `${RUN}/summary.json`,`${RUN}/failures.json`,`${RUN}/RESULTS.md`,'2D/src/nr2d/estimators.py'
 ]);
}
// 12. A bounded next experiment and the robot route.
{
 const s=slide('Next: retain the contact estimate through release and recovery');
 text(s,'Immediate experiment',96,179,1250,46,30,C.ink,true);
 text(s,'Compare recursive classical updates with the current window fits.\nMeasure prediction error, update time and uncertainty at several prediction times.',96,245,1390,108,30);
 text(s,'A small control to explain the history gain',96,416,1350,46,30,C.ink,true);
 text(s,'Compare evolving recovery observations with repeated measurements of a fixed state.\nThis separates dynamic information from noise averaging.',96,481,1380,108,28);
 text(s,'Then test actions under common feedback',96,638,1370,46,30,C.ink,true);
 text(s,'First check whether true-state information can help the selected task.\nFull 3D robot simulation follows the 2D decision test, before real robot operation.',96,701,1380,90,28);
 footer(s,'For discussion: which manipulation needs this state before feedback catches up, and which observable should define success?');
 notes(s,'Next: retain the contact estimate through release and recovery','下一步先不换网络。用经典递推观察器把接触时估计到的状态带过释放与等待，在多个预测时刻比较误差、更新时间和不确定性。补一个静态重复测量对照，区分恢复动力学和降噪。之后做共同反馈动作实验，先确认真实状态参考在给定任务和动作条件下有潜在收益。如果连这个参考都没有收益，应改任务而不是继续改编码器。完整3D机械臂闭环仿真在实机之前。希望讨论的是：哪个操作确实需要反馈尚未来得及补齐的信息，以及应该用什么任务结果判定它有用。',[
 `${RUN}/RESULTS.md#next-experiment`,'research/robot_manipulation/','Planned only: recursive observer, uncertainty calibration, shared-feedback 2D actions, complete 3D robot simulation, hardware.'
 ]);
}
// Appendix A. Complete recorded means and privileged references.
{
 const s=slide('Appendix: all recorded prediction errors','Force RMSE in mN. Twenty-four histories, three independent nominal-noise draws per history.');
 const rows=[['Information','Slow press','Fast press']];
 const labels=[['Current motion + force','basic_0.0'],['Current + lateral','lateral_0.0'],['Recent 0.2 s, without lateral','basic_0.2'],['Recent 0.2 s, with lateral','lateral_0.2'],['Recent 0.8 s, without lateral','basic_0.8'],['Recent 0.8 s, with lateral','lateral_0.8'],['Earlier contact + propagation, without lateral','basic_contact'],['Earlier contact + propagation, with lateral','lateral_contact'],['Full replay from a known relaxed start [privileged]','replay'],['True internal fields and the same solver [privileged]','truth']];
 for(const [l,m] of labels) rows.push([l,mean(m).toFixed(m==='replay'?4:3),mean(m,'Fast press').toFixed(m==='replay'?4:3)]);
 table(s,rows,96,205,[950,229,229],52,23);
 footer(s,'The references supply privileged state or initialization. They are not absolute optimal-control bounds.');
 notes(s,'All recorded prediction errors','这一页保留所有方法的完整均值，避免只展示有效的条件。已知松弛初态的完整重放和真实内部场使用额外信息。真实内部场误差为零来自使用同一个状态和同一个前向求解器，不代表现实物理误差为零，也不是所有控制策略的最优上界。',[
 `${RUN}/summary.json`,`${RUN}/metrics.csv`
 ]);
}
// Appendix B. Paired uncertainty as editable scatter charts.
{
 const s=slide('Appendix: paired gains across complete loading histories','Positive values mean lower force prediction error for Slow press.');
 const cs=[contrast('basic_0.0','lateral_0.0'),contrast('lateral_0.0','lateral_0.2'),contrast('lateral_0.0','lateral_0.8'),contrast('lateral_0.2','lateral_contact')];
 const labs=['Add current lateral shape','Add 0.2 s lateral wait','Add 0.8 s lateral history','Contact + propagation vs lateral wait'];
 cs.forEach((c,i)=>{
   const y=238+i*130;
   text(s,labs[i],96,y+10,600,70,28,C.ink,i===0);
   const x=c.parent_values.map(v=>v.improvement_mN);
   const jit=x.map((_,j)=>(j%5-2)*.09);
   const cc=i===0?C.blue:C.teal;
   scatter(s,{left:704,top:y-12,width:545,height:106},[
     {...series('24 histories',x,jit,'#BAC3C9','circle',0),line:{fill:'none',width:0}},
     series('95% interval',c.ci95_mN,[0,0],cc,'none',4),
     {...series('Mean',[c.mean_improvement_mN],[0],cc,'diamond',0),line:{fill:'none',width:0}},
   ],{xAxis:{min:i===0?-5:-2,max:i===0?25:4,majorUnit:i===0?5:1,numberFormatCode:'0',line:{fill:C.light,width:1}},yAxis:{visible:false,min:-.5,max:.5,majorGridlines:null}});
   text(s,`${c.mean_improvement_mN.toFixed(2)} mN\n[${c.ci95_mN[0].toFixed(2)}, ${c.ci95_mN[1].toFixed(2)}]`,1290,y+5,220,90,26,cc,true);
 });
 footer(s,'Three noise draws average within each history. 2,000 history bootstrap resamples. Pointwise exploratory 95% intervals.');
 notes(s,'Paired gains across complete loading histories','每个点是一个完整历史的配对改善，先平均它的三次噪声重复，再在24条历史上bootstrap。横轴第一行和后面三行范围不同。区间是探索性的逐项95%区间，不做普遍保证。接触对照除了接触内容，也使用了更长运动跨度，这一点不能隐藏。',[
 `${RUN}/summary.json`,`${RUN}/metrics.csv`,'Plot uses stored per-history paired values and stored confidence limits without recomputing selection.'
 ]);
}
// Appendix C. Physical and reproducibility scope without burying overruns.
{
 const s=slide('Appendix: physical checks and reproducibility');
 table(s,[['Item','Recorded status'],
 ['Material and geometry','40 x 20 mm body, 10 mm thickness, 576 triangles, dt = 0.01 s'],
 ['Synthetic relaxation model','E = 20 / 40 / 60 kPa, Poisson ratio 0.35, relaxation 0.12 / 0.90 s'],
 ['Nominal sensor noise','Position 0.5 um, velocity 0.01 mm/s, force 1.5 mN, lateral 1 um'],
 ['Physics exceptions','Test penetration 5.030 um and calibration 5.015 um exceed the 5 um limit'],
 ['Computation and consistency','0 computation exceptions, 10 regression tests and 7 data checks passed'],
 ['Notebook and batch runtime','Fresh Docker kernel Run All: 7.61 s. Main batch: 965.85 s on 8 CPU workers']],96,172,[440,968],88,25);
 text(s,'Both penetration overruns remain in the data. Real-material calibration is still missing.',96,806,1400,37,23,C.gray);
 notes(s,'Physical checks and reproducibility','数值检查不能只报通过。一条测试历史和一条校准历史的惩罚接触穿透略微超过5微米，已经保留并记录。没有计算异常，通道屏蔽、数据一致性和动作间状态复用检查通过。Notebook在干净Docker内核Run All实测7.61秒，这主要是缓存结果回放，不是重新运行整批实验。主批量生成和评估约16.1分钟。更低的估计误差是同一个模型内部的证据，不代表真实材料已达到亚毫牛精度。',[
 `${RUN}/physics.json`,`${RUN}/failures.json`,`${RUN}/verification/notebook.json`,`${RUN}/verification/data_contract.json`,`${RUN}/RESULTS.md`,'2D/notebooks/spatial_2d_hidden_state.ipynb'
 ]);
}

// 16. Open questions from the user's voice memo, after the supporting evidence.
{
 const s=slide('Questions for discussion');
 text(s,'Research focus',96,181,1360,44,27,C.gray,true);
 text(s,'We want to study hidden state beyond the current observation.\nCould too much focus on elasticity shift the project toward soft robotics?',96,241,1400,110,33);
 text(s,'Physical experiment',96,391,1360,44,27,C.gray,true);
 text(s,'We can build the model. How should we carry out\nthese experiments on a real robot?',96,451,1400,110,33);
 text(s,'Broader research question',96,601,1360,44,27,C.gray,true);
 text(s,'After studying hidden state through fast and slow forces,\nhow do we develop the broader idea from this specific case?',96,661,1400,110,33);
 notes(s,'Questions for discussion','我想讨论三个问题。第一，我们研究的是当前观测之外的隐藏状态。如果太关注弹性，会不会让研究方向偏向软体机器人？第二，模型可以建立，但真正上实机时，这个实验应该怎么做？第三，我们已经把 hidden state 具体化到快慢力这个点，接下来如何再升华回来，回到更一般的隐藏状态研究问题？',[
 'User-provided voice memo: Penn Engineering.m4a (78.396 s). Research focus: 00:00-00:30; real-robot experiments: 00:31-00:46; broader research question: 00:54-01:16. The user confirmed the final word as shenghua (conceptual development).',
 'research/presentations/10.2/assets/question_source.json',
 'These are discussion questions paraphrased from the user-provided memo, not additional experimental findings or attributed adviser instructions.'
 ]);
}

await fs.writeFile(path.join(HERE,'slide_sources.json'), JSON.stringify(S,null,2));
await fs.writeFile(path.join(OUT,'speaker-notes.zh-CN.md'), '# 10.2 第二周科研汇报讲稿\n\n主报告 12 页，附录 3 页，最后为讨论问题。正文约 10–12 分钟，讨论另计。\n\n'+S.map(x=>`## ${x.number}. ${x.title}\n\n${x.speaking_notes_zh}\n`).join('\n'),'utf8');
const draft=path.join(BUILD,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(draft);
const suffix=process.env.DECK_REVISION||'';
const finalPath=path.join(OUT,`10.2${suffix}.pptx`);
const report=await finalizePresentation({
 workspaceDir:HERE,candidatePath:draft,finalPath,pythonExecutable:PYTHON,
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','15240000,8572500','--validate-bullet-geometry','--validate-heading-fit',...[2,5,8,9,10,11,13,15].flatMap(n=>['--require-native-table-slide',String(n)])],
 explicitTotalSlideCount:16,requiredNativeTableOwnerSlides:[2,5,8,9,10,11,13,15],requiredNativeChartOwnerSlides:[6,7,8,9,14],
 fontPolicy:{basis:'reference',families:['Arial'],referencePath:D.reference.path,referenceSha256:D.reference.sha256},
 materializeLiteralChartWorkbooks:true,verifyArtifactToolImport:true,
 receiptPath:path.join(BUILD,`validation${suffix}-${Date.now()}.json`),
});
console.log(JSON.stringify({finalPath,validation:report.receiptPath,slides:16},null,2));
for(const [i,s] of p.slides.items.entries()){
 const b=await p.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(BUILD,'slides',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));
 console.log(`Rendered ${i+1}/${p.slides.items.length}`);
}
console.log('Saved editable PowerPoint, slide renders and speaker notes.');
