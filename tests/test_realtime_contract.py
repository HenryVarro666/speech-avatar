"""Node contract checks need no portrait, audio, model or GPU."""
import subprocess
import unittest
from pathlib import Path
class RealtimeContract(unittest.TestCase):
    def test_timeline_and_mapping(self):
        root=Path(__file__).resolve().parents[1]
        result=subprocess.run(['node','--test','tests/realtime-clock.test.mjs'],cwd=root,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
