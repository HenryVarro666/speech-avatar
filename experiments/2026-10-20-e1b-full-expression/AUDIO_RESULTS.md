> Historical snapshot: audio-only stage before the user accepted both voices and authorized video rendering. Current state is in RESULTS.md.

# E1b 自然中文配音：等待用户试听

日期：2026-10-20。状态：**AUDIO_READY / AWAITING_USER_CONFIRMATION**。本轮用户只授权生成男女各一条配音、打开本地试听；四段视频须等用户确认声音后才能开始。

[本地试听页](http://127.0.0.1:56750/index.html)已在 Codex 内置浏览器打开并保留；HTML 文件 — local-only artifact: `../../outputs/e1b-audio/index.html`与两条 WAV 也保留本地。临时服务只监听127.0.0.1，PID63566，不访问 apex。

## 两条候选

同一句：“您好，已经帮您安排好了。明天下午三点半见，路上注意安全。”同一条自然亲切、适中语速、避免播音腔的提示。预设来自 [Qwen 官方 CustomVoice 模型](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)，不是克隆用户或其他真人声音。

| 角色 | 普通话预设 | 时长 | 合成调用耗时 | 当前判断 |
| --- | --- | ---: | ---: | --- |
| avatar-a 女角色 | Serena | 4.96s | 4.040s | 技术检查通过，内容/自然度/人设适配待用户听检 |
| avatar-b 男角色 | Uncle_Fu | 5.36s | 3.845s | 技术检查通过，内容/自然度/人设适配待用户听检 |

均为24kHz、单声道、PCM16。保留模型原始float32数组，仅量化为PCM16，无裁剪、变速、归一化、重采样或追加静音。女声比5s目标短40ms，不为凑时长改动波形。完整文本是否说对、末字是否自然仍须听检，未用自动信号检查代填。

模型固定revision `0c0e3051f131929182e2c023b9537f8b1c68adfe`；每个音色seed42，BF16/SDPA，max_new_tokens1024。权重13文件、合计4.210GiB及各自SHA见 [model_manifest.json](model_manifest.json)；[请求](tts_request.json)、[逐次记录](tts_attempts.jsonl)、[运行元数据](run_metadata.json)、[依赖锁](requirements.lock.txt)完整保留。

## 验证与环境

- [音频验证](audio_validation.json)：2/2哈希、完整ffmpeg解码、长度/采样率、无削波及原始浮点到PCM16量化误差检查通过，试听副本SHA一致。
- [浏览器记录](browser_playback.json)：两条都达到ended=true、媒体错误null、无浏览器warning/error。它只证明播放器可用，**不是人工听感通过**；[人工确认](audio_review.json)所有结论仍为null/pending。
- 新增GPU冲突/已有音频禁止覆盖/异常GPU查询拒绝执行三个前置测试；先观察3fail，再实现，完整本地8项测试通过。[执行记录](EXECUTION.md)保留边界与判断。
- 独立H100主机sn4622126358的GPU1执行，未调用apex。GPU0原有两个外部进程2019086/2088852全程保留；自有2100581已退出，GPU1恢复14MiB已用、95306MiB空闲。见 [运行前](environment-before.json) / [运行后](environment-after.json)，仅是2026-10-20现场快照。
- 新建独立Python3.12.13环境，qwen-tts0.1.1、torch/torchaudio2.8.0+cu128、transformers4.57.3；103包依赖检查通过。[复现说明](../../workers/tts/SETUP.md)。日志保留可选FlashAttention/SoX未安装提示；当前SDPA合成路径正常退出，未做全局安装。

模型加载2.013s，从from_pretrained前到CUDA同步结束；两条调用耗时从generate_custom_voice前到CUDA同步结束，不含保存。整子进程19.860s含导入、加载、两条生成和保存，不含环境安装、权重下载与传输。不是实时首块、说完到首声或严格冷启动计时。

## 下一步与尚未开始的工作

等待用户分别确认女声、男声的自然度、内容与人设。若不合适，先修改配音；两条都接受后才冻结视频manifest、准备LongCat环境并开始四段对照。[任务草案](pilot_spec.json)已填真实音频信息但仍frozen=false，四个任务均awaiting_audio_confirmation；未生成任何新视频，未安装LongCat或其他视觉模型。

原E0、E1十二段成品及NEEDS WORK结论保持。未启动子代理、暂存、提交、配置远端或推送。

[准备阶段核对](preparation_checks.json)是此前快照，旧草案保留于 [pilot_spec.before_audio.json](pilot_spec.before_audio.json)；本轮最终核对见 [audio_final_checks.json](audio_final_checks.json)。
