"""Isolated CPU Qwen3-TTS stream worker. No shared model/runtime writes."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1')
import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import random
import re
import threading
import time
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from workers.realtime_tts.jobs import Jobs
from workers.realtime_tts.streaming import CodecBlocks,Cancelled


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(4*1024*1024),b''):h.update(data)
    return h.hexdigest()


class Engine:
    def __init__(self,root,prior):
        self.root=root;self.spec=json.loads((root/'manifest.json').read_text());self.jobs=Jobs(self.spec['max_requests'])
        pins=json.loads((root/'runtime-pin.json').read_text())
        for p,h in pins.items():assert sha(prior/p)==h,('Pinned runtime mismatch',p)
        model_manifest=json.loads((prior/'model_manifest.json').read_text())
        assert model_manifest['revision']==self.spec['model_revision']
        for f in model_manifest['files']:assert sha(prior/'model'/f['path'])==f['sha256'],f['path']
        available=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))
        assert available>20*1024*1024,'Insufficient availableRAM'
        started=time.perf_counter()
        import numpy as np
        import torch
        from qwen_tts import Qwen3TTSModel
        self.np,self.torch=np,torch;torch.set_num_threads(4);torch.set_num_interop_threads(1)
        assert not torch.cuda.is_available()
        self.model=Qwen3TTSModel.from_pretrained(str(prior/'model'),device_map='cpu',dtype=torch.bfloat16,attn_implementation='sdpa')
        assert all(p.device.type=='cpu' for p in self.model.model.parameters())
        self.samples_per_frame=int(self.model.model.speech_tokenizer.model.decoder.total_upsample)
        self.load={'load_s':time.perf_counter()-started,'device':'cpu','model_revision':model_manifest['revision'],
                   'samples_per_frame':self.samples_per_frame,'rate':24000,'torch':torch.__version__,'pid':os.getpid(),
                   'affinity':sorted(os.sched_getaffinity(0)),'threads':torch.get_num_threads(),'model_files_checked':len(model_manifest['files'])}
        (root/'load.json').write_text(json.dumps(self.load,indent=2)+'\n')

    def generate(self,job,req,send):
        np,torch=self.np,self.torch;model=self.model;ident=job['id'];out=self.root/'jobs'/ident;out.mkdir(parents=True)
        pcm_file=(out/'stream.pcm').open('xb');started=time.perf_counter();chunks=[]
        def check():
            if time.perf_counter()-started>120:job['cancel'].set();raise TimeoutError('Generation120s limit')
            rss=int(next(x.split()[1] for x in Path('/proc/self/status').read_text().splitlines() if x.startswith('VmRSS:')))
            job['peak_rss_kib']=max(job.get('peak_rss_kib',0),rss)
            if rss>16*1024*1024:raise MemoryError('Owned worker RSS ceiling')
            return job['cancel'].is_set()
        def decode(rows):
            waves,rate=model.model.speech_tokenizer.decode([{'audio_codes':torch.tensor(rows,dtype=torch.long)}])
            assert rate==24000
            audio=np.asarray(waves[0],np.float32)
            assert audio.ndim==1 and np.isfinite(audio).all() and float(np.abs(audio).max())<1
            return np.rint(audio*32768).clip(-32768,32767).astype('<i2').tobytes()
        def emit(frame):
            stamp=time.perf_counter();job.setdefault('first_pcm_s',stamp-started)
            data=base64.b64decode(frame['pcm']);pcm_file.write(data);pcm_file.flush()
            frame['worker_elapsed_s']=stamp-started;send(frame)
            chunks.append({k:v for k,v in frame.items() if k!='pcm'});job['samples_emitted']=frame['offset']+frame['samples']
        blocks=CodecBlocks(decode,emit,chunk_frames=self.spec['chunk_frames'],left_context=self.spec['left_context_frames'],samples_per_frame=self.samples_per_frame,cancelled=check)
        def hook(module,inputs,output):
            if check():raise Cancelled()
            codes=output.hidden_states[1]
            if codes is None:return
            assert tuple(codes.shape)==(1,16)
            row=codes[0].detach().cpu().tolist()
            if row[0]==model.model.config.talker_config.codec_eos_token_id:return
            blocks.push(row)
        handle=None
        try:
            random.seed(self.spec['seed']);np.random.seed(self.spec['seed']);torch.manual_seed(self.spec['seed'])
            send({'type':'start','rate':24000,'channels':1,'format':'s16le','role':req['role'],'speaker':self.spec['speaker_by_role'][req['role']]})
            handle=model.model.talker.register_forward_hook(hook)
            with torch.inference_mode():
                ids=model._tokenize_texts([model._build_assistant_text(req['text'])])
                ins=model._tokenize_texts([model._build_instruct_text(self.spec['instruct'])])[0]
                kwargs=model._merge_generate_kwargs(**self.spec['generation'])
                codes,_=model.model.generate(input_ids=ids,instruct_ids=[ins],languages=['Chinese'],speakers=[self.spec['speaker_by_role'][req['role']]],non_streaming_mode=True,**kwargs)
                job['lm_complete_s']=time.perf_counter()-started
                assert np.array_equal(codes[0].cpu().numpy(),np.asarray(blocks.rows)), 'Captured codes differ from official generation'
                assert len(blocks.rows)<self.spec['generation']['max_new_tokens']-2,'Token limit reached; do not report truncated speech complete'
                blocks.finish()
            job.update(samples=blocks.samples,pcm_sha256=blocks.sha256,codec_frames=len(blocks.rows),codes_exact=True,
                       first_chunk_before_lm_complete=job.get('first_pcm_s',float('inf'))<job['lm_complete_s'],generation_s=time.perf_counter()-started)
            send({'type':'end','samples':blocks.samples,'sha256':blocks.sha256,'worker':{k:job[k] for k in ['first_pcm_s','lm_complete_s','generation_s','codec_frames','codes_exact','first_chunk_before_lm_complete','peak_rss_kib']}})
            self.jobs.finish(job,'complete')
        except (Cancelled,BrokenPipeError,ConnectionResetError):
            job['cancel'].set();self.jobs.finish(job,'cancelled')
        except Exception as e:
            job['error']=type(e).__name__+': '+str(e);self.jobs.finish(job,'failed')
            try:send({'type':'error','reason':type(e).__name__})
            except (BrokenPipeError,ConnectionResetError):pass
        finally:
            if handle:handle.remove()
            pcm_file.close()
            if job['status']=='generating':self.jobs.finish(job,'failed')
            receipt={**self.jobs.snapshot(ident),'request':req,'chunks':chunks,'human_av_accepted':None}
            (out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--prior',type=Path,required=True);p.add_argument('--port',type=int,default=0);a=p.parse_args()
    root=a.root.resolve();assert root.is_dir() and not(root/'worker.json').exists(),'New run directory required'
    os.sched_setaffinity(0,{80,81,82,83});os.nice(19)
    engine=Engine(root,a.prior.resolve())
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def log_message(self,*args):pass
        def json(self,value,status=200):
            b=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        def do_GET(self):
            if self.path=='/health':return self.json({'ready':True,'device':'cpu','rate':24000,'model':engine.spec['model']})
            if self.path.startswith('/job/'):
                return self.json(engine.jobs.snapshot(self.path.split('/')[-1]))
            return self.json({'error':'not found'},404)
        def do_POST(self):
            try:
                size=int(self.headers.get('Content-Length','0'));assert 0<size<=4096
                req=json.loads(self.rfile.read(size));ident=req['id'];assert re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',ident)
                if self.path=='/cancel':return self.json(engine.jobs.cancel(ident))
                assert self.path=='/stream' and req.get('role') in ['female','male'] and isinstance(req.get('text'),str) and 0<len(req['text'])<=120
                job=engine.jobs.submit(ident)
            except (ValueError,KeyError,AssertionError):return self.json({'error':'invalid or duplicate request/budget'},400)
            self.send_response(200);self.send_header('Content-Type','application/x-ndjson');self.send_header('Connection','close');self.end_headers();self.close_connection=True
            def send(frame):
                self.wfile.write((json.dumps(dict(frame,id=ident),ensure_ascii=False)+'\n').encode());self.wfile.flush()
            try:
                with engine.jobs.claim(job):engine.generate(job,req,send)
            except (Cancelled,TimeoutError):engine.jobs.finish(job,'cancelled')
    server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    (root/'worker.json').write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1],'device':'cpu','bind':'127.0.0.1'},indent=2)+'\n')
    print('E5_WORKER_READY',server.server_address[1],flush=True);server.serve_forever()


if __name__=='__main__':main()
