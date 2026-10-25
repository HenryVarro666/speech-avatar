# speech-avatar current state

## 2026-10-25 E5b：CUDA路径已准备，GPU对照待空闲资源

[本轮记录](experiments/2026-10-25-e5-gpu-comparison/RESULTS.md)：固定同模型/revision/参数/4文本/12帧分块/24kHz协议，新增显式CUDA/UUID资源保护和独立后端选择。分配前GPU1已被其他任务占用，GPU推理0次；速度/停顿改善和GPU恢复验收均未完成，不能以41项本地测试替代实卡验收。新CPU路由9实际请求：7完整/1播放中取消/1断流incomplete；显式重试、新句恢复与旧错误丢弃通过，7PCM/hash/样本/code检查通过。首PCM3.040–4.471s、RTF3.088–3.571、最大计划间隙2.696s，CPU性能门槛仍未过。

[独立预览49917](http://127.0.0.1:49917/index.html)；原50451保留。新GPU入口只在无其他计算PID、空闲且完成自有上下文复查后使用；未操作apex/共享包/其他进程。独立H100最近资源核验2026-10-25；841旧冻结记录不变。下一步等空闲卡，GPU预热后执行4句交叉主对照和7请求恢复；真人麦克风/ASR/翻译/人工AV/部署均未验收。用户授权本轮审查后源码/元数据公开备份，推送回执另记。

## 2026-10-24 E5a live TTS substage

[Results](experiments/2026-10-24-e5-live-tts/RESULTS.md):7actual new-TTS browser requests,5complete/4newChinese texts,1controlled playing-time cancellation,1injected disconnect markedincomplete. Explicit retry/newphrase recovery and stale rejection pass; sourcePCM/end/sample proofs5/5. FirstPCM3.133–5.363s, planned audio start3.183–5.415s from text request; CPUworkerRTF3.135–3.591/maxgap2.840s fails realtimeperformance.36tests pass; fixed model/runtime read only, no shared-service deployment. Human microphone/ASR/translation/AV remain pending. [Guide](docs/E5_LIVE_TTS_GUIDE.md); reviewed source/metadata publication authorized, rawmedia/models/vendor/credentials excluded.

## 2026-10-24 realtime browser pilot

[Results](experiments/2026-10-24-e2-e5-realtime/RESULTS.md):12localfour-input×three-mode complete PCM playback comparisons; exact sample accounting, optional actual DSH playback observer and10fault/recovery checks. Planned audio start51.6–81.9ms/request; first HeadAudio active pose78–206ms/audio-start; rollingrAFintervalP95 8.8–9.3ms. These are browser engineering observations, not physical synchronization or live interpreter latency.27avatar tests and13plugin tests/typecheck/build pass. Initial rest-asset/UI callback defects preserved and corrected. Local GPU draws an approximate five-pose portrait; English-trained analysis/Chinese naturalness and neural fidelity remain unaccepted. E5live upstream and CUDA benchmark pending; no service deployment or push. [Guide](docs/REALTIME_PILOT_GUIDE.md).

Date: 2026-10-22, America/Chicago.

Latest: E1c bounded continuation complete:6 local sync derivatives +2 controlled-prompt LongCat videos. Technical checks pass, but hand entry and emphasized articulation persist; Qmotion NEEDS WORK, Qtail skipped by gate (0renders). [Results](experiments/2026-10-21-e1c-controlled-expression/RESULTS.md), [local preview](http://127.0.0.1:55219/index.html). 10/10 browser playback,15tests pass; human sync/video acceptance pending. No apex or git mutation.

Local experiments began on `experiment/e0-e1`. A separate reviewed public source snapshot is now published; see PUBLICATION.md. Historical no-push statements below describe those experiment rounds. [E0 frozen inputs](experiments/2026-10-20-e0/RESULTS.md) pass structural validation: 36 waveforms, two fictional still-image avatars. Text labels remain synthesis inputs, with human listening pending. [E1 results](experiments/2026-10-20-e1-musetalk/RESULTS.md): all 12 offline pairs rendered and passed full decode and source-audio checks. [Quality audit](experiments/2026-10-20-e1-musetalk/QUALITY_REVIEW.md) is complete with **NEEDS WORK / not signed off**: 12/12 browser playback, all 1,032 mouth frames inspected, SyncNet estimates video leading audio by 80–120 ms. Human continuous audiovisual ratings remain absent; the >=10/12 quality gate has not passed. No apex service has been touched.

Read [execution plan](docs/superpowers/plans/2026-10-20-e0-e1.md), [E0 protocol](experiments/2026-10-20-e0/PLAN.md), and [E1 protocol](experiments/2026-10-20-e1-musetalk/PLAN.md).

The user supplied a working SSH destination; existing key authentication works, so no password was used or stored. The verified host is a separate dual H100 NVL system, not apex. Each GPU reported 95,830 MiB total and about 95,306 MiB free at the first check. Isolated work root: `/data/speech-avatar-exx-20261020`, on a partition with about 715 GiB initially free. No shared Python environment was altered.

Dependency setup uses upstream's PyTorch 2.0.1 CUDA 11.8 stack in a new Python 3.10 virtual environment. Chumpy's isolated build initially failed because its setup imports pip; installing it without build isolation in this new environment resolved setup. No render failures have been fabricated from dependency failures.

E1 task median: first saved composited frame 3.003 s; complete encoded video 7.165 s; full-task RTF 1.999. This excludes shared loading and is not conversation latency. First task 18.728 s is retained; seed was not explicitly fixed. Outputs are 512×512 at 25 fps. Local quality audit found soft teeth, incomplete neutral endings (a/zh-02 final 200 ms audio is all zero), and static head/eyes. Model-based sync estimates and playback completion do not replace human continuous audiovisual ratings.

Remote generation end state verified 2026-10-20: worker exited, both H100 GPUs returned to 14 MiB used with no compute processes. All prior TCP listeners remained; a new listener belonged to another PID and was not touched. This is the earlier run snapshot, not a refreshed claim about current GPU occupancy. The quality audit used only local CPU in a new `.venv-quality`, with no SSH. A user-requested local preview server binds only 127.0.0.1 and serves `outputs/e1`; local gallery — local-only artifact: `outputs/e1/index.html` is open in Chrome. Next: E1-Q1 blinded sync variants, E1-Q2 neutral endings, then bounded face/detail and dynamic-reference comparisons. None of these optimizations or E2 has started.

Quality-audit verification snapshot (2026-10-20, before the later selection report): five integrity tests and frozen manifest check pass; all 14 repository Markdown files and 66 local links checked, zero missing targets. All 12 original output hashes are unchanged, fully decode and preserve source audio. Audit/protocol hashes match; the quality-metrics overwrite guard rejects reruns while preserving the original. No HEAD commit, staged files or repository remote; media/vendor/environment remain ignored. Current checks: `experiments/2026-10-20-e1-musetalk/quality_final_checks.json`; the earlier setup check file is retained separately.

User playback feedback (2026-10-20): Chinese sounds stiff; requests full expressions and questions male-avatar/female-voice pairing. Configuration confirms macOS say Tingting/Flo at rate180 and the same six source waveforms for both avatars, without role/voice binding. This is a cross-voice diagnostic matrix, not a finished persona demo. Feedback is recorded separately from unfilled per-clip AV ratings. QUALITY_REVIEW.md now documents the mapping and official full-animation candidates (LongCat-Video-Avatar1.5 priority, OmniAvatar/HunyuanVideo-Avatar alternatives). Suggested next comparison: two natural, role-matched Chinese waveforms first listened to and frozen, then MuseTalk vs LongCat, four clips total. This is a proposal; no new audio, render, model download or remote access has occurred.

## 2026-10-20 Full-expression backend selection and integration design

Read-only official/source comparison completed. LongCat-Video-Avatar1.5 is the preferred offline pilot, OmniAvatar the smaller/research alternative, Hunyuan the conditional third choice. vLLM-Omni offers a community offline recipe; online serving is explicitly unsupported for this pipeline. This is engineering selection, not measured quality/performance or production-readiness. Report: ../voice_ai/reports/Avatar 完整表情 选型 扩展路线.md; pinned upstream commits and local code hashes accompany it.

Design keeps speech-avatar separate and consumes final audio from DSH/native outputs. Reuse frozen-input/logging/media-validation methods and AudioContext/epoch cancellation; do not reuse fixed face boxes for moving heads or replace the old text-to-TTS DUIX call with a model name. Verified LongCat93frames/25fps default and export truncation risk, OmniAvatar0.3/0.34s audio prefixes, and differing dependency environments. Proposed next pilot: two naturally voiced, persona-matched 5–6s Chinese inputs, two backends, four clips; enough LongCat continuation and dynamic face tracking. Real-time browser viseme/expression work remains separate.

Only public source/docs were read/downloaded. No new model weights or packages installed, no inference, SSH/apex access, production changes, staging, commit or push. E1 remains NEEDS WORK and no new experiment protocol has been executed.

Selection-document verification: 20 selected Markdown files / 162 local links checked, zero missing targets; 27 cached official text hashes match the source lock. E0 manifest and all 12 E1 MP4 hashes remain unchanged; staged files/remotes remain empty. No new runtime tests were needed for this documentation-only review. Evidence: voice_ai/research_notes/Avatar 完整表情 选型 扩展路线/verification.json.


## 2026-10-20 E1b operation plan prepared

[Step-by-step plan](docs/superpowers/plans/2026-10-20-full-expression-pilot.md) and [four-job draft](experiments/2026-10-20-e1b-full-expression/pilot_spec.json) are prepared: persona-matched female/male Chinese audio first, then the same accepted audio per role through MuseTalk and LongCat. Existing image/reference hashes are checked; voice provider/voice_id, audio hashes/durations and all listening decisions remain unknown/pending. The draft is not a frozen manifest. No new audio, weights, packages, inference, SSH or GPU measurement occurred. Environment occupancy was not refreshed; a read-only resource check must precede any later inference.

Next: prepare two natural voices, let the user listen, then freeze the inputs. LongCat uses a separate environment, single GPU, v1.5 ai2v / 480p / INT8 / distillation, enough continuation to cover the actual audio, and per-frame face tracking for review. E1 stays NEEDS WORK; no runtime/production changes, subagents, staging, commit or push. Preparation verification is recorded in experiments/2026-10-20-e1b-full-expression/preparation_checks.json.

Preparation checks (2026-10-20): 20 Markdown files / 234 local links, zero missing targets; all four existing reference hashes and twelve original E1 output hashes match, E0 manifest unchanged. Two roles and four pending jobs are consistent; new audio/video counts remain zero, no HEAD/staging/remotes. No runtime tests were rerun for this planning-only change.


## 2026-10-20 E1b audio ready — awaiting user confirmation

Generated two Chinese candidates with Qwen3-TTS-12Hz-1.7B-CustomVoice (pinned 0c0e3051…): Serena female 4.96s / Uncle_Fu male 5.36s, both24kHz PCM16. The same text/style and seed42 are used. Original float32 arrays retained; no trim, speed change, normalization, resampling or added silence. [Listening page](http://127.0.0.1:56750/index.html) opened in Codex IAB and retained; local loopback server PID63566 serves only outputs/e1b-audio. Both complete playback without media/console errors; signal/hash/decode/quantization checks pass. Human naturalness, content and persona approval are pending in audio_review.json; no automatic review scores were entered.

Separate H100 GPU1 only, independent e1b-tts environment (Python3.12.13, qwen-tts0.1.1, torch/torchaudio2.8.0+cu128, transformers4.57.3, 103 packages checked). Other GPU0 PIDs2019086/2088852 remain. Worker2100581 exited; GPU1 returned to14MiB used/95306MiB free (2026-10-20 snapshot). No apex access, service/environment replacement, subagents, staging, commit or push. New resource/overwrite/query guards: observed3 failing tests before implementation; complete local suite8 passed.

Next: wait for the user to accept both candidate hashes. Then freeze the video manifest; do not install LongCat or render the four clips before confirmation. Four jobs remain awaiting_audio_confirmation and frozen=false. E0/E1 evidence unchanged and E1 remains NEEDS WORK. [Audio results](experiments/2026-10-20-e1b-full-expression/RESULTS.md) document load/generation/process timing boundaries, sources and current limitations; final verification is in audio_final_checks.json there.


## 2026-10-20 E1b video execution checkpoint

User accepted both exact WAVs and authorized four videos. Frozen manifest1e80a7f9… binds voices, source portraits and configurations. MuseTalk female/male completed (process23.916/23.607s including loads). LongCat isolated stack and41.737GiB pinned weights ready. First female generation completed the first diffusion segment but failed at export because ffprobe was omitted from the media preflight; retained as failed attempt1. Task-local ffprobe and an added regression guard are now verified (12 local tests pass); retry in a new attempt directory is running, male waits behind a full decode/source-tail checkpoint. No finished LongCat clip or quality preference claimed yet. All earlier setup/source-copy failures are retained. No apex access, shared service changes, staging, commits, pushes or subagents.


E1b resource checkpoint:3/4 delivered. Female LongCat attempt2 passed native full decode and source-tail check (process270.721s); all three local clips passed audio integrity and per-frame face detection (382frames). Male attempts1/2 were refused before diffusion when another project’s finite training coordinator used GPU1. Fresh proc metadata confirmed foreign ownership; no external task was stopped. Remaining attempt3 is waiting without GPU allocation for coordinator2148048 to exit, then rechecks stable idle. No model/audio/prompt/seed changes; existing outputs remain. Local final analysis waits for the fourth file; human video acceptance remains pending.


The external queue completed. Male LongCat attempt3 began only after stable idle and registered worker2174487 in NVML before CPU loading; the existing PID-based idle check can now see this ownership. All prior failures/source variants retained. Final four-way preview remains pending the last render; no video quality score or acceptance is invented.


## 2026-10-20 E1b four-video comparison delivered

User accepted both source voices. Four role-matched MuseTalk1.5/LongCat1.5 videos completed, with frozen manifest1e80a7f9… unchanged. Complete process times including loads: MuseTalk23.916/23.607s, LongCat270.721/267.728s; native512×512 /640×608,25fps. Full decode/source-audio checks4/4, all516 frames tracked/inspected, browser playback4/4 with no media or warning/error logs. Counterbalanced A/B preview opened in Codex IAB at http://127.0.0.1:51894/index.html (loopback PID20941), left unrevealed. Video human acceptance remains pending; old E1 remains NEEDS WORK.

[Results and bounded next experiments](experiments/2026-10-20-e1b-full-expression/RESULTS.md) document model-estimated video leads120/80ms for MuseTalk female/male,80/40ms for LongCat, dynamic-expression benefit visible in frame inspection, and hand entry at the lower crop edge. These estimates/observations do not replace continuous human audiovisual review or prove a backend winner. Next: review the four originals, then only if worthwhile test constrained gestures/half-body reference, derived neutral ending and a separately versioned sync comparison. No new grid, OmniAvatar/Hunyuan or E2 integration started.

Eight video attempts retained:4 successful, MuseTalk import-copy failure1, LongCat ffprobe export failure1 and selected-GPU resource refusals2. The final male worker reserves a minimal visible CUDA allocation before CPU loading, after the external finite queue exited; this reduces the observed idle-detection race but is not a machine-wide atomic lease. No foreign queue was stopped/changed. Final environment verified2026-10-20: own workers exited; GPU1 returned to14MiB/no compute PID, GPU0 original2088852 and foreign2154793 retained. No apex access, shared environment/service modification, subagents, staging, commit, remote or push. Final integrity evidence is video_final_checks.json; both READMEs and routes synchronized.

Final E1b verification2026-10-20:12 local tests pass;36 E0 inputs structurally valid, frozen manifest and original12 E1 video hashes unchanged;4 served preview hashes match. 27 Markdown files/319 local links checked, zero missing targets. No HEAD/staged files/remotes. Human video acceptance remains pending.


## 2026-10-20 E1b comprehensive quality review complete

Assistant technical/visual review completed with NEEDS WORK; [comparison](experiments/2026-10-20-e1b-full-expression/quality-review-v1/REVIEW.md) and [next experiments](experiments/2026-10-20-e1b-full-expression/quality-review-v1/NEXT_EXPERIMENTS.md). Inspected516 mouth frames,108 full-framing samples,48 matched-time mouth details and68 continuation frames; native hand examples retained. Same frozen inputs and old results locked; user video fields untouched. Whole SyncNet curves reproduced4/4,400ms signed controls exact8/8; strict windows retain120/80/80ms leads and male LongCat40/40/80ms. This is a post-hoc model/visual audit, not direct human audiovisual acceptance.

Decision: prioritize LongCat for bounded offline presentation optimization; MuseTalk stays low-cost mouth/regression baseline; neither is signed off for polished or real-time delivery. LongCat adds motion but excessive mouth/brow emphasis, bright/block-like teeth and crop-edge hand entry remain. No confirmed extra-finger anomaly; no gross3.72s identity break found. Fixed official source confirms distill8steps/CFG1/1 and no negative-prompt embedding branch at these CFG values. Next plan: local0/40/80ms video-delay comparison, then2 LongCat positive-prompt constrained clips; only if effective add2 derived300ms neutral-tail clips. No new render/model install yet.

Local preview lifecycle recovered: previous own server had exited, cached female metadata caused pending playback; restored same127.0.0.1:51894 URL, own PID22743, media unchanged. Environment last verified2026-10-20: this review uses local CPU only, no SSH/apex or remote-GPU refresh; prior H100 snapshot is historical. No agents, staging, commits, remotes or pushes. OriginalE0/E1 and video/human-review hashes verified separately in quality-review-v1/verification.json.

Comprehensive review final verification2026-10-20:4 original outputs and12 oldE1 hashes unchanged;4fresh decode/audio/browser checks,4whole sync curves reproduced,8signed shift controls exact,12existing tests pass, overwrite guard preserves prior diagnostics. 31Markdown/368local links, zero missing targets. No new render/remote access/staging/commit/push; human AV ratings unchanged.


## 2026-10-21 E1c execution checkpoint (completed below)

User authorized continuing the bounded plan. New manifestc7081319… freezes2LongCat original-audio controlled-prompt jobs; parentE1b media/metrics/user ratings remain unchanged. Six local0/40/80ms picture-delay variants generated with exact decoded-YUV source-frame preservation and unchanged acceptedPCM speech prefix plus exactzero tail. Added3 meaningful delay/content/overwrite checks, full15tests pass. Numeric analysis restarted after a local evidence-directory error; original failed log/source preserved. No human sync preference inferred.

SeparateH100 read-only preflight2026-10-21 America/Chicago:GPU1 idle14MiB/95306MiB free; GPU0 service2154793 left running. Two controlled-prompt jobs run serially in newe1c-controlled root, reusing earlier source/weights/environment read-only and own cache; worker reserves a visibleGPU PID beforeCPUloading. This cooperative check is not an atomic shared lease. No apex, shared-service/environment change, agents, staging, commits or pushes. Qtail remains conditional on both role results; no broadergrid/otherbackend.


## 2026-10-22 E1c complete — prompt-only gate not met

[Results](experiments/2026-10-21-e1c-controlled-expression/RESULTS.md):6 local0/40/80ms picture-delay derivatives preserve all decoded source frames and accepted PCM speech prefix; no new TTS.2 controlled-prompt videos267.418/263.161s process includingloading,640×608/25fps,124+134frames, full decode/audio2/2. All258mouth/lower-edge frames and continuation/ending details reviewed. Hands still enter the crop and large articulation/bright merged teeth persist; this prompt-only hypothesis does not establish gains. Qtail gate not met,0tailrenders. Whole SyncNet female/male remain-80/-40ms; strict windows-80/-80/-40 and-40/-40/-80ms. Model estimates are not human AV acceptance.

10/10files completely play in the new loopback gallery;3balanced sync rotations, counterbalanced motion pairs, reveal/singleaudio/pauseall verified. Leftunrevealed; userreviewsnull/unchanged.15tests pass. New results, bothREADMEs, technicalroute and voice_aicoordination synchronized; final_checks.json binds preservedoldinputs/media, executedprompt, localcopy/PCM/frame checks and preview. Existing preparation/analysis failure evidence retained.

Environment snapshot2026-10-22 04:56:44UTC (2026-10-21 23:56CDT):own2H100workersgone;GPU1=14MiB/no compute PID. GPU0original2154793 retained and foreign3580266arrived, untouched; no claim entiremachine loadunchanged. No apex/sharedservice/environment change, agents, staging, commit, remote or push. Next:human comparison, then separately freeze a stronger framing/motion-control hypothesis; no automatic grid, Qtail or otherbackend.

Final E1c verification2026-10-22:15tests pass;36 E0inputs/2avatars structurally valid;10parentlocked files and12oldE1videos unchanged; fresh6YUV/PCM preservation and8decode/audio checks pass;10served/browser files verified.33selectedMarkdown/345local links,0missing. Humanratingspending; noHEAD/staging/remotes. Verification: speech-avatar/experiments/2026-10-21-e1c-controlled-expression/final_checks.json.


## 2026-10-22 Public source backup

User authorized public source backup and README/index organization. Separate reviewed checkout: https://github.com/HenryVarro666/speech-avatar . Code/metadata only; private media, model/vendor trees and original frozen evidence remain local. Original experiment worktree is preserved, while the publication checkout has its own commit history.15CPUtests passed; no GPU/service operations. Publication receipts are tracked in voice_ai/PUBLIC_BACKUP.md.


## 2026-10-23 E1d reference-framing result

Two fixed-ROI input references were compared with E1c parents using unchanged accepted audio, prompt, seed and model. Face-box area26.62%→41.22% /27.07%→42.49%, but hands and emphasized articulation persist; tighter headroom is a tradeoff. Not adopted as a hand/expression fix. New full processes271.001/264.656s include loads,640×608/25fps;2decode/audio checks,258single-face frames,4browser playbacks and18CPUtests pass. Conditioned audio samples match the parents. Human AV ratings remain pending; next verify explicit motion/driving-video or rig interfaces before more inference. No apex, production deployment or public push.


## 2026-10-23 E1d review recovery

Completed videos were preserved and the local preview gained draft feedback export. Framing preference and explicit audiovisual acceptance are independent; defaults stay unreviewed, the export binds frozen clip hashes, and human records are never auto-filled.22CPUtests and4fresh browser playbacks pass; actual downloads, reveal, single audio and clean delivery were checked using isolated QA fixtures. No new render, model/service change or apex access; E1d remains NEEDS WORK and human acceptance pending.


## 2026-10-23 E1f-R男女分区动作对照完成

先核对显式控制接口，选LivePortrait原生模板分区：头姿/非眼表达0.65、眼区1.0、global1.0，复用原头像/已接受配音/E1c驱动。男女各attempt1成功，原生worker856.164/371.437s；共享CPU亲和性不同，见资源修订，不作速度排名。2片1254²/25fps、258单脸帧/原PCM母版通过；旧片/评分保留。深闭眼与轻头动/嘴幅可共存，下沿未见手部；牙齿仍软、末帧略张口和模型同步偏移未修，NEEDS WORK/人工接受null。[结果](experiments/2026-10-23-e1f-regional-motion/RESULTS.md)。

[本地四段预览](http://127.0.0.1:54462/index.html)；本轮独立目录2026-10-23-e1f-regional-motion，和另项E1f-independent-blink互不覆盖。[每步进展总账](experiments/PROGRESS_LEDGER.md)汇总问题→改动→证据→决定；早期格式不同，主要步骤/失败有记录，不声称完整逐命令历史。无apex、共享环境/服务改动、GPU推理、子代理、暂存/源码提交或推送。公开备份仅preview/diff。

E1f-R verification2026-10-23:26CPU tests,9script compiles,4browser endings/served hashes,258paired eye/mouth/lower-edge frames,29full/15native frames and4known nonzero sync controls pass. Source PCM exact,197locked parent files unchanged;human AVpending,NEEDS WORK. Noapex/shared-service restart/GPU inference/source commit/push.
