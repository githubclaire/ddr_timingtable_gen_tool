#include <stdio.h>
#include <stdint.h>
#include "arise2_omc.h"

int main() {
    printf("sizeof(struct orbit_config) = %zu\n", sizeof(struct orbit_config));
    printf("sizeof(struct chip_config) = %zu\n", sizeof(struct chip_config));
    printf("sizeof(train_result_t) = %zu\n", sizeof(train_result_t));
    printf("sizeof(prbs_result_t) = %zu\n", sizeof(prbs_result_t));
    return 0;
}