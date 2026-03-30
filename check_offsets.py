#!/usr/bin/env python2
import ctypes
from orbit_config import orbit_config

cfg = orbit_config()
print "Size of orbit_config:", ctypes.sizeof(cfg)

# Get offsets by creating instance and checking address differences
zero = orbit_config()
base = ctypes.addressof(zero)
for field_name, field_type in zero._fields_:
    field_addr = ctypes.addressof(getattr(zero, field_name))
    offset = field_addr - base
    size = ctypes.sizeof(field_type)
    print "%s offset=%d size=%d" % (field_name.ljust(30), offset, size)
    # Check alignment
    if offset % 8 != 0:
        print "  WARNING: offset not aligned to 8 bytes"

# Also check first few bytes
print "\nFirst 64 bytes (hex):"
data = ctypes.string_at(base, 64)
for i in range(0, len(data), 16):
    line = ' '.join('%02x' % ord(b) for b in data[i:i+16])
    print "%04x: %s" % (i, line)