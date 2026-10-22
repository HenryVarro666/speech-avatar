# MuseTalk E1 environment

Verified 2026-10-20 on a separate Linux dual H100 NVL host. One GPU is used; apex is not contacted. Independent root: `/data/speech-avatar-exx-20261020`. No shared Python environment or service configuration is changed.

## Pinned inputs

- Upstream source: TMElyralab/MuseTalk `0a89dec45a0192b824e3cf4daf96c239440c5ed8`.
- Python 3.10 virtual environment, PyTorch `2.0.1+cu118`, torchvision `0.15.2+cu118`, torchaudio `2.0.2+cu118`.
- [Inference requirements](requirements.inference.txt) omit unused Gradio, TensorFlow and training components. Compiled mmcv `2.0.1` comes from the official cu118/torch2.0 wheel index; the import was checked.
- Chumpy `0.70` requires a non-isolated build because its setup imports pip. Install setuptools `69.5.1`, numpy `1.23.5` and wheel in this new environment, then install chumpy with `--no-build-isolation` before the remaining requirements.
- FFmpeg 7.0.2 comes from imageio-ffmpeg `0.6.0`, linked under the isolated root's bin directory. Mac input conversion uses FFmpeg 9.0.2; distinguish those environments.

## Reproduce the stages

Create a new dedicated directory and virtual environment on the chosen GPU host; do not reuse or alter an existing service environment. Pin the source revision above and install the requirements and official mmcv wheel. Use the inference-only dependencies, not upstream's broad download/install shell script.

`download_models.py ROOT` downloads official MuseTalk 1.5, SD-VAE, Whisper tiny, DWPose, face parser and S3FD weights. It records resolved revisions and file SHA-256 in `ROOT/model_manifest.json`. Use an experiment-specific HF_HOME and cache; public downloads do not require an account token.

Copy only the six E1 development WAVs, two avatar reference loops, and [trial plan](../../experiments/2026-10-20-e1-musetalk/trial_plan.json), retaining the relative media paths. The runner verifies input hashes before importing the inference modules.

From the GPU host, with ROOT set to the dedicated experiment path:

```bash
CUDA_VISIBLE_DEVICES=0 TORCH_HOME="$ROOT/cache/torch" \
HF_HOME="$ROOT/cache/huggingface" MPLCONFIGDIR="$ROOT/cache/matplotlib" \
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PATH="$ROOT/bin:$PATH" \
"$ROOT/.venv/bin/python" -u "$ROOT/run_e1.py" "$ROOT"
```

The runner refuses an existing trial ledger, saves every completed/failed trial, stops after a failed smoke, and stops before a later trial if another compute process appears on the selected physical GPU. It does not kill other processes or start HTTP services.

Models load once per process. Each task includes frame extraction, audio features, landmarks, generation, compositing and encoding. The first-frame event is the first successfully written composited PNG, not GPU first tensor or browser presentation. Frame-writing observation and landmark synchronization add diagnostic overhead. Random seeds are not explicitly fixed in this first feasibility run; preserve output hashes and do not claim deterministic reproduction.

After running, retain `trials.jsonl`, `run_metadata.json`, input/config/weight hashes, dependency lock, relevant setup failures, and before/after resource snapshots. Decode complete MP4s and inspect visual quality before accepting E1.
