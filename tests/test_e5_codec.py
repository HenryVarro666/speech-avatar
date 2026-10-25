import base64
import hashlib
import unittest
from workers.realtime_tts.streaming import CodecBlocks, Cancelled


class CodecStreamingTests(unittest.TestCase):
    def test_emit_before_finish_with_left_context_and_exact_tail(self):
        frames=[];windows=[]
        def decode(rows):
            windows.append([r[0] for r in rows])
            return bytes(v for r in rows for v in [r[0],0,r[0],0])
        c=CodecBlocks(decode,frames.append,chunk_frames=3,left_context=2,samples_per_frame=2)
        for n in range(7):c.push([n]*16)
        self.assertEqual(len(frames),2)
        c.finish()
        self.assertEqual(windows,[[0,1,2],[1,2,3,4,5],[4,5,6]])
        pcm=b''.join(base64.b64decode(x['pcm']) for x in frames)
        self.assertEqual(pcm,bytes(v for n in range(7) for v in [n,0,n,0]))
        self.assertEqual([x['offset'] for x in frames],[0,6,12])
        self.assertEqual(c.samples,14)
        self.assertEqual(c.sha256,hashlib.sha256(pcm).hexdigest())

    def test_cancel_before_decode_and_after_decode_never_emits(self):
        for during in [False,True]:
            cancelled=[not during];sent=[]
            def decode(rows):cancelled[0]=True;return bytes(4)
            c=CodecBlocks(decode,sent.append,chunk_frames=1,left_context=0,samples_per_frame=2,cancelled=lambda:cancelled[0])
            with self.assertRaises(Cancelled):c.push([1]*16)
            self.assertEqual(sent,[])

    def test_bad_shape_or_decoder_length_cannot_become_success(self):
        c=CodecBlocks(lambda x:b'bad',lambda x:None,chunk_frames=1,left_context=0,samples_per_frame=2)
        with self.assertRaises(ValueError):c.push([0]*15)
        with self.assertRaises(ValueError):c.push([0]*16)
