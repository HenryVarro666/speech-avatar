# LongCat E1b offline worker

Verified on the separate H100 host in the E1b run, 2026-10-20. No apex calls, shared service restarts or shared Python environment changes. Independent root: `/data/speech-avatar-exx-20261020/e1b-video`.

## Pinned sources and necessary weights

- Native [LongCat source](https://github.com/meituan-longcat/LongCat-Video/tree/6b3f4b8582a8bc3f20f795735f5383716c4ba794), commit `6b3f4b8582a8bc3f20f795735f5383716c4ba794`. Archive SHA256 `16d240be5dc81e729f18412dcde6b51156cf3a3a230277a1b1a7bc4e0ef94e48`.
- [Avatar1.5 weights](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar-1.5/tree/92016c71d5d318d0f5d84e4db30015a571484ab6), revision `92016c71d5d318d0f5d84e4db30015a571484ab6`: INT8 base, DMD LoRA, scheduler, Whisper-large-v3 safetensors/config/tokenizer, vocal separator/model metadata. No full BF16 DiT, redundant Whisper formats or demo media.
- [LongCat foundation components](https://huggingface.co/meituan-longcat/LongCat-Video/tree/03b55529b1d1d4045f5fbe14d65c8c6e8116b278), revision `03b55529b1d1d4045f5fbe14d65c8c6e8116b278`: tokenizer, UMT5 text encoder and VAE only. Not the foundation DiT or unrelated LoRAs.
- The two selected repositories total44 files /41.737GiB. Exact files and hashes are in the experiment's `longcat-model_manifest.json`; `longcat-weights_plan.json` records allow_patterns. Public downloads run without implicit account tokens.

## Environment and recovery records

Separate `.venv-longcat`: Python3.10.12, torch2.6.0+cu124, torchvision0.21.0+cu124, torchaudio2.6.0+cu124, transformers4.41.0, diffusers0.35.1, numpy1.26.4, audio-separator0.30.2, onnxruntime1.16.3. Full lock retained with E1b. Unused upstream UI/server packages are omitted; setuptools75.8.0 and wheel are installed for Triton imports.

FlashAttention2.7.4.post1 uses the official Dao-AILab release wheel for CUDA12 / torch2.6 / CPython3.10 / CXX11ABI=false, confirmed against the installed torch ABI. No system CUDA/compiler or global Python changes.

The first wheel extraction exhausted the default user-cache partition. The retry uses this experiment's data-partition cache. Only the torch2.6 cache archive newly created during this task was relocated into the experiment's data partition, with the original path retained as a link; other cache contents and installed environments were not removed. The first CPU import then exposed missing setuptools; installing it in the new venv resolved import. Original errors and retry results are retained, rather than counted as renderer quality failures.

All further HF, uv, TorchInductor, Triton, XDG and temporary caches are directed under the experiment root. ONNX vocal separation uses the pinned CPU runtime; its warning about no CUDAExecutionProvider is retained. The main video model uses the selected H100 GPU.

## Running a frozen job

`run_pilot.py --job descriptor.json` is launched by this environment's `torchrun --standalone --nnodes=1 --nproc_per_node=1`. The descriptor names a root and trial_id; `workers/pilot_common.py` verifies manifest sidecar, accepted voice hash, source media, continuation coverage, absence of an existing output, and the selected physical GPU UUID before heavy imports. `CUDA_VISIBLE_DEVICES` must be that UUID. CPU thread counts are4.

The native path is ai2v, avatar-v1.5,480p, INT8 plus distillation. Effective steps8 / text and audio CFG1.0, source sampling seed42, context_parallel_size1. Native aspect-ratio bucketing produced640×608 for these portraits; the MuseTalk reference/output is512×512. For both accepted waveforms, two segments generate173frames /6.92s before native export trims to the source-audio length. No external services are unloaded and only one GPU is visible.

The wrapper observes native vocal separation, saves its waveform, and captures the resampled/padded conditioning waveform. It does not skip separation, replace the export audio, alter prompts after scoring, or retime video. The final delivery is `video_continue_2.mp4`; the initial3.72s intermediate file intentionally covers only the first segment and is not a delivered reply.

`generate_ai2v` and `generate_avc` are timed with CUDA synchronization. The first completed segment file is a distinct event; it is not a first saved frame or browser first image. Each CLI process reloads its models. Complete process times include imports, all loads, separation, generation, encoding and exit observation; the2s resource polling can add up to about2s. Torch allocator peaks and2s card-memory samples are separate measurements.

Every retry uses a new attempt directory, keeps prior logs, and appends to attempts/process ledgers. Failed and successful attempts are preserved. The user-facing MP4s are copied only after native generation succeeds and are then fully decoded/audio-checked locally. Dynamic face tracking and SyncNet diagnostics follow the preregistered E1b video quality protocol; they do not replace user video review.

## Media tools and shared-GPU coordination

The first female attempt reached diffusion but export failed because ffprobe was absent. Preflight now requires both ffmpeg and ffprobe. Only this task's bin directory received the checksum-verified BtbN ffprobe n9.0.2-29-g6dfaba896f-20261020 (linked from FFmpeg.org); the existing task-local ImageIO ffmpeg7.0.2 remains. Exact archive/binary hashes are in `video-media-tools.json`. Local analysis uses Homebrew ffmpeg9.0.2, whose AAC padding handling differs: native female smoke decoded32ms extra padding; local analysis trims that padding. Neither is a measured lip-sync offset.

Two male attempts refused before diffusion because a separate project's finite GPU queue became active. No foreign process was stopped or changed. A CUDA context alone was absent from NVML compute-PID queries during CPU loading, creating an idle-detection race. The final wrapper allocates one unused CUDA element before heavy native imports, synchronizes, and verifies its own PID is listed; torch.empty does not consume sampling RNG. Male attempt3 registered PID2174487 and succeeded after the external coordinator had exited and10s stable idle passed. The earlier source snapshot and both refusals remain in the ledger. This improves visibility to the existing PID-based checks; it is not an atomic machine-wide GPU lease. Future shared use needs a common cooperative lease rather than assuming a momentary idle snapshot grants exclusivity.

Final 2026-10-20 snapshot: this task's workers exited and selected GPU1 returned to14MiB used, with no compute PID. GPU0 retained the original2088852 and another project's2154793; no claim is made that unrelated occupancy stayed constant. Evidence: `video-environment-after.json`. No apex was accessed.


## Canonical storage after the 2026-10-23 migration

Future H100 work uses `/mnt/raid/voice_ai/speech-avatar`; source `/mnt/raid/voice_ai/env.sh` before preparing a new task. The historical `/data/speech-avatar-exx-20261020` path is a compatibility symlink, so old frozen commands remain unchanged. This recovery only checked the path and GPU occupancy; both cards were busy with other tasks, and no renderer or service was started. Recheck resources for any future inference. Local E1d feedback export is CPU/browser-only; see the [review guide](../../docs/E1D_REVIEW_GUIDE.md).
