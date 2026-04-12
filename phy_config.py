#=============================================================================
# Release information
# Design version: glenfly_chin_rel7_230725
# Release generated at Tue Jul 25 09:23:19 2023
#=============================================================================

class phy_config():
    def __init__(self, ref):
        self.ref = ref
        self.dram_type = ref.args.dram_type

    def update_conf(self, t_ck):
        pass

    def calculate_mc_timing_param(self, t_ck):
        pass

    def calculate_phy_timing_param(self, t_ck):
        pass