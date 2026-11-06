#!/usr/bin/env python3
"""
Python implementation of ddr_config_init() and orbit_update_chips().

Reference: SCP-firmware/product/arise2/module/arise2_omc/include/ddr_config.h
(2026-11-05) and arise2_omc.h (2026-10-26).

The generated binary is byte-identical to the C path (ddr_config_bin.c +
ddr_config.h.template) for the same inputs; tests/test_c_python_parity.py
enforces this.
"""

import ctypes

from orbit_config import (
    orbit_config, chip_config, get_density_code, create_orbit_config,
    DRAM0_BASE, DRAM0_SIZE, DRAM1_BASE, DRAM1_SIZE,
    OMC_REGISTER_BASE0_0, OMC_REGISTER_BASE0_1,
    OMC_REGISTER_BASE1_0, OMC_REGISTER_BASE1_1,
    PHY_REGISTER_BASE0_0, PHY_REGISTER_BASE0_1,
    PHY_REGISTER_BASE1_0, PHY_REGISTER_BASE1_1,
    CH_256, BG_NOINT, PAGE_SIZE_8, BY_MC, MAXSIZEOF_TIMINGTAB,
    TIMING_TABLE_BIN_SIZE, EMMC_CM4_TIME_TB_SIZE, orbit_config_prefix_size,
)

# Frequency tables used by ddr_config.h.  The LP5 table defaults to the
# "max6000" set currently compiled into SCP-firmware; the max6400 set is kept
# for boards that still use the 6400 speed grade.  Both are ordered fastest
# (smallest tCK) first and are indexed by DDR_FREQ_LEVEL.
LP5_T_CK_SETS = {
    '6000': (1332, 1428, 1672, 2512),   # 6000/5600/4800/3200 MT/s
    '6400': (1256, 1428, 1672, 2512),   # 6368/5600/4800/3200 MT/s
}
LP4_T_CK_SET = (471, 938, 1631, 2500)


def safe_setattr(cfg, name, value):
    """Set attribute if it exists, otherwise ignore (LP4/LP5 differences)."""
    if hasattr(cfg, name):
        setattr(cfg, name, value)


def orbit_update_chips(cfg, byte_mode, mixed, dram_type):
    """Update chip geometry (mirrors orbit_update_chips() in ddr_config.h)."""
    density = cfg.density
    for i in range(cfg.num_rank):
        if i == 1 and mixed:
            density *= 2
        cfg.chip[i].num_col = 10
        cfg.chip[i].num_bg = 0

        if dram_type == 'lpddr4':
            cfg.chip[i].num_bank = 3
            if density == 2:
                cfg.chip[i].num_row = 14 + (1 if byte_mode == 1 else 0)
            elif density in (3, 4):
                cfg.chip[i].num_row = 15 + (1 if byte_mode == 1 else 0)
            elif density in (6, 8):
                cfg.chip[i].num_row = 16 + (1 if byte_mode == 1 else 0)
            elif density in (12, 16):
                cfg.chip[i].num_row = 17 + (1 if byte_mode == 1 else 0)
        else:
            cfg.chip[i].num_bank = 4
            if density == 2:
                cfg.chip[i].num_row = 13 + (1 if byte_mode == 1 else 0)
            elif density in (3, 4):
                cfg.chip[i].num_row = 14 + (1 if byte_mode == 1 else 0)
            elif density in (6, 8):
                cfg.chip[i].num_row = 15 + (1 if byte_mode == 1 else 0)
            elif density in (12, 16):
                cfg.chip[i].num_row = 16 + (1 if byte_mode == 1 else 0)
            elif density in (24, 32):
                cfg.chip[i].num_row = 17 + (1 if byte_mode == 1 else 0)


def _t_ck_set(dram_type, ddr_freq_level, lp5_freq_set):
    if dram_type == 'lpddr5':
        key = str(lp5_freq_set or '6000')
        if key not in LP5_T_CK_SETS:
            raise ValueError("lp5_freq_set must be '6000' or '6400', got %r" % lp5_freq_set)
        table = LP5_T_CK_SETS[key]
    else:
        table = LP4_T_CK_SET
    if not 0 <= int(ddr_freq_level) < MAXSIZEOF_TIMINGTAB:
        raise ValueError("ddr_freq_level must be in [0, %d]" % (MAXSIZEOF_TIMINGTAB - 1))
    return table


def ddr_config_init(cfg, dram_type='lpddr5', two_channel=False, density=16,
                    byte_mode=0, mixed=0, default_ch=0, ddr_freq_level=0,
                    lp5_freq_set='6000', **kwargs):
    """Initialize an orbit_config struct with SCP-firmware defaults.

    Parameters mirror ddr_config.h.  Any keyword argument matching a scalar
    struct field overrides that field after the defaults are applied.
    """
    # --- Clock / timingtable_size / DFS levels -----------------------------
    cfg.reboot = 0
    cfg.rclk_t_ck = 20000
    cfg.boot_t_ck = 20000
    cfg.boot_t_ck_low = 83333

    t_ck_set = _t_ck_set(dram_type, ddr_freq_level, lp5_freq_set)
    level = int(ddr_freq_level)
    cfg.timingtable_size = MAXSIZEOF_TIMINGTAB - level
    cfg.dram_t_ck = t_ck_set[level]
    # Remaining (slower) points go into dfs_lvl_t_ck; unused slots stay zero.
    for i in range(MAXSIZEOF_TIMINGTAB - 1):
        src = level + 1 + i
        cfg.dfs_lvl_t_ck[i] = t_ck_set[src] if src < MAXSIZEOF_TIMINGTAB else 0

    # --- Density ------------------------------------------------------------
    cfg.density = int(density)
    if 'density_code' in kwargs:
        cfg.density_code = int(kwargs['density_code'])
    else:
        cfg.density_code = get_density_code(cfg.density)

    # --- Training control (modified defaults in current firmware) ----------
    cfg.initial_training = kwargs.get('initial_training', 1)
    cfg.phy_vref_trn_mode = kwargs.get('phy_vref_trn_mode', 1)
    cfg.phy_duty_trn_mode = kwargs.get('phy_duty_trn_mode', 1)
    cfg.dram_vref_trn_mode = kwargs.get('dram_vref_trn_mode', 1)
    cfg.dram_duty_trn_mode = kwargs.get('dram_duty_trn_mode', 1)
    cfg.command_bus_training = kwargs.get('command_bus_training', 1)
    cfg.ca_vref_training = kwargs.get('ca_vref_training', 1)
    cfg.prbs_training = kwargs.get('prbs_training', 1)
    cfg.reboot_with_training = kwargs.get('reboot_with_training', 1)
    cfg.init_zq_calibration = kwargs.get('init_zq_calibration', 1)
    cfg.zq_calibration = kwargs.get('zq_calibration', 1)
    cfg.zq_calibration_period = kwargs.get('zq_calibration_period', 48000)

    # --- DRAM address configuration ----------------------------------------
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

    # --- APB base addresses / active OMC channel ---------------------------
    if two_channel:
        cfg.omc_channel = 2
        cfg.base_addr = OMC_REGISTER_BASE0_0
        cfg.phy_base_addr = PHY_REGISTER_BASE0_0
        cfg.base_addr_id[0] = OMC_REGISTER_BASE0_0
        cfg.base_addr_id[1] = OMC_REGISTER_BASE0_1
        cfg.base_addr_id[2] = OMC_REGISTER_BASE1_0
        cfg.base_addr_id[3] = OMC_REGISTER_BASE1_1
        cfg.phy_base_addr_id[0] = PHY_REGISTER_BASE0_0
        cfg.phy_base_addr_id[1] = PHY_REGISTER_BASE0_1
        cfg.phy_base_addr_id[2] = PHY_REGISTER_BASE1_0
        cfg.phy_base_addr_id[3] = PHY_REGISTER_BASE1_1
    elif int(default_ch) == 1:
        cfg.omc_channel = 1
        cfg.base_addr = OMC_REGISTER_BASE1_0
        cfg.phy_base_addr = PHY_REGISTER_BASE1_0
        cfg.base_addr_id[0] = OMC_REGISTER_BASE1_0
        cfg.base_addr_id[1] = OMC_REGISTER_BASE1_1
        cfg.phy_base_addr_id[0] = PHY_REGISTER_BASE1_0
        cfg.phy_base_addr_id[1] = PHY_REGISTER_BASE1_1
    else:
        cfg.omc_channel = 0
        cfg.base_addr = OMC_REGISTER_BASE0_0
        cfg.phy_base_addr = PHY_REGISTER_BASE0_0
        cfg.base_addr_id[0] = OMC_REGISTER_BASE0_0
        cfg.base_addr_id[1] = OMC_REGISTER_BASE0_1
        cfg.phy_base_addr_id[0] = PHY_REGISTER_BASE0_0
        cfg.phy_base_addr_id[1] = PHY_REGISTER_BASE0_1

    # --- Customer request spec (fixed) -------------------------------------
    if dram_type == 'lpddr5':
        cfg.phy_freq_ratio = kwargs.get('phy_freq_ratio', 1)
        cfg.omc_freq_ratio = kwargs.get('omc_freq_ratio', 1)
    else:
        cfg.phy_freq_ratio = kwargs.get('phy_freq_ratio', 2)
        cfg.omc_freq_ratio = kwargs.get('omc_freq_ratio', 2)

    cfg.int_cpipe_depth = kwargs.get('int_cpipe_depth', 1)
    cfg.int_dpipe_depth = kwargs.get('int_dpipe_depth', 1)
    cfg.cpipe_depth = kwargs.get('cpipe_depth', cfg.int_cpipe_depth)
    cfg.dpipe_depth = kwargs.get('dpipe_depth', cfg.int_dpipe_depth)
    cfg.dram_boot = BY_MC
    cfg.reqq_depth = 40
    cfg.ctrl_dq_width = 16
    cfg.dq_width = kwargs.get('dq_width', 16)
    cfg.ch_intr_size = CH_256

    dq_w = cfg.dq_width
    if dq_w == 32:
        default_lane = 0x11
    elif dq_w == 8:
        default_lane = 0xFF
    else:
        default_lane = 0x55
    cfg.mrr_byte_lane = kwargs.get('mrr_byte_lane', default_lane)
    cfg.byte_lane_inversion = kwargs.get('byte_lane_inversion', 0)
    cfg.chip[0].size = cfg.density * cfg.ctrl_dq_width // cfg.dq_width
    cfg.chip[1].size = cfg.density * cfg.ctrl_dq_width // cfg.dq_width
    cfg.fsp_op = 0
    cfg.fsp_wr = 0

    # --- Customer request spec (modifiable) --------------------------------
    cfg.rank_interleaving = kwargs.get('rank_interleaving', 1)
    cfg.num_rank = kwargs.get('num_rank', 1)
    cfg.reboot_with_mrw = kwargs.get('reboot_with_mrw', 1)

    # --- Memory features ----------------------------------------------------
    cfg.rfm_en = kwargs.get('rfm_en', 1)
    cfg.dsm_en = kwargs.get('dsm_en', 0)
    cfg.ca_odt = kwargs.get('ca_odt', 1)
    cfg.phy_odt = kwargs.get('phy_odt', 5)
    cfg.otd_ck = kwargs.get('otd_ck', 1)
    cfg.otd_cs = kwargs.get('otd_cs', 1)
    cfg.otd_ca = kwargs.get('otd_ca', 1)
    if dram_type == 'lpddr5':
        safe_setattr(cfg, 'zq_bg_mode', kwargs.get('zq_bg_mode', 1))
    else:
        safe_setattr(cfg, 'lpddr4_rpre',
                     kwargs.get('lpddr4_rpre', 1 if cfg.dram_t_ck > 937 else 0))

    # --- PHY feature --------------------------------------------------------
    cfg.phy_ind_mode_en = 0

    # --- Periodic training / power management ------------------------------
    cfg.periodic_training = kwargs.get('periodic_training', 1)
    cfg.periodic_training_period = kwargs.get('periodic_training_period', 50000)
    cfg.temp_sensing = kwargs.get('temp_sensing', 1)
    cfg.temp_sensing_period = kwargs.get('temp_sensing_period', 32000)
    cfg.dynamic_self_refresh = kwargs.get('dynamic_self_refresh', 1)
    cfg.dynamic_self_refresh_threshold = kwargs.get(
        'dynamic_self_refresh_threshold', 2048)
    cfg.dynamic_power_down = kwargs.get('dynamic_power_down', 1)
    cfg.dynamic_power_down_threshold = kwargs.get(
        'dynamic_power_down_threshold', 2048)
    cfg.regional_clock_gating = kwargs.get('regional_clock_gating', 1)
    cfg.dram_clock_gating = kwargs.get('dram_clock_gating', 1)
    cfg.phy_clock_gating = kwargs.get('phy_clock_gating', 0)
    cfg.phy_low_power = kwargs.get('phy_low_power', 0)
    cfg.phy_idle_cnt_th = kwargs.get('phy_idle_cnt_th', 128)

    if dram_type == 'lpddr5':
        cfg.bg_intr_size = PAGE_SIZE_8
    else:
        cfg.bg_intr_size = BG_NOINT

    # --- Timing parameters --------------------------------------------------
    cfg.t_refiab = kwargs.get('t_refiab', 3904000)
    cfg.t_refipb = kwargs.get('t_refipb', 488000)
    cfg.t_zqcal = kwargs.get('t_zqcal', 1000000)

    if dram_type == 'lpddr5':
        cfg.link_err_cnt_th = kwargs.get('link_err_cnt_th', 2)
    else:
        cfg.link_err_cnt_th = kwargs.get('link_err_cnt_th', 0)

    # --- Unsupported / fixed ------------------------------------------------
    cfg.tctrlupd_interval = 0
    cfg.lp_wakeup[0] = 4
    cfg.lp_wakeup[1] = 4
    cfg.lp_wakeup[2] = 4
    cfg.half_dq_en = 0

    # --- Chip geometry ------------------------------------------------------
    orbit_update_chips(cfg, byte_mode, mixed, dram_type)

    # --- DFS level override (GUI/JSON sends an explicit 3-entry list) ------
    dfs_override = kwargs.get('dfs_lvl_t_ck')
    if dfs_override is not None:
        for i in range(MAXSIZEOF_TIMINGTAB - 1):
            if i < len(dfs_override):
                cfg.dfs_lvl_t_ck[i] = int(dfs_override[i])

    # --- Additional scalar overrides (JSON / CLI) --------------------------
    # ctypes arrays/structures are skipped: assigning a scalar to them fails.
    field_types = dict(cfg._fields_)
    handled = {
        'density', 'density_code', 'phy_freq_ratio', 'omc_freq_ratio',
        'int_cpipe_depth', 'int_dpipe_depth', 'cpipe_depth', 'dpipe_depth',
        'dq_width', 'mrr_byte_lane', 'byte_lane_inversion',
        'rank_interleaving', 'num_rank', 'reboot_with_mrw', 'rfm_en',
        'dsm_en', 'ca_odt', 'phy_odt', 'otd_ck', 'otd_cs', 'otd_ca',
        'zq_bg_mode', 'lpddr4_rpre', 'periodic_training',
        'periodic_training_period', 'temp_sensing', 'temp_sensing_period',
        'dynamic_self_refresh', 'dynamic_self_refresh_threshold',
        'dynamic_power_down', 'dynamic_power_down_threshold',
        'regional_clock_gating', 'dram_clock_gating', 'phy_clock_gating',
        'phy_low_power', 'phy_idle_cnt_th', 't_refiab', 't_refipb',
        't_zqcal', 'link_err_cnt_th', 'initial_training',
        'phy_vref_trn_mode', 'phy_duty_trn_mode', 'dram_vref_trn_mode',
        'dram_duty_trn_mode', 'command_bus_training', 'ca_vref_training',
        'prbs_training', 'reboot_with_training', 'init_zq_calibration',
        'zq_calibration', 'zq_calibration_period',
    }
    for key, value in kwargs.items():
        if key in handled or key not in field_types:
            continue
        ftype = field_types[key]
        if issubclass(ftype, (ctypes.Array, ctypes.Structure)):
            continue
        setattr(cfg, key, int(value))


def generate_orbit_config_binary(dram_type='lpddr5', two_channel=False, density=16,
                                 byte_mode=0, mixed=0, output_file='ddr_timing_table.bin',
                                 offset=0x800, **kwargs):
    """Generate the orbit_config prefix and write it at ``offset``.

    Mirrors the SCP build:
      * timing table occupies 0x000..0x7FF (max 6 LP4 / 5 LP5 entries),
      * orbit_config prefix starts at 0x800,
      * the per-DRAM image is padded to 4 KiB.
    Only the prefix through ``prbs_result`` is written; the runtime training
    result arrays are intentionally excluded.
    """
    if offset != EMMC_CM4_TIME_TB_SIZE:
        raise ValueError("orbit_config must be written at 0x%x" %
                         EMMC_CM4_TIME_TB_SIZE)

    cfg = create_orbit_config(dram_type, two_channel)
    ddr_config_init(cfg, dram_type=dram_type, two_channel=two_channel,
                    density=density, byte_mode=byte_mode, mixed=mixed, **kwargs)

    prefix_len = orbit_config_prefix_size(dram_type, two_channel)
    if offset + prefix_len > TIMING_TABLE_BIN_SIZE:
        raise ValueError("orbit_config prefix does not fit in the 4 KiB image")

    with open(output_file, 'r+b') as f:
        f.seek(0, 2)
        if f.tell() > offset:
            raise ValueError(
                "timing table is %d bytes but the orbit_config area starts at 0x%x; "
                "reduce the number of periods" % (f.tell(), offset))
        f.seek(offset)
        struct_data = ctypes.string_at(ctypes.addressof(cfg), prefix_len)
        f.write(struct_data)
        # Match the SCP build's ``dd bs=1 count=4k`` padding.
        f.truncate(TIMING_TABLE_BIN_SIZE)

    print("Written orbit_config prefix (%d bytes) to %s at offset 0x%x"
          % (prefix_len, output_file, offset))


if __name__ == '__main__':
    generate_orbit_config_binary()
