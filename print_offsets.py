#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from orbit_config import make_orbit_config_class

# Create LPDDR4 single channel class
cls = make_orbit_config_class('lpddr4', False)
print("Field offsets for orbit_config_lpddr4_1ch:")
for field_name, field_type in cls._fields_:
    offset = getattr(cls, field_name).offset
    size = getattr(cls, field_name).size
    print(f"  {offset:4d} ({offset:#04x}): {field_name:30s} size {size}")
print(f"Total size: {cls()._sizeof_()}")

# Also print the first 64 bytes of default config
from ddr_config_init import ddr_config_init, create_orbit_config
cfg = create_orbit_config('lpddr4', False)
ddr_config_init(cfg)
data = bytes(cfg)
print("\nFirst 64 bytes of default config:")
for i in range(0, min(64, len(data)), 8):
    line = data[i:i+8]
    hex_str = ''.join(f'{b:02x}' for b in line)
    print(f"  {i:4d}: {hex_str}")

# Compare with C binary
import subprocess
subprocess.run(['gcc', '-std=c99', '-D', 'DDR_TYPE=lpddr4', '-D', 'DDR_TWO_CHANNEL=0', '-I', '.', 'ddr_config_bin.c', '-o', 'ddr_config_bin_exec'], check=False)
subprocess.run(['./ddr_config_bin_exec'], check=False)
with open('ddr_timing_table.bin', 'rb') as f:
    f.seek(0x800)
    c_data = f.read(3048)
    print("\nC binary first 64 bytes:")
    for i in range(0, min(64, len(c_data)), 8):
        line = c_data[i:i+8]
        hex_str = ''.join(f'{b:02x}' for b in line)
        print(f"  {i:4d}: {hex_str}")