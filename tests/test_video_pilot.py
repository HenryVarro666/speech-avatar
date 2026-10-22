import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


class VideoPilotGuards(unittest.TestCase):
    def module(self):
        file = Path(__file__).resolve().parents[1] / 'workers/pilot_common.py'
        self.assertTrue(file.exists(), 'Video pilot input guards are not implemented')
        spec = importlib.util.spec_from_file_location('pilot_common', file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self, root, accepted=True, segments=2):
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        for name in ['voice.wav', 'image.png', 'reference.mp4']:
            (root / name).write_bytes(b'frozen-' + name.encode())
        review = {'clips': [{'audio_id': 'audio', 'accepted': accepted,
                             'reviewed_audio_sha256': digest(root/'voice.wav')}]}
        (root/'audio_review.json').write_text(json.dumps(review))
        trial = {'trial_id': 'test', 'audio_id': 'audio', 'backend': 'longcat-avatar-v15-int8-distill',
                 'audio_path': 'voice.wav', 'audio_sha256': digest(root/'voice.wav'),
                 'image_path': 'image.png', 'image_sha256': digest(root/'image.png'),
                 'reference_path': 'reference.mp4', 'reference_sha256': digest(root/'reference.mp4'),
                 'audio_duration_s': 5.36, 'num_segments': segments,
                 'planned_output_path': 'outputs/result.mp4'}
        manifest = {'audio_review_sha256': digest(root/'audio_review.json'), 'trials': [trial]}
        (root/'manifest.json').write_text(json.dumps(manifest))
        (root/'manifest.sha256').write_text(digest(root/'manifest.json')+'  manifest.json\n')

    def test_modified_audio_is_rejected(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.fixture(root)
            (root/'voice.wav').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'audio hash'):
                module.load_trial(root, 'test')

    def test_unaccepted_voice_is_rejected_even_with_consistent_hashes(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.fixture(root, accepted=False)
            with self.assertRaisesRegex(ValueError, 'not accepted'):
                module.load_trial(root, 'test')

    def test_short_coverage_and_existing_output_are_rejected(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.fixture(root, segments=1)
            with self.assertRaisesRegex(ValueError, 'coverage'):
                module.load_trial(root, 'test')
            self.fixture(root, segments=2)
            (root/'outputs').mkdir(); (root/'outputs/result.mp4').write_bytes(b'keep')
            with self.assertRaises(FileExistsError):
                module.load_trial(root, 'test')

    def test_missing_ffprobe_is_rejected_before_gpu_work(self):
        module = self.module()
        self.assertTrue(hasattr(module, 'assert_media_tools'), 'Media executable preflight is missing')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'ffmpeg').write_text('#!/bin/sh\nexit 0\n')
            (root/'ffmpeg').chmod(0o755)
            previous = os.environ.get('PATH', '')
            try:
                os.environ['PATH'] = str(root)
                with self.assertRaisesRegex(RuntimeError, 'ffprobe'):
                    module.assert_media_tools()
            finally:
                os.environ['PATH'] = previous


if __name__ == '__main__':
    unittest.main()
