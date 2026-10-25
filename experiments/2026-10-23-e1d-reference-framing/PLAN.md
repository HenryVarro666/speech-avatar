# E1d reference-framing plan

2026-10-23, America/Chicago. Spec: the user requests one stronger LongCat framing/motion-control path, female/male one new clip each, preview and experiment records, no apex or commits/pushes. Execute inline using executing-plans; no subagents, no publish. Existing experiment/e0-e1 workspace stays in place. No initial commit/staging/remote is created.

## Decision before generation

Use **pre-generation reference-image framing** through native ai2v image conditioning. From each unchanged 1254×1254 fictional portrait, take the same fixed rectangle `[125,75,1129,1079]` (1004×1004, ~1.249× linear enlargement at equal output size). No redraw, interpolation, color change or final-video crop. Hair/headroom and shoulders will be reduced. Keep E1c controlled positive prompt, accepted WAV, seed42, model/source/worker, INT8/DMD8steps/CFG1/1,2segments, ref_img_index10/mask_frame_range3 unchanged. Compare new output with the corresponding unaltered E1c controlled-prompt parent. This tests one framing change, not a general pose controller or hand-anatomy repair.

Audit pinned/native runtime code and current official upstream first. ai2v preprocesses the image and inserts its encoded latent as the first conditioning frame; continuation reuses its anchor. Native ref_img_index/mask_frame_range change continuation reference insertion/attention, not explicit body pose, and cannot address first-segment hand entry. ref_target_masks belongs to dual-speaker spatial routing, not skeleton control. Current v1.5 distillation forces8steps/CFG1/1 and official docs require distillation; do not run an unsupported non-distilled CFG grid. No public pose/skeleton/control-video input is assumed from marketing.

Ruling: user delegated path selection and authorized two bounded renders; proceed without another design approval. HyperFrames entry reviewed; this is native-model experimentation, not an HTML motion composition. Exact lossless crop is model-data preprocessing, not a new generated artwork or a post-render correction. Preserve auditable pixels instead of stochastic image regeneration. Test its pixel content/hash/overwrite/bounds contracts before producing candidates. Reuse unchanged renderer and CPU diagnostics rather than refactor production code.

## Tasks

- [x] Audit and lock source references; create deterministic crop helper with failing then passing content/guard tests; freeze new inputs/manifest/protocol. Preserve parent evidence and user scores.
- [x] Independent H100 read-only resource/weight/source checks. New e1d-framing root/cache/output, read-only reuse of existing environment/weights/vendor. Stable idleGPU1 then visible own reservation;2serial jobs only, every failure retained, no foreign process/service signals. Do not use apex.
- [x] Retrieve/hash2native videos; full decode/audio, per-frame face/mouth/lower-edge, continuation/ending, same SyncNet protocol. Evaluate framing as face-box area fraction and head-center span relative to median face height; larger face pixels alone do not prove better texture or calmer motion.
- [x] Two counterbalanced original/new pairs, original full framing displayed without output cropping, one audiblevideo, hidden factor until reveal, user review null. Open/verify local preview.
- [x] RESULTS, execution ledger, both workspaces' status/evolution, bilingual README/index, reviewed public summary and public-backup preview/diff only. No push. New experiment include only after per-file review; raw media/source snapshots stay excluded.

## Gates / stopping

Exactly2successful new videos; no seed/prompt grid, noQtail/otherbackend. At least one clear reduction of hand entry per role with preserved identity/mouth and no obvious new framing/teeth/sync regression is needed before recommending this framing. Report negative/mixed results without further generation. Technical and assistant image checks do not replace human continuous audiovisual acceptance.
