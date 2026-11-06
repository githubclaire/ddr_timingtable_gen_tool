"""Compare the SCP build timing-table command against the GUI output.

The SCP build (``build/scp.mk``) invokes ``gen_timing_params`` with a fixed
argument set per DDR type and ``DDR_FREQ_LEVEL``.  This test:

  1. parses those argument sets directly from ``build/scp.mk`` (so it follows
     future build changes automatically),
  2. runs the same build-style CLI (C orbit-config path) to produce a 4 KiB
     image,
  3. runs the GUI's ``build_generate_cmd()`` with the equivalent form values,
  4. compares the two images byte-for-byte.

If the SCP build tree is not present, the test is skipped.
"""
import os
import re
import shlex
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import gui  # noqa: E402
from tests.test_gui_matrix import base_params  # noqa: E402
from tests.test_ui_roundtrip import set_dfs_for_level  # noqa: E402

SCP_MK = '/home/se/git/arise2/build/scp.mk'
BIN = os.path.join(ROOT, 'ddr_timing_table.bin')


def parse_scp_timing_commands(path):
    """Return {dram_type: {'args': [...], 'freqs': {level: [...]}}}."""
    with open(path) as f:
        text = f.read()

    freq_tables = {'lpddr5': {}, 'lpddr4': {}}
    level = None
    for line in text.splitlines():
        m = re.match(r'\s*(?:else\s+)?ifeq\s+\(\$\(DDR_FREQ_LEVEL\),\s*(\d+)\)', line)
        if m:
            level = int(m.group(1))
            continue
        m = re.match(r'\s*TIMING_FREQS_DDR5\s*:=\s*(.+)', line)
        if m and level is not None:
            freq_tables['lpddr5'][level] = m.group(1).split()
            continue
        m = re.match(r'\s*TIMING_FREQS_DDR4\s*:=\s*(.+)', line)
        if m and level is not None:
            freq_tables['lpddr4'][level] = m.group(1).split()

    def extract(var):
        lines = text.splitlines()
        out = []
        collecting = False
        for line in lines:
            if not collecting:
                if re.match(r'\s*%s\s*:=' % re.escape(var), line):
                    collecting = True
                    out.append(line.split(':=', 1)[1].strip())
            else:
                out.append(line.strip())
            if collecting and not line.rstrip().endswith('\\'):
                break
        return ' '.join(x.rstrip('\\').strip() for x in out)

    result = {}
    for dt, var, freq_var in (
        ('lpddr5', 'TIMING_TABLE_GEN_ARGS_DDR5', 'TIMING_FREQS_DDR5'),
        ('lpddr4', 'TIMING_TABLE_GEN_ARGS_DDR4', 'TIMING_FREQS_DDR4'),
    ):
        raw = extract(var)
        if not raw:
            continue
        raw = raw.replace('$(%s)' % freq_var, '__FREQS__')
        base = shlex.split(raw)
        result[dt] = {'base_args': base, 'freqs': freq_tables[dt]}
    return result


def _args_to_gui_params(dt, args, freqs, level, two_channel, default_ch):
    p = base_params(dt)
    p['periods'] = ' '.join(freqs)
    p['orbit-freq-level'] = str(level)
    p['orbit-default-ch'] = str(default_ch)
    p['orbit-config-density'] = '16'
    if two_channel:
        p['two-channel'] = '1'
    p['orbit-lp5-freq-set'] = '6000'
    p['orbit-byte-mode'] = '0'
    p['orbit-mixed'] = '0'
    p['orbit-num-rank'] = '1'
    p['orbit-rank-interleaving'] = '1'
    # CLI defaults for options that scp.mk does not pass.  The GUI has its
    # own form defaults for these, so set them explicitly to the generator
    # defaults before applying the build flags.
    p['min-dram-tck'] = '314'
    p['rpste-upto'] = '0'
    p['wpste-upto'] = '0'
    p['read-lecc-upto'] = '0'
    p['write-lecc-upto'] = '0'
    p['nt-odt-upto'] = '0'
    p['wck-hf-upto'] = '624'

    # Copy every option from scp.mk into the equivalent form field.
    i = 0
    while i < len(args):
        tok = args[i]
        if tok == '__FREQS__':
            i += 1
            continue
        if tok.startswith('--'):
            name = tok[2:]
            if (i + 1 < len(args) and args[i + 1] != '__FREQS__'
                    and not args[i + 1].startswith('--')):
                value = args[i + 1]
                i += 2
            else:
                value = '1'
                i += 1
            p[name] = value
        else:
            i += 1

    set_dfs_for_level(p)
    return p


class BuildVsUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(SCP_MK):
            raise unittest.SkipTest('SCP build tree not present: %s' % SCP_MK)
        cls.commands = parse_scp_timing_commands(SCP_MK)
        if not cls.commands:
            raise unittest.SkipTest('no timing-table command found in scp.mk')

    def _run_build_style(self, dt, level, two_channel, default_ch):
        cmd_info = self.commands[dt]
        freqs = cmd_info['freqs'][level]
        args = []
        for tok in cmd_info['base_args']:
            if tok == '__FREQS__':
                args.extend(freqs)
            else:
                args.append(tok)
        args += ['--orbit-config-density', '16',
                 '--orbit-freq-level', str(level),
                 '--orbit-default-ch', str(default_ch),
                 '--orbit-lp5-freq-set', '6000']
        if two_channel:
            args.append('--two-channel')
        # Build-style: no --orbit-config-use-python, so the C path runs.
        cmd = [sys.executable, os.path.join(ROOT, 'gen_timing_params')] + args
        proc = subprocess.run(
            cmd, cwd=ROOT, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        with open(BIN, 'rb') as f:
            return f.read()

    def _run_ui_style(self, dt, level, two_channel, default_ch):
        params = _args_to_gui_params(
            dt, self.commands[dt]['base_args'],
            self.commands[dt]['freqs'][level], level,
            two_channel, default_ch)
        cmd, _ = gui.build_generate_cmd(params)
        proc = subprocess.run(
            cmd, cwd=ROOT, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        with open(BIN, 'rb') as f:
            return f.read()

    def test_scp_commands_match_ui(self):
        for dt in ('lpddr5', 'lpddr4'):
            if dt not in self.commands:
                continue
            for level in sorted(self.commands[dt]['freqs']):
                for two_channel in (False, True):
                    default_ch = 0
                    with self.subTest(dt=dt, level=level,
                                      two_channel=two_channel):
                        build_bin = self._run_build_style(
                            dt, level, two_channel, default_ch)
                        ui_bin = self._run_ui_style(
                            dt, level, two_channel, default_ch)
                        self.assertEqual(len(build_bin), 0x1000)
                        self.assertEqual(len(ui_bin), 0x1000)
                        self.assertEqual(
                            build_bin, ui_bin,
                            'SCP build command and GUI differ for %s level=%d '
                            'two_channel=%s' % (dt, level, two_channel))


if __name__ == '__main__':
    unittest.main(verbosity=2)
