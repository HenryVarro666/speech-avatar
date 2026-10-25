# LivePortrait explicit motion experiments

The isolated E1e pilot — local-only artifact: `../../experiments/2026-10-23-e1e-motion-control/RESULTS.md` uses the official [KlingAIResearch source](https://github.com/KlingAIResearch/LivePortrait/tree/9b294b3d0536135442ea73cb01e6cb3ca7029dd3), commit9b294b3d0536135442ea73cb01e6cb3ca7029dd3, and official KlingTeam human weights revision82a4fa6735ca58432b6ce39301b4b9ee066dea47. Private setup records bind8weight files by SHA256. This is a video-driven face layer; it has no audio-to-expression model or full-body skeleton controller.

The existing independent environment is CPU-only PyTorch2.3.1 and ONNXRuntime1.18.0. Do not install into or change a shared service environment. Worker constructors explicitly forward force-CPU to both wrapper and Cropper; ONNX sessions are restricted to CPUExecutionProvider,4intra-op/1inter-op threads. CUDA is hidden and must be unavailable. Set all temporary/cache/output paths inside the new trial, nice19 and a verified4-core affinity. Read resources before each new job; a prior GPU/CPU snapshot is not an allocation lease.

`motion_template.py` implements the [E1f-R frozen recipe](../../experiments/2026-10-23-e1f-regional-motion/PLAN.md). It copies the native template, scales relativeSO(3) rotations and relative translation/scale, and applies separate expression/eye gains. Official eye-region indices are11/13/15/16/18. The original template, learned canonical keypoints and source media are not mutated. Global native multiplier must be1.0when using this recipe, otherwise motion is attenuated twice. Eye/lip retargeting remains disabled because the upstream relative branch can reconstruct target from source and replace pose.

The task-local worker wraps native template extraction; vendor algorithm files remain untouched. Raw and controlled templates plus generated source/target keypoints are retained privately. Source-image pasteback can exclude the driver's body/hand gestures; this does not synthesize correct hands or guarantee tooth detail. Eye-region latent indices are learned controls and may interact after stitching; verify final image landmarks and visual playback separately.

CPU contract checks:

```bash
.venv-quality/bin/python -m unittest discover -s tests -p test_motion_template.py -v
```

Successful-count/overwrite guards prevent aesthetic retries. A new render requires a separately frozen manifest and plan; do not rerun a completed experiment. The current scripts preserve every technical failure. No service, real-time, microphone or human-quality acceptance is implied by an offline MP4.
