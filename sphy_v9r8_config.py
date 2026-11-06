#=============================================================================
# Release information
# Design version: glenfly_chin_rel7_230725
# Release generated at Tue Jul 25 09:23:19 2023
#=============================================================================

from phy_config import phy_config
from math import ceil

class sphy_v9r8_config(phy_config):
    sphy_v9r8_lp4_dfs_offsetr         = (0x0, 0x0,0x0,0x0)
    sphy_v9r8_lp4_dfs_offsetw         = (0x0, 0x0,0x0,0x0)
    sphy_v9r8_lp4_dfs_half            = (0x1, 0x0,0x1,0x0)
    sphy_v9r8_lp4_dfs_dll_on          = (0x1, 0x1,0x1,0x1)
    sphy_v9r8_lp4_dfs_rodt_disable    = (0x0, 0x0,0x1,0x0)
    sphy_v9r8_lp4_dfs_wr_per_rank_en  = (0x1, 0x1,0x1,0x1)
    sphy_v9r8_lp4_dfs_rd_per_rank_en  = (0x0, 0x0,0x0,0x1)
    sphy_v9r8_lp4_dfs_gateadj         = (0x0, 0x0,0x0,0x0)
    sphy_v9r8_lp4_dfs_gateduradj      = (0x4, 0x4,0x4,0x4)
    sphy_v9r8_lp4_dfs_cmosrcv         = (0x0, 0x0,0x0,0x0)
    sphy_v9r8_lp4_dfs_shgate          = (0x0, 0x0,0x0,0x0)
    sphy_v9r8_lp4_dfs_rpre_opt        = (0x0, 0x0,0x0,0x1)
    sphy_v9r8_lp4_dfs_twpre           = (0x0, 0x0,0x0,0x0)
    sphy_v9r8_lp4_dfs_pulld_dqs       = (0x0, 0x0,0x3,0x0)
    sphy_v9r8_lp4_dfs_readadj         = (0x0, 0x0,0x1,0x0)
    sphy_v9r8_lp4_dfs_readduradj      = (0x5, 0x5,0x5,0x7)
    sphy_v9r8_lp4_dfs_dfdqs           = (0x0, 0x0,0x0,0x1)
    sphy_v9r8_lp4_dfs_auto_dqs        = (0x0, 0x0,0x0,0x1)
    sphy_v9r8_lp4_dfs_testircv        = (0x0, 0x0,0x0,0x3)
    sphy_v9r8_lp4_dfs_gatetrain       = (0x0, 0x0,0x0,0x0)
    sphy_v9r8_lp4_dfs_wrtrain         = (0x0, 0x0,0x0,0x1)
    sphy_v9r8_lp4_dfs_rd_pre_type     = (0x0, 0x0,0x0,0x1)

    sphy_v9r8_lp5_lecc_dfs_link_ecc_mode   = (0x0, 0x0,0x0,0x0,0x1)
    sphy_v9r8_lp5_lecc_dfs_offsetr         = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_lecc_dfs_offsetw         = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_lecc_dfs_half            = (0x1, 0x1,0x0,0x0,0x0)
    sphy_v9r8_lp5_lecc_dfs_phy_dll_2x      = (0x1, 0x1,0x1,0x0,0x0)
    sphy_v9r8_lp5_lecc_dfs_dll_on          = (0x1, 0x1,0x1,0x1,0x1)
    sphy_v9r8_lp5_lecc_dfs_rodt_disable    = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_lecc_dfs_wr_per_rank_en  = (0x1, 0x1,0x1,0x1,0x1)
    sphy_v9r8_lp5_lecc_dfs_rd_per_rank_en  = (0x0, 0x0,0x1,0x1,0x1)
    sphy_v9r8_lp5_lecc_dfs_gateadj         = (0xa, 0xa,0xa,0x0,0x0)
    sphy_v9r8_lp5_lecc_dfs_gateduradj      = (0x3, 0x3,0x5,0x0,0x0)
    sphy_v9r8_lp5_lecc_dfs_cmosrcv         = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_lecc_dfs_shgate          = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_lecc_dfs_rpre_opt        = (0x0, 0x0,0x0,0x1,0x1)
    sphy_v9r8_lp5_lecc_dfs_rpost_opt       = (0x0, 0x0,0x0,0x2,0x2)
    sphy_v9r8_lp5_lecc_dfs_twpre           = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_lecc_dfs_pulld_dqs       = (0x3, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_lecc_dfs_readadj         = (0xc, 0xc,0xc,0xc,0xb)
    sphy_v9r8_lp5_lecc_dfs_readduradj      = (0x5, 0x5,0x7,0x7,0x7)
    sphy_v9r8_lp5_lecc_dfs_dfdqs           = (0x0, 0x0,0x0,0x1,0x1)
    sphy_v9r8_lp5_lecc_dfs_auto_dqs        = (0x0, 0x0,0x0,0x1,0x1)
    sphy_v9r8_lp5_lecc_dfs_testircv        = (0x0, 0x0,0x0,0x3,0x3)
    sphy_v9r8_lp5_lecc_dfs_wrtrain         = (0x0, 0x0,0x1,0x1,0x1)
    sphy_v9r8_lp5_lecc_dfs_rd_pre_type     = (0x0, 0x0,0x0,0x1,0x1)
    sphy_v9r8_lp5_lecc_dfs_rd_post_type1   = (0x0, 0x0,0x0,0x2,0x2)
    sphy_v9r8_lp5_lecc_dfs_rd_post_type2   = (0x0, 0x0,0x0,0x1,0x1)

    sphy_v9r8_lp5_dfs_link_ecc_mode   = (0x0, 0x0,0x0,0x0,0x1)
    sphy_v9r8_lp5_dfs_offsetr         = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_dfs_offsetw         = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_dfs_half            = (0x1, 0x1,0x0,0x0,0x0)
    sphy_v9r8_lp5_dfs_phy_dll_2x      = (0x1, 0x1,0x1,0x0,0x0)
    sphy_v9r8_lp5_dfs_dll_on          = (0x1, 0x1,0x1,0x1,0x1)
    sphy_v9r8_lp5_dfs_rodt_disable    = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_dfs_wr_per_rank_en  = (0x1, 0x1,0x1,0x1,0x1)
    sphy_v9r8_lp5_dfs_rd_per_rank_en  = (0x0, 0x0,0x1,0x1,0x1)
    sphy_v9r8_lp5_dfs_gateadj         = (0xa, 0xa,0xa,0x0,0x0)
    sphy_v9r8_lp5_dfs_gateduradj      = (0x3, 0x3,0x5,0x0,0x0)
    sphy_v9r8_lp5_dfs_cmosrcv         = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_dfs_shgate          = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_dfs_rpre_opt        = (0x0, 0x0,0x0,0x1,0x1)
    sphy_v9r8_lp5_dfs_rpost_opt       = (0x0, 0x0,0x0,0x2,0x2)
    sphy_v9r8_lp5_dfs_twpre           = (0x0, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_dfs_pulld_dqs       = (0x3, 0x0,0x0,0x0,0x0)
    sphy_v9r8_lp5_dfs_readadj         = (0xc, 0xc,0xc,0xc,0xb)
    sphy_v9r8_lp5_dfs_readduradj      = (0x5, 0x5,0x7,0x7,0x7)
    sphy_v9r8_lp5_dfs_dfdqs           = (0x0, 0x0,0x0,0x1,0x1)
    sphy_v9r8_lp5_dfs_auto_dqs        = (0x0, 0x0,0x0,0x1,0x1)
    sphy_v9r8_lp5_dfs_testircv        = (0x0, 0x0,0x0,0x3,0x3)
    sphy_v9r8_lp5_dfs_wrtrain         = (0x0, 0x0,0x1,0x1,0x1)
    sphy_v9r8_lp5_dfs_rd_pre_type     = (0x0, 0x0,0x0,0x1,0x1)
    sphy_v9r8_lp5_dfs_rd_post_type1   = (0x0, 0x0,0x0,0x2,0x2)
    sphy_v9r8_lp5_dfs_rd_post_type2   = (0x0, 0x0,0x0,0x1,0x1)

    def dfs_level(self, dram_type, t_ck, wck_ratio):
        if dram_type == 'lpddr5':
            if t_ck/wck_ratio < 468:
                dvfs_level = 4
            elif t_ck/wck_ratio < 625:
                dvfs_level = 3
            elif t_ck/wck_ratio < 1250:
                dvfs_level = 2
            elif t_ck/wck_ratio < 1876:
                dvfs_level = 1
            else:
                dvfs_level = 0
        else:
            if t_ck < 938:
                dvfs_level = 3
            elif t_ck < 1631:
                dvfs_level = 2
            elif t_ck < 2500:
                dvfs_level = 1
            else:
                dvfs_level = 0
        return dvfs_level

    def get_auto_dqs_clean(self, t_ck):
        if t_ck < 833:
            return 1
        else:
            return 0

    def get_readadj(self, dram_type, t_ck, wck_ratio, link_ecc_en):
        dfs_level = self.dfs_level(dram_type, t_ck, wck_ratio)

        if dram_type == 'lpddr5':
            readadj = self.sphy_v9r8_lp5_lecc_dfs_readadj[dfs_level] if link_ecc_en else self.sphy_v9r8_lp5_dfs_readadj[dfs_level]
        else:
            readadj = self.sphy_v9r8_lp4_dfs_readadj[dfs_level]

        if readadj > 8:
            readadj = -(readadj-8)

        return readadj

    def get_readduradj(self, dram_type, t_ck, wck_ratio, link_ecc_en):
        dfs_level = self.dfs_level(dram_type, t_ck, wck_ratio)

        if dram_type == 'lpddr5':
            readduradj = self.sphy_v9r8_lp5_lecc_dfs_readduradj[dfs_level] if link_ecc_en else self.sphy_v9r8_lp5_dfs_readduradj[dfs_level]
        else:
            readduradj = self.sphy_v9r8_lp4_dfs_readduradj[dfs_level]

        if readduradj > 8:
            readduradj = -(readduradj-8)

        return readduradj

    def get_rd_pre_type(self, dram_type, t_ck, min_t_ck, wck_ratio, link_ecc_en):
        dfs_level = self.dfs_level(dram_type, t_ck, wck_ratio)

        if dram_type == 'lpddr4':
            rd_pre_type = self.sphy_v9r8_lp4_dfs_rd_pre_type[dfs_level]
        else:
            rd_pre_type = self.sphy_v9r8_lp5_lecc_dfs_rd_pre_type[dfs_level] if link_ecc_en else self.sphy_v9r8_lp5_dfs_rd_pre_type[dfs_level]
            if self.ref.emulation:
                rd_pre_type = 0

        return rd_pre_type

    def get_rd_post_type1(self, dram_type, t_ck, min_t_ck, wck_ratio, link_ecc_en):
        dfs_level = self.dfs_level(dram_type, t_ck, wck_ratio)

        rd_post_type1 = self.sphy_v9r8_lp5_lecc_dfs_rd_post_type1[dfs_level] if link_ecc_en else self.sphy_v9r8_lp5_dfs_rd_post_type1[dfs_level]
        if self.ref.emulation:
            rd_post_type1 = 0

        return rd_post_type1

    def get_rd_post_type2(self, dram_type, t_ck, min_t_ck, wck_ratio, link_ecc_en):
        dfs_level = self.dfs_level(dram_type, t_ck, wck_ratio)

        rd_post_type2 = self.sphy_v9r8_lp5_lecc_dfs_rd_post_type2[dfs_level] if link_ecc_en else self.sphy_v9r8_lp5_dfs_rd_post_type2[dfs_level]
        if self.ref.emulation:
            rd_post_type2 = 0

        return rd_post_type2

    def calculate_mc_timing_param(self, t_ck):
        readduradj = self.get_readduradj(self.dram_type, t_ck, self.ref.data_freq_ratio, self.ref.write_lecc or self.ref.read_lecc)
        readadj = self.get_readadj(self.dram_type, t_ck, self.ref.data_freq_ratio, self.ref.write_lecc or self.ref.read_lecc)

        readdur_ext = False
        readadj_ext = False

        readdur_sub = (readduradj>>3)&1
        readadj_sub = (readadj>>3)&1
        readduradj  = (readduradj&7)+8 if readdur_ext else readduradj&7
        readadj     = (readadj&7)+8 if readadj_ext else readadj&7

        readduradj  = 0-readduradj if readdur_sub else readduradj
        readadj     = 0-readadj if readadj_sub else readadj

        if self.dram_type == "lpddr4":
            phy_delay = max(readduradj + 4, self.ref.p_t_dqsckmax.calc_ceil(t_ck))
            t_rtw_phy = self.ref.read_latency + phy_delay + self.ref.bl//2 + self.ref.rpste - self.ref.write_latency + 2 # t_wpre
        elif self.dram_type == "lpddr5":
            phy_delay = int(ceil((readduradj+readadj+4)/4) if (self.ref.data_freq_ratio == 4) else ceil((readduradj+readadj+6)/2))
            phy_delay = max(phy_delay, self.ref.p_t_wck2dqomax.calc_ceil(t_ck))
            t_rtw_phy = self.ref.read_latency + phy_delay + self.ref.bl_nmax - self.ref.write_latency;

        if self.ref.write_odt or self.dram_type == "lpddr5":
            self.ref.t_rtw = max(self.ref.t_rtw, t_rtw_phy)
        else:
            self.ref.t_rtw = t_rtw_phy

    def update_conf(self, t_ck):
        
        self.ref.tctrl_delay = self.ref.tctrl_delay + self.ref.args.cpipe_depth*2*self.ref.pipe_freq_ratio

        if self.dram_type == "lpddr5":
            if ( t_ck >= 1836 and self.ref.data_freq_ratio == 2 ) or ( t_ck >= 1250 and self.ref.data_freq_ratio == 4) : # wck and wck ratio
                if self.ref.wck_always_on == False :
                    # Keep parity with the SCP build's toolchain (and its
                    # --wck-always-on-upto 630 slow point): WCK always-on is
                    # mandatory only at the fast points; slow points may run
                    # with WCK gating.  Do not abort generation here.
                    pass
            t_ck = t_ck * self.ref.data_freq_ratio
            self.ref.rdqs_pre = self.get_rd_pre_type(self.dram_type, t_ck, self.ref.min_t_ck, self.ref.data_freq_ratio, self.ref.write_lecc or self.ref.read_lecc)
            self.ref.rdqs_pst = self.get_rd_post_type1(self.dram_type, t_ck, self.ref.min_t_ck, self.ref.data_freq_ratio, self.ref.write_lecc or self.ref.read_lecc)
            self.ref.rdqs_pst_mode = self.get_rd_post_type2(self.dram_type, t_ck, self.ref.min_t_ck, self.ref.data_freq_ratio, self.ref.write_lecc or self.ref.read_lecc)
            self.ref.wck_pst = self.ref.rdqs_pst
        elif self.dram_type == "lpddr4":
            self.ref.rdqs_pre = self.get_rd_pre_type(self.dram_type, t_ck, self.ref.min_t_ck, self.ref.data_freq_ratio, 0)

    def calculate_phy_timing_param(self, t_ck):
        if self.dram_type == "lpddr4":
            self.ref.trddata_en = self.ref.read_latency + (self.ref.p_t_dqsckmax
                                                           + 0.480 # IO output delay
                                                           + 0.07*self.ref.args.wire_length # Board delay
                                                           + 0.036 # System clock output jitter
                                                           + 0.07*self.ref.args.wire_length # Board delay
                                                           + 0.150 # IO input dleay
                                                           + 0.157 # Other mismatch
                                                           + 4.25*t_ck/1000 # CTS delay
                                                           + 1.625 # CTS delay
                                                          ).calc_ceil(t_ck) - self.ref.pipe_depth_diff*self.ref.pipe_freq_ratio
            self.ref.trddata_en += (self.ref.trddata_en+1)%2

            self.ref.tphy_wrdata = 2
            self.ref.tphy_wrlat = self.ref.write_latency - 2 - self.ref.pipe_delay
            self.ref.twrdata_delay = self.ref.twrdata_delay + 4
        elif self.dram_type == "lpddr5":
            self.ref.trddata_en = self.ref.read_latency + (self.ref.p_t_wck2dqomax
                                                           + 0.480 # IO output delay
                                                           + 0.07*self.ref.args.wire_length # Board delay
                                                           + 0.020 # System clock output jitter
                                                           + 0.07*self.ref.args.wire_length # Board delay
                                                           + 0.150 # IO input delay
                                                           + 0.110 # Other mismatch
                                                           + 4.25*t_ck/1000/self.ref.data_freq_ratio
                                                           + 1.970 # CTS delay
                                                          ).calc_ceil(t_ck) - self.ref.pipe_depth_diff*self.ref.pipe_freq_ratio
            self.ref.trddata_en = self.ref.trddata_en*self.ref.data_freq_ratio
            if self.ref.data_freq_ratio == 4:
                if self.ref.trddata_en%4 != 0:
                  self.ref.trddata_en += 4-(self.ref.trddata_en%4)
            else:
                self.ref.trddata_en += self.ref.trddata_en%2

            #self.ref.tphy_wrdata = self.ref.data_freq_ratio
            self.ref.tphy_wrlat = self.ref.write_latency*self.ref.data_freq_ratio - 2 - self.ref.pipe_delay
            self.ref.twrdata_delay = self.ref.twrdata_delay*self.ref.data_freq_ratio + 4

        self.ref.tphy_wrcslat = self.ref.tphy_wrlat
        self.ref.tphy_rdcslat = self.ref.trddata_en
        self.ref.auto_dqs_clean = self.get_auto_dqs_clean(t_ck)
        self.ref.tlp_resp = (3 + self.ref.args.cpipe_depth*2*self.ref.pipe_freq_ratio + 1)*self.ref.args.omc_freq_ratio

        phyupd_wait_cnt = 59 # In phy spec, default 63 DFI clock cycle

        phyupd_wait_cnt = (phyupd_wait_cnt - self.ref.args.cpipe_depth*2*self.ref.pipe_freq_ratio)*self.ref.args.omc_freq_ratio

        #self.ref.tphyupd_req_dis = phyupd_wait_cnt//self.ref.args.omc_freq_ratio - 1
        self.ref.tphyupd_req_dis = 0

        self.ref.dfi_tctrlupd_max = 76
        self.ref.dfi_tctrlupd_min = 2