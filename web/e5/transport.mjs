/** A missing end message is incomplete even if the HTTP stream closes cleanly. */
export class FrameDecoder {
  constructor(id,onFrame=()=>{}) {this.id=id;this.onFrame=onFrame;this.buffer='';this.started=false;this.end=null;this.samples=0;this.seq=0;}
  push(text) {
    this.buffer+=text;if(this.buffer.length>1048576)throw Error('Frame exceeds limit');
    const out=[];let at;
    while((at=this.buffer.indexOf('\n'))>=0){
      const line=this.buffer.slice(0,at);this.buffer=this.buffer.slice(at+1);if(!line.trim())continue;
      const f=JSON.parse(line);if(f.id!==this.id)throw Error('Wrong request ID');if(this.end)throw Error('Frame after end');
      if(f.type==='start'){
        if(this.started||f.rate!==24000||f.channels!==1||f.format!=='s16le')throw Error('Unsupported stream start');this.started=true;
      }else if(f.type==='audio'){
        if(!this.started||f.seq!==this.seq||f.offset!==this.samples||!Number.isInteger(f.samples)||f.samples<=0)throw Error('Noncontiguous audio');
        const bytes=Uint8Array.from(atob(f.pcm),c=>c.charCodeAt(0));if(bytes.length!==f.samples*2)throw Error('Invalid PCM length');
        this.samples+=f.samples;this.seq++;out.push(bytes);
      }else if(f.type==='end'){
        if(!this.started||!this.samples||f.samples!==this.samples)throw Error('Invalid end samples');this.end=f;
      }else if(f.type==='error')throw Error('TTS stream error: '+f.reason);
      else throw Error('Unknown frame');
      this.onFrame(f);
    }return out;
  }
  finish(){if(this.buffer.trim()||!this.end)throw Error('Missing complete end message');return this.end;}
}

export function pcmStream(body,id,onFrame=()=>{}){
  const reader=body.getReader(),decoder=new TextDecoder(),frames=new FrameDecoder(id,onFrame);
  let settled=false,resolve;const completion=new Promise(r=>resolve=r);
  const settle=x=>{if(!settled){settled=true;resolve(x)}};
  const stream=new ReadableStream({
    async pull(controller){
      try{
        while(!settled){
          const x=await reader.read();
          if(settled)return;
          const out=frames.push(decoder.decode(x.value||new Uint8Array(),{stream:!x.done}));
          for(const b of out)controller.enqueue(b);
          if(x.done){const end=frames.finish();settle({status:'complete',...end});controller.close();return}
          if(out.length)return;
        }
      }catch(e){settle({status:'incomplete',error:String(e),samples:frames.samples});try{controller.error(e)}catch{}void reader.cancel().catch(()=>{})}
    },
    async cancel(){settle({status:'cancelled',samples:frames.samples});await reader.cancel().catch(()=>{})}
  });return {stream,completion};
}
