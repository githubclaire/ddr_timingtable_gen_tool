"""UI input -> binary -> load -> compare round-trip coverage.

This is the contract test for the web form.  It parses every control in
templates/gui.html, drives the same parameter dict the browser would submit,
generates a 4 KiB image, loads it through gui.analyze_binary_file(), and
compares every recoverable input against the parsed value.

Fields that cannot be recovered from the image are listed explicitly in
NON_ROUNDTRIP with the reason, so adding a new UI control without deciding
how to verify it fails CI.
"""
import os
import subprocess
import sys
import unittest
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import gui  # noqa: E402
from tests.test_gui_matrix import base_params, _expected_rows  # noqa: E402


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_form = False
        self.controls = []
        self._select = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form' and a.get('id') == 'paramsForm':
            self.in_form = True
            return
        if not self.in_form:
            return
        if tag == 'input' and a.get('type') != 'button':
            self.controls.append(('input', a))
        elif tag == 'select':
            self._select = {'name': a.get('name'), 'options': []}
        elif tag == 'option' and self._select is not None:
            self._select['options'].append(a.get('value'))

    def handle_endtag(self, tag):
        if tag == 'select' and self._select is not None:
            self.controls.append(('select', self._select))
            self._select = None
        elif tag == 'form':
            self.in_form = False


def form_controls():
    p = FormParser()
    with open(os.path.join(ROOT, 'templates', 'gui.html')) as f:
        p.feed(f.read())
    out = {}
    for kind, attrs in p.controls:
        name = attrs.get('name')
        if not name:
            continue
        out.setdefault(name, []).append((kind, attrs))
    return out


# GUI control -> orbit_config field.  Values are compared exactly.
EXACT_ORBIT = {
    'orbit-config-density': 'density',
    'orbit-num-rank': 'num_rank',
    'orbit-rank-interleaving': 'rank_interleaving',
    'orbit-reboot-with-mrw': 'reboot_with_mrw',
    'orbit-rfm-en': 'rfm_en',
    'orbit-dsm-en': 'dsm_en',
    'orbit-ca-odt': 'ca_odt',
    'orbit-phy-odt': 'phy_odt',
    'orbit-otd-ck': 'otd_ck',
    'orbit-otd-cs': 'otd_cs',
    'orbit-otd-ca': 'otd_ca',
    'orbit-zq-bg-mode': 'zq_bg_mode',
    'orbit-initial-training': 'initial_training',
    'command-bus-training': 'command_bus_training',
    'ca-vref-training': 'ca_vref_training',
    'prbs-training': 'prbs_training',
    'reboot-with-training': 'reboot_with_training',
    'phy-vref-trn-mode': 'phy_vref_trn_mode',
    'phy-duty-trn-mode': 'phy_duty_trn_mode',
    'dram-vref-trn-mode': 'dram_vref_trn_mode',
    'dram-duty-trn-mode': 'dram_duty_trn_mode',
    'init-zq-calibration': 'init_zq_calibration',
    'zq-calibration': 'zq_calibration',
    'zq-calibration-period': 'zq_calibration_period',
    'periodic-training': 'periodic_training',
    'periodic-training-period': 'periodic_training_period',
    'temp-sensing': 'temp_sensing',
    'temp-sensing-period': 'temp_sensing_period',
    't-refiab': 't_refiab',
    't-refipb': 't_refipb',
    't-zqcal': 't_zqcal',
    'dynamic-power-down': 'dynamic_power_down',
    'dynamic-power-down-threshold': 'dynamic_power_down_threshold',
    'dynamic-self-refresh': 'dynamic_self_refresh',
    'dynamic-self-refresh-threshold': 'dynamic_self_refresh_threshold',
    'phy-low-power': 'phy_low_power',
    'phy-idle-cnt-th': 'phy_idle_cnt_th',
    'regional-clock-gating': 'regional_clock_gating',
    'dram-clock-gating': 'dram_clock_gating',
    'phy-clock-gating': 'phy_clock_gating',
    'dq-width': 'dq_width',
}

# Recoverable but not a direct struct field.
DERIVED = {
    'two-channel': 'analysis.two_channel',
    'orbit-default-ch': 'orbit.omc_channel (single channel)',
    'orbit-freq-level': 'timingtable_size / dram_t_ck',
    'orbit-lp5-freq-set': 'dram_t_ck (level 0 only)',
    'orbit-byte-mode': 'chip[0].num_row - density base',
    'orbit-mixed': 'chip[1].num_row (rank 2 only)',
    'dfs-lvl-t-ck-0': 'orbit.dfs_lvl_t_ck[0]',
    'dfs-lvl-t-ck-1': 'orbit.dfs_lvl_t_ck[1]',
    'dfs-lvl-t-ck-2': 'orbit.dfs_lvl_t_ck[2]',
    'mrr-byte-lane': 'orbit.mrr_byte_lane (computed from dq-width)',
    'omc-freq-ratio': 'orbit.omc_freq_ratio (fixed by DRAM type)',
    'phy-freq-ratio': 'orbit.phy_freq_ratio (fixed by DRAM type)',
}

# Inputs that only influence the timing table or are presentation-only.
NON_ROUNDTRIP = {
    'phy-name': 'not stored in the binary',
    'speed-bin': 'selects memcfg tables; not stored as a field',
    'dram-tck': 'timing calculation input; orbit stores freq-level dram_t_ck',
    'min-dram-tck': 'timing calculation input; not stored',
    'wire-length': 'timing calculation input; not stored',
    'timing-unit': 'ps/MHz presentation toggle only',
    'wdqs-ctrl-mode': 'affects generated MR values; not exposed as a field',
    'variable-trrd': 'timing calculation input; not stored',
    'txsr-as-1st-ed': 'timing calculation input; not stored',
    'enhanced-nt-odt': 'MR option; not exposed as a field',
    'cpipe-depth': 'timing pipeline input; orbit_config fixes it to 1',
    'wck-pst1-upto': 'SPHY-V9R8 derives PST from the timing table',
    'wck-pst2-upto': 'SPHY-V9R8 derives PST from the timing table',
    'rdqs-pst1-upto': 'SPHY-V9R8 derives PST from the timing table',
    'rdqs-pst2-upto': 'SPHY-V9R8 derives PST from the timing table',
    'dpipe-depth': 'timing pipeline input; orbit_config fixes it to 1',
}

# Timing feature thresholds recoverable from per-entry flags.
TIMING_THRESHOLDS = {
    'write-odt-upto': ('write_odt', '>='),
    'read-dbi-upto': ('read_dbi', '>='),
    'write-dbi-upto': ('write_dbi', '>='),
    'read-lecc-upto': ('read_link_parity', '>'),
    'write-lecc-upto': ('write_link_parity', '>'),
    'rpste-upto': ('rpste', '>='),
    'wpste-upto': ('wpste', '>='),
    'nt-odt-upto': ('nt_odt', '>='),
    'bg-mode-upto': ('bank_mode', 'special'),
}

# LP4-only thresholds (the GUI hides them for LP5).
LP4_TIMING = {
    'rpste-upto': ('rpste', '>='),
    'wpste-upto': ('wpste', '>='),
}

# LP5 WCK/PST/window controls, verified through per-entry fields.
SPECIAL_TIMING = {
    'wck-1to4-upto', 'wck-always-on-from', 'wck-always-on-upto',
    'wck-hf-upto',
}


def set_dfs_for_level(params):
    level = int(params.get('orbit-freq-level', '0'))
    set_name = params.get('orbit-lp5-freq-set', '6000')
    dram_type = params['dram-type']
    table = ([1332, 1428, 1672, 2512] if set_name == '6000'
             else [1256, 1428, 1672, 2512]) if dram_type == 'lpddr5' \
        else [471, 938, 1631, 2500]
    rest = table[level + 1:] + [0] * (3 - len(table[level + 1:]))
    for i in range(3):
        params['dfs-lvl-t-ck-%d' % i] = str(rest[i])


def generate_and_analyze(params):
    if 'dfs-lvl-t-ck-0' not in params:
        set_dfs_for_level(params)
    cmd, _ = gui.build_generate_cmd(params)
    proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise AssertionError(proc.stdout + proc.stderr)
    result = gui.analyze_binary_file(
        os.path.join(ROOT, 'ddr_timing_table.bin'))
    if not result['success']:
        raise AssertionError(result)
    return result['data']


class FormCoverage(unittest.TestCase):
    def test_every_control_is_accounted_for(self):
        controls = form_controls()
        accounted = (set(EXACT_ORBIT) | set(DERIVED) | set(NON_ROUNDTRIP) |
                     set(TIMING_THRESHOLDS) | set(LP4_TIMING) | SPECIAL_TIMING)
        missing = sorted(set(controls) - accounted)
        self.assertEqual(missing, [],
                         "UI controls not covered by round-trip mapping: %r"
                         % missing)

    def test_mapping_targets_exist(self):
        controls = form_controls()
        missing = sorted(set(EXACT_ORBIT) - set(controls))
        self.assertEqual(missing, [],
                         "mapping references missing controls: %r" % missing)


class FullRoundTrip(unittest.TestCase):
    """Modify every recoverable control at once, then verify after load."""

    def test_all_recoverable_fields(self):
        p = base_params('lpddr5', **{
            'two-channel': '1',
            'orbit-byte-mode': '1',
            'orbit-mixed': '1',
            'orbit-num-rank': '2',
            'orbit-config-density': '16',
            'orbit-freq-level': '0',
            'orbit-lp5-freq-set': '6400',
            'orbit-reboot-with-mrw': '0',
            'orbit-rfm-en': '0',
            'orbit-dsm-en': '1',
            'orbit-ca-odt': '0',
            'orbit-phy-odt': '7',
            'orbit-otd-ck': '0', 'orbit-otd-cs': '0', 'orbit-otd-ca': '0',
            'orbit-zq-bg-mode': '0',
            'orbit-initial-training': '0',
            'command-bus-training': '0',
            'ca-vref-training': '0',
            'prbs-training': '0',
            'reboot-with-training': '0',
            'phy-vref-trn-mode': '0', 'phy-duty-trn-mode': '0',
            'dram-vref-trn-mode': '0', 'dram-duty-trn-mode': '0',
            'init-zq-calibration': '0',
            'zq-calibration': '1', 'zq-calibration-period': '24000',
            'periodic-training': '1', 'periodic-training-period': '25000',
            'temp-sensing': '1', 'temp-sensing-period': '16000',
            't-refiab': '1234000', 't-refipb': '345000', 't-zqcal': '900000',
            'dynamic-power-down': '0',
            'dynamic-power-down-threshold': '1024',
            'dynamic-self-refresh': '0',
            'dynamic-self-refresh-threshold': '4096',
            'phy-low-power': '1', 'phy-idle-cnt-th': '32',
            'regional-clock-gating': '0', 'dram-clock-gating': '0',
            'phy-clock-gating': '1',
            'dq-width': '8',
        })
        data = generate_and_analyze(p)
        orbit = data['orbit']
        self.assertTrue(orbit['available'])

        for gui_name, field in EXACT_ORBIT.items():
            expected = p[gui_name]
            actual = orbit[field]
            if isinstance(actual, str):
                actual = int(actual, 16)
            self.assertEqual(actual, int(expected),
                             '%s -> %s mismatch' % (gui_name, field))

        self.assertTrue(data['two_channel'])
        self.assertEqual(orbit['omc_channel'], 2)
        self.assertEqual(orbit['timingtable_size'], 4)
        self.assertEqual(orbit['dram_t_ck'], 1256)  # 6400 set level 0
        self.assertEqual(list(orbit['dfs_lvl_t_ck']), [1428, 1672, 2512])
        self.assertEqual(int(orbit['mrr_byte_lane'], 16), 0xFF)

        # byte mode / mixed inferred from chip geometry
        rows = _expected_rows('lpddr5', 16, 1, 1, 2)
        self.assertEqual([c['num_row'] for c in orbit['chip'][:2]], rows)

        # Periods round-trip through t_ck_display.
        self.assertEqual([e['t_ck_display'] for e in
                          data['timing_entries']['entries']],
                         [int(x) for x in p['periods'].split()])


class IndividualFields(unittest.TestCase):
    """Change one control at a time to catch cross-field masking."""

    CASES = [
        ('lpddr5', {'orbit-config-density': '8'}),
        ('lpddr5', {'orbit-num-rank': '2', 'orbit-rank-interleaving': '0'}),
        ('lpddr5', {'two-channel': '1'}),
        ('lpddr5', {'orbit-default-ch': '1'}),
        ('lpddr5', {'orbit-freq-level': '2'}),
        ('lpddr5', {'orbit-freq-level': '1', 'orbit-lp5-freq-set': '6400'}),
        ('lpddr5', {'orbit-byte-mode': '1'}),
        ('lpddr5', {'orbit-mixed': '1', 'orbit-num-rank': '2'}),
        ('lpddr5', {'orbit-phy-odt': '9'}),
        ('lpddr5', {'orbit-otd-ck': '0'}),
        ('lpddr5', {'orbit-initial-training': '0'}),
        ('lpddr5', {'zq-calibration': '0'}),
        ('lpddr5', {'periodic-training': '0'}),
        ('lpddr5', {'temp-sensing': '0'}),
        ('lpddr5', {'dynamic-power-down': '0'}),
        ('lpddr5', {'dynamic-self-refresh': '0'}),
        ('lpddr5', {'phy-low-power': '1'}),
        ('lpddr5', {'regional-clock-gating': '0'}),
        ('lpddr5', {'dram-clock-gating': '0'}),
        ('lpddr5', {'phy-clock-gating': '1'}),
        ('lpddr5', {'dfs-lvl-t-ck-0': '1400', 'dfs-lvl-t-ck-1': '1800',
                    'dfs-lvl-t-ck-2': '2700'}),
        ('lpddr4', {'orbit-config-density': '4'}),
        ('lpddr4', {'orbit-default-ch': '1'}),
        ('lpddr4', {'orbit-byte-mode': '1'}),
        ('lpddr4', {'orbit-mixed': '1', 'orbit-num-rank': '2'}),
    ]

    def test_cases(self):
        for dram_type, overrides in self.CASES:
            with self.subTest(dram_type=dram_type, overrides=overrides):
                p = base_params(dram_type)
                p.update(overrides)
                data = generate_and_analyze(p)
                orbit = data['orbit']
                self.assertTrue(orbit['available'])

                for gui_name, field in EXACT_ORBIT.items():
                    if gui_name not in p:
                        continue
                    actual = orbit[field]
                    if isinstance(actual, str):
                        actual = int(actual, 16)
                    self.assertEqual(actual, int(p[gui_name]),
                                     '%s -> %s' % (gui_name, field))

                if 'orbit-freq-level' in overrides:
                    level = int(overrides['orbit-freq-level'])
                    self.assertEqual(orbit['timingtable_size'], 4 - level)
                    self.assertEqual(
                        list(orbit['dfs_lvl_t_ck']),
                        [int(p['dfs-lvl-t-ck-%d' % i]) for i in range(3)])

                if 'two-channel' in overrides:
                    self.assertEqual(data['two_channel'], True)
                    self.assertEqual(orbit['omc_channel'], 2)
                elif 'orbit-default-ch' in overrides:
                    self.assertEqual(orbit['omc_channel'],
                                     int(overrides['orbit-default-ch']))


class TimingFlagsRoundTrip(unittest.TestCase):
    """Timing '*-upto' inputs must be recoverable from per-entry flags."""

    def _check_flags(self, data, thresholds, mapping):
        entries = data['timing_entries']['entries']
        for entry in entries:
            tck = entry['t_ck_display']
            read_lecc_on = False
            if 'read-lecc-upto' in thresholds:
                read_lecc_on = thresholds['read-lecc-upto'] > tck
            for gui_name, (field, op) in mapping.items():
                limit = thresholds[gui_name]
                if op == '>=':
                    expected = limit >= tck
                elif op == '>':
                    expected = limit > tck
                else:  # bank_mode encodes !bg_mode (0 = BG, 2 = 16B)
                    expected = 0 if limit >= tck else 2
                if gui_name == 'read-dbi-upto':
                    expected = expected and not read_lecc_on
                actual = entry.get(field)
                if op != 'special':
                    actual = 1 if actual else 0
                self.assertEqual(actual, expected,
                                 '%s at tWCK=%d' % (gui_name, tck))

    def test_lp5_threshold_flags(self):
        thresholds = {
            'write-odt-upto': 418,
            'read-dbi-upto': 556,
            'write-dbi-upto': 314,
            'write-lecc-upto': 417,   # strict '>'
            'read-lecc-upto': 555,    # strict '>'
            'nt-odt-upto': 418,
            'bg-mode-upto': 556,
        }
        p = base_params('lpddr5')
        p.update({k: str(v) for k, v in thresholds.items()})
        data = generate_and_analyze(p)
        self._check_flags(data, thresholds, {
            k: v for k, v in TIMING_THRESHOLDS.items()
            if k not in LP4_TIMING and k in thresholds
        })

    def test_lp4_threshold_flags(self):
        thresholds = {
            'write-odt-upto': 938,
            'read-dbi-upto': 1631,
            'write-dbi-upto': 938,
            'rpste-upto': 1631,
            'wpste-upto': 938,
        }
        p = base_params('lpddr4')
        p.update({k: str(v) for k, v in thresholds.items()})
        data = generate_and_analyze(p)
        mapping = {k: v for k, v in {**TIMING_THRESHOLDS, **LP4_TIMING}.items()
                   if k in thresholds}
        self._check_flags(data, thresholds, mapping)

    def test_lp5_wck_flags(self):
        thresholds = {
            'wck-1to4-upto': 625,
            'wck-hf-upto': 938,
            'wck-always-on-from': 0,
            'wck-always-on-upto': 3000,
        }
        p = base_params('lpddr5')
        p['periods'] = '625 938 2500'
        p.update({k: str(v) for k, v in thresholds.items()})
        data = generate_and_analyze(p)
        for entry in data['timing_entries']['entries']:
            tck = entry['t_ck_display']
            expected_ratio = 4 if thresholds['wck-1to4-upto'] >= tck else 2
            self.assertEqual(entry['wck_ratio'], expected_ratio)
            self.assertEqual(entry['wck_fm'],
                             1 if thresholds['wck-hf-upto'] >= tck else 0)
            expected_on = (thresholds['wck-always-on-from'] <= tck
                           <= thresholds['wck-always-on-upto'])
            self.assertEqual(bool(entry['wck_on']), expected_on)


if __name__ == '__main__':
    unittest.main(verbosity=2)
