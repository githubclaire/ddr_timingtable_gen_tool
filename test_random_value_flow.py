#!/usr/bin/env python3
"""
Test random value flow - traverse checkboxes, numeric values, and dropdowns
- Checkboxes: traverse all (0,1) across 4 DRAM configs
- Numeric: test multiple values in valid range across 4 DRAM configs
- Dropdowns: traverse all options across 4 DRAM configs
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import analyze_binary_file
from ddr_config_init import create_orbit_config
import ctypes


def generate_test_binary(params):
    """Generate binary with given params."""
    cfg = create_orbit_config(params.get('dram_type', 'lpddr4'), params.get('two_channel', False))
    
    for key, value in params.items():
        if key in ['dram_type', 'two_channel']:
            continue
        if hasattr(cfg, key):
            setattr(cfg, key, value)
    
    cfg.num_rank = params.get('num_rank', 2)
    cfg.density = params.get('density', 4)
    cfg.ctrl_dq_width = params.get('dq_width', 16)
    cfg.dq_width = params.get('dq_width', 16)
    
    with open('test_random_flow.bin', 'wb') as f:
        f.write(b'\x00' * 0x800)
        struct_data = ctypes.string_at(ctypes.addressof(cfg), ctypes.sizeof(cfg))
        f.write(struct_data)


DRAM_CONFIGS = [
    ('lpddr4', False, 'LP4_Single'),
    ('lpddr4', True, 'LP4_Dual'),
    ('lpddr5', False, 'LP5_Single'),
    ('lpddr5', True, 'LP5_Dual'),
]


def test_checkboxes():
    """Test all checkboxes with both 0 and 1 values across multiple DRAM configs."""
    print("\n" + "=" * 60)
    print("Part A: Checkbox Testing (Traverse ALL 0 and 1)")
    print("=" * 60)
    
    checkboxes = [
        'eye_scan_rd_en', 'eye_scan_wr_en', 'eye_scan_prbs_rd_en', 'eye_scan_prbs_wr_en',
        'phy_vref_trn_mode', 'phy_duty_trn_mode', 'dram_vref_trn_mode', 'dram_duty_trn_mode',
        'command_bus_training', 'ca_vref_training', 'prbs_training', 'reboot_with_training',
        'init_zq_calibration', 'zq_calibration', 'dfs_training', 'phy_clock_gating',
        'rfm_en', 'dsm_en', 'ca_odt', 'rank_interleaving', 'reboot_with_mrw',
        'dynamic_power_down', 'dynamic_self_refresh', 'periodic_training', 'temp_sensing',
        'regional_clock_gating', 'dram_clock_gating', 'phy_low_power',
    ]
    
    passed = 0
    failed = 0
    
    for dram_type, two_channel, config_name in DRAM_CONFIGS:
        for checkbox in checkboxes:
            for test_value in [0, 1]:
                params = {'dram_type': dram_type, 'two_channel': two_channel, checkbox: test_value}
                generate_test_binary(params)
                
                result = analyze_binary_file('test_random_flow.bin')
                if result['success']:
                    parsed = result['data']['orbit'].get(checkbox, -1)
                    if parsed == test_value:
                        passed += 1
                    else:
                        print("  FAIL: " + config_name + " " + checkbox + "=" + str(test_value) + " -> parsed=" + str(parsed))
                        failed += 1
                else:
                    print("  FAIL: " + config_name + " " + checkbox + "=" + str(test_value) + " -> parse error")
                    failed += 1
    
    print("  Checkbox results: " + str(passed) + " passed, " + str(failed) + " failed")
    return failed == 0


def test_numeric_fields():
    """Test numeric fields with multiple values in valid range across 4 DRAM configs."""
    print("\n" + "=" * 60)
    print("Part B: Numeric Field Testing (5-10 values per field)")
    print("=" * 60)
    
    numeric_tests = {
        'zq_calibration_period': [10000, 20000, 30000, 40000, 48000, 60000],
        'periodic_training_period': [5000, 10000, 20000, 24000, 40000],
        'temp_sensing_period': [5000, 10000, 20000, 32000, 40000],
        't_refiab': [2000000, 3000000, 3904000, 5000000],
        't_refipb': [200000, 300000, 488000, 600000],
        't_zqcal': [500000, 800000, 1000000, 2000000],
        'phy_idle_cnt_th': [100, 1000, 5000, 10000, 30000],
        'dynamic_power_down_threshold': [0, 10000, 50000, 100000, 500000],
        'dynamic_self_refresh_threshold': [0, 10000, 50000, 100000, 500000],
        'density': [4, 8, 16, 32],
        'num_rank': [1, 2],
        'dq_width': [16, 32],
    }
    
    passed = 0
    failed = 0
    
    for field, test_values in numeric_tests.items():
        for test_value in test_values:
            for dram_type, two_channel, config_name in DRAM_CONFIGS:
                params = {'dram_type': dram_type, 'two_channel': two_channel, field: test_value}
                generate_test_binary(params)
                
                result = analyze_binary_file('test_random_flow.bin')
                if result['success']:
                    parsed = result['data']['orbit'].get(field, -1)
                    if parsed == test_value:
                        passed += 1
                    else:
                        print("  FAIL: " + config_name + " " + field + "=" + str(test_value) + " -> parsed=" + str(parsed))
                        failed += 1
                else:
                    print("  FAIL: " + config_name + " " + field + "=" + str(test_value) + " -> parse error")
                    failed += 1
    
    print("  Numeric results: " + str(passed) + " passed, " + str(failed) + " failed")
    return failed == 0


def test_dropdowns():
    """Test dropdown fields with all options across 4 DRAM configs."""
    print("\n" + "=" * 60)
    print("Part C: Dropdown Testing (Traverse ALL options)")
    print("=" * 60)
    
    dropdown_tests = {
        'dq_width': [4, 8, 16, 32],
        'num_rank': [1, 2],
    }
    
    passed = 0
    failed = 0
    
    for field, test_values in dropdown_tests.items():
        for test_value in test_values:
            for dram_type, two_channel, config_name in DRAM_CONFIGS:
                params = {'dram_type': dram_type, 'two_channel': two_channel, field: test_value}
                generate_test_binary(params)
                
                result = analyze_binary_file('test_random_flow.bin')
                if result['success']:
                    parsed = result['data']['orbit'].get(field, -1)
                    if parsed == test_value:
                        passed += 1
                    else:
                        print("  FAIL: " + config_name + " " + field + "=" + str(test_value) + " -> parsed=" + str(parsed))
                        failed += 1
                else:
                    print("  FAIL: " + config_name + " " + field + "=" + str(test_value) + " -> parse error")
                    failed += 1
    
    print("  Dropdown results: " + str(passed) + " passed, " + str(failed) + " failed")
    return failed == 0


def test_all():
    """Run all tests."""
    print("=" * 60)
    print("Random Value Flow Test - Comprehensive")
    print("=" * 60)
    
    cb_pass = test_checkboxes()
    num_pass = test_numeric_fields()
    dd_pass = test_dropdowns()
    
    print("\n" + "=" * 60)
    print("Final Summary")
    print("=" * 60)
    print("  Checkboxes: " + ("PASS" if cb_pass else "FAIL"))
    print("  Numeric: " + ("PASS" if num_pass else "FAIL"))
    print("  Dropdowns: " + ("PASS" if dd_pass else "FAIL"))
    
    if cb_pass and num_pass and dd_pass:
        print("\nAll tests PASSED!")
        return True
    else:
        print("\nSome tests FAILED!")
        return False


if __name__ == '__main__':
    success = test_all()
    if os.path.exists('test_random_flow.bin'):
        os.remove('test_random_flow.bin')
    sys.exit(0 if success else 1)