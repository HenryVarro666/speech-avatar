# E0 frozen inputs

Date: 2026-10-20. Structural E0 freeze completed; human listening is separately pending.

- 36 synthetic clips: development 6 English + 6 Chinese; test 12 English + 12 Chinese. Two local macOS voices per language, balanced: each voice supplies 9 clips overall. Family/text/hash validation found no duplicates or cross-split family overlap.
- All derived audio is mono PCM16, 16 kHz; durations 2.55675–8.5345625 seconds, no clipping/cropping of the source content. Raw AIFF and derived WAV retained privately. Text is explicitly labeled synthesis input, not a human-confirmed transcript. No real microphone or native speech model recordings are included.
- Two fictional adult portraits generated with the built-in image tool; frontal face and closed mouth inspected in the tool output. 512×512, 25-fps, two-second static-loop MP4 references derived from the originals. These cannot evaluate blinking or head motion; E1 evaluates mouth replacement on them.
- [Manifest](manifest.json), [SHA-256](manifest.sha256), [waveform validation](validation.json), [corpus](../../assets/corpus.json), [avatar metadata](../../assets/avatars.json) and [prompts](../../assets/avatar-prompts.json) are retained. Media stays under ignored data/private; speech redistribution rights have not been assumed.
- Manifest SHA-256: `6c8a132f01101f447819f6cc708c2fe27d8d1fc88244f36a631a8cdb73911920`.
- Five negative integrity tests demonstrated failure before implementation and passed afterward: altered file hash, missing provenance, cross-split family with a different voice, silent waveform, and modified manifest metadata. The last was added during final review; the original frozen manifest itself remains unchanged.

Local environment: MacStudio arm64, Python 3.12.15, FFmpeg/ffprobe 9.0.2, installed macOS voices. E1 host verified separately as a dual H100 NVL machine, with each GPU reporting 95,830 MiB total and roughly 95,306 MiB free at the first read-only check. This is not apex. Independent work uses its /data partition; no apex connection or service changes.

Decision: freeze this synthetic/still-image dataset for E1 technical feasibility. Human transcript listening and visual acceptability of generated video remain explicit later quality checks. Do not claim general microphone, natural motion or multilingual model performance from this setup.
