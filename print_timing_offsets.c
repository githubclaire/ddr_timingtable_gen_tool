#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

#define DDR_TYPE 2
#define DRAM_TYPE_LPDDR4
#define DDR_TWO_CHANNEL 1

#include "arise2_omc.h"

int main() {
    printf("sizeof(struct timing_param) = %zu\n", sizeof(struct timing_param));
    printf("\nField offsets:\n");
    
#define PRINT_OFFSET(field) printf("  %-30s offset = %4zu, size = %2zu\n", \
    #field, offsetof(struct timing_param, field), sizeof(((struct timing_param*)0)->field))
    
    PRINT_OFFSET(freq);
    PRINT_OFFSET(t_ck);
    PRINT_OFFSET(timing_zqcal);
    PRINT_OFFSET(timing_param);
    PRINT_OFFSET(timing_param_derate);
    PRINT_OFFSET(dfi_timing_param);
    PRINT_OFFSET(t_rfcab);
    PRINT_OFFSET(t_rfcpb);
    PRINT_OFFSET(t_rfmab);
    PRINT_OFFSET(t_rfmpb);
    PRINT_OFFSET(t_refdpr);
    PRINT_OFFSET(tx_pbr2pbr);
    PRINT_OFFSET(t_xsr);
    PRINT_OFFSET(t_xsdll);
    PRINT_OFFSET(t_xs_fast);
    PRINT_OFFSET(wck_ratio);
    PRINT_OFFSET(tlp_resp);
    PRINT_OFFSET(auto_dqs_clean);
    PRINT_OFFSET(dll_enable);
    PRINT_OFFSET(write_odt);
    PRINT_OFFSET(nt_odt);
    PRINT_OFFSET(write_dbi);
    PRINT_OFFSET(read_dbi);
    PRINT_OFFSET(wpste);
    PRINT_OFFSET(rpste);
    PRINT_OFFSET(rl);
    PRINT_OFFSET(wl);
    PRINT_OFFSET(mr_rl);
    PRINT_OFFSET(mr_wl);
    PRINT_OFFSET(mr_wr);
    PRINT_OFFSET(mr_rtp);
    PRINT_OFFSET(mr_cal);
    PRINT_OFFSET(mr_tccd_l);
    PRINT_OFFSET(bank_mode);
    PRINT_OFFSET(wck_fm);
    PRINT_OFFSET(rdqs_pst_mode);
    PRINT_OFFSET(rdqs_pst);
    PRINT_OFFSET(rdqs_pre);
    PRINT_OFFSET(wck_pst);
    PRINT_OFFSET(wck_on);
    PRINT_OFFSET(read_link_parity);
    PRINT_OFFSET(write_link_parity);
    PRINT_OFFSET(t_rtw);
    PRINT_OFFSET(t_wtr_a);
    PRINT_OFFSET(t_wtr);
    PRINT_OFFSET(t_rc);
    PRINT_OFFSET(trddata_en);
    
    return 0;
}