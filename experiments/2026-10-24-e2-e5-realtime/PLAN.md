# E2–E5 realtime browser pilot

2026-10-24，America/Chicago。用户明确选择实时语音助手/口译方向，并要求新句稳定性、等待和出错恢复，询问GPU加速。本轮在现有speech-avatar内实现本机原型，按既定E2→E3→E4→E5边界；不访问apex、不部署、不提交推送、不用子代理。

## Architecture and fixed choices

One actual DSH ReplySpeaker owns PCM playback. Add optional read-only scheduling/reset observations at the real scheduling point; default behavior remains audio-only. Events carry epoch/utterance/chunk/sample-rate/sample-offset/context-start and a copied PCM block plus the source node for a silent analysis tap. Observer exceptions never block speech. Mirror the small source edit into DSH's existing identical plugin copy.

E2 compares idle/RMS/official pinned HeadAudio MFCC Gaussian-viseme analysis on the same audio clock. Use existing fictional portrait/5mouth-pose texture atlas and independent eye-blink patches, WebGL2 on the local GPU; approximate portrait puppetry is a technical prototype, not the previously accepted offline photorealism. HeadAudio model is trained on English synthetic speech; Chinese naturalness remains unaccepted. No TTS, ASR, translation or new LongCat driver is synthesized here.

E3 measures received-to-scheduled audio, scheduling lead, first active visual/context time and rAF intervals; these are browser scheduling/render observations, not acoustic glass-to-glass latency or physical display timestamps. No extra audio hold for avatar. E4 tests stop/stale epochs, late chunk/underflow, broken analysis model, delayed visual preparation, WebGL context loss/restore and recovery to a new utterance. If visuals fail, keep audio playing with a static portrait/RMS fallback. One audio owner, no duplicate soundtrack.

E5 imports the actual compiled DSH playback class into the local prototype and tests the observer/adapter with four frozen PCM fixtures (two accepted old voices + two E0devdifferent-content engineering stimuli). This verifies local playback integration, not live model/microphone/interpreter deployment. Native24kHz output and translation state remain upstream responsibilities.

## Steps and verification

- [x] Freeze sources/fixtures/old records; read-only GPU check. Both95.8GiB H100cards currently100percentbusy, so no neural GPU benchmark or package install. Document CUDA path/timing protocol; do not infer speed from a paper's per-module number.
- [x] RED→GREEN for pure timeline epoch/start/gap/offset/reset guards and viseme mapping. Run in Node; expose through Python unittest wrapper.
- [x] RED→GREEN for DSH schedule observer: exact start/offset/rate, observer errors isolated, stop resets and no stale/duplicate playback. Run existing plugin tests/typecheck/build, mirror bytes identically. No running service refresh.
- [x] Prepare private atlas/audio/vendor assets and self-contained WebGL2 preview with arbitrary local WAV input and four frozen fixtures; source code stays separate from private media/vendor/model files.
- [x] Browser compare3modes×4fixtures, actual complete playback, audio-clock/rAF telemetry and explicit fault controls; save raw exported receipts, screenshot, GPUrenderer string and limitations. Human quality staysnull.
- [x] Update bilingualREADME, route, both state/history logs and optimization ledgers. Public backup onlypreview/diff; no push. Mark E5partial and GPUbenchmarkpending until their distinct evidence exists.

## Self-review / workflow ruling

The existing approved E2–E5 direction plus the user's explicit instruction authorizes this bounded implementation; no repeated design permission gate. Use writing-plans/TDD/verification-before-completion inline, no subagent or commit/worktree helpers under user constraints. Do not overwrite or re-score E0/E1/E1g. A new GPU run requires a fresh resource check and quiet cooperative allocation; free VRAM alone is insufficient.
