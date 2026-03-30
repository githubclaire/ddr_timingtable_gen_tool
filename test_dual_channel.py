#!/usr/bin/env python3
import sys, ctypes, struct
sys.path.insert(0, '.')
from orbit_config import make_orbit_config_class
from ddr_config_init import ddr_config_init, create_orbit_config

# Create LPDDR4 dual channel config
cfg = create_orbit_config('lpddr4', True)
ddr_config_init(cfg, dram_type='lpddr4', two_channel=True, density=16, density_code=1, rank_interleaving=1, num_rank=2, byte_mode=0, mixed=0)
print('Python config size:', ctypes.sizeof(cfg))
print('Expected C size: 5816')
print('Fields (partial):')
for field_name, field_type in cfg._fields_:
    offset = getattr(cfg.__class__, field_name).offset
    size = getattr(cfg.__class__, field_name).size
    if offset > 200:
        break
    value = getattr(cfg, field_name)
    if size <= 4:
        if isinstance(value, (int, ctypes.c_uint8, ctypes.c_uint16, ctypes.c_uint32)):
            val = int(value)
        else:
            val = value
        print(f'  {offset:4d}: {field_name:30s} = {val}')
    else:
        print(f'  {offset:4d}: {field_name:30s} size {size}')

# Get binary representation
data = bytes(cfg)
print('\nFirst 128 bytes hex:')
for i in range(0, min(128, len(data)), 16):
    chunk = data[i:i+16]
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f'{i:04x}: {hex_str:<48} {ascii_str}')

# Read C binary
with open('ddr_timing_table.bin', 'rb') as f:
    f.seek(0x800)
    c_data = f.read(len(data))
print('\nC binary size:', len(c_data))
if len(c_data) == len(data):
    mismatches = []
    for i in range(len(data)):
        if c_data[i] != data[i]:
            mismatches.append(i)
            if len(mismatches) <= 10:
                print(f'Mismatch at offset {i}: C={c_data[i]:02x} Py={data[i]:02x}')
    if mismatches:
        print(f'Total mismatches: {len(mismatches)}')
    else:
        print('Binary matches!')
else:
    print('Size mismatch:', len(c_data), 'vs', len(data))