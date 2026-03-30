#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

// Define macros same as gen_ddr_config
#define DDR_TYPE 2
//#define DRAM_TYPE_LPDDR4  // implied by DDR_TYPE==2
// DDR_TWO_CHANNEL defined via command line

#include "arise2_omc.h"

int main() {
    printf("DDR_TWO_CHANNEL = %d\n", DDR_TWO_CHANNEL);
    printf("NUM_OF_OMC = %d\n", NUM_OF_OMC);
    printf("sizeof(struct orbit_config) = %zu\n", sizeof(struct orbit_config));
    printf("\nField offsets:\n");
    
#define PRINT_OFFSET(field) printf("  %-30s offset = %4zu, size = %2zu\n", \
    #field, offsetof(struct orbit_config, field), sizeof(((struct orbit_config*)0)->field))
    
    // Print key fields around offset 256
    PRINT_OFFSET(t_refipb);
    PRINT_OFFSET(t_refiab);
    PRINT_OFFSET(t_zqcal);
    PRINT_OFFSET(link_err_cnt_th);
    PRINT_OFFSET(mrr_byte_lane);
    PRINT_OFFSET(byte_lane_inversion);
    PRINT_OFFSET(region_start);
    PRINT_OFFSET(region_end);
    PRINT_OFFSET(prbs_result);
    PRINT_OFFSET(train_result);
    
    return 0;
}