#!/usr/bin/env python2
import ctypes
from orbit_config import orbit_config
cfg = orbit_config()
print "Size of orbit_config:", ctypes.sizeof(cfg)
print "Size of chip_config:", ctypes.sizeof(cfg.chip[0])
print "Size of train_result_t:", ctypes.sizeof(cfg.train_result[0])
print "Size of prbs_result_t:", ctypes.sizeof(cfg.prbs_result[0])
# compute expected size: 3048?