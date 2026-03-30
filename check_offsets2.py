#!/usr/bin/env python2
import ctypes
from orbit_config import orbit_config

cfg = orbit_config()
print "Size of orbit_config:", ctypes.sizeof(cfg)

# Get offsets using ctypes.offsetof (should work)
for field_name, field_type in cfg._fields_:
    try:
        off = ctypes.offsetof(orbit_config, field_name)
        sz = ctypes.sizeof(field_type)
        print "%s offset=%d size=%d" % (field_name.ljust(30), off, sz)
    except Exception as e:
        print "%s error: %s" % (field_name, e)

# Print first 64 bytes
zero = orbit_config()
base = ctypes.addressof(zero)
data = ctypes.string_at(base, 64)
print "\nFirst 64 bytes (hex):"
for i in range(0, len(data), 16):
    line = ' '.join('%02x' % ord(b) for b in data[i:i+16])
    print "%04x: %s" % (i, line)