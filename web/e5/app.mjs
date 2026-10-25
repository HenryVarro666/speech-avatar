import {ReplySpeaker} from './speaker.mjs';
import {pcmStream} from './transport.mjs';
import {AvatarView} from './avatar.mjs';
const $=id=>document.getElementById(id),speaker=new ReplySpeaker(),runs=[],events=[];
let spec,assets,view,active,prior,lastRequest;
const status=text=>$('status').textContent=text;
function log(kind,data={}){events.push({t:performance.now(),kind,...data});$('events').textContent=events.slice(-12).map(x=>JSON.stringify(x)).join('\n')}
function table(){const body=$('results');body.replaceChildren();for(const r of runs){const tr=document.createElement('tr');for(const x of [r.text+' / '+r.role,r.firstPcmMs==null?'—':r.firstPcmMs.toFixed(0)+'ms',r.requestToScheduleMs==null?'—':(r.requestToScheduleMs+r.scheduleLeadMs).toFixed(0)+'ms',r.scheduledSamples,r.status]){const td=document.createElement('td');td.textContent=x;tr.append(td)}body.append(tr)}}
async function serverJob(r){try{const p=await fetch('/api/job/'+r.id);r.server=await p.json();log('worker_state',{id:r.id,status:r.server.status});table()}catch(e){log('worker_state_unavailable',{id:r.id})}}
function stop(reason='user'){
  const r=active;if(r&&!['complete','incomplete','failed','cancelled'].includes(r.status)){
    r.cancelled=true;r.status='cancelled';r.stopAt=performance.now();r.playbackActive=false;r.abort.abort();prior=r;
    void fetch('/api/cancel',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:r.id})}).then(p=>p.json()).then(s=>{r.cancelAck=s;log('cancel_ack',{id:r.id,status:s.status});setTimeout(()=>void serverJob(r),1200)}).catch(()=>log('cancel_rpc_failed',{id:r.id}));
  }
  speaker.stop();if(r)r.audioStoppedAfterCall=!speaker.speaking;log('stop',{id:r?.id,reason,speaking:speaker.speaking});table();
}
function updateIfCurrent(r,text){if(active!==r||r.cancelled){log('stale_ui_discarded',{id:r.id});return false}status(text);return true}
async function play(request={text:$('text').value.trim(),role:$('role').value},profile='normal'){
  if(!request.text)return;stop('replacement');
  const r={...request,id:'e5-'+crypto.randomUUID(),profile,status:'requesting',requestAt:performance.now(),abort:new AbortController(),pendingSources:[],firstAudioContext:null,firstVisualContext:null,scheduledSamples:0,schedules:[],classifierCallbacks:0,animatedFrames:0,analysisReady:false,chunks:0,pcmSamples:0,playbackActive:false,humanAvAccepted:null};
  active=r;lastRequest=request;runs.push(r);view.begin(r);updateIfCurrent(r,'正在实际生成：'+r.text);log('request',{id:r.id,role:r.role,profile});table();
  try{
    const response=await fetch('/api/tts/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:r.id,text:request.text,role:request.role,profile}),signal:r.abort.signal});
    if(!response.ok)throw Error('TTS请求失败：HTTP'+response.status);if(active!==r||r.cancelled){await response.body.cancel();return}
    const pipe=pcmStream(response.body,r.id,f=>{
      if(active!==r||r.cancelled)return;
      if(f.type==='audio'){r.firstPcmMs??=performance.now()-r.requestAt;r.chunks++;r.pcmSamples+=f.samples;r.status='streaming';r.playbackActive=true;log('pcm',{id:r.id,seq:f.seq,samples:f.samples});updateIfCurrent(r,'正在播放真实语音流；已收到 '+r.chunks+' 块。');table()}
      if(f.type==='end'){r.endFrame=f;r.endReceivedMs=performance.now()-r.requestAt}
    });
    await speaker.speakStream(pipe.stream,24000);const result=await pipe.completion;r.transport=result;
    if(active!==r||r.cancelled)return;
    r.status='draining';const until=performance.now()+r.pcmSamples/24000*1000+5000;
    while(active===r&&!r.cancelled&&speaker.speaking&&performance.now()<until)await new Promise(f=>setTimeout(f,15));
    if(active!==r||r.cancelled)return;
    r.playbackActive=false;r.status=speaker.speaking?'timeout':result.status==='complete'?'complete':'incomplete';r.finishedMs=performance.now()-r.requestAt;
    updateIfCurrent(r,r.status==='complete'?'完整播放结束。可更换一句话。':'音频不完整：已播放收到的部分。请显式重试本句或换新句。');
    await new Promise(f=>setTimeout(f,35));if(active===r){r.finalControllerRest=view.pose===0;await serverJob(r)}
  }catch(e){
    if(r.cancelled||active!==r)return;r.playbackActive=false;r.status='failed';r.error=String(e);updateIfCurrent(r,String(e));log('request_failed',{id:r.id,error:String(e)});
  }table();
}
$('speak').onclick=()=>void play();$('stop').onclick=()=>{stop();status('已打断：旧音源停止，旧生成已请求取消。')};
$('interrupt').onclick=()=>{log('controlled_barge_in');$('text').value=spec.utterances[2].text;$('role').value=spec.utterances[2].role;void play(spec.utterances[2])};
$('drop').onclick=()=>void play(undefined,'drop');$('retry').onclick=()=>lastRequest&&void play(lastRequest);
$('stale').onclick=()=>{const old=prior||runs.at(-2);if(old)updateIfCurrent(old,'上一轮迟到错误：这行不应成为当前状态')};
$('utterance').onchange=()=>{const u=spec.utterances[$('utterance').selectedIndex];$('text').value=u.text;$('role').value=u.role};
$('export').onclick=()=>{const result={schema:1,scope:'Actual TTS streaming local prototype; controlled client interruption, no human microphone/ASR/translation/physical audio pass',gpuRenderer:view.renderer.renderer,results:runs.map(({abort,context,pendingSources,...r})=>r),events,humanAvAccepted:null};const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));a.download='e5-live-report.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
spec=await (await fetch('/config')).json();assets=await (await fetch('./assets.json')).json();
view=new AvatarView(speaker,assets,f=>{$('pose').textContent=f.pose?'说话口型':'待机';$('audio').textContent=f.active?'有声片段播放中':f.waiting?'等下一块／欠载':'未播放';$('chunks').textContent=active?.chunks||0;$('epoch').textContent=view.timeline.epoch;$('renderer').textContent='WebGL2：'+f.renderer},log);
for(const u of spec.utterances){const o=document.createElement('option');o.textContent=u.id+' · '+u.text;o.value=u.id;$('utterance').append(o)}$('utterance').onchange();
view.begin({role:'female',pendingSources:[],cancelled:false});
try{const h=await(await fetch('/health')).json();if(!h.ready)throw Error('worker未就绪');$('backend').textContent='独立CPU worker已连接；Serena／Uncle_Fu，24kHz，串行生成。';$('speak').disabled=false;status('真实 TTS 已就绪。每次点击都会重新合成。')}catch(e){status('TTS worker不可用，请检查本机代理/SSH转发。')}
