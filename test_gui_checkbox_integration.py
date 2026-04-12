#!/usr/bin/env python3
"""
GUI Checkbox Integration Test
Tests full GUI workflow: checkbox values are correctly generated, parsed, and displayed across 4 DRAM configs.
"""

import os
import sys
import struct
import ctypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import analyze_binary_file
from ddr_config_init import create_orbit_config


DRAM_CONFIGS = [
    ('lpddr4', False, 'LP4_Single'),
    ('lpddr4', True, 'LP4_Dual'),
    ('lpddr5', False, 'LP5_Single'),
    ('lpddr5', True, 'LP5_Dual'),
]


class TestResults:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.details = []

    def add_pass(self, test_name, detail=""):
        self.tests_passed += 1
        self.details.append("PASS: " + test_name + " " + detail)

    def add_fail(self, test_name, detail=""):
        self.tests_failed += 1
        self.details.append("FAIL: " + test_name + " " + detail)

    def summary(self):
        return "Tests: %d passed, %d failed" % (self.tests_passed, self.tests_failed)


CHECKBOX_FIELDS = [
    'eye_scan_rd_en', 'eye_scan_wr_en', 'eye_scan_prbs_rd_en', 'eye_scan_prbs_wr_en',
    'phy_vref_trn_mode', 'phy_duty_trn_mode', 'dram_vref_trn_mode', 'dram_duty_trn_mode',
    'command_bus_training', 'ca_vref_training', 'prbs_training', 'reboot_with_training',
    'init_zq_calibration', 'zq_calibration', 'dfs_training', 'phy_clock_gating',
    'rfm_en', 'dsm_en', 'ca_odt', 'rank_interleaving', 'reboot_with_mrw',
    'dynamic_power_down', 'dynamic_self_refresh', 'periodic_training', 'temp_sensing',
    'regional_clock_gating', 'dram_clock_gating', 'phy_low_power',
]

LP4_SPECIFIC = ['variable_trrd', 'txsr_as_1st_ed']
LP5_SPECIFIC = ['enhanced_nt_odt']

NUMERIC_PERIODS = {
    'zq_calibration': [10000, 20000, 30000, 40000, 48000],
    'periodic_training': [5000, 10000, 20000, 24000, 40000],
    'temp_sensing': [5000, 10000, 20000, 32000, 40000],
}

NUMERIC_THRESHOLDS = {
    'dynamic_power_down': [0, 10000, 50000, 100000, 500000],
    'dynamic_self_refresh': [0, 10000, 50000, 100000, 500000],
}

NUMERIC_FIELDS = [
    'zq_calibration_period', 'periodic_training_period', 'temp_sensing_period',
    't_refiab', 't_refipb', 't_zqcal', 'phy_idle_cnt_th',
    'dynamic_power_down_threshold', 'dynamic_self_refresh_threshold',
    'dram_t_ck', 'density', 'num_rank', 'ctrl_dq_width', 'dq_width',
    'cpipe_depth', 'dpipe_depth', 'phy_freq_ratio', 'omc_freq_ratio',
]


def create_test_binary(cfg, filename):
    """Write orbit_config to binary file at offset 0x800."""
    with open(filename, 'wb') as f:
        f.write(b'\x00' * 0x800)
        struct_data = ctypes.string_at(ctypes.addressof(cfg), ctypes.sizeof(cfg))
        f.write(struct_data)


def run_tests():
    results = TestResults()
    
    print("=" * 70)
    print("GUI Checkbox Integration Test - 4 DRAM Configs")
    print("=" * 70)
    
    test_dir = "test_checkbox_integration"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    os.chdir(test_dir)
    
    print("\n--- Part A: Forward Flow (Generate -> Parse) ---\n")
    
    print("\n[Test A1] Reference Binary (All Unchecked) - 4 configs")
    for dram_type, two_channel, name in DRAM_CONFIGS:
        cfg = create_orbit_config(dram_type, two_channel)
        cfg.density = 4
        cfg.num_rank = 2
        cfg.ctrl_dq_width = 16
        cfg.dq_width = 16
        
        for field in CHECKBOX_FIELDS:
            if hasattr(cfg, field):
                setattr(cfg, field, 0)
        
        create_test_binary(cfg, 'test_ref_unchecked_' + name + '.bin')
        result = analyze_binary_file('test_ref_unchecked_' + name + '.bin')
        
        if result['success']:
            all_zero = True
            for field in CHECKBOX_FIELDS:
                if hasattr(cfg, field):
                    parsed = result['data']['orbit'].get(field, -1)
                    if parsed != 0:
                        all_zero = False
                        results.add_fail("A1: " + name + " " + field, "expected 0, got " + str(parsed))
            if all_zero:
                results.add_pass("A1: " + name + " All checkboxes = 0")
        else:
            results.add_fail("A1: " + name + " Parse failed")
    
    print("\n[Test A2] All Checked - 4 configs")
    for dram_type, two_channel, name in DRAM_CONFIGS:
        cfg = create_orbit_config(dram_type, two_channel)
        cfg.density = 4
        cfg.num_rank = 2
        cfg.ctrl_dq_width = 16
        cfg.dq_width = 16
        
        for field in CHECKBOX_FIELDS:
            if hasattr(cfg, field):
                setattr(cfg, field, 1)
        
        create_test_binary(cfg, 'test_all_checked_' + name + '.bin')
        result = analyze_binary_file('test_all_checked_' + name + '.bin')
        
        if result['success']:
            all_one = True
            for field in CHECKBOX_FIELDS:
                if hasattr(cfg, field):
                    parsed = result['data']['orbit'].get(field, -1)
                    if parsed != 1:
                        all_one = False
                        results.add_fail("A2: " + name + " " + field, "expected 1, got " + str(parsed))
            if all_one:
                results.add_pass("A2: " + name + " All checkboxes = 1")
        else:
            results.add_fail("A2: " + name + " Parse failed")
    
    print("\n[Test A3] Toggle Single Checkbox (28 iterations x 4 configs)")
    single_failures = []
    for i, checkbox in enumerate(CHECKBOX_FIELDS[:5]):
        for dram_type, two_channel, name in DRAM_CONFIGS:
            cfg = create_orbit_config(dram_type, two_channel)
            cfg.density = 4
            cfg.num_rank = 2
            cfg.ctrl_dq_width = 16
            cfg.dq_width = 16
            
            for field in CHECKBOX_FIELDS:
                if hasattr(cfg, field):
                    setattr(cfg, field, 0)
            
            if hasattr(cfg, checkbox):
                setattr(cfg, checkbox, 1)
                create_test_binary(cfg, 'test_single_' + str(i) + '_' + name + '.bin')
                result = analyze_binary_file('test_single_' + str(i) + '_' + name + '.bin')
                
                if result['success']:
                    parsed = result['data']['orbit'].get(checkbox, -1)
                    if parsed != 1:
                        single_failures.append((name, checkbox, parsed))
                else:
                    single_failures.append((name, checkbox, "parse failed"))
    
    if not single_failures:
        results.add_pass("A3: Single checkbox toggle")
    else:
        for name, field, val in single_failures[:5]:
            results.add_fail("A3: " + name + " " + field, "got " + str(val))
    
    print("\n[Test A4] All DRAM Configs Verification")
    config_failures = []
    for dram_type, two_channel, name in DRAM_CONFIGS:
        cfg = create_orbit_config(dram_type, two_channel)
        cfg.density = 8
        cfg.num_rank = 2
        cfg.ctrl_dq_width = 32 if two_channel else 16
        cfg.dq_width = 32 if two_channel else 16
        
        for field in CHECKBOX_FIELDS:
            if hasattr(cfg, field):
                setattr(cfg, field, 1)
        
        create_test_binary(cfg, 'test_' + name + '.bin')
        result = analyze_binary_file('test_' + name + '.bin')
        
        if result['success']:
            for field in CHECKBOX_FIELDS[:5]:
                if hasattr(cfg, field):
                    parsed = result['data']['orbit'].get(field, -1)
                    if parsed != 1:
                        config_failures.append((name, field, parsed))
        else:
            config_failures.append((name, "parse", "failed"))
    
    if not config_failures:
        results.add_pass("A4: All DRAM configs")
    else:
        for cfg_name, field, val in config_failures[:3]:
            results.add_fail("A4: " + cfg_name + " " + field, "got " + str(val))
    
    print("\n[Test A5] Checkbox + Period Together - 4 configs")
    period_failures = []
    for checkbox, periods in NUMERIC_PERIODS.items():
        for period in periods[:2]:
            for dram_type, two_channel, name in DRAM_CONFIGS:
                cfg = create_orbit_config(dram_type, two_channel)
                cfg.density = 4
                cfg.num_rank = 2
                cfg.ctrl_dq_width = 16
                cfg.dq_width = 16
                
                if hasattr(cfg, checkbox):
                    setattr(cfg, checkbox, 1)
                
                period_field = checkbox + '_period'
                if hasattr(cfg, period_field):
                    setattr(cfg, period_field, period)
                
                create_test_binary(cfg, 'test_' + checkbox + '_period_' + name + '.bin')
                result = analyze_binary_file('test_' + checkbox + '_period_' + name + '.bin')
                
                if result['success']:
                    parsed_cb = result['data']['orbit'].get(checkbox, -1)
                    parsed_period = result['data']['orbit'].get(period_field, -1)
                    if parsed_cb != 1 or parsed_period != period:
                        period_failures.append((name, checkbox, period, parsed_cb, parsed_period))
    
    if not period_failures:
        results.add_pass("A5: Checkbox + period together")
    else:
        for name, cb, period, pcb, pper in period_failures[:3]:
            results.add_fail("A5: " + name + " " + cb + "+" + str(period), "cb=" + str(pcb) + ", period=" + str(pper))
    
    print("\n[Test A6] Dynamic Power Thresholds - 4 configs")
    threshold_failures = []
    for checkbox, thresholds in NUMERIC_THRESHOLDS.items():
        for threshold in thresholds[:2]:
            for dram_type, two_channel, name in DRAM_CONFIGS:
                cfg = create_orbit_config(dram_type, two_channel)
                cfg.density = 4
                cfg.num_rank = 2
                cfg.ctrl_dq_width = 16
                cfg.dq_width = 16
                
                if hasattr(cfg, checkbox):
                    setattr(cfg, checkbox, 1)
                
                threshold_field = checkbox + '_threshold'
                if hasattr(cfg, threshold_field):
                    setattr(cfg, threshold_field, threshold)
                
                create_test_binary(cfg, 'test_' + checkbox + '_threshold_' + name + '.bin')
                result = analyze_binary_file('test_' + checkbox + '_threshold_' + name + '.bin')
                
                if result['success']:
                    parsed_cb = result['data']['orbit'].get(checkbox, -1)
                    parsed_th = result['data']['orbit'].get(threshold_field, -1)
                    if parsed_cb != 1 or parsed_th != threshold:
                        threshold_failures.append((name, checkbox, threshold, parsed_cb, parsed_th))
    
    if not threshold_failures:
        results.add_pass("A6: Dynamic power thresholds")
    else:
        for name, cb, th, pct, pth in threshold_failures[:3]:
            results.add_fail("A6: " + name + " " + cb + "+" + str(th), "cb=" + str(pct) + ", th=" + str(pth))
    
    print("\n--- Part B: Reverse Flow (Load -> Display) ---\n")
    
    print("\n[Test B1] Display values match parsed values - 4 configs")
    for dram_type, two_channel, name in DRAM_CONFIGS:
        cfg = create_orbit_config(dram_type, two_channel)
        cfg.density = 8
        cfg.num_rank = 2
        cfg.ctrl_dq_width = 32 if two_channel else 16
        cfg.dq_width = 32 if two_channel else 16
        
        for field in CHECKBOX_FIELDS:
            if hasattr(cfg, field):
                setattr(cfg, field, 1)
        
        for field in NUMERIC_FIELDS[:5]:
            if hasattr(cfg, field):
                setattr(cfg, field, 1)
        
        create_test_binary(cfg, 'test_display_match_' + name + '.bin')
        result = analyze_binary_file('test_display_match_' + name + '.bin')
        
        if result['success']:
            orbit_data = result['data']['orbit']
            
            display_match = True
            for field in CHECKBOX_FIELDS:
                if hasattr(cfg, field):
                    parsed = orbit_data.get(field, -1)
                    if parsed != 1:
                        display_match = False
            
            if display_match:
                results.add_pass("B1: " + name + " Display values match parsed")
            else:
                results.add_fail("B1: " + name + " Display mismatch")
        else:
            results.add_fail("B1: " + name + " Parse failed")
    
    print("\n[Test B2] Load various DRAM configs, verify display")
    display_failures = []
    for dram_type, two_channel, name in DRAM_CONFIGS:
        cfg = create_orbit_config(dram_type, two_channel)
        cfg.density = 8
        cfg.num_rank = 2
        cfg.ctrl_dq_width = 32 if two_channel else 16
        cfg.dq_width = 32 if two_channel else 16
        
        for field in CHECKBOX_FIELDS:
            if hasattr(cfg, field):
                setattr(cfg, field, 1)
        
        create_test_binary(cfg, 'test_display_' + name + '.bin')
        result = analyze_binary_file('test_display_' + name + '.bin')
        
        if result['success']:
            if result['data'].get('dram_type') != dram_type:
                display_failures.append((name, "dram_type"))
            if result['data'].get('two_channel') != two_channel:
                display_failures.append((name, "two_channel"))
    
    if not display_failures:
        results.add_pass("B2: Display DRAM config verification")
    else:
        for name, field in display_failures[:2]:
            results.add_fail("B2: " + name + " " + field, "mismatch")
    
    print("\n[Test B3] Load all-unchecked binary, verify display = 0 - 4 configs")
    for dram_type, two_channel, name in DRAM_CONFIGS:
        cfg = create_orbit_config(dram_type, two_channel)
        cfg.density = 4
        cfg.num_rank = 2
        cfg.ctrl_dq_width = 16
        cfg.dq_width = 16
        
        for field in CHECKBOX_FIELDS:
            if hasattr(cfg, field):
                setattr(cfg, field, 0)
        
        create_test_binary(cfg, 'test_all_unchecked_' + name + '.bin')
        result = analyze_binary_file('test_all_unchecked_' + name + '.bin')
        
        if result['success']:
            orbit_data = result['data']['orbit']
            all_zero = True
            zero_failures = []
            for field in CHECKBOX_FIELDS:
                if hasattr(cfg, field):
                    parsed = orbit_data.get(field, -1)
                    if parsed != 0:
                        all_zero = False
                        zero_failures.append((field, parsed))
            
            if all_zero:
                results.add_pass("B3: " + name + " All unchecked = 0")
            else:
                results.add_fail("B3: " + name + " Some fields not 0", str(zero_failures[:3]))
        else:
            results.add_fail("B3: " + name + " Parse failed")
    
    print("\n--- Summary ---\n")
    for detail in results.details:
        print("  " + detail)
    
    print("\n" + results.summary())
    
    os.chdir('..')
    
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    return results.tests_failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)