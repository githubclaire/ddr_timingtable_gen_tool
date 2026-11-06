"""Cross-check GUI timing-table parsing against the C timing_param layout.

The reference parser in ``tools/compare_timing_parse.py`` is independent of
``gui.parse_timing_entries``: it reads the binary through a ctypes struct with
the exact field order/size from arise2_omc.h, then every field is compared.
"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import compare_timing_parse as ref  # noqa: E402


def _generate(dram_type, two_channel, density, periods):
    args = [sys.executable, os.path.join(ROOT, 'gen_timing_params'),
            '--dram-type', dram_type,
            '--phy-name', 'sphy-v9r8',
            '--speed-bin', '4266' if dram_type == 'lpddr4' else '6400',
            '--dq-width', '16',
            '--orbit-config-density', str(density),
            '--wire-length', '10',
            '--read-dbi-upto', '10000',
            '--write-dbi-upto', '10000',
            '--write-lecc-upto', '625',
            '--write-odt-upto', '10000',
            '--cpipe-depth', '1',
            '--dpipe-depth', '1',
            '--omc-freq-ratio', '1' if dram_type == 'lpddr5' else '2',
            '--phy-freq-ratio', '1' if dram_type == 'lpddr5' else '2']
    if dram_type == 'lpddr5':
        args += ['--wck-1to4-upto', '625',
                 '--wck-always-on-from', '0',
                 '--wck-always-on-upto', '10000']
    if two_channel:
        args.append('--two-channel')
    args.append('--orbit-config-use-python')
    args.extend(periods)
    subprocess.run(args, cwd=ROOT, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with open(os.path.join(ROOT, 'ddr_timing_table.bin'), 'rb') as f:
        return f.read()


class TimingStructLayout(unittest.TestCase):
    def test_entry_sizes(self):
        self.assertEqual(ref.entry_size('lpddr4'), 0x128)
        self.assertEqual(ref.entry_size('lpddr5'), 0x15C)

    def test_ctypes_offsets(self):
        for dram_type, n in (('lpddr4', 7), ('lpddr5', 10)):
            cls = ref.make_timing_struct(dram_type)
            self.assertEqual(cls.freq.offset, 0x00)
            self.assertEqual(cls.t_ck.offset, 0x04)
            self.assertEqual(cls.timing_zqcal.offset, 0x08)
            self.assertEqual(cls.timing_param.offset, 0x0C)
            self.assertEqual(cls.timing_param_derate.offset, 0x60)
            self.assertEqual(cls.dfi_timing_param.offset, 0x68)
            self.assertEqual(cls.t_rfcab.offset, 0x88)
            self.assertEqual(cls.t_rfcpb.offset, 0x88 + 2 * n)
            self.assertEqual(cls.wck_ratio.offset, 0x88 + 18 * n)
            self.assertEqual(cls.rl.offset, 0x88 + 18 * n + 10)


class TimingParseMatrix(unittest.TestCase):
    def _check(self, dram_type, two_channel, density, periods):
        data = _generate(dram_type, two_channel, density, periods)
        self.assertEqual(len(data), 0x1000,
                         "generated image must be padded to 4 KiB")
        problems = ref.compare(data, dram_type, density)
        self.assertEqual(problems, [],
                         "%s %s density=%d:\n%s" % (
                             dram_type, 'dual' if two_channel else 'single',
                             density, '\n'.join(problems)))

    def test_lp4_single_d16(self):
        self._check('lpddr4', False, 16, ['938', '1631', '2500'])

    def test_lp4_dual_d8(self):
        self._check('lpddr4', True, 8, ['938', '1631', '2500'])

    def test_lp5_single_d16(self):
        self._check('lpddr5', False, 16, ['314', '418', '556', '2500'])

    def test_lp5_dual_d32(self):
        self._check('lpddr5', True, 32, ['314', '418', '556', '2500'])


class OriginalRepoImages(unittest.TestCase):
    """If the SCP build output is present, verify its 4 KiB images too."""

    def _check(self, path, dram_type):
        if not os.path.exists(path):
            self.skipTest("original image not present: %s" % path)
        with open(path, 'rb') as f:
            data = f.read()
        self.assertEqual(len(data), 0x1000)
        problems = ref.compare(data, dram_type, 16)
        self.assertEqual(problems, [], '\n'.join(problems))

    def test_lp4_4k_image(self):
        self._check('/home/se/git/arise2/out/Arise2-chip/bin/'
                    'ddr_timing_table_lpddr4.bin', 'lpddr4')

    def test_lp5_4k_image(self):
        self._check('/home/se/git/arise2/out/Arise2-chip/bin/'
                    'ddr_timing_table_lpddr5.bin', 'lpddr5')


if __name__ == '__main__':
    unittest.main(verbosity=2)
