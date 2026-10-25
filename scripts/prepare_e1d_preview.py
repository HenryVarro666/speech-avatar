"""Counterbalanced E1c/E1d full-frame replay; no inferred user ratings."""
import json
from pathlib import Path
import random

import prepare_e1c_preview as common

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT/'experiments/2026-10-23-e1d-reference-framing'
OLD = ROOT/'experiments/2026-10-21-e1c-controlled-expression'
OUT = ROOT/'outputs/e1d'


def main():
    manifest = json.loads((EXP/'manifest.json').read_text())
    checked = json.loads((EXP/'video_quality.json').read_text())
    assert checked['full_decode_passed']==2 and checked['audio_integrity_passed']==2
    old = json.loads((OLD/'manifest.json').read_text())
    old_checks = json.loads((OLD/'qmotion_quality.json').read_text())['checks']
    common.OUT = OUT
    groups=[]
    order=[False,True]
    random.Random(20261023).shuffle(order)
    for i,t in enumerate(manifest['trials']):
        parent=next(p for p in old['trials'] if p['trial_id']==t['parent_trial_id'])
        parent_check=next(c for c in old_checks if c['trial_id']==parent['trial_id'])
        new_check=next(c for c in checked['checks'] if c['trial_id']==t['trial_id'])
        role='female' if t['avatar_id']=='avatar-a' else 'male'
        clips=[]
        for index,is_new in enumerate(order if i==0 else order[::-1]):
            trial,check=(t,new_check) if is_new else (parent,parent_check)
            ident=role+'-'+chr(97+index)
            clips.append({'id':ident,'label':chr(65+index),'trial_id':trial['trial_id'],
                'filename':common.media(ROOT/trial['planned_output_path'],ident,check['output_sha256']),
                'sha256':check['output_sha256'],'reveal':'生成前紧构图参考' if is_new else '原构图参考（E1c）'})
        groups.append({'role':role,'label':'女角色' if role=='female' else '男角色','clips':clips})
    data={'seed':20261023,'groups':groups,'manifest_sha256':common.sha(EXP/'manifest.json'),
          'blinding':'interface labels only; visible framing differences; opposite order across roles',
          'human_review':'pending'}
    (EXP/'preview_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    user=EXP/'user_review.json'
    if not user.exists():
        user.write_text(json.dumps({'reviewer':None,'framing_preference':None,'motion_acceptance':None,
            'human_av_acceptance':None,'source_video_hashes':[c['sha256'] for g in groups for c in g['clips']]},indent=2)+'\n')
    (OUT/'review-feedback.js').write_bytes((ROOT/'scripts/e1d_feedback.js').read_bytes())
    html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>E1d · 参考构图对照</title><style>
:root{color-scheme:dark;font-family:system-ui,-apple-system,"PingFang SC",sans-serif;background:#101722;color:#edf3fc}*{box-sizing:border-box}main{max-width:1160px;margin:auto;padding:22px}h1{font-size:28px;margin:12px 0}h2{margin:24px 0 12px}p{line-height:1.65;color:#c4d2e5}.pair{display:grid;gap:16px;grid-template-columns:1fr 1fr}article{background:#1a2537;border:1px solid #34445c;padding:12px;border-radius:12px}h3{margin:4px 0 12px}video{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:#090e16}button{min-height:44px;padding:10px 15px;border:0;border-radius:8px;background:#a8ead6;color:#10251f;font-size:15px;font-weight:600;cursor:pointer;margin:8px 8px 8px 0}button:focus-visible,video:focus-visible{outline:3px solid #f2cb82;outline-offset:3px}.status,small{font-size:13px;color:#bdcce0}.script{background:#1b293d;padding:12px;border-radius:10px}@media(max-width:760px){.pair{grid-template-columns:1fr}}
fieldset{border:1px solid #34445c;border-radius:10px;padding:16px;margin:18px 0}label{display:block;margin:12px 0 6px}select,input,textarea{font:inherit;color:inherit;background:#101722;border:1px solid #72839b;border-radius:6px;min-height:44px;padding:9px;width:100%}textarea{min-height:88px;resize:vertical}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;padding:12px;background:#1a2537}.feedback-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:760px){.feedback-grid{grid-template-columns:1fr}}
</style><main><small>SPEECH AVATAR · E1d · 2026-10-23</small><h1>参考构图能否让动作更合适？</h1>
<p>同一角色、配音、提示与模型，只改变生成前参考图的构图。视频完整展示，没有在成片后裁去手部。</p>
<p class="script">您好，已经帮您安排好了。明天下午三点半见，路上注意安全。</p>
<button id="stop">停止全部播放</button><div id="pairs"></div><button id="reveal">揭示处理方式</button><p id="reveal-state">当前未揭示。构图差异本身可见，处理名称暂隐藏。</p>
<p>比较手是否入画、表情是否用力、牙齿、口型与3.72秒续接；同时看头顶、下巴和肩部是否过于拥挤。每次只有一段发声；技术检查不替代你的观看判断。</p>
<h2>记录观看反馈</h2><p>更喜欢一段，不等于它的音画已经可接受。选项默认未判断，可只填写看过的角色。反馈仅保留在当前页面，刷新前请先导出；导出文件交回后可归档，不会自动更新实验评分。</p>
<label for="reviewer">审阅者（可选）</label><input id="reviewer" type="text" autocomplete="off">
<div id="feedback-fields" class="feedback-grid"></div><button id="export-feedback">导出我的反馈</button><p id="feedback-state" role="status">尚未导出反馈。</p><details id="feedback-details" hidden><summary>查看导出内容</summary><pre id="feedback-json"></pre></details></main>
<script src="review-feedback.js"></script><script>const data=__DATA__;let revealed=false;const players=[];function stop(){for(const v of players)v.pause()}
function render(){stop();players.length=0;const root=document.querySelector('#pairs');root.replaceChildren();for(const g of data.groups){const h=document.createElement('h2');h.textContent=g.label;root.append(h);const pair=document.createElement('section');pair.className='pair';for(const c of g.clips){const a=document.createElement('article'),name=document.createElement('h3');name.textContent='样片 '+c.label+(revealed?' · '+c.reveal:'');const v=document.createElement('video');v.id=c.id;v.src=c.filename;v.poster=c.filename.replace('.mp4','.png');v.controls=true;v.preload='metadata';v.playsInline=true;v.setAttribute('aria-label',g.label+' '+c.label+'视频');const b=document.createElement('button');b.textContent='播放 '+g.label+' '+c.label;const s=document.createElement('div');s.id=c.id+'-state';s.className='status';s.textContent='待播放';b.onclick=async()=>{stop();v.currentTime=0;try{await v.play()}catch(e){s.textContent='无法播放：'+e.message}};v.onplay=()=>{for(const o of players)if(o!==v)o.pause();s.textContent='正在播放'};v.onended=()=>s.textContent='播放完毕';v.onpause=()=>{if(!v.ended)s.textContent='已暂停'};v.onerror=()=>s.textContent='媒体加载失败';players.push(v);a.append(name,v,b,s);pair.append(a)}root.append(pair)}}document.querySelector('#stop').onclick=stop;document.querySelector('#reveal').onclick=()=>{revealed=true;render();document.querySelector('#reveal-state').textContent='处理方式已揭示；尚未记录任何主观通过';document.querySelector('#reveal').disabled=true};render();</script></html>'''
    feedback_ui='''<script>
const feedbackRoot=document.querySelector('#feedback-fields');
for(const group of data.groups){
 const field=document.createElement('fieldset'),legend=document.createElement('legend');legend.textContent=group.label;field.append(legend);
 const choices=[['preference','构图偏好',[['unreviewed','尚未判断'],['A','更喜欢 A'],['B','更喜欢 B'],['no_difference','无明显差别'],['neither','两段都不喜欢']]],['acceptance','音画接受',[['unreviewed','尚未判断'],['A','仅 A 可接受'],['B','仅 B 可接受'],['both','两段都可接受'],['neither','两段都不可接受']]]];
 for(const [key,title,options] of choices){const label=document.createElement('label'),select=document.createElement('select');select.id='feedback-'+group.role+'-'+key;label.htmlFor=select.id;label.textContent=group.label+' '+title;for(const [value,text] of options){const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option)}field.append(label,select)}
 const label=document.createElement('label'),notes=document.createElement('textarea');notes.id='feedback-'+group.role+'-notes';label.htmlFor=notes.id;label.textContent=group.label+' 问题与时间点';notes.placeholder='例如：2.64 秒手入画；牙齿或口型问题。';field.append(label,notes);feedbackRoot.append(field);
}
for(const input of document.querySelectorAll('#feedback-fields select,#feedback-fields textarea,#reviewer'))input.addEventListener('input',()=>{document.querySelector('#feedback-state').textContent='有未导出的修改，刷新前请先导出。';document.querySelector('#feedback-details').hidden=true});
document.querySelector('#export-feedback').onclick=()=>{
 try{const answers={reviewer:document.querySelector('#reviewer').value};for(const group of data.groups){const prefix='#feedback-'+group.role+'-';answers[group.role]={preference:document.querySelector(prefix+'preference').value,acceptance:document.querySelector(prefix+'acceptance').value,notes:document.querySelector(prefix+'notes').value}}
 const draft=buildFeedback(data,answers,{revealed}),text=JSON.stringify(draft,null,2)+'\\n';document.querySelector('#feedback-json').textContent=text;document.querySelector('#feedback-details').hidden=false;
 const url=URL.createObjectURL(new Blob([text],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='e1d-feedback-draft.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);document.querySelector('#feedback-state').textContent='反馈草稿已导出；请交回文件归档。实验评分尚未自动更新。';
 }catch(error){document.querySelector('#feedback-state').textContent='导出失败：'+error.message}
};</script>'''
    html=html.replace('</html>',feedback_ui+'</html>')
    (OUT/'index.html').write_text(html.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('<','\\u003c')))
    print('Prepared two counterbalanced pairs; human review remains pending.')


if __name__=='__main__':
    main()
