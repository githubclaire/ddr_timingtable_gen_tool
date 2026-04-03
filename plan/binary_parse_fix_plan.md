# Binary Parse Fix Plan - Comprehensive

## Date: 2026-04-03

## Goal

Fix gui.py binary parsing to parse ALL fields from binary instead of using hardcoded values.

## Issues Identified

### 1. Timing Features - LECC Offsets Wrong
- `read_link_parity`: Currently at `offset + 179`, should be `offset + 0x11F` (191)
- `write_link_parity`: Currently at `offset + 180`, should be `offset + 0x120` (192)

### 2. Basic Parameters - Hardcoded
- `dq_width`: Hardcoded to 16, should parse from binary (0x826 for LPDDR4, 0x834 for LPDDR5)

### 3. Pipe Configuration - Partially Hardcoded
- `omc_freq_ratio`: Parsed but may have wrong offset
- `phy_freq_ratio`: Parsed but may have wrong offset

### 4. Orbit Config - Almost ALL Hardcoded
Only 11 fields parsed, 37+ fields hardcoded:
- reboot_with_mrw, rfm_en, dsm_en, ca_odt
- eye_scan_rd_en, eye_scan_wr_en, eye_scan_prbs_rd_en, eye_scan_prbs_wr_en
- init_zq_calibration, temp_sensing, zq_calibration, periodic_training
- regional_clock_gating, dram_clock_gating, phy_clock_gating
- command_bus_training, ca_vref_training, prbs_training
- reboot_with_training, dfs_training
- phy_vref_trn_mode, phy_duty_trn_mode, dram_vref_trn_mode, dram_duty_trn_mode
- zq_calibration_period, t_refiab, t_refipb, t_zqcal, temp_sensing_period, mrr_byte_lane

---

## Implementation

### 1. Fix LECC Offsets (gui.py lines 464-480)

```python
# BEFORE:
read_link_parity = data[offset + 179]
write_link_parity = data[offset + 180]

# AFTER:
read_link_parity = data[offset + 0x11F]  # 191
write_link_parity = data[offset + 0x120]  # 192
```

### 2. Expand fields_to_read (gui.py lines 546-558)

Add 37 new fields to parse from binary:

#### LPDDR4 Single Channel Offsets (struct offset -> file offset):

| Field | Struct | File | Size | Type |
|-------|--------|------|------|------|
| reboot_with_mrw | 0x22 | 0x822 | 2 | uint16 |
| ctrl_dq_width | 0x24 | 0x824 | 2 | uint16 |
| dq_width | 0x26 | 0x826 | 2 | uint16 |
| rfm_en | 0x3A | 0x83A | 2 | uint16 |
| dsm_en | 0x3C | 0x83C | 2 | uint16 |
| eye_scan_rd_en | 0x3E | 0x83E | 2 | uint16 |
| eye_scan_wr_en | 0x40 | 0x840 | 2 | uint16 |
| eye_scan_prbs_rd_en | 0x42 | 0x842 | 2 | uint16 |
| eye_scan_prbs_wr_en | 0x44 | 0x844 | 2 | uint16 |
| ca_odt | 0x46 | 0x846 | 2 | uint16 |
| init_zq_calibration | 0x4A | 0x84A | 2 | uint16 |
| temp_sensing | 0x4C | 0x84C | 2 | uint16 |
| zq_calibration | 0x4E | 0x84E | 2 | uint16 |
| periodic_training | 0x50 | 0x850 | 2 | uint16 |
| periodic_training_period | 0x52 | 0x852 | 2 | uint16 |
| regional_clock_gating | 0x58 | 0x858 | 2 | uint16 |
| phy_clock_gating | 0x5A | 0x85A | 2 | uint16 |
| dram_clock_gating | 0x5C | 0x85C | 2 | uint16 |
| command_bus_training | 0x66 | 0x866 | 2 | uint16 |
| ca_vref_training | 0x68 | 0x868 | 2 | uint16 |
| prbs_training | 0x6A | 0x86A | 2 | uint16 |
| reboot_with_training | 0x6C | 0x86C | 2 | uint16 |
| dfs_training | 0x6E | 0x86E | 2 | uint16 |
| phy_vref_trn_mode | 0x72 | 0x872 | 2 | uint16 |
| phy_duty_trn_mode | 0x74 | 0x874 | 2 | uint16 |
| dram_vref_trn_mode | 0x76 | 0x876 | 2 | uint16 |
| dram_duty_trn_mode | 0x78 | 0x878 | 2 | uint16 |
| zq_calibration_period | 0xE4 | 0x8E4 | 4 | uint32 |
| temp_sensing_period | 0xEC | 0x8EC | 4 | uint32 |
| t_refipb | 0xF0 | 0x8F0 | 4 | uint32 |
| t_refiab | 0xF4 | 0x8F4 | 4 | uint32 |
| t_zqcal | 0xF8 | 0x8F8 | 4 | uint32 |
| mrr_byte_lane | 0x100 | 0x900 | 4 | uint32 |

#### LPDDR5 Offset Shift

All struct offsets after lp5_mr* and zq_bg_mode shifted by +0x0C (12 bytes):
- e.g., density: 0x1C → 0x28

### 3. Remove Hardcoded Defaults

Replace all hardcoded values in result dict with orbit_data.get() calls.

### 4. Add LPDDR5 Offset Handling

Apply +0x0C shift to struct offsets for LPDDR5.

---

## Test Cases

### test_binary_parse.py

| # | Test Function | Description |
|---|---------------|-------------|
| 1 | test_lpddr4_dual_all_fields_parsed | Verify all ~50 fields parsed from LPDDR4 dual reference binary |
| 2 | test_lpddr4_single_all_fields_parsed | Verify all ~50 fields parsed from LPDDR4 single reference binary |
| 3 | test_lpddr5_dual_all_fields_parsed | Verify all ~50 fields parsed from LPDDR5 dual reference binary |
| 4 | test_lpddr5_single_all_fields_parsed | Verify all ~50 fields parsed from LPDDR5 single reference binary |
| 5 | test_lecc_parsing | Verify LECC flags at correct offsets (0x11F, 0x120) |
| 6 | test_no_hardcoded_defaults | Verify no hardcoded values in parsed result |
| 7 | test_orbit_config_field_values | Verify field values match binary (e.g., rfm_en=1) |
| 8 | test_timing_features_from_binary | Verify write_odt/read_dbi/write_dbi parsed from binary |

---

## Files to Modify

1. **gui.py** - Fix binary parsing logic
   - Fix LECC offsets (lines 464-480)
   - Expand fields_to_read from 11 to 48+ fields (lines 546-558)
   - Remove hardcoded defaults in result dict (lines 505-602)
   - Add LPDDR5 offset handling

2. **test_binary_parse.py** (new) - Add comprehensive test cases

---

## Expected Outcome

After fix, all orbit config parameters should be parsed from binary, with no hardcoded default values.
