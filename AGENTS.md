# speech-avatar collaboration

Read PROJECT_STATUS.md and the active experiment PLAN before work. This repository owns audio-driven visual rendering, synchronization, cancellation and replay. It does not own ASR, dialogue, translation or booking state.

- No commits, staging, remotes, pushes or deployment unless requested. Experiments originated on experiment/e0-e1; this public checkout contains the reviewed source snapshot.
- Do not start subagents unless explicitly requested.
- Do not stop/restart apex services, alter shared environments or unload other models. Use an independent directory/environment/process. Read-only resource verification precedes inference.
- E0 freezes 12 development and 24 test audio inputs, family-separated, plus two authorized avatar assets. E1 uses six development clips (four English, two Chinese) × two avatars.
- Preserve every attempt and failure. A static-image reference is not a recorded moving portrait. Synthetic input is not a live microphone trial; offline video throughput is not end-to-end conversation latency.
- Keep private/generated media, model weights, environments and vendor code ignored. Track hashes, provenance, prompts, numerical results and reproducible scripts. Never store credentials.
- Update PROJECT_STATUS.md and EVOLUTION.md after work; also synchronize the voice_ai coordination records. README.md is English, README.zh-CN.md Chinese; keep their features, commands and numbers aligned.
