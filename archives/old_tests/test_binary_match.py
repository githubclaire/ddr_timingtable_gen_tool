#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ddr_config_init import generate_orbit_config_binary
import ctypes
from orbit_config import EMMC_CM4_TIME_TB_SIZE, make_orbit_config_class

# Generate Python binary
python_bin = 'test_python.bin'
# First create empty file of size offset + struct size
cfg_class = make_orbit_config_class('lpddr4', False)
struct_size = ctypes.sizeof(cfg_class())
with open(python_bin, 'wb') as f:
    f.write(b'\x00' * (EMMC_CM4_TIME_TB_SIZE + struct_size))

# Generate orbit config at offset
# Match C binary parameters: density=16
generate_orbit_config_binary(dram_type='lpddr4', two_channel=False, density=16,
                             output_file=python_bin, offset=EMMC_CM4_TIME_TB_SIZE,
                             rank_interleaving=1, num_rank=2)

# Read C binary
c_bin = 'ddr_timing_table.bin'
if not os.path.exists(c_bin):
    print("C binary not found")
    sys.exit(1)

with open(c_bin, 'rb') as f:
    f.seek(EMMC_CM4_TIME_TB_SIZE)
    c_data = f.read(struct_size)

with open(python_bin, 'rb') as f:
    f.seek(EMMC_CM4_TIME_TB_SIZE)
    py_data = f.read(struct_size)

print("C data size:", len(c_data))
print("Python data size:", len(py_data))

if len(c_data) != len(py_data):
    print("Size mismatch")
    sys.exit(1)

# Compare byte by byte
mismatch = 0
for i in range(len(c_data)):
    c_byte = c_data[i]
    py_byte = py_data[i]
    if isinstance(c_byte, str):
        c_byte = ord(c_byte)
    if isinstance(py_byte, str):
        py_byte = ord(py_byte)
    if c_byte != py_byte:
        if mismatch < 10:
            print("Mismatch at offset %d (0x%x): C=0x%02x Python=0x%02x" % (i, i, c_byte, py_byte))
        mismatch += 1

if mismatch == 0:
    print("SUCCESS: Binary matches exactly!")
else:
    print("Total mismatches:", mismatch)
    # Optionally dump hex diff
    import binascii
    print("First 64 bytes C:", binascii.hexlify(c_data[:64]))
    print("First 64 bytes Py:", binascii.hexlify(py_data[:64]))

# Cleanup
os.remove(python_bin)