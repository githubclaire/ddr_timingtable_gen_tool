#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stddef.h>
#include <unistd.h>

#include "arise2_config.h"
#define _ORBIT_GET_DENSITY_
#include "orbit_init_gen.h"
#include "mr_config_gen.h"
#include "arise2_omc.h"
#include "ddr_config.h"

/* Match the SCP build: timing table at 0x000, orbit_config prefix at 0x800,
 * whole per-DRAM image padded to 4 KiB.  Runtime training results
 * (prbs_result/train_result) are deliberately not stored. */
#define ORBIT_PREFIX_SIZE offsetof(struct orbit_config, prbs_result)
#define TIMING_TABLE_BIN_SIZE 0x1000

int main(){

    struct orbit_config* config = (struct orbit_config*)malloc(sizeof(struct orbit_config));
    if (!config) {
        perror("ddr_config: malloc failed");
        return 1;
    }

    ddr_config_init(config);

    FILE *fp = fopen("ddr_timing_table.bin", "rb+");
    if (fp == NULL) {
        perror("gen timing table: fopen failed");
        free(config);
        return 1;
    }

    long target_offset = EMMC_CM4_TIME_TB_SIZE;
    if (fseek(fp, 0, SEEK_END) != 0) {
        perror("gen timing table: fseek failed");
        fclose(fp);
        free(config);
        return 1;
    }
    if (ftell(fp) > target_offset) {
        fprintf(stderr, "gen timing table: timing table exceeds 0x%lx bytes\n",
                target_offset);
        fclose(fp);
        free(config);
        return 1;
    }
    if (fseek(fp, target_offset, SEEK_SET) != 0) {
        perror("gen timing table: fseek failed");
        fclose(fp);
        free(config);
        return 1;
    }

    size_t write_result = fwrite(config, 1, ORBIT_PREFIX_SIZE, fp);
    if (write_result != ORBIT_PREFIX_SIZE) {
        perror("gen timing table: fwrite failed");
        fclose(fp);
        free(config);
        return 1;
    }

    if (ftruncate(fileno(fp), TIMING_TABLE_BIN_SIZE) != 0) {
        perror("gen timing table: ftruncate failed");
        fclose(fp);
        free(config);
        return 1;
    }

    fclose(fp);
    free(config);
    return 0;
}
