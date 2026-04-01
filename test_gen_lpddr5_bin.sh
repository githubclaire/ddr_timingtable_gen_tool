#!/bin/bash
set -e

ORBIT_DENSITY=4

echo "=== Generating LPDDR5 Reference Binaries ==="

# Single channel
echo "1. Generating LPDDR5 single channel..."
rm -f ddr_timing_table.bin
./gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 --speed-bin 6400 --dq-width 16 \
    --orbit-config-density $ORBIT_DENSITY \
    --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-lecc-upto 625 --write-odt-upto 10000 \
    --cpipe-depth 1 --dpipe-depth 1 \
    --omc-freq-ratio 1 --phy-freq-ratio 1 --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 314 \
    --orbit-config-use-python --orbit-byte-mode 0 --orbit-mixed 0 --orbit-rank-interleaving 1 --orbit-num-rank 2 \
    314 418 556 2500
cp ddr_timing_table.bin ddr_timing_table.lpddr5.single.ref.bin

# Dual channel
echo "2. Generating LPDDR5 dual channel..."
rm -f ddr_timing_table.bin
./gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 --speed-bin 6400 --dq-width 16 \
    --orbit-config-density $ORBIT_DENSITY \
    --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-lecc-upto 625 --write-odt-upto 10000 \
    --cpipe-depth 1 --dpipe-depth 1 \
    --omc-freq-ratio 1 --phy-freq-ratio 1 --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 314 \
    --orbit-config-use-python --orbit-byte-mode 0 --orbit-mixed 0 --orbit-rank-interleaving 1 --orbit-num-rank 2 \
    --two-channel \
    314 418 556 2500
cp ddr_timing_table.bin ddr_timing_table.lpddr5.dual.ref.bin

echo "=== LPDDR5 Reference Binaries Generated ==="
ls -la ddr_timing_table.lpddr5.*.ref.bin
