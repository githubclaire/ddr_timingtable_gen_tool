/*
 * Arm SCP/MCP Software
 * Copyright (c) 2019-2021, Arm Limited and Contributors. All rights reserved.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#ifndef ARISE2_OMC_H
#define ARISE2_OMC_H

#include <stdint.h>
#include "orbit_init_gen.h"
#include "arise2_omc.h"
#include "arise2_config.h"
#include "mr_config_gen.h"

/* DDR type */
#if defined(DDR_TYPE) && (DDR_TYPE == 2)
#define DRAM_TYPE_LPDDR4
#else
#define DRAM_TYPE_LPDDR5
#endif

//Number of timing paramas
#define SIZEOF_TIMING_PARAMS    4

//Number of OMC (PHY) instance
#if DDR_TWO_CHANNEL
#define NUM_OF_OMC    4
#else
#define NUM_OF_OMC    2
#endif
#define NUM_OF_PHY    NUM_OF_OMC

#define NUM_OF_DFS_FREQ    3

#define CLOCK_RATE_REFCLK   (50UL * FWK_MHZ)
#define CLOCK_RATE_SYSCLK   (1600UL * FWK_MHZ)

/* Default for Arise2 SoC */
#define SYSINCLK            (1600UL * FWK_MHZ)

/* DDR frequency in MHz */
#define DDR_FREQUENCY_MHZ   UINT32_C(800)

/* Clock divider */
#define CLKDIV              ((SYSINCLK / (DDR_FREQUENCY_MHZ * FWK_MHZ)) - 1)

//api index for diff module
enum arise2_omc_api_idx {
    ARISE2_OMC_API_IDX_SW_INFO,
    ARISE2_OMC_API_IDX_PHY_V9R8,
    ARISE2_OMC_API_COUNT,
};

enum orbit_grcmd {
  GRCMD_ZQ_START =  0,
  GRCMD_ZQ_LATCH =  1,
  GRCMD_REFAB    =  3,
  GRCMD_ACT      =  4,
  GRCMD_PREPB    =  7,
  GRCMD_PREAB    =  8,
  GRCMD_SRE      =  9,
  GRCMD_PD       = 10,
  GRCMD_SREX     = 11,
  GRCMD_PDX      = 12,
  GRCMD_DSM      = 13,
  GRCMD_WS_FS    = 14,
  GRCMD_WS_OFF   = 15
};

typedef enum {
  OMC_PS_NORMAL = 0,
  OMC_PS_PWR_MODE = 1,
  OMC_PS_DFS = 3,
  OMC_PS_FAILSAFE = 4
} pstate_t;

typedef enum {
  QOS_NORMAL = 0,
  WURGENT = 2,
  SURGENT = 3
} qos_ctrl_t;

typedef enum bank_mode {
  BG_MODE = 0,
  B8_MODE = 1,
  B16_MODE = 2
} bank_mode_t;


#pragma pack(8)

#define CH_128    0
#define CH_256    1

#define BG_NOINT     0
#define PAGE_SIZE_32 1
#define PAGE_SIZE_16 2
#define PAGE_SIZE_8  3

typedef uint8_t ch_intr_size_t;
typedef uint8_t bg_intr_size_t;

// Initializer of DRAM. And state of DRAM when MC take over privilege of DRAM.
#define BY_MC        0
#define BY_PHY_IDLE  1
#define BY_PHY_PD    2
#define BY_PHY_SR    3
#define BY_PHY_SRPD  4

typedef uint8_t dram_boot_t;

struct chip_config {
  uint32_t size; // Gb
  uint32_t num_bg;
  uint32_t num_bank;
  uint32_t num_row;
  uint32_t num_col;
};

typedef struct {
  uint32_t lock_value_init;

  uint32_t rd_deskew_center_dm_cs0;
  uint32_t rd_deskew_center_cs0[8];
  uint32_t rd_deskew_left_dm_cs0;
  uint32_t rd_deskew_left_cs0[8];
  uint32_t rd_dqs_vwmc_cs0;
  uint32_t rd_dqs_vwml_cs0;
  uint32_t rd_deskew_center_dm_cs1;
  uint32_t rd_deskew_center_cs1[8];
  uint32_t rd_deskew_left_dm_cs1;
  uint32_t rd_deskew_left_cs1[8];
  uint32_t rd_dqs_vwmc_cs1;
  uint32_t rd_dqs_vwml_cs1;

  uint32_t wr_deskewc_cs0[8];
  uint32_t dm_deskewc_cs0;
  uint32_t ecc_deskewc_cs0;
  uint32_t wr_deskewl_cs0[8];
  uint32_t dm_deskewl_cs0;
  uint32_t ecc_deskewl_cs0;
  uint32_t wr_byte0_cyc_cs0_code;
  uint32_t wr_byte1_cyc_cs0_code;
  uint32_t wr_deskewc_cs1[8];
  uint32_t dm_deskewc_cs1;
  uint32_t ecc_deskewc_cs1;
  uint32_t wr_deskewl_cs1[8];
  uint32_t dm_deskewl_cs1;
  uint32_t ecc_deskewl_cs1;
  uint32_t wr_byte0_cyc_cs1_code;
  uint32_t wr_byte1_cyc_cs1_code;
} train_result_t;

typedef struct {
  uint16_t offsetr0_cs0;
  uint16_t offsetr1_cs0;
  uint16_t offsetw0_cs0;
  uint16_t offsetw1_cs0;
  uint16_t offsetr0_cs1;
  uint16_t offsetr1_cs1;
  uint16_t offsetw0_cs1;
  uint16_t offsetw1_cs1;
} prbs_result_t;

// Note that FIXED items are not modifiable. Fixed in synthesis time.

struct orbit_config {
  dram_boot_t dram_boot;  // Agent of DRAM initialization. State of DRAM after initialization when the agent is PHY
  ch_intr_size_t ch_intr_size; // FIXED, channel interleaving granularity
  bg_intr_size_t bg_intr_size;
  uint8_t fsp_op;
  uint8_t fsp_wr;
  //uint8_t timing_set;
  uint8_t dq_vref_byte0 [2];
  uint8_t dq_vref_byte1 [2];
  uint8_t ca_vref[2];
#ifdef DRAM_TYPE_LPDDR5
  uint8_t  lp5_mr2;
  uint8_t  lp5_mr3;
  uint8_t  lp5_mr10;
  uint8_t  lp5_mr11;
  uint8_t  lp5_mr12;
  uint8_t  lp5_mr16;
  uint8_t  lp5_mr17;
  uint8_t  lp5_mr18;
  uint8_t  zq_bg_mode;
#endif
#ifdef ORBIT_ECC
  uint8_t  fsecc_code_err_0; // 8bit
  uint8_t  fsecc_code_err_1; // 8bit
  uint8_t  fsecc_code_err_2; // 8bit
  uint8_t  fsecc_code_err_3; // 8bit
  uint16_t fsecc_op_en; // 1: in-line ECC enabled
  uint16_t fsecc_region_op_en; // 1: region based ecc feature enable
                                     // full space ecc enabled     when fsecc_op_en == 1 and fsecc_region_op_en == 0
                                     // regions based  ecc enabled when fsecc_op_en == 1 and fsecc_region_op_en == 1
                              // And DRAM type should be DDR4 DQ x64
#endif
  uint16_t phy_freq_ratio; // = (peroid of dfi_clk) / (period of dfi_phy_clk) of PHY.
  uint16_t omc_freq_ratio; // = (peroid of omc_clk) / (period of dfi_phy_clk) of PHY.
  uint16_t int_cpipe_depth; // controller internal pipe depth of DFI command/control signals
  uint16_t int_dpipe_depth; // controller internal pipe depth of DFI data signals
  uint16_t cpipe_depth; // pipe depth of DFI command/control signals
  uint16_t dpipe_depth; // pipe depth of DFI data signals

  uint16_t reboot;    // 1: reboot, 0: coldboot

  //uint16_t allow_apb_amid_dfs; // APB commands can be issued middle of DFS sequence.
                                   // More specifically, after accepting DFS pstate but before requesting NORMAL pstate.

  //uint32_t phy_version; // Internal PHY version managed by openedges
  //uint16_t split_sapb; // Two secure APB interfaces are implemented in design.
  uint16_t reqq_depth; // FIXED
  uint16_t density; // Gb (depends on connected device)
  uint16_t rank_interleaving; // Enable rank inteleaving
  uint16_t num_rank; // Numerical. Number of ranks (CS) connected to
  uint16_t reboot_with_mrw;
  uint16_t ctrl_dq_width; // FIXED, DQ width of the MC.
  uint16_t dq_width; // DQ width of a device.
  uint16_t use_dfi_train_if;
  uint16_t phy_ind_mode_en; // PHY feature: All initial trainings are performed by PHY.
  uint16_t phy_low_power;   // PHY feature: PHY Lowpower enter/exit with dfi_lp_* handshake
  uint16_t phy_idle_cnt_th; // It is valid only when phy_low_power

  //uint16_t dfs_frequency;   // operation dfi_frequency after boot sequence completed
  uint16_t lp_wakeup[SIZEOF_TIMING_PARAMS - 1];    // dfi_lp_wakeup for each timing_set.

  //uint16_t asp_op_en; // OMC ASP feature enable/disable
  uint16_t half_dq_en; // OMC half DQ feature enable/disable

  //uint16_t scr_op_en;        // 1: scrambler feature enable
  //uint16_t aslr_op_en;       // 1: aslr feature enable

#ifdef DRAM_TYPE_LPDDR4
  uint16_t lpddr4_rpre; // 1: LPDDR4 toggle read pre-amble
#endif

  uint16_t rfm_en; // only for LPDDR4, LPDDR5
  uint16_t dsm_en; // LPDDR5 Deep Sleep Mode. In Power-Off scenario, DRAM goes into DSM.

  //uint16_t read_dbi; // Enable read DBI (depends on memory type)
  //uint16_t write_dbi; // Enable write DBI (depends on memory type)
  //uint16_t read_link_par;  // When LPDDR5, read_dbi and read_link_par can be enabled exclusively.
  //uint16_t write_link_par;
  uint16_t eye_scan_rd_en;
  uint16_t eye_scan_wr_en;
  uint16_t eye_scan_prbs_rd_en;
  uint16_t eye_scan_prbs_wr_en;

  uint16_t ca_odt; // Enable CA ODT (depends on memory type)
  uint16_t phy_odt; // Can set by PHY ODT Value, please check the PHY document.
  uint16_t init_zq_calibration; // Enable boot-up ZQ calibration

  // timing parameters (as us)
  uint16_t temp_sensing; // LPDDR3 and LPDDR4 only. Periodic monitoring MR4 ref_rate and dynamically changing refresh rate
  uint16_t zq_calibration; // Periodic ZQ calibration
  uint16_t periodic_training; // Periodic training
  uint16_t periodic_training_period;
  uint16_t dynamic_power_down; // Dynamic power-down for unloaded rank.
  uint16_t dynamic_self_refresh; // Dynamic self-refresh for unloaded rank.

  // Note: For LPDDR4 self-refresh with power-down mode, two functions should be enabled.
  //
  // If dynamic_power_down_threshold is equal to or larger than dynamic_self_refresh, then
  // No power-down mode be entered. Only self-refresh with power-down mode is utilized.

  uint16_t regional_clock_gating; // Enable internal regional clock gating to reduce power-comsumption
  uint16_t phy_clock_gating; // Enable PHY's clock-gating feature if the PHY has dedicated clock-gating ports
  uint16_t dram_clock_gating; // Enable DRAM's dynamic clok stop function.

  uint16_t dfs_lvl_t_ck[SIZEOF_TIMING_PARAMS - 1];

  uint16_t num_of_region; // number of AXI address spaces

  //int tphy_wrdata_alter;
  //int dfi_wrpath_int_delay;

  //training
  //uint16_t initial_training;     //replace by SPHY_V9R8_EMUL,when SPHY_V9R8_EMUL = 1,initial_training must be 0
  uint16_t command_bus_training;  // Enable Command bus training (LPDDR5/4), Command Bus Training when initial_training is 1.
  uint16_t ca_vref_training;      // Enable CA vref training (LPDDR5/4), Ca vref training when initial_training and command bus training are 1.
  //uint16_t write_leveling;        // Enable Write Leveling when initial_training is 1.
  //uint16_t gate_training;         // Enable Read Gate Training enable when initial_training is 1
  //uint16_t read_training;         // enable Read DQ Calibration enable when initial_training is 1
  //uint16_t write_training;        // enable Write DQ Calibration enable when initial_training is 1
  uint16_t prbs_training;
  uint16_t reboot_with_training;
  uint16_t dfs_training;
  //uint16_t reduced_periodic_training;
  uint16_t phy_vref_trn_mode;
  uint16_t phy_duty_trn_mode;
  uint16_t dram_vref_trn_mode;
  uint16_t dram_duty_trn_mode;
  //uint16_t rddata_en_aft_dqs;

  omc_dram_density_t density_code; // Selected automatically

  uint32_t rclk_t_ck; // reference clock period, pico seconds, normally 26,000 kHz
  uint32_t boot_t_ck; // booting clock period, pico seconds, normally 50,000 kHz
  uint32_t boot_t_ck_low; // When using SPHY, it should be use 24MHz clkphy2x in reset sequence
  uint32_t dram_t_ck; // normal working clock period. normally maximum frequency
  uint32_t prev_dram_t_ck; // frequency before DFS, for using issue dfs command

  struct chip_config chip[2];
  uint32_t num_of_ch[2]; // Number of channel

  uint32_t base_addr;  // Base address of control registers (broadcast)
  uint32_t base_addr_id[NUM_OF_OMC];  // Base address of control registers (control each OMC)
  uint32_t phy_base_addr;  // Base address of control registers (boardcast) 
  uint32_t phy_base_addr_id[NUM_OF_PHY];  // Base address of control registers (control each phy)
  // If one PHY is connected into one OMC, then set phy_base_addr only.
  // If two PHYs are connected into one OMC, then set phy_base_addr_id.
  //uint32_t wdqlvl_bst; //FIXME find appropreate position
  uint32_t tphyupd_resp;
  uint32_t dynamic_self_refresh_threshold; // Unloaded rank will enter self-refresh mode after specified cycles.
  uint32_t dynamic_power_down_threshold; // Unloaded rank will enter power-down mode after specified cycles.
  uint32_t zq_calibration_period;
  uint32_t tctrlupd_interval; // Periodic MC-initiated PHY update
  uint32_t temp_sensing_period;
  //uint32_t abr_granularity; // DDR4 only. Fine granularity refresh. 0: turn-off, 1: fixed 2x, 2: fixed 4x
  // timing parameters (as ps)
  uint32_t t_refipb; // LPDDR3 and LPDDR4 only.
  uint32_t t_refiab; // All memory types.
  uint32_t t_zqcal; // LPDDR4 only
  uint32_t link_err_cnt_th;
  uint32_t mrr_byte_lane;
  // LPDDR3 and LPDDR4.
  // If byte lanes are twisted on board or in package, then select proper byte lane of MRR data in this field.
  // MRR data are loaded on the lowest byte lane of a device.
  //
  // For example, byte lane 2 and byte lane 0 are twisted in x32 LPDDR3 device then setting it to '4' = 4'b0100. (*a)
  //
  // If multiple devices covers full DQ lanes, for example, two x16 LPDDR4 devices are connected to one x32 OMC instance.
  // Selects all the byte lanes. If no byte lane is twisted, then setting it to '5' = 4'b0101. (*b)
  uint32_t byte_lane_inversion;
  // LPDDR3 and LPDDR4
  //
  // In some cases, a MRR byte lane of a DRAM device is reversed (1st pin is connected to 8th. 2nd to 7th, ..., 8th to 1st)
  // due to issues on board or in package.
  //
  // In this case, the reversed byte lane should be indicated correctly.
  // If byte lanes are swapped, then selecte byte lane after swapping.
  //
  // For example, *a case in mrr_byte_lane, the lane also inverted. Then setting it to '4' = 4'b0100.
  // If the 1st byte lane is inverted in *b case, then setting it to '1' = 4'b0001.

#ifdef ORBIT_ECC
  uint32_t ecc_region_base_low_0;
  uint32_t ecc_region_base_high_0;
  uint32_t ecc_region_top_low_0;
  uint32_t ecc_region_top_high_0;

  uint32_t ecc_region_base_low_1;
  uint32_t ecc_region_base_high_1;
  uint32_t ecc_region_top_low_1;
  uint32_t ecc_region_top_high_1;

  uint64_t fsecc_data_err_0; // 64bit
  uint64_t fsecc_data_err_1; // 64bit
  uint64_t fsecc_data_err_2; // 64bit
  uint64_t fsecc_data_err_3; // 64bit
#endif

  uint64_t region_start[2]; // Start address of assigned memory space in your system
  uint64_t region_end[2]; // End address of assigned memory space in your system

  prbs_result_t  prbs_result[NUM_OF_PHY];
  train_result_t train_result[NUM_OF_PHY][SIZEOF_TIMING_PARAMS];
};

struct orbit_reg {
  uint32_t mc_config;
  uint32_t refresh_ctrl;
  uint32_t fsp_ctrl;
  uint32_t dramclk_disable_ctrl;
  uint32_t dpwdn_dsr_ctrl;
  uint32_t phy_lp_ctrl;
  uint32_t pch_ctrl;
  uint32_t phy_ctrl2;
  uint32_t dcg_enable;
};

struct timing_param {
  uint32_t freq; // as mega herz
  uint32_t t_ck; // as picoseconds
  uint32_t timing_zqcal;
  uint32_t timing_param[OMC_NUM_TIMING_PARAMS];
  uint32_t timing_param_derate[OMC_NUM_DERATE_PARAMS];
  uint32_t dfi_timing_param[OMC_NUM_DFI_TIMING_PARAMS];
  uint16_t t_rfcab[OMC_NUM_DENSITIES];
  uint16_t t_rfcpb[OMC_NUM_DENSITIES];
  uint16_t t_rfmab[OMC_NUM_DENSITIES];
  uint16_t t_rfmpb[OMC_NUM_DENSITIES];
  uint16_t t_refdpr[OMC_NUM_DENSITIES];
  uint16_t tx_pbr2pbr[OMC_NUM_DENSITIES];
  uint16_t t_xsr[OMC_NUM_DENSITIES];
  uint16_t t_xsdll[OMC_NUM_DENSITIES];
  uint16_t t_xs_fast[OMC_NUM_DENSITIES];
  uint8_t wck_ratio;
  uint8_t tlp_resp;
  uint8_t auto_dqs_clean;
  uint8_t dll_enable;
  uint8_t write_odt;
  uint8_t nt_odt;
  uint8_t write_dbi;
  uint8_t read_dbi;
  uint8_t wpste;
  uint8_t rpste;
  uint8_t rl;
  uint8_t wl;
  uint8_t mr_rl;
  uint8_t mr_wl;
  uint8_t mr_wr;
  uint8_t mr_rtp;
  uint8_t mr_cal;
  uint8_t mr_tccd_l;
  // here: new added - 2021-0817
  uint8_t bank_mode;
  uint8_t wck_fm;
  uint8_t rdqs_pst_mode;
  uint8_t rdqs_pst;
  uint8_t rdqs_pre;
  uint8_t wck_pst;
  uint8_t wck_on;
  uint8_t read_link_parity;
  uint8_t write_link_parity;
  uint8_t t_rtw;
  uint8_t t_wtr_a;
  uint8_t t_wtr;
  uint8_t t_rc;
  uint8_t trddata_en;
};
#pragma pack()
#endif  /* ARISE2_OMC_H */
