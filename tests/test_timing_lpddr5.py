"""Phase 5 — pinned timing regression tests for LPDDR5.

See tests/test_timing_lpddr4.py for the rationale.
"""
import hashlib
import os
import struct
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LP5_ARGS = [
    sys.executable, os.path.join(ROOT, "gen_timing_params"),
    "--dram-type", "lpddr5",
    "--phy-name", "sphy-v9r8",
    "--speed-bin", "6400",
    "--dq-width", "16",
    "--orbit-config-density", "16",
    "--wire-length", "10",
    "--read-dbi-upto", "10000",
    "--write-dbi-upto", "10000",
    "--write-lecc-upto", "625",
    "--write-odt-upto", "10000",
    "--cpipe-depth", "1",
    "--dpipe-depth", "1",
    "--omc-freq-ratio", "1",
    "--phy-freq-ratio", "1",
    "--wck-1to4-upto", "625",
    "--wck-always-on-from", "0",
    "--wck-always-on-upto", "10000",
    "--orbit-config-use-python",
    "314", "418", "556", "2500",
]

LP5_EXPECTED_SHA256 = \
    "4f08f34b95438fccb2c60595618bf10f6feed0ab959af791721793e2a0638e66"
LP5_ENTRY_SIZE = 0x15C
# t_ck is stored in hardware units (not the CLI period — LP5 converts);
# these are the values actually written to each entry's +0x4 slot.
LP5_EXPECTED_TCK = [1256, 1672, 2224, 5000]


class LPDDR5TimingPin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(LP5_ARGS, cwd=ROOT, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        with open(os.path.join(ROOT, "ddr_timing_table.bin"), "rb") as f:
            cls.data = f.read()

    def test_sha256_pinned(self):
        actual = hashlib.sha256(self.data).hexdigest()
        self.assertEqual(
            actual, LP5_EXPECTED_SHA256,
            "LP5 timing table sha256 drifted. If intentional, update "
            "LP5_EXPECTED_SHA256 in tests/test_timing_lpddr5.py.",
        )

    def test_per_entry_tck_values(self):
        for i, expected in enumerate(LP5_EXPECTED_TCK):
            off = i * LP5_ENTRY_SIZE
            t_ck = struct.unpack("<I", self.data[off + 4:off + 8])[0]
            self.assertEqual(
                t_ck, expected,
                "entry %d t_ck mismatch: got %d expected %d" %
                (i, t_ck, expected),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
