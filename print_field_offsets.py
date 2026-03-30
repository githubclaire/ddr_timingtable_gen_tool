#!/usr/bin/env python2
import ctypes
from orbit_config import make_orbit_config_class

cls = make_orbit_config_class('lpddr4')
cfg = cls()
base = ctypes.addressof(cfg)
print "Size:", ctypes.sizeof(cfg)
for field_name, field_type in cfg._fields_:
    # compute offset by address of field
    field_addr = ctypes.addressof(getattr(cfg, field_name))
    offset = field_addr - base
    size = ctypes.sizeof(field_type)
    print "%s offset=%d size=%d" % (field_name.ljust(30), offset, size)
    # print first 4 bytes of field
    data = ctypes.string_at(field_addr, min(size, 16))
    hexstr = ' '.join('%02x' % ord(b) for b in data)
    print "  data: %s" % hexstr