# E5a execution ledger

2026-10-24 America/Chicago. Read both status entries, roadmap and E2–E5 pilot first. Parallel new-audio asynchronous experiment is actively using its own CPU group; do not touch it or count its outputs. User explicitly authorizes reviewed public push for this round. Existing source worktrees/index/history remain separate from five-repository source-only backup.

Read-only H100 preflight21:18:03CDT: both95,830MiB GPUs100%busy with foreign compute PIDs; availableRAM232,585MiB,96CPU. Original2154793/2184143 startup times unchanged. No CUDA allocation/shared environment install/apex. Existing local API-key environment variables absent; choose same fixed local1.7Bmodel, no cloud credential/payment dependency.

Pinned official qwen-tts0.1.1 adapter source hashes plus model revision and13model files verified. SeparateRAIDroot e5-live-tts-20261024/attempt1. Ownedworker2653863,loopback43151,CPUbf16/4threads/80–83cores/nice19, excluding parallel88–91affinity. Model load4.6449s after file verification; available-memory guard before import/load. Original shared runtime/weights read only, bytecode writes disabled. OptionalSoX warning retained; codec decoding does not invoke SoX, no installation.

TDD: codec3, job lifecycle3, proxy2 Python cases and3Node transport cases fail for missing modules before implementation, thenpass. Real threaded model-lock replacement/cancel-before-arrival tombstones, PCM context/sample offsets, missingend, badseq/ID and proxydrop are covered. Tests have no remote/model inference. Browser and actual model receipts remain distinct.

Initial smoke-01 request hit SSH forwarding startup race(Connectionrefused before any remote job). No inference output or model failure claimed. Forward became healthy; fresh smoke-02 completed:61actualcodecframes/117,120samples/4.88s;6PCMchunks. Worker firstPCM4.0224s, LMcomplete17.6110s, whole generation17.8347s; client received first4.123s/end17.907s. First chunk precedes generation completion, capturedcode rows exactly match official returnedcodes. Peak sampledRSS5,816,712KiB. CPU is slower than playback; do not call this realtime performance acceptance.

New browser page uses loopback50451/Macproxy93538 and SSHforward50032. Existing57383page/assets/evidence left untouched. Runtime replies never expose model paths/credentials. Request IDs explicitly override frozen fixture IDs during transport; stale/cancel guards checked before UI updates. Source voices are fixed presets, but new text/stream decoder/style are new conditions, humanAVnull.


Actual browser7requests: welcome/confirm complete; playing-time welcome→correction cancels old generation and completes new; injected two-chunk drop staysincomplete; explicit full retry and new male recovery phrase complete.5completed PCM/end hash and sample accounting/code-row/first-chunk-before-LM checks pass. Browser firstPCM3.133–5.363s/plannedstart3.183–5.415s; workerRTF3.135–3.591, maxscheduledgap2.840s; sampledRSS5.881–6.587GiB. CPU lifecycle works but realtimeperformance gate fails. Human microphone/ASR/translation/physical audio/crossbrowser/longrun remainpending.

Final36Python tests(includingNode wrappers),3JSsyntax and6Pythoncompile checks pass.270frozen prior experiment records unchanged,215selected local links/served hashes pass; original57383page preserved. ActualReplySpeaker source/module remains byte-identical to previous tested artifact. User-authorized source-only publication uses reviewed per-file8metadata list, newweb/e5source and existing scripts/workers/tests discovery; no parallel asynchronous experiment directory, PCM, model/vendor or runtime snapshots included. Source Git HEAD/branch/index recorded before publication.


Publication preflight1stopped on one generic-api-key finding: runtime-pin.json line4 is the verifiedSHA256of the installed official tokenizer source, not a credential. Add only the exact repo/path/rule/full-linecontext fingerprint to the existing reviewed nonsecretallowlist; no scanner disabled or broad file exemption. Regenerate candidate under the new policyhash.


Reviewed first successful candidate20261025T023931Z-459246: changes only reviewed source/metadata,0unreviewedscan findings after exactnonsecretSHAexception.4repositories have pending source/docs changes; local-speaker-lab unchanged. The last plan step is clarified as completed documentation/export preparation; actual user-authorized push and remote/sourceGit verification remain a separate checkpoint. Regenerate final candidate to bind this exact record before release.
