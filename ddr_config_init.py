#!/usr/bin/env python3
"""
Implementation of ddr_config_init and orbit_update_chips.
"""

from orbit_config import orbit_config, chip_config, get_density_code, create_orbit_config, \
    DRAM0_BASE, DRAM0_SIZE, DRAM1_BASE, DRAM1_SIZE, \
    OMC_REGISTER_BASE0_0, OMC_REGISTER_BASE0_1, \
    OMC_REGISTER_BASE1_0, OMC_REGISTER_BASE1_1, \
    PHY_REGISTER_BASE0_0, PHY_REGISTER_BASE0_1, \
    PHY_REGISTER_BASE1_0, PHY_REGISTER_BASE1_1, \
    CH_256, BG_NOINT, PAGE_SIZE_8, BY_MC

def safe_setattr(cfg, name, value):
    """Set attribute if it exists, otherwise ignore."""
    if hasattr(cfg, name):
        setattr(cfg, name, value)

def orbit_update_chips(cfg, byte_mode, mixed, dram_type):
    """
    Update chip geometry.
    cfg: orbit_config instance
    byte_mode: 0 or 1
    mixed: 0 or 1
    dram_type: 'lpddr4' or 'lpddr5'
    """
    density = cfg.density
    for i in range(cfg.num_rank):
        if i == 1 and mixed:
            density *= 2
        cfg.chip[i].num_col = 10
        cfg.chip[i].num_bg = 0
        if dram_type == 'lpddr4':
            cfg.chip[i].num_bank = 3
            if density in (2,):
                cfg.chip[i].num_row = 14 + (1 if byte_mode == 1 else 0)
            elif density in (3, 4):
                cfg.chip[i].num_row = 15 + (1 if byte_mode == 1 else 0)
            elif density in (6, 8):
                cfg.chip[i].num_row = 16 + (1 if byte_mode == 1 else 0)
            elif density in (12, 16):
                cfg.chip[i].num_row = 17 + (1 if byte_mode == 1 else 0)
            else:
                # default fallback
                cfg.chip[i].num_row = 14
        else:  # lpddr5
            cfg.chip[i].num_bank = 4
            if density in (2,):
                cfg.chip[i].num_row = 13 + (1 if byte_mode == 1 else 0)
            elif density in (3, 4):
                cfg.chip[i].num_row = 14 + (1 if byte_mode == 1 else 0)
            elif density in (6, 8):
                cfg.chip[i].num_row = 15 + (1 if byte_mode == 1 else 0)
            elif density in (12, 16):
                cfg.chip[i].num_row = 16 + (1 if byte_mode == 1 else 0)
            elif density in (24, 32):
                cfg.chip[i].num_row = 17 + (1 if byte_mode == 1 else 0)
            else:
                cfg.chip[i].num_row = 13

def ddr_config_init(cfg, dram_type='lpddr5', two_channel=False, density=16,
                     byte_mode=0, mixed=0, **kwargs):
    """
    Initialize orbit_config struct.
    Parameters:
        cfg: orbit_config instance (will be modified)
        dram_type: 'lpddr4' or 'lpddr5'
        two_channel: boolean for DDR_TWO_CHANNEL macro
        density: density per rank in Gb
        byte_mode: 0 or 1 (for LPDDR4 byte mode)
        mixed: mixed rank density flag
        **kwargs: override any field (field name as keyword)
    """
    # Zero the struct (already done by caller)
    
    # Fixed parameters (lines 63-137)
    cfg.reboot = 0
    cfg.rclk_t_ck = 41666
    cfg.boot_t_ck = 20000
    cfg.boot_t_ck_low = 83333
    if dram_type == 'lpddr5':
        cfg.dram_t_ck = 1256
    else:
        cfg.dram_t_ck = 471
    cfg.density = density
    if 'density_code' in kwargs:
        cfg.density_code = kwargs['density_code']
    else:
        cfg.density_code = get_density_code(cfg.density)
    
    # DRAM Address Configuration
    cfg.num_of_region = 2
    cfg.region_start[0] = DRAM0_BASE
    cfg.region_end[0] = DRAM0_BASE + DRAM0_SIZE - 1
    cfg.num_of_ch[0] = 2
    cfg.region_start[1] = DRAM1_BASE
    cfg.region_end[1] = DRAM1_BASE + DRAM1_SIZE - 1
    cfg.num_of_ch[1] = 2
    
    if two_channel:
        cfg.region_start[0] //= 2
        cfg.region_end[0] //= 2
        cfg.region_start[1] //= 2
        cfg.region_end[1] //= 2
    
    # APB Base Address Configuration
    cfg.base_addr = OMC_REGISTER_BASE0_0
    cfg.phy_base_addr = PHY_REGISTER_BASE0_0
    
    cfg.base_addr_id[0] = OMC_REGISTER_BASE0_0
    cfg.base_addr_id[1] = OMC_REGISTER_BASE0_1
    cfg.phy_base_addr_id[0] = PHY_REGISTER_BASE0_0
    cfg.phy_base_addr_id[1] = PHY_REGISTER_BASE0_1
    
    if two_channel:
        cfg.base_addr_id[2] = OMC_REGISTER_BASE1_0
        cfg.base_addr_id[3] = OMC_REGISTER_BASE1_1
        cfg.phy_base_addr_id[2] = PHY_REGISTER_BASE1_0
        cfg.phy_base_addr_id[3] = PHY_REGISTER_BASE1_1
    
    # Customer Request Spec. (Don't change)
    if dram_type == 'lpddr5':
        cfg.phy_freq_ratio = 1
        cfg.omc_freq_ratio = 1
    else:
        cfg.phy_freq_ratio = 2
        cfg.omc_freq_ratio = 2
    
    cfg.int_cpipe_depth = 1
    cfg.int_dpipe_depth = 1
    cfg.cpipe_depth = 0 + cfg.int_cpipe_depth
    cfg.dpipe_depth = 0 + cfg.int_dpipe_depth
    cfg.dram_boot = BY_MC
    cfg.reqq_depth = 40
    cfg.ctrl_dq_width = 16
    cfg.dq_width = 16
    cfg.ch_intr_size = CH_256
    # mrr_byte_lane depends on physical_dq_width
    # C code hardcodes 0x55 regardless of dq_width
    cfg.mrr_byte_lane = 0x55  # matches C binary
    cfg.byte_lane_inversion = 0
    cfg.chip[0].size = cfg.density * cfg.ctrl_dq_width // cfg.dq_width
    cfg.chip[1].size = cfg.density * cfg.ctrl_dq_width // cfg.dq_width
    cfg.fsp_op = 0
    cfg.fsp_wr = 0
    
    # Customer Request Spec. (Modifiable)
    cfg.rank_interleaving = kwargs.get('rank_interleaving', 1)
    cfg.num_rank = kwargs.get('num_rank', 2)
    cfg.reboot_with_mrw = kwargs.get('reboot_with_mrw', 0)
    
    # Memory Feature (Modifiable)
    cfg.rfm_en = kwargs.get('rfm_en', 0)
    cfg.dsm_en = kwargs.get('dsm_en', 0)
    cfg.ca_odt = kwargs.get('ca_odt', 0)
    if dram_type == 'lpddr5':
        safe_setattr(cfg, 'zq_bg_mode', kwargs.get('zq_bg_mode', 1))
    else:
        if cfg.dram_t_ck > 937:
            safe_setattr(cfg, 'lpddr4_rpre', 1)  # Toggle
        else:
            safe_setattr(cfg, 'lpddr4_rpre', 0)  # Static
    
    # PHY Feature (Don't change)
    cfg.phy_ind_mode_en = 0
    
    # Training control (Modifiable)
    cfg.eye_scan_rd_en = kwargs.get('eye_scan_rd_en', 0)
    cfg.eye_scan_wr_en = kwargs.get('eye_scan_wr_en', 0)
    cfg.eye_scan_prbs_rd_en = kwargs.get('eye_scan_prbs_rd_en', 0)
    cfg.eye_scan_prbs_wr_en = kwargs.get('eye_scan_prbs_wr_en', 0)
    cfg.phy_vref_trn_mode = kwargs.get('phy_vref_trn_mode', 0)
    cfg.phy_duty_trn_mode = kwargs.get('phy_duty_trn_mode', 0)
    cfg.dram_vref_trn_mode = kwargs.get('dram_vref_trn_mode', 0)
    cfg.dram_duty_trn_mode = kwargs.get('dram_duty_trn_mode', 0)
    cfg.command_bus_training = kwargs.get('command_bus_training', 0)
    cfg.ca_vref_training = kwargs.get('ca_vref_training', 0)
    cfg.prbs_training = kwargs.get('prbs_training', 0)
    cfg.reboot_with_training = kwargs.get('reboot_with_training', 0)
    cfg.init_zq_calibration = kwargs.get('init_zq_calibration', 0)
    cfg.zq_calibration = kwargs.get('zq_calibration', 0)
    cfg.zq_calibration_period = kwargs.get('zq_calibration_period', 48000)
    cfg.dfs_training = kwargs.get('dfs_training', 0)
    
    # Training control (Modifiable)
    cfg.periodic_training = kwargs.get('periodic_training', 0)
    cfg.periodic_training_period = kwargs.get('periodic_training_period', 24000)
    
    # All level training control
    if dram_type == 'lpddr5':
        cfg.dfs_lvl_t_ck[0] = 1672
        cfg.dfs_lvl_t_ck[1] = 2224
        cfg.dfs_lvl_t_ck[2] = 5000
    else:
        cfg.dfs_lvl_t_ck[0] = 938
        cfg.dfs_lvl_t_ck[1] = 1631
        cfg.dfs_lvl_t_ck[2] = 2500
    
    # OMC Functions (Modifiable)
    cfg.temp_sensing = kwargs.get('temp_sensing', 0)
    cfg.temp_sensing_period = kwargs.get('temp_sensing_period', 32000)
    cfg.dynamic_self_refresh = kwargs.get('dynamic_self_refresh', 0)
    cfg.dynamic_self_refresh_threshold = kwargs.get('dynamic_self_refresh_threshold', 0)
    cfg.dynamic_power_down = kwargs.get('dynamic_power_down', 0)
    cfg.dynamic_power_down_threshold = kwargs.get('dynamic_power_down_threshold', 0)
    cfg.regional_clock_gating = kwargs.get('regional_clock_gating', 1)
    cfg.dram_clock_gating = kwargs.get('dram_clock_gating', 1)
    cfg.phy_clock_gating = kwargs.get('phy_clock_gating', 0)
    cfg.phy_low_power = kwargs.get('phy_low_power', 0)
    cfg.phy_idle_cnt_th = kwargs.get('phy_idle_cnt_th', 0)
    
    if dram_type == 'lpddr5':
        cfg.bg_intr_size = PAGE_SIZE_8
    else:
        cfg.bg_intr_size = BG_NOINT
    
    # Timing Param
    cfg.t_refiab = kwargs.get('t_refiab', 3904000)
    cfg.t_refipb = kwargs.get('t_refipb', 488000)
    cfg.t_zqcal = kwargs.get('t_zqcal', 1000000)
    
    # OMC features (conditional)
    # ORBIT_ECC not implemented
    if dram_type == 'lpddr5':
        cfg.link_err_cnt_th = kwargs.get('link_err_cnt_th', 5)
    else:
        cfg.link_err_cnt_th = kwargs.get('link_err_cnt_th', 0)
    
    # These features aren't supported. (Don't change)
    cfg.tctrlupd_interval = 0
    cfg.lp_wakeup[0] = 4
    cfg.lp_wakeup[1] = 4
    cfg.lp_wakeup[2] = 4
    cfg.half_dq_en = 0
    
    # Update chip geometry
    orbit_update_chips(cfg, byte_mode, mixed, dram_type)
    
    # Apply any additional overrides (kwargs may contain other fields)
    for key, value in kwargs.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
        else:
            # Try nested attributes (e.g., chip[0].size)
            pass

def generate_orbit_config_binary(dram_type='lpddr5', two_channel=False, density=16,
                                 byte_mode=0, mixed=0, output_file='ddr_timing_table.bin',
                                 offset=0x800, **kwargs):
    """
    Generate orbit_config binary and write to file at offset.
    """
    cfg = create_orbit_config(dram_type, two_channel)
    ddr_config_init(cfg, dram_type=dram_type, two_channel=two_channel,
                    density=density, byte_mode=byte_mode, mixed=mixed, **kwargs)
    import ctypes
    with open(output_file, 'r+b') as f:
        f.seek(offset)
        f.write(ctypes.string_at(ctypes.addressof(cfg), ctypes.sizeof(cfg)))
    print("Written orbit_config to %s at offset 0x%x" % (output_file, offset))

if __name__ == '__main__':
    # Test
    generate_orbit_config_binary()