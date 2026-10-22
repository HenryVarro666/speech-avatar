# E1b Chinese listening candidates

This worker prepares audio only. Avatar rendering remains blocked until the user accepts both candidates. It never calls apex or starts a remote HTTP service.

## Selection and isolation

- Official [Qwen3-TTS CustomVoice model](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice), revision `0c0e3051f131929182e2c023b9537f8b1c68adfe`; public download, no account token required.
- Official [Python API](https://github.com/QwenLM/Qwen3-TTS): `generate_custom_voice`, Chinese, Serena / Uncle_Fu. The model card describes these as Chinese female / male presets. This metadata does not establish listener preference or persona fit.
- A new environment at `/data/speech-avatar-exx-20261020/e1b-tts/.venv` on the separate H100 host: Python 3.12.13, qwen-tts 0.1.1, torch / torchaudio 2.8.0+cu128, transformers 4.57.3. Existing MuseTalk and service environments are not changed.
- Install via the existing uv executable into this new environment; full dependency lock and check are saved with the experiment. Cross-filesystem hardlink fallback copies packages; it does not modify another environment.
- BF16 and PyTorch SDPA; no FlashAttention compilation. CPU inference/installation threads bounded to four where applicable.

## Execution

The worker consumes the experiment's `tts_request.json` and a local `model/` directory whose files are bound in `model_manifest.json`. Select the UUID of a currently idle GPU in both `CUDA_VISIBLE_DEVICES` and `--gpu-uuid`. It checks compute processes before allocating CUDA, before model load, and before/after each voice. It refuses to overwrite audio or run metadata. It never stops external processes.

`generate_custom_voice.py ROOT --gpu-uuid UUID` is run with the environment's Python, `CUDA_VISIBLE_DEVICES=UUID`, and `OMP_NUM_THREADS=4 MKL_NUM_THREADS=4`. Root points to the independent E1b TTS directory. Actual request, script, weights and package hashes are retained in the experiment; repeat attempts require a new output directory and log entry.

The same text and style instruction are used for both presets. Seed42 is reset before each voice; this does not promise bitwise reproduction across machines. Model defaults come from the pinned generation_config.json; max_new_tokens is explicitly limited to1024. This is file synthesis, not a streaming latency experiment.

For each candidate, preserve the model float32 array and a PCM16 WAV. The latter introduces only quantization: no resampling, trimming, speed adjustment, normalization, or extra silence. Actual length is measured after synthesis; the 5–6s goal must not cause truncation of a natural ending. A longer accepted clip requires sufficient LongCat continuation later.

Load timing starts immediately before `from_pretrained` and ends after CUDA synchronization. Generation timing starts before `generate_custom_voice` and ends after CUDA synchronization, excluding file saving. Download and setup are separate; neither timing is speech-end-to-first-sound or strict cold-start latency.

## Validation and handoff

Run the shared-GPU/overwrite tests and the existing integrity suite locally. After copying back candidates, check SHA-256, full WAV decode, finite samples, clipping, source/raw quantization consistency and actual duration. Listen through the loopback-only preview. Browser completion and automated signal checks do not supply human naturalness/content/persona approval.

Keep `audio_review.json` pending until the user replies; preserve source hashes with the review. Do not create the frozen video manifest, install LongCat, or render any of the four videos during this audio-only request.
