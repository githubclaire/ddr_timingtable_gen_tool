# Detailed Test Plan: GUI Checkbox Integration Test

## Overview

Test the full GUI workflow to verify checkbox values are correctly:
1. Generated in binary (via GUI generate)
2. Parsed from binary (via GUI load)
3. Displayed correctly in GUI

---

## Test Workflow (For Each Test)

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Test Execution Flow                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Prepare Input                                          │
│  - Set checkbox values in test params dict                       │
│  - Format: {'eye-scan-rd-en': '1', 'zq-calibration': '0', ...}  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Generate Binary                                        │
│  - Call gui.py generate logic (simulate /generate endpoint)      │
│  - Creates orbit_config_override.json with checkbox values        │
│  - Calls gen_timing_params with --orbit-config-json              │
│  - ddr_config_init.py reads JSON, writes binary                  │
│  - Output: ddr_timing_table.bin with correct checkbox values     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Load/Analyze Binary                                    │
│  - Call gui.analyze_binary_file('ddr_timing_table.bin')         │
│  - Reads binary at orbit offset (0x800)                          │
│  - Parses fields at correct struct offsets                       │
│  - Output: dict with parsed checkbox values                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Verify Parsed Values                                    │
│  - Compare parsed[checkbox] == expected[checkbox]                │
│  - For each of 28 checkboxes                                     │
│  - PASS if all match, FAIL if any mismatch                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Verify Display Values                                   │
│  - Compare display_value (from result['data']['orbit'])          │
│    with parsed_value                                            │
│  - PASS if all match                                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 6: Report Result                                          │
│  - Print PASS/FAIL for each checkbox                             │
│  - Summary: X passed, Y failed                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Binary File Handling

**Option A: Separate files per test case** (Recommended)

| Test Case | Binary File |
|-----------|-------------|
| test_ref_bin_all_unchecked | test_ref_unchecked.bin |
| test_all_checked | test_all_checked.bin |
| test_mixed_checkboxes | test_mixed.bin |
| test_dram_configs | test_lp4_single.bin, test_lp4_dual.bin, etc. |

**Pros:**
- Easier to debug failures (inspect specific binary)
- Can compare binaries after test
- If one test corrupts file, others still work
- Can manually inspect any binary

---

## Test Cases Detail

### Part A: Generate → Parse Flow (Forward)

#### Test 1: Reference Binary (All Unchecked)
- Load ref binary with all checkboxes = 0
- Verify parsed = 0 for all 28 checkboxes

#### Test 2: All Checked
- Generate binary with all 28 checkboxes = 1
- Verify parsed = 1 for all

#### Test 3: Mixed Values (Alternating)
- Generate with alternating 0/1 pattern
- Verify each matches

#### Test 4: Toggle Single Checkbox (Edge Case)
- For each of 28 checkboxes:
  - Set ONLY that checkbox to 1, others to 0
  - Generate binary
  - Verify that checkbox = 1, others = 0
- **Total: 28 test iterations**

#### Test 5: Toggle Pair Checkboxes (Edge Case)
- Test pairs of checkboxes together
- Verify both values correct
- **Total: ~14 test iterations**

#### Test 6: All DRAM Configs (Edge Case)
- Test 4 configs: LP4 Single, LP4 Dual, LP5 Single, LP5 Dual
- All checkboxes = 1
- Verify parsed = 1 for all

#### Test 7: Different Densities (Edge Case)
- Test with different density values: 4, 8, 16
- Verify checkboxes parse correctly regardless of density

#### Test 8: With Timing Params (Edge Case)
- Generate binary with checkboxes + timing params set
- Verify checkboxes still parse correctly

---

### Part B: Load Binary → Display Flow (Reverse)

#### Test 1: Load ref bin (all 0), verify display
- Load binary with all checkboxes = 0
- Verify display values = 0 for all 28 checkboxes

#### Test 2: Load all checked bin, verify display
- Load binary with all checkboxes = 1
- Verify display values = 1 for all

#### Test 3: Load mixed bin, verify display matches
- Load binary with mixed values
- Verify display values match parsed values

#### Test 4: Load each single-checkbox bin, verify display
- Load 28 binaries (each with single checkbox = 1)
- Verify display shows that checkbox checked

#### Test 5: Load pair-checkbox bins, verify display
- Load binaries with pair checkboxes
- Verify display shows both checked

#### Test 6: Load 4 DRAM configs, verify display
- Load LP4 Single, LP4 Dual, LP5 Single, LP5 Dual
- Verify display values match for all configs

#### Test 7: Load different densities, verify display
- Load binaries with different densities
- Verify display values correct regardless of density

#### Test 8: Load with timing params, verify display
- Load binary with checkboxes + timing params
- Verify display checkbox values correct

---

## Checkbox List (28 fields)

```
eye-scan-rd-en, eye-scan-wr-en, eye-scan-prbs-rd-en, eye-scan-prbs-wr-en,
phy-vref-trn-mode, phy-duty-trn-mode, dram-vref-trn-mode, dram-duty-trn-mode,
command-bus-training, ca-vref-training, prbs-training, reboot-with-training,
init-zq-calibration, zq-calibration, dfs-training, phy-clock-gating,
two-channel, orbit-rank-interleaving, orbit-reboot-with-mrw,
orbit-rfm-en, orbit-dsm-en, orbit-ca-odt,
phy-low-power, dynamic-power-down, dynamic-self-refresh,
periodic-training, temp-sensing,
regional-clock-gating, dram-clock-gating
```

---

## Checkbox Mapping (GUI → Struct Field)

| GUI Param (hyphen) | Struct Field (underscore) |
|-------------------|---------------------------|
| eye-scan-rd-en | eye_scan_rd_en |
| eye-scan-wr-en | eye_scan_wr_en |
| eye-scan-prbs-rd-en | eye_scan_prbs_rd_en |
| eye-scan-prbs-wr-en | eye_scan_prbs_wr_en |
| phy-vref-trn-mode | phy_vref_trn_mode |
| phy-duty-trn-mode | phy_duty_trn_mode |
| dram-vref-trn-mode | dram_vref_trn_mode |
| dram-duty-trn-mode | dram_duty_trn_mode |
| command-bus-training | command_bus_training |
| ca-vref-training | ca_vref_training |
| prbs-training | prbs_training |
| reboot-with-training | reboot_with_training |
| init-zq-calibration | init_zq_calibration |
| zq-calibration | zq_calibration |
| dfs-training | dfs_training |
| phy-clock-gating | phy_clock_gating |
| two-channel | (handled separately) |
| orbit-rank-interleaving | rank_interleaving |
| orbit-reboot-with-mrw | reboot_with_mrw |
| orbit-rfm-en | rfm_en |
| orbit-dsm-en | dsm_en |
| orbit-ca-odt | ca_odt |
| phy-low-power | phy_low_power |
| dynamic-power-down | dynamic_power_down |
| dynamic-self-refresh | dynamic_self_refresh |
| periodic-training | periodic_training |
| temp-sensing | temp_sensing |
| regional-clock-gating | regional_clock_gating |
| dram-clock-gating | dram_clock_gating |

---

## Additional Checkboxes (LPDDR4/LPDDR5 Specific + Dynamic)

### LPDDR4 Specific (2 fields)
| GUI Param | CLI Arg | Description |
|-----------|---------|-------------|
| variable-trrd | `--variable-trrd` | Use tRRD of 10 ns for LPDDR4-4267 |
| txsr-as-1st-ed | `--txsr-as-1st-ed` | SRX to ACT/REF commands constraints |

### LPDDR5 Specific (1 field)
| GUI Param | CLI Arg | Description |
|-----------|---------|-------------|
| enhanced-nt-odt | `--enhanced-nt-odt` | Enhanced NT-ODT support |

### Dynamic Power with Thresholds (2 + 2 numeric)
| Checkbox | Threshold Numeric | Test Values |
|----------|-------------------|--------------|
| dynamic_power_down | dynamic_power_down_threshold | 0, 10000, 50000, 100000, 500000 |
| dynamic_self_refresh | dynamic_self_refresh_threshold | 0, 10000, 50000, 100000, 500000 |

### Checkbox + Period Together (3 + 3 numeric)
| Checkbox | Period Numeric | Test Values |
|----------|----------------|--------------|
| zq_calibration | zq_calibration_period | 10000, 20000, 30000, 40000, 48000, 60000 |
| periodic_training | periodic_training_period | 5000, 10000, 20000, 24000, 40000 |
| temp_sensing | temp_sensing_period | 5000, 10000, 20000, 32000, 40000 |

---

## Updated Test Cases (Part A - Forward Flow)

#### Test 9: LPDDR4 Specific Checkboxes
- Generate for LPDDR4 with variable-trrd=1, txsr-as-1st-ed=1
- Verify both parse correctly

#### Test 10: LPDDR5 Specific Checkboxes
- Generate for LPDDR5 with enhanced-nt-odt=1
- Verify parses correctly

#### Test 11: Dynamic Power with Thresholds
- For each combination:
  - dynamic_power_down=1 + threshold=N (5 values)
  - dynamic_self_refresh=1 + threshold=N (5 values)
- Verify both checkbox AND threshold parse correctly
- **Total: 10 test iterations**

#### Test 12: Checkbox + Period Together
- For each combination:
  - zq_calibration=1 + period=N (6 values)
  - periodic_training=1 + period=N (5 values)
  - temp_sensing=1 + period=N (5 values)
- Verify both checkbox AND period parse correctly
- **Total: 16 test iterations**

---

## Updated Checkbox List (32 fields)

```
# LPDDR4 specific (2)
variable-trrd, txsr-as-1st-ed

# LPDDR5 specific (1)
enhanced-nt-odt

# Training (12)
eye-scan-rd-en, eye-scan-wr-en, eye-scan-prbs-rd-en, eye-scan-prbs-wr-en,
phy-vref-trn-mode, phy-duty-trn-mode, dram-vref-trn-mode, dram-duty-trn-mode,
command-bus-training, ca-vref-training, prbs-training, reboot-with-training

# ZQ/Training (4)
init-zq-calibration, zq-calibration, dfs-training, phy-clock-gating

# Orbit config (6)
two-channel, orbit-rank-interleaving, orbit-reboot-with-mrw,
orbit-rfm-en, orbit-dsm-en, orbit-ca-odt

# Dynamic power (2 + thresholds)
dynamic-power-down, dynamic-self-refresh

# Period features (3 + periods)
periodic-training, temp-sensing

# Clock gating (3)
phy-low-power, regional-clock-gating, dram-clock-gating
```

---

## Updated Part B - Reverse Flow (Load → Display)

Add Tests 9-12 for reverse flow (verify display matches parse):
- Test 9: Verify display for LPDDR4 specific checkboxes
- Test 10: Verify display for LPDDR5 specific checkboxes
- Test 11: Verify display for dynamic power + thresholds
- Test 12: Verify display for checkbox + period together

---

## Summary Table (Updated)

| Flow | Tests | Iterations |
|------|-------|------------|
| Forward (Generate→Parse) | 12 | ~460 |
| Reverse (Load→Display) | 12 | ~460 |
| Comprehensive All-Params | 1 | ~500 |
| **Total** | **25** | **~1400** |

---

## test_random_value_flow.py Updates

### Current Coverage
- Part A: Checkboxes traverse (0,1) - 32 fields
- Part B: Numeric traverse (5-10 values each) - ~25 fields
- Part C: Dropdowns traverse all - ~5 fields

### Add New Coverage
1. **Checkbox + Period Together** (like Test 11 above)
2. **LPDDR4 specific** (variable-trrd, txsr-as-1st-ed)
3. **LPDDR5 specific** (enhanced-nt-odt)
4. **All DRAM configs** (LP4 single/dual, LP5 single/dual)
5. **Verify display values match parse** (reverse flow)
6. **Dynamic thresholds** (checkbox + threshold numeric)

### Comprehensive All-Params Display Test

#### All Display Fields to Traverse (~51 fields)

| Category | # Fields | Fields |
|----------|----------|--------|
| **Basic Info** | 5 | dram_type, density, num_rank, dq_width, two_channel |
| **Pipe Config** | 4 | phy_freq_ratio, omc_freq_ratio, cpipe_depth, dpipe_depth |
| **Mode Control** | 4 | reboot_with_mrw, rfm_en, dsm_en, ca_odt |
| **Training** | 12 | eye_scan_rd_en, eye_scan_wr_en, eye_scan_prbs_rd_en, eye_scan_prbs_wr_en, phy_vref_trn_mode, phy_duty_trn_mode, dram_vref_trn_mode, dram_duty_trn_mode, command_bus_training, ca_vref_training, prbs_training, reboot_with_training |
| **ZQ/Training** | 4 | init_zq_calibration, zq_calibration, dfs_training, phy_clock_gating |
| **Clock Gating** | 3 | regional_clock_gating, dram_clock_gating, phy_clock_gating |
| **Dynamic Power** | 4 | phy_low_power, dynamic_power_down, dynamic_self_refresh, phy_idle_cnt_th |
| **Dynamic Thresholds** | 2 | dynamic_power_down_threshold, dynamic_self_refresh_threshold |
| **Timing Features** | 3 | temp_sensing, zq_calibration, periodic_training |
| **Timing Periods** | 3 | temp_sensing_period, zq_calibration_period, periodic_training_period |
| **Timing Values** | 3 | t_refiab, t_refipb, t_zqcal |
| **DFS Timing** | 3 | dfs_lvl_t_ck_0, dfs_lvl_t_ck_1, dfs_lvl_t_ck_2 |
| **MRR** | 1 | mrr_byte_lane |

**Total: ~51 display fields**

#### test_random_value_flow.py - Comprehensive Coverage

| Test Category | Fields | Test Values | Iterations |
|---------------|--------|-------------|-------------|
| Checkboxes | 32 | 0, 1 | 64 |
| Numeric timing | ~15 | 5-10 each | ~100 |
| Numeric periods/thresholds | ~8 | 5-10 each | ~60 |
| Dropdowns | ~5 | all options | ~20 |
| LPDDR4/LPDDR5 specific | 3 | 0, 1 | 6 |
| DRAM configs | 4 | - | all above × 4 |
| Display verification | all above | - | all above |
| **Total** | **~51** | | **~500+** |

### Updated test_random_value_flow.py Summary

| Test Category | Tests | Iterations |
|---------------|-------|------------|
| Existing (checkboxes, numeric, dropdowns) | 3 | ~100 |
| New (checkbox+period, LP4/LP5 specific, configs, display) | 5 | ~200 |
| Comprehensive all-params | 1 | ~500 |
| **Total** | **9** | **~800** |

---

## test_random_value_flow.py Test Workflow

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              test_random_value_flow.py Workflow                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Generate Test Params                                  │
│  - Select field category (checkboxes/numeric/dropdowns)         │
│  - Generate test values based on category:                       │
│    * Checkboxes: 0 or 1                                         │
│    * Numeric: 5-10 random values in valid range                 │
│    * Dropdowns: all options                                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Generate Binary                                        │
│  - Create ctypes struct (create_orbit_config)                   │
│  - Set all test params as struct fields                          │
│  - Write struct to binary at offset 0x800                        │
│  - Output: test_random_flow.bin                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Parse Binary                                          │
│  - Call gui.analyze_binary_file('test_random_flow.bin')        │
│  - Extract all fields from result['data']['orbit']               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Verify Parsed Values                                   │
│  - Compare: parsed[field] == expected[field]                    │
│  - For each field in test category                               │
│  - Record PASS/FAIL for each field                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Verify Display Values (Reverse Flow)                   │
│  - Compare: display_value == parsed_value                        │
│  - For each field                                                │
│  - PASS if all match                                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 6: Report Results                                          │
│  - Print: category, passed, failed                               │
│  - Continue to next category                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed Test Functions

#### Function 1: test_checkboxes_traverse()
```
For each of 32 checkboxes:
  For each value in [0, 1]:
    1. Create orbit_config struct
    2. Set checkbox = value, others = 0
    3. Write binary
    4. Parse binary
    5. Verify: parsed[checkbox] == value
    6. Verify display: display == parsed
Result: 64 iterations + 64 display verifications
```

#### Function 2: test_numeric_traverse()
```
For each numeric field (~25 fields):
  For each test value in valid range (5-10 values):
    1. Create orbit_config struct
    2. Set field = test_value, others = defaults
    3. Write binary
    4. Parse binary
    5. Verify: parsed[field] == test_value
    6. Verify display: display == parsed
Result: ~200 iterations + ~200 display verifications
```

#### Function 3: test_dropdowns_traverse()
```
For each dropdown field (~5 fields):
  For each option in dropdown:
    1. Create orbit_config struct
    2. Set dropdown = option
    3. Write binary
    4. Parse binary
    5. Verify: parsed[dropdown] == option
    6. Verify display: display == parsed
Result: ~20 iterations + ~20 display verifications
```

#### Function 4: test_lp4_lp5_specific()
```
LPDDR4 specific: variable-trrd, txsr-as-1st-ed
  - Generate with both = 1 for LPDDR4
  - Verify parsed values = 1
  
LPDDR5 specific: enhanced-nt-odt
  - Generate with = 1 for LPDDR5
  - Verify parsed value = 1
Result: 6 iterations + 6 display verifications
```

#### Function 5: test_all_dram_configs()
```
For each config: LP4 Single, LP4 Dual, LP5 Single, LP5 Dual
  1. Generate binary with all checkboxes = 1
  2. Parse binary
  3. Verify all 32 checkboxes = 1
  4. Verify display matches
Result: 4 configs × 32 checkboxes = 128 iterations
```

#### Function 6: test_checkbox_period_together()
```
For each combination:
  - zq_calibration=1 + period=N (6 values)
  - periodic_training=1 + period=N (5 values)
  - temp_sensing=1 + period=N (5 values)
  1. Generate binary with checkbox + period
  2. Parse binary
  3. Verify both checkbox AND period correct
Result: 16 iterations + 16 display verifications
```

#### Function 7: test_dynamic_thresholds()
```
For each combination:
  - dynamic_power_down=1 + threshold=N (5 values)
  - dynamic_self_refresh=1 + threshold=N (5 values)
  1. Generate binary with checkbox + threshold
  2. Parse binary
  3. Verify both checkbox AND threshold correct
Result: 10 iterations + 10 display verifications
```

#### Function 8: test_all_params_display()
```
For all ~51 display fields:
  1. Generate binary with all fields set to test values
  2. Parse binary
  3. Verify each field: parsed == expected
  4. Verify display: display == parsed
  5. Test multiple DRAM configs (4)
Result: ~500+ iterations
```

#### Function 9: test_summary()
```
Print summary:
  - Total iterations by category
  - Pass/Fail count
  - List of any failures
```

### Edge Cases Covered

| Edge Case | Description |
|-----------|--------------|
| All 0 | Generate with all checkboxes = 0 |
| All 1 | Generate with all checkboxes = 1 |
| Single toggle | Only one checkbox = 1 |
| Pair toggle | Two checkboxes = 1 |
| Mixed | Alternating 0/1 pattern |
| Boundary numeric | Min/max values for numeric fields |
| LPDDR4 only | variable-trrd, txsr-as-1st-ed |
| LPDDR5 only | enhanced-nt-odt |
| All configs | LP4/5 single/dual |
| Display match | Verify display == parsed |

---

## Debugging Approach

**My approach**: Debug **one failure at a time**, but run **all tests first** to see full scope.

**Workflow**:
```
1. Run all tests
2. Report ALL failures (e.g., "5 checkboxes failed in Test 4")
3. Debug first failure:
   - Inspect binary at correct offset
   - Check ctypes struct offset
   - Compare with reference
4. Fix the issue
5. Re-run tests to verify fix
6. Repeat until all pass
```

---

## Files to Create

- **Create**: `test_gui_checkbox_integration.py` - New integration test

---

## Implementation Notes

- Use separate binary files per test case for easier debugging
- Continue and report all failures on each run
- Debug one failure at a time after seeing full failure report
- Test both forward (generate→parse) and reverse (load→display) flows
- Include all edge cases for both flows