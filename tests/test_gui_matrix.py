"""End-to-end GUI-case matrix.

Each case builds the same parameter dict the web form would submit, runs
``gui.build_generate_cmd()``, analyses the resulting 4 KiB image through
``gui.analyze_binary_file()`` (auto-detection included), and checks the
orbit_config fields and timing entries the UI would display.
"""
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import gui  # noqa: E402
from orbit_config import EMMC_CM4_TIME_TB_SIZE  # noqa: E402

LP5_SETS = {
    '6000': [1332, 1428, 1672, 2512],
    '6400': [1256, 1428, 1672, 2512],
}
LP4_SET = [471, 938, 1631, 2500]


def base_params(dram_type='lpddr4', **overrides):
    """A complete set of form values (mirrors the HTML defaults)."""
    is_lp5 = dram_type == 'lpddr5'
    params = {
        'dram-type': dram_type,
        'phy-name': 'sphy-v9r8',
        'speed-bin': '6400' if is_lp5 else '4266',
        'dq-width': '16',
        'cpipe-depth': '1',
        'dpipe-depth': '1',
        'wire-length': '10',
        'write-odt-upto': '10000' if is_lp5 else '1249',
        'read-dbi-upto': '10000',
        'write-dbi-upto': '10000',
        'read-lecc-upto': '0',
        'write-lecc-upto': '625',
        'min-dram-tck': '314' if is_lp5 else '468',
        'dram-tck': '1256' if is_lp5 else '471',
        'periods': '314 418 556 2500' if is_lp5 else '938 1631 2500',
        'orbit-config-density': '16',
        'orbit-byte-mode': '0',
        'orbit-mixed': '0',
        'orbit-num-rank': '1',
        'orbit-rank-interleaving': '1',
        'orbit-default-ch': '0',
        'orbit-freq-level': '0',
        'orbit-lp5-freq-set': '6000',
        'orbit-reboot-with-mrw': '1',
        'orbit-rfm-en': '1',
        'orbit-ca-odt': '1',
        'orbit-phy-odt': '5',
        'orbit-otd-ck': '1',
        'orbit-otd-cs': '1',
        'orbit-otd-ca': '1',
        'orbit-initial-training': '1',
        'phy-vref-trn-mode': '1',
        'phy-duty-trn-mode': '1',
        'dram-vref-trn-mode': '1',
        'dram-duty-trn-mode': '1',
        'command-bus-training': '1',
        'ca-vref-training': '1',
        'prbs-training': '1',
        'reboot-with-training': '1',
        'init-zq-calibration': '1',
        'zq-calibration': '1',
        'zq-calibration-period': '48000',
        'phy-idle-cnt-th': '128',
        'phy-low-power': '0',
        'dynamic-power-down': '1',
        'dynamic-power-down-threshold': '2048',
        'dynamic-self-refresh': '1',
        'dynamic-self-refresh-threshold': '2048',
        'periodic-training': '1',
        'periodic-training-period': '50000',
        'temp-sensing': '1',
        'temp-sensing-period': '32000',
        't-refiab': '3904000',
        't-refipb': '488000',
        't-zqcal': '1000000',
        'regional-clock-gating': '1',
        'dram-clock-gating': '1',
        'phy-clock-gating': '0',
        'orbit-dsm-en': '0',
        'orbit-zq-bg-mode': '1',
    }
    if is_lp5:
        params.update({
            'wck-1to4-upto': '625',
            'wck-always-on-from': '0',
            'wck-always-on-upto': '10000',
            'nt-odt-upto': '625',
            'bg-mode-upto': '625',
            'wck-hf-upto': '625',
            'wck-pst1-upto': '1250',
            'wck-pst2-upto': '625',
            'rdqs-pst1-upto': '1250',
            'rdqs-pst2-upto': '625',
        })
    else:
        params.update({
            'rpste-upto': '625',
            'wpste-upto': '625',
            'wdqs-ctrl-mode': '1',
            'variable-trrd': '0',
            'txsr-as-1st-ed': '1',
        })
    params.update(overrides)
    return params


def _levels(params):
    set_name = params.get('orbit-lp5-freq-set', '6000')
    dram_type = params['dram-type']
    table = LP5_SETS[set_name] if dram_type == 'lpddr5' else LP4_SET
    level = int(params.get('orbit-freq-level', '0'))
    dfs = table[level + 1:] + [0] * (3 - len(table[level + 1:]))
    return table[level], dfs


def _expected_rows(dram_type, density, byte_mode, mixed, num_rank):
    rows = []
    for i in range(num_rank):
        d = density * (2 if (i == 1 and mixed) else 1)
        bump = 1 if byte_mode else 0
        if dram_type == 'lpddr4':
            if d == 2:
                row = 14
            elif d in (3, 4):
                row = 15
            elif d in (6, 8):
                row = 16
            else:
                row = 17
        else:
            if d == 2:
                row = 13
            elif d in (3, 4):
                row = 14
            elif d in (6, 8):
                row = 15
            elif d in (12, 16):
                row = 16
            else:
                row = 17
        rows.append(row + bump)
    return rows


def run_case(case, params):
    if 'dfs-lvl-t-ck-0' in params:
        expected_dfs = [int(params.get('dfs-lvl-t-ck-%d' % i, 0) or 0)
                        for i in range(3)]
    else:
        _, expected_dfs = _levels(params)
        params['dfs-lvl-t-ck-0'] = str(expected_dfs[0])
        params['dfs-lvl-t-ck-1'] = str(expected_dfs[1])
        params['dfs-lvl-t-ck-2'] = str(expected_dfs[2])
    cmd, json_path = gui.build_generate_cmd(params)
    proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True)
    case.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    bin_path = os.path.join(ROOT, 'ddr_timing_table.bin')
    case.assertEqual(os.path.getsize(bin_path), 0x1000,
                     'generated image must be 4 KiB')
    case.assertTrue(os.path.exists(json_path))

    result = gui.analyze_binary_file(bin_path)
    case.assertTrue(result['success'], result)
    data = result['data']
    orbit = data['orbit']

    dram_type = params['dram-type']
    two_channel = params.get('two-channel') == '1'
    case.assertEqual(data['dram_type'], dram_type)
    case.assertEqual(data['two_channel'], two_channel)
    case.assertTrue(orbit['available'])

    case.assertEqual(orbit['density'], int(params['orbit-config-density']))
    case.assertEqual(orbit['num_rank'], int(params['orbit-num-rank']))
    rows = _expected_rows(
        dram_type, int(params['orbit-config-density']),
        int(params['orbit-byte-mode']), int(params['orbit-mixed']),
        int(params['orbit-num-rank']))
    for i, row in enumerate(rows):
        case.assertEqual(orbit['chip'][i]['num_row'], row)
        case.assertEqual(orbit['chip'][i]['num_col'], 10)
        case.assertEqual(orbit['chip'][i]['num_bg'], 0)
        case.assertEqual(orbit['chip'][i]['num_bank'], 3 if dram_type == 'lpddr4' else 4)
    case.assertEqual(orbit['rank_interleaving'],
                     int(params['orbit-rank-interleaving']))
    case.assertEqual(orbit['omc_channel'],
                     2 if two_channel else int(params['orbit-default-ch']))
    case.assertEqual(orbit['phy_odt'], int(params['orbit-phy-odt']))

    boot, _ = _levels(params)
    case.assertEqual(orbit['dram_t_ck'], boot)
    case.assertEqual(orbit['timingtable_size'], 4 - int(params['orbit-freq-level']))
    case.assertEqual(list(orbit['dfs_lvl_t_ck']), expected_dfs)

    for gui_name, field in (
        ('orbit-initial-training', 'initial_training'),
        ('command-bus-training', 'command_bus_training'),
        ('ca-vref-training', 'ca_vref_training'),
        ('prbs-training', 'prbs_training'),
        ('reboot-with-training', 'reboot_with_training'),
        ('orbit-rfm-en', 'rfm_en'),
        ('orbit-ca-odt', 'ca_odt'),
        ('orbit-reboot-with-mrw', 'reboot_with_mrw'),
        ('periodic-training', 'periodic_training'),
        ('temp-sensing', 'temp_sensing'),
        ('dynamic-power-down', 'dynamic_power_down'),
        ('dynamic-self-refresh', 'dynamic_self_refresh'),
        ('regional-clock-gating', 'regional_clock_gating'),
        ('dram-clock-gating', 'dram_clock_gating'),
        ('phy-clock-gating', 'phy_clock_gating'),
        ('phy-low-power', 'phy_low_power'),
        ('orbit-otd-ck', 'otd_ck'),
        ('orbit-otd-cs', 'otd_cs'),
        ('orbit-otd-ca', 'otd_ca'),
        ('init-zq-calibration', 'init_zq_calibration'),
        ('zq-calibration', 'zq_calibration'),
    ):
        case.assertEqual(orbit[field], int(params[gui_name]),
                         '%s mismatch' % field)

    case.assertEqual(orbit['periodic_training_period'],
                     int(params['periodic-training-period']))
    case.assertEqual(orbit['dynamic_power_down_threshold'],
                     int(params['dynamic-power-down-threshold']))
    case.assertEqual(orbit['dynamic_self_refresh_threshold'],
                     int(params['dynamic-self-refresh-threshold']))
    if dram_type == 'lpddr5':
        case.assertEqual(orbit['bg_intr_size'], 3)
        case.assertEqual(orbit['zq_bg_mode'], int(params['orbit-zq-bg-mode']))
        case.assertEqual(orbit['dsm_en'], int(params['orbit-dsm-en']))
    else:
        case.assertEqual(orbit['bg_intr_size'], 0)

    # Timing entries: one per period, t_ck as stored internally.
    entries = data['timing_entries']['entries']
    case.assertEqual(len(entries), len(params['periods'].split()))
    expected_tck = [int(p) for p in params['periods'].split()]
    for entry, expected in zip(entries, expected_tck):
        if dram_type == 'lpddr5':
            case.assertEqual(entry['t_ck_display'], expected)
        else:
            case.assertEqual(entry['t_ck'], expected)
        case.assertEqual(len(entry['timing_param']), 21)
        case.assertEqual(len(entry['dfi_timing_param']), 8)
        case.assertEqual(len(entry['t_rfcab']), 7 if dram_type == 'lpddr4' else 10)

    # JSON override file must contain the fields the GUI sent.
    with open(json_path) as f:
        override = json.load(f)
    case.assertEqual(override['num_rank'], int(params['orbit-num-rank']))
    case.assertEqual(override['dq_width'], int(params['dq-width']))


class GuiCaseMatrix(unittest.TestCase):
    def test_lp4_single_default(self):
        run_case(self, base_params('lpddr4'))

    def test_lp4_dual_byte_mixed_rank2(self):
        p = base_params('lpddr4', **{
            'two-channel': '1', 'orbit-byte-mode': '1', 'orbit-mixed': '1',
            'orbit-num-rank': '2', 'orbit-config-density': '8',
        })
        run_case(self, p)

    def test_lp4_single_omc1_level1(self):
        p = base_params('lpddr4', **{
            'orbit-default-ch': '1', 'orbit-freq-level': '1',
            'orbit-config-density': '4',
        })
        run_case(self, p)

    def test_lp5_single_6000(self):
        run_case(self, base_params('lpddr5'))

    def test_lp5_dual_6400_rank2(self):
        p = base_params('lpddr5', **{
            'two-channel': '1', 'orbit-lp5-freq-set': '6400',
            'orbit-num-rank': '2', 'orbit-config-density': '32',
        })
        run_case(self, p)

    def test_lp5_single_level1(self):
        p = base_params('lpddr5', **{'orbit-freq-level': '1'})
        run_case(self, p)

    def test_lp5_single_level3_6400(self):
        p = base_params('lpddr5', **{
            'orbit-freq-level': '3', 'orbit-lp5-freq-set': '6400',
            'orbit-config-density': '8',
        })
        run_case(self, p)

    def test_lp5_training_all_off(self):
        p = base_params('lpddr5', **{
            'orbit-initial-training': '0', 'phy-vref-trn-mode': '0',
            'phy-duty-trn-mode': '0', 'dram-vref-trn-mode': '0',
            'dram-duty-trn-mode': '0', 'command-bus-training': '0',
            'ca-vref-training': '0', 'prbs-training': '0',
            'reboot-with-training': '0', 'init-zq-calibration': '0',
            'zq-calibration': '0', 'dynamic-power-down': '0',
            'dynamic-self-refresh': '0',
        })
        run_case(self, p)

    def test_lp5_custom_dfs_and_thresholds(self):
        p = base_params('lpddr5', **{
            'dfs-lvl-t-ck-0': '1500', 'dfs-lvl-t-ck-1': '1700',
            'dfs-lvl-t-ck-2': '2600',
            'dynamic-power-down-threshold': '4096',
            'dynamic-self-refresh-threshold': '1024',
            'orbit-zq-bg-mode': '0', 'orbit-dsm-en': '1',
        })
        run_case(self, p)

    def test_lp5_all_optional_features_off(self):
        p = base_params('lpddr5', **{
            'regional-clock-gating': '0', 'dram-clock-gating': '0',
            'phy-clock-gating': '1', 'orbit-rfm-en': '0',
            'orbit-reboot-with-mrw': '0', 'orbit-ca-odt': '0',
            'orbit-otd-ck': '0', 'orbit-otd-cs': '0', 'orbit-otd-ca': '0',
            'periodic-training': '0', 'temp-sensing': '0',
            'zq-calibration': '0', 'init-zq-calibration': '0',
            'orbit-zq-bg-mode': '0', 'orbit-dsm-en': '1',
        })
        run_case(self, p)

    def test_lp5_low_power(self):
        p = base_params('lpddr5', **{
            'phy-low-power': '1', 'phy-idle-cnt-th': '64',
            'orbit-config-density': '24',
        })
        run_case(self, p)

    def test_timing_only_4k_still_parses_entries(self):
        p = base_params('lpddr5')
        cmd, _ = gui.build_generate_cmd(p)
        subprocess.run(cmd, cwd=ROOT, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        path = os.path.join(ROOT, 'ddr_timing_table.bin')
        with open(path, 'rb') as f:
            data = bytearray(f.read())
        data[EMMC_CM4_TIME_TB_SIZE:] = b'\0' * (len(data) - EMMC_CM4_TIME_TB_SIZE)
        with open(path, 'wb') as f:
            f.write(data)
        result = gui.analyze_binary_file(path)
        self.assertTrue(result['success'], result)
        self.assertFalse(result['data']['orbit']['available'])
        self.assertEqual(result['data']['dram_type'], 'lpddr5')
        self.assertEqual(len(result['data']['timing_entries']['entries']), 4)

    def test_original_repo_4k_images_auto_identify(self):
        for name, dram_type in (
            ('ddr_timing_table_lpddr4.bin', 'lpddr4'),
            ('ddr_timing_table_lpddr5.bin', 'lpddr5'),
        ):
            path = os.path.join('/home/se/git/arise2/out/Arise2-chip/bin', name)
            if not os.path.exists(path):
                continue
            result = gui.analyze_binary_file(path)
            self.assertTrue(result['success'], result)
            self.assertEqual(result['data']['dram_type'], dram_type)
            self.assertTrue(result['data']['two_channel'])
            self.assertTrue(result['data']['orbit']['available'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
