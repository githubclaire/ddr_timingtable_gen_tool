# DDR Timing Table Binary Layout Fix Plan

## Issue Summary

Reference binaries have **garbage/uninitialized values** at C struct expected offsets. All 4 configurations (LP4 Single/Dual, LP5 Single/Dual) have incorrect binary layouts that don't match the C struct definitions.

### Root Cause
- Reference binary generation was inconsistent/incomplete
- gui.py uses hardcoded offsets that differ from C struct layout by +1 to +9 offset
- Test coverage only compares timing table (0x0-0x800), NOT orbit config section (0x800+)

---

## Complete Field Offset Analysis (LP4 Single)

### Summary
- **Total C struct fields**: 86 fields
- **Fields parsed by gui.py**: 49 fields
- **MISSING from gui.py**: 22 fields (not parsed at all)
- **WRONG offset in gui.py**: 46 fields (parsed but at wrong offset)
- **All 68 parsed fields need fixing** + 22 missing to add

### Fields MISSING from gui.py (22 fields - not parsed at all)
```
base_addr                      (C offset 0xBF)
base_addr_id                   (C offset 0xC3)
boot_t_ck                      (C offset 0x7F)
boot_t_ck_low                  (C offset 0x83)
byte_lane_inversion            (C offset 0x103)
chip                           (C offset 0x8F)
density_code                   (C offset 0x77)
dfs_lvl_t_ck                   (C offset 0x5D) - note: gui parses _0, _1, _2 separately
dram_t_ck                      (C offset 0x87)
half_dq_en                     (C offset 0x35)
link_err_cnt_th                (C offset 0xFB)
lpddr4_rpre                    (C offset 0x37)
num_of_ch                      (C offset 0xB7)
num_of_region                  (C offset 0x63)
phy_base_addr                  (C offset 0xCB)
phy_base_addr_id               (C offset 0xCF)
phy_ind_mode_en                (C offset 0x29)
phy_odt                        (C offset 0x47)
prev_dram_t_ck                 (C offset 0x8B)
rclk_t_ck                      (C offset 0x7B)
tctrlupd_interval              (C offset 0xE7)
tphyupd_resp                   (C offset 0xD7)
```

### Fields with WRONG Offset in gui.py (46 fields)

Most have **+1 offset difference** (because gui.py doesn't account for lp5_mr* header fields in LPDDR5 struct that shift all subsequent offsets).

Key mismatches with larger differences:
```
t_refipb:         C=0xEF, GUI=0xF4  (diff +5)
zq_calibration_period: C=0xE3, GUI=0xEC  (diff +9)
dynamic_power_down_threshold: C=0xDF, GUI=0xDC  (diff -3)
dynamic_self_refresh_threshold: C=0xDB, GUI=0xD8  (diff -3)
dram_vref_trn_mode: C=0x73, GUI=0x76  (diff +3)
dram_duty_trn_mode: C=0x75, GUI=0x78  (diff +3)
phy_duty_trn_mode: C=0x71, GUI=0x74  (diff +3)
phy_vref_trn_mode: C=0x6F, GUI=0x72  (diff +3)
```

Full list of offset differences:
```
ca_odt:                  C=0x45, GUI=0x46   (diff +1)
ca_vref_training:        C=0x67, GUI=0x68   (diff +1)
command_bus_training:    C=0x65, GUI=0x66   (diff +1)
cpipe_depth:            C=0x13, GUI=0x14   (diff +1)
ctrl_dq_width:          C=0x23, GUI=0x24   (diff +1)
density:                C=0x1B, GUI=0x1C   (diff +1)
dfs_training:           C=0x6D, GUI=0x6E   (diff +1)
dpipe_depth:            C=0x15, GUI=0x16   (diff +1)
dq_width:               C=0x25, GUI=0x24   (diff -1)
dram_clock_gating:      C=0x5B, GUI=0x5C   (diff +1)
dram_duty_trn_mode:      C=0x75, GUI=0x78   (diff +3)
dram_vref_trn_mode:      C=0x73, GUI=0x76   (diff +3)
dsm_en:                 C=0x3B, GUI=0x3C   (diff +1)
dynamic_power_down:     C=0x53, GUI=0x54   (diff +1)
dynamic_power_down_threshold: C=0xDF, GUI=0xDC  (diff -3)
dynamic_self_refresh:   C=0x55, GUI=0x56   (diff +1)
dynamic_self_refresh_threshold: C=0xDB, GUI=0xD8  (diff -3)
eye_scan_prbs_rd_en:     C=0x41, GUI=0x42   (diff +1)
eye_scan_prbs_wr_en:     C=0x43, GUI=0x44   (diff +1)
eye_scan_rd_en:          C=0x3D, GUI=0x3E   (diff +1)
eye_scan_wr_en:          C=0x3F, GUI=0x40   (diff +1)
init_zq_calibration:    C=0x49, GUI=0x4A   (diff +1)
mrr_byte_lane:          C=0xFF, GUI=0x100  (diff +1)
num_rank:               C=0x1F, GUI=0x20   (diff +1)
omc_freq_ratio:          C=0x0D, GUI=0x0E   (diff +1)
periodic_training:      C=0x4F, GUI=0x50   (diff +1)
periodic_training_period: C=0x51, GUI=0x52  (diff +1)
phy_clock_gating:       C=0x59, GUI=0x5A   (diff +1)
phy_duty_trn_mode:       C=0x71, GUI=0x74   (diff +3)
phy_freq_ratio:          C=0x0B, GUI=0x0C   (diff +1)
phy_idle_cnt_th:         C=0x2D, GUI=0x2E   (diff +1)
phy_low_power:          C=0x2B, GUI=0x2C   (diff +1)
phy_vref_trn_mode:       C=0x6F, GUI=0x72   (diff +3)
prbs_training:          C=0x69, GUI=0x6A   (diff +1)
rank_interleaving:       C=0x1D, GUI=0x1E   (diff +1)
reboot_with_mrw:        C=0x21, GUI=0x22   (diff +1)
reboot_with_training:   C=0x6B, GUI=0x6C   (diff +1)
regional_clock_gating:  C=0x57, GUI=0x58   (diff +1)
rfm_en:                 C=0x39, GUI=0x3A   (diff +1)
t_refiab:               C=0xF3, GUI=0xF4   (diff +1)
t_refipb:               C=0xEF, GUI=0xF4   (diff +5)
t_zqcal:                C=0xF7, GUI=0xF8   (diff +1)
temp_sensing:           C=0x4B, GUI=0x4C   (diff +1)
temp_sensing_period:    C=0xEB, GUI=0xEC   (diff +1)
zq_calibration:         C=0x4D, GUI=0x4E   (diff +1)
zq_calibration_period:  C=0xE3, GUI=0xEC   (diff +9)
```

---

## C Struct Offsets Reference (All 4 Configurations)

### LP4 Single (NUM_OF_OMC=2, NUM_OF_PHY=2) - struct size: 3048 bytes
| Field | Offset |
|-------|--------|
| dram_boot | 0x00 |
| ch_intr_size | 0x01 |
| bg_intr_size | 0x02 |
| fsp_op | 0x03 |
| fsp_wr | 0x04 |
| dq_vref_byte0 | 0x05 |
| dq_vref_byte1 | 0x07 |
| ca_vref | 0x09 |
| phy_freq_ratio | 0x0B |
| omc_freq_ratio | 0x0D |
| int_cpipe_depth | 0x0F |
| int_dpipe_depth | 0x11 |
| cpipe_depth | 0x13 |
| dpipe_depth | 0x15 |
| reboot | 0x17 |
| reqq_depth | 0x19 |
| density | 0x1B |
| rank_interleaving | 0x1D |
| num_rank | 0x1F |
| reboot_with_mrw | 0x21 |
| ctrl_dq_width | 0x23 |
| dq_width | 0x25 |
| use_dfi_train_if | 0x27 |
| phy_ind_mode_en | 0x29 |
| phy_low_power | 0x2B |
| phy_idle_cnt_th | 0x2D |
| lp_wakeup | 0x2F |
| half_dq_en | 0x35 |
| lpddr4_rpre | 0x37 |
| rfm_en | 0x39 |
| dsm_en | 0x3B |
| eye_scan_rd_en | 0x3D |
| eye_scan_wr_en | 0x3F |
| eye_scan_prbs_rd_en | 0x41 |
| eye_scan_prbs_wr_en | 0x43 |
| ca_odt | 0x45 |
| phy_odt | 0x47 |
| init_zq_calibration | 0x49 |
| temp_sensing | 0x4B |
| zq_calibration | 0x4D |
| periodic_training | 0x4F |
| periodic_training_period | 0x51 |
| dynamic_power_down | 0x53 |
| dynamic_self_refresh | 0x55 |
| regional_clock_gating | 0x57 |
| phy_clock_gating | 0x59 |
| dram_clock_gating | 0x5B |
| dfs_lvl_t_ck | 0x5D |
| num_of_region | 0x63 |
| command_bus_training | 0x65 |
| ca_vref_training | 0x67 |
| prbs_training | 0x69 |
| reboot_with_training | 0x6B |
| dfs_training | 0x6D |
| phy_vref_trn_mode | 0x6F |
| phy_duty_trn_mode | 0x71 |
| dram_vref_trn_mode | 0x73 |
| dram_duty_trn_mode | 0x75 |
| density_code | 0x77 |
| rclk_t_ck | 0x7B |
| boot_t_ck | 0x7F |
| boot_t_ck_low | 0x83 |
| dram_t_ck | 0x87 |
| prev_dram_t_ck | 0x8B |
| chip | 0x8F |
| num_of_ch | 0xB7 |
| base_addr | 0xBF |
| base_addr_id | 0xC3 |
| phy_base_addr | 0xCB |
| phy_base_addr_id | 0xCF |
| tphyupd_resp | 0xD7 |
| dynamic_self_refresh_threshold | 0xDB |
| dynamic_power_down_threshold | 0xDF |
| zq_calibration_period | 0xE3 |
| tctrlupd_interval | 0xE7 |
| temp_sensing_period | 0xEB |
| t_refipb | 0xEF |
| t_refiab | 0xF3 |
| t_zqcal | 0xF7 |
| link_err_cnt_th | 0xFB |
| mrr_byte_lane | 0xFF |
| byte_lane_inversion | 0x103 |
| region_start | 0x107 |
| region_end | 0x117 |
| prbs_result | 0x127 |
| train_result | 0x147 |

### LP4 Dual (NUM_OF_OMC=4, NUM_OF_PHY=4) - struct size: 5816 bytes
Key offset differences from single:
| Field | Offset |
|-------|--------|
| dynamic_self_refresh_threshold | 0xEB |
| dynamic_power_down_threshold | 0xEF |
| zq_calibration_period | 0xF3 |
| tctrlupd_interval | 0xF7 |
| temp_sensing_period | 0xFB |
| t_refipb | 0xFF |
| t_refiab | 0x103 |
| t_zqcal | 0x107 |
| link_err_cnt_th | 0x10B |
| mrr_byte_lane | 0x10F |

### LP5 Single - struct size: 3056 bytes
Key offset differences from LP4:
| Field | Offset |
|-------|--------|
| (lp5 header fields before phy_freq_ratio shift all offsets) |
| dynamic_self_refresh_threshold | 0xE2 |
| dynamic_power_down_threshold | 0xE6 |
| zq_calibration_period | 0xEA |
| tctrlupd_interval | 0xEE |
| temp_sensing_period | 0xF2 |
| t_refipb | 0xF6 |
| t_refiab | 0xFA |
| t_zqcal | 0xFE |
| link_err_cnt_th | 0x102 |
| mrr_byte_lane | 0x106 |

### LP5 Dual - struct size: 5824 bytes
Key offset differences from LP5 single:
| Field | Offset |
|-------|--------|
| dynamic_self_refresh_threshold | 0xF2 |
| dynamic_power_down_threshold | 0xF6 |
| zq_calibration_period | 0xFA |
| tctrlupd_interval | 0xFE |
| temp_sensing_period | 0x102 |
| t_refipb | 0x106 |
| t_refiab | 0x10A |
| t_zqcal | 0x10E |
| link_err_cnt_th | 0x112 |
| mrr_byte_lane | 0x116 |

---

## Test Coverage Gaps

### test_lpddr4.sh (line 46)
```python
TIMING_SIZE = 0x800  # Only compares timing table, NOT orbit config!
```

### test_lpddr5.sh
Same issue - only compares first 0x800 bytes

### test_gui_params.py (lines 1083, 1552)
```python
compare_binaries_timing(gui_bin, cli_bin, 0x800)  # Only compares 0x800 bytes
```

---

## Implementation Plan

### Phase 1: Regenerate Reference Binaries

1. Run `./test_gen_lpddr4_bin.sh` → generates LP4 single/dual .ref.bin
2. Run `./test_gen_lpddr5_bin.sh` → generates LP5 single/dual .ref.bin
3. Analyze generated binary layout vs C struct expectations
4. Investigate any differences between Python ctypes struct output and expected

### Phase 2: Fix Binary Compare Test Coverage + Timing Table Check

1. **test_lpddr4.sh line 46**: Change TIMING_SIZE to compare full binary or at least orbit section (0x800+)
2. **test_lpddr5.sh**: Same fix
3. **test_gui_params.py** lines 1083, 1552: Change compare size to cover full binary

### Phase 2b: Verify Timing Table Params (CLI Comparison)

Currently timing table comparison covers 0x800 bytes which includes:
- periods (t_ck values)
- write-odt-upto
- read-dbi-upto
- write-dbi-upto
- read-lecc-upto
- write-lecc-upto
- wck-1to4-upto
- dfs-lvl-t-ck values

**Task**: Verify the GUI → CLI timing parameter comparison is complete and working.

### Phase 2c: Fix Checkbox Value Handling Bug

**Bug Location**: `templates/gui.html` line 941-943

**Issue**: The `generate()` function only sets `'false'` for unchecked checkboxes, but does NOT set `'1'` for checked checkboxes.

```javascript
// BUGGY (line 941-943)
checkboxes.forEach(cb => {
    if (!cb.checked) params[cb.name] = 'false';
    // MISSING: Should also set '1' for checked checkboxes!
});

// CORRECT version (line 1213-1214 - works correctly)
checkboxes.forEach(cb => params[cb.name] = cb.checked ? '1' : '0');
```

**Affected Checkboxes** (may not be passed correctly to CLI):
- variable-trrd
- txr-as-1st-ed
- enhanced-nt-odt
- two-channel
- orbit-rank-interleaving
- orbit-reboot-with-mrw
- reboot-with-training
- eye-scan-rd-en, eye-scan-wr-en, eye-scan-prbs-rd-en, eye-scan-prbs-wr-en
- phy-vref-trn-mode, phy-duty-trn-mode
- dram-vref-trn-mode, dram-duty-trn-mode
- command-bus-training
- ca-vref-training
- prbs-training
- regional-clock-gating, dram-clock-gating, phy-clock-gating
- phy-low-power
- dynamic-power-down, dynamic-self-refresh
- orbit-rfm-en, orbit-dsm-en
- orbit-ca-odt
- init-zq-calibration
- zq-calibration
- dfs-training
- periodic-training
- temp-sensing

**Fix**: Update line 941-943 to match the correct pattern at line 1213-1214

**Test**: Add test case to verify checkbox values are correctly passed to CLI

### Phase 3: Compare C vs Python Binary

1. Run test_lpddr4.sh to generate both C and Python binaries
2. Compare full binary (including orbit config section 0x800+)
3. Investigate any differences

### Phase 4: Fix ALL gui.py Parsing Offsets

This is a major fix - need to update ALL 68 fields with wrong offsets.

#### Option A: Use dynamic offset calculation (RECOMMENDED)
Instead of hardcoding offsets, calculate them dynamically from the ctypes struct.

#### Option B: Fix all hardcoded offsets manually
Update each field's offset in gui.py to match C struct.

### Phase 5: Add 22 Missing Fields to gui.py Parsing

Add parsing for these fields that are currently not read:
- base_addr, base_addr_id
- boot_t_ck, boot_t_ck_low
- byte_lane_inversion
- chip (struct, may need special handling)
- density_code
- dram_t_ck
- half_dq_en
- link_err_cnt_th
- lpddr4_rpre
- num_of_ch (array)
- num_of_region
- phy_base_addr, phy_base_addr_id
- phy_ind_mode_en
- phy_odt
- prev_dram_t_ck
- rclk_t_ck
- tctrlupd_interval
- tphyupd_resp

### Phase 6: Update test_gui_params.py Offset Tests

- Update `test_parse_offset_comparison()` (line 1869+) to use correct C struct offsets
- Update all binary compare sizes to cover full binary

### Phase 7: Run Tests

1. `python test_binary_parse.py`
2. `python test_gui_params.py`
3. `./test_lpddr4.sh`
4. `./test_lpddr5.sh`

---

## Files to Modify

1. **gui.py** - Fix ALL 68 field offsets + add 22 missing fields
2. **templates/gui.html** (line 941-943) - Fix checkbox value handling in generate() function
3. **test_lpddr4.sh** (line 46) - Fix binary compare size
4. **test_lpddr5.sh** - Same fix
5. **test_gui_params.py** (lines 1083, 1552, 1869+) - Fix compare size and offset tests

---

## Commands to Run

```bash
# Regenerate reference binaries
./test_gen_lpddr4_bin.sh
./test_gen_lpddr5_bin.sh

# Run tests
python test_binary_parse.py
python test_gui_params.py
./test_lpddr4.sh
./test_lpddr5.sh
```