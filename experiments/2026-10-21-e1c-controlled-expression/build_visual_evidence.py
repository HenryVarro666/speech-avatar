from pathlib import Path
import json,math,sys
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageOps
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'scripts'))
import audit_e1_quality as sync
from review_e1b_quality import sheet
exp=Path(__file__).parent;parent=root/'experiments/2026-10-20-e1b-full-expression';out=root/'outputs/e1c/qmotion/quality'
m=json.loads((exp/'manifest.json').read_text());tracks=json.loads((exp/'qmotion_face_tracks.json').read_text());oldtracks=json.loads((parent/'video_face_tracks.json').read_text());oldm=json.loads((parent/'manifest.json').read_text())
allframes={}
for t in m['trials']:
 ident=t['trial_id'];frames=sync.read_video(root/t['planned_output_path']);allframes[ident]=frames
 ids=sorted(set(range(0,len(frames),5))|{len(frames)-1});sheet(frames,ids,out/(ident+'-full200ms.png'))
 sheet(frames,list(range(len(frames))),out/(ident+'-all-bottom.png'),size=(160,94),crop=(0,int(len(frames[0])*.66),frames.shape[2],len(frames[0])),cols=8)
 sheet(frames,list(range(85,102)),out/(ident+'-join.png'))
 sheet(frames,list(range(len(frames)-13,len(frames))),out/(ident+'-ending.png'))
 for i in ([25,66] if t['avatar_id']=='avatar-a' else [35,115]):
  Image.fromarray(cv2.cvtColor(frames[i],cv2.COLOR_BGR2RGB)).save(out/(ident+f'-f{i:03d}-native.png'))
 cells=[]
 for i in [20,30,40,60,70,90,93,110,120]:
  a,b,c,d=tracks[ident]['smoothed_boxes'][i];w,h=c-a,d-b;crop=frames[i,int(b+.52*h):min(frames.shape[1],int(d+.1*h)),int(a+.15*w):int(c-.15*w)]
  cells.append(crop)
 # Each native original frame remains available; these are diagnostic crops only.
panel=Image.new('RGB',(1024,820),'#edf1f6');draw=ImageDraw.Draw(panel)
for col,(t,is_new) in enumerate([(m['trials'][0],False),(m['trials'][0],True),(m['trials'][1],False),(m['trials'][1],True)]):
 x=col*256;female=t['avatar_id']=='avatar-a';ident=t['trial_id'] if is_new else t['parent_trial_id'];source=t if is_new else next(r for r in oldm['trials'] if r['trial_id']==ident);frames=allframes[t['trial_id']] if is_new else sync.read_video(root/source['planned_output_path']);tr=tracks[ident] if is_new else oldtracks[ident]
 draw.text((x+8,8),('Female / ' if female else 'Male / ')+('Controlled' if is_new else 'Original'),fill='#102238')
 for y,i,region,label in [(30,35,'full','Full /1.40s'),(318,30,'mouth','Mouth /1.20s'),(552,66 if female else 115,'bottom','Lower /'+('2.64s' if female else '4.60s'))]:
  fr=frames[i]
  if region=='mouth':
   a,b,c,d=tr['smoothed_boxes'][i];w,h=c-a,d-b;fr=fr[int(b+.52*h):min(len(fr),int(d+.1*h)),int(a+.15*w):int(c-.15*w)]
  if region=='bottom':fr=fr[int(len(fr)*.66):]
  pic=Image.fromarray(cv2.cvtColor(fr,cv2.COLOR_BGR2RGB));panel.paste(ImageOps.pad(pic,(248,256 if region=='full' else 192),color='#152133'),(x+4,y+24));draw.text((x+8,y+5),label,fill='#102238')
draw.text((8,798),'Same audio/image/seed/model per role; positive prompt changed only. Display crops; original videos remain unchanged.',fill='#102238');panel.save(out/'prompt-comparison.png')
print('visual evidence built')
