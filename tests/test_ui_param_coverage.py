"""Exhaustive UI-parameter coverage.

Every control in templates/gui.html must have at least one executable case
here.  The case either:
  * changes the value, generates a 4 KiB image, loads it, and compares the
    recovered value (orbit field / derived field / per-entry timing flag), or
  * is explicitly classified as calculation-only/presentation-only and is
    still executed to prove the generator accepts it.

Adding a new form control without a case fails the final completeness check.
"""
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tests.test_gui_matrix import base_params  # noqa: E402
from tests.test_ui_roundtrip import (  # noqa: E402
    EXACT_ORBIT, TIMING_THRESHOLDS, LP4_TIMING, form_controls,
    generate_and_analyze, set_dfs_for_level,
)

# Alternate value per control.  Only entries that are actually exercised need
# to be here; missing ones are reported by the completeness check.
ALT = {
    'phy-name': 'sphy-v9r8',
    'dq-width': '8',
    'speed-bin': '5600',
    'dram-tck': '1000',
    'min-dram-tck': '400',
    'wire-length': '20',
    'cpipe-depth': '2',
    'dpipe-depth': '3',
    'omc-freq-ratio': '2',
    'phy-freq-ratio': '2',
    'write-odt-upto': '800',
    'read-dbi-upto': '800',
    'write-dbi-upto': '800',
    'read-lecc-upto': '800',
    'write-lecc-upto': '800',
    'dfs-lvl-t-ck-0': '1400',
    'dfs-lvl-t-ck-1': '1800',
    'dfs-lvl-t-ck-2': '2700',
    'orbit-config-density': '8',
    'orbit-byte-mode': '1',
    'orbit-num-rank': '2',
    'orbit-default-ch': '1',
    'orbit-freq-level': '1',
    'orbit-lp5-freq-set': '6400',
    'orbit-rank-interleaving': '0',
    'two-channel': '1',
    'orbit-mixed': '1',
    'regional-clock-gating': '0',
    'dram-clock-gating': '0',
    'phy-clock-gating': '1',
    'phy-low-power': '1',
    'phy-idle-cnt-th': '32',
    'dynamic-power-down': '0',
    'dynamic-power-down-threshold': '1024',
    'dynamic-self-refresh': '0',
    'dynamic-self-refresh-threshold': '4096',
    'orbit-initial-training': '0',
    'command-bus-training': '0',
    'ca-vref-training': '0',
    'prbs-training': '0',
    'reboot-with-training': '0',
    'phy-vref-trn-mode': '0',
    'phy-duty-trn-mode': '0',
    'dram-vref-trn-mode': '0',
    'dram-duty-trn-mode': '0',
    'orbit-phy-odt': '9',
    'orbit-otd-ck': '0',
    'orbit-otd-cs': '0',
    'orbit-otd-ca': '0',
    'orbit-zq-bg-mode': '0',
    'orbit-reboot-with-mrw': '0',
    'orbit-rfm-en': '0',
    'orbit-dsm-en': '1',
    'orbit-ca-odt': '0',
    'init-zq-calibration': '0',
    'zq-calibration': '0',
    'zq-calibration-period': '24000',
    'periodic-training': '0',
    'periodic-training-period': '25000',
    'temp-sensing': '0',
    'temp-sensing-period': '16000',
    't-refiab': '1234000',
    't-refipb': '345000',
    't-zqcal': '900000',
    'wdqs-ctrl-mode': '0',
    'rpste-upto': '1000',
    'wpste-upto': '1000',
    'variable-trrd': '1',
    'txsr-as-1st-ed': '0',
    'wck-1to4-upto': '800',
    'wck-always-on-from': '0',
    'wck-always-on-upto': '3000',
    'nt-odt-upto': '800',
    'bg-mode-upto': '800',
    'wck-hf-upto': '800',
    'wck-pst1-upto': '800',
    'wck-pst2-upto': '800',
    'rdqs-pst1-upto': '800',
    'rdqs-pst2-upto': '800',
    'enhanced-nt-odt': '1',
    'mrr-byte-lane': '0x11',
    'timing-unit': 'MHz',
}

DYN_PERIODS = ['periods-0', 'periods-1', 'periods-2', 'periods-3',
               'periods-4', 'periods-5']
PERIOD_COUNTS = {'lpddr4': 6, 'lpddr5': 5}


def run(p):
    return generate_and_analyze(p)


def check_exact(case, p, data):
    orbit = data['orbit']
    for name, field in EXACT_ORBIT.items():
        if name not in p:
            continue
        actual = orbit[field]
        if isinstance(actual, str):
            actual = int(actual, 16)
        case.assertEqual(actual, int(p[name]), '%s -> %s' % (name, field))


class EveryUiParameter(unittest.TestCase):
    def test_every_control_has_an_executable_case(self):
        controls = form_controls()
        executed = set()
        failures = []

        # 1. Select/numeric/checkbox orbit fields with exact round-trip.
        for name, field in EXACT_ORBIT.items():
            dt = 'lpddr4' if name in ('rpste-upto', 'wpste-upto') else 'lpddr5'
            if name in ('orbit-dsm-en', 'orbit-zq-bg-mode'):
                dt = 'lpddr5'
            p = base_params(dt)
            p[name] = ALT[name]
            try:
                data = run(p)
                actual = data['orbit'][field]
                if isinstance(actual, str):
                    actual = int(actual, 16)
                self.assertEqual(actual, int(p[name]),
                                 '%s -> %s' % (name, field))
                executed.add(name)
            except Exception as e:
                failures.append('%s: %s' % (name, e))

        # 2. Derived controls.
        derived_cases = [
            ('two-channel', 'lpddr5', {'two-channel': '1'}),
            ('orbit-default-ch', 'lpddr5', {'orbit-default-ch': '1'}),
            ('orbit-freq-level', 'lpddr5', {'orbit-freq-level': '2'}),
            ('orbit-lp5-freq-set', 'lpddr5',
             {'orbit-freq-level': '0', 'orbit-lp5-freq-set': '6400'}),
            ('orbit-byte-mode', 'lpddr5', {'orbit-byte-mode': '1'}),
            ('orbit-mixed', 'lpddr5',
             {'orbit-mixed': '1', 'orbit-num-rank': '2'}),
            ('dfs-lvl-t-ck-0', 'lpddr5', {'dfs-lvl-t-ck-0': '1400',
                                           'dfs-lvl-t-ck-1': '1672',
                                           'dfs-lvl-t-ck-2': '2512'}),
            ('dfs-lvl-t-ck-1', 'lpddr5', {'dfs-lvl-t-ck-0': '1428',
                                           'dfs-lvl-t-ck-1': '1800',
                                           'dfs-lvl-t-ck-2': '2512'}),
            ('dfs-lvl-t-ck-2', 'lpddr5', {'dfs-lvl-t-ck-0': '1428',
                                           'dfs-lvl-t-ck-1': '1672',
                                           'dfs-lvl-t-ck-2': '2700'}),
        ]
        for name, dt, overrides in derived_cases:
            p = base_params(dt)
            p.update(overrides)
            try:
                data = run(p)
                orbit = data['orbit']
                if name == 'two-channel':
                    self.assertTrue(data['two_channel'])
                elif name == 'orbit-default-ch':
                    self.assertEqual(orbit['omc_channel'], 1)
                elif name == 'orbit-freq-level':
                    self.assertEqual(orbit['timingtable_size'], 2)
                elif name == 'orbit-lp5-freq-set':
                    self.assertEqual(orbit['dram_t_ck'], 1256)
                elif name == 'orbit-byte-mode':
                    self.assertEqual(
                        orbit['chip'][0]['num_row'] -
                        _base_row('lpddr5', 16), 1)
                elif name == 'orbit-mixed':
                    self.assertNotEqual(orbit['chip'][1]['num_row'], 0)
                elif name.startswith('dfs-lvl'):
                    idx = int(name[-1])
                    self.assertEqual(orbit['dfs_lvl_t_ck'][idx],
                                     int(overrides[name]))
                executed.add(name)
            except Exception as e:
                failures.append('%s: %s' % (name, e))

        # 3. Timing threshold controls, one at a time.
        for name, (field, op) in {**TIMING_THRESHOLDS, **LP4_TIMING}.items():
            dt = 'lpddr4' if name in LP4_TIMING else 'lpddr5'
            periods = ([938, 1631, 2500] if dt == 'lpddr4'
                       else [314, 418, 556, 2500])
            value = periods[1]  # middle point
            p = base_params(dt)
            p[name] = str(value)
            try:
                data = run(p)
                for e in data['timing_entries']['entries']:
                    tck = e['t_ck_display']
                    if name == 'read-dbi-upto':
                        expected = value >= tck and not (
                            int(p.get('read-lecc-upto', '0')) > tck)
                    elif op == '>=':
                        expected = value >= tck
                    elif op == '>':
                        expected = value > tck
                    else:  # bank_mode
                        expected = 0 if value >= tck else 2
                    actual = e.get(field)
                    if op != 'special':
                        actual = 1 if actual else 0
                    self.assertEqual(actual, expected,
                                     '%s at tck=%d' % (name, tck))
                executed.add(name)
            except Exception as e:
                failures.append('%s: %s' % (name, e))

        # 4. LP5 WCK controls.
        for name in ('wck-1to4-upto', 'wck-hf-upto',
                     'wck-always-on-from', 'wck-always-on-upto'):
            p = base_params('lpddr5')
            p['periods'] = '625 938 2500'
            p.update({name: ALT[name]})
            try:
                data = run(p)
                entries = data['timing_entries']['entries']
                if name == 'wck-1to4-upto':
                    for e in entries:
                        self.assertEqual(
                            e['wck_ratio'],
                            4 if int(ALT[name]) >= e['t_ck_display'] else 2)
                elif name == 'wck-hf-upto':
                    for e in entries:
                        self.assertEqual(
                            e['wck_fm'],
                            1 if int(ALT[name]) >= e['t_ck_display'] else 0)
                elif name.startswith('wck-always-on'):
                    for e in entries:
                        from_eff = (1000000 if int(p['wck-always-on-from']) == 0
                                    else int(p['wck-always-on-from']))
                        upto_eff = (1000000 if int(p['wck-always-on-upto']) == 0
                                    else int(p['wck-always-on-upto']))
                        on = (from_eff >= e['t_ck_display']
                              and upto_eff <= e['t_ck_display'])
                        self.assertEqual(bool(e['wck_on']), on)
                executed.add(name)
            except Exception as e:
                failures.append('%s: %s' % (name, e))

        # 5. Calculation-only / presentation-only controls: prove the
        # generator accepts an alternate value (or document why not).
        for name in ('speed-bin', 'dram-tck', 'min-dram-tck', 'wire-length',
                     'cpipe-depth', 'dpipe-depth', 'omc-freq-ratio',
                     'phy-freq-ratio', 'wdqs-ctrl-mode', 'variable-trrd',
                     'txsr-as-1st-ed', 'enhanced-nt-odt',
                     'wck-pst1-upto', 'wck-pst2-upto',
                     'rdqs-pst1-upto', 'rdqs-pst2-upto', 'mrr-byte-lane'):
            dt = 'lpddr4' if name in ('wdqs-ctrl-mode', 'variable-trrd',
                                      'txsr-as-1st-ed', 'rpste-upto',
                                      'wpste-upto') else 'lpddr5'
            p = base_params(dt)
            p[name] = ALT[name]
            try:
                data = run(p)
                self.assertTrue(data['orbit']['available'])
                executed.add(name)
            except Exception as e:
                failures.append('%s: %s' % (name, e))

        # 6. Dynamic period slots (max entries per DRAM type).
        for dt, count in PERIOD_COUNTS.items():
            for n in range(count):
                p = base_params(dt)
                periods = (['625', '938', '1631', '2000', '2500', '3000']
                           if dt == 'lpddr4'
                           else ['314', '418', '556', '1000', '2500'])
                p['periods'] = ' '.join(periods[:n + 1])
                try:
                    data = run(p)
                    self.assertEqual(
                        len(data['timing_entries']['entries']), n + 1)
                    executed.add('periods-%d' % n)
                except Exception as e:
                    failures.append('periods-%d: %s' % (n, e))

        # 7. Presentation / PHY name.
        p = base_params('lpddr5')
        p['phy-name'] = 'sphy-v9r8'
        run(p)
        executed.add('phy-name')

        # timing-unit: verify the JS conversion list covers all timing fields.
        with open(os.path.join(ROOT, 'templates', 'gui.html')) as f:
            html = f.read()
        m = re.search(r'const fieldsToConvert = \[(.*?)\];', html, re.S)
        self.assertIsNotNone(m)
        converted = set(re.findall(r"'([^']+)'", m.group(1)))
        for name in ('dram-tck', 'min-dram-tck', 'write-odt-upto',
                     'read-dbi-upto', 'write-dbi-upto', 'read-lecc-upto',
                     'write-lecc-upto', 'dfs-lvl-t-ck-0', 'dfs-lvl-t-ck-1',
                     'dfs-lvl-t-ck-2', 'rpste-upto', 'wpste-upto',
                     'wck-1to4-upto', 'wck-always-on-from',
                     'wck-always-on-upto', 'nt-odt-upto', 'bg-mode-upto',
                     'wck-hf-upto', 'wck-pst1-upto', 'wck-pst2-upto',
                     'rdqs-pst1-upto', 'rdqs-pst2-upto'):
            self.assertIn(name, converted, 'unit conversion missing %s' % name)
        executed.add('timing-unit')

        # 8. Completeness gate.
        expected = set(controls)
        missing = sorted(expected - executed)
        extra = sorted(executed - expected - set(DYN_PERIODS))
        self.assertEqual(missing, [],
                         'UI controls without an executable case: %r' % missing)
        self.assertEqual(failures, [], '\n'.join(failures))
        self.assertEqual(extra, [], 'cases reference unknown controls: %r' % extra)

    def test_all_select_options(self):
        """Run every option of every select control at least once."""
        checks = []

        for density in [2, 3, 4, 6, 8, 12, 16]:
            checks.append(('orbit-config-density', 'lpddr4', str(density),
                           lambda d, v: d['orbit']['density'] == int(v)))
        for density in [2, 3, 4, 6, 8, 12, 16, 24, 32]:
            checks.append(('orbit-config-density', 'lpddr5', str(density),
                           lambda d, v: d['orbit']['density'] == int(v)))
        for width, lane in [(4, 0x55), (8, 0xFF), (16, 0x55), (32, 0x11)]:
            checks.append(('dq-width', 'lpddr5', str(width),
                           lambda d, v, lane=lane:
                           d['orbit']['dq_width'] == int(v) and
                           int(d['orbit']['mrr_byte_lane'], 16) == lane))
        for rank in [1, 2]:
            checks.append(('orbit-num-rank', 'lpddr5', str(rank),
                           lambda d, v: d['orbit']['num_rank'] == int(v)))
        for mode in [0, 1]:
            checks.append(('orbit-byte-mode', 'lpddr5', str(mode),
                           lambda d, v: d['orbit']['chip'][0]['num_row'] -
                           {'2': 13, '3': 14, '4': 14, '6': 15, '8': 15,
                            '12': 16, '16': 16, '24': 17, '32': 17}[
                               str(d['orbit']['density'])] == int(v)))
            checks.append(('orbit-mixed', 'lpddr5', str(mode),
                           lambda d, v: True))
        for ch in [0, 1]:
            checks.append(('orbit-default-ch', 'lpddr5', str(ch),
                           lambda d, v: d['orbit']['omc_channel'] == int(v)))
        for level in range(4):
            checks.append(('orbit-freq-level', 'lpddr5', str(level),
                           lambda d, v: d['orbit']['timingtable_size'] ==
                           4 - int(v)))
        for freq_set, tck in [('6000', 1332), ('6400', 1256)]:
            checks.append(('orbit-lp5-freq-set', 'lpddr5', freq_set,
                           lambda d, v, tck=tck:
                           d['orbit']['dram_t_ck'] == tck))
        checks.append(('orbit-rank-interleaving', 'lpddr5', '0',
                       lambda d, v: d['orbit']['rank_interleaving'] == 0))
        checks.append(('orbit-dsm-en', 'lpddr5', '1',
                       lambda d, v: d['orbit']['dsm_en'] == 1))
        checks.append(('orbit-zq-bg-mode', 'lpddr5', '0',
                       lambda d, v: d['orbit']['zq_bg_mode'] == 0))

        for name, dt, value, verify in checks:
            with self.subTest(control=name, value=value):
                p = base_params(dt)
                p[name] = value
                # Keep dependent fields consistent.
                if name == 'orbit-freq-level':
                    rest = ([1332, 1428, 1672, 2512] if dt == 'lpddr5'
                            else [471, 938, 1631, 2500])[int(value) + 1:]
                    rest = rest + [0] * (3 - len(rest))
                    for i in range(3):
                        p['dfs-lvl-t-ck-%d' % i] = str(rest[i])
                data = generate_and_analyze(p)
                self.assertTrue(verify(data, value),
                                '%s=%s not reflected' % (name, value))


def _base_row(dram_type, density):
    if dram_type == 'lpddr4':
        return {2: 14, 3: 15, 4: 15, 6: 16, 8: 16, 12: 17, 16: 17}.get(density, 0)
    return {2: 13, 3: 14, 4: 14, 6: 15, 8: 15, 12: 16, 16: 16, 24: 17, 32: 17}.get(density, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
