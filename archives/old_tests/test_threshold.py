#!/usr/bin/env python3
"""
Threshold and late field roundtrip test.
Tests: dynamic_power_down_threshold, dynamic_self_refresh_threshold, zq_calibration_period
Tests across all 4 configs: LP4 Single, LP4 Dual, LP5 Single, LP5 Dual
"""

import os
import sys
import ctypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gui import analyze_binary_file
from ddr_config_init import create_orbit_config


def test_threshold_roundtrip():
    """Test threshold values roundtrip across all 4 configs."""
    print("=" * 60)
    print("Threshold Roundtrip Test")
    print("=" * 60)
    
    configs = [
        ('lpddr4', False, 'LP4 Single'),
        ('lpddr4', True, 'LP4 Dual'),
        ('lpddr5', False, 'LP5 Single'),
        ('lpddr5', True, 'LP5 Dual'),
    ]
    
    test_values = [
        (0, 0, 48000),      # default
        (111, 222, 555),    # small values
        (10000, 20000, 10000),   # medium
        (50000, 100000, 100000),  # large
    ]
    
    all_pass = True
    
    for dram_type, two_channel, name in configs:
        for dp, ds, zq in test_values:
            cfg = create_orbit_config(dram_type, two_channel)
            cfg.dynamic_power_down_threshold = dp
            cfg.dynamic_self_refresh_threshold = ds
            cfg.zq_calibration_period = zq
            
            bin_name = f'test_threshold_{name.replace(" ", "_")}_{dp}_{ds}_{zq}.bin'
            with open(bin_name, 'wb') as f:
                f.write(b'\x00' * 0x800)
                struct_data = ctypes.string_at(ctypes.addressof(cfg), ctypes.sizeof(cfg))
                f.write(struct_data)
            
            result = analyze_binary_file(bin_name)
            if result['success']:
                orbit = result['data']['orbit']
                parsed_dp = orbit.get('dynamic_power_down_threshold')
                parsed_ds = orbit.get('dynamic_self_refresh_threshold')
                parsed_zq = orbit.get('zq_calibration_period')
                
                if parsed_dp == dp and parsed_ds == ds and parsed_zq == zq:
                    print(f"✓ {name}: dp={dp}, ds={ds}, zq={zq}")
                else:
                    print(f"✗ {name}: dp={dp}->{parsed_dp}, ds={ds}->{parsed_ds}, zq={zq}->{parsed_zq}")
                    all_pass = False
            else:
                print(f"✗ {name}: Parse failed - {result.get('message')}")
                all_pass = False
            
            if os.path.exists(bin_name):
                os.remove(bin_name)
    
    return all_pass


def test_additional_late_fields():
    """Test additional late field params."""
    print("\n" + "=" * 60)
    print("Additional Late Fields Test")
    print("=" * 60)
    
    configs = [
        ('lpddr4', False, 'LP4 Single'),
        ('lpddr5', False, 'LP5 Single'),
    ]
    
    late_field_tests = [
        ('phy_idle_cnt_th', 10000),
        ('periodic_training_period', 10000),
        ('temp_sensing_period', 10000),
        ('t_refiab', 3000000),
        ('t_refipb', 400000),
        ('t_zqcal', 800000),
    ]
    
    all_pass = True
    
    for dram_type, two_channel, name in configs:
        for field, test_value in late_field_tests:
            cfg = create_orbit_config(dram_type, two_channel)
            setattr(cfg, field, test_value)
            
            bin_name = f'test_latefield_{name.replace(" ", "_")}_{field}_{test_value}.bin'
            with open(bin_name, 'wb') as f:
                f.write(b'\x00' * 0x800)
                struct_data = ctypes.string_at(ctypes.addressof(cfg), ctypes.sizeof(cfg))
                f.write(struct_data)
            
            result = analyze_binary_file(bin_name)
            if result['success']:
                orbit = result['data']['orbit']
                parsed = orbit.get(field)
                
                if parsed == test_value:
                    print(f"✓ {name} {field}={test_value}")
                else:
                    print(f"✗ {name} {field}={test_value}->{parsed}")
                    all_pass = False
            else:
                print(f"✗ {name} {field}: Parse failed")
                all_pass = False
            
            if os.path.exists(bin_name):
                os.remove(bin_name)
    
    return all_pass


if __name__ == '__main__':
    passed = 0
    failed = 0
    
    if test_threshold_roundtrip():
        passed += 1
    else:
        failed += 1
    
    if test_additional_late_fields():
        passed += 1
    else:
        failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)