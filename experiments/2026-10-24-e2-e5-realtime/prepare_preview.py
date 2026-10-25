"""Derive private mouth/eye texture atlases from frozen accepted-avatar material."""
import argparse,hashlib,json,shutil,subprocess,wave,urllib.request
from pathlib import Path
import cv2,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];EXP=Path(__file__).resolve().parent;OUT=ROOT/'outputs/realtime'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fetch-official',action='store_true',help='Fetch hash-pinned MIT HeadAudio source/model from official GitHub into private cache');args=parser.parse_args()
    OUT.mkdir(exist_ok=True);m=json.loads((EXP/'manifest.json').read_text());assets={}
    cache=ROOT/'.cache/headaudio-source'
    if args.fetch_official:
        dep=m['head_audio'];cache.mkdir(parents=True,exist_ok=True)
        for row in dep['files']:
            target=cache/row['path']
            if target.is_file() and sha(target)==row['sha256']:continue
            url=f"https://raw.githubusercontent.com/met4citizen/HeadAudio/{dep['revision']}/{row['path']}"
            with urllib.request.urlopen(url,timeout=30) as response:data=response.read()
            assert hashlib.sha256(data).hexdigest()==row['sha256'],f"Dependency hash mismatch: {row['path']}"
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        (cache/'provenance.json').write_text(json.dumps(dep,indent=2)+'\n')
    for role,avatar,ids in [('female','avatar-a',[0,40,100,30,24]),('male','avatar-b',[0,40,80,31,53])]:
        video=ROOT/f'outputs/e1f-regional/{role}-regional.mp4';q=json.loads((ROOT/f'experiments/2026-10-23-e1f-regional-motion/quality-{role}.json').read_text());cap=cv2.VideoCapture(str(video))
        def read(i):cap.set(cv2.CAP_PROP_POS_FRAMES,i);ok,f=cap.read();assert ok;return Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB))
        neutral=ROOT/f'data/private/avatars/{avatar}/source.png';base=Image.open(neutral).convert('RGB');base.save(OUT/f'{role}-base.png');box=q['face_boxes'][0]
        def rect(box,kind):
            x1,y1,x2,y2=box;w,h=x2-x1,y2-y1
            return ([x1+.1*w,y1+.58*h,x2-.1*w,y1+1.02*h] if kind=='mouth' else [x1-.02*w,y1+.18*h,x2+.02*w,y1+.55*h])
        mouth=Image.new('RGB',(256*5,160));eye=Image.new('RGB',(384*2,120))
        for col,i in enumerate(ids):mouth.paste(read(i).crop(tuple(map(round,rect(q['face_boxes'][i],'mouth')))).resize((256,160)),(col*256,0))
        for col,i in enumerate([0,18]):eye.paste(read(i).crop(tuple(map(round,rect(q['face_boxes'][i],'eye')))).resize((384,120)),(col*384,0))
        mouth.save(OUT/f'{role}-mouth.png');eye.save(OUT/f'{role}-eyes.png');cap.release()
        def uv(r):x1,y1,x2,y2=r;return [x1/base.width,y1/base.height,(x2-x1)/base.width,(y2-y1)/base.height]
        assets[role]={'base':f'{role}-base.png','mouth':f'{role}-mouth.png','eyes':f'{role}-eyes.png','mouthRect':uv(rect(box,'mouth')),'eyeRect':uv(rect(box,'eye')),'neutral_source':str(neutral.relative_to(ROOT)),'neutral_source_sha256':sha(neutral),'source_video_sha256':sha(video),'mouth_frame_ids':ids,'eye_frame_ids':[0,18],'scope':'Approximate pose atlas, not ground-truth phoneme labels or new neural frame generation'}
    clips=[]
    for row in m['fixtures']:
        src=ROOT/row['path'];assert sha(src)==row['sha256'];target=OUT/(row['id']+'.wav');shutil.copyfile(src,target)
        with wave.open(str(src)) as w:
            assert w.getnchannels()==1 and w.getsampwidth()==2;rate=w.getframerate();samples=w.getnframes()
        clips.append({**row,'url':target.name,'sampleRate':rate,'samples':samples,'duration':samples/rate})
    provenance=json.loads((ROOT/'.cache/headaudio-source/provenance.json').read_text());vendor=OUT/'vendor/headaudio';vendor.mkdir(parents=True,exist_ok=True)
    for row in provenance['files']:
        src=ROOT/'.cache/headaudio-source'/row['path'];assert sha(src)==row['sha256'];target=vendor/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
    for file in (ROOT/'web/realtime').glob('*'):
        if file.is_file():shutil.copyfile(file,OUT/file.name)
    (OUT/'assets.json').write_text(json.dumps({'portraits':assets,'clips':clips,'headaudio_revision':provenance['revision']},ensure_ascii=False,indent=2)+'\n')
    (EXP/'asset-provenance.json').write_text(json.dumps({'portraits':assets,'clips':clips,'derived_assets':{p.name:sha(p) for p in OUT.glob('*.png')},'private_media_only':True},ensure_ascii=False,indent=2)+'\n')
    plugin=ROOT.parent/'voice_ai/dsh-voice-ai-girlfriend-plugin'
    subprocess.run([str(plugin/'node_modules/.bin/esbuild'),str(plugin/'src/client/voice/speaker.ts'),'--format=esm','--target=es2022','--outfile='+str(OUT/'speaker.mjs')],check=True)
    print('Prepared4audio fixtures/two pose atlases and actual DSH speaker; no neural generation')
if __name__=='__main__':main()
