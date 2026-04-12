"""Phase 2 — gate that orbit_tables.gen.h is in sync with orbit_tables.py.

Rebuilds the header in memory via tools/gen_orbit_tables.py::render() and
diffs it against the checked-in file. Any drift means an engineer edited
the generated header by hand (or forgot to re-run the generator) and the
test must fail so that source-of-truth is not silently lost.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import gen_orbit_tables  # noqa: E402


class OrbitTablesGenSync(unittest.TestCase):
    def test_header_matches_python_source(self):
        expected = gen_orbit_tables.render()
        with open(os.path.join(ROOT, "orbit_tables.gen.h")) as f:
            actual = f.read()
        self.assertEqual(
            actual, expected,
            "orbit_tables.gen.h is out of sync with orbit_tables.py. "
            "Re-run: python3 tools/gen_orbit_tables.py",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
