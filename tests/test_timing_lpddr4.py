"""Phase 5 — pinned timing regression tests for LPDDR4.

Runs gen_timing_params against a fixed LP4 configuration (4266 speed-bin,
periods 938/1631/2500 ps, density 16) and asserts:

  * the full binary sha256 is unchanged (cheap global regression gate), and
  * the per-entry t_ck values at the head of each timing entry match the
    intended frequency points (a semantic sanity check that would have
    caught e.g. the P0-2 `wck_always_on` inversion when the period was in
    the affected window).

When the generator output legitimately changes, update the expected
sha256 in one place. The test double-runs the generator before hashing
so transient `ddr_timing_table.bin` state from a prior test can't mask a
real regression.
"""
import hashlib
import os
import struct
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LP4_ARGS = [
    sys.executable, os.path.join(ROOT, "gen_timing_params"),
    "--dram-type", "lpddr4",
    "--phy-name", "sphy-v9r8",
    "--speed-bin", "4266",
    "--dq-width", "16",
    "--orbit-config-density", "16",
    "--wire-length", "10",
    "--read-dbi-upto", "10000",
    "--write-dbi-upto", "10000",
    "--write-lecc-upto", "625",
    "--write-odt-upto", "10000",
    "--cpipe-depth", "1",
    "--dpipe-depth", "1",
    "--omc-freq-ratio", "2",
    "--phy-freq-ratio", "2",
    "--orbit-config-use-python",
    "938", "1631", "2500",
]

LP4_EXPECTED_SHA256 = \
    "c7b6120581a93e8a979ba9c5543f5b73f30c0165e0105b4902002bdf58559f1e"
LP4_ENTRY_SIZE = 0x128
LP4_EXPECTED_TCK = [938, 1631, 2500]


class LPDDR4TimingPin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(LP4_ARGS, cwd=ROOT, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        with open(os.path.join(ROOT, "ddr_timing_table.bin"), "rb") as f:
            cls.data = f.read()

    def test_sha256_pinned(self):
        actual = hashlib.sha256(self.data).hexdigest()
        self.assertEqual(
            actual, LP4_EXPECTED_SHA256,
            "LP4 timing table sha256 drifted. If this change is intentional, "
            "update LP4_EXPECTED_SHA256 in tests/test_timing_lpddr4.py.",
        )

    def test_per_entry_tck_values(self):
        for i, expected in enumerate(LP4_EXPECTED_TCK):
            off = i * LP4_ENTRY_SIZE
            t_ck = struct.unpack("<I", self.data[off + 4:off + 8])[0]
            self.assertEqual(
                t_ck, expected,
                "entry %d t_ck mismatch: got %d expected %d" %
                (i, t_ck, expected),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
