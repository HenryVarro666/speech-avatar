"""Small, dependency-free streaming bookkeeping; model/decoder live in worker.py."""
import base64
import hashlib


class Cancelled(Exception):
    pass


class CodecBlocks:
    def __init__(self,decode,emit,*,chunk_frames=12,left_context=25,samples_per_frame=1920,cancelled=lambda:False):
        self.decode,self.emit,self.cancelled=decode,emit,cancelled
        self.chunk_frames,self.left_context,self.samples_per_frame=chunk_frames,left_context,samples_per_frame
        self.rows=[];self.emitted_frames=0;self.samples=0;self.seq=0;self.digest=hashlib.sha256()

    @property
    def sha256(self):return self.digest.hexdigest()

    def push(self,row):
        if self.cancelled():raise Cancelled()
        if len(row)!=16 or any(not isinstance(x,int) or x<0 or x>=2048 for x in row):raise ValueError('Invalid codec frame')
        self.rows.append(list(row))
        if len(self.rows)-self.emitted_frames>=self.chunk_frames:self._flush()

    def _flush(self):
        if self.cancelled():raise Cancelled()
        if len(self.rows)==self.emitted_frames:return
        start=max(0,self.emitted_frames-self.left_context)
        context=self.emitted_frames-start
        pcm=self.decode(self.rows[start:])
        expected=(len(self.rows)-start)*self.samples_per_frame*2
        if not isinstance(pcm,bytes) or len(pcm)!=expected:raise ValueError('Unexpected decoder PCM length')
        if self.cancelled():raise Cancelled()
        pcm=pcm[context*self.samples_per_frame*2:]
        samples=len(pcm)//2
        self.emit({'type':'audio','seq':self.seq,'offset':self.samples,'samples':samples,
                   'pcm':base64.b64encode(pcm).decode(),'sha256':hashlib.sha256(pcm).hexdigest()})
        self.digest.update(pcm);self.samples+=samples;self.seq+=1;self.emitted_frames=len(self.rows)

    def finish(self):self._flush()
