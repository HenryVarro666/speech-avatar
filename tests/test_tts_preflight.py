"""Protect shared GPU workloads and existing listening candidates."""
import importlib.util
from pathlib import Path
import tempfile
import unittest


class TTSPreflightTests(unittest.TestCase):
    def worker(self):
        path = Path(__file__).resolve().parents[1] / "workers/tts/generate_custom_voice.py"
        self.assertTrue(path.exists(), "TTS preflight worker is not implemented")
        spec = importlib.util.spec_from_file_location("tts_worker", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_other_gpu_is_allowed_but_selected_gpu_is_protected(self):
        worker = self.worker()
        worker.assert_gpu_available("other, 12\nchosen, 45", "chosen", 45)
        with self.assertRaisesRegex(RuntimeError, "external GPU process"):
            worker.assert_gpu_available("other, 12\nchosen, 99", "chosen", 45)

    def test_existing_waveform_is_never_overwritten(self):
        worker = self.worker()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "female.wav").write_bytes(b"preserve me")
            with self.assertRaises(FileExistsError):
                worker.assert_new_outputs(root, ["female", "male"])
            self.assertEqual((root / "female.wav").read_bytes(), b"preserve me")

    def test_unrecognizable_gpu_output_fails_closed(self):
        worker = self.worker()
        with self.assertRaises(ValueError):
            worker.assert_gpu_available("driver error", "chosen", 45)


if __name__ == "__main__":
    unittest.main()
