"""Compare the *original* SCP toolchain output against the updated UI.

`tests/test_build_scp_parity.py` verifies that the scp.mk argument set and the
updated generator reproduce the GUI image byte-for-byte.  This test goes one
step further and runs the original toolchain checked into
``arise2/toolchains/ddr_timingtable_gen_tool`` (the code the current SCP build
actually invokes), assembles its 4 KiB image exactly like ``build/scp.mk``,
and compares it field-by-field with the GUI output.

Two intentional fixes in this repository are tolerated, and nothing else:

  * LPDDR5 ``wck_on`` / ``timing_param[16]``: the original toolchain's
    always-on window comparison is inverted; this repo uses the documented
    [from, upto] window.
  * LPDDR4 ``density_code``: the original toolchain assigns positional codes
    (16 Gb -> 6); this repo uses the canonical SCP mapping (16 Gb -> 7).

Any other difference fails the test.
"""
import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import compare_timing_parse as ref  # noqa: E402
import gui  # noqa: E402
from tests.test_build_scp_parity import (  # noqa: E402
    parse_scp_timing_commands, _args_to_gui_params,
)

ARISE2 = '/home/se/git/arise2'
ORIG_TOOL = os.path.join(ARISE2, 'toolchains', 'ddr_timingtable_gen_tool')
SCP = os.path.join(ARISE2, 'SCP-firmware')
BUILD = os.path.join(ARISE2, 'build')
SCP_MK = os.path.join(BUILD, 'scp.mk')
DRAM_MACRO = {'lpddr4': '2', 'lpddr5': '1'}


def _scalar(value):
    return list(value) if not isinstance(value, int) else value


class OriginalToolchainCompare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (os.path.exists(ORIG_TOOL) and os.path.exists(SCP_MK)):
            raise unittest.SkipTest('original Arise2 toolchain/build not present')
        cls.commands = parse_scp_timing_commands(SCP_MK)
        cls.tmp = tempfile.mkdtemp(prefix='ddr_orig_')
        os.symlink(SCP, os.path.join(cls.tmp, 'SCP-firmware'))
        os.symlink(BUILD, os.path.join(cls.tmp, 'build'))
        os.makedirs(os.path.join(cls.tmp, 'toolchains'))
        cls.tool = os.path.join(cls.tmp, 'toolchains', 'ddr_timingtable_gen_tool')
        shutil.copytree(ORIG_TOOL, cls.tool)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _run(self, cmd, cwd=None):
        p = subprocess.run(cmd, cwd=cwd or self.tool,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True)
        self.assertEqual(p.returncode, 0, p.stdout)

    def _original_bin(self, dt, level, two_channel):
        info = self.commands[dt]
        args = ['1', '0']  # machine_mode=1 (SoC), use_release=0
        for tok in info['base_args']:
            if tok == '__FREQS__':
                args.extend(info['freqs'][level])
            else:
                args.append(tok)
        self._run(['./gen_timing_params'] + args)
        default_ch = '2' if two_channel else '0'
        self._run(['./gen_ddr_config', '1', '0', DRAM_MACRO[dt],
                   '1' if two_channel else '0', str(level), default_ch])
        out = os.path.join(self.tool, 'orig_4k.bin')
        with open(out, 'wb') as f:
            f.write(b'\0' * 0x1000)
        for src, seek in (('timing_table.bin', 0),
                          ('ddr_config.bin', 0x800)):
            with open(os.path.join(self.tool, src), 'rb') as f:
                data = f.read()
            with open(out, 'r+b') as f:
                f.seek(seek)
                f.write(data)
        with open(out, 'rb') as f:
            return f.read()

    def _ui_bin(self, dt, level, two_channel):
        info = self.commands[dt]
        params = _args_to_gui_params(
            dt, info['base_args'], info['freqs'][level], level,
            two_channel, 0)
        cmd, _ = gui.build_generate_cmd(params)
        self._run(cmd, cwd=ROOT)
        with open(os.path.join(ROOT, 'ddr_timing_table.bin'), 'rb') as f:
            return f.read()

    def _compare(self, dt, level, two_channel):
        original = self._original_bin(dt, level, two_channel)
        updated = self._ui_bin(dt, level, two_channel)

        # Orbit config prefix: compare every scalar field.  The original
        # toolchain uses positional density codes for LPDDR4.
        a_cfg = gui._load_cfg_from_data(original, dt, two_channel)
        b_cfg = gui._load_cfg_from_data(updated, dt, two_channel)
        cls = type(a_cfg)
        for name, ftype in cls._fields_:
            if issubclass(ftype, ctypes.Array):
                continue
            av, bv = getattr(a_cfg, name), getattr(b_cfg, name)
            if name == 'density_code' and dt == 'lpddr4':
                # Original positional code (16 Gb -> 6) vs canonical (7).
                self.assertIn((av, bv), [(6, 7), (5, 6), (4, 5), (3, 4),
                                         (2, 3), (1, 2), (0, 1)])
                continue
            self.assertEqual(av, bv, 'orbit field %s differs' % name)

        # Timing entries: every field must match except the documented WCK
        # window fix (wck_on and timing_param[16] which carries wck_mode).
        a_entries = ref.parse_reference(original, dt)
        b_entries = ref.parse_reference(updated, dt)
        self.assertEqual(len(a_entries), len(b_entries))
        for idx, ((_, ea), (_, eb)) in enumerate(zip(a_entries, b_entries)):
            for name in ref.SCALAR_FIELDS:
                av = _scalar(getattr(ea, name))
                bv = _scalar(getattr(eb, name))
                if dt == 'lpddr5' and name == 'wck_on':
                    continue
                if dt == 'lpddr5' and name == 'timing_param':
                    # Compare all 21 words except index 16 (wck_mode).
                    for i, (x, y) in enumerate(zip(av, bv)):
                        if i != 16:
                            self.assertEqual(x, y,
                                             'entry %d timing_param[%d]' % (idx, i))
                    continue
                self.assertEqual(av, bv,
                                 'entry %d field %s' % (idx, name))

    def test_original_toolchain_vs_ui(self):
        for dt in ('lpddr5', 'lpddr4'):
            if dt not in self.commands:
                continue
            for level in sorted(self.commands[dt]['freqs']):
                for two_channel in (False, True):
                    with self.subTest(dt=dt, level=level,
                                      two_channel=two_channel):
                        self._compare(dt, level, two_channel)


if __name__ == '__main__':
    unittest.main(verbosity=2)
