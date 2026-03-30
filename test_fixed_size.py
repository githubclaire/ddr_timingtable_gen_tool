#!/usr/bin/env python2
import ctypes
from orbit_config_fixed import make_orbit_config_class

cls4 = make_orbit_config_class('lpddr4')
cfg4 = cls4()
print "Size LPDDR4:", ctypes.sizeof(cfg4)

cls5 = make_orbit_config_class('lpddr5')
cfg5 = cls5()
print "Size LPDDR5:", ctypes.sizeof(cfg5)

# Compare with C size (5816)
print "Difference from C (5816):", ctypes.sizeof(cfg4) - 5816