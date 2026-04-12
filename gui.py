#!/usr/bin/env python3
"""
DDR Timing Table Generator - Web GUI
Runs locally without internet using Python standard library.
"""

import http.server
import socketserver
import ctypes
import json
import os
import struct
import subprocess
import sys

from orbit_config import make_orbit_config_class, EMMC_CM4_TIME_TB_SIZE


def _ctypes_value_to_python(value):
    """Convert a ctypes field read to a plain Python value (scalar or list)."""
    if isinstance(value, (int, float)):
        return value
    # ctypes arrays — convert recursively
    try:
        return [_ctypes_value_to_python(v) for v in value]
    except TypeError:
        # Nested Structure fallback (chip_config, prbs_result_t, train_result_t)
        try:
            return {
                name: _ctypes_value_to_python(getattr(value, name))
                for name, _ in value._fields_
            }
        except AttributeError:
            return value


def _identify_binary(file_size):
    """Pick (dram_type, two_channel) by matching ctypes struct size to file size.

    This replaces the old file-size-based heuristic with a structural lookup:
    the file layout is EMMC_CM4_TIME_TB_SIZE (0x800) + sizeof(orbit_config),
    and sizeof(orbit_config) is unique per (dram_type, two_channel).
    Returns (dram_type, two_channel) or (None, None) if no match.
    """
    expected = file_size - EMMC_CM4_TIME_TB_SIZE
    for dram_type in ("lpddr4", "lpddr5"):
        for two_channel in (False, True):
            if ctypes.sizeof(make_orbit_config_class(dram_type, two_channel)) == expected:
                return dram_type, two_channel
    return None, None


def _read_orbit_ctypes(file_path, dram_type, two_channel):
    """Read the orbit_config struct at offset 0x800 into a ctypes instance."""
    cls = make_orbit_config_class(dram_type, two_channel)
    cfg = cls()
    with open(file_path, 'rb') as f:
        f.seek(EMMC_CM4_TIME_TB_SIZE)
        f.readinto(cfg)
    return cfg

PORT = 5010


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
    
    # LP4 common params at 0x106, LP5 at 0x13c; per-entry LP4 at 0x110, LP5 at 0x146
    common_offset_base = 0x13c if dram_type == 'lpddr5' else 0x106
    per_entry_base = 0x146 if dram_type == 'lpddr5' else 0x110

    for idx in range(num_entries):
        entry_offset = idx * entry_size
        if entry_offset + entry_size > len(data):
            break

        # Check enable flags using correct offsets per DRAM type
        write_odt = data[entry_offset + common_offset_base + 4] if entry_offset + common_offset_base + 4 < len(data) else 0
        write_dbi = data[entry_offset + common_offset_base + 6] if entry_offset + common_offset_base + 6 < len(data) else 0
        read_dbi = data[entry_offset + common_offset_base + 7] if entry_offset + common_offset_base + 7 < len(data) else 0
        read_link_parity = data[entry_offset + per_entry_base + 15] if entry_offset + per_entry_base + 15 < len(data) else 0
        write_link_parity = data[entry_offset + per_entry_base + 16] if entry_offset + per_entry_base + 16 < len(data) else 0

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
    
    common = {}
    
    return {
        'entries': timing_entries,
        'common': common,
        'density_dependent': density_dependent,
        'selected_density': density,
    }


def analyze_binary_file(file_path, dram_type_override=None, two_channel_override=None):
    """Analyze a ddr_timing_table binary using the ctypes orbit_config class.

    No more hand-rolled offset tables. Caller may pass explicit
    ``dram_type_override`` / ``two_channel_override``; otherwise the
    (dram_type, two_channel) pair is identified by matching
    ``file_size - 0x800`` against ``ctypes.sizeof(make_orbit_config_class(...))``.
    """
    if not os.path.exists(file_path):
        return {'success': False, 'message': f'File not found: {file_path}'}
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        return {'success': False, 'message': f'Error reading file: {str(e)}'}

    file_size = len(data)
    if file_size < EMMC_CM4_TIME_TB_SIZE + 32:
        return {'success': False,
                'message': 'File too small to be a valid binary: %d bytes' % file_size}

    # Identify (dram_type, two_channel) from size unless overridden.
    dram_type = dram_type_override if dram_type_override and dram_type_override != 'auto' else None
    if two_channel_override is not None:
        two_channel = bool(int(two_channel_override))
    else:
        two_channel = None
    if dram_type is None or two_channel is None:
        dt_auto, ch_auto = _identify_binary(file_size)
        if dram_type is None:
            dram_type = dt_auto
        if two_channel is None:
            two_channel = ch_auto
    if dram_type is None:
        return {'success': False,
                'message': ('Unable to identify (dram_type, two_channel) from file '
                            'size %d; pass dram_type_override explicitly.' % file_size)}

    # Read the orbit_config region via ctypes.
    try:
        cfg = _read_orbit_ctypes(file_path, dram_type, bool(two_channel))
    except Exception as e:
        return {'success': False,
                'message': 'Failed to read orbit_config via ctypes: %s' % e}

    # Flatten every field into a plain dict.
    orbit = {}
    for name, _ in cfg._fields_:
        orbit[name] = _ctypes_value_to_python(getattr(cfg, name))

    # Parse timing entries for the periods / feature-flag ranges used by the GUI.
    periods = []
    read_lecc_upto = 0
    write_lecc_upto = 0
    write_odt_upto = 0
    read_dbi_upto = 0
    write_dbi_upto = 0
    is_lpddr5 = (dram_type == 'lpddr5')
    entry_size = 0x15C if is_lpddr5 else 0x128
    # LP4 common params at 0x106, LP5 at 0x13c within each entry
    common_off = 0x13c if is_lpddr5 else 0x106
    max_entries = 8
    for i in range(max_entries):
        offset = i * entry_size
        if offset + 8 > len(data):
            break
        t_ck = struct.unpack('<I', data[offset+4:offset+8])[0]
        if not (300 <= t_ck <= 5000):
            continue
        if is_lpddr5:
            wck_ratio = data[offset + 0x13c] if offset + 0x13c < len(data) else 4
            display_period = t_ck // wck_ratio if wck_ratio else t_ck
        else:
            display_period = t_ck
        periods.append(display_period)
        # write_odt is at common_off+4, write_dbi at common_off+6,
        # read_dbi at common_off+7 within each entry
        if len(data) >= offset + common_off + 10:
            write_odt_flag = data[offset + common_off + 4]
            write_dbi_flag = data[offset + common_off + 6]
            read_dbi_flag = data[offset + common_off + 7]
            # Per-entry params: LP4 at 0x110+15/+16, LP5 at 0x146+15/+16
            per_entry_off = 0x146 if is_lpddr5 else 0x110
            read_link_parity = data[offset + per_entry_off + 15] if len(data) > offset + per_entry_off + 16 else 0
            write_link_parity = data[offset + per_entry_off + 16] if len(data) > offset + per_entry_off + 16 else 0
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
    # For LP5, the binary stores t_ck = tWCK * wck_ratio internally.
    # Convert the "upto" values back to tWCK units for the GUI.
    if is_lpddr5:
        # Use the wck_ratio from the first valid entry (typically 4)
        first_wck_ratio = 4
        for i in range(max_entries):
            off = i * entry_size
            if off + 0x13c < len(data):
                wr = data[off + 0x13c]
                if wr in (2, 4):
                    first_wck_ratio = wr
                    break
        if write_odt_upto > 0:
            write_odt_upto = write_odt_upto // first_wck_ratio
        if read_dbi_upto > 0:
            read_dbi_upto = read_dbi_upto // first_wck_ratio
        if write_dbi_upto > 0:
            write_dbi_upto = write_dbi_upto // first_wck_ratio
        if read_lecc_upto > 0:
            read_lecc_upto = read_lecc_upto // first_wck_ratio
        if write_lecc_upto > 0:
            write_lecc_upto = write_lecc_upto // first_wck_ratio

    if not periods:
        periods = [314, 418, 556, 2500] if is_lpddr5 else [471, 938, 1631, 2500]
    if len(periods) == 1:
        periods = [314, 418, 556, 2500] if is_lpddr5 else [471, 938, 1631, 2500]

    # Collapse dfs_lvl_t_ck to a list of valid entries (300..5000 range).
    dfs_list = [v for v in orbit.get('dfs_lvl_t_ck', []) if 300 <= v <= 5000]

    non_parseable_fields = [
        'variable-trrd', 'txsr-as-1st-ed', 'enhanced-nt-odt', 'wire-length',
        'wdqs-ctrl-mode', 'rpste-upto', 'wpste-upto', 'nt-odt-upto',
        'bg-mode-upto', 'wck-always-on-from', 'wck-always-on-upto',
        'wck-1to4-upto', 'wck-hf-upto', 'wck-pst1-upto', 'wck-pst2-upto',
        'rdqs-pst1-upto', 'rdqs-pst2-upto',
    ]

    result = {
        'success': True,
        'data': {
            'file_path': file_path,
            'file_size': file_size,
            'dram_type': dram_type,
            'two_channel': bool(two_channel),
            'basic': {
                'dram_type': dram_type,
                'phy_name': 'sphy-v9r8',
                'dq_width': orbit.get('dq_width', 16),
                'speed_bin': '4266' if dram_type == 'lpddr4' else '6400',
                'periods': ' '.join(map(str, periods)),
                'min_dram_tck': 314,
                'dram_tck': orbit.get('dram_t_ck', periods[0] if periods else 471),
            },
            'pipe': {
                'cpipe_depth': orbit.get('cpipe_depth', 1),
                'dpipe_depth': orbit.get('dpipe_depth', 1),
                'omc_freq_ratio': orbit.get('omc_freq_ratio', 1 if is_lpddr5 else 2),
                'phy_freq_ratio': orbit.get('phy_freq_ratio', 1 if is_lpddr5 else 2),
                'wire_length': 10,
            },
            'timing': {
                'write_odt_upto': write_odt_upto or (1250 if dram_type == 'lpddr4' else 10000),
                'read_dbi_upto': read_dbi_upto or 10000,
                'write_dbi_upto': write_dbi_upto or 10000,
                'read_lecc_upto': read_lecc_upto,
                'write_lecc_upto': write_lecc_upto,
            },
            'timing_entries': parse_timing_entries(data, dram_type),
            'orbit': {
                'density': orbit.get('density', 16),
                'density_code': orbit.get('density_code', 0),
                'cpipe_depth': orbit.get('cpipe_depth', 1),
                'dpipe_depth': orbit.get('dpipe_depth', 1),
                'rank_interleaving': orbit.get('rank_interleaving', 1),
                'num_rank': orbit.get('num_rank', 2),
                'dfs_lvl_t_ck': dfs_list or ([1672, 2224, 5000] if is_lpddr5 else [938, 1631, 2500]),
                'two_channel': 1 if two_channel else 0,
                'ctrl_dq_width': orbit.get('ctrl_dq_width', 16),
                'dq_width': orbit.get('dq_width', 16),
                'dram_t_ck': orbit.get('dram_t_ck', 0),
                'rclk_t_ck': orbit.get('rclk_t_ck', 0),
                'boot_t_ck': orbit.get('boot_t_ck', 0),
                'reboot_with_mrw': orbit.get('reboot_with_mrw', 0),
                'rfm_en': orbit.get('rfm_en', 0),
                'dsm_en': orbit.get('dsm_en', 0),
                'ca_odt': orbit.get('ca_odt', 0),
                'eye_scan_rd_en': orbit.get('eye_scan_rd_en', 0),
                'eye_scan_wr_en': orbit.get('eye_scan_wr_en', 0),
                'eye_scan_prbs_rd_en': orbit.get('eye_scan_prbs_rd_en', 0),
                'eye_scan_prbs_wr_en': orbit.get('eye_scan_prbs_wr_en', 0),
                'init_zq_calibration': orbit.get('init_zq_calibration', 0),
                'command_bus_training': orbit.get('command_bus_training', 0),
                'ca_vref_training': orbit.get('ca_vref_training', 0),
                'prbs_training': orbit.get('prbs_training', 0),
                'reboot_with_training': orbit.get('reboot_with_training', 0),
                'dfs_training': orbit.get('dfs_training', 0),
                'phy_vref_trn_mode': orbit.get('phy_vref_trn_mode', 0),
                'phy_duty_trn_mode': orbit.get('phy_duty_trn_mode', 0),
                'dram_vref_trn_mode': orbit.get('dram_vref_trn_mode', 0),
                'dram_duty_trn_mode': orbit.get('dram_duty_trn_mode', 0),
                'regional_clock_gating': orbit.get('regional_clock_gating', 0),
                'phy_clock_gating': orbit.get('phy_clock_gating', 0),
                'dram_clock_gating': orbit.get('dram_clock_gating', 0),
                'temp_sensing': orbit.get('temp_sensing', 0),
                'zq_calibration': orbit.get('zq_calibration', 0),
                'periodic_training': orbit.get('periodic_training', 0),
                'periodic_training_period': orbit.get('periodic_training_period', 0),
                'zq_calibration_period': orbit.get('zq_calibration_period') or 48000,
                'temp_sensing_period': orbit.get('temp_sensing_period', 32000),
                't_refiab': orbit.get('t_refiab', 3904000),
                't_refipb': orbit.get('t_refipb', 488000),
                't_zqcal': orbit.get('t_zqcal', 1000000),
                'mrr_byte_lane': hex(orbit.get('mrr_byte_lane', 0x55)),
                'phy_low_power': orbit.get('phy_low_power', 0),
                'phy_idle_cnt_th': orbit.get('phy_idle_cnt_th', 0),
                'dynamic_power_down': orbit.get('dynamic_power_down', 0),
                'dynamic_self_refresh': orbit.get('dynamic_self_refresh', 0),
                'dynamic_power_down_threshold': orbit.get('dynamic_power_down_threshold', 0),
                'dynamic_self_refresh_threshold': orbit.get('dynamic_self_refresh_threshold', 0),
                'non_parseable_fields': non_parseable_fields,
            },
        },
    }
    return result




def build_generate_cmd(params):
    """Build the gen_timing_params command list from GUI params.

    Returns (cmd, orbit_json_path) where cmd is a list of strings
    and orbit_json_path is the path to the generated JSON override file.
    """
    def to_int(val):
        if val is None or val == '':
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    dram_type = params.get('dram-type', 'lpddr4')
    cmd = [sys.executable, 'gen_timing_params']
    cmd.extend(['--dram-type', dram_type])
    cmd.extend(['--phy-name', params.get('phy-name', 'sphy-v9r8')])
    cmd.extend(['--speed-bin', params.get('speed-bin', '4266')])
    dq_width = params.get('dq-width', '16')
    cmd.extend(['--dq-width', dq_width])

    cpipe = to_int(params.get('cpipe-depth'))
    dpipe = to_int(params.get('dpipe-depth'))
    cmd.extend(['--cpipe-depth', str(cpipe if cpipe else 1)])
    cmd.extend(['--dpipe-depth', str(dpipe if dpipe else 1)])

    if dram_type == 'lpddr5':
        default_omc_freq, default_phy_freq = 1, 1
    else:
        default_omc_freq, default_phy_freq = 2, 2
    cmd.extend(['--omc-freq-ratio', str(params.get('omc-freq-ratio', default_omc_freq))])
    cmd.extend(['--phy-freq-ratio', str(params.get('phy-freq-ratio', default_phy_freq))])

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
    if dram_type == 'lpddr5' and is_checked(params.get('orbit-dsm-en')):
        cmd.extend(['--orbit-dsm-en', '1'])
    if is_checked(params.get('orbit-ca-odt')):
        cmd.extend(['--orbit-ca-odt', '1'])

    phy_idle_cnt_th = to_int(params.get('phy-idle-cnt-th'))
    if phy_idle_cnt_th is not None:
        cmd.extend(['--orbit-phy-idle-cnt-th', str(phy_idle_cnt_th)])

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

    # Generate JSON override file
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
        'dsm_en': (1 if is_checked(params.get('orbit-dsm-en')) else 0) if dram_type == 'lpddr5' else 0,
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
        'dfs_lvl_t_ck': [
            to_int(params.get('dfs-lvl-t-ck-0')) or (1672 if dram_type == 'lpddr5' else 938),
            to_int(params.get('dfs-lvl-t-ck-1')) or (2224 if dram_type == 'lpddr5' else 1631),
            to_int(params.get('dfs-lvl-t-ck-2')) or (5000 if dram_type == 'lpddr5' else 2500),
        ],
        'dq_width': to_int(params.get('dq-width')) or 16,
    }
    json_path = os.path.join(os.path.dirname(__file__), 'orbit_config_override.json')
    with open(json_path, 'w') as f:
        json.dump(orbit_json, f)

    cmd.extend(['--orbit-config-json', json_path])
    cmd.extend(['--orbit-config-use-python'])

    periods = params.get('periods', '471 938 1631 2500').split()
    cmd.extend(periods)

    return cmd, json_path


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

            cmd, _ = build_generate_cmd(params)

            message.append(f"Running: {' '.join(cmd)}")

            output_path = params.get('output_path', '')

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    message.append(f"gen_timing_params failed: {result.stderr}")
                    success = False
                else:
                    default_bin = 'ddr_timing_table.bin'
                    if output_path and os.path.abspath(output_path) != os.path.abspath(default_bin):
                        import shutil
                        shutil.copy2(default_bin, output_path)
                        message.append(f"Binary saved to {output_path}")
                    else:
                        message.append(f"Binary saved to {os.path.abspath(default_bin)}")
            except Exception as e:
                message.append(f"Error running gen_timing_params: {e}")
                success = False
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': success, 'message': '\n'.join(message)}).encode())
        
        elif self.path == '/preview-cmd':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = json.loads(body)
            try:
                cmd, _ = build_generate_cmd(params)
                result = {'success': True, 'command': ' '.join(cmd)}
            except Exception as e:
                result = {'success': False, 'message': str(e)}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        elif self.path == '/analyze':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = json.loads(body)

            file_path = params.get('file_path', 'ddr_timing_table.bin')
            dram_type_override = params.get('dram_type_override', 'auto')
            two_channel_override = params.get('two_channel_override', None)
            result = analyze_binary_file(file_path, dram_type_override, two_channel_override)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        elif self.path == '/browse':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = json.loads(body)
            dir_path = params.get('path', os.getcwd())
            file_filter = params.get('filter', '')  # e.g. '.json', '.bin'

            try:
                if not os.path.isdir(dir_path):
                    dir_path = os.path.dirname(dir_path) or os.getcwd()
                entries = []
                # Parent directory
                parent = os.path.dirname(os.path.abspath(dir_path))
                if parent != os.path.abspath(dir_path):
                    entries.append({'name': '..', 'path': parent, 'is_dir': True})
                for name in sorted(os.listdir(dir_path)):
                    if name.startswith('.'):
                        continue
                    full = os.path.join(dir_path, name)
                    is_dir = os.path.isdir(full)
                    if is_dir or not file_filter or name.endswith(file_filter):
                        entries.append({'name': name, 'path': full, 'is_dir': is_dir})
                result = {'success': True, 'cwd': os.path.abspath(dir_path), 'entries': entries}
            except Exception as e:
                result = {'success': False, 'message': str(e)}

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        elif self.path == '/save-json':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = json.loads(body)
            file_path = params.get('file_path', 'ddr_config.json')
            data = params.get('data', {})

            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                result = {'success': True, 'message': f'JSON saved to {file_path}'}
            except Exception as e:
                result = {'success': False, 'message': str(e)}

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        elif self.path == '/load-json-path':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = json.loads(body)
            file_path = params.get('file_path', '')

            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                result = {'success': True, 'data': data}
            except Exception as e:
                result = {'success': False, 'message': str(e)}

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
