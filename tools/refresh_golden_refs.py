#!/usr/bin/env python3
"""Regenerate the committed golden reference binaries.

This is a *deliberate* refresh tool: running it overwrites the four
``ddr_timing_table.<dram>.<channel>.ref.bin`` files at the repo root.
Use it only when an intentional numerical change has been made (e.g.
a coefficient update) and the diff has been reviewed.

``tests/test_golden_refs.py`` locks the output to these files in CI, so
if you run the generator and the test fails, that is the system doing
its job — it is asking you to come here and decide whether the drift
was intentional.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Keep in sync with tests/test_golden_refs.py::MATRIX.
MATRIX = [
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


def main():
    for dram_type, two_channel, periods, ref_name in MATRIX:
        print("refreshing %s" % ref_name)
        subprocess.run(_python_args(dram_type, two_channel, periods),
                       cwd=ROOT, check=True)
        src = os.path.join(ROOT, "ddr_timing_table.bin")
        dst = os.path.join(ROOT, ref_name)
        shutil.copyfile(src, dst)
    print("done.")


if __name__ == "__main__":
    main()
