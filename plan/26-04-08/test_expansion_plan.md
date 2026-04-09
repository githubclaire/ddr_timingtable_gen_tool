# Test Expansion Plan - 2026-04-08

## 1. Current Test Scripts Analysis

### test_random_value_flow.py Status

| Test Type | Configs Tested | Status |
|-----------|---------------|--------|
| Checkboxes (27 fields) | 4 configs (LP4/5 Single/Dual) | ✓ Complete |
| Numeric (9 fields) | 1 config (LP4 Single only) | ✗ Incomplete |
| Dropdowns (2 fields) | 1 config (LP4 Single only) | ✗ Incomplete |

### test_gui_checkbox_integration.py Status

| Test | Configs Tested | Status |
|------|---------------|--------|
| A1-A6 | LP4 Single only (mostly) | ✗ Incomplete |
| B1-B3 | LP4 Single only | ✗ Incomplete |

---

## 2. All Numeric Fields in test_random_value_flow.py

### Currently Tested (9 fields):
- zq_calibration_period
- periodic_training_period
- temp_sensing_period
- t_refiab
- t_refipb
- t_zqcal
- phy_idle_cnt_th
- dynamic_power_down_threshold
- dynamic_self_refresh_threshold

### Missing (14 fields):
- density, num_rank, ctrl_dq_width, dq_width
- cpipe_depth, dpipe_depth, phy_freq_ratio, omc_freq_ratio
- density_code, rclk_t_ck, boot_t_ck, dram_t_ck
- link_err_cnt_th, mrr_byte_lane

---

## 3. Dropdown Fields Analysis

### GUI Dropdowns (6 total):
| # | Field | Test Status |
|---|-------|-------------|
| 1 | dram-type | Input only (not from binary) |
| 2 | dq-width | ✓ Tested |
| 3 | orbit-config-density (density) | ✗ Missing |
| 4 | orbit-byte-mode | ✗ Missing |
| 5 | orbit-mixed | ✗ Missing |
| 6 | orbit-num-rank | ✓ Tested |

---

## 4. Non-Parseable Fields with gen_timing_params Code References

### LP4-Specific Params:
| # | Param | gen_timing_params Line | Default | Not in Binary |
|---|-------|----------------------|---------|----------------|
| 1 | variable-trrd | 664 | flag | Yes |
| 2 | txsr-as-1st-ed | 666 | flag | Yes |
| 3 | wdqs-ctrl-mode | 665 | 0 | Yes |
| 4 | rpste-upto | 667 | 0 | Yes |
| 5 | wpste-upto | 668 | 0 | Yes |

### LP5-Specific Params:
| # | Param | gen_timing_params Line | Default | Not in Binary |
|---|-------|----------------------|---------|----------------|
| 6 | enhanced-nt-odt | 672 | flag | Yes |
| 7 | nt-odt-upto | 671 | 0 | Yes |
| 8 | bg-mode-upto | 673 | 625 | Yes |
| 9 | wck-always-on-from | 674 | 1000000 | Yes |
| 10 | wck-always-on-upto | 675 | 1000000 | Yes |
| 11 | wck-1to4-upto | 676 | 625 | Yes |
| 12 | wck-hf-upto | 677 | 624 | Yes |
| 13 | wck-pst1-upto | 678 | 0 | Yes |
| 14 | wck-pst2-upto | 679 | 0 | Yes |
| 15 | rdqs-pst1-upto | 680 | 0 | Yes |
| 16 | rdqs-pst2-upto | 681 | 0 | Yes |

### Common Params:
| # | Param | gen_timing_params Line | Default | Not in Binary |
|---|-------|----------------------|---------|----------------|
| 17 | wire-length | 643 | 0 | Yes |

### Detection-Only:
| # | Param | Description |
|---|-------|-------------|
| 18 | dram_type | Derived from file size, not stored in binary |

---

## 5. Special Case: dram_t_ck

### Finding: dram_t_ck IS in Orbit Config BUT NOT PARSED

**dram_t_ck exists in orbit config struct**:
| DRAM Type | Offset | Exists in Struct |
|-----------|--------|------------------|
| LP4 | 0x88 | ✓ YES |
| LP5 | 0x90 | ✓ YES |

**Current GUI behavior** (gui.py line 384):
```python
'dram_tck': periods[0] if periods else 471,
```

**Problem**: The GUI does NOT read `orbit_data['dram_t_ck']` from the orbit config struct. Instead, it **derives** dram_tck from the timing table's periods array (timing periods, not orbit config).

**Root cause**: The `dram_t_ck` field in orbit config is NOT being parsed by the GUI - it should read from orbit config offset 0x88 (LP4) / 0x90 (LP5) but instead derives from timing periods.

**Impact**: When loading binary, the displayed dram-tck value comes from timing table periods, not from the actual orbit config value stored at offset 0x88/0x90.

---

## 6. Display Test Coverage Analysis

### test_gui_checkbox_integration.py - Config Usage:
| Test | Current Configs | Display Verified? |
|------|-----------------|-------------------|
| A1 | LP4 Single | Yes (parsing) |
| A2 | LP4 Single | Yes (parsing) |
| A3 | LP4 Single | Yes (parsing) |
| A4 | 4 configs | Yes (parsing) |
| A5 | LP4 Single | Yes (parsing) |
| A6 | LP4 Single | Yes (parsing) |
| B1 | LP4 Single | Limited |
| B2 | LP2 configs (error: should be 4) | No |
| B3 | LP4 Single | Yes |

**Issues**:
1. Most tests only use LP4 Single config
2. Display tests (B1-B3) don't verify all 27 checkbox fields + all numeric fields across 4 configs
3. No verification that orbit config fields (byte_mode, mixed, density) work for all 4 configs

### Missing Display Tests:
- Verify all 27 checkbox fields display correctly for all 4 configs
- Verify all numeric fields (23 total) display correctly for all 4 configs
- Verify orbit config fields (byte_mode, mixed, density) for all 4 configs

---

## 7. Complete Non-Parseable Fields List (18 fields)

| # | Field Name | HTML Name | Category | gen_timing_params Line |
|---|------------|-----------|----------|----------------------|
| 1 | variable-trrd | variable-trrd | LP4 Specific | 664 |
| 2 | txsr-as-1st-ed | txsr-as-1st-ed | LP4 Specific | 666 |
| 3 | enhanced-nt-odt | enhanced-nt-odt | LP5 Specific | 672 |
| 4 | wire-length | wire-length | Common | 643 |
| 5 | wdqs-ctrl-mode | wdqs-ctrl-mode | LP4 Timing | 665 |
| 6 | rpste-upto | rpste-upto | LP4 Timing | 667 |
| 7 | wpste-upto | wpste-upto | LP4 Timing | 668 |
| 8 | nt-odt-upto | nt-odt-upto | LP5 Timing | 671 |
| 9 | bg-mode-upto | bg-mode-upto | LP5 Timing | 673 |
| 10 | wck-always-on-from | wck-always-on-from | LP5 Timing | 674 |
| 11 | wck-always-on-upto | wck-always-on-upto | LP5 Timing | 675 |
| 12 | wck-1to4-upto | wck-1to4-upto | LP5 Timing | 676 |
| 13 | wck-hf-upto | wck-hf-upto | LP5 Timing | 677 |
| 14 | wck-pst1-upto | wck-pst1-upto | LP5 Timing | 678 |
| 15 | wck-pst2-upto | wck-pst2-upto | LP5 Timing | 679 |
| 16 | rdqs-pst1-upto | rdqs-pst1-upto | LP5 Timing | 680 |
| 17 | rdqs-pst2-upto | rdqs-pst2-upto | LP5 Timing | 681 |
| 18 | dram_type | (detection) | Derived | N/A |

---

## 8. Test Expansion Requirements - 4 DDR Configs

| Config | DRAM Type | Channels |
|--------|-----------|----------|
| LP4 Single | lpddr4 | single |
| LP4 Dual | lpddr4 | dual |
| LP5 Single | lpddr5 | single |
| LP5 Dual | lpddr5 | dual |

### test_random_value_flow.py:
| Test Type | Current | Required |
|-----------|---------|----------|
| Checkboxes | 4 configs | ✓ Already complete |
| Numeric (9 fields) | 1 config | Expand to 4 configs |
| Numeric (14 missing) | 0 | Add all + 4 configs |
| Dropdowns | 1 config | Expand to 4 configs |

### test_gui_checkbox_integration.py:
| Test | Current | Required |
|------|---------|----------|
| A1-A6 | LP4 Single (mostly) | Expand to 4 configs |
| B1-B3 | LP4 Single | Expand to 4 configs + full display verification |

---

## 9. Implementation Plan

### Phase 1: test_random_value_flow.py
1. Expand `test_numeric_fields()` to 4 configs
2. Expand `test_dropdowns()` to 4 configs
3. Add 14 missing numeric fields
4. Fix dram_t_ck: Add to numeric tests (should parse from orbit config)

### Phase 2: test_gui_checkbox_integration.py
1. Expand all tests (A1-A6, B1-B3) to 4 configs
2. Add full display verification for all fields across all configs
3. Add verification for orbit config fields (byte_mode, mixed, density)

### Phase 3: gui.py
1. Fix dram_t_ck parsing: Read from orbit config at 0x88 (LP4) / 0x90 (LP5)
2. Add 17 non-parseable fields (excluding dram_type) warning list to result data
3. Note: dram_type is derived, not stored - no warning needed

---

## 10. Test Matrix - Numeric Fields Across 4 Configs

| Field | LP4 Single | LP4 Dual | LP5 Single | LP5 Dual |
|-------|------------|----------|------------|----------|
| zq_calibration_period | ✓ | Add | Add | Add |
| periodic_training_period | ✓ | Add | Add | Add |
| temp_sensing_period | ✓ | Add | Add | Add |
| t_refiab | ✓ | Add | Add | Add |
| t_refipb | ✓ | Add | Add | Add |
| t_zqcal | ✓ | Add | Add | Add |
| phy_idle_cnt_th | ✓ | Add | Add | Add |
| dynamic_power_down_threshold | ✓ | Add | Add | Add |
| dynamic_self_refresh_threshold | ✓ | Add | Add | Add |
| dram_t_ck | ✗ | Add | Add | Add | (NEW - fix parsing)
| density | ✗ | Add | Add | Add |
| num_rank | ✗ | Add | Add | Add |
| ctrl_dq_width | ✗ | Add | Add | Add |
| dq_width | ✗ | Add | Add | Add |
| cpipe_depth | ✗ | Add | Add | Add |
| dpipe_depth | ✗ | Add | Add | Add |
| phy_freq_ratio | ✗ | Add | Add | Add |
| omc_freq_ratio | ✗ | Add | Add | Add |
| density_code | ✗ | Add | Add | Add |
| rclk_t_ck | ✗ | Add | Add | Add |
| boot_t_ck | ✗ | Add | Add | Add |
| link_err_cnt_th | ✗ | Add | Add | Add |
| mrr_byte_lane | ✗ | Add | Add | Add |

---

## 11. Summary

| Category | Count | Status |
|-----------|-------|--------|
| Non-parseable fields | 17 | Need warning display (dram_type excluded) |
| dram_t_ck parsing | 1 | Need to FIX (in struct but not parsed) |
| Checkbox fields | 27 | ✓ Tested across 4 configs |
| Numeric fields in test | 9 | Need 4 config expansion |
| Missing numeric fields | 14 | Need to add |
| Display tests | - | Need full verification across 4 configs |