#=============================================================================
# Release information
# Design version: glenfly_chin_rel7_230725
# Release generated at Tue Jul 25 09:23:19 2023
#=============================================================================

from collections import namedtuple
from math import ceil, floor

class Timing(namedtuple('Timing', 'min_ns min_nck add_tck')):
    def __add__(self, other):
        if type(other) in [int, float]:
            return Timing(self.min_ns + other, self.min_nck, self.add_tck)
        elif type(other) is Timing:
            return Timing(self.min_ns + other.min_ns, max(self.min_nck, other.min_nck), self.add_tck + other.add_tck)
        else:
            raise Exception('type %s is not supported yet' % type(other))
    def __sub__(self, other):
        if type(other) in [int, float]:
            return Timing(self.min_ns - other, self.min_nck, self.add_tck)
        elif type(other) is Timing:
            return Timing(self.min_ns - other.min_ns, self.min_nck, self.add_tck - other.add_tck)
        else:
            raise Exception('type %s is not supported yet' % type(other))
    def __rsub__(self, other):
        return Timing(other - self.min_ns, 0, self.add_tck)
    def __truediv__(self, other):
        if type(other) in [int, float]:
            return Timing(self.min_ns/other, self.min_nck, self.add_tck)
        else:
            raise Exception('type %s is not supported yet' % type(other))
    def __floordiv__(self, other):
        if type(other) in [int, float]:
            return Timing(self.min_ns//other, self.min_nck, self.add_tck)
        else:
            raise Exception('type %s is not supported yet' % type(other))

    def calc_ceil(self, t_ck):
        return int(max(ceil((self.min_ns*1000+t_ck*self.add_tck)/t_ck), self.min_nck))
    def calc_floor(self, t_ck):
        return int(max(floor((self.min_ns*1000+t_ck*self.add_tck)/t_ck), self.min_nck))
