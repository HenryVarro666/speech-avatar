# E1 quality audit supplement

Registered 2026-10-20 before inspecting SyncNet scores. This supplements the frozen render protocol; it does not change or rerender its twelve outputs.

- Open the local twelve-video gallery and exercise playback. Record browser playback separately from visual frame inspection and audio listening. The assistant can inspect screenshots and decoded frames but cannot hear the browser audio through these tools; do not assign human audiovisual MOS or claim a human sync pass.
- Inspect every decoded frame in chronological lower-face contact sheets, plus whole-face samples and source portraits. Record specific timestamps for suspected lip closure, teeth, blending, identity or temporal artifacts. Static references cannot establish natural head motion or blinking.
- Run the official SyncNet model from `joonson/syncnet_python`, pin source and checkpoint hashes, first reproduce its official example (expected approximately offset 3 frames, distance 5.353, confidence 10.021). Keep calibration failures.
- Use its default crop scale 0.40, 224-square BGR input, 25 fps, 16 kHz MFCCs, five-frame windows, and ±15-frame search. Detect the first frame of each static avatar with official S3FD at scale 0.25 and threshold 0.9; keep that box for every clip of that avatar. This fixed-box adaptation is specific to these motionless references and is not a benchmark face-tracking pipeline. No crop selection using scores.
- Test audio shifts of -10 and +10 frames on every clip using the same extracted embeddings and valid overlapping windows; compare the recovered offsets against the unshifted offset. Reuse embeddings without retiming or editing the original videos. Also inspect the unshifted distance curves and confidence. A shift control tests sensitivity, not absolute perceptual correctness.
- Report offset, minimum distance and confidence per clip. No universal quality cutoff is inferred from the official example, and English-trained SyncNet scores on synthetic Chinese clips are supporting evidence only. Do not substitute source-audio preservation correlation for lip sync.
- Retain the original gate of >=10/12 acceptable clips spanning both languages and avatars. Without human continuous audiovisual ratings, final disposition is **quality not signed off**, even if technical and automated checks succeed. A completed audit may conclude NEEDS WORK; this is not a claim that all clips are proven perceptually bad.
- Use local CPU only in a new `.venv-quality`. No SSH, apex service access, GPU reservation, shared environment mutation, model inference rerun, staging, commit or push.

Primary reference: [official SyncNet implementation and example](https://github.com/joonson/syncnet_python). Exact versions and commands are recorded with results.
