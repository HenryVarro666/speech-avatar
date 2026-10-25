# Speech Avatar

[English](README.md) · **简体中文**

**验证音频驱动头像能否成为清晰、有表情的语音 Agent 视觉界面。**

## 问题与目标场景

语音 Agent 配上头像，不能只让嘴动：身份要稳定，音画要对齐，表情要自然，手、牙齿和片尾不能干扰语音信息。

本项目开发未来说话助手或口译型界面的生成与审阅层。ASR、对话、翻译和预约状态属于其他项目。离线生成可用不代表口译产品已部署，也不代表实时数字人。

## 使用与探索的方法

固定合成语音和两个虚构静态头像，离线比较 MuseTalk1.5 / LongCat1.5。审阅结合完整解码/源音轨检查、动态嘴部/全景检查、SyncNet 偏移诊断与平衡顺序的本地人工对照。

MuseTalk 保留为低成本口型/回归基线；LongCat 是离线完整表情开发候选。两者均未通过精修视频或实时对话验收，OmniAvatar、Hunyuan 尚未运行。

## 当前结果与决定

| 阶段 | 做了什么 | 结论与决定 |
|---|---|---|
| [E0 输入](experiments/2026-10-20-e0/RESULTS.md) | 12 开发＋24 测试合成语音，两个虚构头像 | 结构冻结；媒体留本地 |
| [E1 MuseTalk](experiments/2026-10-20-e1-musetalk/RESULTS.md) | 12 个离线组合；首保存帧/完整任务中位 3.003/7.165 秒，RTF1.999 | 解码/音轨通过；齿列糊、头眼静止及收尾待改善 |
| [E1b 后端对照](experiments/2026-10-20-e1b-full-expression/RESULTS.md) | 同一已接受男女配音分别驱动两个后端，共四片 | MuseTalk 整进程 23.916/23.607 秒；LongCat 270.721/267.728 秒；表情增加但强度、齿列和手入画仍有问题 |
| [E1b 质量审查](experiments/2026-10-20-e1b-full-expression/quality-review-v1/REVIEW.md) | 516 嘴帧、108 全景及同步细节；模型偏移控制 | LongCat 继续离线开发、MuseTalk 留基线；NEEDS WORK |
| [E1c 受控优化](experiments/2026-10-21-e1c-controlled-expression/RESULTS.md) | 六份 0/40/80ms 同步副本＋两段受控提示 LongCat 新片 | 只改提示未解决手入画/强调张嘴；按门槛跳过收尾生成（0 段） |
| [E1d参考构图](experiments/2026-10-23-e1d-reference-framing/RESULTS.md) | 固定ROI参考图，男女各1段；原E1c配音/提示/seed/模型 | 脸框26.62%→41.22%／27.07%→42.49%；手入画和强调表情仍在，不采用为修复 |
| DUIX单段 — local-only artifact: `experiments/2026-10-23-duix-single/RESULTS.md` | H100上同一4.96s已接受女声/静态头像；请求28.018s，采样进程峰值16,702MiB | 口型可生成；头眼静止、估计画面早120ms、有声尾部缺80ms新画面；NEEDS WORK |
| E1e显式动作 — local-only artifact: `experiments/2026-10-23-e1e-motion-control/RESULTS.md` | 原头像/配音/已有LongCat动作，LivePortrait幅度0.65，CPU单段323.408s | 头眼可动、3次部分闭眼；嘴幅P95较参考低26.3%；估计画面早80ms；NEEDS WORK |
| E1f独立闭眼 — local-only artifact: `experiments/2026-10-23-e1f-independent-blink/RESULTS.md` |固定E1e，仅22帧眼区修正，CPU341.509s |完整闭合3/3；眼区外YUV、102整帧及AAC精确保留；自然度待人工反馈 |
| E1g口部同步与收尾 — local-only artifact: `experiments/2026-10-24-e1g-mouth-sync-tail/RESULTS.md` |仅嘴部延后80ms＋0.48s无声闭嘴收尾，保留原版/只修同步对照 |偏移−80→0ms；固定6/6尾帧闭嘴；口部外YUV/248眼区RGB/AAC精确；置信度下降，人工待验 |
| E1h口腔细节 — local-only artifact: `experiments/2026-10-24-e1h-oral-detail/RESULTS.md` |内口腔亮度高频：原版/轻锐化/受限GFPGAN |逐帧相对HF-RMS均值+21.59%/−6.63%；模型未胜出不默认采用；眨眼/唇缘/尾段/AAC精确，同步均0ms |
| [E2–E5实时原型](experiments/2026-10-24-e2-e5-realtime/RESULTS.md) |4语音×静止/RMS/HeadAudio，实际播放时钟＋本机GPU贴片 |12完整播放/样本核验、10故障恢复；计划音频起点51.6–81.9ms；本轮为已备音频；真实TTS见E5a |
| [E5a真实TTS](experiments/2026-10-24-e5-live-tts/RESULTS.md) |7新生成请求，4中文文本/男女两声；插话/断流/重试 |5完整、1取消、1不完整；首PCM3.133–5.363s、RTF3.135–3.591，CPU实时性能未过 |

E1 计时不含共享模型加载；E1b/E1c 整进程包含加载，不能当同口径比较或语音对话视频延迟。E1c 两新片整进程 267.418/263.161 秒，640×608/25fps。

原 E1b LongCat 的 SyncNet 估计女/男画面领先 80/40ms。延后副本用于人工比较，不自动作为同步验收。人工连续音画评分待做，≥10/12 质量门槛尚未通过。

E1d两次新整进程271.001/264.656s（含加载），640×608/25fps；解码/音轨2/2、258单脸帧、原/新浏览器完整播放4/4及18项CPU测试通过。实际条件音频样本与父片相同，未裁切成片；人工音画接受仍待反馈。

DUIX服务启动16.570s、整容器47.347s，均不称严格冷启动延迟。原片512×512/25fps、122帧完整解码，119,040音频样本保留；人工音画接受待反馈。独立H100工作区已迁到 `/mnt/raid/voice_ai/`，旧路径兼容链接保留。

后续本地DUIX完善 — local-only artifact: `experiments/2026-10-23-duix-single/CONTINUATION_RESULTS.md`新增一份画面延后120ms候选：125帧/5.00s，原122帧及4.96sAAC音轨逐字节保留；同一模型诊断−120→0ms。该事后校正仍待人工比较，未改变表情/细节质量，没有新增GPU推理。

E1d回放已补本地反馈导出：构图偏好与明确音画接受分别填写，默认未判断，导出JSON绑定冻结视频；草稿不会自动更新人工评分。本次续接没有重新渲染，22项CPU测试与4段新回放检查通过。[反馈与中断恢复指南](docs/E1D_REVIEW_GUIDE.md)。

E1e验证显式视频运动层：124帧、1254×1254/25fps，CPU进程树采样RSS峰值2.695GiB，没有CUDA推理。另存母版逐位保留119,040源PCM采样。三次眼睑变化仍像半闭眼，人工音画接受待反馈；后端/分辨率不同，不能把全部变化归因于0.65幅度。

E1f单独恢复完整闭眼，同时保留E1e较轻头嘴画面：124帧/4.96s，采样CPU进程树RSS峰值2.766GiB，无CUDA。仅眼区改变，102个非眨眼帧整帧精确保留；原估计画面领先80ms、牙齿和收尾限制仍在。

E1g保留E1f完整眨眼/轻头动，仅嘴部延后80ms，并用固定0.48s无声画面在说完后闭嘴：新视频136帧/5.44s，原音轨4.96s和119,040源PCM样本不变。全片/固定前后段估计偏移均为0ms，但SyncNet置信度7.961→6.785且最小距离变差，熟悉片段补偿不等于泛化或整体质量接受。固定6帧闭嘴通过，口部外YUV、248眼区RGB裁片、AAC精确保留。CPU worker38.089s包含5帧学习式闭嘴和两版136帧合成/编码/证明，采样RSS2.294GiB，无CUDA或服务替换；人工音画接受待反馈。

E1h保留E1g时序、完整眨眼和闭嘴收尾，单测口腔纹理。轻锐化边缘略清楚；受限GFPGAN未胜出，不默认采用。没有真实齿列真值或人工音画接受。单次成功CPU worker125.811s含106模型帧和两版136帧编码/证明，采样RSS2.049GiB。部署准备判断 — local-only artifact: `experiments/2026-10-24-e1h-oral-detail/DEPLOYMENT_READINESS.md`区分可用的离线影片、新音频异步试用和未验收的实时对话。

本机实时原型已接实际DSH播放器的可选观察接口，M4Pro用WebGL2绘制照片/五嘴形，HeadAudio在CPUAudioWorklet。支持换句、原采样率PCM和本地WAV、打断/旧轮次丢弃与视觉降级。首活动嘴形比计划音频起点晚78–206ms，rAF间隔P95为8.8–9.3ms；不等于声学同步或真实ASR/译音时延。当前画面用于工程验证，中文自然度/照片真实神经画质仍待验收，E5a已接真实TTS，真人麦克风/ASR/翻译仍待接入。[运行、恢复和GPU路线](docs/REALTIME_PILOT_GUIDE.md)。

E5a已在独立实例逐块解码和传输实际新生成声音，保持一个播放器和明确end/epoch契约。5源PCM/结束摘要及客户端样本检查通过，真实播放中的客户端更正可取消旧生成，断流明确不完整并由新请求恢复。浏览器计划音频起点3.183–5.415s包含本次TTS，不能与E2已有音频约50–82ms同口径比较。CPU最大块间空隙2.840s，不能用于低延迟实战；真人麦克风/完整口译与人工自然度仍未验收。[E5运行与恢复](docs/E5_LIVE_TTS_GUIDE.md)。

<!-- e2-async-trial -->

用户已选择保留E1h原轻锐化片，这项视觉选择不等于新内容接受。独立新音频异步试用 — local-only artifact: `experiments/2026-10-24-e2-async-single-user/RUNBOOK.md`已准备12条新Serena配音，正在RAID/CPU上真正推理新嘴型。7项进程/队列/轮次检查通过，完整12片/浏览器/故障矩阵进行中；不假定原80ms补偿泛化。

<!-- /e2-async-trial -->

## 实验如何记录

[优化台账](experiments/OPTIMIZATION_LOG.md)把每一步为什么改、改动、证据、是否采用和下一步串起来，保留失败与跳过项；原目录继续保存完整计划、清单和执行取证。

[阶段索引](experiments/INDEX.md)链接冻结计划、清单、结果与审查决定。失败尝试全部保留。公开提示、哈希、汇总诊断和脚本；录音、头像、渲染视频、检查拼图及模型/vendor 目录留本地。

## 验证与复现

CPU 检查需要 Python3.12、Node.js18+ 和 ffmpeg/ffprobe，不运行生成模型：

```bash
python3.12 -m unittest discover -s tests -v
```

另有4项分区动作检查需要NumPy/OpenCV；缺少时明确跳过。现有本地质量环境可运行完整36项：

```bash
.venv-quality/bin/python -m unittest discover -s tests -v
```

本地保有对应私有输入时，再运行：

```bash
python3.12 scripts/validate_e0.py experiments/2026-10-20-e0/manifest.json
```

GPU 推理需要独立的 [MuseTalk](workers/musetalk/SETUP.md) / [LongCat](workers/longcat/SETUP.md) 环境、模型权限和冻结计划，不声称实时数字人一键安装已验证。

## 下一步

1. 收集现有同步及原片/新片对照的人工判断。
2. 连续比较E1g原版/只修同步/同步＋闭嘴；在另冻新短句上验证补偿后再决定采用。
3. 不默认采用受限GFPGAN；比较可选轻锐化，优先新音频单用户闭环及取消/失败回退验证。
4. 浏览器实时生成及语音 Agent 接入作为后续独立阶段。

[技术边界](docs/TECHNICAL_ROUTE.md) · [当前状态](PROJECT_STATUS.md) · [公开范围](PUBLICATION.md) · [工作区](https://github.com/HenryVarro666/voice-ai-workspace)。


## 分区视频驱动 / E1f-R

[男女配对两段](experiments/2026-10-23-e1f-regional-motion/RESULTS.md)沿用原角色配音/头像和E1c驱动：头姿/非眼0.65、眼1.0、global1.0。均1254²/25fps，258单脸帧与源PCM精确保留通过；CPU原生worker耗时856.164/371.437s，核心共享条件不同。手部未入画，轻嘴幅下恢复深闭眼；软牙齿、结尾和模型同步偏移仍NEEDS WORK，人工接受待反馈。[每步进展总账](experiments/PROGRESS_LEDGER.md)串联决策、失败与证据，不补造历史命令。
