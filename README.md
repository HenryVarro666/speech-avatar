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

E1 timing excludes shared model loading; E1b/E1c complete-process times include loading. They cannot be compared as identical benchmarks or used as voice-to-video conversation latency. E1c new processes took 267.418/263.161 s at640×608/25fps.

SyncNet estimates an 80 ms female /40 ms male LongCat video lead in the original E1b clips. Delay variants support a human comparison, not automatic sync acceptance. Human continuous audiovisual ratings remain pending; the >=10/12 quality gate has not passed.

## Experiment records

[Stage index](experiments/INDEX.md) links frozen plans, manifests, results and review decisions. Every failed attempt remains recorded. Public metadata includes prompts, hashes, aggregate diagnostics and scripts; recordings, portraits, rendered videos, contact sheets and model/vendor trees remain local.

## Verify or reproduce

Python3.12 CPU contracts do not run a rendering model:

```bash
python3.12 -m unittest discover -s tests -v
```

With the matching private inputs retained locally:

```bash
python3.12 scripts/validate_e0.py experiments/2026-10-20-e0/manifest.json
```

GPU inference requires the separately documented [MuseTalk](workers/musetalk/SETUP.md) / [LongCat](workers/longcat/SETUP.md) environments, approved model access and the frozen experiment plan. There is no one-command live avatar installation claim.

## Next work

1. Collect human judgments on the existing sync and original/new comparisons.
2. Freeze one stronger framing/motion-control hypothesis; prompts alone did not establish a gain.
3. Require a visible quality improvement before conditional neutral-tail generation.
4. Treat browser real-time rendering and audio-agent integration as separate future stages.

[Technical scope](docs/TECHNICAL_ROUTE.md) · [Current state](PROJECT_STATUS.md) · [Publication scope](PUBLICATION.md) · [Workspace](https://github.com/HenryVarro666/voice-ai-workspace).
