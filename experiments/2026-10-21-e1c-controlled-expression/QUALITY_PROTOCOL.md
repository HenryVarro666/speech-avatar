# E1c diagnostic protocol before new comparative metrics

2026-10-21. Reuse pinned SyncNet, S3FD and E1b crop geometry. LocalCPU4threads only. Qsync known frame mapping means parent smoothed boxes plus repeated prefix; report this as mapping, not a fresh detection result. Qmotion redetects every frame(conf0.9,scale0.25), chooses continuity byIoU,13frame median; save all boxes/counts. Fullffmpeg decode, actualframes/nativewidth/height25fps and image evidence retained.

Audio analysis16k mono only. Compare accepted speech PCM with output at original start, search±32ms, correlation≥.95 and|lag|≤20ms, original final300ms≥.95; compare decoded length to source+knownzero tail with[-20,+100]ms tolerance for codec padding. Qsync derivatives separately prove losslessYUV frame equality and unchanged24kPCM speech prefix/exactzero tail; AAC export is lossy and its metrics are not lip-sync metrics. No audio speed/normalization or cropping.

Whole SyncNet±15frames and strict valid windows0.60–2.00,2.00–3.40,3.40–source-duration-.80s; no wrapped/paddedfeature scoring,40ms resolution. Retain distance curves; all estimates are model diagnostics, never human acceptance. Compare Qmotion per-role whole/window offsets to parent; no score-driven parameter/crop retuning.

Inspect every chronological mouth and lower-frame image,16 fullframes plus3.40–4.04s allframes, native hand/teeth examples and final500ms. Log visibility, articulation/motion, identity, teeth/edges, any hand entry and continuation. Unknown anatomy is not passed; two roles need gains and no evident regression to continue Qtail. Even passing technical/visual checks does not auto-fill user video rating or choose a Qsync preference. No new reference/model/seedselection.
