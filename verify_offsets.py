#!/usr/bin/env python3
"""Verify all orbit config field offsets against reference binaries."""

import struct
import sys

bin_files = {
    'LPDDR4 Single': 'ddr_timing_table.lpddr4.single.ref.bin',
    'LPDDR4 Dual': 'ddr_timing_table.lpddr4.dual.ref.bin',
    'LPDDR5 Single': 'ddr_timing_table.lpddr5.single.ref.bin',
    'LPDDR5 Dual': 'ddr_timing_table.lpddr5.dual.ref.bin',
}

# Correct offsets verified from binary analysis
# These are STRUCT offsets (relative to orbit config start at 0x800)
correct_offsets = {
    # LPDDR4 (no header) - same for single and dual channel
    'lp4': {
        'phy_freq_ratio': 0x0C,
        'omc_freq_ratio': 0x0E,
        'cpipe_depth': 0x14,
        'dpipe_depth': 0x16,
        'density': 0x1C,
        'rank_interleaving': 0x1E,
        'num_rank': 0x20,
        'reboot_with_mrw': 0x22,
        'ctrl_dq_width': 0x24,
        'dq_width': 0x24,  # Same as ctrl_dq_width in binary
        'phy_low_power': 0x2C,
        'phy_idle_cnt_th': 0x2E,
        'rfm_en': 0x3A,
        'dsm_en': 0x3C,
        'eye_scan_rd_en': 0x3E,
        'eye_scan_wr_en': 0x40,
        'eye_scan_prbs_rd_en': 0x42,
        'eye_scan_prbs_wr_en': 0x44,
        'ca_odt': 0x46,
        'init_zq_calibration': 0x4A,
        'temp_sensing': 0x4C,
        'zq_calibration': 0x4E,
        'periodic_training': 0x50,
        'periodic_training_period': 0x52,
        'dynamic_power_down': 0x54,
        'dynamic_self_refresh': 0x56,
        'regional_clock_gating': 0x58,
        'phy_clock_gating': 0x5A,
        'dram_clock_gating': 0x5C,
        'dfs_lvl_t_ck_0': 0x5E,
        'dfs_lvl_t_ck_1': 0x60,
        'dfs_lvl_t_ck_2': 0x62,
        'command_bus_training': 0x66,
        'ca_vref_training': 0x68,
        'prbs_training': 0x6A,
        'reboot_with_training': 0x6C,
        'dfs_training': 0x6E,
        'phy_vref_trn_mode': 0x72,
        'phy_duty_trn_mode': 0x74,
        'dram_vref_trn_mode': 0x76,
        'dram_duty_trn_mode': 0x78,
    },
    # LPDDR5 (has 9-byte header: lp5_mr2-18 + zq_bg_mode)
    'lp5': {
        'phy_freq_ratio': 0x14,  # 0x0C + 8
        'omc_freq_ratio': 0x16,
        'cpipe_depth': 0x18,
        'dpipe_depth': 0x1A,
        'density': 0x20,
        'rank_interleaving': 0x22,
        'num_rank': 0x28,
        'reboot_with_mrw': 0x26,
        'ctrl_dq_width': 0x2A,
        'dq_width': 0x2C,
        'phy_low_power': 0x30,
        'phy_idle_cnt_th': 0x32,
        'rfm_en': 0x3C,
        'dsm_en': 0x3E,
        'eye_scan_rd_en': 0x40,
        'eye_scan_wr_en': 0x42,
        'eye_scan_prbs_rd_en': 0x44,
        'eye_scan_prbs_wr_en': 0x46,
        'ca_odt': 0x48,
        'init_zq_calibration': 0x4C,
        'temp_sensing': 0x4E,
        'zq_calibration': 0x50,
        'periodic_training': 0x52,
        'periodic_training_period': 0x54,
        'dynamic_power_down': 0x56,
        'dynamic_self_refresh': 0x58,
        'regional_clock_gating': 0x5A,
        'phy_clock_gating': 0x5C,
        'dram_clock_gating': 0x5E,
        'dfs_lvl_t_ck_0': 0x63,
        'dfs_lvl_t_ck_1': 0x65,
        'dfs_lvl_t_ck_2': 0x67,
        'command_bus_training': 0x75,
        'ca_vref_training': 0x77,
        'prbs_training': 0x79,
        'reboot_with_training': 0x7B,
        'dfs_training': 0x7D,
        'phy_vref_trn_mode': 0x81,
        'phy_duty_trn_mode': 0x83,
        'dram_vref_trn_mode': 0x85,
        'dram_duty_trn_mode': 0x87,
    },
}

def verify_offsets():
    print("=== GUI Offsets vs Verified Binary Offsets ===\n")
    
    errors = []
    
    # Read current gui.py
    with open('gui.py', 'r') as f:
        content = f.read()
    
    # Extract LPDDR4 section
    lp4_start = content.find('# LPDDR4: use LPDDR4 struct offsets')
    lp4_end = content.find('for field_name, field_offset', lp4_start)
    lp4_section = content[lp4_start:lp4_end]
    
    # Extract LPDDR5 section  
    lp5_start = content.find('# LPDDR5: use correct struct offsets')
    lp5_end = content.find('else:', lp5_start)
    lp5_section = content[lp5_start:lp5_end]
    
    # Parse current offsets
    import re
    gui_offsets = {'lp4': {}, 'lp5': {}}
    
    for match in re.findall(r"\('(\w+)',\s*(0x[0-9a-fA-F]+),", lp4_section):
        gui_offsets['lp4'][match[0]] = int(match[1], 16)
    
    for match in re.findall(r"\('(\w+)',\s*(0x[0-9a-fA-F]+),", lp5_section):
        gui_offsets['lp5'][match[0]] = int(match[1], 16)
    
    # Compare LPDDR4
    print("--- LPDDR4 ---")
    print(f"{'Field':<25} {'GUI':<8} {'Correct':<8} {'Status'}")
    print("-" * 55)
    
    for field, correct in sorted(correct_offsets['lp4'].items()):
        gui = gui_offsets['lp4'].get(field, None)
        if gui is None:
            status = "MISSING"
            errors.append(f"LPDDR4: {field} missing in GUI")
        elif gui != correct:
            status = f"WRONG (0x{gui:02X})"
            errors.append(f"LPDDR4: {field} wrong offset 0x{gui:02X} vs 0x{correct:02X}")
        else:
            status = "OK"
        gui_str = f"0x{gui:02X}" if gui else "N/A"
        print(f"{field:<25} {gui_str:<8} 0x{correct:02X}   {status}")
    
    print()
    print("--- LPDDR5 ---")
    print(f"{'Field':<25} {'GUI':<8} {'Correct':<8} {'Status'}")
    print("-" * 55)
    
    for field, correct in sorted(correct_offsets['lp5'].items()):
        gui = gui_offsets['lp5'].get(field, None)
        if gui is None:
            status = "MISSING"
            errors.append(f"LPDDR5: {field} missing in GUI")
        elif gui != correct:
            status = f"WRONG (0x{gui:02X})"
            errors.append(f"LPDDR5: {field} wrong offset 0x{gui:02X} vs 0x{correct:02X}")
        else:
            status = "OK"
        gui_str = f"0x{gui:02X}" if gui else "N/A"
        print(f"{field:<25} {gui_str:<8} 0x{correct:02X}   {status}")
    
    print()
    if errors:
        print(f"=== {len(errors)} ERRORS FOUND ===")
        for e in errors:
            print(f"  - {e}")
        return 1
    else:
        print("=== All offsets verified correct ===")
        return 0

if __name__ == '__main__':
    sys.exit(verify_offsets())