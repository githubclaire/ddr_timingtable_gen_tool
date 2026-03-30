#!/bin/bash
set -e

SRC_DIR=.

echo "=== LPDDR5 Binary Compatibility Test ==="
echo "1. Clean up previous binaries..."
rm -f ddr_timing_table.bin ddr_timing_table.lpddr5.bin

echo "2. First generate timing table (required for C binary)..."
$SRC_DIR/gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 --speed-bin 6400 --dq-width 16 \
                           --densities 16 \
                           --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-lecc-upto 625 --write-odt-upto 10000 \
                           --cpipe-depth 1 --dpipe-depth 1 \
                           --omc-freq-ratio 1 --phy-freq-ratio 1 --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 314 \
                           314 418 556 2500

echo "3. Generate C reference binary..."
/usr/bin/python3 ./gen_ddr_config 5 0
if [ -f "ddr_timing_table.bin" ]; then
    cp ddr_timing_table.bin ddr_timing_table.lpddr5.bin
    echo "Created C reference: ddr_timing_table.lpddr5.bin"
else
    echo "ERROR: Failed to generate C reference binary"
    exit 1
fi

echo "4. Generate Python orbit config binary..."
rm -f ddr_timing_table.bin
$SRC_DIR/gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 --speed-bin 6400 --dq-width 16 \
                           --densities 16 \
                           --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-lecc-upto 625 --write-odt-upto 10000 \
                           --cpipe-depth 1 --dpipe-depth 1 \
                           --omc-freq-ratio 1 --phy-freq-ratio 1 --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 314 \
                           --orbit-config-use-python --orbit-byte-mode 0 --orbit-mixed 0 --orbit-rank-interleaving 1 --orbit-num-rank 2 \
                           314 418 556 2500

echo "5. Comparing Python vs C binaries..."
python -c "
import sys
with open('ddr_timing_table.bin', 'rb') as f1, open('ddr_timing_table.lpddr5.bin', 'rb') as f2:
    data1 = f1.read()
    data2 = f2.read()
    if len(data1) != len(data2):
        print('Size mismatch:', len(data1), 'vs', len(data2))
        sys.exit(1)
    mismatches = []
    for i in range(len(data1)):
        if data1[i] != data2[i]:
            mismatches.append(i)
            if len(mismatches) > 10:
                break
    if mismatches:
        print('Binary mismatches at offsets:', mismatches[:10])
        # Show first mismatch context
        i = mismatches[0]
        start = max(0, i-16)
        end = min(len(data1), i+16)
        print('Python:', ' '.join('%02x' % ord(data1[j]) for j in range(start, end)))
        print('C     :', ' '.join('%02x' % ord(data2[j]) for j in range(start, end)))
        sys.exit(1)
    else:
        print('SUCCESS: Binary matches C implementation exactly!')
" 2>&1

echo "=== Test Complete ==="

