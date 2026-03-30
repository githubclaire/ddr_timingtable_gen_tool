

void orbit_update_chips(struct orbit_config *cfg, uint8_t byte_mode, uint8_t mixed) {
  int i;
  int density = cfg->density;

  for (i=0; i<cfg->num_rank; i++) {
    if (i==1 && mixed) density *= 2;
    cfg->chip[i].num_col = 10;
    cfg->chip[i].num_bg  = 0;
#ifdef DRAM_TYPE_LPDDR4
      cfg->chip[i].num_bank = 3;
      switch (density) {
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
      }
#endif
#ifdef DRAM_TYPE_LPDDR5
      cfg->chip[i].num_bank = 4;
      switch (density) {
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
      }
#endif
  }
}

//init omc_config
static void ddr_config_init(struct orbit_config *omc_config)
{
  memset(omc_config, 0, sizeof(struct orbit_config));

  omc_config->reboot = 0;
  omc_config->rclk_t_ck = 41666;
  omc_config->boot_t_ck = 20000;
  omc_config->boot_t_ck_low = 83333;
#ifdef DRAM_TYPE_LPDDR5
  omc_config->dram_t_ck = 1256;
#else
  omc_config->dram_t_ck = 471;
#endif
  omc_config->density = 16;  // for each rank
  omc_config->density_code = get_density_code(omc_config->density);

  // DRAM Address Configuration
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

  // APB Base Address Configuration
  //Boardcast addr
  omc_config->base_addr = (uintptr_t)OMC_REGISTER_BASE0_0;
  omc_config->phy_base_addr = (uintptr_t)PHY_REGISTER_BASE0_0;
  //addr of each

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


//================================================
// Customer Request Spec.
//  - Don't change the following parameters
//================================================
#ifdef DRAM_TYPE_LPDDR5
  omc_config->phy_freq_ratio = 1;
  omc_config->omc_freq_ratio = 1;
#else
  omc_config->phy_freq_ratio = 2;
  omc_config->omc_freq_ratio = 2;
#endif
  omc_config->int_cpipe_depth = 1;
  omc_config->int_dpipe_depth = 1;
  omc_config->cpipe_depth = 0 + omc_config->int_cpipe_depth;
  omc_config->dpipe_depth = 0 + omc_config->int_dpipe_depth;
  omc_config->dram_boot = BY_MC;
  omc_config->reqq_depth = 40;
  omc_config->ctrl_dq_width = 16;
  omc_config->dq_width = 16; // per each device (physical dq width)
  omc_config->ch_intr_size = CH_256;
  omc_config->mrr_byte_lane = 0x55;  // This is decided by physical_dq_width
                             // When physical_dq_width == 32, valid lane is 4'b0001 (first)
                             // When physical_dq_width == 16, valid lane is 4'b0101
                             // When physical_dq_width ==  8, valid lane is 4'b1111
  omc_config->byte_lane_inversion = 0;
  omc_config->chip[0].size = omc_config->density*omc_config->ctrl_dq_width/omc_config->dq_width;
  omc_config->chip[1].size = omc_config->density*omc_config->ctrl_dq_width/omc_config->dq_width;
  omc_config->fsp_op = 0;
  omc_config->fsp_wr = 0;

//================================================
// Customer Request Spec.
//  - The following parameters can be modified for tests
//================================================
  omc_config->rank_interleaving = 1;
  omc_config->num_rank = 2; // number of rank.
                    // - This value should be under the maximum rank number. Maxumum number is 2.
  omc_config->reboot_with_mrw = 0;

//================================================
// Memory Feature
//  - The following parameters can be modified for tests
//================================================
  omc_config->rfm_en = 0; // only for LPDDR4, LPDDR5
  omc_config->dsm_en = 0; // LPDDR5 Deep Sleep Mode. In Power-Off scenario, DRAM goes into DSM.
  omc_config->ca_odt = 0;
#ifdef DRAM_TYPE_LPDDR5
  omc_config->zq_bg_mode = 1;
#else
  if (omc_config->dram_t_ck > 937) {
    omc_config->lpddr4_rpre = 1; // Toggle
  } else {
    omc_config->lpddr4_rpre = 0; // Static
  }
#endif

//================================================
// PHY Feature
//  - Don't change the following parameters
//================================================
  omc_config->phy_ind_mode_en = 0;

//================================================
// Training control
//  - The following parameters can be modified for tests
//================================================
  omc_config->eye_scan_rd_en        = 0;
  omc_config->eye_scan_wr_en        = 0;
  omc_config->eye_scan_prbs_rd_en   = 0;
  omc_config->eye_scan_prbs_wr_en   = 0;      
  omc_config->phy_vref_trn_mode     = 0;
  omc_config->phy_duty_trn_mode     = 0;
  omc_config->dram_vref_trn_mode    = 0;
  omc_config->dram_duty_trn_mode    = 0;
  omc_config->command_bus_training  = 0;
  omc_config->ca_vref_training      = 0;
  omc_config->prbs_training         = 0;
  omc_config->reboot_with_training  = 0;
  omc_config->init_zq_calibration   = 0;
  omc_config->zq_calibration        = 0;
  omc_config->zq_calibration_period = 48000; // us. Follow ZQ_INTERVAL in mr_config.h
  omc_config->dfs_training         = 0;

//================================================
// Training control
//  - The following parameters can be modified for tests
//================================================
  omc_config->periodic_training = 0;
  omc_config->periodic_training_period = 24000; // us

//================================================
// All level training control
//================================================
#ifdef DRAM_TYPE_LPDDR5
  // 1:2 ratio can support up to 3200Mbps
  omc_config->dfs_lvl_t_ck[0] = 1672; // tCK = 600MHz
  omc_config->dfs_lvl_t_ck[1] = 2224; // tCK = 450MHz
  omc_config->dfs_lvl_t_ck[2] = 5000; // tCK = 200MHz
#else
  omc_config->dfs_lvl_t_ck[0] = 938;  // tCK = 400MHz
  omc_config->dfs_lvl_t_ck[1] = 1631; // tCK = 613MHz
  omc_config->dfs_lvl_t_ck[2] = 2500; // tCK = 1066MHz
#endif

//================================================
// OMC Functions
//  - The following parameters can be modified for tests
//================================================
  omc_config->temp_sensing = 0;
  omc_config->temp_sensing_period = 32000; // us
  omc_config->dynamic_self_refresh = 0;
  omc_config->dynamic_self_refresh_threshold = 0; // cycle
  omc_config->dynamic_power_down = 0;
  omc_config->dynamic_power_down_threshold = 0; // cycle
  omc_config->regional_clock_gating = 1;
  omc_config->dram_clock_gating = 1;
  omc_config->phy_clock_gating = 0; // This should be 0 when DFI LP interface enabled
  omc_config->phy_low_power = 0;  // Enable DFI LP interface
  omc_config->phy_idle_cnt_th = 0; // Valid when phy_low_power is not 0
#ifdef DRAM_TYPE_LPDDR5
  omc_config->bg_intr_size = PAGE_SIZE_8;
#else
  omc_config->bg_intr_size = BG_NOINT;
#endif
  // Timing Param
  omc_config->t_refiab = 3904000;
  omc_config->t_refipb = 488000;
  omc_config->t_zqcal = 1000000;
  // OMC features
#ifdef ORBIT_ECC
  omc_config->fsecc_op_en = 0;        // 1: in-line ECC enabled
  omc_config->fsecc_region_op_en = 0; // 1: region based ecc feature enable
                              // full space ecc enabled     when fsecc_op_en == 1 and fsecc_region_op_en == 0
                              // regions based  ecc enabled when fsecc_op_en == 1 and fsecc_region_op_en == 1
#endif
#ifdef DRAM_TYPE_LPDDR5
  omc_config->link_err_cnt_th = 5;
#else
  omc_config->link_err_cnt_th = 0;
#endif

//================================================
// These features aren't supported.
//  - Don't change the following parameters
//================================================
  omc_config->tctrlupd_interval = 0;
  omc_config->lp_wakeup[0] = 4;
  omc_config->lp_wakeup[1] = 4;
  omc_config->lp_wakeup[2] = 4;
  omc_config->half_dq_en = 0;

  orbit_update_chips(omc_config, 0, 0);
}
