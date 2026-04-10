#!/usr/bin/env python3
"""
DDR Timing Table Generator - Web GUI
Runs locally without internet using Python standard library.
"""

import http.server
import socketserver
import json
import os
import struct
import subprocess
import sys

PORT = 5000


def get_mrr_byte_lane(dq_width):
    """Calculate mrr_byte_lane based on dq_width."""
    if dq_width == 32:
        return 0x11
    elif dq_width == 8:
        return 0xFF
    else:
        return 0x55


def safe_int(val, default=0):
    """Safely convert value to int, handling float strings."""
    if val is None or val == '':
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def is_checked(val):
    """Convert checkbox value: supports '1', '0', 'true', 'false'."""
    if val in ('1', 'true', True):
        return True
    if val in ('0', 'false', False):
        return False
    return False


def parse_timing_entries(data, dram_type):
    """Parse all timing entry params from binary."""
    # LP5 uses different entry size than LP4
    # LP4: 0x128 (296 bytes)
    # LP5: 0x15C (348 bytes)
    entry_size = 0x15C if dram_type == 'lpddr5' else 0x128
    num_entries = len(data) // entry_size
    
    # Number of densities
    num_densities = 7 if dram_type == 'lpddr4' else 10
    
    # Parse density from orbit config
    # LP4: offset 0x1C within struct = 0x81C in file
    # LP5: offset 0x24 within struct = 0x824 in file
    orbit_offset = 0x800
    density_offset = 0x1C if dram_type == 'lpddr4' else 0x24
    try:
        density = struct.unpack('<H', data[orbit_offset+density_offset:orbit_offset+density_offset+2])[0]
    except:
        density = 16
    
    # Density index mapping - find density in array
    # LP4: [2, 3, 4, 6, 8, 12, 16]
    # LP5: [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
    if dram_type == 'lpddr5':
        DENSITIES = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
    else:
        DENSITIES = [2, 3, 4, 6, 8, 12, 16]
    try:
        density_index = DENSITIES.index(density)
    except ValueError:
        density_index = 0  # Default to first density if not found
    
    # Parse density-dependent arrays
    # LP5 and LP4 density arrays are both at file-level offset 0x80
    density_start = 0x80
    
    density_arrays = {}
    try:
        density_arrays['t_rfcab'] = [struct.unpack('<H', data[density_start+i*2: density_start+2+i*2])[0] for i in range(num_densities)]
        density_arrays['t_rfcpb'] = [struct.unpack('<H', data[density_start+0x14+i*2: density_start+0x16+i*2])[0] for i in range(num_densities)]
        density_arrays['t_rfmab'] = [struct.unpack('<H', data[density_start+0x28+i*2: density_start+0x2A+i*2])[0] for i in range(num_densities)]
        density_arrays['t_rfmpb'] = [struct.unpack('<H', data[density_start+0x3C+i*2: density_start+0x3E+i*2])[0] for i in range(num_densities)]
        density_arrays['t_refdpr'] = [struct.unpack('<H', data[density_start+0x50+i*2: density_start+0x52+i*2])[0] for i in range(num_densities)]
        density_arrays['tx_pbr2pbr'] = [struct.unpack('<H', data[density_start+0x64+i*2: density_start+0x66+i*2])[0] for i in range(num_densities)]
        density_arrays['t_xsr'] = [struct.unpack('<H', data[density_start+0x78+i*2: density_start+0x7A+i*2])[0] for i in range(num_densities)]
        density_arrays['t_xsdll'] = [struct.unpack('<H', data[density_start+0x8C+i*2: density_start+0x8E+i*2])[0] for i in range(num_densities)]
        density_arrays['t_xs_fast'] = [struct.unpack('<H', data[density_start+0xA0+i*2: density_start+0xA2+i*2])[0] for i in range(num_densities)]
    except:
        density_arrays = {k: [0]*num_densities for k in ['t_rfcab','t_rfcpb','t_rfmab','t_rfmpb','t_refdpr','tx_pbr2pbr','t_xsr','t_xsdll','t_xs_fast']}
    
    density_dependent = {k: v[density_index] if density_index < len(v) else 0 for k, v in density_arrays.items()}
    
    timing_entries = []
    
    for idx in range(num_entries):
        entry_offset = idx * entry_size
        if entry_offset + 0x126 > len(data):
            break
        
        # Check enable flags (OR logic)
        write_odt = data[entry_offset + 0x10A] if entry_offset + 0x10A < len(data) else 0
        write_dbi = data[entry_offset + 0x10C] if entry_offset + 0x10C < len(data) else 0
        read_dbi = data[entry_offset + 0x10D] if entry_offset + 0x10D < len(data) else 0
        read_link_parity = data[entry_offset + 0x11F] if entry_offset + 0x11F < len(data) else 0
        write_link_parity = data[entry_offset + 0x120] if entry_offset + 0x120 < len(data) else 0
        
        if not (write_odt > 0 or write_dbi > 0 or read_dbi > 0 or read_link_parity > 0 or write_link_parity > 0):
            continue
        
        # Validate t_ck range (must be between 100-10000 ps for valid entry)
        t_ck = struct.unpack('<I', data[entry_offset+0x04:entry_offset+0x08])[0]
        if not (100 < t_ck < 10000):
            continue
        
        # LP5 has different entry structure than LP4 - use LP5-specific offsets
        # LP5 common params start at offset 0x13c (after density arrays), not 0x106
        common_offset = 0x13c if dram_type == 'lpddr5' else 0x106
        per_entry_offset = 0x146 if dram_type == 'lpddr5' else 0x110
        
        try:
            # Get wck_ratio for period conversion from correct offset 0x13c
            wck_ratio = data[entry_offset + 0x13c] if dram_type == 'lpddr5' else 4
            if wck_ratio == 0:
                wck_ratio = 4
            
            t_ck_val = struct.unpack('<I', data[entry_offset+0x04:entry_offset+0x08])[0]
            
            entry = {
                'entry': idx,
                't_ck': t_ck_val,
                't_ck_display': t_ck_val // wck_ratio if dram_type == 'lpddr5' else t_ck_val,
                'freq': struct.unpack('<I', data[entry_offset+0x00:entry_offset+0x04])[0],
                'timing_zqcal': struct.unpack('<I', data[entry_offset+0x08:entry_offset+0x0C])[0],
                'timing_param': [struct.unpack('<I', data[entry_offset+0x0C+i*4:entry_offset+0x10+i*4])[0] for i in range(21)],
                'timing_derate': [
                    struct.unpack('<I', data[entry_offset+0x60:entry_offset+0x64])[0],
                    struct.unpack('<I', data[entry_offset+0x64:entry_offset+0x68])[0]
                ],
                'dfi_timing_param': [struct.unpack('<I', data[entry_offset+0x68+i*4:entry_offset+0x6C+i*4])[0] for i in range(8)],
                # Common params - use LP5-specific offsets if needed
                'wck_ratio': data[entry_offset + common_offset],
                'tlp_resp': data[entry_offset + common_offset + 1] if dram_type == 'lpddr5' else data[entry_offset + 0x107],
                'adc': data[entry_offset + common_offset + 2] if dram_type == 'lpddr5' else data[entry_offset + 0x108],
                'dll_enable': data[entry_offset + common_offset + 3] if dram_type == 'lpddr5' else data[entry_offset + 0x109],
                'write_odt': data[entry_offset + common_offset + 4] if dram_type == 'lpddr5' else data[entry_offset + 0x10A],
                'nt_odt': data[entry_offset + common_offset + 5] if dram_type == 'lpddr5' else data[entry_offset + 0x10B],
                'write_dbi': data[entry_offset + common_offset + 6] if dram_type == 'lpddr5' else data[entry_offset + 0x10C],
                'read_dbi': data[entry_offset + common_offset + 7] if dram_type == 'lpddr5' else data[entry_offset + 0x10D],
                'wpste': data[entry_offset + common_offset + 8] if dram_type == 'lpddr5' else data[entry_offset + 0x10E],
                'rpste': data[entry_offset + common_offset + 9] if dram_type == 'lpddr5' else data[entry_offset + 0x10F],
                # Per-entry params
                'rl': data[entry_offset + per_entry_offset],
                'wl': data[entry_offset + per_entry_offset + 1],
                'mr_rl': data[entry_offset + per_entry_offset + 2],
                'mr_wl': data[entry_offset + per_entry_offset + 3],
                'mr_wr': data[entry_offset + per_entry_offset + 4],
                'mr_rtp': data[entry_offset + per_entry_offset + 5],
                'mr_cal': data[entry_offset + per_entry_offset + 6],
                'mr_tccd_l': data[entry_offset + per_entry_offset + 7],
                'bank_mode': data[entry_offset + per_entry_offset + 8],
                'wck_fm': data[entry_offset + per_entry_offset + 9],
                'rdqs_pst_mode': data[entry_offset + per_entry_offset + 10],
                'rdqs_pst': data[entry_offset + per_entry_offset + 11],
                'rdqs_pre': data[entry_offset + per_entry_offset + 12],
                'wck_pst': data[entry_offset + per_entry_offset + 13],
                'wck_on': data[entry_offset + per_entry_offset + 14],
                'read_link_parity': data[entry_offset + per_entry_offset + 15],
                'write_link_parity': data[entry_offset + per_entry_offset + 16],
                't_rtw': data[entry_offset + per_entry_offset + 17],
                't_wtr_a': data[entry_offset + per_entry_offset + 18],
                't_wtr': data[entry_offset + per_entry_offset + 19],
                't_rc': data[entry_offset + per_entry_offset + 20],
                'trddata_en': data[entry_offset + per_entry_offset + 21],
            }
            timing_entries.append(entry)
        except:
            continue
    
    # Get common params from first entry
    common = {}
    if timing_entries:
        first = timing_entries[0]
        common = {
            'tlp_resp': first.get('tlp_resp', 0),
            'dll_enable': first.get('dll_enable', 0),
            'write_odt': first.get('write_odt', 0),
            'nt_odt': first.get('nt_odt', 0),
            'write_dbi': first.get('write_dbi', 0),
            'read_dbi': first.get('read_dbi', 0),
            'wpste': first.get('wpste', 0),
            'rpste': first.get('rpste', 0),
        }
    
    return {
        'entries': timing_entries,
        'common': common,
        'density_dependent': density_dependent,
        'selected_density': density,
    }


def analyze_binary_file(file_path, dram_type_override=None):
    """Analyze binary file with optional DRAM type override."""
    if not os.path.exists(file_path):
        return {'success': False, 'message': f'File not found: {file_path}'}
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        return {'success': False, 'message': f'Error reading file: {str(e)}'}
    
    file_size = len(data)
    
    # Determine DRAM type and size
    # Methods: 1) file size (most reliable), 2) dual channel flag
    is_lpddr5 = False
    is_dual_channel = False
    
    # Method 1: File size thresholds (most reliable)
    # LP4 single: 5096, LP5 single: 5104 (diff of 8 bytes for lp5 header)
    # LP4 dual: 7864, LP5 dual: 7872
    if file_size >= 7860:
        is_dual_channel = True
        # Single vs dual already detected, now check LP4 vs LP5
        # Use tighter thresholds: LP4 dual: ~7864, LP5 dual: ~7872
        if file_size >= 7870:
            is_lpddr5 = True
    elif file_size >= 5090 and file_size < 5200:
        is_dual_channel = False
        if file_size >= 5100:
            is_lpddr5 = True  # 5104 = LP5 single
        else:
            is_lpddr5 = False  # 5096 = LP4 single
    elif file_size >= 3050 and file_size < 4000:
        is_dual_channel = False
        is_lpddr5 = True  # Small LP5 files
    elif file_size < 3000:
        return {'success': False, 'message': 'File too small to be valid binary: %d bytes' % file_size}
    
    # Method 2: Verify dual channel via phy_base_addr_id[2]
    # Only trust this if value is clearly non-zero (not just any value)
    # LP4: 0x8E0, LP5: 0x8E8
    if file_size > 0x800 + 0xE0:
        dual_check_offset = 0x8E8 if is_lpddr5 else 0x8E0
        phy_addr_id_2 = struct.unpack('<I', data[dual_check_offset:dual_check_offset+4])[0]
        # Only mark as dual channel if value is >= 0x100000 (typical base address)
        if phy_addr_id_2 >= 0x100000:
            is_dual_channel = True
    
    dram_type = 'lpddr5' if is_lpddr5 else 'lpddr4'
    
    # Apply manual override if specified
    if dram_type_override and dram_type_override != 'auto':
        dram_type = dram_type_override
    
    # Parse timing table for periods and lecc settings
    periods = []
    read_lecc_upto = 0
    write_lecc_upto = 0
    write_odt_upto = 0
    read_dbi_upto = 0
    write_dbi_upto = 0
    # LP5 uses different entry size than LP4
    entry_size = 0x15C if is_lpddr5 else 0x128
    max_entries = 8
    
    for i in range(max_entries):
        offset = i * entry_size
        if offset + 4 > len(data):
            break
        t_ck = struct.unpack('<I', data[offset+4:offset+8])[0] if len(data) >= offset + 8 else 0
        
        # Use raw t_ck for detection (t_ck values are in range 300-5000)
        # But store converted t_wck for display
        period_value = t_ck
        
        if 300 <= period_value <= 5000:
            # For LP5: convert to t_wck for display (user input period)
            # Use per-entry wck_ratio from offset 0x13c
            if is_lpddr5:
                wck_ratio = data[offset + 0x13c] if offset + 0x13c < len(data) else 4
                if wck_ratio > 0:
                    display_period = t_ck // wck_ratio
                else:
                    display_period = t_ck
            else:
                display_period = t_ck
            periods.append(display_period)
            if len(data) >= offset + 192:
                # Timing feature flags
                # write_odt at offset +0x9E (158)
                # write_dbi at offset +0xA0 (160)
                # read_dbi at offset +0xA1 (161)
                # read_link_parity at offset +0x11F (191)
                # write_link_parity at offset +0x120 (192)
                write_odt_flag = data[offset + 158]
                write_dbi_flag = data[offset + 160]
                read_dbi_flag = data[offset + 161]
                read_link_parity = data[offset + 0x11F]
                write_link_parity = data[offset + 0x120]
                
                # Use flag > 0 to avoid false positives from garbage values in binary
                if write_odt_flag > 0 and t_ck > write_odt_upto:
                    write_odt_upto = t_ck
                if write_dbi_flag > 0 and t_ck > write_dbi_upto:
                    write_dbi_upto = t_ck
                if read_dbi_flag > 0 and t_ck > read_dbi_upto:
                    read_dbi_upto = t_ck
                if read_link_parity > 0 and t_ck > read_lecc_upto:
                    read_lecc_upto = t_ck
                if write_link_parity > 0 and t_ck > write_lecc_upto:
                    write_lecc_upto = t_ck
    
    if not periods:
        periods = [471, 938, 1631, 2500]  # Default
    
    # If we only got 1 period (common for single-channel binaries), use defaults
    if len(periods) == 1:
        if is_lpddr5:
            # LPDDR5 default periods (t_wck values, before WCK conversion)
            periods = [314, 418, 556, 2500]
        else:
            # LPDDR4 default periods
            periods = [471, 938, 1631, 2500]
    
    # Parse orbit config at offset 0x800
    orbit_offset = 0x800
    
    # First, parse orbit config fields
    orbit_data = {}
    try:
        with open(file_path, 'rb') as f:
            # dfs_lvl_t_ck offsets differ by DRAM type
            # LPDDR4: 0x85e, 0x860, 0x862 (orbit config area)
            # LPDDR5: 0x864, 0x866, 0x868 (orbit config area)
            # LPDDR5 struct has different offsets than LPDDR4
            # Get offsets dynamically based on dram type
            if is_lpddr5:
                # LPDDR5: use correct struct offsets
                # dfs_lvl_t_ck at 0x64, 0x66, 0x68 (not 0x63, 0x65, 0x67)
                dfs_offsets = (0x64, 0x66, 0x68)
                # Threshold offsets from C struct
                # LP5 Single: dp_threshold=0xE6, ds_threshold=0xE2
                # LP5 Dual: dp_threshold=0xF6, ds_threshold=0xF2
                dp_thresh_offset = 0xf6 if is_dual_channel else 0xe6
                ds_thresh_offset = 0xf2 if is_dual_channel else 0xe2
                fields_to_read = [
                    # Pipe config (LPDDR5 struct starts at offset 0x14)
                    ('phy_freq_ratio', 0x14, '<H'),
                    ('omc_freq_ratio', 0x16, '<H'),
                    ('cpipe_depth', 0x18, '<H'),
                    ('dpipe_depth', 0x1a, '<H'),
                    ('dram_t_ck', 0x90, '<I'),  # LP5: value at 0x890 = 1256
                    ('rclk_t_ck', 0x84, '<I'),  # LP5: value at 0x884 = 41666
                    ('boot_t_ck', 0x88, '<I'),  # LP5: value at 0x888 = 20000
                    
                    # Basic geometry
                    ('density', 0x24, '<H'),
                    ('rank_interleaving', 0x26, '<H'),
                    ('num_rank', 0x28, '<H'),
                    ('ctrl_dq_width', 0x2a, '<H'),
                    ('dq_width', 0x2c, '<H'),
                    
                    # Mode control
                    ('reboot_with_mrw', 0x2a, '<H'),
                    ('rfm_en', 0x40, '<H'),
                    ('dsm_en', 0x42, '<H'),
                    ('ca_odt', 0x4c, '<H'),
                    
                    # Training enable (LP5: +6 offset from LP4)
                    ('eye_scan_rd_en', 0x44, '<H'),
                    ('eye_scan_wr_en', 0x46, '<H'),
                    ('eye_scan_prbs_rd_en', 0x48, '<H'),
                    ('eye_scan_prbs_wr_en', 0x4a, '<H'),
                    ('init_zq_calibration', 0x50, '<H'),
                    ('command_bus_training', 0x6c, '<H'),
                    ('ca_vref_training', 0x6e, '<H'),
                    ('prbs_training', 0x70, '<H'),
                    ('reboot_with_training', 0x72, '<H'),
                    ('dfs_training', 0x74, '<H'),
                    ('phy_vref_trn_mode', 0x76, '<H'),
                    ('phy_duty_trn_mode', 0x78, '<H'),
                    ('dram_vref_trn_mode', 0x7a, '<H'),
                    ('dram_duty_trn_mode', 0x7c, '<H'),
                    
                    # Power management (LP5: +6 offset from LP4)
                    ('regional_clock_gating', 0x5e, '<H'),
                    ('phy_clock_gating', 0x60, '<H'),
                    ('dram_clock_gating', 0x62, '<H'),
                    
                    # Dynamic power management (LP5: +6 offset from LP4)
                    ('phy_low_power', 0x34, '<H'),
                    ('phy_idle_cnt_th', 0x36, '<H'),
                    ('dynamic_power_down', 0x5a, '<H'),
                    ('dynamic_self_refresh', 0x5c, '<H'),
                    ('dynamic_power_down_threshold', dp_thresh_offset, '<I'),
                    ('dynamic_self_refresh_threshold', ds_thresh_offset, '<I'),
                    
                    # Timing features (LP5: +6 offset from LP4)
                    ('temp_sensing', 0x52, '<H'),
                    ('zq_calibration', 0x54, '<H'),
                    ('periodic_training', 0x56, '<H'),
                    ('periodic_training_period', 0x58, '<H'),
                    
                    # DFS timing
                    ('dfs_lvl_t_ck_0', dfs_offsets[0], '<H'),
                    ('dfs_lvl_t_ck_1', dfs_offsets[1], '<H'),
                    ('dfs_lvl_t_ck_2', dfs_offsets[2], '<H'),
                    
                    # Late fields - using ctypes struct offsets for LPDDR5
                    # LP5 density_code at 0x80 (not 0xA5)
                    ('density_code', 0x80, '<I'),
                    ('zq_calibration_period', 0xFC if is_dual_channel else 0xEC, '<I'),
                    ('temp_sensing_period', 0x104 if is_dual_channel else 0xF4, '<I'),
                    ('t_refipb', 0x108 if is_dual_channel else 0xF8, '<I'),
                    ('t_refiab', 0x10C if is_dual_channel else 0xFC, '<I'),
                    ('t_zqcal', 0x110 if is_dual_channel else 0x100, '<I'),
                    ('mrr_byte_lane', 0x118 if is_dual_channel else 0x108, '<H'),
                ]
            else:
                # LPDDR4: use LPDDR4 struct offsets (no lp5 header)
                # Correct offsets from ctypes struct
                dfs_offsets = (0x5E, 0x60, 0x62)
                # Threshold offsets - verify against binary data
                # LP4 Single: dp=0xE0 (file 0x8E0), ds=0xDC (file 0x8DC) - both should read 0
                # LP4 Dual: unknown, try 0xEC/0xF0
                dp_thresh_offset = 0xf0 if is_dual_channel else 0xe0
                ds_thresh_offset = 0xec if is_dual_channel else 0xdc
                fields_to_read = [
                    # Pipe config
                    ('phy_freq_ratio', 0x0C, '<H'),
                    ('omc_freq_ratio', 0x0E, '<H'),
                    ('cpipe_depth', 0x14, '<H'),
                    ('dpipe_depth', 0x16, '<H'),
                    ('dram_t_ck', 0x88, '<I'),
                    ('rclk_t_ck', 0x7C, '<I'),
                    ('boot_t_ck', 0x80, '<I'),
                    
                    # Basic geometry
                    ('density', 0x1C, '<H'),
                    ('rank_interleaving', 0x1E, '<H'),
                    ('num_rank', 0x20, '<H'),
                    ('ctrl_dq_width', 0x24, '<H'),
                    ('dq_width', 0x24, '<H'),
                    
                    # Mode control
                    ('reboot_with_mrw', 0x22, '<H'),
                    ('rfm_en', 0x3A, '<H'),
                    ('dsm_en', 0x3C, '<H'),
                    ('ca_odt', 0x46, '<H'),
                    
                    # Training enable
                    ('eye_scan_rd_en', 0x3E, '<H'),
                    ('eye_scan_wr_en', 0x40, '<H'),
                    ('eye_scan_prbs_rd_en', 0x42, '<H'),
                    ('eye_scan_prbs_wr_en', 0x44, '<H'),
                    ('init_zq_calibration', 0x4A, '<H'),
                    ('command_bus_training', 0x66, '<H'),
                    ('ca_vref_training', 0x68, '<H'),
                    ('prbs_training', 0x6A, '<H'),
                    ('reboot_with_training', 0x6C, '<H'),
                    ('dfs_training', 0x6E, '<H'),
                    ('phy_vref_trn_mode', 0x70, '<H'),
                    ('phy_duty_trn_mode', 0x72, '<H'),
                    ('dram_vref_trn_mode', 0x74, '<H'),
                    ('dram_duty_trn_mode', 0x76, '<H'),
                    
                    # Power management
                    ('regional_clock_gating', 0x58, '<H'),
                    ('phy_clock_gating', 0x5A, '<H'),
                    ('dram_clock_gating', 0x5C, '<H'),
                    
                    # Dynamic power management
                    ('phy_low_power', 0x2C, '<H'),
                    ('phy_idle_cnt_th', 0x2E, '<H'),
                    ('dynamic_power_down', 0x54, '<H'),
                    ('dynamic_self_refresh', 0x56, '<H'),
                    ('dynamic_power_down_threshold', dp_thresh_offset, '<I'),
                    ('dynamic_self_refresh_threshold', ds_thresh_offset, '<I'),
                    
                    # Timing features
                    ('temp_sensing', 0x4C, '<H'),
                    ('zq_calibration', 0x4E, '<H'),
                    ('periodic_training', 0x50, '<H'),
                    ('periodic_training_period', 0x52, '<H'),
                    
                    # DFS timing
                    ('dfs_lvl_t_ck_0', dfs_offsets[0], '<H'),
                    ('dfs_lvl_t_ck_1', dfs_offsets[1], '<H'),
                    ('dfs_lvl_t_ck_2', dfs_offsets[2], '<H'),
                    
                    # Late fields - using ctypes struct offsets
                    # These are STRUCT offsets (relative to 0x800 orbit config start)
                    # Correct ctypes struct offsets:
                    # LP4 Single: zq=0xE3, temp=0xEB, t_refipb=0xEF, t_refiab=0xF3, t_zq=0xF7, mrr=0xFF
                    # LP4 Dual: zq=0xF3, temp=0xFB, t_refipb=0xFF, t_refiab=0x103, t_zq=0x107, mrr=0x10F
                    # ctypes struct offsets (LP4: no lp5 header, LP5: has lp5 header)
                    # LP4 Single: zq=0xE4, temp=0xEC, t_refipb=0xF0, t_refiab=0xF4, t_zq=0xF8, mrr=0x100
                    # LP4 Dual: zq=0xF4, temp=0xFC, t_refipb=0x100, t_refiab=0x104, t_zq=0x108, mrr=0x110
                    # LP5 Single: zq=0xEC, temp=0xF4, t_refipb=0xF8, t_refiab=0xFC, t_zq=0x100, mrr=0x108
                    # LP5 Dual: zq=0xFC, temp=0x104, t_refipb=0x108, t_refiab=0x10C, t_zq=0x110, mrr=0x118
                    ('zq_calibration_period', 
                     0xFC if (is_lpddr5 and is_dual_channel) else 
                     0xEC if is_lpddr5 else
                     0xF4 if is_dual_channel else 0xE4, '<I'),
                    ('temp_sensing_period', 
                     0x104 if (is_lpddr5 and is_dual_channel) else
                     0xF4 if is_lpddr5 else
                     0xFC if is_dual_channel else 0xEC, '<I'),
                    ('t_refipb', 
                     0x108 if (is_lpddr5 and is_dual_channel) else
                     0xF8 if is_lpddr5 else
                     0x100 if is_dual_channel else 0xF0, '<I'),
                    ('t_refiab', 
                     0x10C if (is_lpddr5 and is_dual_channel) else
                     0xFC if is_lpddr5 else
                     0x104 if is_dual_channel else 0xF4, '<I'),
                    ('t_zqcal', 
                     0x110 if (is_lpddr5 and is_dual_channel) else
                     0x100 if is_lpddr5 else
                     0x108 if is_dual_channel else 0xF8, '<I'),
                    ('mrr_byte_lane', 
                     0x118 if (is_lpddr5 and is_dual_channel) else
                     0x108 if is_lpddr5 else
                     0x110 if is_dual_channel else 0x100, '<H'),
                ]
            
            for field_name, field_offset, fmt in fields_to_read:
                # All fields use orbit_offset base (0x800)
                f.seek(orbit_offset + field_offset)
                bytes_read = f.read(struct.calcsize(fmt))
                if bytes_read:
                    value = struct.unpack(fmt, bytes_read)[0]
                    if 'dfs_lvl_t_ck' in field_name:
                        # Only include valid values (300-5000 ps range)
                        if 300 <= value <= 5000:
                            if 'dfs_lvl_t_ck' not in orbit_data:
                                orbit_data['dfs_lvl_t_ck'] = []
                            orbit_data['dfs_lvl_t_ck'].append(value)
                    else:
                        orbit_data[field_name] = value
    except Exception as e:
        pass  # Use defaults if parsing fails
    
    result = {
        'success': True,
        'data': {
            'file_path': file_path,
            'file_size': file_size,
            'dram_type': dram_type,
            'two_channel': is_dual_channel,
            
            'basic': {
                'dram_type': dram_type,
                'phy_name': 'sphy-v9r8',
                'dq_width': orbit_data.get('dq_width', 16),
                'speed_bin': '4266' if dram_type == 'lpddr4' else '6400',
                'periods': ' '.join(map(str, periods)),
                'min_dram_tck': 314,
                'dram_tck': orbit_data.get('dram_t_ck', periods[0] if periods else 471),
            },
            
            'pipe': {
                'cpipe_depth': orbit_data.get('cpipe_depth', 1),
                'dpipe_depth': orbit_data.get('dpipe_depth', 1),
                'omc_freq_ratio': orbit_data.get('omc_freq_ratio', 1 if dram_type == 'lpddr5' else 2),
                'phy_freq_ratio': orbit_data.get('phy_freq_ratio', 1 if dram_type == 'lpddr5' else 2),
                'wire_length': 10,
            },
            
            'timing': {
                'write_odt_upto': 1250 if dram_type == 'lpddr4' else 10000,
                'read_dbi_upto': 10000,
                'write_dbi_upto': 10000,
                'read_lecc_upto': read_lecc_upto,
                'write_lecc_upto': write_lecc_upto,
            },
            
            'timing_entries': parse_timing_entries(data, dram_type),
            
            'orbit': {}
        }
    }
    
    # Set orbit config - use parsed values from binary
    # Non-parseable fields (not in binary, generated at runtime):
    non_parseable_fields = [
        'variable-trrd', 'txsr-as-1st-ed', 'enhanced-nt-odt', 'wire-length',
        'wdqs-ctrl-mode', 'rpste-upto', 'wpste-upto', 'nt-odt-upto',
        'bg-mode-upto', 'wck-always-on-from', 'wck-always-on-upto',
        'wck-1to4-upto', 'wck-hf-upto', 'wck-pst1-upto', 'wck-pst2-upto',
        'rdqs-pst1-upto', 'rdqs-pst2-upto',
    ]
    
    result['data']['orbit'] = {
        'density': orbit_data.get('density', 16),
        'density_code': orbit_data.get('density_code', 0),
        'cpipe_depth': orbit_data.get('cpipe_depth', 1),
        'dpipe_depth': orbit_data.get('dpipe_depth', 1),
        'rank_interleaving': orbit_data.get('rank_interleaving', 1),
        'num_rank': orbit_data.get('num_rank', 2),
        'dfs_lvl_t_ck': orbit_data.get('dfs_lvl_t_ck', [938, 1631, 2500]),
        'two_channel': 1 if is_dual_channel else 0,
        'ctrl_dq_width': orbit_data.get('ctrl_dq_width', 16),
        'dq_width': orbit_data.get('dq_width', 16),
        'dram_t_ck': orbit_data.get('dram_t_ck', 0),
        'rclk_t_ck': orbit_data.get('rclk_t_ck', 0),
        'boot_t_ck': orbit_data.get('boot_t_ck', 0),
        'reboot_with_mrw': orbit_data.get('reboot_with_mrw', 0),
        'rfm_en': orbit_data.get('rfm_en', 0),
        'dsm_en': orbit_data.get('dsm_en', 0),
        'ca_odt': orbit_data.get('ca_odt', 0),
        'eye_scan_rd_en': orbit_data.get('eye_scan_rd_en', 0),
        'eye_scan_wr_en': orbit_data.get('eye_scan_wr_en', 0),
        'eye_scan_prbs_rd_en': orbit_data.get('eye_scan_prbs_rd_en', 0),
        'eye_scan_prbs_wr_en': orbit_data.get('eye_scan_prbs_wr_en', 0),
        'init_zq_calibration': orbit_data.get('init_zq_calibration', 0),
        'command_bus_training': orbit_data.get('command_bus_training', 0),
        'ca_vref_training': orbit_data.get('ca_vref_training', 0),
        'prbs_training': orbit_data.get('prbs_training', 0),
        'reboot_with_training': orbit_data.get('reboot_with_training', 0),
        'dfs_training': orbit_data.get('dfs_training', 0),
        'phy_vref_trn_mode': orbit_data.get('phy_vref_trn_mode', 0),
        'phy_duty_trn_mode': orbit_data.get('phy_duty_trn_mode', 0),
        'dram_vref_trn_mode': orbit_data.get('dram_vref_trn_mode', 0),
        'dram_duty_trn_mode': orbit_data.get('dram_duty_trn_mode', 0),
        'regional_clock_gating': orbit_data.get('regional_clock_gating', 0),
        'phy_clock_gating': orbit_data.get('phy_clock_gating', 0),
        'dram_clock_gating': orbit_data.get('dram_clock_gating', 0),
        'temp_sensing': orbit_data.get('temp_sensing', 0),
        'zq_calibration': orbit_data.get('zq_calibration', 0),
        'periodic_training': orbit_data.get('periodic_training', 0),
        'periodic_training_period': orbit_data.get('periodic_training_period', 0),
        'zq_calibration_period': orbit_data.get('zq_calibration_period') or 48000,
        'temp_sensing_period': orbit_data.get('temp_sensing_period', 32000),
        't_refiab': orbit_data.get('t_refiab', 3904000),
        't_refipb': orbit_data.get('t_refipb', 488000),
        't_zqcal': orbit_data.get('t_zqcal', 1000000),
        'mrr_byte_lane': hex(orbit_data.get('mrr_byte_lane', 0x55)),
        'phy_low_power': orbit_data.get('phy_low_power', 0),
        'phy_idle_cnt_th': orbit_data.get('phy_idle_cnt_th', 0),
        'dynamic_power_down': orbit_data.get('dynamic_power_down', 0),
        'dynamic_self_refresh': orbit_data.get('dynamic_self_refresh', 0),
        'dynamic_power_down_threshold': orbit_data.get('dynamic_power_down_threshold', 0),
        'dynamic_self_refresh_threshold': orbit_data.get('dynamic_self_refresh_threshold', 0),
        'non_parseable_fields': non_parseable_fields,
    }
    
    return result


class DDRHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            html_path = os.path.join(os.path.dirname(__file__), 'templates', 'gui.html')
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, 'GUI template not found')
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/generate':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = json.loads(body)
            
            message = []
            success = True
            
            # Helper function to convert param to int (handles float strings)
            def to_int(val):
                if val is None or val == '':
                    return None
                try:
                    return int(float(val))
                except (ValueError, TypeError):
                    return None
            
            # Build gen_timing_params command
            cmd = [sys.executable, 'gen_timing_params']
            cmd.extend(['--dram-type', params.get('dram-type', 'lpddr4')])
            cmd.extend(['--densities', str(to_int(params.get('orbit-config-density')) or 16)])
            cmd.extend(['--phy-name', params.get('phy-name', 'sphy-v9r8')])
            cmd.extend(['--speed-bin', params.get('speed-bin', '4266')])
            dq_width = params.get('dq-width', '16')
            cmd.extend(['--dq-width', dq_width])
            
            # Pipe params - convert to int
            cpipe = to_int(params.get('cpipe-depth'))
            dpipe = to_int(params.get('dpipe-depth'))
            cmd.extend(['--cpipe-depth', str(cpipe if cpipe else 1)])
            cmd.extend(['--dpipe-depth', str(dpipe if dpipe else 1)])
            
            # Frequency ratios - use DRAM-type-specific defaults
            dram_type = params.get('dram-type', 'lpddr4')
            if dram_type == 'lpddr5':
                default_omc_freq = 1
                default_phy_freq = 1
            else:
                default_omc_freq = 2
                default_phy_freq = 2
            cmd.extend(['--omc-freq-ratio', str(params.get('omc-freq-ratio', default_omc_freq))])
            cmd.extend(['--phy-freq-ratio', str(params.get('phy-freq-ratio', default_phy_freq))])
            
            # Timing params - convert to int
            if params.get('wire-length'):
                val = to_int(params.get('wire-length'))
                if val:
                    cmd.extend(['--wire-length', str(val)])
            write_odt = to_int(params.get('write-odt-upto'))
            if write_odt is not None:
                cmd.extend(['--write-odt-upto', str(write_odt)])
            read_dbi = to_int(params.get('read-dbi-upto'))
            if read_dbi is not None:
                cmd.extend(['--read-dbi-upto', str(read_dbi)])
            write_dbi = to_int(params.get('write-dbi-upto'))
            if write_dbi is not None:
                cmd.extend(['--write-dbi-upto', str(write_dbi)])
            min_dram = to_int(params.get('min-dram-tck'))
            if min_dram is not None:
                cmd.extend(['--min-dram-tck', str(min_dram)])
            dram_tck = to_int(params.get('dram-tck'))
            if dram_tck is not None:
                cmd.extend(['--dram-tck', str(dram_tck)])
            read_lecc = to_int(params.get('read-lecc-upto'))
            if read_lecc is not None:
                cmd.extend(['--read-lecc-upto', str(read_lecc)])
            write_lecc = to_int(params.get('write-lecc-upto'))
            if write_lecc is not None:
                cmd.extend(['--write-lecc-upto', str(write_lecc)])
            
            # LPDDR4 specific
            if dram_type == 'lpddr4':
                wdqs = to_int(params.get('wdqs-ctrl-mode'))
                if wdqs:
                    cmd.extend(['--wdqs-ctrl-mode', str(wdqs)])
                if is_checked(params.get('variable-trrd')):
                    cmd.append('--variable-trrd')
                if is_checked(params.get('txsr-as-1st-ed')):
                    cmd.append('--txsr-as-1st-ed')
                rpste = to_int(params.get('rpste-upto'))
                if rpste is not None:
                    cmd.extend(['--rpste-upto', str(rpste)])
                wpste = to_int(params.get('wpste-upto'))
                if wpste is not None:
                    cmd.extend(['--wpste-upto', str(wpste)])
            else:
                # LPDDR5 specific
                wck_1to4 = to_int(params.get('wck-1to4-upto'))
                if wck_1to4 is not None:
                    cmd.extend(['--wck-1to4-upto', str(wck_1to4)])
                wck_from = to_int(params.get('wck-always-on-from'))
                if wck_from is not None:
                    cmd.extend(['--wck-always-on-from', str(wck_from)])
                wck_upto = to_int(params.get('wck-always-on-upto'))
                if wck_upto is not None:
                    cmd.extend(['--wck-always-on-upto', str(wck_upto)])
                nt_odt = to_int(params.get('nt-odt-upto'))
                if nt_odt is not None:
                    cmd.extend(['--nt-odt-upto', str(nt_odt)])
                if is_checked(params.get('enhanced-nt-odt')):
                    cmd.append('--enhanced-nt-odt')
                bg_mode = to_int(params.get('bg-mode-upto'))
                if bg_mode is not None:
                    cmd.extend(['--bg-mode-upto', str(bg_mode)])
                wck_hf = to_int(params.get('wck-hf-upto'))
                if wck_hf is not None:
                    cmd.extend(['--wck-hf-upto', str(wck_hf)])
                wck_pst1 = to_int(params.get('wck-pst1-upto'))
                if wck_pst1 is not None:
                    cmd.extend(['--wck-pst1-upto', str(wck_pst1)])
                wck_pst2 = to_int(params.get('wck-pst2-upto'))
                if wck_pst2 is not None:
                    cmd.extend(['--wck-pst2-upto', str(wck_pst2)])
                rdqs_pst1 = to_int(params.get('rdqs-pst1-upto'))
                if rdqs_pst1 is not None:
                    cmd.extend(['--rdqs-pst1-upto', str(rdqs_pst1)])
                rdqs_pst2 = to_int(params.get('rdqs-pst2-upto'))
                if rdqs_pst2 is not None:
                    cmd.extend(['--rdqs-pst2-upto', str(rdqs_pst2)])
            
            # Orbit config
            if is_checked(params.get('two-channel')):
                cmd.append('--two-channel')
            orbit_density = to_int(params.get('orbit-config-density'))
            if orbit_density:
                cmd.extend(['--orbit-config-density', str(orbit_density)])
            byte_mode = to_int(params.get('orbit-byte-mode'))
            if byte_mode is not None:
                cmd.extend(['--orbit-byte-mode', str(byte_mode)])
            mixed = to_int(params.get('orbit-mixed'))
            if mixed is not None:
                cmd.extend(['--orbit-mixed', str(mixed)])
            if is_checked(params.get('orbit-rank-interleaving')):
                cmd.extend(['--orbit-rank-interleaving', '1'])
            num_rank = to_int(params.get('orbit-num-rank'))
            if num_rank:
                cmd.extend(['--orbit-num-rank', str(num_rank)])
            if is_checked(params.get('orbit-reboot-with-mrw')):
                cmd.extend(['--orbit-reboot-with-mrw', '1'])
            if is_checked(params.get('orbit-rfm-en')):
                cmd.extend(['--orbit-rfm-en', '1'])
            # dsm-en only for LPDDR5
            if dram_type == 'lpddr5' and is_checked(params.get('orbit-dsm-en')):
                cmd.extend(['--orbit-dsm-en', '1'])
            if is_checked(params.get('orbit-ca-odt')):
                cmd.extend(['--orbit-ca-odt', '1'])
            
            # Training enable parameters (newly added CLI mappings)
            if is_checked(params.get('eye-scan-rd-en')):
                cmd.extend(['--orbit-eye-scan-rd-en', '1'])
            if is_checked(params.get('eye-scan-wr-en')):
                cmd.extend(['--orbit-eye-scan-wr-en', '1'])
            if is_checked(params.get('eye-scan-prbs-rd-en')):
                cmd.extend(['--orbit-eye-scan-prbs-rd-en', '1'])
            if is_checked(params.get('eye-scan-prbs-wr-en')):
                cmd.extend(['--orbit-eye-scan-prbs-wr-en', '1'])
            if is_checked(params.get('phy-vref-trn-mode')):
                cmd.extend(['--orbit-phy-vref-trn-mode', '1'])
            if is_checked(params.get('phy-duty-trn-mode')):
                cmd.extend(['--orbit-phy-duty-trn-mode', '1'])
            if is_checked(params.get('dram-vref-trn-mode')):
                cmd.extend(['--orbit-dram-vref-trn-mode', '1'])
            if is_checked(params.get('dram-duty-trn-mode')):
                cmd.extend(['--orbit-dram-duty-trn-mode', '1'])
            if is_checked(params.get('command-bus-training')):
                cmd.extend(['--orbit-command-bus-training', '1'])
            if is_checked(params.get('ca-vref-training')):
                cmd.extend(['--orbit-ca-vref-training', '1'])
            if is_checked(params.get('prbs-training')):
                cmd.extend(['--orbit-prbs-training', '1'])
            if is_checked(params.get('reboot-with-training')):
                cmd.extend(['--orbit-reboot-with-training', '1'])
            if is_checked(params.get('init-zq-calibration')):
                cmd.extend(['--orbit-init-zq-calibration', '1'])
            if is_checked(params.get('zq-calibration')):
                cmd.extend(['--orbit-zq-calibration', '1'])
            if is_checked(params.get('dfs-training')):
                cmd.extend(['--orbit-dfs-training', '1'])
            if is_checked(params.get('phy-clock-gating')):
                cmd.extend(['--orbit-phy-clock-gating', '1'])
            
            # PHY idle counter threshold
            phy_idle_cnt_th = to_int(params.get('phy-idle-cnt-th'))
            if phy_idle_cnt_th is not None:
                cmd.extend(['--orbit-phy-idle-cnt-th', str(phy_idle_cnt_th)])
            
            # Dynamic power management parameters
            if is_checked(params.get('dynamic-power-down')):
                cmd.extend(['--orbit-dynamic-power-down', '1'])
                dyn_pwr_th = to_int(params.get('dynamic-power-down-threshold'))
                if dyn_pwr_th is not None:
                    cmd.extend(['--orbit-dynamic-power-down-threshold', str(dyn_pwr_th)])
            if is_checked(params.get('dynamic-self-refresh')):
                cmd.extend(['--orbit-dynamic-self-refresh', '1'])
                dyn_sr_th = to_int(params.get('dynamic-self-refresh-threshold'))
                if dyn_sr_th is not None:
                    cmd.extend(['--orbit-dynamic-self-refresh-threshold', str(dyn_sr_th)])
            
            # Timing interval parameters
            if is_checked(params.get('periodic-training')):
                cmd.extend(['--orbit-periodic-training', '1'])
                pt_period = to_int(params.get('periodic-training-period'))
                if pt_period is not None:
                    cmd.extend(['--orbit-periodic-training-period', str(pt_period)])
            if is_checked(params.get('temp-sensing')):
                cmd.extend(['--orbit-temp-sensing', '1'])
                ts_period = to_int(params.get('temp-sensing-period'))
                if ts_period is not None:
                    cmd.extend(['--orbit-temp-sensing-period', str(ts_period)])
            
            # Timing values
            zq_cal = to_int(params.get('zq-calibration-period'))
            if zq_cal is not None:
                cmd.extend(['--orbit-zq-calibration-period', str(zq_cal)])
            t_refiab = to_int(params.get('t-refiab'))
            if t_refiab is not None:
                cmd.extend(['--orbit-t-refiab', str(t_refiab)])
            t_refipb = to_int(params.get('t-refipb'))
            if t_refipb is not None:
                cmd.extend(['--orbit-t-refipb', str(t_refipb)])
            t_zqcal = to_int(params.get('t-zqcal'))
            if t_zqcal is not None:
                cmd.extend(['--orbit-t-zqcal', str(t_zqcal)])
            
            # Generate JSON override file with all orbit config params
            import json as json_module
            orbit_json = {
                'eye_scan_rd_en': 1 if is_checked(params.get('eye-scan-rd-en')) else 0,
                'eye_scan_wr_en': 1 if is_checked(params.get('eye-scan-wr-en')) else 0,
                'eye_scan_prbs_rd_en': 1 if is_checked(params.get('eye-scan-prbs-rd-en')) else 0,
                'eye_scan_prbs_wr_en': 1 if is_checked(params.get('eye-scan-prbs-wr-en')) else 0,
                'phy_vref_trn_mode': 1 if is_checked(params.get('phy-vref-trn-mode')) else 0,
                'phy_duty_trn_mode': 1 if is_checked(params.get('phy-duty-trn-mode')) else 0,
                'dram_vref_trn_mode': 1 if is_checked(params.get('dram-vref-trn-mode')) else 0,
                'dram_duty_trn_mode': 1 if is_checked(params.get('dram-duty-trn-mode')) else 0,
                'command_bus_training': 1 if is_checked(params.get('command-bus-training')) else 0,
                'ca_vref_training': 1 if is_checked(params.get('ca-vref-training')) else 0,
                'prbs_training': 1 if is_checked(params.get('prbs-training')) else 0,
                'reboot_with_training': 1 if is_checked(params.get('reboot-with-training')) else 0,
                'init_zq_calibration': 1 if is_checked(params.get('init-zq-calibration')) else 0,
                'zq_calibration': 1 if is_checked(params.get('zq-calibration')) else 0,
                'dfs_training': 1 if is_checked(params.get('dfs-training')) else 0,
                'phy_clock_gating': 1 if is_checked(params.get('phy-clock-gating')) else 0,
                'phy_idle_cnt_th': to_int(params.get('phy-idle-cnt-th')) or 0,
                'rank_interleaving': 1 if is_checked(params.get('orbit-rank-interleaving')) else 0,
                'num_rank': to_int(params.get('orbit-num-rank')) or 2,
                'reboot_with_mrw': 1 if is_checked(params.get('orbit-reboot-with-mrw')) else 0,
                'rfm_en': 1 if is_checked(params.get('orbit-rfm-en')) else 0,
                'dsm_en': 1 if is_checked(params.get('orbit-dsm-en')) else 0 if dram_type == 'lpddr4' else (1 if is_checked(params.get('orbit-dsm-en')) else 0),
                'ca_odt': 1 if is_checked(params.get('orbit-ca-odt')) else 0,
                'dynamic_power_down': 1 if is_checked(params.get('dynamic-power-down')) else 0,
                'dynamic_power_down_threshold': to_int(params.get('dynamic-power-down-threshold')) or 0,
                'dynamic_self_refresh': 1 if is_checked(params.get('dynamic-self-refresh')) else 0,
                'dynamic_self_refresh_threshold': to_int(params.get('dynamic-self-refresh-threshold')) or 0,
                'periodic_training': 1 if is_checked(params.get('periodic-training')) else 0,
                'periodic_training_period': to_int(params.get('periodic-training-period')) or 24000,
                'temp_sensing': 1 if is_checked(params.get('temp-sensing')) else 0,
                'temp_sensing_period': to_int(params.get('temp-sensing-period')) or 32000,
                'zq_calibration_period': to_int(params.get('zq-calibration-period')) or 48000,
                't_refiab': to_int(params.get('t-refiab')) or 3904000,
                't_refipb': to_int(params.get('t-refipb')) or 488000,
                't_zqcal': to_int(params.get('t-zqcal')) or 1000000,
                'regional_clock_gating': 1 if is_checked(params.get('regional-clock-gating')) else 0,
                'dram_clock_gating': 1 if is_checked(params.get('dram-clock-gating')) else 0,
                'phy_low_power': 1 if is_checked(params.get('phy-low-power')) else 0,
            }
            json_path = os.path.join(os.path.dirname(__file__), 'orbit_config_override.json')
            with open(json_path, 'w') as f:
                json_module.dump(orbit_json, f)
            
            # Pass JSON override to CLI
            cmd.extend(['--orbit-config-json', json_path])
            
            # Always use Python implementation for full binary
            cmd.extend(['--orbit-config-use-python'])
            
            # Periods
            periods = params.get('periods', '471 938 1631 2500').split()
            cmd.extend(periods)
            
            message.append(f"Running: {' '.join(cmd)}")
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    message.append(f"gen_timing_params failed: {result.stderr}")
                    success = False
                else:
                    message.append("ddr_timing_table.bin generated successfully")
            except Exception as e:
                message.append(f"Error running gen_timing_params: {e}")
                success = False
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': success, 'message': '\n'.join(message)}).encode())
        
        elif self.path == '/analyze':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = json.loads(body)
            
            file_path = params.get('file_path', 'ddr_timing_table.bin')
            dram_type_override = params.get('dram_type_override', 'auto')
            result = analyze_binary_file(file_path, dram_type_override)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        else:
            self.send_error(404)


class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def run_server():
    with ReuseAddrTCPServer(('', PORT), DDRHandler) as httpd:
        print(f"DDR Timing Table Generator")
        print(f"Open http://localhost:{PORT} in your browser")
        print(f"Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")


if __name__ == '__main__':
    run_server()
