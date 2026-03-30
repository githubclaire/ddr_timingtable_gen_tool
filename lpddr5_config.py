#=============================================================================
# Release information
# Design version: glenfly_chin_rel7_230725
# Release generated at Tue Jul 25 09:23:19 2023
#=============================================================================

from collections import OrderedDict
from dram_config import dram_config, Memcfg, Boundary, WCK
from math import ceil, floor
from timing import Timing

class lpddr5_config(dram_config):
    def initialize(self):
        self.memcfgs_map =[[] for i in range(3)]
        # From Table 201 - WCK2CK Sync AC Parameters for Read operation (1854.99B)
        #      Table 438~442 - Clock AC Timings (1854.99B)
        # For LPDDR5X ranges, integer values are used instead of floating points at MHz and ps granules.

        # memcfgs_map[0] : Table 203 - DVFSC disabled (MR19 OP[1:0] = 00b) , Read Link ECC eanble (MR22 OP[7:6]=01b)
        #
        #                                         | Lower               | Upper        | OP    | RL          | WL     | nRBTP | nWR              | ODTon | ODToff | WCKPRE | WCKRD                 | WCKWR          | WCKFS     | ODTLoff_RD|ODTLon_RD |
        #                                         | Freq | t_ck         | Freq  | t_ck |       |S0| S1| S2   | A | B  |       | A | B            |       |        | _static| enl            | tgl  | enl     |tgl   | enl | NA  |           |          |
        self.memcfgs_map[0].append(Memcfg(Boundary(400,  2500), Boundary( 467,  2141), 0b0110, (12, 13,  0), ( 6,  9),       2, (16, 17, 18, 19), (-2,),  (+3,),   3,         WCK(( 5,  6, 0),  5), WCK((2,  5), 2), WCK((1,), 0),    (-3,),     (+4,)));
        self.memcfgs_map[0].append(Memcfg(Boundary(467,  2141), Boundary( 533,  1875), 0b0111, (13, 14,  0), ( 6, 11),       2, (19, 20, 21, 22), (-3,),  (+3,),   3,         WCK(( 5,  6, 0),  6), WCK((2,  7), 2), WCK((1,), 0),    (-4,),     (+5,)));
        self.memcfgs_map[0].append(Memcfg(Boundary(533,  1875), Boundary( 600,  1667), 0b1000, (15, 16,  0), ( 7, 12),       3, (21, 22, 23, 24), (-3,),  (+3,),   3,         WCK(( 7,  8, 0),  6), WCK((3,  8), 2), WCK((2,), 0),    (-4,),     (+5,)));
        self.memcfgs_map[0].append(Memcfg(Boundary(600,  1667), Boundary( 688,  1453), 0b1001, (17, 18,  0), ( 8, 14),       4, (24, 25, 27, 28), (-3,),  (+3,),   4,         WCK(( 8,  9, 0),  6), WCK((3,  9), 2), WCK((2,), 0),    (-4,),     (+5,)));
        self.memcfgs_map[0].append(Memcfg(Boundary(688,  1453), Boundary( 750,  1333), 0b1010, (18, 20,  0), ( 9, 15),       4, (26, 28, 29, 31), (-3,),  (+3,),   4,         WCK(( 8, 10, 0),  7), WCK((4, 10), 2), WCK((2,), 0),    (-4,),     (+5,)));
        self.memcfgs_map[0].append(Memcfg(Boundary(750,  1333), Boundary( 800,  1250), 0b1011, (19, 21,  0), ( 9, 16),       4, (28, 29, 31, 32), (-3,),  (+3,),   4,         WCK(( 9, 11, 0),  7), WCK((4, 11), 2), WCK((2,), 0),    (-4,),     (+5,)));
        self.memcfgs_map[0].append(Memcfg(Boundary(800,  1250), Boundary( 937,  1067), 0b1100, (23, 24,  0), (11, 19),       6, (32, 34, 36, 38), (-4,),  (+3,),   5,         WCK((10, 11, 0),  9), WCK((5, 13), 2), WCK((3,), 0),    (-5,),     (+5,)));
        self.memcfgs_map[0].append(Memcfg(Boundary(937,  1067), Boundary(1066,   938), 0b1101, (26, 28,  0), (12, 22),       6, (37, 39, 41, 43), (-4,),  (+3,),   6,         WCK((11, 13, 0), 10), WCK((5, 15), 2), WCK((3,), 0),    (-5,),     (+5,)));
        # memcfgs_map[1] : Table 201 - DVFSC disabled (MR19 OP[1:0] = 00b) , Read Link ECC off (MR22 OP[7:6]=00b), WCK:CK ratio = 2:1
        #                                         | Lower               | Upper        | OP    | RL          | WL     | nRBTP | nWR              | ODTon | ODToff | WCKPRE | WCKRD                 | WCKWR          | WCKFS     | ODTLoff_RD|ODTLon_RD |
        #                                         | Freq | t_ck         | Freq  | t_ck |       |S0| S1| S2   | A | B  |       | A | B            |       |        | _static| enl            | tgl  | enl     |tgl   | enl | NA  |           |          |
        self.memcfgs_map[1].append(Memcfg(Boundary( 10, 10000), Boundary( 133,  7518), 0b0000, ( 6,  6,  6), ( 4,  4),       0, ( 5,  5        ), (-1,),  (+5,),   1,         WCK((0,  0,  0),  6), WCK((1,  1), 3), WCK((0,), 0),    (-3,),     (+7,)));
        self.memcfgs_map[1].append(Memcfg(Boundary(133,  7518), Boundary( 267,  3750), 0b0001, ( 8,  8,  8), ( 4,  6),       0, (10, 10        ), (-2,),  (+5,),   2,         WCK((0,  0,  0),  7), WCK((0,  2), 3), WCK((0,), 0),    (-4,),     (+7,)));
        self.memcfgs_map[1].append(Memcfg(Boundary(267,  3750), Boundary( 400,  2500), 0b0010, (10, 10, 12), ( 6,  8),       0, (14, 15        ), (-2,),  (+5,),   2,         WCK((1,  1,  3),  8), WCK((1,  3), 4), WCK((1,), 0),    (-4,),     (+7,)));
        self.memcfgs_map[1].append(Memcfg(Boundary(400,  2500), Boundary( 533,  1875), 0b0011, (12, 14, 14), ( 8, 10),       0, (19, 20        ), (-3,),  (+5,),   3,         WCK((2,  4,  4),  8), WCK((2,  4), 4), WCK((1,), 0),    (-5,),     (+8,)));
        self.memcfgs_map[1].append(Memcfg(Boundary(533,  1875), Boundary( 688,  1453), 0b0100, (16, 16, 18), ( 8, 14),       2, (24, 25        ), (-3,),  (+5,),   4,         WCK((3,  3,  5), 10), WCK((1,  7), 4), WCK((1,), 0),    (-5,),     (+8,)));
        self.memcfgs_map[1].append(Memcfg(Boundary(688,  1453), Boundary( 800,  1250), 0b0101, (18, 20, 20), (10, 16),       2, (28, 29        ), (-4,),  (+5,),   4,         WCK((5,  7,  7), 10), WCK((3,  9), 4), WCK((2,), 0),    (-6,),     (+8,)));
        # memcfgs_map[2] : Table 201 - DVFSC disabled (MR19 OP[1:0] = 00b) , Read Link ECC off (MR22 OP[7:6]=00b), WCK:CK ratio = 4:1
        #                                         | Lower               | Upper        | OP    | RL          | WL     | nRBTP | nWR              | ODTon | ODToff | WCKPRE | WCKRD                 | WCKWR          | WCKFS     | ODTLoff_RD|ODTLon_RD |
        #                                         | Freq | t_ck         | Freq  | t_ck |       |S0| S1| S2   | A | B  |       | A | B            |       |        | _static| enl            | tgl  | enl     |tgl   | enl | NA  |           |          |
        self.memcfgs_map[2].append(Memcfg(Boundary(  5, 20000), Boundary(  67, 14930), 0b0000, ( 3,  3,  3), ( 2,  2),       0, ( 3,  3        ), (-1,),  (+3,),   1,         WCK((0,  0,  0),  3), WCK((0,  0), 2), WCK((0,), 0),    (-2,),     (+4,)));
        self.memcfgs_map[2].append(Memcfg(Boundary( 67, 14930), Boundary( 133,  7518), 0b0001, ( 4,  4,  4), ( 2,  3),       0, ( 5,  5        ), (-1,),  (+3,),   1,         WCK((0,  0,  0),  4), WCK((0,  1), 2), WCK((0,), 0),    (-2,),     (+4,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(133,  7518), Boundary( 200,  5000), 0b0010, ( 5,  5,  6), ( 3,  4),       0, ( 7,  8        ), (-1,),  (+3,),   1,         WCK((1,  1,  2),  4), WCK((1,  2), 2), WCK((1,), 0),    (-2,),     (+4,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(200,  5000), Boundary( 267,  3750), 0b0011, ( 6,  7,  7), ( 4,  5),       0, (10, 10        ), (-2,),  (+3,),   2,         WCK((1,  2,  2),  4), WCK((1,  2), 2), WCK((1,), 0),    (-3,),     (+4,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(267,  3750), Boundary( 344,  2907), 0b0100, ( 8,  8,  9), ( 4,  7),       1, (12, 13        ), (-2,),  (+3,),   2,         WCK((2,  2,  3),  5), WCK((1,  4), 2), WCK((1,), 0),    (-3,),     (+4,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(344,  2907), Boundary( 400,  2500), 0b0101, ( 9, 10, 10), ( 5,  8),       1, (14, 15        ), (-2,),  (+3,),   2,         WCK((3,  4,  4),  5), WCK((2,  5), 2), WCK((1,), 0),    (-3,),     (+4,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(400,  2500), Boundary( 467,  2141), 0b0110, (10, 11, 12), ( 6,  9),       2, (16, 17, 18, 19), (-2,),  (+3,),   3,         WCK((3,  4,  5),  5), WCK((2,  5), 2), WCK((1,), 0),    (-3,),     (+4,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(467,  2141), Boundary( 533,  1875), 0b0111, (12, 13, 14), ( 6, 11),       2, (19, 20, 21, 22), (-3,),  (+3,),   3,         WCK((4,  5,  6),  6), WCK((2,  7), 2), WCK((1,), 0),    (-4,),     (+5,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(533,  1875), Boundary( 600,  1667), 0b1000, (13, 14, 15), ( 7, 12),       3, (21, 22, 23, 24), (-3,),  (+3,),   3,         WCK((5,  6,  7),  6), WCK((3,  8), 2), WCK((2,), 0),    (-4,),     (+5,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(600,  1667), Boundary( 688,  1453), 0b1001, (15, 16, 17), ( 8, 14),       4, (24, 25, 27, 28), (-3,),  (+3,),   4,         WCK((6,  7,  8),  6), WCK((3,  9), 2), WCK((2,), 0),    (-4,),     (+5,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(688,  1453), Boundary( 750,  1333), 0b1010, (16, 17, 19), ( 9, 15),       4, (26, 28, 29, 31), (-3,),  (+3,),   4,         WCK((6,  7,  9),  7), WCK((4, 10), 2), WCK((2,), 0),    (-4,),     (+5,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(750,  1333), Boundary( 800,  1250), 0b1011, (17, 18, 20), ( 9, 16),       4, (28, 29, 31, 32), (-3,),  (+3,),   4,         WCK((7,  8, 10),  7), WCK((4, 11), 2), WCK((2,), 0),    (-4,),     (+5,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(800,  1250), Boundary( 937,  1067), 0b1100, (20, 22, 24), (11, 19),       6, (32, 34, 36, 38), (-4,),  (+3,),   5,         WCK((7,  9, 11),  9), WCK((5, 13), 2), WCK((3,), 0),    (-5,),     (+5,)));
        self.memcfgs_map[2].append(Memcfg(Boundary(937,  1067), Boundary(1066,   938), 0b1101, (23, 25, 26), (12, 22),       6, (37, 39, 41, 43), (-4,),  (+3,),   6,         WCK((8, 10, 11), 10), WCK((5, 15), 2), WCK((3,), 0),    (-5,),     (+5,)));

        if self.ref.args.densities:
            self.ref.densities = self.ref.args.densities
        else:
            self.ref.densities = (1, 2, 3, 4, 6, 8, 12, 16, 24, 32)

        self.ref.p_t_rfcpb = OrderedDict(sorted({
             1: Timing( 60,0,0),
             2: Timing( 60,0,0),
             3: Timing( 90,0,0),
             4: Timing( 90,0,0),
             6: Timing(120,0,0),
             8: Timing(120,0,0),
            12: Timing(140,0,0),
            16: Timing(140,0,0),
            24: Timing(190,0,0),
            32: Timing(190,0,0),
        }.items()))

        self.ref.p_t_rfcab = OrderedDict(sorted({
             1: Timing(130,0,0),
             2: Timing(130,0,0),
             3: Timing(180,0,0),
             4: Timing(180,0,0),
             6: Timing(210,0,0),
             8: Timing(210,0,0),
            12: Timing(280,0,0),
            16: Timing(280,0,0),
            24: Timing(380,0,0),
            32: Timing(380,0,0),
        }.items()))

        self.ref.p_t_rfmpb = OrderedDict(sorted({
             1: Timing(110,0,0),
             2: Timing(110,0,0),
             3: Timing(130,0,0),
             4: Timing(130,0,0),
             6: Timing(170,0,0),
             8: Timing(170,0,0),
            12: Timing(190,0,0),
            16: Timing(190,0,0),
            24: Timing(260,0,0),
            32: Timing(260,0,0),
        }.items()))

        self.ref.p_t_rfmab = OrderedDict(sorted({
             1: Timing(130,0,0),
             2: Timing(130,0,0),
             3: Timing(180,0,0),
             4: Timing(180,0,0),
             6: Timing(210,0,0),
             8: Timing(210,0,0),
            12: Timing(280,0,0),
            16: Timing(280,0,0),
            24: Timing(380,0,0),
            32: Timing(380,0,0),
        }.items()))

        self.ref.p_t_pbr2pbr = OrderedDict(sorted({
             1: Timing(60,0,0),
             2: Timing(60,0,0),
             3: Timing(90,0,0),
             4: Timing(90,0,0),
             6: Timing(90,0,0),
             8: Timing(90,0,0),
            12: Timing(90,0,0),
            16: Timing(90,0,0),
            24: Timing(90,0,0),
            32: Timing(90,0,0),
        }.items()))

        self.ref.p_t_xsr_add = Timing(7.5, 2, 0)
        for d in self.ref.densities:
            self.ref.p_t_xsr[d] = self.ref.p_t_xsr_add;

        self.ref.p_t_pbr2act = Timing(7.5, 0, 0)
        self.ref.p_t_rppb = Timing(18, 2, 0)
        self.ref.p_t_rpab = Timing(21, 2, 0)
        self.ref.p_t_cke = Timing(10, 1, 1.75)
        self.ref.p_t_cmdcke = Timing(0, 3, 0) # tCMDPD
        self.ref.p_t_ckesr = Timing(15, 2, 0)
        self.ref.p_t_ckelck = Timing(5.0, 3, 0)
        self.ref.p_t_ckckeh = Timing(1.75, 3, 1)
        self.ref.p_t_cacsh = Timing(1.75, 0, 1.5)
        self.ref.p_t_csh = Timing(3.0, 1, 0)
        self.ref.p_t_pdxl = Timing(1.75, 0, 0)
        self.ref.p_t_ras = Timing(42, 3, 0)
        self.ref.p_t_rc = Timing(self.ref.p_t_ras.min_ns + self.ref.p_t_rppb.min_ns, 7, 0)
        self.ref.p_t_rcd = Timing(18, 2, 0)
        self.ref.p_t_rcdwr = Timing(18, 2, 0)
        self.ref.p_t_ccd_l = Timing(0, 4, 0)
        self.ref.p_t_rrd = Timing( 5, 2, 0)
        self.ref.p_t_faw = Timing(20, 0, 0)

        if True: # FIXME CA or CS ODT is enabled
            self.ref.p_t_xp = Timing(20, 5, 0.75)
        else:
            self.ref.p_t_xp = Timing(7, 5, 0.75)
        self.ref.p_t_xp_mrri = self.ref.p_t_xp + self.ref.p_t_rcd + Timing(0, 0, 2)

        self.ref.p_t_mrw = Timing(10, 5, 0)
        self.ref.p_t_mod = Timing(14, 6, 0)

        self.ref.p_t_rcd_derate = self.ref.p_t_rcd + 1.875
        self.ref.p_t_rcdwr_derate = self.ref.p_t_rcdwr + 1.875
        self.ref.p_t_rc_derate = self.ref.p_t_rc + 3.7
        self.ref.p_t_ras_derate = self.ref.p_t_ras + 1.875
        self.ref.p_t_rpab_derate = self.ref.p_t_rpab + 1.875
        self.ref.p_t_rppb_derate = self.ref.p_t_rppb + 1.875
        self.ref.p_t_rrd_derate = self.ref.p_t_rrd + 1.875

        self.ref.p_t_zqcs = Timing( 0, 0, 0)
        self.ref.p_t_zqcl = Timing(30, 4, 0)

        self.ref.p_t_wckstop = Timing(6, 2, 0)
        self.ref.p_t_cslck = Timing(5, 3, 0)

        self.ref.p_t_odtonmax = Timing(3.5, 0, 0)
        self.ref.p_t_odtonmin = Timing(1.5, 0, 0)
        self.ref.p_t_odtoffmax = Timing(3.5, 0, 0)
        self.ref.p_t_odtoffmin = Timing(1.5, 0, 0)

        self.ref.p_t_tmp = Timing(7.5, 8, 0)
        self.ref.t_rdqs_pre_as_wck = 4

    def update(self, t_ck):
        if self.ref.read_dbi and self.ref.read_lecc:
            self.ref.read_dbi = 0

        self.ref.p_t_wckstop = Timing(6 + int(ceil(t_ck/1000/2/self.ref.data_freq_ratio)) , 2+1, 0)

        if self.ref.byte_mode:
            self.ref.p_t_wr = Timing(36 + 4*self.ref.write_lecc, 3, 0)
            if self.ref.bg_mode:
                self.ref.p_t_wtr = Timing(8.25 + 4*self.ref.write_lecc, 4, 0)
            else:
                self.ref.p_t_wtr = Timing(14 + 4*self.ref.write_lecc, 4, 0)
            self.ref.p_t_wtr_l = Timing(14 + 4*self.ref.write_lecc, 4, 0)
        else:
            self.ref.p_t_wr = Timing(34 + 4*self.ref.write_lecc, 3, 0)
            self.ref.p_t_wtr = Timing(10, 8, 0)
            if self.ref.bg_mode:
                self.ref.p_t_wtr = Timing(6.25 + 4*self.ref.write_lecc, 4, 0)
            else:
                self.ref.p_t_wtr = Timing(12 + 4*self.ref.write_lecc, 4, 0)
            self.ref.p_t_wtr_l = Timing(12 + 4*self.ref.write_lecc, 4, 0)

        self.ref.p_t_wr_p = Timing(self.ref.p_t_wr.min_ns + 0.8, 6, 0.25)
        self.ref.p_n_wr_p = Timing(0.8, 0, 0.25)

        if self.ref.data_freq_ratio == 4:
            self.ref.p_t_rtp = Timing(7.5, 2, 0)
            self.ref.p_t_mrr = Timing(0, 4, 0)
        else:
            self.ref.p_t_rtp = Timing(7.5, 4, 0)
            self.ref.p_t_mrr = Timing(0, 8, 0)

        self.ref.p_t_wck2dqomin = Timing(0.65, 0, 0)
        self.ref.p_t_wck2dqomax = Timing(1.6, 0, 0) if self.ref.wck_hf else Timing(1.9, 0,0)
        self.ref.p_t_wck2dqimin = Timing(0.3, 0, 0)
        self.ref.p_t_wck2dqimax = Timing(0.7, 0, 0) if self.ref.wck_hf else Timing(0.9, 0,0)
        self.ref.p_t_wck2dqo_rank2rank = self.ref.p_t_wck2dqomax - self.ref.p_t_wck2dqomin
        self.ref.p_t_wck2dqi_rank2rank = self.ref.p_t_wck2dqimax - self.ref.p_t_wck2dqimin

        if self.ref.wck_pst == 0:
            self.ref.t_wck_pst_as_wck = 2.5
        elif self.ref.wck_pst == 1:
            self.ref.t_wck_pst_as_wck = 4.5
        else:
            self.ref.t_wck_pst_as_wck = 6.5

        if self.ref.rdqs_pst == 0:
            self.ref.t_rdqs_pst_as_wck = 0.5
        elif self.ref.rdqs_pst == 1:
            self.ref.t_rdqs_pst_as_wck = 2.5
        else:
            self.ref.t_rdqs_pst_as_wck = 4.5

        if self.ref.bg_mode:
            self.ref.bl_nmax = 16//self.ref.data_freq_ratio
            self.ref.bl_nmin = self.ref.bl_nmax//2
        else:
            self.ref.bl_nmax = 16//(2*self.ref.data_freq_ratio)
            self.ref.bl_nmin = self.ref.bl_nmax

        if self.ref.read_lecc:
            self.memcfgs = self.memcfgs_map[0]
        elif self.ref.data_freq_ratio == 2:
            self.memcfgs = self.memcfgs_map[1]
        else:
            self.memcfgs = self.memcfgs_map[2]

        self.ref.memcfg = self.search_memcfgs(t_ck)

        self.ref.rl_set = 0
        self.ref.wl_set = 0
        self.ref.nwr_set = 1 if self.ref.byte_mode else 0
        if self.ref.byte_mode:
            self.ref.rl_set += 1
        if self.ref.read_dbi:
            self.ref.rl_set += 1
        if self.ref.write_lecc:
            self.ref.nwr_set += 2

        if self.ref.bg_mode:
            self.ref.bank_mode = 0
        else:
            self.ref.bank_mode = 0b10 # 16B mode

        self.ref.wck_mode = self.ref.wck_always_on
        self.ref.asize_ctrl = 1 if self.ref.data_freq_ratio == 2 else 0

    def calculate(self, t_ck):
        t_ck_ns = t_ck/1000

        self.ref.odtlon = self.ref.write_latency + self.ref.memcfg.odtlon[0]
        self.ref.odtloff = self.ref.write_latency + self.ref.memcfg.odtloff[0]
        self.ref.odtlon_rd = self.ref.read_latency + self.ref.memcfg.odtlon_rd[0]
        self.ref.odtloff_rd = self.ref.read_latency + self.ref.memcfg.odtloff_rd[0]
        self.ref.t_wckenl_fs = self.ref.memcfg.wck_fs.enl[0]
        self.ref.t_wckenl_rd = self.ref.memcfg.wck_rd.enl[self.ref.rl_set]
        self.ref.t_wckenl_wr = self.ref.memcfg.wck_wr.enl[self.ref.wl_set]
        self.ref.t_wckpre_static = self.ref.memcfg.wckpre_static

        self.ref.t_mod += 1 # MRW is a two-cycle command
        self.ref.t_mrw += 1

        self.ref.t_ccd_l = self.ref.p_t_ccd_l.calc_ceil(t_ck)
        self.ref.t_ccdmw = 4*self.ref.bl_nmax
        self.ref.t_ccdmw_bg = self.ref.bl_nmax if self.ref.bg_mode else 0

        self.ref.t_rdqs_pst_f = int(floor(self.ref.t_rdqs_pst_as_wck/self.ref.data_freq_ratio))

        use_rdqs_as_input = self.ref.write_lecc # Write Link ECC || WCK-RDQS training || Read/Write based WCK-RDQS training. Only the first one is used by MC;
        rdqs_mode = 0b10 # FIXME
        if self.ref.bg_mode:
            t_rtw      = self.ref.read_latency + self.ref.bl_nmax + self.ref.p_t_wck2dqomax.calc_ceil(t_ck) - self.ref.write_latency + (1 if use_rdqs_as_input else 0)
            t_rtw_odt  = self.ref.read_latency + self.ref.bl_nmax + self.ref.p_t_wck2dqomax.calc_ceil(t_ck) + self.ref.t_rdqs_pst_f - self.ref.odtlon - self.ref.p_t_odtonmin.calc_floor(t_ck) + 1 + (use_rdqs_as_input or (not self.ref.args.enhanced_nt_odt) and self.ref.nt_odt)

        else:
            t_rtw      = self.ref.read_latency + self.ref.bl_nmax + self.ref.p_t_wck2dqomax.calc_ceil(t_ck) - self.ref.write_latency
            t_rtw_odt  = self.ref.read_latency + self.ref.bl_nmax + self.ref.p_t_wck2dqomax.calc_ceil(t_ck) + self.ref.t_rdqs_pst_f - self.ref.odtlon - self.ref.p_t_odtonmin.calc_floor(t_ck) + 1

            if use_rdqs_as_input == 0:
              t_rtw_odt += 4//self.ref.data_freq_ratio if (rdqs_mode != 0 and (not self.ref.args.enhanced_nt_odt) and self.ref.nt_odt) else 0
            else:
              t_rtw     += 1 if rdqs_mode != 0 else 0
              t_rtw_odt += 1 if rdqs_mode != 0 else 0

        if self.ref.write_odt:
            self.ref.t_rtw = max(t_rtw, t_rtw_odt)
        else:
            self.ref.t_rtw = t_rtw

        if self.ref.write_odt:
            self.ref.t_wtwcr = self.ref.odtloff + self.ref.p_t_odtoffmax.calc_ceil(t_ck) - self.ref.odtlon
        else:
            self.ref.t_wtwcr = self.ref.bl_nmin + self.ref.p_t_wck2dqi_rank2rank.calc_ceil(t_ck)

        self.ref.t_rtrcr = int(ceil(0.99*(self.ref.t_rdqs_pre_as_wck + floor(self.ref.t_rdqs_pst_as_wck))/self.ref.data_freq_ratio)) + self.ref.p_t_wck2dqo_rank2rank.calc_ceil(t_ck)
        if self.ref.wck_always_on == True and self.ref.write_odt and self.ref.nt_odt:
            self.ref.t_rtrcr = self.ref.odtlon_rd - self.ref.odtloff_rd - (2 if self.ref.data_freq_ratio == 4 else 4)

        self.ref.t_rdidle = self.ref.read_latency + self.ref.p_t_wck2dqomax.calc_ceil(t_ck) + self.ref.bl_nmax + int(ceil(self.ref.t_rdqs_pst_as_wck/self.ref.data_freq_ratio)) + self.ref.p_t_tmp.calc_ceil(t_ck);
        self.ref.t_rtrrd = self.ref.t_rdidle

        self.ref.t_wtr_a = self.ref.write_latency + self.ref.bl_nmax + self.ref.p_t_wtr.calc_ceil(t_ck)
        self.ref.t_wtr_a_l = self.ref.write_latency + self.ref.bl_nmax + self.ref.p_t_wtr_l.calc_ceil(t_ck)
        if self.ref.write_odt:
            if self.ref.nt_odt:
                self.ref.t_wtrcr = self.ref.odtloff + self.ref.p_t_odtoffmax.calc_ceil(t_ck) - (self.ref.read_latency - (int(floor(self.ref.t_rdqs_pre_as_wck/self.ref.data_freq_ratio)) if self.ref.write_lecc or self.ref.read_lecc or not self.ref.args.enhanced_nt_odt else 0))
            else:
                self.ref.t_wtrcr = self.ref.odtloff + self.ref.p_t_odtoffmax.calc_ceil(t_ck) - (self.ref.read_latency - (int(floor(self.ref.t_rdqs_pre_as_wck/self.ref.data_freq_ratio)) if self.ref.write_lecc or self.ref.read_lecc else 0))
        else:
            self.ref.t_wtrcr = self.ref.write_latency + self.ref.bl_nmin + 1 - (self.ref.read_latency - (int(floor(self.ref.t_rdqs_pre_as_wck/self.ref.data_freq_ratio)) if self.ref.write_lecc or self.ref.read_lecc else 0))

        if (self.ref.bank_mode == 0):
            self.ref.t_wtrcr = max(self.ref.t_wtrcr, 3)

        self.ref.t_wr_a = self.ref.write_latency + 1 + self.ref.bl_nmax + self.ref.t_wr
        self.ref.n_wr_a = self.ref.write_latency + 1 + self.ref.bl_nmax + self.ref.n_wr

        self.ref.t_wr_p = self.ref.write_latency + 1 + self.ref.bl_nmax + self.ref.t_wr + self.ref.p_t_wck2dqimax.calc_ceil(t_ck)
        self.ref.n_wr_p = self.ref.write_latency + 1 + self.ref.bl_nmax + self.ref.n_wr + self.ref.p_t_wck2dqimax.calc_ceil(t_ck) + self.ref.t_cmdcke

        # XP control
        self.ref.t_xp_mrri = self.ref.p_t_xp.calc_ceil(t_ck) + self.ref.p_t_rcd.calc_ceil(t_ck) + 2
        self.ref.t_xp += self.ref.t_csh - 1
        self.ref.t_xp_mrri += self.ref.t_csh - 1
        self.ref.t_pdxl += self.ref.t_csh

        # WCK control
        self.ref.t_casoff = int(ceil(self.ref.t_wck_pst_as_wck/self.ref.data_freq_ratio))
        self.ref.t_casoff = max(self.ref.t_casoff, self.ref.p_t_wckstop.calc_ceil(t_ck))

        self.ref.t_wck_pst_f = int(floor(self.ref.t_wck_pst_as_wck/self.ref.data_freq_ratio))

        self.ref.t_wckoff_on = max(self.ref.t_casoff - self.ref.t_wckenl_fs + 1, 3)
        self.ref.t_wckoff_fs = max(self.ref.t_wckenl_fs + self.ref.t_wckpre_static, 6)
        self.ref.t_wckoff_rd = self.ref.read_latency + self.ref.bl_nmax + self.ref.t_wck_pst_f + 1
        self.ref.t_wckoff_wr = self.ref.write_latency+ self.ref.bl_nmax + self.ref.t_wck_pst_f + 1

        self.ref.t_wcktgl_cs = 0
        self.ref.t_wcktgl_rd = self.ref.memcfg.wck_rd.pre_toggle # not yet
        self.ref.t_wcktgl_wr = self.ref.memcfg.wck_rd.pre_toggle # not yet
        self.ref.t_wck_fast_tgl = 1
        self.ref.t_wck_tgl = self.ref.t_wckpre_static
        if not self.ref.wck_always_on and self.ref.write_odt:
            self.ref.t_add_wrtowck_rtr = max(0, self.ref.p_t_odtoffmax.calc_ceil(t_ck) - self.ref.t_wck_pst_f - 2)
            self.ref.t_add_rdtowrwck_rtr = max(0, self.ref.t_wckenl_wr - (self.ref.odtlon + self.ref.p_t_odtonmin.calc_floor(t_ck)) - 2)

        self.ref.tdram_clk_enable = self.ref.tctrl_delay + 2 + 2