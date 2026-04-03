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

def generate_ddr_config_h(params):
    """Generate ddr_config.h with full template matching ddr_config.h.template."""
    dram_type = params.get('dram-type', 'lpddr4')
    cpipe_depth = safe_int(params.get('cpipe-depth'), 1)
    dpipe_depth = safe_int(params.get('dpipe-depth'), 1)
    orbit_density = safe_int(params.get('orbit-config-density'), 16)
    dq_width = safe_int(params.get('dq-width'), 16)
    mrr_byte_lane = get_mrr_byte_lane(dq_width)
    two_channel = is_checked(params.get('two-channel'))
    byte_mode = safe_int(params.get('orbit-byte-mode'), 0)
    mixed = safe_int(params.get('orbit-mixed'), 0)
    
    rank_interleaving = 1 if is_checked(params.get('orbit-rank-interleaving')) else 0
    num_rank = safe_int(params.get('orbit-num-rank'), 2)
    reboot_with_mrw = 1 if is_checked(params.get('orbit-reboot-with-mrw')) else 0
    rfm_en = 1 if is_checked(params.get('orbit-rfm-en')) else 0
    dsm_en = 1 if is_checked(params.get('orbit-dsm-en')) else 0
    ca_odt = 1 if is_checked(params.get('orbit-ca-odt')) else 0
    
    eye_scan_rd_en = 1 if is_checked(params.get('eye-scan-rd-en')) else 0
    eye_scan_wr_en = 1 if is_checked(params.get('eye-scan-wr-en')) else 0
    eye_scan_prbs_rd_en = 1 if is_checked(params.get('eye-scan-prbs-rd-en')) else 0
    eye_scan_prbs_wr_en = 1 if is_checked(params.get('eye-scan-prbs-wr-en')) else 0
    phy_vref_trn_mode = 1 if is_checked(params.get('phy-vref-trn-mode')) else 0
    phy_duty_trn_mode = 1 if is_checked(params.get('phy-duty-trn-mode')) else 0
    dram_vref_trn_mode = 1 if is_checked(params.get('dram-vref-trn-mode')) else 0
    dram_duty_trn_mode = 1 if is_checked(params.get('dram-duty-trn-mode')) else 0
    command_bus_training = 1 if is_checked(params.get('command-bus-training')) else 0
    ca_vref_training = 1 if is_checked(params.get('ca-vref-training')) else 0
    prbs_training = 1 if is_checked(params.get('prbs-training')) else 0
    reboot_with_training = 1 if is_checked(params.get('reboot-with-training')) else 0
    
    regional_clock_gating = 1 if is_checked(params.get('regional-clock-gating')) else 0
    dram_clock_gating = 1 if is_checked(params.get('dram-clock-gating')) else 0
    phy_clock_gating = 1 if is_checked(params.get('phy-clock-gating')) else 0
    phy_low_power = 1 if is_checked(params.get('phy-low-power')) else 0
    
    zq_calibration_period = safe_int(params.get('zq-calibration-period'), 48000)
    periodic_training = 1 if is_checked(params.get('periodic-training')) else 0
    periodic_training_period = safe_int(params.get('periodic-training-period'), 24000)
    temp_sensing = 1 if is_checked(params.get('temp-sensing')) else 0
    temp_sensing_period = safe_int(params.get('temp-sensing-period'), 32000)
    t_refiab = safe_int(params.get('t-refiab'), 3904000)
    t_refipb = safe_int(params.get('t-refipb'), 488000)
    t_zqcal = safe_int(params.get('t-zqcal'), 1000000)
    
    dfs_lvl_t_ck_0 = safe_int(params.get('dfs-lvl-t-ck-0'), 938)
    dfs_lvl_t_ck_1 = safe_int(params.get('dfs-lvl-t-ck-1'), 1631)
    dfs_lvl_t_ck_2 = safe_int(params.get('dfs-lvl-t-ck-2'), 2500)
    dfs_lvl_t_ck_1 = int(params.get('dfs-lvl-t-ck-1', 1631))
    dfs_lvl_t_ck_2 = int(params.get('dfs-lvl-t-ck-2', 2500))
    
    dfs_training = 1 if is_checked(params.get('dfs-training')) else 0
    init_zq_calibration = 1 if is_checked(params.get('init-zq-calibration')) else 0
    zq_calibration = 1 if is_checked(params.get('zq-calibration')) else 0
    
    if dram_type == 'lpddr5':
        dram_t_ck = '1256'
        dram_type_macro = '5'
        omc_freq_ratio = 1
        phy_freq_ratio = 1
        min_dram_tck = safe_int(params.get('min-dram-tck'), 1256)
        bg_mode_upto = safe_int(params.get('bg-mode-upto'), 0)
        zq_bg_mode = 1 if bg_mode_upto >= min_dram_tck else 0
    else:
        dram_t_ck = '471'
        dram_type_macro = '2'
        omc_freq_ratio = 2
        phy_freq_ratio = 2
        zq_bg_mode = 0
    
    content = f'''#ifndef __DDR_CONFIG__
#define __DDR_CONFIG__

#include <stdint.h>

'''
    if dram_type == 'lpddr5':
        content += '#define DRAM_TYPE_LPDDR5\n'
    else:
        content += '#define DRAM_TYPE_LPDDR4\n'
    content += f'#define DDR_TYPE {dram_type_macro}\n'
    content += '''
#define OMC_REGISTER_BASE0_0   0x20000000
#define OMC_REGISTER_BASE0_1   0x21000000
#define PHY_REGISTER_BASE0_0   0x10000000
#define PHY_REGISTER_BASE0_1   0x11000000

#define DRAM0_BASE  0x80000000
#define DRAM0_SIZE  0x40000000
#define DRAM1_BASE  0x100000000
#define DRAM1_SIZE  0x40000000

#define BY_MC  0
#define DDR_TWO_CHANNEL {'1' if two_channel else '0'}
#define ORBIT_DENSITY {orbit_density}
#define CPIPE_DEPTH {cpipe_depth}
#define DPIPE_DEPTH {dpipe_depth}
#define MRR_BYTE_LANE {hex(mrr_byte_lane)}

struct orbit_config;
struct chip_config;
struct train_result_t;
struct prbs_result_t;

static void ddr_config_init(struct orbit_config *omc_config);

void orbit_update_chips(struct orbit_config *cfg, uint8_t byte_mode, uint8_t mixed) {{
  int i;
  int density = cfg->density;

  for (i=0; i<cfg->num_rank; i++) {{
    if (i==1 && mixed) density *= 2;
    cfg->chip[i].num_col = 10;
    cfg->chip[i].num_bg  = 0;
#ifdef DRAM_TYPE_LPDDR4
      cfg->chip[i].num_bank = 3;
      switch (density) {{
        case 2:
          cfg->chip[i].num_row = 14 + ((byte_mode == 1) ? 1: 0);
          break;
        case 3:
        case 4:
          cfg->chip[i].num_row = 15 + ((byte_mode == 1) ? 1: 0);
          break;
        case 6:
        case 8:
          cfg->chip[i].num_row = 16 + ((byte_mode == 1) ? 1: 0);
          break;
        case 12:
        case 16:
          cfg->chip[i].num_row = 17 + ((byte_mode == 1) ? 1: 0);
          break;
      }}
#endif
#ifdef DRAM_TYPE_LPDDR5
      cfg->chip[i].num_bank = 4;
      switch (density) {{
        case 2:
          cfg->chip[i].num_row = 13 + ((byte_mode == 1) ? 1: 0);
          break;
        case 3:
        case 4:
          cfg->chip[i].num_row = 14 + ((byte_mode == 1) ? 1 : 0);
          break;
        case 6:
        case 8:
          cfg->chip[i].num_row = 15 + ((byte_mode == 1) ? 1 : 0);
          break;
        case 12:
        case 16:
          cfg->chip[i].num_row = 16 + ((byte_mode == 1) ? 1 : 0);
          break;
        case 24:
        case 32:
          cfg->chip[i].num_row = 17 + ((byte_mode == 1) ? 1 : 0);
          break;
      }}
#endif
  }}
}}

static unsigned int get_density_code(unsigned int density) {{
  switch (density) {{
    case 1: return 0;
    case 2: return 1;
    case 3: return 2;
    case 4: return 3;
    case 6: return 4;
    case 8: return 5;
    case 12: return 6;
    case 16: return 7;
    case 24: return 8;
    case 32: return 9;
    default: return 0;
  }}
}}

static void ddr_config_init(struct orbit_config *omc_config)
{{
  memset(omc_config, 0, sizeof(struct orbit_config));

  omc_config->reboot = 0;
  omc_config->rclk_t_ck = 41666;
  omc_config->boot_t_ck = 20000;
  omc_config->boot_t_ck_low = 83333;
#ifdef DRAM_TYPE_LPDDR5
  omc_config->dram_t_ck = {dram_t_ck};
#else
  omc_config->dram_t_ck = {dram_t_ck};
#endif
  omc_config->density = ORBIT_DENSITY;
  omc_config->density_code = get_density_code(omc_config->density);

  omc_config->num_of_region = 2;
  omc_config->region_start[0] = (DRAM0_BASE);
  omc_config->region_end[0]   = (DRAM0_BASE + DRAM0_SIZE - 1);
  omc_config->num_of_ch[0] = 2;
  omc_config->region_start[1] = (DRAM1_BASE);
  omc_config->region_end[1]   = (DRAM1_BASE + DRAM1_SIZE - 1);
  omc_config->num_of_ch[1] = 2;

#if (DDR_TWO_CHANNEL)
  omc_config->region_start[0] /= 2;
  omc_config->region_end[0]   /= 2;
  omc_config->region_start[1] /= 2;
  omc_config->region_end[1]   /= 2;
#endif

  omc_config->base_addr = (uintptr_t)OMC_REGISTER_BASE0_0;
  omc_config->phy_base_addr = (uintptr_t)PHY_REGISTER_BASE0_0;

  omc_config->base_addr_id[0] = (uintptr_t)OMC_REGISTER_BASE0_0;
  omc_config->base_addr_id[1] = (uintptr_t)OMC_REGISTER_BASE0_1;
  omc_config->phy_base_addr_id[0] = (uintptr_t)PHY_REGISTER_BASE0_0 ;
  omc_config->phy_base_addr_id[1] = (uintptr_t)PHY_REGISTER_BASE0_1 ;
#if DDR_TWO_CHANNEL
  omc_config->base_addr_id[2] = (uintptr_t)OMC_REGISTER_BASE1_0;
  omc_config->base_addr_id[3] = (uintptr_t)OMC_REGISTER_BASE1_1;
  omc_config->phy_base_addr_id[2] = (uintptr_t)PHY_REGISTER_BASE1_0 ;
  omc_config->phy_base_addr_id[3] = (uintptr_t)PHY_REGISTER_BASE1_1 ;
#endif

#ifdef DRAM_TYPE_LPDDR5
  omc_config->phy_freq_ratio = 1;
  omc_config->omc_freq_ratio = 1;
#else
  omc_config->phy_freq_ratio = 2;
  omc_config->omc_freq_ratio = 2;
#endif
  omc_config->int_cpipe_depth = {cpipe_depth};
  omc_config->int_dpipe_depth = {dpipe_depth};
  omc_config->cpipe_depth = 0 + omc_config->int_cpipe_depth;
  omc_config->dpipe_depth = 0 + omc_config->int_dpipe_depth;
  omc_config->dram_boot = BY_MC;
  omc_config->reqq_depth = 40;
  omc_config->ctrl_dq_width = {dq_width};
  omc_config->dq_width = {dq_width};
  omc_config->ch_intr_size = CH_256;
  omc_config->mrr_byte_lane = {hex(mrr_byte_lane)};
  omc_config->byte_lane_inversion = 0;
  omc_config->chip[0].size = omc_config->density*omc_config->ctrl_dq_width/omc_config->dq_width;
  omc_config->chip[1].size = omc_config->density*omc_config->ctrl_dq_width/omc_config->dq_width;
  omc_config->fsp_op = 0;
  omc_config->fsp_wr = 0;

  omc_config->rank_interleaving = {rank_interleaving};
  omc_config->num_rank = {num_rank};
  omc_config->reboot_with_mrw = {reboot_with_mrw};

  omc_config->rfm_en = {rfm_en};
  omc_config->dsm_en = {dsm_en};
  omc_config->ca_odt = {ca_odt};
#ifdef DRAM_TYPE_LPDDR5
  omc_config->zq_bg_mode = {zq_bg_mode};
#else
  if (omc_config->dram_t_ck > 937) {{
    omc_config->lpddr4_rpre = 1;
  }} else {{
    omc_config->lpddr4_rpre = 0;
  }}
#endif

  omc_config->phy_ind_mode_en = 0;

  omc_config->eye_scan_rd_en        = {eye_scan_rd_en};
  omc_config->eye_scan_wr_en        = {eye_scan_wr_en};
  omc_config->eye_scan_prbs_rd_en   = {eye_scan_prbs_rd_en};
  omc_config->eye_scan_prbs_wr_en   = {eye_scan_prbs_wr_en};      
  omc_config->phy_vref_trn_mode     = {phy_vref_trn_mode};
  omc_config->phy_duty_trn_mode     = {phy_duty_trn_mode};
  omc_config->dram_vref_trn_mode    = {dram_vref_trn_mode};
  omc_config->dram_duty_trn_mode    = {dram_duty_trn_mode};
  omc_config->command_bus_training  = {command_bus_training};
  omc_config->ca_vref_training      = {ca_vref_training};
  omc_config->prbs_training         = {prbs_training};
  omc_config->reboot_with_training  = {reboot_with_training};
  omc_config->init_zq_calibration   = {init_zq_calibration};
  omc_config->zq_calibration        = {zq_calibration};
  omc_config->zq_calibration_period = {zq_calibration_period};
  omc_config->dfs_training         = {dfs_training};

  omc_config->periodic_training = {periodic_training};
  omc_config->periodic_training_period = {periodic_training_period};

#ifdef DRAM_TYPE_LPDDR5
  omc_config->dfs_lvl_t_ck[0] = {dfs_lvl_t_ck_0};
  omc_config->dfs_lvl_t_ck[1] = {dfs_lvl_t_ck_1};
  omc_config->dfs_lvl_t_ck[2] = {dfs_lvl_t_ck_2};
#else
  omc_config->dfs_lvl_t_ck[0] = {dfs_lvl_t_ck_0};
  omc_config->dfs_lvl_t_ck[1] = {dfs_lvl_t_ck_1};
  omc_config->dfs_lvl_t_ck[2] = {dfs_lvl_t_ck_2};
#endif

  omc_config->temp_sensing = {temp_sensing};
  omc_config->temp_sensing_period = {temp_sensing_period};
  omc_config->dynamic_self_refresh = 0;
  omc_config->dynamic_self_refresh_threshold = 0;
  omc_config->dynamic_power_down = 0;
  omc_config->dynamic_power_down_threshold = 0;
  omc_config->regional_clock_gating = {regional_clock_gating};
  omc_config->dram_clock_gating = {dram_clock_gating};
  omc_config->phy_clock_gating = {phy_clock_gating};
  omc_config->phy_low_power = {phy_low_power};
  omc_config->phy_idle_cnt_th = 0;
#ifdef DRAM_TYPE_LPDDR5
  omc_config->bg_intr_size = PAGE_SIZE_8;
#else
  omc_config->bg_intr_size = BG_NOINT;
#endif
  omc_config->t_refiab = {t_refiab};
  omc_config->t_refipb = {t_refipb};
  omc_config->t_zqcal = {t_zqcal};
#ifdef DRAM_TYPE_LPDDR5
  omc_config->link_err_cnt_th = 5;
#else
  omc_config->link_err_cnt_th = 0;
#endif

  omc_config->tctrlupd_interval = 0;
  omc_config->lp_wakeup[0] = 4;
  omc_config->lp_wakeup[1] = 4;
  omc_config->lp_wakeup[2] = 4;
  omc_config->half_dq_en = 0;

  orbit_update_chips(omc_config, {byte_mode}, {mixed});
}}

#endif
'''
    return content


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
    # Methods: 1) file size, 2) t_ck pattern at offset 0x04, 3) dual channel flag
    is_lpddr5 = False
    is_dual_channel = False
    
    # Method 1: Check t_ck at offset 0x04 (LPDDR5 typically has 1256, LPDDR4 has 471)
    if file_size >= 4:
        t_ck_at_04 = struct.unpack('<I', data[4:8])[0] if len(data) >= 8 else 0
        # LPDDR5: t_ck=1256 or 796; LPDDR4: t_ck=471
        if t_ck_at_04 in [1256, 796]:
            is_lpddr5 = True
        elif t_ck_at_04 == 471:
            is_lpddr5 = False  # Explicit LPDDR4 marker
    
    # Method 2: File size thresholds (fallback)
    # LPDDR4 single: 5096, LPDDR5 single: 5104
    # LPDDR4 dual: 7864, LPDDR5 dual: 7872
    # Use tighter thresholds: >= 7860 = dual channel
    if file_size >= 7860:
        is_dual_channel = True
        # Don't assume LPDDR5 - dual channel can be LPDDR4 too
    elif file_size >= 5090 and file_size < 5200:
        # Single channel - check t_ck to differentiate
        if file_size >= 5100:
            is_lpddr5 = True  # 5104 = LPDDR5
        # Otherwise keep t_ck detection result
    elif file_size >= 3050:
        if not is_lpddr5:  # Only if t_ck didn't detect
            is_lpddr5 = True
    elif file_size < 3000:
        return {'success': False, 'message': f'File too small to be valid binary: {file_size} bytes'}
    
    # Method 3: Check dual channel via phy_base_addr_id[2] (most reliable)
    # LPDDR4: 0x8E0, LPDDR5: 0x8E8 (due to 9-byte header shift)
    # Non-zero value at this offset indicates dual channel
    if file_size > 0x800 + 0xE0:
        dual_check_offset = 0x8E8 if is_lpddr5 else 0x8E0
        phy_addr_id_2 = struct.unpack('<I', data[dual_check_offset:dual_check_offset+4])[0]
        if phy_addr_id_2 != 0:
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
    entry_size = 0x128
    max_entries = 8
    
    for i in range(max_entries):
        offset = i * entry_size
        if offset + 4 > len(data):
            break
        t_ck = struct.unpack('<I', data[offset+4:offset+8])[0] if len(data) >= offset + 8 else 0
        if 300 <= t_ck <= 5000:
            periods.append(t_ck)
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
            # LPDDR5 default periods
            periods = [1256, 796, 556, 2500]
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
                dfs_offsets = (0x6E, 0x70, 0x72)
                fields_to_read = [
                    # Pipe config (LPDDR5 specific offsets)
                    ('phy_freq_ratio', 0x14, '<H'),
                    ('omc_freq_ratio', 0x16, '<H'),
                    ('cpipe_depth', 0x1C, '<H'),
                    ('dpipe_depth', 0x1E, '<H'),
                    
                    # Basic geometry
                    ('density', 0x24, '<H'),
                    ('rank_interleaving', 0x26, '<H'),
                    ('num_rank', 0x28, '<H'),
                    ('ctrl_dq_width', 0x2C, '<H'),
                    ('dq_width', 0x2E, '<H'),
                    
                    # Mode control
                    ('reboot_with_mrw', 0x2A, '<H'),
                    ('rfm_en', 0x46, '<H'),
                    ('dsm_en', 0x48, '<H'),
                    ('ca_odt', 0x52, '<H'),
                    
                    # Training enable
                    ('eye_scan_rd_en', 0x4A, '<H'),
                    ('eye_scan_wr_en', 0x4C, '<H'),
                    ('eye_scan_prbs_rd_en', 0x4E, '<H'),
                    ('eye_scan_prbs_wr_en', 0x50, '<H'),
                    ('init_zq_calibration', 0x56, '<H'),
                    ('command_bus_training', 0x72, '<H'),
                    ('ca_vref_training', 0x74, '<H'),
                    ('prbs_training', 0x76, '<H'),
                    ('reboot_with_training', 0x78, '<H'),
                    ('dfs_training', 0x7A, '<H'),
                    ('phy_vref_trn_mode', 0x7E, '<H'),
                    ('phy_duty_trn_mode', 0x80, '<H'),
                    ('dram_vref_trn_mode', 0x82, '<H'),
                    ('dram_duty_trn_mode', 0x84, '<H'),
                    
                    # Power management
                    ('regional_clock_gating', 0x64, '<H'),
                    ('phy_clock_gating', 0x66, '<H'),
                    ('dram_clock_gating', 0x68, '<H'),
                    
                    # Timing features
                    ('temp_sensing', 0x58, '<H'),
                    ('zq_calibration', 0x5A, '<H'),
                    ('periodic_training', 0x5C, '<H'),
                    ('periodic_training_period', 0x5E, '<H'),
                    
                    # DFS timing
                    ('dfs_lvl_t_ck_0', dfs_offsets[0], '<H'),
                    ('dfs_lvl_t_ck_1', dfs_offsets[1], '<H'),
                    ('dfs_lvl_t_ck_2', dfs_offsets[2], '<H'),
                    
                    # Late fields (LPDDR5 specific offsets after chip config)
                    ('density_code', 0x88, '<I'),
                    ('zq_calibration_period', 0xEC, '<I'),
                    ('temp_sensing_period', 0xF4, '<I'),
                    ('t_refipb', 0xF8, '<I'),
                    ('t_refiab', 0xFC, '<I'),
                    ('t_zqcal', 0x100, '<I'),
                    ('mrr_byte_lane', 0x108, '<I'),
                ]
            else:
                # LPDDR4: use LPDDR4 offsets
                dfs_offsets = (0x5e, 0x60, 0x62)
                fields_to_read = [
                    # Pipe config
                    ('phy_freq_ratio', 0x0c, '<H'),
                    ('omc_freq_ratio', 0x0e, '<H'),
                    ('cpipe_depth', 0x14, '<H'),
                    ('dpipe_depth', 0x16, '<H'),
                    
                    # Basic geometry
                    ('density', 0x1c, '<H'),
                    ('rank_interleaving', 0x1e, '<H'),
                    ('num_rank', 0x20, '<H'),
                    ('ctrl_dq_width', 0x24, '<H'),
                    ('dq_width', 0x26, '<H'),
                    
                    # Mode control
                    ('reboot_with_mrw', 0x22, '<H'),
                    ('rfm_en', 0x3a, '<H'),
                    ('dsm_en', 0x3c, '<H'),
                    ('ca_odt', 0x46, '<H'),
                    
                    # Training enable
                    ('eye_scan_rd_en', 0x3e, '<H'),
                    ('eye_scan_wr_en', 0x40, '<H'),
                    ('eye_scan_prbs_rd_en', 0x42, '<H'),
                    ('eye_scan_prbs_wr_en', 0x44, '<H'),
                    ('init_zq_calibration', 0x4a, '<H'),
                    ('command_bus_training', 0x66, '<H'),
                    ('ca_vref_training', 0x68, '<H'),
                    ('prbs_training', 0x6a, '<H'),
                    ('reboot_with_training', 0x6c, '<H'),
                    ('dfs_training', 0x6e, '<H'),
                    ('phy_vref_trn_mode', 0x72, '<H'),
                    ('phy_duty_trn_mode', 0x74, '<H'),
                    ('dram_vref_trn_mode', 0x76, '<H'),
                    ('dram_duty_trn_mode', 0x78, '<H'),
                    
                    # Power management
                    ('regional_clock_gating', 0x58, '<H'),
                    ('phy_clock_gating', 0x5a, '<H'),
                    ('dram_clock_gating', 0x5c, '<H'),
                    
                    # Timing features
                    ('temp_sensing', 0x4c, '<H'),
                    ('zq_calibration', 0x4e, '<H'),
                    ('periodic_training', 0x50, '<H'),
                    ('periodic_training_period', 0x52, '<H'),
                    
                    # DFS timing
                    ('dfs_lvl_t_ck_0', dfs_offsets[0], '<H'),
                    ('dfs_lvl_t_ck_1', dfs_offsets[1], '<H'),
                    ('dfs_lvl_t_ck_2', dfs_offsets[2], '<H'),
                    
                    # Late fields
                    ('density_code', 0x78, '<I'),
                    ('zq_calibration_period', 0xe4, '<I'),
                    ('temp_sensing_period', 0xec, '<I'),
                    ('t_refipb', 0xf0, '<I'),
                    ('t_refiab', 0xf4, '<I'),
                    ('t_zqcal', 0xf8, '<I'),
                    ('mrr_byte_lane', 0x100, '<I'),
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
                'dram_tck': periods[0] if periods else 471,
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
            
            'orbit': {}
        }
    }
    
    # Set orbit config - use parsed values from binary
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
        'regional_clock_gating': orbit_data.get('regional_clock_gating', 1),
        'phy_clock_gating': orbit_data.get('phy_clock_gating', 0),
        'dram_clock_gating': orbit_data.get('dram_clock_gating', 1),
        'temp_sensing': orbit_data.get('temp_sensing', 0),
        'zq_calibration': orbit_data.get('zq_calibration', 0),
        'periodic_training': orbit_data.get('periodic_training', 0),
        'periodic_training_period': orbit_data.get('periodic_training_period', 0),
        'zq_calibration_period': orbit_data.get('zq_calibration_period', 48000),
        'temp_sensing_period': orbit_data.get('temp_sensing_period', 32000),
        't_refiab': orbit_data.get('t_refiab', 3904000),
        't_refipb': orbit_data.get('t_refipb', 488000),
        't_zqcal': orbit_data.get('t_zqcal', 1000000),
        'mrr_byte_lane': hex(orbit_data.get('mrr_byte_lane', 0x55)),
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
