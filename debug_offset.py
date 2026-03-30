#!/usr/bin/env python2
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ddr_config_init import generate_orbit_config_binary
from orbit_config import EMMC_CM4_TIME_TB_SIZE, make_orbit_config_class
import ctypes

# Generate Python binary
python_bin = 'debug_python.bin'
# First create empty file of size offset + struct size
cfg_class = make_orbit_config_class('lpddr4', False)
struct_size = ctypes.sizeof(cfg_class())
print "Python struct size:", struct_size
with open(python_bin, 'wb') as f:
    f.write(b'\x00' * (EMMC_CM4_TIME_TB_SIZE + struct_size))

# Generate orbit config at offset
generate_orbit_config_binary(dram_type='lpddr4', two_channel=False, density=16,
                             output_file=python_bin, offset=EMMC_CM4_TIME_TB_SIZE)

# Read Python binary at offset 256
with open(python_bin, 'rb') as f:
    f.seek(EMMC_CM4_TIME_TB_SIZE + 256)
    py_data = f.read(4)
    print "Python bytes at offset 256:", ' '.join('%02x' % ord(b) for b in py_data)

# Read C binary
c_bin = 'ddr_timing_table.bin'
with open(c_bin, 'rb') as f:
    f.seek(EMMC_CM4_TIME_TB_SIZE + 256)
    c_data = f.read(4)
    print "C bytes at offset 256:", ' '.join('%02x' % ord(b) for b in c_data)

# Cleanup
os.remove(python_bin)