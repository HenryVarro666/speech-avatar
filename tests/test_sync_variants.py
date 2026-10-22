import importlib.util
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import wave

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/make_sync_variants.py'
spec = importlib.util.spec_from_file_location('sync_variants', SCRIPT)
sync_variants = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_variants)


class SyncVariantsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.video = self.root/'source.mp4'
        self.audio = self.root/'source.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                        'testsrc2=size=64x64:rate=25:duration=0.4', '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p', str(self.video)], check=True)
        with wave.open(str(self.audio), 'wb') as output:
            output.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
            output.writeframes(b''.join(struct.pack('<h', 4000 if i%16<8 else -4000)
                                        for i in range(9600)))

    def tearDown(self):
        self.temp.cleanup()

    def check_delay(self, delay, padding):
        target = self.root/('derived-%s.mp4'%delay)
        derived_wav = self.root/('derived-%s.wav'%delay)
        result = sync_variants.make_variant(self.video, self.audio, target, derived_wav, delay)
        original = sync_variants.raw_frames(self.video)
        actual = sync_variants.raw_frames(target)
        self.assertEqual(actual[padding:], original)
        self.assertTrue(all(frame==original[0] for frame in actual[:padding]))
        with wave.open(str(self.audio)) as source, wave.open(str(derived_wav)) as derived:
            self.assertEqual(derived.readframes(9600), source.readframes(9600))
            self.assertEqual(derived.readframes(1920), b'\0'*(padding*960*2))
        self.assertEqual(result['source_frame_count'], 10)
        self.assertEqual(result['derived_frame_count'], 10+padding)
        self.assertTrue(result['all_source_video_frames_identical'])

    def test_positive_delay_prepends_frames_and_never_moves_audio(self):
        self.check_delay(80, 2)

    def test_zero_control_preserves_every_source_frame(self):
        self.check_delay(0, 0)

    def test_invalid_delay_and_existing_output_are_rejected(self):
        target = self.root/'keep.mp4'
        target.write_bytes(b'preserve')
        with self.assertRaises(FileExistsError):
            sync_variants.make_variant(self.video, self.audio, target, self.root/'d.wav', 40)
        self.assertEqual(target.read_bytes(), b'preserve')
        for delay in [-40, 20]:
            with self.assertRaises(ValueError):
                sync_variants.make_variant(self.video, self.audio, self.root/'unused.mp4',
                                           self.root/'unused.wav', delay)


if __name__=='__main__':
    unittest.main()
