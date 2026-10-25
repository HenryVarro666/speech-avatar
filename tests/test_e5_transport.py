import subprocess
import unittest
from pathlib import Path


class E5BrowserTransport(unittest.TestCase):
    def test_protocol_contracts(self):
        root=Path(__file__).resolve().parents[1]
        result=subprocess.run(['node','--test','tests/e5-transport.test.mjs'],cwd=root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
