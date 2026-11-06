"""Phase 2 — the ``check-c-python-parity`` CI gate.

For each supported (dram_type, two_channel, density) combination, run the
Python generator, capture the output, zero the orbit_config region, rebuild
``ddr_config_bin.c`` as the C oracle, run it, and assert byte-identity.

This is the structural successor to the Phase 0 P0-5 regression test. Once
this lands, future Python/C divergence on any supported config surfaces as a
single red test with a concrete matrix cell.
"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXEC = os.path.join(ROOT, "ddr_config_bin_parity_exec")

COMBINATIONS = [
    # (dram_type, two_channel, density, periods)
    ("lpddr4", False, 16, ["938", "1631", "2500"]),
    ("lpddr4", False, 8,  ["938", "1631", "2500"]),
    ("lpddr4", True,  16, ["938", "1631", "2500"]),
    ("lpddr5", False, 16, ["314", "418", "556", "2500"]),
    ("lpddr5", False, 8,  ["314", "418", "556", "2500"]),
    ("lpddr5", True,  16, ["314", "418", "556", "2500"]),
]


def _run(cmd, **kwargs):
    return subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, check=True, **kwargs)


def _python_args(dram_type, two_channel, density, periods):
    args = [sys.executable, os.path.join(ROOT, "gen_timing_params"),
            "--dram-type", dram_type,
            "--phy-name", "sphy-v9r8",
            "--speed-bin", "4266" if dram_type == "lpddr4" else "6400",
            "--dq-width", "16",
            "--orbit-config-density", str(density),
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


def _build_c(dram_type, two_channel, density):
    if os.path.exists(EXEC):
        os.remove(EXEC)
    # ddr_config.h is generated from the checked-in template and gitignored.
    template = os.path.join(ROOT, "ddr_config.h.template")
    target = os.path.join(ROOT, "ddr_config.h")
    if os.path.exists(template):
        import shutil
        shutil.copyfile(template, target)
    _run(["gcc", "-std=c99",
          "-D", "DDR_TYPE=%d" % (2 if dram_type == "lpddr4" else 3),
          "-D", "DDR_TWO_CHANNEL=%d" % (1 if two_channel else 0),
          "-D", "ORBIT_DENSITY=%d" % density,
          "-I", ".",
          "ddr_config_bin.c",
          "-o", os.path.basename(EXEC)])


def _check_combo(case, dram_type, two_channel, density, periods):
    _run(_python_args(dram_type, two_channel, density, periods))
    bin_path = os.path.join(ROOT, "ddr_timing_table.bin")
    with open(bin_path, "rb") as f:
        py_data = f.read()
    # Recreate the timing-table-only file the C generator expects: the SCP
    # flow writes the timing table first, then appends the orbit prefix.
    with open(bin_path, "wb") as f:
        f.write(py_data[:0x800])
    _build_c(dram_type, two_channel, density)
    _run([EXEC])
    with open(bin_path, "rb") as f:
        c_data = f.read()
    case.assertEqual(
        len(c_data), len(py_data),
        "%s %s density=%d size mismatch (Python=%d C=%d)" % (
            dram_type, "dual" if two_channel else "single",
            density, len(py_data), len(c_data),
        ),
    )
    case.assertEqual(
        c_data, py_data,
        "%s %s density=%d Python/C byte mismatch" % (
            dram_type, "dual" if two_channel else "single", density,
        ),
    )


def _make_test(dram_type, two_channel, density, periods):
    def test(self):
        _check_combo(self, dram_type, two_channel, density, periods)
    test.__name__ = "test_parity_%s_%s_d%d" % (
        dram_type, "dual" if two_channel else "single", density,
    )
    return test


class CheckCPythonParity(unittest.TestCase):
    pass


for combo in COMBINATIONS:
    fn = _make_test(*combo)
    setattr(CheckCPythonParity, fn.__name__, fn)


if __name__ == "__main__":
    unittest.main(verbosity=2)
