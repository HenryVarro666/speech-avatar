# GPU use and next bounded benchmark

2026-10-24. Goal: realtime assistant/interpreter display, with a single audio owner.

## Already measured versus pending

The local prototype uses WebGL2 through ANGLE Metal on Apple M4 Pro for textured portrait drawing. HeadAudio's small MFCC/Gaussian classifier runs in an AudioWorklet on the CPU. This is local low-cost streaming animation, not CUDA neural image generation. Browser rAF cadence is neither neural inference time nor physical display latency.

Separate H100 read-only snapshot at20:56:48CDT shows both95,830MiB cards at100%utilization, with foreign compute jobs. Original service2154793/2184143 startup times remain. No allocation/install/remote write or shared-service change was performed. See gpu-preflight.txt. VRAM availability alone does not justify sharing a busy card. CUDA benchmark remains pending; there is no measured speedup number for this round.

## Neural path

Prefer existing MuseTalk as an arbitrary-audio neural mouth baseline. Existing LivePortrait can consume explicit motion/retargeting controls, but replaying an old driver cannot pronounce a new utterance. A streaming audio-to-expression generator or separately validated phoneme/viseme-to-retargeting adapter is still required for the more expressive neural path. Keep LongCat for offline complete-expression comparison while its first-output/throughput measurements do not meet streaming needs.

GPU acceleration is supported by the relevant neural backends. [Official LivePortrait speed table](https://github.com/KlingAIResearch/LivePortrait/blob/main/assets/docs/speed.md) measures individual modules on4090/PyTorch compile; those module numbers exclude upstream speech, complete preprocessing, transport, browser scheduling and display. Do not add them up and call the sum our end-to-end latency. [HeadAudio](https://github.com/met4citizen/HeadAudio) is a browser viseme detector; our pinned English model and five approximate mouth textures do not establish Chinese phoneme accuracy.

## Fixed next trial once a dedicated GPU is available

1. Recheck exact GPU UUID, compute PIDs, utilization, free RAM/disk and original service starts. Allocate one unused card cooperatively; abort if any foreign compute process appears before launch. Never stop or unload it. Use a new RAID directory and separate environment/ports, bounded1worker/concurrency1; no apex.
2. Freeze two independently selected new Chinese sentences, female/male accepted TTS configuration, portrait and code/model hashes before rendering. Old E1g80ms correction and old motion driver are not new-audio ground truth. Preserve all failed attempts. Keep held-out evaluation separate from development.
3. Reuse one neural mouth backend first. Cache reference preprocessing, keep model resident, use GPU inference/inference_mode/compatibleFP16 only after output equality/quality checks. Record device explicitly; do not silently fall back to CPU and label it CUDA. Exclude GFPGAN/detail restoration initially.
4. Record separate timestamps: process launch; weights ready; request received; first actual input PCM chunk received; first render submitted; first complete video frame emitted; first frame displayed; complete audio/video end. Use CUDA events plus synchronization for module timing and monotonic wallclock for pipeline timing. Report setup/coldload/warm runs separately and no CPU/GPU speedup unless identical scope/inputs/output resolution are compared.
5. Gate: warm first frame within200ms of available target PCM, sustained25fps andRTF<1; avatar-added audio hold≤40ms, no duplicated or lost audio. These are proposed acceptance thresholds, not current results. Verify audio sample accounting, signed sync error with an independent measurement, stop/stale/underflow handling and memory after20turns. Human Chinese naturalness/teeth/identity still separately pending. If the gate fails, retain browser/static fallback; do not expand to concurrent sessions.

## E5 continuation

Observe real sentence/PCM scheduling in an isolated DSH instance with the avatar switch off by default. Then test live ASR→translation/dialogue→role-matchedTTS→singleReplySpeaker→avatar, including24kHz boundaries, corrections, utterance IDs and barge-in. Report each upstream latency separately. The local fixture page and optional scheduling observer alone do not constitute deployed live interpretation.
