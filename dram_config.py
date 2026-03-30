#=============================================================================
# Release information
# Design version: glenfly_chin_rel7_230725
# Release generated at Tue Jul 25 09:23:19 2023
#=============================================================================

from collections import namedtuple, OrderedDict

Boundary = namedtuple('Boundary', 'freq, t_ck')
WCK = namedtuple('WCK', 'enl, pre_toggle')
Memcfg = namedtuple('Memcfg', 'lower, upper, op, read_latency, write_latency, n_rtp, n_wr, odtlon, odtloff, wckpre_static, wck_rd, wck_wr, wck_fs, odtloff_rd, odtlon_rd')

class dram_config:
    def __init__(self, ref):
        self.memcfgs = []
        self.ref = ref

    def search_memcfgs(self, t_ck):
        for memcfg in self.memcfgs:
            if memcfg.lower.t_ck > t_ck and t_ck >= memcfg.upper.t_ck:
                return memcfg
        raise Exception('invalid target clock period: %d ps' % t_ck)