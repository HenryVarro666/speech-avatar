# Avatar experiment decisions / 数字人实验决策

[Optimization log / 优化台账](OPTIMIZATION_LOG.md) traces each change, result and adoption decision.

Goal: a clear and expressive visual companion to speech. Scope: rendering, sync, cancellation and review; no ASR/dialogue/translation ownership. **Current quality decision: NEEDS WORK.**

| Stage | Frozen comparison | Evidence and decision |
|---|---|---|
| [E0](2026-10-20-e0/RESULTS.md) |12dev/24test synthetic clips;2fictional still portraits | Structural freeze, hashes and prompts; human audio acceptance separate |
| [E1](2026-10-20-e1-musetalk/RESULTS.md) |6 development clips ×2avatars, MuseTalk1.5 |12 decode/source-audio passes; first-frame/full-task median3.003/7.165s without shared load |
| [E1 quality](2026-10-20-e1-musetalk/QUALITY_REVIEW.md) |1,032mouth frames and continuous playback | Soft teeth/static head/endings;80–120ms estimated video lead; quality gate unmet |
| [E1b](2026-10-20-e1b-full-expression/RESULTS.md) |Same accepted female/male speech and portraits;MuseTalk vsLongCat |4videos; LongCat expressions present but hand crop/intensity/teeth remain |
| [E1b review](2026-10-20-e1b-full-expression/quality-review-v1/REVIEW.md) |516mouth/108full frames, sync offset controls | LongCat offline candidate;MuseTalk regression baseline; no polished/live acceptance |
| [E1c](2026-10-21-e1c-controlled-expression/RESULTS.md) |6local0/40/80ms picture-delay variants;2prompt-only new videos | No demonstrated prompt-only motion gain; conditional tail0renders; human AV pending |
| [E1d](2026-10-23-e1d-reference-framing/RESULTS.md) |2fixed-ROI input-reference renders;same E1c voices/prompt/seed/model | Framing changes but hand/expression fix not established;no tail/grid;human AV pending |
| DUIX — local-only artifact: `2026-10-23-duix-single/RESULTS.md` |1accepted4.96s female/static-reference segment; isolated H100 |28.018s request,16,702MiB sampled process peak;120ms estimated video lead/80ms missing picture tail;human AV pending |
| DUIX sync continuation — local-only artifact: `2026-10-23-duix-single/CONTINUATION_RESULTS.md` |One local lossless+120ms candidate;no GPU regeneration |125frames/5.00s, original122frames/AAC exact;diagnostic−120→0ms;human pending |
| E1e explicit motion — local-only artifact: `2026-10-23-e1e-motion-control/RESULTS.md` |1CPU-only LivePortrait0.65render; existing same-avatar driver |323.408s,124frames;head/eyelids move but3partial closures/soft teeth;80ms estimated lead;human pending |
| E1f independent blink — local-only artifact: `2026-10-23-e1f-independent-blink/RESULTS.md` |22eye frames over fixed E1e head/mouth;same audio |3/3complete closures;outside-eyeYUV/102frames/AAC exact;341.509s CPU;human pending |
| [E1f-R regional motion](2026-10-23-e1f-regional-motion/RESULTS.md) |2CPU-only same-role drivers;pose/non-eye0.65,eye1.0,global1.0 | Hands contained and deep eye closures with lighter motion;soft teeth/sync/endings remain;human pending |
| E1g mouth sync/ending — local-only artifact: `2026-10-24-e1g-mouth-sync-tail/RESULTS.md` | E1f mouth-only80ms delay; sync-only vs0.48s silent closure | Full/early/late0ms;6/6tail closure;outside-mouth/eyes/AAC exact;confidence lower;human pending |
| E1h oral detail — local-only artifact: `2026-10-24-e1h-oral-detail/RESULTS.md` | Same E1g oral lumaHF; base/unsharp/boundedGFPGAN | Model not superior; unsharp optional; outside-oral/eyes/lips/tail/AAC exact; all sync0ms; human pending |
| [E2–E5 realtime pilot](2026-10-24-e2-e5-realtime/RESULTS.md) |4localPCMfixtures×idle/RMS/HeadAudio, actual DSH player observer/WebGL2 |12complete/sample-exact runs;10fault/recovery checks; planned audio start51.6–81.9ms; E5live upstream and neuralGPU pending |
| [E5a actual TTS](2026-10-24-e5-live-tts/RESULTS.md) |7real new requests/4Chinese texts/2voices; sameplayer |5complete/1cancelled/1incomplete; explicit recovery/stale rejection; CPU RTF3.135–3.591 fails realtime gate |
| E2 asynchronous new utterances — local-only artifact: `2026-10-24-e2-async-single-user/RESULTS.md` |Same retained avatar/Serena,12new audio-driven MuseTalk videos, single-user isolated queue |12/12source/media/tail proofs; two12plays,9backend/13browser checks; CPU98.474–266.092s; sync/human acceptance remains open |

E1b/E1c full-process timings include model loading and cannot be directly compared with E1's shared-load-excluded timings. SyncNet is a diagnostic, not human preference or semantic correctness. Public JSON/figures preserve numeric evidence; private media/contact sheets remain local and are explicitly marked when referenced.

Realtime next: isolated actual TTS/ASR/translation input with cancellation/fallback and a dedicated-GPU arbitrary-audio benchmark; current fixture adapter alone is partialE5. Offline quality track: collect continuous E1g original/sync-only/sync+closure judgments, then test timing on separately frozen new phrases. Preserve complete blinks/light head motion and the closed-ending candidate; oral detail and lower SyncNet confidence remain separate. No parameter grid or production default based on this familiar clip.

Detailed optimization history: [step-by-step progress ledger](PROGRESS_LEDGER.md). E1f-R preserves both role clips; collect human comparison before another render, and keep oral-detail/sync interventions separate.


## 2026-10-25 E5b：CUDA路径已准备，GPU对照待空闲资源

[本轮记录](2026-10-25-e5-gpu-comparison/RESULTS.md)：固定同模型/revision/参数/4文本/12帧分块/24kHz协议，新增显式CUDA/UUID资源保护和独立后端选择。分配前GPU1已被其他任务占用，GPU推理0次；速度/停顿改善和GPU恢复验收均未完成，不能以41项本地测试替代实卡验收。新CPU路由9实际请求：7完整/1播放中取消/1断流incomplete；显式重试、新句恢复与旧错误丢弃通过，7PCM/hash/样本/code检查通过。首PCM3.040–4.471s、RTF3.088–3.571、最大计划间隙2.696s，CPU性能门槛仍未过。

[独立预览49917](http://127.0.0.1:49917/index.html)；原50451保留。新GPU入口只在无其他计算PID、空闲且完成自有上下文复查后使用；未操作apex/共享包/其他进程。独立H100最近资源核验2026-10-25；841旧冻结记录不变。下一步等空闲卡，GPU预热后执行4句交叉主对照和7请求恢复；真人麦克风/ASR/翻译/人工AV/部署均未验收。用户授权本轮审查后源码/元数据公开备份，推送回执另记。

