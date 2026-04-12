"""Python wrapper for tests/test_struct_layout.sh so the Phase 1 layout CI gate
is reachable from ``python3 -m unittest``.
"""
import os
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "tests", "test_struct_layout.sh")


class StructLayoutTest(unittest.TestCase):
    def test_python_matches_c(self):
        result = subprocess.run([SCRIPT], cwd=ROOT,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
        self.assertEqual(
            result.returncode, 0,
            "struct layout diverges:\nstdout:\n%s\nstderr:\n%s" %
            (result.stdout, result.stderr),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
