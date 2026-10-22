# E1b 自然中文与完整表情四段对照操作计划

> **For agentic workers:** 使用 superpowers:executing-plans，按下列任务在当前会话内逐项执行。用户要求未明确授权时不启动子代理，且暂不暂存、提交或推送。

**Goal:** 先改善两个人物的中文配音，再用四段样片判断 LongCat 1.5 的表情收益是否值得继续投入。

**Architecture:** speech-avatar 消费已经完成的 WAV；上游负责 TTS。两个角色各绑定自己的声音，同一角色的音频与底图在 MuseTalk / LongCat 间保持一致，后端预处理差异明确记录。独立离线 worker 出片后，由一个带声 video 播放器回放。

**Tech Stack:** Python、ffmpeg/ffprobe；现有 MuseTalk 1.5 环境；独立 LongCat 1.5 CUDA 环境。首轮不引入 vLLM-Omni、OmniAvatar、Hunyuan 或前端生产接入。

**Spec:** [选型与代码接入报告](https://github.com/HenryVarro666/voice-ai-workspace/blob/main/reports/Avatar%20%E5%AE%8C%E6%95%B4%E8%A1%A8%E6%83%85%20%E9%80%89%E5%9E%8B%20%E6%89%A9%E5%B1%95%E8%B7%AF%E7%BA%BF.md)；[四任务草案](../../../experiments/2026-10-20-e1b-full-expression/pilot_spec.json)；[当前记录](../../../experiments/2026-10-20-e1b-full-expression/RESULTS.md)。

## Global Constraints

- 原 E0 manifest、36 条语音、两个形象和 E1 的 12 段视频保持原样；held-out test 不参与本轮选择或调参。
- 不访问 apex，不启动/停止其服务，不混装 MuseTalk 与 LongCat 依赖。H100 是此前核验的另一台机器，当前空闲情况尚未刷新。
- 后续推理前只读核对 GPU PID、显存、磁盘和环境；只用空闲单卡，外部任务占用则延期，不释放别人的模型。
- 本文编写时尚无新音频；后续执行状态以实验 RESULTS.md 为准。pilot_spec.json 在人工接受前仍是草案，null 表示未知，不能自动填为通过。
- 输入冻结前可以修改草案；试听后写独立 manifest.json / SHA sidecar，正式尝试追加 attempts.jsonl，不覆盖旧结果。

## Review Focus

1. 音色与人设：听两条完整音频，男角色不能继续继承女声默认值。
2. 内容与自然度：数字、停顿、句尾和机械感必须单独回听；ASR 文本正确不能替代听感。
3. 覆盖时长：不能把默认单段 LongCat 的可播放文件误认成完整回复。
4. 动态画面：移动人头必须逐帧检测/跟踪，不能直接复用 E1 的固定人脸框。
5. 播放与计时：一个音频所有者；完整命令含加载的时间不能直接减去 E1 排除共享加载的 7.165 秒。

## Task 1：两条音频先过关

**Files:** 新媒体保存在忽略目录 `data/private/e1b/audio/`；更新实验目录中的 `pilot_spec.json`，试听记录另存 `audio_review.json`。

**Interface:** 两个 WAV 和各自的来源、voice_id、文本、采样率、时长、SHA-256、试听人及结论；两位角色分别绑定一个 audio_id。

- [x] 核对明确音色：独立运行 Qwen3-TTS-1.7B-CustomVoice，Serena 女声 / Uncle_Fu 男声；不使用现有 Base 的默认克隆配音，不调用 apex。
- [x] 两个音色用同一句：“您好，已经帮您安排好了。明天下午三点半见，路上注意安全。”实际4.96/5.36秒；保留自然输出，不强制变速。
- [x] 保留原始float32数组和PCM16导出；本轮未重采样、裁剪或追加静音。后续若转换，另存派生文件并记录哈希。
- [x] 打开本地试听页，两条完整播放技术检查通过；用户随后明确“两条配音都可以”，总体接受绑定原WAV哈希，不代填细分评分。
- [x] 两条均通过后写入冻结 manifest。包含两个底图及 MuseTalk 静态参考视频的已有哈希；保留各后端的缩放处理差异。不覆盖 E0。

**Check:** 两条真实音频均存在、可完整解码、时长与哈希可重算，并且试听记录绑定实际文件哈希与真实 reviewer；若输入变更，之前的试听结论失效。

## Task 2：准备独立 worker，先只做一个 LongCat 冒烟

**Files:** 未来新增 `workers/longcat/run_pilot.py` 与 `workers/longcat/SETUP.md`；已有 `workers/musetalk/run_e1.py` 保留，E1b 需要新的任务入口或薄适配，不能直接改原实验输出目录。

**Interface:** `run_pilot.py --job <frozen-job.json> --attempt N` 已实现，消费单个冻结任务，在独立目录输出并追加 `video_attempts.jsonl`。复现环境见 workers/longcat/SETUP.md。

- [x] 先补关键失败验证：音频哈希变化、未完成试听、续接覆盖不足、输出已存在、GPU 上出现外部任务时拒绝开始；不启动模型来验证这些前置条件。
- [x] 在独立 H100 工作目录建立 LongCat 环境，记录源码版本 `6b3f4b8582a8bc3f20f795735f5383716c4ba794`、依赖锁、权重来源和实际文件哈希，不升级现有 MuseTalk 环境。
- [x] 包装原生 CLI：单 GPU / context_parallel_size=1、stage_1=ai2v、avatar-v1.5、480p、use_distill、use_int8。源代码固定采样 seed42；记录实际生效的 8 steps / text CFG1 / audio CFG1。不是添加不存在的 --seed 参数。
- [x] 按实际音频长度计算段数：首段 93/25=3.72 秒，每个续接增加 80/25=3.20 秒；`n=max(1,1+ceil(max(0,duration-3.72)/3.20))`。5–6 秒至少两段；两段覆盖 6.92 秒，超过即增加段数。整数采样/帧数处理要向上覆盖。
- [x] 首个已冻结角色运行一次冒烟，成功结果可计入四段，不额外跑重复样片。记录原始播放音频与 vocal separation 后 conditioning 音频、转换、哈希和已知偏移。

**Check:** 先记录单卡实际可运行性及失败，不能引用第三方 H100 数字作为本机预算。文件完整解码，最后一个词与音频有效范围保留；发现截断停止后续任务，保留失败，不覆盖原文件。

## Task 3：完成四段，按角色比较

**Files:** `outputs/e1b/` 保存原生成品及审阅页；实验目录保存 `video_attempts.jsonl`、`video_process_results.jsonl`、`video_validation.json`、`video_review.json`；已新增 `scripts/analyze_e1b.py`，旧 E1 分析结果不改。

**Interface:** 每个 artifact 绑定 trial_id、backend/revision、seed、输入/配置/输出哈希、原生分辨率/fps、音频时间映射和检查结果。

- [x] 按草案的四个任务串行运行：女声 MuseTalk / LongCat，男声 MuseTalk / LongCat。两边都使用新音频；不能拿旧 E1 的 macOS 音轨成品来证明新模型改善了声音。
- [x] 新 MuseTalk 入口固定 seed42；保持原 E1 的主要渲染设置，记录必要的路径适配。LongCat 与 MuseTalk 同 seed 不代表算法等价或跨硬件逐位复现。
- [x] 完整解码所有成品，核对全句音轨、时长/时间变换、未截断句尾；按帧跟踪人脸生成可复查证据，SyncNet 只作辅助。
- [x] 做两组按角色的 A/B 回放，统一显示尺寸，保留原生文件与分辨率差异。审阅字段：同步可接受、牙齿/身份、眨眼/眉眼/头动、表情适合、片尾回中性、复查时间点。允许无明显收益／无法判断。
- [x] 记录实际命令启动至最终文件关闭的 wall time、加载/生成可分阶段、峰值显存的采样口径。没有埋点的首保存帧设 null；不填首声、实时延迟或 p95。

**Check:** 4/4 完整媒体与输入绑定通过；两位角色均经真实连续音画审阅，且 LongCat 没有明显同步/身份/收尾退化，增加的动态确有展示价值，才建议继续。四段结果不替代原 E1 的 ≥10/12 签收门槛。

## Task 4：只选一个后续方向

- [x] 更新实验结果、双方 PROJECT_STATUS / EVOLUTION；中英 README 的功能与数字同步，不提交或推送。
- [ ] 若离线收益明确，下一轮新增版本化半身参考、较长中文和英文；当前头像不能验证手势或完整身体动作。再决定是否需要 vLLM-Omni 批量调度。
- [ ] 若目标变成实时可打断，另开 E2–E4 的浏览器 viseme/表情工作，复用真实 AudioContext 排程与 epoch；离线成片不作为实时验收。
- [ ] LongCat 环境不可行或收益不足时，先总结这四段，再决定是否用相同输入试 OmniAvatar 1.3B；不同时安装三个大模型。

## 现在的操作

2026-10-20用户已接受两条配音，manifest已冻结，四段已完成（8次尝试：4成功、4失败/资源拒绝）。技术检查和本地A/B预览见实验RESULTS.md。**视频人工连续音画审阅仍待反馈**；本轮不追加参数网格、不安装其他后端、不开始实时接入。后续方向需结合这四段的实际偏好决定。

执行补充：完整单卡实测、4/4解码与音轨、516帧跟踪及4/4浏览器播放已完成；Task3的人工连续音画质量Check仍待反馈。Task4后三项为条件后续，未开始。
