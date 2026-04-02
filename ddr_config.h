#ifndef __DDR_CONFIG__
#define __DDR_CONFIG__

#include <stdint.h>

#define DRAM_TYPE_LPDDR4
#define DDR_TYPE 2

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
