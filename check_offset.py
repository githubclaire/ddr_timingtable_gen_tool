#!/usr/bin/env python3
import sys, ctypes
sys.path.insert(0, '.')
from orbit_config import make_orbit_config_class

cls = make_orbit_config_class('lpddr5', False)
cfg = cls()

print("Field offsets for LPDDR5 single channel:")
offset = 0
for field_name, field_type in cfg._fields_:
    field = getattr(cfg.__class__, field_name)
    size = field.size
    print(f"{field.offset:4d}: {field_name:30s} size={size:3d} type={field_type}")
    
    # Check if this field contains offset 128
    if field.offset <= 128 < field.offset + size:
        print(f"  *** Field {field_name} contains offset 128 ***")
        inner_offset = 128 - field.offset
        print(f"  Inner offset: {inner_offset}")
        
    offset = field.offset + size

# Also check specific offset 128
print("\nChecking offset 128 specifically:")
for field_name, field_type in cfg._fields_:
    field = getattr(cfg.__class__, field_name)
    if field.offset <= 128 < field.offset + field.size:
        print(f"Offset 128 is in field {field_name} (offset {field.offset}, size {field.size})")
        # Try to get value
        value = getattr(cfg, field_name)
        if field.size <= 8:
            print(f"  Value: {value}")
            if field.size == 4:
                print(f"  Hex: 0x{value:08x}")
        break