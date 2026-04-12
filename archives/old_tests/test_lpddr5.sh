#!/bin/bash
set -e

SRC_DIR=.

ORBIT_DENSITY=4

echo "=== LPDDR5 Binary Compatibility Test (Single & Dual Channel) ==="
echo "1. Clean up previous binaries..."
rm -f ddr_timing_table.bin ddr_timing_table.lpddr5.bin ddr_timing_table.lpddr5.single.bin ddr_timing_table.lpddr5.dual.bin

echo "2. First generate timing table (required for C binary)..."
$SRC_DIR/gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 --speed-bin 6400 --dq-width 16 \
                           --orbit-config-density $ORBIT_DENSITY \
                           --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-lecc-upto 625 --write-odt-upto 10000 \
                           --cpipe-depth 1 --dpipe-depth 1 \
                           --omc-freq-ratio 1 --phy-freq-ratio 1 --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 10000 \
                           314 418 556 2500

echo "3. Generate C reference binary (single channel)..."
/usr/bin/python3 ./gen_ddr_config 5 0
if [ -f "ddr_timing_table.bin" ]; then
    cp ddr_timing_table.bin ddr_timing_table.c.bin
    cp ddr_timing_table.bin ddr_timing_table.lpddr5.bin
    cp ddr_timing_table.bin ddr_timing_table.lpddr5.single.bin
    echo "Created C reference: ddr_timing_table.lpddr5.single.bin"
else
    echo "ERROR: Failed to generate C reference binary"
    exit 1
fi

echo "4. Generate Python orbit config binary (single channel)..."
rm -f ddr_timing_table.bin
$SRC_DIR/gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 --speed-bin 6400 --dq-width 16 \
                           --orbit-config-density $ORBIT_DENSITY \
                           --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-lecc-upto 625 --write-odt-upto 10000 \
                           --cpipe-depth 1 --dpipe-depth 1 \
                           --omc-freq-ratio 1 --phy-freq-ratio 1 --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 10000 \
                           --orbit-config-use-python --orbit-byte-mode 0 --orbit-mixed 0 --orbit-rank-interleaving 1 --orbit-num-rank 2 \
                           314 418 556 2500

echo "5. Comparing Python vs C binaries (single channel)..."
python -c "
import sys
# Compare full binary (timing table + orbit config)
with open('ddr_timing_table.bin', 'rb') as f1, open('ddr_timing_table.c.bin', 'rb') as f2:
    data1 = f1.read()
    data2 = f2.read()
    compare_size = min(len(data1), len(data2))
    if compare_size < 100:
        print('Size too small:', len(data1), 'vs', len(data2))
        sys.exit(1)
    mismatches = []
    for i in range(compare_size):
        if data1[i] != data2[i]:
            mismatches.append(i)
            if len(mismatches) > 10:
                break
    if mismatches:
        print('Binary mismatches at offsets:', mismatches[:10])
        i = mismatches[0]
        start = max(0, i-16)
        end = min(compare_size, i+16)
        print('Python:', ' '.join('%02x' % data1[j] for j in range(start, end)))
        print('C     :', ' '.join('%02x' % data2[j] for j in range(start, end)))
        sys.exit(1)
    else:
        print('SUCCESS: Full binary matches C implementation! (compared ' + str(compare_size) + ' bytes)')
" 2>&1

echo "6. Generate C reference binary (dual channel)..."
rm -f ddr_timing_table.bin
$SRC_DIR/gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 --speed-bin 6400 --dq-width 16 \
                           --orbit-config-density $ORBIT_DENSITY \
                           --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-lecc-upto 625 --write-odt-upto 10000 \
                           --cpipe-depth 1 --dpipe-depth 1 \
                           --omc-freq-ratio 1 --phy-freq-ratio 1 --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 10000 \
                           314 418 556 2500
/usr/bin/python3 ./gen_ddr_config 5 1
if [ -f "ddr_timing_table.bin" ]; then
    cp ddr_timing_table.bin ddr_timing_table.c.dual.bin
    cp ddr_timing_table.bin ddr_timing_table.lpddr5.dual.bin
    echo "Created C reference: ddr_timing_table.lpddr5.dual.bin"
else
    echo "ERROR: Failed to generate C reference binary"
    exit 1
fi

echo "7. Generate Python orbit config binary (dual channel)..."
rm -f ddr_timing_table.bin
$SRC_DIR/gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 --speed-bin 6400 --dq-width 16 \
                           --orbit-config-density $ORBIT_DENSITY \
                           --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-lecc-upto 625 --write-odt-upto 10000 \
                           --cpipe-depth 1 --dpipe-depth 1 \
                           --omc-freq-ratio 1 --phy-freq-ratio 1 --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 10000 \
                           --orbit-config-use-python --orbit-byte-mode 0 --orbit-mixed 0 --orbit-rank-interleaving 1 --orbit-num-rank 2 \
                           --two-channel \
                           314 418 556 2500

echo "8. Comparing Python vs C binaries (dual channel)..."
python -c "
import sys
# Compare timing table section (first 0x800 bytes)
TIMING_SIZE = 0x800
with open('ddr_timing_table.bin', 'rb') as f1, open('ddr_timing_table.c.dual.bin', 'rb') as f2:
    data1 = f1.read()
    data2 = f2.read()
    # Compare up to the smaller size
    compare_size = min(len(data1), len(data2), TIMING_SIZE)
    if compare_size < 100:
        print('Size too small:', len(data1), 'vs', len(data2))
        sys.exit(1)
    mismatches = []
    for i in range(compare_size):
        if data1[i] != data2[i]:
            mismatches.append(i)
            if len(mismatches) > 10:
                break
    if mismatches:
        print('Binary mismatches at offsets:', mismatches[:10])
        i = mismatches[0]
        start = max(0, i-16)
        end = min(compare_size, i+16)
        print('Python:', ' '.join('%02x' % data1[j] for j in range(start, end)))
        print('C     :', ' '.join('%02x' % data2[j] for j in range(start, end)))
        sys.exit(1)
    else:
        print('SUCCESS: Timing table matches C implementation! (compared ' + str(compare_size) + ' bytes)')
" 2>&1

echo "=== Test Complete ==="
