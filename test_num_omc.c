#include <stdio.h>
#include <stdint.h>

#define DDR_TYPE 2
#define DDR_TWO_CHANNEL 0
#include "arise2_omc.h"

int main() {
    printf("DDR_TWO_CHANNEL = %d\n", DDR_TWO_CHANNEL);
    printf("NUM_OF_OMC = %d\n", NUM_OF_OMC);
    printf("sizeof(uint32_t) = %zu\n", sizeof(uint32_t));
    printf("sizeof(base_addr_id field) = %zu\n", sizeof(((struct orbit_config*)0)->base_addr_id));
    printf("number of elements = %zu\n", sizeof(((struct orbit_config*)0)->base_addr_id) / sizeof(uint32_t));
    return 0;
}