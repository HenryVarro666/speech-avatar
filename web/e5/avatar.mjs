import {PlaybackTimeline,pcmRms,poseFromWeights} from './clock.mjs';
import {PortraitGL} from './portrait-gl.mjs';
import {HeadAudio} from './vendor/headaudio/modules/headaudio.mjs';

export class AvatarView {
  constructor(speaker,assets,onFrame,log){
    this.speaker=speaker;this.assets=assets;this.onFrame=onFrame;this.log=log;this.timeline=new PlaybackTimeline();this.modules=new WeakMap();this.weights={};this.rafTimes=[];this.last=performance.now();
    this.renderer=new PortraitGL(document.getElementById('avatar'),(ok,reason)=>{document.getElementById('fallback').hidden=ok;this.log('renderer',{ok,reason})});
    speaker.observePlayback(e=>this.scheduled(e));requestAnimationFrame(t=>this.frame(t));
  }
  clear(){if(this.head){this.head.onvalue=this.head.onviseme=null;this.head.stop();this.head.disconnect();this.head=null}if(this.analyser)this.analyser.disconnect();this.analyser=null;this.weights={}}
  begin(run){
    this.run=run;this.clear();const a=this.assets.portraits[run.role];document.getElementById('fallback').src=a.base;
    if(this.renderer.asset!==a){this.renderer.ok=false;document.getElementById('fallback').hidden=false}
    void this.renderer.init(a).catch(e=>{if(this.run===run){document.getElementById('fallback').hidden=false;this.log('visual_error',{message:String(e)})}});
  }
  async setup(ctx,run){
    try{
      let p=this.modules.get(ctx);if(!p){p=ctx.audioWorklet.addModule('./vendor/headaudio/modules/headworklet.mjs');this.modules.set(ctx,p)}await p;
      if(this.run!==run||run.cancelled)return;
      const h=new HeadAudio(ctx,{processorOptions:{visemeEventsEnabled:true}});this.head=h;
      h.onvalue=(k,v)=>{if(this.run===run&&!run.cancelled)this.weights[k]=v};h.onviseme=()=>{if(this.run===run&&!run.cancelled)run.classifierCallbacks++};
      await h.loadModel('./vendor/headaudio/dist/model-en-mixed.bin');
      if(this.run!==run||run.cancelled){h.stop();h.disconnect();return}run.analysisReady=true;
      for(const s of run.pendingSources)try{s.connect(h)}catch{}run.pendingSources=[];
    }catch(e){if(this.run===run){run.visualFallback='rms';this.log('analysis_error',{message:String(e)})}}
  }
  scheduled(e){
    this.timeline.accept(e);if(e.type==='reset'){this.clear();return}
    const r=this.run;if(!r||r.cancelled)return;
    r.context=e.context;r.epoch=e.epoch;r.scheduledSamples+=e.pcm.length;
    if(r.firstAudioContext===null){r.firstAudioContext=e.contextStartTime;r.requestToScheduleMs=performance.now()-r.requestAt;r.scheduleLeadMs=(e.contextStartTime-e.context.currentTime)*1000;this.analyser=e.context.createAnalyser();this.analyser.fftSize=512;void this.setup(e.context,r)}
    e.source.connect(this.analyser);if(r.analysisReady&&this.head)e.source.connect(this.head);else r.pendingSources.push(e.source);
    r.schedules.push({index:e.chunkIndex,offset:e.sampleOffset,rate:e.sampleRate,start:e.contextStartTime,samples:e.pcm.length,epoch:e.epoch,utterance:e.utteranceId});
  }
  frame(now){
    const dt=Math.min(100,now-this.last);this.last=now;this.rafTimes.push(dt);if(this.rafTimes.length>300)this.rafTimes.shift();
    const r=this.run,segment=r?.context?this.timeline.at(r.context.currentTime):null;let pose=0,amount=0;
    if(r?.playbackActive&&!r.cancelled&&segment){
      if(r.analysisReady){this.head?.update(dt);({pose,amount}=poseFromWeights(this.weights))}
      else if(r.visualFallback){const b=new Float32Array(512);this.analyser?.getFloatTimeDomainData(b);amount=Math.max(0,Math.min(1,(pcmRms(b)-.008)*9));pose=amount?1:0}
      if(pose&&amount>.03){r.animatedFrames++;r.firstVisualContext??=r.context.currentTime}
    }
    if(r?.cancelled&&r.stopToRestMs==null)r.stopToRestMs=performance.now()-r.stopAt;
    const p=(now/1000)%4.1,blink=p<.18?Math.sin(Math.PI*p/.18)**2:0;
    this.renderer.draw(pose,amount,blink);this.pose=pose;
    this.onFrame({pose,active:!!segment&&!!r?.playbackActive&&!r.cancelled,waiting:!!r?.playbackActive&&!segment,renderer:this.renderer.renderer||'initializing',speaking:this.speaker.speaking});
    if(r?.context)this.timeline.prune(r.context.currentTime);requestAnimationFrame(t=>this.frame(t));
  }
}
