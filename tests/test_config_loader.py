"""F4 — tests for ``config_loader`` and the ``--config`` flag."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

import config_loader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ConfigLoaderUnit(unittest.TestCase):
    def test_load_json(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"dram_type": "lpddr4", "dq_width": 16}, f)
            path = f.name
        try:
            d = config_loader.load(path)
            self.assertEqual(d["dram_type"], "lpddr4")
            self.assertEqual(d["dq_width"], 16)
        finally:
            os.unlink(path)

    def test_load_missing_raises(self):
        with self.assertRaises(IOError):
            config_loader.load("/nonexistent/path/config.json")

    def test_load_non_mapping_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump([1, 2, 3], f)
            path = f.name
        try:
            with self.assertRaises(ValueError):
                config_loader.load(path)
        finally:
            os.unlink(path)


class ConfigLoaderCli(unittest.TestCase):
    """End-to-end: --config path fills in almost all args, CLI supplies
    only the positional periods list."""

    def test_config_drives_generator(self):
        cfg = {
            "dram_type": "lpddr4",
            "phy_name": "sphy-v9r8",
            "speed_bin": "4266",
            "dq_width": 16,
            "orbit_config_density": 16,
            "wire_length": 10,
            "read_dbi_upto": 10000,
            "write_dbi_upto": 10000,
            "write_lecc_upto": 625,
            "write_odt_upto": 10000,
            "cpipe_depth": 1,
            "dpipe_depth": 1,
            "omc_freq_ratio": 2,
            "phy_freq_ratio": 2,
            "orbit_config_use_python": True,
            "bogus_unknown_field": "ignored",
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(cfg, f)
            path = f.name
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(ROOT, "gen_timing_params"),
                 "--config", path, "938", "1631", "2500"],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("ignoring unknown keys", r.stdout)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
