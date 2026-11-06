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


def _load_cfg_from_data(data, dram_type, two_channel):
    """Build a zero-padded orbit_config from the 0x800 region of ``data``.

    The SCP image only stores the configuration prefix (up to region_end) and
    pads the rest to 4 KiB, so reading the full struct from a 4 KiB file is
    intentionally allowed to leave the trailing runtime-result fields zero.
    """
    cls = make_orbit_config_class(dram_type, two_channel)
    size = ctypes.sizeof(cls)
    buf = bytearray(size)
    available = max(0, min(len(data) - EMMC_CM4_TIME_TB_SIZE, size))
    if available:
        buf[:available] = data[EMMC_CM4_TIME_TB_SIZE:EMMC_CM4_TIME_TB_SIZE + available]
    return cls.from_buffer_copy(bytes(buf))


def _orbit_score(cfg, dram_type):
    """Plausibility score for a candidate (dram_type, two_channel) layout."""
    score = 0
    if cfg.ch_intr_size == 1:
        score += 2
    if cfg.reboot == 0:
        score += 1
    if cfg.reqq_depth == 40:
        score += 1
    if cfg.density in (1, 2, 3, 4, 6, 8, 12, 16, 24, 32):
        score += 2
    if cfg.num_rank in (1, 2):
        score += 1
    if cfg.ctrl_dq_width in (8, 16, 32):
        score += 1
    if cfg.dq_width in (4, 8, 16, 32):
        score += 1
    if 100 <= cfg.dram_t_ck <= 20000:
        score += 2
    if 1 <= cfg.timingtable_size <= 4:
        score += 1
    if 1000 <= cfg.rclk_t_ck <= 100000:
        score += 1
    if cfg.omc_channel in (0, 1, 2):
        score += 1
    if dram_type == 'lpddr5':
        if cfg.bg_intr_size == 3:
            score += 2
        if cfg.phy_freq_ratio == 1:
            score += 1
        if cfg.omc_freq_ratio == 1:
            score += 1
    else:
        if cfg.bg_intr_size == 0:
            score += 2
        if cfg.phy_freq_ratio == 2:
            score += 1
        if cfg.omc_freq_ratio == 2:
            score += 1
    return score


def _identify_binary(file_size, data=None):
    """Identify (dram_type, two_channel) from the orbit_config content.

    File size is no longer sufficient: the SCP build always pads the per-DRAM
    image to 4 KiB, and LP4/LP5 single-channel structs share the same prefix
    size.  We therefore score each candidate layout against fields that are
    stable across configurations (density, ranks, widths, ratios, clock).
    """
    if not data or len(data) <= EMMC_CM4_TIME_TB_SIZE:
        return None, None

    scored = []
    for dram_type in ("lpddr4", "lpddr5"):
        for two_channel in (False, True):
            cfg = _load_cfg_from_data(data, dram_type, two_channel)
            scored.append((_orbit_score(cfg, dram_type),
                           (dram_type, two_channel)))
    best_score, best = max(scored, key=lambda item: item[0])
    if best_score < 8:
        return None, None
    return best


def _guess_dram_type_from_timing(data):
    """Fallback for timing-only images: pick the entry size that parses best."""
    best_type, best_hits = 'lpddr4', -1
    for dram_type, entry_size in (('lpddr4', 0x128), ('lpddr5', 0x15C)):
        hits = 0
        for i in range(EMMC_CM4_TIME_TB_SIZE // entry_size):
            off = i * entry_size
            if off + 8 > len(data):
                break
            freq, t_ck = struct.unpack_from('<II', data, off)
            if 10 <= freq <= 20000 and 100 <= t_ck <= 20000:
                hits += 1
        if hits > best_hits:
            best_type, best_hits = dram_type, hits
    return best_type


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


def parse_timing_entries(data, dram_type, density=None, density_index=None):
    """Parse every timing_param entry from a per-DRAM timing-table image.

    Layout (from ``struct timing_param`` in arise2_omc.h):

        0x000  freq, t_ck, timing_zqcal                    (3 x u32)
        0x00C  timing_param[21]                            (21 x u32)
        0x060  timing_param_derate[2]                      (2 x u32)
        0x068  dfi_timing_param[8]                         (8 x u32)
        0x088  nine density arrays                         (9 x N x u16)
        0x088 + 18*N  wck_ratio .. rpste                   (10 x u8)
        ...            rl .. trddata_en                    (22 x u8)

    N is 7 for LPDDR4 and 10 for LPDDR5, giving entry sizes 0x128 / 0x15C.
    The timing table region is 0x000..0x7FF; orbit_config starts at 0x800.
    """
    is_lp5 = (dram_type == 'lpddr5')
    num_densities = 10 if is_lp5 else 7
    raw_size = 0x88 + 18 * num_densities + 32
    entry_size = (raw_size + 3) & ~3  # struct tail padding (LP4: 294 -> 296)
    num_entries = EMMC_CM4_TIME_TB_SIZE // entry_size

    if is_lp5:
        densities = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
    else:
        densities = [2, 3, 4, 6, 8, 12, 16]

    if density is None:
        density = 16
    if density_index is None:
        try:
            density_index = densities.index(density)
        except ValueError:
            density_index = 0

    density_array_names = [
        't_rfcab', 't_rfcpb', 't_rfmab', 't_rfmpb', 't_refdpr',
        'tx_pbr2pbr', 't_xsr', 't_xsdll', 't_xs_fast',
    ]
    array_stride = num_densities * 2

    common_offset = 0x88 + 9 * array_stride
    per_entry_offset = common_offset + 10

    per_entry_names = [
        'rl', 'wl', 'mr_rl', 'mr_wl', 'mr_wr', 'mr_rtp', 'mr_cal',
        'mr_tccd_l', 'bank_mode', 'wck_fm', 'rdqs_pst_mode', 'rdqs_pst',
        'rdqs_pre', 'wck_pst', 'wck_on', 'read_link_parity',
        'write_link_parity', 't_rtw', 't_wtr_a', 't_wtr', 't_rc',
        'trddata_en',
    ]
    common_names = [
        'wck_ratio', 'tlp_resp', 'auto_dqs_clean', 'dll_enable',
        'write_odt', 'nt_odt', 'write_dbi', 'read_dbi', 'wpste', 'rpste',
    ]

    timing_entries = []
    first_density_arrays = None

    for idx in range(num_entries):
        entry_offset = idx * entry_size
        if entry_offset + entry_size > len(data):
            break

        freq, t_ck = struct.unpack_from('<II', data, entry_offset)
        if not (10 <= freq <= 20000 and 100 < t_ck <= 20000):
            continue

        timing_zqcal, = struct.unpack_from('<I', data, entry_offset + 0x08)
        timing_param = list(struct.unpack_from(
            '<21I', data, entry_offset + 0x0C))
        derate = list(struct.unpack_from('<2I', data, entry_offset + 0x60))
        dfi = list(struct.unpack_from('<8I', data, entry_offset + 0x68))

        density_arrays = {}
        for i, name in enumerate(density_array_names):
            density_arrays[name] = list(struct.unpack_from(
                '<%dH' % num_densities, data,
                entry_offset + 0x88 + i * array_stride))
        if first_density_arrays is None:
            first_density_arrays = density_arrays

        common = {
            name: data[entry_offset + common_offset + i]
            for i, name in enumerate(common_names)
        }
        per_entry = {
            name: data[entry_offset + per_entry_offset + i]
            for i, name in enumerate(per_entry_names)
        }

        wck_ratio = common['wck_ratio'] or (1 if is_lp5 else 4)
        entry = {
            'entry': idx,
            'offset': entry_offset,
            'entry_size': entry_size,
            'freq': freq,
            't_ck': t_ck,
            't_ck_display': t_ck // wck_ratio if is_lp5 else t_ck,
            'timing_zqcal': timing_zqcal,
            'timing_param': timing_param,
            'timing_derate': derate,
            'dfi_timing_param': dfi,
            'density_index': density_index,
            'selected_density': density,
        }
        entry.update(common)
        entry.update(per_entry)
        entry.update(density_arrays)
        timing_entries.append(entry)

    density_dependent = {}
    if first_density_arrays is not None:
        density_dependent = {
            k: (v[density_index] if density_index < len(v) else 0)
            for k, v in first_density_arrays.items()
        }

    return {
        'entries': timing_entries,
        'common': {},
        'density_dependent': density_dependent,
        'selected_density': density,
        'density_index': density_index,
    }


def analyze_binary_file(file_path, dram_type_override=None, two_channel_override=None):
    """Analyze a per-DRAM timing-table image.

    The SCP build pads each image to 4 KiB and stores only the orbit_config
    prefix at 0x800, so identification is content-based (see
    ``_identify_binary``).  Timing-only images are still accepted: the timing
    entries are parsed and the orbit section is reported as unavailable.
    """
    if not os.path.exists(file_path):
        return {'success': False, 'message': f'File not found: {file_path}'}
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        return {'success': False, 'message': f'Error reading file: {str(e)}'}

    file_size = len(data)
    if file_size < 32:
        return {'success': False,
                'message': 'File too small to be a valid binary: %d bytes' % file_size}

    # Identify (dram_type, two_channel) from content unless overridden.
    dram_type = dram_type_override if dram_type_override and dram_type_override != 'auto' else None
    if two_channel_override is not None and two_channel_override != '':
        two_channel = bool(int(two_channel_override))
    else:
        two_channel = None

    candidates = []
    for dt in ((dram_type,) if dram_type else ("lpddr4", "lpddr5")):
        for tc in ((two_channel,) if two_channel is not None else (False, True)):
            cfg = _load_cfg_from_data(data, dt, tc)
            candidates.append((_orbit_score(cfg, dt), dt, tc, cfg))
    best_score, best_dt, best_tc, best_cfg = max(candidates, key=lambda item: item[0])

    orbit_available = best_score >= 8 and len(data) > EMMC_CM4_TIME_TB_SIZE
    if orbit_available:
        dram_type, two_channel, cfg = best_dt, best_tc, best_cfg
    else:
        # Timing-only image: infer the table type from entry alignment.
        if dram_type is None:
            dram_type = _guess_dram_type_from_timing(data)
        if two_channel is None:
            two_channel = False
        cfg = None
        orbit = {}

    if cfg is not None:
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
    max_entries = EMMC_CM4_TIME_TB_SIZE // entry_size
    for i in range(max_entries):
        offset = i * entry_size
        if offset + 8 > len(data):
            break
        t_ck = struct.unpack('<I', data[offset+4:offset+8])[0]
        # Binary stores internal tCK (= tWCK * wck_ratio for LP5).
        # LP5 4:1 memcfgs go up to 20000ps internal tCK.
        if not (100 < t_ck <= 20000):
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
    # Keep the three DFS slots positional: unused levels are zero, not dropped.
    raw_dfs = list(orbit.get('dfs_lvl_t_ck', []))
    dfs_list = [(v if 300 <= v <= 5000 else 0) for v in raw_dfs]
    dfs_list = (dfs_list + [0, 0, 0])[:3]
    if not orbit_available:
        dfs_list = [0, 0, 0]

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
            'orbit_available': orbit_available,
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
            'timing_entries': parse_timing_entries(data, dram_type,
                                                     density=orbit.get('density')),
            'orbit': {
                'available': orbit_available,
                'density': orbit.get('density', 16),
                'density_code': orbit.get('density_code', 0),
                'ch_intr_size': orbit.get('ch_intr_size', 1),
                'bg_intr_size': orbit.get('bg_intr_size', 3 if is_lpddr5 else 0),
                'phy_freq_ratio': orbit.get('phy_freq_ratio', 1 if is_lpddr5 else 2),
                'omc_freq_ratio': orbit.get('omc_freq_ratio', 1 if is_lpddr5 else 2),
                'cpipe_depth': orbit.get('cpipe_depth', 1),
                'dpipe_depth': orbit.get('dpipe_depth', 1),
                'rank_interleaving': orbit.get('rank_interleaving', 1),
                'num_rank': orbit.get('num_rank', 1),
                'dfs_lvl_t_ck': dfs_list or ([1428, 1672, 2512] if is_lpddr5 else [938, 1631, 2500]),
                'two_channel': 1 if two_channel else 0,
                'omc_channel': orbit.get('omc_channel', 0),
                'ctrl_dq_width': orbit.get('ctrl_dq_width', 16),
                'dq_width': orbit.get('dq_width', 16),
                'chip': orbit.get('chip', []),
                'num_of_ch': orbit.get('num_of_ch', []),
                'dram_t_ck': orbit.get('dram_t_ck', 0),
                'rclk_t_ck': orbit.get('rclk_t_ck', 0),
                'boot_t_ck': orbit.get('boot_t_ck', 0),
                'reboot_with_mrw': orbit.get('reboot_with_mrw', 1),
                'rfm_en': orbit.get('rfm_en', 1),
                'dsm_en': orbit.get('dsm_en', 0),
                'ca_odt': orbit.get('ca_odt', 1),
                'phy_odt': orbit.get('phy_odt', 5),
                'otd_ck': orbit.get('otd_ck', 1),
                'otd_cs': orbit.get('otd_cs', 1),
                'otd_ca': orbit.get('otd_ca', 1),
                'zq_bg_mode': orbit.get('zq_bg_mode', 1),
                'lpddr4_rpre': orbit.get('lpddr4_rpre', 0),
                'initial_training': orbit.get('initial_training', 1),
                'init_zq_calibration': orbit.get('init_zq_calibration', 1),
                'command_bus_training': orbit.get('command_bus_training', 1),
                'ca_vref_training': orbit.get('ca_vref_training', 1),
                'prbs_training': orbit.get('prbs_training', 1),
                'reboot_with_training': orbit.get('reboot_with_training', 1),
                'phy_vref_trn_mode': orbit.get('phy_vref_trn_mode', 1),
                'phy_duty_trn_mode': orbit.get('phy_duty_trn_mode', 1),
                'dram_vref_trn_mode': orbit.get('dram_vref_trn_mode', 1),
                'dram_duty_trn_mode': orbit.get('dram_duty_trn_mode', 1),
                'regional_clock_gating': orbit.get('regional_clock_gating', 1),
                'phy_clock_gating': orbit.get('phy_clock_gating', 0),
                'dram_clock_gating': orbit.get('dram_clock_gating', 1),
                'temp_sensing': orbit.get('temp_sensing', 1),
                'zq_calibration': orbit.get('zq_calibration', 1),
                'periodic_training': orbit.get('periodic_training', 1),
                'periodic_training_period': orbit.get('periodic_training_period', 50000),
                'zq_calibration_period': orbit.get('zq_calibration_period') or 48000,
                'temp_sensing_period': orbit.get('temp_sensing_period', 32000),
                't_refiab': orbit.get('t_refiab', 3904000),
                't_refipb': orbit.get('t_refipb', 488000),
                't_zqcal': orbit.get('t_zqcal', 1000000),
                'mrr_byte_lane': hex(orbit.get('mrr_byte_lane', 0x55)),
                'phy_low_power': orbit.get('phy_low_power', 0),
                'phy_idle_cnt_th': orbit.get('phy_idle_cnt_th', 128),
                'dynamic_power_down': orbit.get('dynamic_power_down', 1),
                'dynamic_self_refresh': orbit.get('dynamic_self_refresh', 1),
                'dynamic_power_down_threshold': orbit.get('dynamic_power_down_threshold', 2048),
                'dynamic_self_refresh_threshold': orbit.get('dynamic_self_refresh_threshold', 2048),
                'timingtable_size': orbit.get('timingtable_size', 4),
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

    # Orbit config.  Defaults below mirror SCP-firmware's ddr_config.h.  We
    # always pass every field explicitly so unchecking a default-on toggle
    # actually reaches the generator instead of silently falling back to the
    # firmware default.
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
    num_rank = to_int(params.get('orbit-num-rank'))
    if num_rank:
        cmd.extend(['--orbit-num-rank', str(num_rank)])
    default_ch = to_int(params.get('orbit-default-ch'))
    if default_ch is not None:
        cmd.extend(['--orbit-default-ch', str(default_ch)])
    freq_level = to_int(params.get('orbit-freq-level'))
    if freq_level is not None:
        cmd.extend(['--orbit-freq-level', str(freq_level)])
    lp5_set = params.get('orbit-lp5-freq-set')
    if dram_type == 'lpddr5' and lp5_set:
        cmd.extend(['--orbit-lp5-freq-set', str(lp5_set)])

    # (GUI name, CLI flag, JSON field, default, kind)
    orbit_fields = [
        ('orbit-reboot-with-mrw', '--orbit-reboot-with-mrw', 'reboot_with_mrw', 1, 'check'),
        ('orbit-rfm-en', '--orbit-rfm-en', 'rfm_en', 1, 'check'),
        ('orbit-ca-odt', '--orbit-ca-odt', 'ca_odt', 1, 'check'),
        ('orbit-phy-odt', '--orbit-phy-odt', 'phy_odt', 5, 'int'),
        ('orbit-otd-ck', '--orbit-otd-ck', 'otd_ck', 1, 'check'),
        ('orbit-otd-cs', '--orbit-otd-cs', 'otd_cs', 1, 'check'),
        ('orbit-otd-ca', '--orbit-otd-ca', 'otd_ca', 1, 'check'),
        ('orbit-initial-training', '--orbit-initial-training', 'initial_training', 1, 'check'),
        ('phy-vref-trn-mode', '--orbit-phy-vref-trn-mode', 'phy_vref_trn_mode', 1, 'check'),
        ('phy-duty-trn-mode', '--orbit-phy-duty-trn-mode', 'phy_duty_trn_mode', 1, 'check'),
        ('dram-vref-trn-mode', '--orbit-dram-vref-trn-mode', 'dram_vref_trn_mode', 1, 'check'),
        ('dram-duty-trn-mode', '--orbit-dram-duty-trn-mode', 'dram_duty_trn_mode', 1, 'check'),
        ('command-bus-training', '--orbit-command-bus-training', 'command_bus_training', 1, 'check'),
        ('ca-vref-training', '--orbit-ca-vref-training', 'ca_vref_training', 1, 'check'),
        ('prbs-training', '--orbit-prbs-training', 'prbs_training', 1, 'check'),
        ('reboot-with-training', '--orbit-reboot-with-training', 'reboot_with_training', 1, 'check'),
        ('init-zq-calibration', '--orbit-init-zq-calibration', 'init_zq_calibration', 1, 'check'),
        ('zq-calibration', '--orbit-zq-calibration', 'zq_calibration', 1, 'check'),
        ('zq-calibration-period', '--orbit-zq-calibration-period', 'zq_calibration_period', 48000, 'int'),
        ('phy-idle-cnt-th', '--orbit-phy-idle-cnt-th', 'phy_idle_cnt_th', 128, 'int'),
        ('phy-low-power', '--orbit-phy-low-power', 'phy_low_power', 0, 'check'),
        ('dynamic-power-down', '--orbit-dynamic-power-down', 'dynamic_power_down', 1, 'check'),
        ('dynamic-power-down-threshold', '--orbit-dynamic-power-down-threshold', 'dynamic_power_down_threshold', 2048, 'int'),
        ('dynamic-self-refresh', '--orbit-dynamic-self-refresh', 'dynamic_self_refresh', 1, 'check'),
        ('dynamic-self-refresh-threshold', '--orbit-dynamic-self-refresh-threshold', 'dynamic_self_refresh_threshold', 2048, 'int'),
        ('periodic-training', '--orbit-periodic-training', 'periodic_training', 1, 'check'),
        ('periodic-training-period', '--orbit-periodic-training-period', 'periodic_training_period', 50000, 'int'),
        ('temp-sensing', '--orbit-temp-sensing', 'temp_sensing', 1, 'check'),
        ('temp-sensing-period', '--orbit-temp-sensing-period', 'temp_sensing_period', 32000, 'int'),
        ('t-refiab', '--orbit-t-refiab', 't_refiab', 3904000, 'int'),
        ('t-refipb', '--orbit-t-refipb', 't_refipb', 488000, 'int'),
        ('t-zqcal', '--orbit-t-zqcal', 't_zqcal', 1000000, 'int'),
        ('regional-clock-gating', '--orbit-regional-clock-gating', 'regional_clock_gating', 1, 'check'),
        ('dram-clock-gating', '--orbit-dram-clock-gating', 'dram_clock_gating', 1, 'check'),
        ('phy-clock-gating', '--orbit-phy-clock-gating', 'phy_clock_gating', 0, 'check'),
    ]
    if dram_type == 'lpddr5':
        orbit_fields.extend([
            ('orbit-dsm-en', '--orbit-dsm-en', 'dsm_en', 0, 'check'),
            ('orbit-zq-bg-mode', '--orbit-zq-bg-mode', 'zq_bg_mode', 1, 'check'),
        ])

    orbit_json = {}
    for gui_name, cli_flag, json_key, default, kind in orbit_fields:
        if kind == 'check':
            value = 1 if is_checked(params.get(gui_name)) else 0
        else:
            value = to_int(params.get(gui_name))
            if value is None:
                value = default
        cmd.extend([cli_flag, str(value)])
        orbit_json[json_key] = value

    orbit_json['rank_interleaving'] = 1 if is_checked(params.get('orbit-rank-interleaving')) else 0
    orbit_json['num_rank'] = num_rank or 1
    orbit_json['dfs_lvl_t_ck'] = [
        to_int(params.get('dfs-lvl-t-ck-0')) or 0,
        to_int(params.get('dfs-lvl-t-ck-1')) or 0,
        to_int(params.get('dfs-lvl-t-ck-2')) or 0,
    ]
    orbit_json['dq_width'] = to_int(params.get('dq-width')) or 16
    cmd.extend(['--orbit-rank-interleaving', str(orbit_json['rank_interleaving'])])

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
