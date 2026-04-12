/*
 * Dump the C struct orbit_config layout as machine-readable lines:
 *     <field_name> <offset>
 *     sizeof <total_size>
 *
 * Compile with one of:
 *     gcc -DDDR_TYPE=2 -DDDR_TWO_CHANNEL=0 -I.. -o dump_struct_layout \
 *         tools/dump_struct_layout.c
 *     (and DDR_TYPE=3, DDR_TWO_CHANNEL=1 combinations)
 *
 * The output must diff cleanly against the Python tools/dump_struct_layout.py
 * output for the same (dram_type, two_channel) pair.
 */
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

#ifndef DDR_TYPE
#define DDR_TYPE 2
#endif
#ifndef DDR_TWO_CHANNEL
#define DDR_TWO_CHANNEL 0
#endif

#if DDR_TYPE == 2
#define DRAM_TYPE_LPDDR4
#elif DDR_TYPE == 3
#define DRAM_TYPE_LPDDR5
#else
#error "DDR_TYPE must be 2 (lpddr4) or 3 (lpddr5)"
#endif

#include "arise2_omc.h"

#define P(field) printf("%s %zu\n", #field, offsetof(struct orbit_config, field))

int main(void) {
    P(dram_boot);
    P(ch_intr_size);
    P(bg_intr_size);
    P(fsp_op);
    P(fsp_wr);
    P(dq_vref_byte0);
    P(dq_vref_byte1);
    P(ca_vref);
#ifdef DRAM_TYPE_LPDDR5
    P(lp5_mr2);
    P(lp5_mr3);
    P(lp5_mr10);
    P(lp5_mr11);
    P(lp5_mr12);
    P(lp5_mr16);
    P(lp5_mr17);
    P(lp5_mr18);
    P(zq_bg_mode);
#endif
    P(phy_freq_ratio);
    P(omc_freq_ratio);
    P(int_cpipe_depth);
    P(int_dpipe_depth);
    P(cpipe_depth);
    P(dpipe_depth);
    P(reboot);
    P(reqq_depth);
    P(density);
    P(rank_interleaving);
    P(num_rank);
    P(reboot_with_mrw);
    P(ctrl_dq_width);
    P(dq_width);
    P(use_dfi_train_if);
    P(phy_ind_mode_en);
    P(phy_low_power);
    P(phy_idle_cnt_th);
    P(lp_wakeup);
    P(half_dq_en);
#ifdef DRAM_TYPE_LPDDR4
    P(lpddr4_rpre);
#endif
    P(rfm_en);
    P(dsm_en);
    P(eye_scan_rd_en);
    P(eye_scan_wr_en);
    P(eye_scan_prbs_rd_en);
    P(eye_scan_prbs_wr_en);
    P(ca_odt);
    P(phy_odt);
    P(init_zq_calibration);
    P(temp_sensing);
    P(zq_calibration);
    P(periodic_training);
    P(periodic_training_period);
    P(dynamic_power_down);
    P(dynamic_self_refresh);
    P(regional_clock_gating);
    P(phy_clock_gating);
    P(dram_clock_gating);
    P(dfs_lvl_t_ck);
    P(num_of_region);
    P(command_bus_training);
    P(ca_vref_training);
    P(prbs_training);
    P(reboot_with_training);
    P(dfs_training);
    P(phy_vref_trn_mode);
    P(phy_duty_trn_mode);
    P(dram_vref_trn_mode);
    P(dram_duty_trn_mode);
    P(density_code);
    P(rclk_t_ck);
    P(boot_t_ck);
    P(boot_t_ck_low);
    P(dram_t_ck);
    P(prev_dram_t_ck);
    P(chip);
    P(num_of_ch);
    P(base_addr);
    P(base_addr_id);
    P(phy_base_addr);
    P(phy_base_addr_id);
    P(tphyupd_resp);
    P(dynamic_self_refresh_threshold);
    P(dynamic_power_down_threshold);
    P(zq_calibration_period);
    P(tctrlupd_interval);
    P(temp_sensing_period);
    P(t_refipb);
    P(t_refiab);
    P(t_zqcal);
    P(link_err_cnt_th);
    P(mrr_byte_lane);
    P(byte_lane_inversion);
    P(region_start);
    P(region_end);
    P(prbs_result);
    P(train_result);
    printf("sizeof %zu\n", sizeof(struct orbit_config));
    return 0;
}
