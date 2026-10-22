# Avatar experiment decisions / 数字人实验决策

Goal: a clear and expressive visual companion to speech. Scope: rendering, sync, cancellation and review; no ASR/dialogue/translation ownership. **Current quality decision: NEEDS WORK.**

| Stage | Frozen comparison | Evidence and decision |
|---|---|---|
| [E0](2026-10-20-e0/RESULTS.md) |12dev/24test synthetic clips;2fictional still portraits | Structural freeze, hashes and prompts; human audio acceptance separate |
| [E1](2026-10-20-e1-musetalk/RESULTS.md) |6 development clips ×2avatars, MuseTalk1.5 |12 decode/source-audio passes; first-frame/full-task median3.003/7.165s without shared load |
| [E1 quality](2026-10-20-e1-musetalk/QUALITY_REVIEW.md) |1,032mouth frames and continuous playback | Soft teeth/static head/endings;80–120ms estimated video lead; quality gate unmet |
| [E1b](2026-10-20-e1b-full-expression/RESULTS.md) |Same accepted female/male speech and portraits;MuseTalk vsLongCat |4videos; LongCat expressions present but hand crop/intensity/teeth remain |
| [E1b review](2026-10-20-e1b-full-expression/quality-review-v1/REVIEW.md) |516mouth/108full frames, sync offset controls | LongCat offline candidate;MuseTalk regression baseline; no polished/live acceptance |
| [E1c](2026-10-21-e1c-controlled-expression/RESULTS.md) |6local0/40/80ms picture-delay variants;2prompt-only new videos | No demonstrated prompt-only motion gain; conditional tail0renders; human AV pending |

E1b/E1c full-process timings include model loading and cannot be directly compared with E1's shared-load-excluded timings. SyncNet is a diagnostic, not human preference or semantic correctness. Public JSON/figures preserve numeric evidence; private media/contact sheets remain local and are explicitly marked when referenced.

Next decision: obtain human sync judgments, then freeze one stronger framing/motion hypothesis. Do not expand a parameter grid or neutral-tail generation without meeting the preceding quality gate.
