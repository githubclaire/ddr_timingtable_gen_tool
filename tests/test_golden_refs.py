"""F7 — golden reference CI matrix.

Complements ``test_c_python_parity``: that test verifies Python == C on
each invocation, i.e. it pins the *structural* parity between the two
paths but not the *numerical* values. If a future refactor changes a
coefficient and both the C and Python paths drift in lock-step, parity
still holds but the emitted binary silently mutates.

This test locks the numerical output to the four committed reference
binaries (``ddr_timing_table.<lpddr4|lpddr5>.<single|dual>.ref.bin``),
which were regenerated during Phase 0. If a change intentionally moves
the numbers, the engineer must refresh the refs via
``tools/refresh_golden_refs.py`` as a deliberate, reviewed step.
"""
import hashlib
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MATRIX = [
    # (dram_type, two_channel, periods, ref_name)
    ("lpddr4", False, ["938", "1631", "2500"],
     "ddr_timing_table.lpddr4.single.ref.bin"),
    ("lpddr4", True,  ["938", "1631", "2500"],
     "ddr_timing_table.lpddr4.dual.ref.bin"),
    ("lpddr5", False, ["314", "418", "556", "2500"],
     "ddr_timing_table.lpddr5.single.ref.bin"),
    ("lpddr5", True,  ["314", "418", "556", "2500"],
     "ddr_timing_table.lpddr5.dual.ref.bin"),
]


def _python_args(dram_type, two_channel, periods):
    args = [sys.executable, os.path.join(ROOT, "gen_timing_params"),
            "--dram-type", dram_type,
            "--phy-name", "sphy-v9r8",
            "--speed-bin", "4266" if dram_type == "lpddr4" else "6400",
            "--dq-width", "16",
            "--orbit-config-density", "16",
            "--wire-length", "10",
            "--read-dbi-upto", "10000",
            "--write-dbi-upto", "10000",
            "--write-lecc-upto", "625",
            "--write-odt-upto", "10000",
            "--cpipe-depth", "1",
            "--dpipe-depth", "1",
            "--omc-freq-ratio", "1" if dram_type == "lpddr5" else "2",
            "--phy-freq-ratio", "1" if dram_type == "lpddr5" else "2"]
    if dram_type == "lpddr5":
        args += ["--wck-1to4-upto", "625",
                 "--wck-always-on-from", "0",
                 "--wck-always-on-upto", "10000"]
    if two_channel:
        args.append("--two-channel")
    args.append("--orbit-config-use-python")
    args.extend(periods)
    return args


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def _check_combo(case, dram_type, two_channel, periods, ref_name):
    ref_path = os.path.join(ROOT, ref_name)
    case.assertTrue(os.path.exists(ref_path), "missing golden ref %s" % ref_name)
    subprocess.run(_python_args(dram_type, two_channel, periods),
                   cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                   check=True, text=True)
    bin_path = os.path.join(ROOT, "ddr_timing_table.bin")
    produced = _sha(bin_path)
    expected = _sha(ref_path)
    case.assertEqual(
        produced, expected,
        "%s %s: golden drift (got %s, want %s). "
        "If intentional, run tools/refresh_golden_refs.py and review the diff."
        % (dram_type, "dual" if two_channel else "single", produced, expected),
    )


def _make_test(dram_type, two_channel, periods, ref_name):
    def test(self):
        _check_combo(self, dram_type, two_channel, periods, ref_name)
    test.__name__ = "test_golden_%s_%s" % (
        dram_type, "dual" if two_channel else "single",
    )
    return test


class GoldenRefMatrix(unittest.TestCase):
    pass


for combo in MATRIX:
    fn = _make_test(*combo)
    setattr(GoldenRefMatrix, fn.__name__, fn)


if __name__ == "__main__":
    unittest.main(verbosity=2)
