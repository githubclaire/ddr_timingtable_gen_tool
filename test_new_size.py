#!/usr/bin/env python2
import ctypes
from orbit_config_new import get_orbit_config_class, create_orbit_config

cls4 = get_orbit_config_class('lpddr4')
cfg4 = cls4()
print "Size LPDDR4:", ctypes.sizeof(cfg4)

cls5 = get_orbit_config_class('lpddr5')
cfg5 = cls5()
print "Size LPDDR5:", ctypes.sizeof(cfg5)

# Also print size of sub-structures
print "chip_config:", ctypes.sizeof(cfg4.chip[0])
print "train_result_t:", ctypes.sizeof(cfg4.train_result[0])
print "prbs_result_t:", ctypes.sizeof(cfg4.prbs_result[0])