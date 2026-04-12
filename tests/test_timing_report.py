"""F5 — test that ``--emit-report`` produces a report with the expected
headline rows. Doesn't pin content byte-for-byte because the report is a
human-readable artifact that may evolve; the test asserts structural
invariants instead.
"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "ddr_timing_table.bin.report.txt")


class TimingReport(unittest.TestCase):
    def setUp(self):
        if os.path.exists(REPORT):
            os.remove(REPORT)

    def _run(self, args):
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "gen_timing_params")] + args,
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=True, text=True,
        )

    def test_lp4_report_contains_expected_frequencies(self):
        self._run([
            "--dram-type", "lpddr4", "--phy-name", "sphy-v9r8",
            "--speed-bin", "4266", "--dq-width", "16",
            "--orbit-config-density", "16", "--wire-length", "10",
            "--read-dbi-upto", "10000", "--write-dbi-upto", "10000",
            "--write-lecc-upto", "625", "--write-odt-upto", "10000",
            "--cpipe-depth", "1", "--dpipe-depth", "1",
            "--omc-freq-ratio", "2", "--phy-freq-ratio", "2",
            "--emit-report", "--orbit-config-use-python",
            "938", "1631", "2500",
        ])
        self.assertTrue(os.path.exists(REPORT))
        with open(REPORT) as f:
            body = f.read()
        self.assertIn("dram_type          : lpddr4", body)
        # freq column: 1066, 613, 400 MHz for the three tCKs above.
        self.assertIn("1066", body)
        self.assertIn("613", body)
        self.assertIn("400", body)
        # Per-frequency section header
        self.assertIn("freq(MHz)", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
