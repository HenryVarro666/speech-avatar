# 每步优化与进展总账

最近核对：2026-10-24，America/Chicago。现有实验已经保留主要设计、配置、出片/失败和验证证据；本表把分散记录串成“问题→改了什么→结果→下一步”。不是声称保存了所有历史shell命令、每条聊天或每个人的主观观感。人工音画接受未填写的仍为null，技术通过不能代替自然度验收。

| 步骤 | 想改善什么／固定改动 | 已观察结果与采用决定 | 详细记录 |
|---|---|---|---|
| E0 | 冻结两虚构人物与12dev/24test合成音频、划分/哈希 | 结构验收通过；声音接受另行处理 | [计划](2026-10-20-e0/PLAN.md)、[结果](2026-10-20-e0/RESULTS.md) |
| E1 | MuseTalk1.5，6dev×2人物 |12片技术出片；软牙齿、静止头眼、同步问题，NEEDS WORK | [计划](2026-10-20-e1-musetalk/PLAN.md)、[逐次trial](2026-10-20-e1-musetalk/trials.jsonl)、[质量审阅](2026-10-20-e1-musetalk/QUALITY_REVIEW.md) |
| E1b声音 | 更换自然中文男/女音色，先试听再生成 | 用户明确“两条配音都可以”，固定男女角色匹配；不外推视频接受 | [声音结果](2026-10-20-e1b-full-expression/AUDIO_RESULTS.md)、[真实声音确认](2026-10-20-e1b-full-expression/audio_review.json) |
| E1b后端 | 同头像/已接受配音，MuseTalk vs LongCat四片 | LongCat有表情/头动；手入画、强调表情、齿列仍在；离线候选 | [执行计划/过程](2026-10-20-e1b-full-expression/EXECUTION.md)、[冻结协议](2026-10-20-e1b-full-expression/VIDEO_QUALITY_PROTOCOL.md)、[结果](2026-10-20-e1b-full-expression/RESULTS.md) |
| E1b质量复核 | 516嘴帧/108全景，SyncNet及已知音移控制 | 估计画面领先不是人的同步接受；保留两后端的不同用途 | [复核](2026-10-20-e1b-full-expression/quality-review-v1/REVIEW.md)、[下一轮依据](2026-10-20-e1b-full-expression/quality-review-v1/NEXT_EXPERIMENTS.md) |
| E1c同步 | 本地0/40/80ms画面延后6副本；原帧/PCM不改 | 模型分数随位移改变；实际偏好仍待用户 | [计划](2026-10-21-e1c-controlled-expression/PLAN.md)、[结果](2026-10-21-e1c-controlled-expression/RESULTS.md) |
| E1c表情 |2段正面提示，模型/音频/seed等不变 | 手与强调嘴眉仍在；未达到动作门槛，条件尾段0次，停止网格 | [结果](2026-10-21-e1c-controlled-expression/RESULTS.md) |
| E1d构图 | 生成前参考图固定ROI1254→1004，两段新片 | 脸占比增大；手/牙齿/表情收益未成立，头顶更挤；不采用 | [源码选择](2026-10-23-e1d-reference-framing/SOURCE_REVIEW.md)、[计划](2026-10-23-e1d-reference-framing/PLAN.md)、[结果](2026-10-23-e1d-reference-framing/RESULTS.md) |
| E1d恢复/反馈 | 原片完整性复核；新增分角色偏好/音画判断草稿导出 |22CPU测试、4完整播放；QA填写不算人工接受，无新视频 | 恢复账 — local-only artifact: `2026-10-23-e1d-reference-framing/recovery-20261023-v1/EXECUTION.md`、验收回执 — local-only artifact: `2026-10-23-e1d-reference-framing/recovery-20261023-v1/verification.json`、[操作指南](../docs/E1D_REVIEW_GUIDE.md) |
| DUIX单段 | 原头像/女声，隔离真实DUIX后端 | 技术出片，静止头眼/软牙齿/画面少80ms，NEEDS WORK | 计划 — local-only artifact: `2026-10-23-duix-single/PLAN.md`、结果 — local-only artifact: `2026-10-23-duix-single/RESULTS.md` |
| DUIX同步 | 本地画面延后120ms，完整保留原帧/AAC，覆盖音轨 | 同模型诊断回0ms；不是独立参数选择验证，头眼/牙齿不变 | 续接结果 — local-only artifact: `2026-10-23-duix-single/CONTINUATION_RESULTS.md` |
| E1e显式动作 | 旧E1c女性视频驱动原头像，LivePortrait全局0.65 | 头眼可动、3次部分闭眼；软牙齿/末帧张口/80ms诊断偏移仍在 | 源码核对 — local-only artifact: `2026-10-23-e1e-motion-control/SOURCE_REVIEW.md`、环境失败保留 — local-only artifact: `2026-10-23-e1e-motion-control/SETUP_ATTEMPTS.md`、结果 — local-only artifact: `2026-10-23-e1e-motion-control/RESULTS.md` |
| E1f-B局部闭眼（另项） | E1e女性基片眼区域纠正；本轮开始时已有独立计划 | 本轮开始时只有计划，收尾时另项已有结果；由其独立记录评估，不计本轮两段 | 其冻结计划 — local-only artifact: `2026-10-23-e1f-independent-blink/PLAN.md`、其独立结果 — local-only artifact: `2026-10-23-e1f-independent-blink/RESULTS.md` |
| E1f-R男女分区驱动（本轮） | 同角色原E1c模板；眼1.0、头姿/其余表达0.65、global1.0；各一片 | 2段完成，轻头动/嘴幅与深闭眼共存；手未入画、软牙齿/同步/结尾仍NEEDS WORK | [选择核对](2026-10-23-e1f-regional-motion/SOURCE_REVIEW.md)、[计划](2026-10-23-e1f-regional-motion/PLAN.md)、过程 — local-only artifact: `2026-10-23-e1f-regional-motion/EXECUTION.md`、[结果](2026-10-23-e1f-regional-motion/RESULTS.md) |
| E1g局部口型同步 | 固定E1f局部闭眼女基片，只将嘴部延后2帧，不移头/眼/音轨 | 全片/固定前后段估计0ms，原−80ms；置信度下降，不外推逐音素/新语音 | 计划 — local-only artifact: `2026-10-24-e1g-mouth-sync-tail/PLAN.md`、对照结果 — local-only artifact: `2026-10-24-e1g-mouth-sync-tail/RESULTS.md` |
| E1g独立闭嘴收尾 | 同步对照另增0.48s无声画面，末字和延迟嘴形完成后5.04s起5帧lip-MLP收拢 | 固定6/6尾帧闭嘴；只延长对照仍张口；口部外像素/完整眨眼/AAC精确保留；1次成功，人工待验 | 逐帧控制 — local-only artifact: `2026-10-24-e1g-mouth-sync-tail/frame-control.json`、每步准备/问题 — local-only artifact: `2026-10-24-e1g-mouth-sync-tail/PREPARATION.md`、验证 — local-only artifact: `2026-10-24-e1g-mouth-sync-tail/local-quality.json` |
| E1h口腔细节 |固定E1g，同内口腔亮度高频：轻锐化vs受限GFPGAN；原时序/眨眼/收尾不动 |2帧各1像素跨平台计数保护失败后同参数重跑；轻锐化边缘略强，模型未胜出不默认采用；新音频/部署另验 |计划 — local-only artifact: `2026-10-24-e1h-oral-detail/PLAN.md`、失败与调整 — local-only artifact: `2026-10-24-e1h-oral-detail/PREPARATION.md`、结果 — local-only artifact: `2026-10-24-e1h-oral-detail/RESULTS.md`、部署准备 — local-only artifact: `2026-10-24-e1h-oral-detail/DEPLOYMENT_READINESS.md` |
| E2–E5实时原型 |一个实际播放器＋3驱动模式，4固定语音换句、GPU贴片和故障恢复 |12完整/样本核验，10故障检查；计划音频起点51.6–81.9ms；E5真实上游/照片真实神经画质待验 |[计划](2026-10-24-e2-e5-realtime/PLAN.md)、[执行/失败](2026-10-24-e2-e5-realtime/EXECUTION.md)、[结果](2026-10-24-e2-e5-realtime/RESULTS.md)、[下一轮GPU](2026-10-24-e2-e5-realtime/GPU_PROTOCOL.md) |
| E5a真实TTS流 |固定原模型双角色、真实逐块PCM接播放器，插话与断流恢复 |7请求5完整/1取消/1不完整，RTF3.135–3.591实时性能未过；显式恢复通过 |[计划](2026-10-24-e5-live-tts/PLAN.md)、[执行](2026-10-24-e5-live-tts/EXECUTION.md)、[结果](2026-10-24-e5-live-tts/RESULTS.md) |
| E2新音频异步 |用户保留原轻锐化；同人物/音色12新句→真实嘴型→验证后播放；单活动/单等待/epoch与客户端意图 |12片/1152帧、源PCM精确/闭嘴/眨眼模板保持，两轮各12播完；7单元/9后台/13浏览器通过；CPU98.474–266.092s；新句同步与人工待验 |计划 — local-only artifact: `2026-10-24-e2-async-single-user/PLAN.md`、每步失败 — local-only artifact: `2026-10-24-e2-async-single-user/PREPARATION.md`、结果 — local-only artifact: `2026-10-24-e2-async-single-user/RESULTS.md`、操作 — local-only artifact: `2026-10-24-e2-async-single-user/RUNBOOK.md` |

## 记录覆盖与剩余边界

本轮启动时逐目录核对见记录盘点 — local-only artifact: `2026-10-23-e1f-regional-motion/record-audit.json`。E1使用trial_plan而非名为manifest的文件；E1b计划拆在EXECUTION及音频/视频冻结协议中，不能仅凭缺少同名PLAN判为没有设计。大文件、原始音视频、模型与运行目录仅本机/独立实验磁盘保存，哈希与公开可审元数据分开。

各轮并非都采用同一记录模板，早期也没有统一的逐命令总日志。持续补总账和链接，不伪造未留存历史。失败、负结果、未触发的条件实验、输入差异、测量时间边界和人工pending都应保留。今后每次新试验固定增加：冻结计划/输入哈希、实际命令和attempt、资源环境、技术/视觉验收、采用或停止理由、下一步及双方状态历史。


## 2026-10-25 E5b：CUDA路径已准备，GPU对照待空闲资源

[本轮记录](2026-10-25-e5-gpu-comparison/RESULTS.md)：固定同模型/revision/参数/4文本/12帧分块/24kHz协议，新增显式CUDA/UUID资源保护和独立后端选择。分配前GPU1已被其他任务占用，GPU推理0次；速度/停顿改善和GPU恢复验收均未完成，不能以41项本地测试替代实卡验收。新CPU路由9实际请求：7完整/1播放中取消/1断流incomplete；显式重试、新句恢复与旧错误丢弃通过，7PCM/hash/样本/code检查通过。首PCM3.040–4.471s、RTF3.088–3.571、最大计划间隙2.696s，CPU性能门槛仍未过。

[独立预览49917](http://127.0.0.1:49917/index.html)；原50451保留。新GPU入口只在无其他计算PID、空闲且完成自有上下文复查后使用；未操作apex/共享包/其他进程。独立H100最近资源核验2026-10-25；841旧冻结记录不变。下一步等空闲卡，GPU预热后执行4句交叉主对照和7请求恢复；真人麦克风/ASR/翻译/人工AV/部署均未验收。用户授权本轮审查后源码/元数据公开备份，推送回执另记。

