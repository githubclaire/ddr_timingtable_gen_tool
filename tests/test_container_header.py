"""F3/F6 — tests for ``container_header`` and the ``--emit-container``
end-to-end path."""
import os
import subprocess
import sys
import unittest

import container_header

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTAINER = os.path.join(ROOT, "ddr_timing_table.container")


class ContainerHeaderUnit(unittest.TestCase):
    def test_roundtrip(self):
        hdr = container_header.build_header(
            "lpddr5", True, 16, [3184, 2392, 1798], payload_size=7872,
        )
        self.assertEqual(len(hdr), container_header.HEADER_SIZE)
        parsed = container_header.parse_header(hdr)
        self.assertEqual(parsed["dram_type"], "lpddr5")
        self.assertTrue(parsed["two_channel"])
        self.assertEqual(parsed["density_gb"], 16)
        self.assertEqual(parsed["num_freq_points"], 3)
        self.assertEqual(parsed["freq_points"], [3184, 2392, 1798])
        self.assertEqual(parsed["payload_offset"], container_header.HEADER_SIZE)
        self.assertEqual(parsed["payload_size"], 7872)

    def test_bad_magic_raises(self):
        buf = bytearray(container_header.HEADER_SIZE)
        buf[0:4] = b"XXXX"
        with self.assertRaises(ValueError):
            container_header.parse_header(bytes(buf))

    def test_truncated_raises(self):
        with self.assertRaises(ValueError):
            container_header.parse_header(b"DDRT")


class ContainerEndToEnd(unittest.TestCase):
    def setUp(self):
        if os.path.exists(CONTAINER):
            os.remove(CONTAINER)

    def test_emit_container_lp4_single(self):
        subprocess.run(
            [sys.executable, os.path.join(ROOT, "gen_timing_params"),
             "--dram-type", "lpddr4", "--phy-name", "sphy-v9r8",
             "--speed-bin", "4266", "--dq-width", "16",
             "--orbit-config-density", "16", "--wire-length", "10",
             "--read-dbi-upto", "10000", "--write-dbi-upto", "10000",
             "--write-lecc-upto", "625", "--write-odt-upto", "10000",
             "--cpipe-depth", "1", "--dpipe-depth", "1",
             "--omc-freq-ratio", "2", "--phy-freq-ratio", "2",
             "--emit-container", "--orbit-config-use-python",
             "938", "1631", "2500"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=True, text=True,
        )
        self.assertTrue(os.path.exists(CONTAINER))
        with open(CONTAINER, "rb") as f:
            data = f.read()
        parsed = container_header.parse_header(data)
        self.assertEqual(parsed["dram_type"], "lpddr4")
        self.assertFalse(parsed["two_channel"])
        self.assertEqual(parsed["density_gb"], 16)
        self.assertEqual(parsed["num_freq_points"], 3)
        # payload_size + header should equal file size
        self.assertEqual(parsed["payload_offset"] + parsed["payload_size"],
                         len(data))
        # The bare .bin is untouched and has the same content as the
        # container's payload.
        with open(os.path.join(ROOT, "ddr_timing_table.bin"), "rb") as f:
            bare = f.read()
        self.assertEqual(data[parsed["payload_offset"]:], bare)


if __name__ == "__main__":
    unittest.main(verbosity=2)
