# E5b matched CPU / GPU streaming comparison

**Goal:** Use the accepted E5 model and PCM protocol to reduce first-chunk waiting and playback gaps, then repeat controlled interruption and disconnect recovery.

**Architecture:** Two new isolated workers on the independent H100 host, sharing read-only pinned model/runtime files. CPU and GPU use identical worker code, BF16/SDPA, seed, text, generation parameters, 12 codec frames/chunk and 25 context frames. One local loopback proxy routes an explicit backend selection; the existing ReplySpeaker and avatar clock remain common. The original CPU preview and other services remain available.

**Spec:** User request 2026-10-25 and E5a `../2026-10-24-e5-live-tts/PLAN.md`. No microphone, ASR or translation claim. Human AV acceptance stays null.

## Constraints and gates

- New RAID root `/mnt/raid/voice_ai/speech-avatar/e5-gpu-comparison-20261025`; no apex operations, shared package changes, foreign process signals or production deployment.
- Recheck exact GPU UUID, utilization, memory and foreign compute PIDs before allocation, after an owned CUDA reservation, before model load/jobs, while resident and at final verification. A cooperative guard is not an atomic scheduler lease. If the selected GPU becomes shared, exit only the owned worker.
- CPU affinity 80–83, four threads, nice19; GPU also four host threads, same affinity and priority. Load and one warmup per device are separate from measured paired requests; neither is strict system cold start.
- Four fixed utterances, CPU→GPU / GPU→CPU counterbalanced order, sequential requests. No parameter tuning inside the primary comparison. Cross-device sampling need not produce identical audio; verify each run's official code rows, PCM hash, offsets, samples and end frame independently.
- Engineering targets: warmed first PCM ≤1s, worker RTF <1, scheduled inter-chunk gap ≤20ms, valid complete stream. Four phrases are a development comparison, not a latency SLO or human quality acceptance.
- Repeat normal female/male, interruption during scheduled audio, correction, true proxy disconnect after two audio blocks, explicit retry, new recovery phrase and stale UI rejection. These are controlled client events, not human microphone trials.
- Source-only publication is authorized this turn; review backup manifest and diff, exclude private AV/model/vendor/credentials, then use the established five-repository backup workflow.

## Tasks

- [x] Add failing device-guard and backend-routing tests; implement minimal CPU-default GPU selection, guard and telemetry in `workers/realtime_tts/device.py`, `worker.py`, `scripts/e5_service.py`.
- [x] Extend the existing preview with optional backend selection and an independent output directory; retain the original model/protocol/player. Test existing codec, jobs, proxy, transport and timeline contracts.
- [ ] Freeze parent hashes; deploy only owned source copies, launch fresh CPU/GPU workers, save resource/load/warmup receipts.
- [ ] Run eight paired browser requests and GPU lifecycle checks; export scheduling data, gather worker receipts and source PCM hashes, and preserve failures without overwriting attempts.
- [x] Analyze timing/gaps/integrity, update bilingual guides, ledgers and coordination records; open final preview and save UI evidence.
- [ ] Review and push source-only public backups; independently verify remote commits, file hashes and unchanged original Git state.

## Review focus

GPU contention during loading or idle residence must release only our process. Default CPU operation must still hide CUDA. Unknown backend paths must fail before forwarding. Cancellation must retain its original backend after the UI switches. A dropped stream must never be marked complete or retried automatically. Faster synthesis must not mask sample truncation or leave cancelled audio scheduled.

The user has already approved the E5 direction, isolated execution and reviewed source-only push. Planning/testing skills are applied inline; no subagents or additional approval round is needed.

## Current disposition

CPU preparation completed separately (9 requests/7 complete/1 controlled cancellation/1 actual incomplete drop); its PCM/code proofs are not a GPU result. CUDA model load, warmup, paired primary comparison and GPU lifecycle remain unchecked because the resource gate has not passed. Preserve these open tasks rather than marking the experiment complete. Documentation and source-only backup can save this explicitly incomplete state.
