#!/usr/bin/env python3
"""
P0 regression suite.

Locks in the Phase 0 fixes from plans/codebase_review_and_refactor_plan.md:
- P0-1: mr_rtp is no longer aliased to mr_wr
- P0-2: wck_always_on uses the [from, upto] inclusive window
- P0-3: self.args (not bare args) references
- P0-4: byte_mode / mixed threaded into ddr_config.h
- P0-5: Python orbit_config struct is no longer file-offset-patched and
        matches the C gen_ddr_config output byte-for-byte
- P0-8: LPDDR5 dead assignment to p_t_wtr removed
"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))


def run(*cmd, env=None, cwd=ROOT, check=True):
    result = subprocess.run(
        list(cmd),
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            "command %s failed (rc=%d)\nstdout:\n%s\nstderr:\n%s"
            % (cmd, result.returncode, result.stdout, result.stderr)
        )
    return result


def lp5_python(density=16):
    """Invoke gen_timing_params for LP5 single via the Python orbit path."""
    run(
        sys.executable, "gen_timing_params",
        "--dram-type", "lpddr5",
        "--phy-name", "sphy-v9r8",
        "--speed-bin", "6400",
        "--dq-width", "16",
        "--orbit-config-density", str(density),
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
        "--orbit-config-use-python", "314", "418", "556", "2500",
    )


def lp4_python(density=16):
    run(
        sys.executable, "gen_timing_params",
        "--dram-type", "lpddr4",
        "--phy-name", "sphy-v9r8",
        "--speed-bin", "4266",
        "--dq-width", "16",
        "--orbit-config-density", str(density),
        "--wire-length", "10",
        "--read-dbi-upto", "10000",
        "--write-dbi-upto", "10000",
        "--write-lecc-upto", "625",
        "--write-odt-upto", "10000",
        "--cpipe-depth", "1",
        "--dpipe-depth", "1",
        "--omc-freq-ratio", "2",
        "--phy-freq-ratio", "2",
        "--orbit-config-use-python", "468", "625", "938", "2500",
    )


class P01_MrRtp(unittest.TestCase):
    """P0-1: mr_rtp must come from self.mr_rtp, not self.mr_wr."""

    def test_mr_rtp_not_aliased(self):
        with open(os.path.join(ROOT, "gen_timing_params")) as f:
            src = f.read()
        # The bug was `mr_rtp=self.mr_wr` at the entry construction site.
        self.assertNotIn("mr_rtp=self.mr_wr", src,
                         "mr_rtp must not alias mr_wr (P0-1)")
        self.assertIn("mr_rtp=self.mr_rtp", src,
                      "mr_rtp must be sourced from self.mr_rtp (P0-1)")


class P02_WckAlwaysOn(unittest.TestCase):
    """P0-2: wck_always_on uses the (from <= t_ck <= upto) window."""

    def test_window_semantics(self):
        with open(os.path.join(ROOT, "gen_timing_params")) as f:
            src = f.read()
        self.assertIn(
            "self.wck_always_on = (self.args.wck_always_on_from <= t_ck <= self.args.wck_always_on_upto)",
            src,
            "wck_always_on must use inclusive window (P0-2)",
        )


class P03_SelfArgs(unittest.TestCase):
    """P0-3: gen_timing_params must not reference bare `args.*` inside methods."""

    def test_known_bare_args_bugs_fixed(self):
        # The P0-3 plan enumerates specific lines where bare `args.X` was
        # referenced inside ``TimingTableGenerator`` methods and would raise
        # NameError at runtime. Lock in those exact fixes.
        import re
        with open(os.path.join(ROOT, "gen_timing_params")) as f:
            src = f.read()
        # Use negative-lookbehind so `self.args.X` does not match.
        forbidden_patterns = [
            r"(?<!self\.)args\.rpste_upto",
            r"(?<!self\.)args\.wpste_upto",
            r"(?<!self\.)args\.dpipe_depth\s*-\s*(?<!self\.)args\.cpipe_depth",
            r"if\s+(?<!self\.)args\.meso_synchronizer",
            r"open\(\s*args\.output",
        ]
        for pat in forbidden_patterns:
            # Only count matches inside class-method bodies (indent >= 8).
            bad = []
            for i, line in enumerate(src.splitlines(), 1):
                if re.search(pat, line):
                    indent = len(line) - len(line.lstrip())
                    if indent >= 8:
                        bad.append((i, line))
            self.assertEqual(
                bad, [],
                "P0-3: pattern %r still present in class methods:\n%s" % (
                    pat, "\n".join("%d: %s" % b for b in bad),
                ),
            )
        self.assertIn("self.args.rpste_upto", src)
        self.assertIn("self.args.wpste_upto", src)
        self.assertIn("self.args.meso_synchronizer", src)


class P04_ByteModeMixed(unittest.TestCase):
    """P0-4: ddr_config.h threads ORBIT_BYTE_MODE / ORBIT_MIXED into orbit_update_chips."""

    def test_defines_present(self):
        with open(os.path.join(ROOT, "ddr_config.h")) as f:
            src = f.read()
        self.assertIn("ORBIT_BYTE_MODE", src, "ddr_config.h missing ORBIT_BYTE_MODE")
        self.assertIn("ORBIT_MIXED", src, "ddr_config.h missing ORBIT_MIXED")
        self.assertIn("orbit_update_chips(omc_config, ORBIT_BYTE_MODE, ORBIT_MIXED)", src)


class P05_StructCorruption(unittest.TestCase):
    """P0-5: Python struct must match C struct and not contain file-offset patching."""

    def test_no_file_offset_patching(self):
        with open(os.path.join(ROOT, "ddr_config_init.py")) as f:
            src = f.read()
        # The removed patch wrote dual-channel offsets to a single-channel file.
        self.assertNotIn("f.seek(0x8C4", src)
        self.assertNotIn("struct.pack_into", src)

    def test_python_matches_c_lp5_single(self):
        # Run Python path for LP5 single
        lp5_python(density=16)
        py_bin = os.path.join(ROOT, "/tmp/test_regression_lp5_py.bin")
        with open(os.path.join(ROOT, "ddr_timing_table.bin"), "rb") as src:
            data = src.read()
        with open(py_bin, "wb") as dst:
            dst.write(data)
        # Zero out orbit_config region (from 0x800 to end) for a clean C rebuild
        seeded = bytearray(data)
        for i in range(0x800, len(seeded)):
            seeded[i] = 0
        with open(os.path.join(ROOT, "ddr_timing_table.bin"), "wb") as f:
            f.write(bytes(seeded))
        # Build and run C reference
        exec_path = os.path.join(ROOT, "ddr_config_bin_exec")
        if os.path.exists(exec_path):
            os.remove(exec_path)
        run("gcc", "-std=c99", "-D", "DDR_TYPE=3", "-D", "DDR_TWO_CHANNEL=0",
            "-D", "ORBIT_DENSITY=16", "-I", ".", "ddr_config_bin.c",
            "-o", "ddr_config_bin_exec")
        run("./ddr_config_bin_exec")
        with open(os.path.join(ROOT, "ddr_timing_table.bin"), "rb") as f:
            c_data = f.read()
        with open(py_bin, "rb") as f:
            py_data = f.read()
        self.assertEqual(len(c_data), len(py_data),
                         "LP5 single size mismatch (P0-5)")
        self.assertEqual(c_data, py_data,
                         "LP5 single Python/C mismatch (P0-5)")

    def test_python_matches_c_lp4_single(self):
        lp4_python(density=16)
        with open(os.path.join(ROOT, "ddr_timing_table.bin"), "rb") as f:
            py_data = f.read()
        seeded = bytearray(py_data)
        for i in range(0x800, len(seeded)):
            seeded[i] = 0
        with open(os.path.join(ROOT, "ddr_timing_table.bin"), "wb") as f:
            f.write(bytes(seeded))
        exec_path = os.path.join(ROOT, "ddr_config_bin_exec")
        if os.path.exists(exec_path):
            os.remove(exec_path)
        run("gcc", "-std=c99", "-D", "DDR_TYPE=2", "-D", "DDR_TWO_CHANNEL=0",
            "-D", "ORBIT_DENSITY=16", "-I", ".", "ddr_config_bin.c",
            "-o", "ddr_config_bin_exec")
        run("./ddr_config_bin_exec")
        with open(os.path.join(ROOT, "ddr_timing_table.bin"), "rb") as f:
            c_data = f.read()
        self.assertEqual(c_data, py_data,
                         "LP4 single Python/C mismatch (P0-5)")


class P08_DeadAssignment(unittest.TestCase):
    """P0-8: LPDDR5 dead assignment to p_t_wtr removed."""

    def test_dead_assign_gone(self):
        with open(os.path.join(ROOT, "lpddr5_config.py")) as f:
            src = f.read()
        # Count occurrences — previously one was dead (immediately overwritten).
        self.assertLessEqual(
            src.count("self.ref.p_t_wtr = Timing(10, 8, 0)"),
            0,
            "dead p_t_wtr assignment must be removed (P0-8)",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
