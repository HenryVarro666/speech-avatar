"""Make a labeled evidence panel from exact source frames; no enhancement."""
import json
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT/'experiments/2026-10-20-e1b-full-expression'
OUT = ROOT/'outputs/e1b/quality-review-v1'
manifest = json.loads((EXP/'manifest.json').read_text())
tracks = json.loads((EXP/'video_face_tracks.json').read_text())
panel = Image.new('RGB', (4*256, 820), '#edf1f6')
draw = ImageDraw.Draw(panel)
for col, trial in enumerate(manifest['trials']):
    female = trial['avatar_id']=='avatar-a'
    name = ('Female / ' if female else 'Male / ')+('MuseTalk' if trial['backend']=='musetalk-v15' else 'LongCat')
    x = col*256
    draw.text((x+8, 8), name, fill='#102238')
    cap = cv2.VideoCapture(str(ROOT/trial['planned_output_path']))
    for top, index, region, label in [(30, 35, 'full', 'Full frame / 1.40s'),
                                      (318, 30, 'mouth', 'Mouth detail / 1.20s'),
                                      (552, 66 if female else 115, 'hands',
                                       'Lower frame / '+('2.64s' if female else '4.60s'))]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = cap.read()
        assert ok
        if region=='mouth':
            a,b,c,d=tracks[trial['trial_id']]['smoothed_boxes'][index]
            w,h=c-a,d-b
            frame=frame[int(b+.52*h):min(len(frame),int(d+.10*h)),int(a+.15*w):int(c-.15*w)]
        elif region=='hands':
            frame=frame[int(len(frame)*.66):]
        picture = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        size=(248,256 if region=='full' else 192)
        panel.paste(ImageOps.pad(picture,size,color='#152133'),(x+4,top+24))
        draw.text((x+8,top+5),label,fill='#102238')
    cap.release()
draw.text((8,798),'Exact decoded frames. Same audio within role. Display scaling only; no anatomy or sync acceptance implied.',fill='#102238')
panel.save(OUT/'evidence-overview.png')
