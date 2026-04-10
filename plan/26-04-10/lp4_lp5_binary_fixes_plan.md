# LP4/LP5 Binary Issues Fix Plan - 2026-04-10

## Investigation Summary

### LP5 Works Correctly (No Fix Needed)

LP5 struct has different field offsets than LP4, but gui.py uses the CORRECT offsets for LP5.

### LP4 Has Wrong Offsets

| Field | LP4 gui.py uses | LP4 should use |
|-------|-----------------|----------------|
| rclk_t_ck | 0x8C | **0x7C** |
| boot_t_ck | 0x90 | **0x80** |
| dram_t_ck | 0x88 | 0x88 ✓ |

---

## Issues to Fix

### Issue 1: CLI Argument Missing

Add to gen_timing_params:
```python
orbit_grp.add_argument('--orbit-phy-idle-cnt-th', type=int, default=0)
orbit_grp.add_argument('--orbit-phy-low-power', type=int, default=0, choices=[0,1])
```

### Issue 2: LP4 Orbit Config Wrong Offsets

Change gui.py lines 434-436:
- rclk_t_ck: 0x8C → 0x7C
- boot_t_ck: 0x90 → 0x80

### Issue 3: Density Index Calculation

Replace formula with proper mapping.

---

## Comprehensive Test Cases

### TC1: Orbit Config (52 fields per config × 4 configs = 208 validations)

**LP4 Fields:**
| # | Field | Offset | # | Field | Offset |
|---|-------|-------|---|-------|-------|
| 1 | phy_freq_ratio | 0x0C | 27 | phy_duty_trn_mode | 0x72 |
| 2 | omc_freq_ratio | 0x0E | 28 | dram_vref_trn_mode | 0x74 |
| 3 | cpipe_depth | 0x14 | 29 | dram_duty_trn_mode | 0x76 |
| 4 | dpipe_depth | 0x16 | 30 | regional_clock_gating | 0x58 |
| 5 | dram_t_ck | 0x88 | 31 | phy_clock_gating | 0x5A |
| 6 | rclk_t_ck | **0x7C** | 32 | dram_clock_gating | 0x5C |
| 7 | boot_t_ck | **0x80** | 33 | phy_low_power | 0x2C |
| 8 | density | 0x1C | 34 | phy_idle_cnt_th | 0x2E |
| 9 | rank_interleaving | 0x1E | 35 | dynamic_power_down | 0x54 |
| 10 | num_rank | 0x20 | 36 | dynamic_self_refresh | 0x56 |
| 11 | ctrl_dq_width | 0x24 | 37 | dp_threshold | var |
| 12 | dq_width | 0x24 | 38 | ds_threshold | var |
| 13 | reboot_with_mrw | 0x22 | 39 | temp_sensing | 0x4C |
| 14 | rfm_en | 0x3A | 40 | zq_calibration | 0x4E |
| 15 | dsm_en | 0x3C | 41 | periodic_training | 0x50 |
| 16 | ca_odt | 0x46 | 42 | periodic_training_period | 0x52 |
| 17 | eye_scan_rd_en | 0x3E | 43 | dfs_lvl_t_ck_0 | 0x5E |
| 18 | eye_scan_wr_en | 0x40 | 44 | dfs_lvl_t_ck_1 | 0x60 |
| 19 | eye_scan_prbs_rd_en | 0x42 | 45 | dfs_lvl_t_ck_2 | 0x62 |
| 20 | eye_scan_prbs_wr_en | 0x44 | 46 | zq_calibration_period | 0xE4/0xF4 |
| 21 | init_zq_calibration | 0x4A | 47 | temp_sensing_period | 0xEC/0xFC |
| 22 | command_bus_training | 0x66 | 48 | t_refipb | 0xF0/0x100 |
| 23 | ca_vref_training | 0x68 | 49 | t_refiab | 0xF4/0x104 |
| 24 | prbs_training | 0x6A | 50 | t_zqcal | 0xF8/0x108 |
| 25 | reboot_with_training | 0x6C | 51 | mrr_byte_lane | 0x100/0x110 |
| 26 | dfs_training | 0x6E | | | |
| 27 | phy_vref_trn_mode | 0x70 | | | |

**LP5** uses same 52 fields with offsets +8 for most (due to extra header).

---

### TC2: Timing Entry Params (59 fields per entry × 4 entries × 4 configs)

**Per-entry scalar (28):**
rl, wl, mr_rl, mr_wl, mr_wr, mr_rtp, mr_cal, mr_tccd_l, wck_ratio, tlp_resp, dll_enable, write_odt, nt_odt, write_dbi, read_dbi, wpste, rpste, bank_mode, wck_fm, rdqs_pst_mode, rdqs_pst, rdqs_pre, wck_pst, wck_on, read_link_parity, write_link_parity, t_rtw, t_wtr_a, t_wtr, t_rc, trddata_en

**Array (31):**
timing_param[21], timing_derate[2], dfi_timing_param[8]

---

### TC3: Density Index - ALL densities

**LP4:** [2, 3, 4, 6, 8, 12, 16] - 7 densities
**LP5:** [1, 2, 3, 4, 6, 8, 12, 16, 24, 32] - 10 densities

---

### TC4: CLI New Arguments

- --orbit-phy-idle-cnt-th=111
- --orbit-phy-low-power=1

---

## Verification Steps

### Orbit Config (52 × 4 = 208 validations)
1. LP4 Single: all 52 fields
2. LP4 Dual: all 52 fields
3. LP5 Single: all 52 fields (verify unchanged)
4. LP5 Dual: all 52 fields (verify unchanged)

### Timing Entry (59 × 4 × 4 = 944 validations)
5. LP4 Single: all 59 fields
6. LP4 Dual: all 59 fields
7. LP5 Single: all 59 fields
8. LP5 Dual: all 59 fields

### Density (7 + 10 = 17 validations)
9. LP4: [2,3,4,6,8,12,16] all tested
10. LP5: [1,2,3,4,6,8,12,16,24,32] all tested

### CLI (2 validations)
11. Test --orbit-phy-idle-cnt-th=111
12. Test --orbit-phy-low-power=1

**Total: 1,173 validation points**

---

## Implementation Steps

1. Add CLI arguments to gen_timing_params
2. Fix LP4 rclk_t_ck/boot_t_ck offsets in gui.py
3. Fix density index calculation in gui.py
4. Run all test scripts to verify