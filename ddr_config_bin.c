#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#include "arise2_config.h"
#define _ORBIT_GET_DENSITY_
#include "orbit_init_gen.h"
#include "mr_config_gen.h"
#include "arise2_omc.h"
#include "ddr_config.h"

int main(){

    struct orbit_config* config = (struct orbit_config*)malloc(sizeof(struct orbit_config));

    ddr_config_init(config);

    FILE *fp = fopen("ddr_timing_table.bin", "rb+");
    if (fp == NULL) {
        perror("gen timing table: fopen failed");
        return 1;
    }

    long target_offset = EMMC_CM4_TIME_TB_SIZE;
    if (fseek(fp, target_offset, SEEK_SET) != 0) {
        perror("gen timing table: fseek failed");
        fclose(fp);
        return 1;
    }

    size_t write_result = fwrite(config, sizeof(struct orbit_config), 1, fp);
    if (write_result != 1) {
        perror("gen timing table: fwrite failed");
        fclose(fp);
        return 1;
    }

    fclose(fp);
    return 0;
}
