"""Build the E1c blinded replay page from checked existing artifacts."""
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT/'experiments/2026-10-21-e1c-controlled-expression'
OLD = ROOT/'experiments/2026-10-20-e1b-full-expression'
OUT = ROOT/'outputs/e1c'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def media(source, ident, expected):
    target = OUT/'review-media'/(ident+'.mp4')
    target.parent.mkdir(parents=True, exist_ok=True)
    assert sha(source)==expected
    if target.exists() and sha(target)!=expected:
        raise FileExistsError(target)
    if not target.exists():
        shutil.copyfile(source, target)
    poster = target.with_suffix('.png')
    if not poster.exists():
        subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', str(source),
                        '-frames:v', '1', str(poster)], capture_output=True, check=True)
    return 'review-media/'+target.name


def main():
    sync_rows = json.loads((EXP/'sync_variants.json').read_text())['variants']
    sync_checks = json.loads((EXP/'qsync_quality.json').read_text())
    motion_checks = json.loads((EXP/'qmotion_quality.json').read_text())
    assert sync_checks['audio_integrity_passed']==6 and motion_checks['audio_integrity_passed']==2
    manifest = json.loads((EXP/'manifest.json').read_text())
    old_trials = json.loads((OLD/'manifest.json').read_text())['trials']
    old_checks = json.loads((OLD/'video_validation.json').read_text())['checks']
    rng = random.Random(20261021)
    order = list(range(3))
    rng.shuffle(order)
    groups = []
    for number, role in enumerate(['female','male']):
        values = sorted([r for r in sync_rows if r['role']==role], key=lambda r:r['video_delay_ms'])
        initial = order if number==0 else order[::-1]
        rounds = []
        for round_id in range(3):
            clips = []
            for position in range(3):
                row = values[initial[(position+round_id)%3]]
                ident = f'sync-{role}-r{round_id+1}-{chr(97+position)}'
                clips.append({'id':ident, 'label':chr(65+position),
                    'filename':media(ROOT/row['output_path'], 'sync-'+role+'-'+row['output_sha256'][:12], row['output_sha256']),
                    'sha256':row['output_sha256'], 'reveal':f"画面延后{row['video_delay_ms']}ms",
                    'variant_id':row['id']})
            rounds.append(clips)
        trial = next(t for t in manifest['trials'] if ('female' if t['avatar_id']=='avatar-a' else 'male')==role)
        baseline = next(t for t in old_trials if t['trial_id']==trial['parent_trial_id'])
        old_check = next(c for c in old_checks if c['trial_id']==baseline['trial_id'])
        new_check = next(c for c in motion_checks['checks'] if c['trial_id']==trial['trial_id'])
        candidates = [(ROOT/baseline['planned_output_path'],old_check['output_sha256'],'原提示',baseline['trial_id']),
                      (ROOT/trial['planned_output_path'],new_check['output_sha256'],'受控正面提示',trial['trial_id'])]
        if number==0:
            if rng.randrange(2):
                candidates.reverse()
            female_order = [c[2] for c in candidates]
        else:
            candidates.sort(key=lambda c:female_order[::-1].index(c[2]))
        motion = []
        for position,(source,digest,label,trial_id) in enumerate(candidates):
            ident = f'motion-{role}-{chr(97+position)}'
            motion.append({'id':ident,'label':chr(65+position),'filename':media(source,ident,digest),
                           'sha256':digest,'reveal':label,'trial_id':trial_id})
        groups.append({'role':role,'label':'女角色' if role=='female' else '男角色',
                       'sync_rounds':rounds,'motion':motion})
    data = {'seed':20261021,'groups':groups,'manifest_sha256':sha(EXP/'manifest.json'),
            'blinding':'interface only;3Latin rotations put each sync candidate in each position once',
            'human_review':'pending'}
    (EXP/'preview_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    review = EXP/'user_review.json'
    if not review.exists():
        review.write_text(json.dumps({'reviewer':None,'sync_preference':None,
            'motion_acceptance':None,'source_video_hashes':[c['sha256'] for g in groups for c in g['motion']]},indent=2)+'\n')
    html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>E1c · 同步与受控表情实验</title><style>
:root{color-scheme:dark;font-family:system-ui,-apple-system,"PingFang SC",sans-serif;background:#101722;color:#edf3fc}*{box-sizing:border-box}main{max-width:1160px;margin:auto;padding:28px 22px}h1{font-size:29px}h2{margin-top:36px}p{line-height:1.7;color:#c4d2e5}.pair,.trio{display:grid;gap:16px}.pair{grid-template-columns:1fr 1fr}.trio{grid-template-columns:repeat(3,1fr)}article{background:#1a2537;border:1px solid #34445c;padding:15px;border-radius:12px}video{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:#090e16}button{min-height:44px;padding:10px 15px;border:0;border-radius:8px;background:#a8ead6;color:#10251f;font-size:15px;font-weight:600;cursor:pointer;margin:8px 8px 8px 0}button:focus-visible,video:focus-visible{outline:3px solid #f2cb82;outline-offset:3px}.status{font-size:13px;color:#bdcce0}.script{background:#1b293d;padding:18px;border-radius:10px}a{color:#a8ead6}small{color:#bed0e5}@media(max-width:760px){.pair,.trio{grid-template-columns:1fr}}
</style><main><small>SPEECH AVATAR · E1c · 2026-10-21</small><h1>同步校准与受控表情</h1>
<p>先比较两段新视频是否更适合平静对话，再试同步校准。样片编号可在聊天中反馈；揭示处理方式前先观察。</p>
<p class="script">您好，已经帮您安排好了。明天下午三点半见，路上注意安全。</p>
<button id="stop">停止全部播放</button><h2>① 原提示与受控提示</h2><p>同一人物、配音、种子与模型配置，仅正面提示变化。看牙齿、眉眼、嘴幅、下沿手部和3.72秒续接。</p><div id="motion"></div>
<h2>② 同步校准：三个候选</h2><p>原片派生副本只改变画面起始位置，保留全部源帧和语音；不是新的模型生成。每轮是相同三个候选换位置，三轮后每个候选各占一次A/B/C。可反馈“女角色第1轮B”等，无明确差别可说无法判断。</p><button id="rotate">换一轮位置</button><span id="round"></span><div id="sync"></div>
<button id="reveal">揭示处理方式</button><p id="reveal-state">当前未揭示。属于界面单盲，文件/源码仍可检查；技术诊断不会代填你的偏好。</p>
<p>每次只有一段发声。本页只回放已有文件；动态更大不等于更自然，SyncNet接近零也不自动代表同步可接受。</p></main>
<script>const data=__DATA__;let round=0,revealed=false;const players=[];
function stop(){for(const v of players)v.pause()}
function card(clip,role,section){const a=document.createElement('article'),h=document.createElement('h3');h.textContent='样片 '+clip.label+(revealed?' · '+clip.reveal:'');const v=document.createElement('video');v.src=clip.filename;v.poster=clip.filename.replace('.mp4','.png');v.controls=true;v.preload='metadata';v.playsInline=true;v.id=clip.id;v.setAttribute('aria-label',role+' '+section+' '+clip.label+'视频');players.push(v);const b=document.createElement('button');b.textContent='播放 '+role+' '+section+' '+clip.label;const s=document.createElement('div');s.className='status';s.id=clip.id+'-state';s.textContent='待播放';b.onclick=async()=>{stop();v.currentTime=0;try{await v.play()}catch(e){s.textContent='无法播放：'+e.message}};v.onplay=()=>{for(const o of players)if(o!==v)o.pause();s.textContent='正在播放'};v.onended=()=>s.textContent='播放完毕';v.onpause=()=>{if(!v.ended)s.textContent='已暂停'};v.onerror=()=>s.textContent='媒体加载失败';a.append(h,v,b,s);return a}
function render(){stop();players.length=0;for(const section of ['motion','sync']){const container=document.querySelector('#'+section);container.replaceChildren();for(const g of data.groups){const h=document.createElement('h3');h.textContent=g.label;container.append(h);const grid=document.createElement('section');grid.className=section==='motion'?'pair':'trio';for(const c of section==='motion'?g.motion:g.sync_rounds[round])grid.append(card(c,g.label,section==='motion'?'表情':'同步'));container.append(grid)}}document.querySelector('#round').textContent='当前第'+(round+1)+'轮 / 共3轮'}
document.querySelector('#stop').onclick=stop;document.querySelector('#rotate').onclick=()=>{round=(round+1)%3;render()};document.querySelector('#reveal').onclick=()=>{revealed=true;render();document.querySelector('#reveal-state').textContent='处理方式已揭示；没有自动选择偏移或记录主观通过';document.querySelector('#reveal').disabled=true};render();</script></html>'''
    (OUT/'index.html').write_text(html.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('<','\\u003c')))
    print(json.dumps({'preview':str(OUT/'index.html'),'motion_clips':4,'unique_sync_variants':6,'balanced_rotations':3}))


if __name__=='__main__':
    main()
