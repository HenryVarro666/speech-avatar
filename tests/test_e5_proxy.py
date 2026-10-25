import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from scripts.e5_service import create_server


class LiveProxyTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];calls=self.calls
        class Upstream(BaseHTTPRequestHandler):
            def log_message(self,*a):pass
            def do_POST(self):
                q=json.loads(self.rfile.read(int(self.headers['Content-Length'])));calls.append((self.path,q))
                self.send_response(200);self.end_headers()
                if self.path=='/cancel':self.wfile.write(b'{}');return
                for f in [{'type':'start','id':q['id']},*({'type':'audio','id':q['id'],'seq':i,'samples':2,'pcm':'AAAAAA=='} for i in range(3)),{'type':'end','id':q['id']}]:
                    try:self.wfile.write((json.dumps(f)+'\n').encode());self.wfile.flush()
                    except BrokenPipeError:break
        self.up=ThreadingHTTPServer(('127.0.0.1',0),Upstream);threading.Thread(target=self.up.serve_forever,daemon=True).start()
        self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name);(root/'manifest.json').write_text('{"utterances":[]}');(root/'index.html').write_text('local')
        self.proxy=create_server(root,f'http://127.0.0.1:{self.up.server_port}',root/'events.jsonl');threading.Thread(target=self.proxy.serve_forever,daemon=True).start();self.url=f'http://127.0.0.1:{self.proxy.server_port}'
    def tearDown(self):self.proxy.shutdown();self.up.shutdown();self.proxy.server_close();self.up.server_close();self.tmp.cleanup()
    def post(self,q,origin=None):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        return urllib.request.urlopen(urllib.request.Request(self.url+'/api/tts/stream',data=json.dumps(q).encode(),headers=headers),timeout=3)
    def test_live_chunks_pass_normally_and_drop_has_no_end_then_cancels_upstream(self):
        q={'id':'a','role':'female','text':'你好','profile':'normal'}
        with self.post(q) as f:frames=[json.loads(x) for x in f]
        self.assertEqual(frames[-1]['type'],'end')
        with self.post(dict(q,id='b',profile='drop')) as f:frames=[json.loads(x) for x in f]
        self.assertEqual(sum(x['type']=='audio' for x in frames),2);self.assertNotIn('end',[x['type'] for x in frames]);self.assertIn(('/cancel',{'id':'b'}),self.calls)
    def test_foreign_origin_and_unbounded_text_are_rejected_before_upstream(self):
        for q,origin in [({'id':'a','text':'你','role':'female'},'https://example.com'),({'id':'a','text':'你'*121,'role':'female'},None)]:
            with self.assertRaises(urllib.error.HTTPError):self.post(q,origin)
        self.assertEqual(self.calls,[])

    def test_explicit_backend_routes_stream_cancel_and_health_without_fallback(self):
        root=Path(self.tmp.name)
        server=create_server(root,f'http://127.0.0.1:{self.up.server_port}',root/'routed.jsonl',backends={'cpu':f'http://127.0.0.1:{self.up.server_port}','gpu':'http://127.0.0.1:1'})
        threading.Thread(target=server.serve_forever,daemon=True).start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with urllib.request.urlopen(base+'/config') as f:self.assertEqual(json.load(f)['backends'],['cpu','gpu'])
            req=lambda path:urllib.request.Request(base+path,data=json.dumps({'id':'routed','text':'你好','role':'female'}).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req('/api/cpu/tts/stream')) as f:self.assertEqual(json.loads(list(f)[-1])['type'],'end')
            with urllib.request.urlopen(req('/api/cpu/cancel')) as f:json.load(f)
            before=len(self.calls)
            for path in ['/api/gpu/tts/stream','/api/unknown/tts/stream']:
                with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(req(path))
            self.assertEqual(len(self.calls),before)
            self.assertIn(('/cancel',{'id':'routed'}),self.calls)
        finally:server.shutdown();server.server_close()
