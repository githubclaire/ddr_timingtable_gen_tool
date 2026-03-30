#!/usr/bin/env python3
import ctypes
from orbit_config import orbit_config

cfg = orbit_config()
print(f"Size of orbit_config: {ctypes.sizeof(cfg)}")
print("\nField offsets:")
for field_name, field_type in cfg._fields_:
    offset = getattr(cfg, '_fields_offsets', {}).get(field_name, None)
    if offset is None:
        # compute offset
        pass
    # Use ctypes.offsetof
    print(f"  {field_name:30s} offset = {ctypes.offsetof(orbit_config, field_name):4d}, size = {ctypes.sizeof(field_type)}")

# Also print first 64 bytes as hex
print("\nFirst 64 bytes of zeroed struct:")
zero = orbit_config()
data = bytes(zero)
for i in range(0, min(64, len(data)), 16):
    line = ' '.join(f'{b:02x}' for b in data[i:i+16])
    print(f"{i:04x}: {line}")