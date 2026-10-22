# E1 MuseTalk offline lip-sync protocol

Date: 2026-10-20. Original protocol retained below. Execution completed for all twelve pairs; [quality audit](QUALITY_REVIEW.md) completed with NEEDS WORK / not signed off. The human >=10/12 gate has not passed. Follow-up audit methods were registered separately in [QUALITY_PROTOCOL.md](QUALITY_PROTOCOL.md).

## Inputs and controls

MuseTalk source fixed at `0a89dec45a0192b824e3cf4daf96c239440c5ed8`, version 1.5. Record every checkpoint revision and file hash. Two frozen fictional avatars × six development waveforms: four English and two Chinese, fixed trial order before inference. Held-out test audio is not used for tuning or E1.

Use 25 fps and a fixed output resolution/configuration; no face-enhancement, random best-of selection or re-synthesis of the output audio. Still-reference loops explicitly limit evaluation to mouth generation, not natural head motion. Record cold preparation/loading separately from warm generation.

## Execution and safety

Independent source, environment, models and output paths; no changes to DSH, voice bridge, ComfyUI, open-webui or training jobs. Snapshot GPU processes before and after. No concurrency with another experiment GPU process. Start only with a verified compatible environment and a conservative resource margin; defer rather than evict anything.

Initial smoke uses the first planned pair; its outcome remains in the trial ledger. Run remaining pairs only after a decodable output and available resource margin. Setup/checkpoint failures are setup attempts, not twelve fabricated render failures.

## Timing and evidence

- Use monotonic wall time. Start when the complete WAV is available and the render task begins; end at first usable frame (only if instrumented) and at complete encoded video. Missing first-frame observation stays null.
- Record model load, portrait preprocessing, inference/merge and encoding if available; report stage boundaries honestly when combined by upstream. Full wall RTF = task wall seconds / input audio duration. FPS does not establish causal streaming.
- Record trial id, input/asset/model/config hashes, exit status, output hash, video dimensions/fps/frame count/duration, decoded audio duration/correlation/alignment, memory and failure details.
- Preserve all attempts. Human visual review rates closed lips, teeth artifacts, identity drift and mouth/audio sync. Automated decoding or detection is not a visual-quality pass.
- Suggested visual gate remains >=10/12 acceptable videos spanning both languages and avatars. No acceptability claim until visual review; no real-time conversation latency claim from offline output.

## Stop conditions and recovery

OOM, unavailable resource margin, incompatible runtime or shared-service degradation stops this worker only. Leave frozen inputs, checkpoint hashes, setup logs and a resumable command. Never stop another job. Installation debugging is bounded to the first independent setup path; report unresolved blockers without claiming a completed E1.
