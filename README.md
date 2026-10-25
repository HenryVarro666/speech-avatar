# Speech Avatar

**English** · [简体中文](README.zh-CN.md)

**Testing whether audio-driven portraits can become a clear, expressive visual interface for a voice agent.**

## Problem and intended use

A voice agent with a portrait needs more than moving lips. The identity must remain stable, speech and video must align, expressions must look natural, and hands/teeth/endings must not distract from the spoken message.

This lab develops the rendering and review layer for a future speaking assistant or interpreter-style interface. ASR, dialogue, translation and booking state belong to other projects. A working offline renderer is not a deployed interpreter or a real-time avatar.

## Methods

Frozen synthetic speech and two fictional still portraits drive offline MuseTalk1.5 and LongCat1.5 comparisons. The review combines full decoding/source-audio checks, tracked mouth/full-frame inspection, SyncNet offset diagnostics and counterbalanced local human previews.

MuseTalk is retained as a lower-cost mouth/regression baseline. LongCat is the offline full-expression development candidate. Neither has passed polished-video or live-conversation acceptance. OmniAvatar and Hunyuan have not been run here.

## Current results and decisions

| Stage | What was done | Finding and decision |
|---|---|---|
| [E0 inputs](experiments/2026-10-20-e0/RESULTS.md) | 12 development + 24 held-out synthetic clips; two fictional portraits | Structural freeze; media stays local |
| [E1 MuseTalk](experiments/2026-10-20-e1-musetalk/RESULTS.md) | 12 offline pairs; median first saved frame / complete task 3.003 / 7.165 s, RTF1.999 | Decode/audio pass; soft teeth, static head/eyes and endings need work |
| [E1b comparison](experiments/2026-10-20-e1b-full-expression/RESULTS.md) | Same accepted female/male audio drives both backends: four videos | MuseTalk complete process 23.916/23.607 s; LongCat 270.721/267.728 s; expressions improve but intensity, teeth and hand entry remain |
| [E1b quality review](experiments/2026-10-20-e1b-full-expression/quality-review-v1/REVIEW.md) | 516 mouth frames, 108 full frames and synchronized details; model offset controls | Continue LongCat offline and MuseTalk baseline; NEEDS WORK |
| [E1c controlled continuation](experiments/2026-10-21-e1c-controlled-expression/RESULTS.md) | Six local 0/40/80 ms sync derivatives + two constrained-prompt LongCat videos | Prompt-only control did not resolve cropped hands/emphasized articulation; tail renders skipped by gate (0) |
| [E1d reference framing](experiments/2026-10-23-e1d-reference-framing/RESULTS.md) | Two fixed-ROI reference-image renders; same E1c audio/prompt/seed/model | Face area 26.62%→41.22% / 27.07%→42.49%; hands and emphasized expressions persist; not adopted as a fix |
| DUIX single segment — local-only artifact: `experiments/2026-10-23-duix-single/RESULTS.md` | One4.96s accepted voice/static portrait on H100;28.018s request time,16,702MiB sampled process peak | Lip generation works; static head/eyes,120ms estimated video lead and80ms missing picture tail; NEEDS WORK |
| E1e explicit motion — local-only artifact: `experiments/2026-10-23-e1e-motion-control/RESULTS.md` | One CPU-only LivePortrait render, existing portrait/voice/LongCat motion, multiplier0.65;323.408s | Head/eyelids move,3partial closures; mouth-openingP95−26.3%vs driver;80ms estimated video lead;NEEDS WORK |
| E1f independent blink — local-only artifact: `experiments/2026-10-23-e1f-independent-blink/RESULTS.md` |22learned eye frames over fixed E1e,341.509s CPU |3/3complete closures; outside-eyeYUV/102whole frames/AAC exact; human naturalness pending |
| E1g mouth sync and ending — local-only artifact: `experiments/2026-10-24-e1g-mouth-sync-tail/RESULTS.md` | Mouth-only80ms delay +0.48s silent picture/learned closure; original and sync-only controls | Offset -80→0ms; fixed6/6tail frames close; outside-mouthYUV/248eyeRGB/AAC exact; confidence decreases, human pending |
| E1h oral detail — local-only artifact: `experiments/2026-10-24-e1h-oral-detail/RESULTS.md` | Inner-oral lumaHF only: base/unsharp/boundedGFPGAN | +21.59%/-6.63%mean relativeHF-RMS; model not superior, not default; blinks/lips/tail/AAC exact, all sync0ms |
| [E2–E5 realtime pilot](experiments/2026-10-24-e2-e5-realtime/RESULTS.md) |4inputs×idle/RMS/HeadAudio, actual player clock and localGPUtexture portrait |12complete/sample checks,10fault/recovery checks; planned audio start51.6–81.9ms; prepared audio only; actual TTS follows in E5a |
| [E5a actual TTS](experiments/2026-10-24-e5-live-tts/RESULTS.md) |7newly generated requests/4Chinese texts/two voices; barge-in/drop/retry |5complete/1cancelled/1incomplete; firstPCM3.133–5.363s, RTF3.135–3.591; CPU realtime gate unmet |
| [E5b GPU comparison preparation](experiments/2026-10-25-e5-gpu-comparison/RESULTS.md) | Same-model CUDA route/ownership guard and CPU routing regression;41tests | 0 GPU inferences: resource gate blocked; CPU9requests/7complete/1cancel/1incomplete, firstPCM3.040–4.471s/maxgap2.696s; acceleration unverified |

E1 timing excludes shared model loading; E1b/E1c complete-process times include loading. They cannot be compared as identical benchmarks or used as voice-to-video conversation latency. E1c new processes took 267.418/263.161 s at640×608/25fps.

SyncNet estimates an 80 ms female /40 ms male LongCat video lead in the original E1b clips. Delay variants support a human comparison, not automatic sync acceptance. Human continuous audiovisual ratings remain pending; the >=10/12 quality gate has not passed.

E1d completed 2 new processes in 271.001/264.656 s including loads, at 640×608/25fps. Decode/audio 2/2, 258 single-face frames, 4/4 original/new browser playbacks and 18 CPU tests passed. Actual conditioning samples equal the parents; no final-video crop. Human AV acceptance remains pending.

DUIX service startup was16.570s and complete container time47.347s; neither is strict cold-start latency. Original output fully decodes at512×512/25fps,122frames; all119,040audio samples remain. Human AV acceptance is pending. The isolated H100 workspace now lives under `/mnt/raid/voice_ai/`, with original paths retained as compatibility links.

A later local DUIX continuation — local-only artifact: `experiments/2026-10-23-duix-single/CONTINUATION_RESULTS.md` adds one lossless+120ms picture-delay candidate:125frames/5.00s, all122original frames and4.96sAAC audio preserved exactly. The same model diagnostic changes−120→0ms; this post-hoc correction remains pending human comparison and does not change expression/detail quality. No new GPU inference.

E1d replay now includes a local feedback export: framing preference and explicit audiovisual acceptance are separate, defaults remain unreviewed, and exported JSON binds the frozen clips. Draft exports do not update human scores automatically. The recovery used no new renders;22CPUtests and4fresh browser playbacks passed. [Review and recovery guide](docs/E1D_REVIEW_GUIDE.md).

E1e tests an explicit video-driven motion layer:124frames at1254×1254/25fps,2.695GiB sampled CPU process-tree RSS, no CUDA work. All119,040source PCM samples are preserved in a separate master. Three eyelid dips remain half-closures; human AV acceptance is pending. Different backend/resolution prevents attributing all changes to the0.65multiplier.

E1f independently restores complete closure while preserving E1e's lighter head/mouth visuals:124frames/4.96s,2.766GiB sampled process-treeRSS; no CUDA. Only eye regions change, and all102nonblink frames remain exact. The80ms model-estimated sync lead and teeth/ending limitations remain.

E1g keeps E1f complete blinks/light head movement while delaying only the mouth by80ms. A fixed0.48s silent picture ending closes the lips after speech:136frames/5.44s video, unchanged4.96s audio and source-exact119,040sample PCM master. Full/early/late estimated offsets become0ms, but SyncNet confidence drops7.961→6.785 and its minimum distance worsens; this familiar-clip correction is not generalization or overall quality acceptance. All6fixed tail frames close; outside-mouthYUV,248eyeRGB patches and AAC remain exact. CPU worker38.089s includes5learned frames/two136frame composites/encoding/proofs; sampledRSS2.294GiB, noCUDA or service replacement. Human AV remains pending.

E1h retains E1g clocks, complete blinks and closed ending while testing oral texture. Light unsharp makes edges modestly stronger; bounded GFPGAN does not win and remains disabled by default. No tooth ground truth or human AV acceptance. One successful CPU worker takes125.811s including106model frames and two136frame encodes/proofs; sampledRSS2.049GiB. Deployment readiness — local-only artifact: `experiments/2026-10-24-e1h-oral-detail/DEPLOYMENT_READINESS.md` separates usable offline media from new-audio asynchronous staging and unvalidated realtime conversation.

A local realtime pilot now observes the actual DSH player, draws a five-pose portrait through M4ProWebGL2, and analyzes audio in a CPUAudioWorklet. It supports new content, source-ratePCM/localWAV, interruption/stale epochs and visual fallback. First active poses appear78–206ms after scheduled audio start; rollingrAFintervalP95 is8.8–9.3ms. These are engineering timings, not physical sync or live ASR/translation latency. E5a now connects actualTTS; Chinese naturalness/neural fidelity and live microphone/ASR/translation remain pending. [Run, recover and GPU route](docs/REALTIME_PILOT_GUIDE.md).

E5a now decodes/transports genuinely new TTS audio in an independent instance, keeping one player and explicit end/epoch contracts.5sourcePCM/end/sample checks pass; controlled playing-time interruption cancels old generation, and interrupted transport stays incomplete until an explicit new request recovers. Planned audio start3.183–5.415s includes actual TTS and differs in scope from E2prepared-audio50–82ms. CPU maxgap2.840s prevents low-latency use; human microphone/full interpretation/naturalness remain unvalidated. [E5 run and recover](docs/E5_LIVE_TTS_GUIDE.md).

<!-- e2-async-trial -->

The user retained the exact E1h light-unsharp clip. The independent new-audio asynchronous trial — local-only artifact: `experiments/2026-10-24-e2-async-single-user/RESULTS.md` now completes12new Serena utterances and12genuine MuseTalk mouth videos:1152frames,40.32s source speech, source-exact PCM masters and closed endings. Two complete12-video browser rounds,7process tests,9real backend checks and13browser checks pass. CPU worker98.474–266.092s (median140.119s), sampled process-groupRSS7.050–7.149GiB; no CUDA. Actual cancellation exits its owned group in0.228s and a99.426s fresh recovery reproduces the original hash. Sync generalization remains unaccepted: only8/20shift controls recover,2short clips are skipped, and human AV is pending. This fixed12-utterance trial remains separate from realtime/upstream integration and existing services.

<!-- /e2-async-trial -->

## Experiment records

[Optimization log](experiments/OPTIMIZATION_LOG.md) records why each change was tried, the controlled change, evidence, adoption decision and next dependency, including failures and skipped stages. Detailed plans/manifests/attempts stay in their original experiment directories.

[Stage index](experiments/INDEX.md) links frozen plans, manifests, results and review decisions. Every failed attempt remains recorded. Public metadata includes prompts, hashes, aggregate diagnostics and scripts; recordings, portraits, rendered videos, contact sheets and model/vendor trees remain local.

## Verify or reproduce

CPU checks require Python3.12, Node.js18+ and ffmpeg/ffprobe; they do not run a rendering model:

```bash
python3.12 -m unittest discover -s tests -v
```

Four regional-motion checks additionally require NumPy/OpenCV; without them they are explicitly skipped. The existing local quality environment runs the complete41-test suite:

```bash
.venv-quality/bin/python -m unittest discover -s tests -v
```

With the matching private inputs retained locally:

```bash
python3.12 scripts/validate_e0.py experiments/2026-10-20-e0/manifest.json
```

GPU inference requires the separately documented [MuseTalk](workers/musetalk/SETUP.md) / [LongCat](workers/longcat/SETUP.md) environments, approved model access and the frozen experiment plan. There is no one-command live avatar installation claim.

## Next work

1. Collect human content/voice/AV judgments on all12new utterances.
2. Diagnose synchronization in the new MuseTalk combination; do not generalize the familiar clip's80ms correction.
3. Keep the selected light unsharp; bounded GFPGAN remains off by default. Test exclusive-GPU latency separately.
4. Extend real new-text/TTS requests and live upstream integration only through a separately measured stage.

[Technical scope](docs/TECHNICAL_ROUTE.md) · [Current state](PROJECT_STATUS.md) · [Publication scope](PUBLICATION.md) · [Workspace](https://github.com/HenryVarro666/voice-ai-workspace).


## Regional video motion / E1f-R

[Two paired candidates](experiments/2026-10-23-e1f-regional-motion/RESULTS.md) use the existing role-matched voices/portraits and E1c drivers: pose/non-eye0.65,eye1.0,global1.0. Both1254²/25fps clips pass258face frames and source-exact PCM masters; CPU native worker times are856.164/371.437s under different shared-core conditions. Hands stay out and deep closures return with lighter articulation; soft teeth, endings and model sync offsets remain NEEDS WORK. Human AV acceptance is pending. [Step-by-step progress ledger](experiments/PROGRESS_LEDGER.md) links decisions, failures and evidence; it does not invent missing historical commands.
