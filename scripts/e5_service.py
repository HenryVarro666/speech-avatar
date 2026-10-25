"""Loopback-only E5 preview/proxy. SSH forwarding and model process are separate."""
import argparse
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
import time
import urllib.request
import urllib.error


def create_server(root,upstream,ledger,backends=None):
    backends=backends or {}
    for name,url in backends.items():
        if not re.fullmatch(r'[a-z]+',name) or not re.fullmatch(r'http://127\.0\.0\.1:\d+',url):raise ValueError('Invalid loopback backend')
    guard=threading.Lock()
    def log(kind,**data):
        with guard:
            with ledger.open('a') as f:f.write(json.dumps(dict(t=time.perf_counter(),kind=kind,**data),ensure_ascii=False)+'\n')
    def rpc(path,value,target):
        req=urllib.request.Request(target+path,data=json.dumps(value).encode(),headers={'Content-Type':'application/json'})
        return urllib.request.urlopen(req,timeout=150 if path=='/stream' else 5)
    class Handler(SimpleHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def __init__(self,*a,**kw):super().__init__(*a,directory=str(root),**kw)
        def log_message(self,*a):pass
        def js(self,value,status=200):
            b=json.dumps(value,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        def do_GET(self):
            if self.path=='/config':return self.js(dict(json.loads((root/'manifest.json').read_text()),backends=list(backends)))
            target=upstream
            if self.path.startswith('/api/') and self.path.split('/')[2] in backends:
                parts=self.path.split('/');target=backends[parts[2]];self.path='/'+('/'.join(parts[3:]) if parts[3:]==['health'] else 'api/'+'/'.join(parts[3:]))
            if self.path=='/health' or self.path.startswith('/api/job/'):
                path='/health' if self.path=='/health' else '/job/'+self.path.split('/')[-1]
                if path!='/health' and not re.fullmatch(r'/job/[a-zA-Z0-9_-]{1,80}',path):return self.js({'error':'invalid ID'},400)
                try:
                    with urllib.request.urlopen(target+path,timeout=5) as f:return self.js(json.load(f))
                except (OSError,ValueError):return self.js({'error':'TTS worker unavailable'},503)
            return super().do_GET()
        def do_POST(self):
            origin=self.headers.get('Origin');host=self.headers.get('Host')
            if origin and origin!='http://'+str(host):return self.js({'error':'foreign origin'},403)
            target=upstream;backend='default'
            parts=self.path.split('/')
            if len(parts)>3 and parts[1]=='api' and parts[2] in backends:
                backend=parts[2];target=backends[backend];self.path='/api/'+'/'.join(parts[3:])
            try:
                size=int(self.headers.get('Content-Length','0'));assert 0<size<=4096
                q=json.loads(self.rfile.read(size));ident=q['id'];assert re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',ident)
                if self.path=='/api/cancel':
                    with rpc('/cancel',{'id':ident},target) as f:result=json.load(f)
                    log('cancel_forwarded',id=ident,backend=backend,result=result);return self.js(result)
                assert self.path=='/api/tts/stream' and q.get('role') in ['female','male'] and isinstance(q.get('text'),str) and 0<len(q['text'])<=120 and q.get('profile','normal') in ['normal','drop']
            except (ValueError,KeyError,AssertionError):return self.js({'error':'invalid request'},400)
            except OSError:return self.js({'error':'TTS worker unavailable'},503)
            started=time.perf_counter();count=0;samples=0;ended=False;fault=False;first=None
            log('request',id=ident,backend=backend,role=q['role'],text=q['text'],profile=q.get('profile','normal'))
            try:response=rpc('/stream',{k:q[k] for k in ['id','text','role']},target)
            except OSError:return self.js({'error':'TTS worker unavailable'},503)
            self.send_response(200);self.send_header('Content-Type','application/x-ndjson');self.send_header('Cache-Control','no-store');self.send_header('Connection','close');self.end_headers();self.close_connection=True
            try:
                with response:
                    while True:
                        line=response.readline(1048577)
                        if not line:break
                        if len(line)>1048576:raise ValueError('Oversized upstream frame')
                        frame=json.loads(line)
                        if frame.get('id')!=ident:raise ValueError('Wrong upstream ID')
                        self.wfile.write(line);self.wfile.flush()
                        if frame['type']=='audio':
                            if first is None:first=time.perf_counter()-started
                            count+=1;samples+=frame['samples'];log('chunk',id=ident,seq=frame['seq'],samples=frame['samples'],elapsed_s=time.perf_counter()-started)
                            if q.get('profile')=='drop' and count==2:fault=True;log('injected_disconnect',id=ident,samples=samples);break
                        if frame['type']=='end':ended=True
            except (OSError,ValueError):log('client_or_upstream_disconnected',id=ident)
            finally:
                if not ended:
                    try:
                        with rpc('/cancel',{'id':ident},target) as f:result=json.load(f)
                        log('upstream_cancel_after_disconnect',id=ident,result=result)
                    except OSError:log('upstream_cancel_unavailable',id=ident)
                log('stream_closed',id=ident,ended=ended,injected=fault,chunks=count,samples=samples,first_pcm_s=first,elapsed_s=time.perf_counter()-started)
    return ThreadingHTTPServer(('127.0.0.1',0),Handler)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--upstream',required=True);p.add_argument('--backends',type=Path);p.add_argument('--ledger',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    assert re.fullmatch(r'http://127\.0\.0\.1:\d+',a.upstream),'Only loopback forwarding is allowed'
    server=create_server(a.root.resolve(),a.upstream,a.ledger,json.loads(a.backends.read_text()) if a.backends else None)
    a.receipt.write_text(json.dumps({'pid':__import__('os').getpid(),'port':server.server_port,'url':f'http://127.0.0.1:{server.server_port}/index.html','bind':'127.0.0.1'},indent=2)+'\n')
    print('E5_PREVIEW_READY',server.server_port,flush=True);server.serve_forever()


if __name__=='__main__':main()
