#!/usr/bin/env python3
"""
Test checkbox flow - traverse ALL possible checkbox values (0 and 1)
32 checkboxes × 2 values = 64 test iterations
"""

import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import analyze_binary_file
from ddr_config_init import generate_orbit_config_binary, create_orbit_config


def test_checkbox_traverse_all():
    """Traverse all possible checkbox values (0 and 1) for all 32 checkboxes."""
    
    checkboxes = [
        'eye_scan_rd_en',
        'eye_scan_wr_en', 
        'eye_scan_prbs_rd_en',
        'eye_scan_prbs_wr_en',
        'phy_vref_trn_mode',
        'phy_duty_trn_mode',
        'dram_vref_trn_mode',
        'dram_duty_trn_mode',
        'command_bus_training',
        'ca_vref_training',
        'prbs_training',
        'reboot_with_training',
        'init_zq_calibration',
        'zq_calibration',
        'dfs_training',
        'phy_clock_gating',
        'rfm_en',
        'dsm_en',
        'ca_odt',
        'rank_interleaving',
        'reboot_with_mrw',
        'dynamic_power_down',
        'dynamic_self_refresh',
        'periodic_training',
        'temp_sensing',
        'regional_clock_gating',
        'dram_clock_gating',
        'phy_low_power',
    ]
    
    print("=" * 60)
    print("Checkbox Flow Test - Traverse ALL Values")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for checkbox in checkboxes:
        for test_value in [0, 1]:
            cfg = create_orbit_config('lpddr4', False)
            
            if hasattr(cfg, checkbox):
                setattr(cfg, checkbox, test_value)
                
                cfg.num_rank = 2
                cfg.density = 4
                cfg.ctrl_dq_width = 16
                cfg.dq_width = 16
                
                import ctypes
                with open('test_checkbox.bin', 'wb') as f:
                    f.write(b'\x00' * 0x800)
                    struct_data = ctypes.string_at(ctypes.addressof(cfg), ctypes.sizeof(cfg))
                    f.write(struct_data)
                
                result = analyze_binary_file('test_checkbox.bin')
                
                if result['success']:
                    parsed_value = result['data']['orbit'].get(checkbox, -1)
                    if parsed_value == test_value:
                        print(f"  PASS: {checkbox}={test_value}")
                        passed += 1
                    else:
                        print(f"  FAIL: {checkbox}={test_value} - parsed as {parsed_value}")
                        failed += 1
                else:
                    print(f"  FAIL: {checkbox}={test_value} - parse failed")
                    failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    os.remove('test_checkbox.bin')
    return failed == 0


if __name__ == '__main__':
    success = test_checkbox_traverse_all()
    sys.exit(0 if success else 1)