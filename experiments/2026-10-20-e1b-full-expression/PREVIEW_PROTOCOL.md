# E1b first-view A/B protocol

Written before opening the four-video user preview,2026-10-20. The selection report requests two role-matched blind comparisons. The numeric video-quality protocol uses labeled files for technical review; the user interface initially hides per-card backend, dimensions and timing, then reveals them on request. Neither the frozen inputs nor the preregistered numeric methods change.

- Two role groups, each containing the original MuseTalk and LongCat MP4. A/B assignments use a fixed seed20261020 and counterbalance the order across the two roles. No assignment depends on sync metrics or preferred appearance.
- Neutral filenames and poster names in the preview; copies must match canonical video SHA256 exactly. No cropping, timing changes, muting or re-encoding for the comparison. Native frames are letterboxed at equal display width.
- One audible video at a time. A/B identifiers stay fixed after revealing backend and complete-process timing. The mapping and source/video hashes are retained with the experiment.
- This is interface-level single blinding only: local source/files can be inspected, and visible animation differences may let a viewer infer the backend. It is not a formal double-blind study or a four-sample quality win rate.
- Browser QA may play/reveal/reload for technical verification. Leave the delivered page unrevealed, with no fabricated human video ratings. Prior acceptance of the voices does not accept these videos.
- User feedback can name female/male A/B in the conversation. Until actual feedback arrives, video_review.json remains pending; the page never launches new renders.
