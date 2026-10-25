"""Prepare private E5 visuals; all audio still comes from the live TTS worker."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=root/'outputs/e5';source=root/'outputs/realtime'
    if out.exists() and not a.refresh:raise FileExistsError('Use --refresh only for the current E5 preview assets')
    out.mkdir(parents=True,exist_ok=True)
    names=['assets.json','clock.mjs','portrait-gl.mjs']+[f'{role}-{part}.png' for role in ['female','male'] for part in ['base','mouth','eyes']]
    for n in names:shutil.copyfile(source/n,out/n)
    shutil.copytree(source/'vendor',out/'vendor',dirs_exist_ok=True)
    for f in (root/'web/e5').glob('*'):
        if f.is_file():shutil.copyfile(f,out/f.name)
    shutil.copyfile(root/'experiments/2026-10-24-e5-live-tts/manifest.json',out/'manifest.json')
    plugin=root.parent/'voice_ai/dsh-voice-ai-girlfriend-plugin'
    subprocess.run([str(plugin/'node_modules/.bin/esbuild'),str(plugin/'src/client/voice/speaker.ts'),'--format=esm','--target=es2022','--outfile='+str(out/'speaker.mjs')],cwd=root,check=True)
    hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()}
    (out/'prepared.json').write_text(json.dumps({'files':hashes,'audio_files_copied':0,'scope':'Private visual/model dependencies only; TTS is generated on each request'},indent=2)+'\n')
    print('Prepared E5 preview; no recorded audio copied')


if __name__=='__main__':main()
