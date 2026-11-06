#!/usr/bin/env python3
"""
Python implementation of the orbit_config struct and helpers.

The layout below mirrors
``SCP-firmware/product/arise2/module/arise2_omc/include/arise2_omc.h``
as of the 2026-10-26 header (ORBIT_ECC disabled, which is the default build
configuration).  Keep this file in sync with:

  * SCP-firmware/.../include/arise2_omc.h       (struct layout)
  * SCP-firmware/.../include/ddr_config.h       (default values/logic)

Run ``tests/test_struct_layout.sh`` after changing either side; it compiles the
C header and diffs every field offset against this module.
"""

import ctypes
from ctypes import c_uint8, c_uint16, c_uint32, c_uint64, Structure

# Constants from arise2_config.h
DRAM0_BASE = 0x0080000000
RESERVED1_BASE = 0x0100000000
DRAM0_SIZE = RESERVED1_BASE - DRAM0_BASE  # 0x0080000000

DRAM1_BASE = 0x0880000000
PCIE1_ECM_BASE = 0x1000000000
DRAM1_SIZE = PCIE1_ECM_BASE - DRAM1_BASE  # 0x0780000000

OMC_REGISTER_BASE0_0 = 0x51120000
OMC_REGISTER_BASE0_1 = 0x51130000
OMC_REGISTER_BASE1_0 = 0x51140000
OMC_REGISTER_BASE1_1 = 0x51150000
PHY_REGISTER_BASE0_0 = 0x51160000
PHY_REGISTER_BASE0_1 = 0x51170000
PHY_REGISTER_BASE1_0 = 0x51180000
PHY_REGISTER_BASE1_1 = 0x51190000

EMMC_CM4_TIME_TB_SIZE = 0x00000800
# The SCP build pads each per-DRAM timing-table image to 4 KiB before merging.
# The orbit_config prefix is written at EMMC_CM4_TIME_TB_SIZE; everything after
# ``offsetof(struct orbit_config, prbs_result)`` is runtime training data and is
# not part of the generated image.
TIMING_TABLE_BIN_SIZE = 0x00001000

# Number of timing-table slots (MAXSIZEOF_TIMINGTAB in arise2_omc.h).
MAXSIZEOF_TIMINGTAB = 4

# Density codes from orbit_init_gen.h
DENSITY_1 = 0
DENSITY_2 = 1
DENSITY_3 = 2
DENSITY_4 = 3
DENSITY_6 = 4
DENSITY_8 = 5
DENSITY_12 = 6
DENSITY_16 = 7
DENSITY_24 = 8
DENSITY_32 = 9

from orbit_tables import get_density_code  # noqa: E402  (canonical table)

# Enums from arise2_omc.h (partial)
CH_128 = 0
CH_256 = 1
BG_NOINT = 0
PAGE_SIZE_32 = 1
PAGE_SIZE_16 = 2
PAGE_SIZE_8 = 3
BY_MC = 0
BY_PHY_IDLE = 1
BY_PHY_PD = 2
BY_PHY_SR = 3
BY_PHY_SRPD = 4


class chip_config(Structure):
    _fields_ = [
        ("size", c_uint32),
        ("num_bg", c_uint32),
        ("num_bank", c_uint32),
        ("num_row", c_uint32),
        ("num_col", c_uint32),
    ]


class train_result_t(Structure):
    _fields_ = [
        ("lock_value_init", c_uint32),
        ("rd_deskew_center_dm_cs0", c_uint32),
        ("rd_deskew_center_cs0", c_uint32 * 8),
        ("rd_deskew_left_dm_cs0", c_uint32),
        ("rd_deskew_left_cs0", c_uint32 * 8),
        ("rd_dqs_vwmc_cs0", c_uint32),
        ("rd_dqs_vwml_cs0", c_uint32),
        ("rd_deskew_center_dm_cs1", c_uint32),
        ("rd_deskew_center_cs1", c_uint32 * 8),
        ("rd_deskew_left_dm_cs1", c_uint32),
        ("rd_deskew_left_cs1", c_uint32 * 8),
        ("rd_dqs_vwmc_cs1", c_uint32),
        ("rd_dqs_vwml_cs1", c_uint32),
        ("wr_deskewc_cs0", c_uint32 * 8),
        ("dm_deskewc_cs0", c_uint32),
        ("ecc_deskewc_cs0", c_uint32),
        ("wr_deskewl_cs0", c_uint32 * 8),
        ("dm_deskewl_cs0", c_uint32),
        ("ecc_deskewl_cs0", c_uint32),
        ("wr_byte0_cyc_cs0_code", c_uint32),
        ("wr_byte1_cyc_cs0_code", c_uint32),
        ("wr_deskewc_cs1", c_uint32 * 8),
        ("dm_deskewc_cs1", c_uint32),
        ("ecc_deskewc_cs1", c_uint32),
        ("wr_deskewl_cs1", c_uint32 * 8),
        ("dm_deskewl_cs1", c_uint32),
        ("ecc_deskewl_cs1", c_uint32),
        ("wr_byte0_cyc_cs1_code", c_uint32),
        ("wr_byte1_cyc_cs1_code", c_uint32),
    ]


class prbs_result_t(Structure):
    _fields_ = [
        ("offsetr0_cs0", c_uint16),
        ("offsetr1_cs0", c_uint16),
        ("offsetw0_cs0", c_uint16),
        ("offsetw1_cs0", c_uint16),
        ("offsetr0_cs1", c_uint16),
        ("offsetr1_cs1", c_uint16),
        ("offsetw0_cs1", c_uint16),
        ("offsetw1_cs1", c_uint16),
    ]


def make_orbit_config_class(dram_type='lpddr4', two_channel=False):
    """Create an orbit_config ctypes class for the requested configuration.

    ``dram_type`` selects the conditional LP4/LP5 MR fields.  ``two_channel``
    selects NUM_OF_OMC/NUM_OF_PHY (2 vs 4), which changes both the per-PHY
    arrays and the total struct size.

    ORBIT_ECC is not modelled: the default Arise2 build does not define it and
    the generated binary is consumed by a non-ECC firmware build.  If a future
    build enables ORBIT_ECC, the struct gains fields and every offset after
    ``omc_channel`` shifts.
    """
    include_lp5 = (dram_type.lower() == 'lpddr5')
    num_of_omc = 4 if two_channel else 2
    num_of_phy = num_of_omc

    fields = []
    # Fields in exact order as arise2_omc.h (ORBIT_ECC disabled).
    fields.append(("dram_boot", c_uint8))
    fields.append(("ch_intr_size", c_uint8))
    fields.append(("bg_intr_size", c_uint8))
    fields.append(("fsp_op", c_uint8))
    fields.append(("fsp_wr", c_uint8))
    fields.append(("dq_vref_byte0", c_uint8 * (num_of_phy * 2)))
    fields.append(("dq_vref_byte1", c_uint8 * (num_of_phy * 2)))
    fields.append(("ca_vref", c_uint8 * (num_of_phy * 2)))
    fields.append(("phy_dq_vref_b0", c_uint8 * num_of_phy))
    fields.append(("phy_dq_vref_b1", c_uint8 * num_of_phy))
    fields.append(("phy_dqs_vref_b0", c_uint8 * num_of_phy))
    fields.append(("phy_dqs_vref_b1", c_uint8 * num_of_phy))
    fields.append(("dcm_mr30", c_uint8 * (num_of_phy * 2)))

    if include_lp5:
        for name in ("lp5_mr2", "lp5_mr3", "lp5_mr10", "lp5_mr11",
                     "lp5_mr12", "lp5_mr16", "lp5_mr17", "lp5_mr18",
                     "zq_bg_mode"):
            fields.append((name, c_uint8))
    else:
        for name in ("lp4_mr1", "lp4_mr2", "lp4_mr3", "lp4_mr11",
                     "lp4_mr12", "lp4_mr13", "lp4_mr14", "lp4_mr22"):
            fields.append((name, c_uint8))

    fields.append(("omc_channel", c_uint8))
    fields.append(("ca_vref_valid", c_uint8 * (num_of_phy * 2)))
    fields.append(("dram_vref_valid", c_uint8 * 2))
    fields.append(("ca_vref_vwm_sum", c_uint16 * (num_of_phy * 2)))

    fields.append(("phy_freq_ratio", c_uint16))
    fields.append(("omc_freq_ratio", c_uint16))
    fields.append(("int_cpipe_depth", c_uint16))
    fields.append(("int_dpipe_depth", c_uint16))
    fields.append(("cpipe_depth", c_uint16))
    fields.append(("dpipe_depth", c_uint16))

    fields.append(("reboot", c_uint16))
    fields.append(("reqq_depth", c_uint16))
    fields.append(("density", c_uint16))
    fields.append(("rank_interleaving", c_uint16))
    fields.append(("num_rank", c_uint16))
    fields.append(("reboot_with_mrw", c_uint16))
    fields.append(("ctrl_dq_width", c_uint16))
    fields.append(("dq_width", c_uint16))
    fields.append(("use_dfi_train_if", c_uint16))
    fields.append(("phy_ind_mode_en", c_uint16))
    fields.append(("phy_low_power", c_uint16))
    fields.append(("phy_idle_cnt_th", c_uint16))
    fields.append(("lp_wakeup", c_uint16 * (MAXSIZEOF_TIMINGTAB - 1)))
    fields.append(("half_dq_en", c_uint16))

    if not include_lp5:
        fields.append(("lpddr4_rpre", c_uint16))

    fields.append(("rfm_en", c_uint16))
    fields.append(("dsm_en", c_uint16))
    fields.append(("ca_odt", c_uint16))
    fields.append(("phy_odt", c_uint16))
    fields.append(("otd_ck", c_uint16))
    fields.append(("otd_cs", c_uint16))
    fields.append(("otd_ca", c_uint16))
    fields.append(("init_zq_calibration", c_uint16))

    fields.append(("temp_sensing", c_uint16))
    fields.append(("zq_calibration", c_uint16))
    fields.append(("periodic_training", c_uint16))
    fields.append(("periodic_training_period", c_uint16))
    fields.append(("dynamic_power_down", c_uint16))
    fields.append(("dynamic_self_refresh", c_uint16))

    fields.append(("regional_clock_gating", c_uint16))
    fields.append(("phy_clock_gating", c_uint16))
    fields.append(("dram_clock_gating", c_uint16))

    fields.append(("dfs_lvl_t_ck", c_uint16 * (MAXSIZEOF_TIMINGTAB - 1)))
    fields.append(("num_of_region", c_uint16))

    fields.append(("initial_training", c_uint16))
    fields.append(("command_bus_training", c_uint16))
    fields.append(("ca_vref_training", c_uint16))
    fields.append(("prbs_training", c_uint16))
    fields.append(("reboot_with_training", c_uint16))
    fields.append(("phy_vref_trn_mode", c_uint16))
    fields.append(("phy_duty_trn_mode", c_uint16))
    fields.append(("dram_vref_trn_mode", c_uint16))
    fields.append(("dram_duty_trn_mode", c_uint16))

    # omc_dram_density_t is unsigned int in the generated orbit_init_gen.h.
    fields.append(("density_code", c_uint32))
    fields.append(("dram_vref_center", c_uint32 * 2))
    fields.append(("dram_vref_vwm_sum", c_uint32 * 2))
    fields.append(("timingtable_size", c_uint32))
    fields.append(("rclk_t_ck", c_uint32))
    fields.append(("boot_t_ck", c_uint32))
    fields.append(("boot_t_ck_low", c_uint32))
    fields.append(("dram_t_ck", c_uint32))
    fields.append(("prev_dram_t_ck", c_uint32))

    fields.append(("chip", chip_config * 2))
    fields.append(("num_of_ch", c_uint32 * 2))
    fields.append(("base_addr", c_uint32))
    fields.append(("base_addr_id", c_uint32 * num_of_omc))
    fields.append(("phy_base_addr", c_uint32))
    fields.append(("phy_base_addr_id", c_uint32 * num_of_phy))
    fields.append(("tphyupd_resp", c_uint32))
    fields.append(("dynamic_self_refresh_threshold", c_uint32))
    fields.append(("dynamic_power_down_threshold", c_uint32))
    fields.append(("zq_calibration_period", c_uint32))
    fields.append(("tctrlupd_interval", c_uint32))
    fields.append(("temp_sensing_period", c_uint32))
    fields.append(("t_refipb", c_uint32))
    fields.append(("t_refiab", c_uint32))
    fields.append(("t_zqcal", c_uint32))
    fields.append(("link_err_cnt_th", c_uint32))
    fields.append(("mrr_byte_lane", c_uint32))
    fields.append(("byte_lane_inversion", c_uint32))

    fields.append(("region_start", c_uint64 * 2))
    fields.append(("region_end", c_uint64 * 2))

    fields.append(("prbs_result", prbs_result_t * num_of_phy))
    fields.append(("train_result", train_result_t * num_of_phy * MAXSIZEOF_TIMINGTAB))

    # The C struct is declared with #pragma pack(8): natural 8-byte alignment
    # for uint64, 4 for uint32, 2 for uint16.
    class_dict = {
        '_pack_': 8,
        '_fields_': fields,
    }
    cls_name = 'orbit_config_' + dram_type + ('_2ch' if two_channel else '_1ch')
    return type(cls_name, (Structure,), class_dict)


# Default class (LPDDR4 single channel) for backward compatibility.
orbit_config = make_orbit_config_class('lpddr4', False)


def create_orbit_config(dram_type='lpddr4', two_channel=False):
    """Create and zero an orbit_config instance for the given configuration."""
    cls = make_orbit_config_class(dram_type, two_channel)
    return cls()  # ctypes zero-initializes all fields


def orbit_config_prefix_size(dram_type='lpddr4', two_channel=False):
    """Size of the serialized orbit_config prefix (through region_end).

    The firmware image only stores the configuration prefix; ``prbs_result``
    and ``train_result`` are runtime training results.  This is also the number
    of bytes the SCP build's ``ddr_config.bin`` contains.
    """
    cls = make_orbit_config_class(dram_type, two_channel)
    return cls.prbs_result.offset
