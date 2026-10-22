"""Integrity regressions for frozen experiment inputs, using real temporary WAVs."""
import array
import hashlib
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest
import wave
import subprocess
import sys

spec = importlib.util.spec_from_file_location("validate_e0", Path(__file__).parents[1] / "scripts/validate_e0.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class FrozenInputsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rows = []
        for i in range(2):
            path = self.root / f"{i}.wav"
            samples = array.array("h", (int(3000 * math.sin((i + 1) * n / 8)) for n in range(32000)))
            with wave.open(str(path), "wb") as stream:
                stream.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                stream.writeframes(samples.tobytes())
            self.rows.append({"id": str(i), "family_id": str(i), "split": ["dev", "test"][i],
                              "language": "en", "voice": "local", "text": f"Sentence {i}",
                              "audio_path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                              "provenance": {"kind": "synthetic", "generator": "test"}})

    def test_corrupted_frozen_file_is_rejected(self):
        self.rows[0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash"):
            validator.validate_rows(self.rows, self.root)

    def test_same_family_across_splits_is_rejected_even_for_different_voices(self):
        self.rows[1]["family_id"] = self.rows[0]["family_id"]
        self.rows[1]["voice"] = "other voice"
        with self.assertRaisesRegex(ValueError, "family"):
            validator.validate_rows(self.rows, self.root)

    def test_missing_provenance_is_rejected(self):
        self.rows[0]["provenance"] = {}
        with self.assertRaisesRegex(ValueError, "provenance"):
            validator.validate_rows(self.rows, self.root)

    def test_silent_wave_is_rejected(self):
        path = self.root / self.rows[0]["audio_path"]
        with wave.open(str(path), "wb") as stream:
            stream.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            stream.writeframes(b"\0\0" * 32000)
        self.rows[0]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "silent"):
            validator.validate_rows(self.rows, self.root)

    def test_changed_manifest_is_rejected_before_media_validation(self):
        path = self.root / "manifest.json"
        path.write_text('{"audio": [], "avatars": []}')
        path.with_suffix(".sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest() + "  manifest.json\n")
        path.write_text('{"audio": [], "avatars": [], "changed": true}')
        result = subprocess.run([sys.executable, str(Path(__file__).parents[1] / "scripts/validate_e0.py"), str(path)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("frozen manifest hash", result.stderr)


if __name__ == "__main__":
    unittest.main()
