import {test} from 'node:test';
import assert from 'node:assert/strict';
import {FrameDecoder, pcmStream} from '../web/e5/transport.mjs';
const start={type:'start',id:'a',rate:24000,channels:1,format:'s16le'};
const audio={type:'audio',id:'a',seq:0,offset:0,samples:2,pcm:'AABAIA=='};
test('partial NDJSON lines preserve source PCM offsets and require end',()=>{
 const d=new FrameDecoder('a');assert.deepEqual(d.push(JSON.stringify(start)+'\n'+JSON.stringify(audio).slice(0,20)),[]);
 const out=d.push(JSON.stringify(audio).slice(20)+'\n');assert.deepEqual([...out[0]],[0,0,64,32]);
 assert.throws(()=>d.finish(),/end/);d.push(JSON.stringify({type:'end',id:'a',samples:2})+'\n');assert.equal(d.finish().samples,2);
});
test('wrong ID, duplicate sequence, missing source samples, odd PCM and bad end fail',()=>{
 for(const patch of [{id:'old'},{seq:1},{offset:2},{samples:3},{pcm:'AA=='}]){
  const d=new FrameDecoder('a');d.push(JSON.stringify(start)+'\n');assert.throws(()=>d.push(JSON.stringify({...audio,...patch})+'\n'));
 }
 const d=new FrameDecoder('a');d.push(JSON.stringify(start)+'\n'+JSON.stringify(audio)+'\n');assert.throws(()=>d.push(JSON.stringify(audio)+'\n'));
 assert.throws(()=>d.push(JSON.stringify({type:'end',id:'a',samples:99})+'\n'));
});
test('actual reader error remains an incomplete result and cancellation cancels source',async()=>{
 let cancelled=false;const body=new ReadableStream({start(c){c.enqueue(new TextEncoder().encode(JSON.stringify(start)+'\n'+JSON.stringify(audio)+'\n'))},cancel(){cancelled=true}});
 const {stream,completion}=pcmStream(body,'a');const reader=stream.getReader();assert.equal((await reader.read()).value.length,4);await reader.cancel();assert.equal(cancelled,true);assert.equal((await completion).status,'cancelled');
 const broken=new ReadableStream({start(c){c.enqueue(new TextEncoder().encode(JSON.stringify(start)+'\n'+JSON.stringify(audio)+'\n'));c.close()}});
 const b=pcmStream(broken,'a');const r=b.stream.getReader();await r.read();await assert.rejects(r.read());assert.equal((await b.completion).status,'incomplete');
});
