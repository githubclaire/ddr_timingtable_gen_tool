#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

// Define macros same as gen_ddr_config
#define DDR_TYPE 2
#define DRAM_TYPE_LPDDR4
#define DDR_TWO_CHANNEL 1

#include "arise2_omc.h"

int main() {
    printf("sizeof(struct orbit_config) = %zu\n", sizeof(struct orbit_config));
    printf("\nField offsets:\n");
    
#define PRINT_OFFSET(field) printf("  %-30s offset = %4zu, size = %2zu\n", \
    #field, offsetof(struct orbit_config, field), sizeof(((struct orbit_config*)0)->field))
    
    PRINT_OFFSET(dram_boot);
    PRINT_OFFSET(ch_intr_size);
    PRINT_OFFSET(bg_intr_size);
    PRINT_OFFSET(fsp_op);
    PRINT_OFFSET(fsp_wr);
    PRINT_OFFSET(dq_vref_byte0);
    PRINT_OFFSET(dq_vref_byte1);
    PRINT_OFFSET(ca_vref);
#ifdef DRAM_TYPE_LPDDR5
    PRINT_OFFSET(lp5_mr2);
    PRINT_OFFSET(lp5_mr3);
    PRINT_OFFSET(lp5_mr10);
    PRINT_OFFSET(lp5_mr11);
    PRINT_OFFSET(lp5_mr12);
    PRINT_OFFSET(lp5_mr16);
    PRINT_OFFSET(lp5_mr17);
    PRINT_OFFSET(lp5_mr18);
    PRINT_OFFSET(zq_bg_mode);
#endif
    PRINT_OFFSET(phy_freq_ratio);
    PRINT_OFFSET(omc_freq_ratio);
    PRINT_OFFSET(int_cpipe_depth);
    PRINT_OFFSET(int_dpipe_depth);
    PRINT_OFFSET(cpipe_depth);
    PRINT_OFFSET(dpipe_depth);
    PRINT_OFFSET(reboot);
    PRINT_OFFSET(reqq_depth);
    PRINT_OFFSET(density);
    PRINT_OFFSET(rank_interleaving);
    PRINT_OFFSET(num_rank);
    PRINT_OFFSET(reboot_with_mrw);
    PRINT_OFFSET(ctrl_dq_width);
    PRINT_OFFSET(dq_width);
    PRINT_OFFSET(use_dfi_train_if);
    PRINT_OFFSET(phy_ind_mode_en);
    PRINT_OFFSET(phy_low_power);
    PRINT_OFFSET(phy_idle_cnt_th);
    PRINT_OFFSET(lp_wakeup);
    PRINT_OFFSET(half_dq_en);
#ifdef DRAM_TYPE_LPDDR4
    PRINT_OFFSET(lpddr4_rpre);
#endif
    PRINT_OFFSET(rfm_en);
    PRINT_OFFSET(dsm_en);
    PRINT_OFFSET(eye_scan_rd_en);
    PRINT_OFFSET(eye_scan_wr_en);
    PRINT_OFFSET(eye_scan_prbs_rd_en);
    PRINT_OFFSET(eye_scan_prbs_wr_en);
    PRINT_OFFSET(ca_odt);
    PRINT_OFFSET(phy_odt);
    PRINT_OFFSET(init_zq_calibration);
    PRINT_OFFSET(temp_sensing);
    PRINT_OFFSET(zq_calibration);
    PRINT_OFFSET(periodic_training);
    PRINT_OFFSET(periodic_training_period);
    PRINT_OFFSET(dynamic_power_down);
    PRINT_OFFSET(dynamic_self_refresh);
    PRINT_OFFSET(regional_clock_gating);
    PRINT_OFFSET(phy_clock_gating);
    PRINT_OFFSET(dram_clock_gating);
    PRINT_OFFSET(dfs_lvl_t_ck);
    PRINT_OFFSET(num_of_region);
    PRINT_OFFSET(command_bus_training);
    PRINT_OFFSET(ca_vref_training);
    PRINT_OFFSET(prbs_training);
    PRINT_OFFSET(reboot_with_training);
    PRINT_OFFSET(dfs_training);
    PRINT_OFFSET(phy_vref_trn_mode);
    PRINT_OFFSET(phy_duty_trn_mode);
    PRINT_OFFSET(dram_vref_trn_mode);
    PRINT_OFFSET(dram_duty_trn_mode);
    PRINT_OFFSET(density_code);
    PRINT_OFFSET(rclk_t_ck);
    PRINT_OFFSET(boot_t_ck);
    PRINT_OFFSET(boot_t_ck_low);
    PRINT_OFFSET(dram_t_ck);
    PRINT_OFFSET(prev_dram_t_ck);
    PRINT_OFFSET(chip);
    PRINT_OFFSET(num_of_ch);
    PRINT_OFFSET(base_addr);
    PRINT_OFFSET(base_addr_id);
    PRINT_OFFSET(phy_base_addr);
    PRINT_OFFSET(phy_base_addr_id);
    PRINT_OFFSET(tphyupd_resp);
    PRINT_OFFSET(dynamic_self_refresh_threshold);
    PRINT_OFFSET(dynamic_power_down_threshold);
    PRINT_OFFSET(zq_calibration_period);
    PRINT_OFFSET(tctrlupd_interval);
    PRINT_OFFSET(temp_sensing_period);
    PRINT_OFFSET(t_refipb);
    PRINT_OFFSET(t_refiab);
    PRINT_OFFSET(t_zqcal);
    PRINT_OFFSET(link_err_cnt_th);
    PRINT_OFFSET(mrr_byte_lane);
    PRINT_OFFSET(byte_lane_inversion);
    PRINT_OFFSET(prbs_result);
    PRINT_OFFSET(train_result);
    PRINT_OFFSET(region_start);
    PRINT_OFFSET(region_end);
    
    return 0;
}