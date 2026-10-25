import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_e1d_inputs import crop_reference


class ReferenceFraming(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / 'source.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                        'testsrc=size=12x10:rate=1', '-frames:v', '1', str(self.source)],
                       check=True, capture_output=True)
        self.digest = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def test_crop_preserves_exact_source_pixels(self):
        target = self.source.with_name('crop.png')
        row = crop_reference(self.source, target, [2, 1, 8, 7], self.digest)
        raw = lambda p: subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(p),
            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stderr=subprocess.PIPE)
        source = raw(self.source)
        expected = b''.join(source[(y*12+2)*3:(y*12+8)*3] for y in range(1, 7))
        self.assertEqual(raw(target), expected)
        self.assertTrue(row['all_pixels_equal_source_roi'])
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.digest)

    def test_wrong_hash_and_invalid_box_leave_no_output(self):
        target = self.source.with_name('crop.png')
        with self.assertRaises(ValueError):
            crop_reference(self.source, target, [2, 1, 8, 7], '0'*64)
        for box in [[-1, 1, 8, 7], [2, 1, 13, 7], [8, 1, 2, 7], [2, 1.5, 8, 7]]:
            with self.assertRaises(ValueError):
                crop_reference(self.source, target, box, self.digest)
        self.assertFalse(target.exists())

    def test_existing_reference_is_never_overwritten(self):
        target = self.source.with_name('crop.png')
        target.write_bytes(b'keep-existing-reference')
        with self.assertRaises(FileExistsError):
            crop_reference(self.source, target, [2, 1, 8, 7], self.digest)
        self.assertEqual(target.read_bytes(), b'keep-existing-reference')
