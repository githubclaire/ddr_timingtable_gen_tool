#=============================================================================
# Release information
# Design version: glenfly_chin_rel7_230725
# Release generated at Tue Jul 25 09:23:19 2023
#=============================================================================

from collections import OrderedDict
from dram_config import dram_config, Memcfg, Boundary, WCK
from math import ceil
from timing import Timing

class lpddr4_config(dram_config):
    def initialize(self):
        #                          | Lower               | Upper               | OP   | RL      | (BM)  | WL     | nRTP | nWR     | ODTon   | ODToff | Not used                                              |
        #                          | Freq | t_ck         | Freq | t_ck         |      | NM | DBI|NM|DBI | A  | B |      | A,  B   |  A | B  | A | B  |                                                       |
        self.memcfgs.append(Memcfg(Boundary( 10,100000), Boundary( 266, 3750), 0b000, ( 6,  6,  6,  6), ( 4,  4),    8, ( 6,  6), (-1, -1), (-1, -1), 0, WCK((0,), 0), WCK((0,), 0), WCK((0,), 0), (0), (0) )) # Down to 3759ps
        self.memcfgs.append(Memcfg(Boundary( 266, 3750), Boundary( 533, 1875), 0b001, (10, 12, 10, 12), ( 6,  8),    8, (10, 12), (-1, -1), (-1, -1), 0, WCK((0,), 0), WCK((0,), 0), WCK((0,), 0), (0), (0) )) # Down to 1876ps
        self.memcfgs.append(Memcfg(Boundary( 533, 1875), Boundary( 801, 1250), 0b010, (14, 16, 16, 18), ( 8, 12),    8, (16, 16), (-1,  6), (-1, 22), 0, WCK((0,), 0), WCK((0,), 0), WCK((0,), 0), (0), (0) )) # Down to 1250ps
        self.memcfgs.append(Memcfg(Boundary( 801, 1250), Boundary(1068,  938), 0b011, (20, 22, 22, 24), (10, 18),    8, (20, 22), ( 4, 12), (20, 28), 0, WCK((0,), 0), WCK((0,), 0), WCK((0,), 0), (0), (0) )) # Down to  938ps
        self.memcfgs.append(Memcfg(Boundary(1068,  938), Boundary(1336,  750), 0b100, (24, 28, 26, 30), (12, 22),   10, (24, 28), ( 4, 14), (22, 32), 0, WCK((0,), 0), WCK((0,), 0), WCK((0,), 0), (0), (0) )) # Down to  750ps
        self.memcfgs.append(Memcfg(Boundary(1336,  750), Boundary(1602,  625), 0b101, (28, 32, 32, 36), (14, 26),   12, (30, 32), ( 6, 18), (24, 36), 0, WCK((0,), 0), WCK((0,), 0), WCK((0,), 0), (0), (0) )) # Down to  625ps
        self.memcfgs.append(Memcfg(Boundary(1602,  625), Boundary(1872,  535), 0b110, (32, 36, 36, 40), (16, 30),   14, (34, 38), ( 6, 20), (26, 40), 0, WCK((0,), 0), WCK((0,), 0), WCK((0,), 0), (0), (0) )) # Down to  535ps
        self.memcfgs.append(Memcfg(Boundary(1872,  535), Boundary(2133,  468), 0b111, (36, 40, 40, 44), (18, 34),   16, (40, 44), ( 8, 24), (28, 44), 0, WCK((0,), 0), WCK((0,), 0), WCK((0,), 0), (0), (0) ))

        if self.ref.args.densities:
            self.ref.densities = self.ref.args.densities
        else:
            self.ref.densities = (2, 3, 4, 6, 8, 12, 16)

        self.ref.p_t_rfcpb = OrderedDict(sorted({
             2: Timing( 60,0,0),
             3: Timing( 90,0,0),
             4: Timing( 90,0,0),
             6: Timing(140,0,0),
             8: Timing(140,0,0),
            12: Timing(190,0,0),
            16: Timing(190,0,0),
        }.items()))

        self.ref.p_t_rfcab = OrderedDict(sorted({
             2: Timing(130,0,0),
             3: Timing(180,0,0),
             4: Timing(180,0,0),
             6: Timing(280,0,0),
             8: Timing(280,0,0),
            12: Timing(380,0,0),
            16: Timing(380,0,0),
        }.items()))

        self.ref.p_t_rfmpb = OrderedDict(sorted({
             2: Timing(110,0,0),
             3: Timing(170,0,0),
             4: Timing(170,0,0),
             6: Timing(190,0,0),
             8: Timing(190,0,0),
            12: Timing(260,0,0),
            16: Timing(260,0,0),
        }.items()))

        self.ref.p_t_rfmab = OrderedDict(sorted({
             2: Timing(130,0,0),
             3: Timing(210,0,0),
             4: Timing(210,0,0),
             6: Timing(280,0,0),
             8: Timing(280,0,0),
            12: Timing(380,0,0),
            16: Timing(380,0,0),
        }.items()))

        self.ref.p_t_pbr2pbr = OrderedDict(sorted({
             2: Timing(60,0,0),
             3: Timing(90,0,0),
             4: Timing(90,0,0),
             6: Timing(90,0,0),
             8: Timing(90,0,0),
            12: Timing(90,0,0),
            16: Timing(90,0,0),
        }.items()))

        self.ref.p_t_xsr_add = Timing(7.5, 2, 0)
        for d in self.ref.densities:
            self.ref.p_t_xsr[d] = self.ref.p_t_rfcab[d] + self.ref.p_t_xsr_add;

        if int(self.ref.args.speed_bin) >= 4266:
            self.ref.p_t_rrd = Timing(7.5, 4, 0)
            self.ref.p_t_faw = Timing(30, 0, 0)
        else:
            self.ref.p_t_rrd = Timing(10, 4, 0)
            self.ref.p_t_faw = Timing(40, 0, 0)

        self.ref.p_t_rppb = Timing(18, 4, 0)
        self.ref.p_t_rpab = Timing(21, 4, 0)
        self.ref.p_t_cke = Timing(7.5, 4, 0)
        self.ref.p_t_cmdcke = Timing(1.75, 3, 0)
        self.ref.p_t_ckesr = Timing(15, 3, 0)
        self.ref.p_t_ckelck = Timing(5.0, 5, 0)
        self.ref.p_t_ckckeh = Timing(1.75, 3, 1)
        self.ref.p_t_xp = Timing(7.5, 5, 0)
        self.ref.p_t_ras = Timing(42, 3, 0)
        self.ref.p_t_rc = Timing(self.ref.p_t_ras.min_ns + self.ref.p_t_rppb.min_ns, 7, 0)
        self.ref.p_t_rtp = Timing(7.5, 8, 0)
        self.ref.p_t_rcd = Timing(18, 4, 0)
        self.ref.p_t_rcdwr = self.ref.p_t_rcd
        self.ref.p_t_xp_mrri = self.ref.p_t_xp + self.ref.p_t_rcd + Timing(0, 0, 3)

        if self.ref.byte_mode:
            self.ref.p_t_wr = Timing(20, 6, 0)
            self.ref.p_t_wtr = Timing(12, 8, 0)
        else:
            self.ref.p_t_wr = Timing(18, 6, 0)
            self.ref.p_t_wtr = Timing(10, 8, 0)

        self.ref.p_t_wr_p = Timing(self.ref.p_t_wr.min_ns+0.8, 6, 0.25)
        self.ref.p_n_wr_p = Timing(0.8, 0, 0.25)
        self.ref.p_t_tmp = Timing(7.5, 8, 0)

        self.ref.p_t_mrw = Timing(10, 10, 0)
        self.ref.p_t_mod = Timing(14, 10, 0)
        self.ref.p_t_mrr = Timing(0, 8, 0)
        self.ref.p_t_rcd_derate = self.ref.p_t_rcd + 1.875
        self.ref.p_t_rcdwr_derate = self.ref.p_t_rcdwr + 1.875
        self.ref.p_t_rc_derate = self.ref.p_t_rc + 3.7
        self.ref.p_t_ras_derate = self.ref.p_t_ras + 1.875
        self.ref.p_t_rrd_derate = self.ref.p_t_rrd + 1.875
        self.ref.p_t_rpab_derate = self.ref.p_t_rpab + 1.875
        self.ref.p_t_rppb_derate = self.ref.p_t_rppb + 1.875
        self.ref.p_t_zqcs = Timing( 0, 0, 0)
        self.ref.p_t_zqcl = Timing(30, 8, 0)
        self.ref.p_t_dqsckmax = Timing(3.5, 0, 0)
        self.ref.p_t_dqsckmin = Timing(1.5, 0, 0)
        self.ref.p_t_dqsck_r2r = Timing(1.0, 0, 0)
        self.ref.p_t_odtonmax = Timing(3.5, 0, 0)
        self.ref.p_t_odtonmin = Timing(1.5, 0, 0)
        self.ref.p_t_odtoffmax = Timing(3.5, 0, 0)
        self.ref.p_t_odtoffmin = Timing(1.5, 0, 0)

        self.ref.t_wpre = 2
        self.ref.t_rpre = 2
        self.ref.t_dqss = 1
        self.ref.t_ccdmw = 32

        self.ref.dll_enable = 0
        self.ref.bl = 16
        self.ref.asize_ctrl = 1 # FIXME from

    def update(self, t_ck):
        if self.ref.args.variable_trrd:
            if t_ck >= 535:
                self.ref.p_t_rrd = Timing(10, 4, 0)
                self.ref.p_t_faw = Timing(40, 0, 0)
            elif int(self.ref.args.speed_bin) >= 4266:
                self.ref.p_t_rrd = Timing(7.5, 4, 0)
                self.ref.p_t_faw = Timing(30, 0, 0)
            self.ref.p_t_rrd_derate = self.ref.p_t_rrd  + 1.875

        self.ref.memcfg = self.search_memcfgs(t_ck)

        self.ref.rl_set = 0
        self.ref.wl_set = 0
        self.ref.nwr_set = 1 if self.ref.byte_mode else 0
        if self.ref.byte_mode:
            self.ref.rl_set += 2
        if self.ref.read_dbi:
            self.ref.rl_set += 1

        self.ref.t_dqsckmax = self.ref.p_t_dqsckmax.calc_ceil(t_ck)
        self.ref.t_dqsckmin = self.ref.p_t_dqsckmin.calc_floor(t_ck)

        self.ref.p_t_xp = Timing(7.5 + (t_ck/1000)*1, 5+1, 0)
        self.ref.p_t_xp_mrri = Timing(self.ref.p_t_xp.min_ns + self.ref.p_t_rcd.min_ns, 5, 0) + Timing(0, 0, 3)

    def calculate(self, t_ck):
        t_ck_ns = t_ck/1000

        self.ref.t_rtw_odt = self.ref.read_latency + self.ref.p_t_dqsckmax.calc_ceil(t_ck) + self.ref.bl//2 + self.ref.rpste - self.ref.memcfg.odtlon[self.ref.wl_set] - self.ref.p_t_odtonmin.calc_floor(t_ck) + 1
        if self.ref.args.wdqs_ctrl_mode == 1 and self.ref.args.phy_name == 'orbit-phy':
            self.ref.t_rtw = self.ref.read_latency + self.ref.p_t_dqsckmax.calc_ceil(t_ck) + self.ref.bl//2 + self.ref.rpste
        else:
            self.ref.t_rtw = self.ref.read_latency + self.ref.p_t_dqsckmax.calc_ceil(t_ck) + self.ref.bl//2 + self.ref.rpste - self.ref.write_latency + 2

        if self.ref.write_odt:
            self.ref.t_wtwcr = self.ref.memcfg.odtloff[self.ref.wl_set] - self.ref.memcfg.odtlon[self.ref.wl_set] - self.ref.bl//2
        else:
            self.ref.t_wtwcr = 8

        self.ref.t_rtrcr = self.ref.p_t_dqsck_r2r.calc_ceil(t_ck) + self.ref.t_rpre + self.ref.rpste

        self.ref.t_rdidle = self.ref.read_latency + self.ref.p_t_dqsckmax.calc_ceil(t_ck) + self.ref.bl//2 + self.ref.rpste + self.ref.p_t_tmp.calc_ceil(t_ck);
        self.ref.t_rtrrd = self.ref.t_rdidle

        self.ref.t_wtr_a = self.ref.write_latency + 1 + self.ref.bl//2 + self.ref.p_t_wtr.calc_ceil(t_ck)
        if self.ref.write_odt:
            self.ref.t_wtrcr = self.ref.memcfg.odtloff[self.ref.wl_set] + ceil((self.ref.p_t_odtoffmax - self.ref.p_t_dqsckmin).min_ns*1000/t_ck) + 2 - self.ref.read_latency
        else:
            self.ref.t_wtrcr = self.ref.write_latency - self.ref.read_latency + 1 + self.ref.bl//2 + self.ref.wpste + 2 + ceil((Timing(t_ck_ns*0.25,0,0) - self.ref.p_t_dqsckmin).min_ns*1000/t_ck)

        #self.ref.t_wtrcr = max(self.ref.t_wtrcr, 0)

        self.ref.t_wr_a = self.ref.write_latency + 1 + self.ref.bl//2 + self.ref.t_wr
        self.ref.t_wr_p = self.ref.write_latency + 1 + self.ref.bl//2 + self.ref.p_t_wr_p.calc_ceil(t_ck)
        self.ref.t_wrwtr = self.ref.write_latency + 1 + self.ref.bl//2 + self.ref.p_t_tmp.calc_ceil(t_ck)

        self.ref.n_wr_a = self.ref.write_latency + 1 + self.ref.bl//2 + self.ref.n_wr
        self.ref.n_wr_p = self.ref.write_latency + 1 + self.ref.bl//2 + self.ref.p_n_wr_p.calc_ceil(t_ck) + self.ref.n_wr + 2

        self.ref.t_xp_mrri = self.ref.p_t_xp.calc_ceil(t_ck) + self.ref.p_t_rcd.calc_ceil(t_ck) + 3

        self.ref.tdram_clk_enable = self.ref.tctrl_delay + self.ref.p_t_ckckeh.calc_ceil(t_ck) + 2