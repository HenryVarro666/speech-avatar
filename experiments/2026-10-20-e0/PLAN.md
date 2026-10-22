# E0 frozen input and asset protocol

Date: 2026-10-20. Status: executing, before E1.

- 12 development clips: six en, six zh. 24 held-out clips: twelve en, twelve zh. Text families do not cross splits; voice variants of a family remain together. Two installed system voices per language, balanced when available.
- Synthetic, local-only audio; retain intended text, generation command, voice, source/derived hashes, PCM parameters and exact crop/sample range. Duration target 2–15 seconds; resample once to mono PCM16 at 16 kHz, with no content trimming unless separately recorded.
- Two distinct fictional adult portrait assets generated with the built-in image tool. Save prompt and generation metadata; inspect frontal face/mouth, then derive 25-fps static-loop MP4 references for MuseTalk. These are synthetic still references, not motion clips or evidence of blinking/head-motion quality.
- Media and raw intermediates remain ignored under data/private. Track metadata and SHA-256. Generated speech redistribution rights are not assumed; outputs remain local pending rights review.
- Structural completion requires count/language/voice balance, split-family integrity, no duplicate audio hashes, nonempty provenance, decoded media validity, non-silent PCM, duration compliance and two avatar references. Human listening/transcript confirmation is a separately reported quality check; E1 uses the recorded waveform regardless of intended-text errors.
- Resource preflight is independent of data freezing. Capture local tools; before E1 check the actual inference host, memory and external GPU processes. No existing process may be stopped or environment altered.
- Freeze manifest and its SHA-256 before the first E1 render. Any amendment gets a new manifest/reason; never overwrite a frozen input silently.
