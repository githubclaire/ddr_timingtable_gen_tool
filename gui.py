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


def generate_ddr_config_h(params):
    """Generate ddr_config.h with full template matching ddr_config.h.template."""
    dram_type = params.get('dram-type', 'lpddr4')
    cpipe_depth = int(params.get('cpipe-depth', 1))
    dpipe_depth = int(params.get('dpipe-depth', 1))
    orbit_density = int(params.get('orbit-config-density', 16))
    dq_width = int(params.get('dq-width', 16))
    mrr_byte_lane = get_mrr_byte_lane(dq_width)
    two_channel = params.get('two-channel', 'false') == 'true'
    byte_mode = int(params.get('orbit-byte-mode', 0))
    mixed = int(params.get('orbit-mixed', 0))
    
    rank_interleaving = 1 if params.get('orbit-rank-interleaving') == 'true' else 0
    num_rank = int(params.get('orbit-num-rank', 2))
    reboot_with_mrw = 1 if params.get('orbit-reboot-with-mrw') == 'true' else 0
    rfm_en = 1 if params.get('orbit-rfm-en') == 'true' else 0
    dsm_en = 1 if params.get('orbit-dsm-en') == 'true' else 0
    ca_odt = 1 if params.get('orbit-ca-odt') == 'true' else 0
    
    eye_scan_rd_en = 1 if params.get('eye-scan-rd-en') == 'true' else 0
    eye_scan_wr_en = 1 if params.get('eye-scan-wr-en') == 'true' else 0
    eye_scan_prbs_rd_en = 1 if params.get('eye-scan-prbs-rd-en') == 'true' else 0
    eye_scan_prbs_wr_en = 1 if params.get('eye-scan-prbs-wr-en') == 'true' else 0
    phy_vref_trn_mode = 1 if params.get('phy-vref-trn-mode') == 'true' else 0
    phy_duty_trn_mode = 1 if params.get('phy-duty-trn-mode') == 'true' else 0
    dram_vref_trn_mode = 1 if params.get('dram-vref-trn-mode') == 'true' else 0
    dram_duty_trn_mode = 1 if params.get('dram-duty-trn-mode') == 'true' else 0
    command_bus_training = 1 if params.get('command-bus-training') == 'true' else 0
    ca_vref_training = 1 if params.get('ca-vref-training') == 'true' else 0
    prbs_training = 1 if params.get('prbs-training') == 'true' else 0
    reboot_with_training = 1 if params.get('reboot-with-training') == 'true' else 0
    
    regional_clock_gating = 1 if params.get('regional-clock-gating') == 'true' else 0
    dram_clock_gating = 1 if params.get('dram-clock-gating') == 'true' else 0
    phy_clock_gating = 1 if params.get('phy-clock-gating') == 'true' else 0
    phy_low_power = 1 if params.get('phy-low-power') == 'true' else 0
    
    zq_calibration_period = int(params.get('zq-calibration-period', 48000))
    periodic_training = 1 if params.get('periodic-training') == 'true' else 0
    periodic_training_period = int(params.get('periodic-training-period', 24000))
    temp_sensing = 1 if params.get('temp-sensing') == 'true' else 0
    temp_sensing_period = int(params.get('temp-sensing-period', 32000))
    t_refiab = int(params.get('t-refiab', 3904000))
    t_refipb = int(params.get('t-refipb', 488000))
    t_zqcal = int(params.get('t-zqcal', 1000000))
    
    dfs_lvl_t_ck_0 = int(params.get('dfs-lvl-t-ck-0', 938))
    dfs_lvl_t_ck_1 = int(params.get('dfs-lvl-t-ck-1', 1631))
    dfs_lvl_t_ck_2 = int(params.get('dfs-lvl-t-ck-2', 2500))
    
    dfs_training = 1 if params.get('dfs-training') == 'true' else 0
    init_zq_calibration = 1 if params.get('init-zq-calibration') == 'true' else 0
    zq_calibration = 1 if params.get('zq-calibration') == 'true' else 0
    
    if dram_type == 'lpddr5':
        dram_t_ck = '1256'
        dram_type_macro = '5'
        omc_freq_ratio = 1
        phy_freq_ratio = 1
        zq_bg_mode = int(params.get('zq-bg-mode', 1))
    else:
        dram_t_ck = '471'
        dram_type_macro = '2'
        omc_freq_ratio = 2
        phy_freq_ratio = 2
        zq_bg_mode = 0
    
    content = f'''#ifndef __DDR_CONFIG__
#define __DDR_CONFIG__

#include <stdint.h>

#define DRAM_TYPE_LPDDR{dram_type.upper()}
#define DDR_TYPE {dram_type_macro}

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
        is_lpddr5 = True  # Dual channel implies LPDDR5
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
    
    # Method 3: Check dual channel flag in orbit config at offset 0x800
    if file_size > 0x800 + 0x30:
        two_ch_flag = struct.unpack('<H', data[0x800 + 0x30:0x800 + 0x32])[0]
        if two_ch_flag > 0:
            is_dual_channel = True
    
    dram_type = 'lpddr5' if is_lpddr5 else 'lpddr4'
    
    # Apply manual override if specified
    if dram_type_override and dram_type_override != 'auto':
        dram_type = dram_type_override
    
    # Parse timing table for periods (at offset 0x0)
    # Each entry is 0x128 bytes, t_ck is at offset + 4 from freq
    periods = []
    entry_size = 0x128
    max_entries = 8  # Max reasonable periods
    for i in range(max_entries):
        offset = i * entry_size + 4
        if offset + 4 > len(data):
            break
        t_ck = struct.unpack('<I', data[offset:offset+4])[0]
        # Valid t_ck range: 300-5000 ps
        if 300 <= t_ck <= 5000:
            periods.append(t_ck)
        else:
            break
    
    if not periods:
        periods = [471, 938, 1631, 2500]  # Default
    
    # Parse orbit config at offset 0x800
    orbit_offset = 0x800
    
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
                'dq_width': 16,
                'speed_bin': '4266' if dram_type == 'lpddr4' else '6400',
                'periods': ' '.join(map(str, periods)),
                'min_dram_tck': 314,
            },
            
            'pipe': {
                'cpipe_depth': 1,
                'dpipe_depth': 1,
                'omc_freq_ratio': 1 if dram_type == 'lpddr5' else 2,
                'phy_freq_ratio': 1 if dram_type == 'lpddr5' else 2,
                'wire_length': 10,
            },
            
            'timing': {
                'write_odt_upto': 1250 if dram_type == 'lpddr4' else 10000,
                'read_dbi_upto': 10000,
                'write_dbi_upto': 10000,
                'read_lecc_upto': 0,
                'write_lecc_upto': 0,
            },
            
            'orbit': {}
        }
    }
    
    # Read orbit config fields
    try:
        with open(file_path, 'rb') as f:
            # Common fields - dfs_lvl_t_ck at offsets 0x5e/0x60/0x62
            fields_to_read = [
                ('density', 0x1c if dram_type == 'lpddr4' else 0x24, '<H'),
                ('density_code', 0x78 if dram_type == 'lpddr4' else 0x80, '<I'),
                ('cpipe_depth', 0x30, '<H'),
                ('dpipe_depth', 0x32, '<H'),
                ('rank_interleaving', 0x3a, '<H'),
                ('num_rank', 0x3c, '<H'),
                ('dfs_lvl_t_ck_0', 0x5e, '<H'),
                ('dfs_lvl_t_ck_1', 0x60, '<H'),
                ('dfs_lvl_t_ck_2', 0x62, '<H'),
            ]
            
            orbit_data = {}
            for field_name, field_offset, fmt in fields_to_read:
                f.seek(orbit_offset + field_offset)
                bytes_read = f.read(struct.calcsize(fmt))
                if bytes_read:
                    value = struct.unpack(fmt, bytes_read)[0]
                    if 'dfs_lvl_t_ck' in field_name:
                        if 'dfs_lvl_t_ck' not in orbit_data:
                            orbit_data['dfs_lvl_t_ck'] = []
                        orbit_data['dfs_lvl_t_ck'].append(value)
                    else:
                        orbit_data[field_name] = value
            
            # Set orbit config
            result['data']['orbit'] = {
                'density': orbit_data.get('density', 16),
                'density_code': orbit_data.get('density_code', 0),
                'cpipe_depth': orbit_data.get('cpipe_depth', 1),
                'dpipe_depth': orbit_data.get('dpipe_depth', 1),
                'rank_interleaving': orbit_data.get('rank_interleaving', 1),
                'num_rank': orbit_data.get('num_rank', 2),
                'dfs_lvl_t_ck': orbit_data.get('dfs_lvl_t_ck', [938, 1631, 2500]),
                'two_channel': 1 if is_dual_channel else 0,
                'byte_mode': 0,
                'mixed': 0,
                'reboot_with_mrw': 0,
                'rfm_en': 0,
                'dsm_en': 0,
                'ca_odt': 0,
                'eye_scan_rd_en': 0,
                'eye_scan_wr_en': 0,
                'command_bus_training': 0,
                'regional_clock_gating': 1,
                'dram_clock_gating': 1,
                'phy_clock_gating': 0,
                'zq_calibration_period': 48000,
                't_refiab': 3904000,
                't_refipb': 488000,
                'mrr_byte_lane': hex(get_mrr_byte_lane(16)),
            }
            
            # Set basic params
            result['data']['basic']['dq_width'] = 16
            result['data']['orbit']['density'] = orbit_data.get('density', 16)
            
    except Exception as e:
        result['data']['orbit']['error'] = f'Parse error: {str(e)}'
    
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
            
            # Build gen_timing_params command
            cmd = [sys.executable, 'gen_timing_params']
            cmd.extend(['--dram-type', params.get('dram-type', 'lpddr4')])
            cmd.extend(['--densities', str(params.get('orbit-config-density', 16))])
            cmd.extend(['--phy-name', params.get('phy-name', 'sphy-v9r8')])
            cmd.extend(['--speed-bin', params.get('speed-bin', '4266')])
            dq_width = params.get('dq-width', '16')
            cmd.extend(['--dq-width', dq_width])
            
            # Pipe params
            cmd.extend(['--cpipe-depth', str(params.get('cpipe-depth', 1))])
            cmd.extend(['--dpipe-depth', str(params.get('dpipe-depth', 1))])
            
            # Frequency ratios
            dram_type = params.get('dram-type', 'lpddr4')
            cmd.extend(['--omc-freq-ratio', str(params.get('omc-freq-ratio', 2))])
            cmd.extend(['--phy-freq-ratio', str(params.get('phy-freq-ratio', 2))])
            
            # Timing params
            if params.get('wire-length'):
                cmd.extend(['--wire-length', str(params.get('wire-length'))])
            if params.get('write-odt-upto'):
                cmd.extend(['--write-odt-upto', str(params.get('write-odt-upto'))])
            if params.get('read-dbi-upto'):
                cmd.extend(['--read-dbi-upto', str(params.get('read-dbi-upto'))])
            if params.get('write-dbi-upto'):
                cmd.extend(['--write-dbi-upto', str(params.get('write-dbi-upto'))])
            if params.get('min-dram-tck'):
                cmd.extend(['--min-dram-tck', str(params.get('min-dram-tck'))])
            if params.get('dram-tck'):
                cmd.extend(['--dram-tck', str(params.get('dram-tck'))])
            if params.get('read-lecc-upto'):
                cmd.extend(['--read-lecc-upto', str(params.get('read-lecc-upto'))])
            if params.get('write-lecc-upto'):
                cmd.extend(['--write-lecc-upto', str(params.get('write-lecc-upto'))])
            
            # LPDDR4 specific
            if dram_type == 'lpddr4':
                if params.get('wdqs-ctrl-mode'):
                    cmd.extend(['--wdqs-ctrl-mode', str(params.get('wdqs-ctrl-mode'))])
                if params.get('variable-trrd') == 'true':
                    cmd.append('--variable-trrd')
                if params.get('txsr-as-1st-ed') == 'true':
                    cmd.append('--txsr-as-1st-ed')
            else:
                if params.get('wck-1to4-upto'):
                    cmd.extend(['--wck-1to4-upto', str(params.get('wck-1to4-upto'))])
                if params.get('wck-always-on-from'):
                    cmd.extend(['--wck-always-on-from', str(params.get('wck-always-on-from'))])
                if params.get('wck-always-on-upto'):
                    cmd.extend(['--wck-always-on-upto', str(params.get('wck-always-on-upto'))])
            
            # Orbit config
            if params.get('two-channel') == 'true':
                cmd.append('--two-channel')
            if params.get('orbit-config-density'):
                cmd.extend(['--orbit-config-density', str(params.get('orbit-config-density'))])
            if params.get('orbit-byte-mode'):
                cmd.extend(['--orbit-byte-mode', str(params.get('orbit-byte-mode'))])
            if params.get('orbit-mixed'):
                cmd.extend(['--orbit-mixed', str(params.get('orbit-mixed'))])
            if params.get('orbit-rank-interleaving') == 'true':
                cmd.extend(['--orbit-rank-interleaving', '1'])
            if params.get('orbit-num-rank'):
                cmd.extend(['--orbit-num-rank', str(params.get('orbit-num-rank'))])
            if params.get('orbit-reboot-with-mrw') == 'true':
                cmd.append('--orbit-reboot-with-mrw')
            if params.get('orbit-rfm-en') == 'true':
                cmd.append('--orbit-rfm-en')
            if params.get('orbit-dsm-en') == 'true':
                cmd.append('--orbit-dsm-en')
            if params.get('orbit-ca-odt') == 'true':
                cmd.append('--orbit-ca-odt')
            if params.get('orbit-config-use-python') == 'true':
                cmd.append('--orbit-config-use-python')
            
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
            
            try:
                config_h = generate_ddr_config_h(params)
                with open('ddr_config.h', 'w') as f:
                    f.write(config_h)
                message.append("ddr_config.h generated successfully")
            except Exception as e:
                message.append(f"Error generating ddr_config.h: {e}")
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
