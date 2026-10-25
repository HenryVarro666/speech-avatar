# E1f-R quality protocol

Recorded before either new output is inspected. One frozen recipe/two roles, no aesthetic retry. Primary comparison is same-role E1c LongCat driver versus regional LivePortrait candidate; female E1e global0.65 is historical secondary context. Backend/face-resolution effects are confounded; do not attribute improvements to gain values alone.

## Technical gates

Both new videos must fully decode at25fps with124/134frames and4.96/5.36s audio, original24kHz PCM16 sample counts119040/128640 exact in separate PCM masters. Native H264 elementary streams must match remuxed review MP4/master; original driver files and parent records unchanged. One tracked face per frame; provide complete eye/mouth/lower-edge sheets and sampled full frames. Record each failed attempt and successful count, no overwrite.

## Observations to report separately

- Hands: inspect every lower-edge frame in both source/candidate; count visible hand-entry intervals when present. New background shoulders come from still-image pasteback, so absence of hands establishes only containment for these clips, not hand generation or anatomy repair.
- Teeth: inspect every mouth frame, maximum opening, onset/offset and native-size details. Report bright fused slabs, blurred boundaries, tooth/gum instability, mouth-corner deformation and any open-mouth ending. No teeth identity/anatomy score is invented; no beautifier/face-restorer or secondary lip model is added.
- Expression: full playback plus all eye/mouth frames, pose extremes, neck/hair mask boundaries. Report degree of head movement and brow/mouth emphasis; static-frame or landmark ratios cannot certify naturalness.
- Blink diagnostic: same203-landmark measure as E1e. Event=at least2frames below0.60of within-clip mean-eye-openingP90, bounded by open frames. Also report both-eye closure at<=0.15of within-clip per-eyeP90; require visual iris coverage before calling a complete blink. Failure does not trigger rerender.
- Sync: tracked face-crop CPU SyncNet and±400ms known-shift controls. Report signed offset in40ms steps, confidence and controls; do not tune output to this score. Inspect final300ms audio/last image; preserve endings rather than fabricate neutral tails.

## Decision

Assistant technical/visual status and actual human AV acceptance are independent. Keep all human fieldsnull until the user gives real feedback. A candidate may reduce hand risk or excessive mouth amplitude while still NEEDS WORK for teeth, eyelids or sync. If gains do not meet the intended quality change, retain the negative result and stop; no automatic next backend, parameter grid, new TTS or deployment.
