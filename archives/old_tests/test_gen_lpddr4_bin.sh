#!/bin/bash
set -e

ORBIT_DENSITY=4

echo "=== Generating LPDDR4 Reference Binaries ==="

# Single channel
echo "1. Generating LPDDR4 single channel..."
rm -f ddr_timing_table.bin
./gen_timing_params --dram-type lpddr4 --phy-name sphy-v9r8 --speed-bin 4266 --dq-width 16 \
    --orbit-config-density $ORBIT_DENSITY \
    --wdqs-ctrl-mode 1 --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-odt-upto 1250 \
    --cpipe-depth 1 --dpipe-depth 1 \
    --txsr-as-1st-ed --variable-trrd \
    --orbit-config-use-python --orbit-byte-mode 0 --orbit-mixed 0 --orbit-rank-interleaving 1 --orbit-num-rank 2 \
    471 938 1631 2500
cp ddr_timing_table.bin ddr_timing_table.lpddr4.single.ref.bin

# Dual channel
echo "2. Generating LPDDR4 dual channel..."
rm -f ddr_timing_table.bin
./gen_timing_params --dram-type lpddr4 --phy-name sphy-v9r8 --speed-bin 4266 --dq-width 16 \
    --orbit-config-density $ORBIT_DENSITY \
    --wdqs-ctrl-mode 1 --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-odt-upto 1250 \
    --cpipe-depth 1 --dpipe-depth 1 \
    --txsr-as-1st-ed --variable-trrd \
    --orbit-config-use-python --orbit-byte-mode 0 --orbit-mixed 0 --orbit-rank-interleaving 1 --orbit-num-rank 2 \
    --two-channel \
    471 938 1631 2500
cp ddr_timing_table.bin ddr_timing_table.lpddr4.dual.ref.bin

echo "=== LPDDR4 Reference Binaries Generated ==="
ls -la ddr_timing_table.lpddr4.*.ref.bin
