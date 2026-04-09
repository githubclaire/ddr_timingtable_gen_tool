# Plan: Checkbox CLI Mappings and Comprehensive Testing

## Overview
Address 4 related tasks:
1. Add missing CLI mappings for checkbox params in gui.py
2. Create comprehensive test for checkbox flow  
3. Enable C code (gen_ddr_config) to use GUI-modified values via JSON override
4. Test all modified input values (random values through full pipeline)

---

## Task 1: Add Missing CLI Mappings in gui.py

### 1a. Missing Checkboxes (16 total)
| GUI Param | CLI Arg to Add |
|-----------|----------------|
| eye-scan-rd-en | --orbit-eye-scan-rd-en |
| eye-scan-wr-en | --orbit-eye-scan-wr-en |
| eye-scan-prbs-rd-en | --orbit-eye-scan-prbs-rd-en |
| eye-scan-prbs-wr-en | --orbit-eye-scan-prbs-wr-en |
| phy-vref-trn-mode | --orbit-phy-vref-trn-mode |
| phy-duty-trn-mode | --orbit-phy-duty-trn-mode |
| dram-vref-trn-mode | --orbit-dram-vref-trn-mode |
| dram-duty-trn-mode | --orbit-dram-duty-trn-mode |
| command-bus-training | --orbit-command-bus-training |
| ca-vref-training | --orbit-ca-vref-training |
| prbs-training | --orbit-prbs-training |
| reboot-with-training | --orbit-reboot-with-training |
| init-zq-calibration | --orbit-init-zq-calibration |
| zq-calibration | --orbit-zq-calibration |
| dfs-training | --orbit-dfs-training |
| phy-clock-gating | --orbit-phy-clock-gating |

### 1b. Missing Numeric Params (1 total)
| GUI Param | CLI Arg to Add |
|-----------|----------------|
| phy-idle-cnt-th | --orbit-phy-idle-cnt-th |

### Implementation Steps

**1a. gen_timing_params - Add CLI arguments**
- File: `gen_timing_params` lines 684-710
- Add 17 new arguments after existing orbit args

**1b. gen_timing_params - Add to field_map**
- File: `gen_timing_params` lines 871-894
- Add entries for each new arg

**1c. gui.py - Add mapping code**
- File: `gui.py` around lines 570-665
- Add mapping for each checkbox and numeric param

---

## Task 2: Enable C Code to Use JSON Override

### Approach: Option A (JSON Override)
gui.py generates a JSON file with all orbit config values → passes to gen_ddr_config via `--orbit-config-json` → gen_ddr_config reads JSON and uses values instead of hardcoded ddr_config.h

### Implementation Steps

**2a. gui.py - Generate JSON file**
- Create orbit_config_override.json with all orbit config params

**2b. gen_timing_params - Pass JSON to CLI**
- Add `--orbit-config-json orbit_config_override.json`

**2c. ddr_config_init.py - Read JSON and apply**
- Read JSON file and apply overrides to ctypes struct

### Validation: How to Verify C Code Binary is Correct

**Method: Compare Python vs C Generated Binaries**
1. Generate with Python + JSON → python_generated.bin
2. Generate with C + JSON → c_generated.bin  
3. Compare: `diff python_generated.bin c_generated.bin`
4. Should be identical if both read same JSON

---

## Task 3: Create Comprehensive Test - test_checkbox_flow.py

### New Test File: `test_checkbox_flow.py`

### Test Strategy: Traverse ALL Possible Values

**For Checkboxes (32 fields, 2 values each = 64 test iterations):**
- Test BOTH 0 and 1 for each checkbox
- Total: 32 checkboxes × 2 values = 64 test iterations

### Detailed Workflow

```
For each checkbox in 32 checkboxes:
  For each value in [0, 1]:
    1. Set checkbox to value in test input
    2. Generate binary with this value
    3. Parse binary using gui.analyze_binary_file()
    4. Extract parsed checkbox value
    5. Compare: parsed == input_value
    6. Report PASS/FAIL

Total: 64 test iterations (32 checkboxes × 2 values)
```

### Checkbox List (32 fields)
```
variable-trrd, txsr-as-1st-ed, enhanced-nt-odt, two-channel,
orbit-rank-interleaving, orbit-reboot-with-mrw, reboot-with-training,
eye-scan-rd-en, eye-scan-wr-en, eye-scan-prbs-rd-en, eye-scan-prbs-wr-en,
phy-vref-trn-mode, phy-duty-trn-mode, dram-vref-trn-mode, dram-duty-trn-mode,
command-bus-training, ca-vref-training, prbs-training,
regional-clock-gating, dram-clock-gating, phy-clock-gating,
phy-low-power, dynamic-power-down, dynamic-self-refresh,
orbit-rfm-en, orbit-dsm-en, orbit-ca-odt,
init-zq-calibration, zq-calibration, dfs-training,
periodic-training, temp-sensing
```

---

## Task 4: Create Random Value Flow Test - test_random_value_flow.py

### New Test File: `test_random_value_flow.py`

### Test Strategy

**For Checkboxes (32 fields):**
- Traverse ALL possible values: 0 and 1
- Already covered in Task 3

**For Numeric Fields (~25 fields):**
- Test 5-10 random values in VALID RANGE for each field
- NOT just default value
- Must test multiple different values to verify parsing works

**For Dropdowns (5 fields):**
- Traverse ALL possible values in dropdown
- Test every option in the dropdown

### Valid Ranges for Numeric Fields

| Field | Valid Range | Test Values (5-10) |
|-------|-------------|-------------------|
| write-odt-upto | 0-5000 | 100, 500, 1000, 2000, 3000, 4000 |
| read-dbi-upto | 0-15000 | 1000, 3000, 5000, 8000, 10000, 13000 |
| write-dbi-upto | 0-15000 | 1000, 3000, 5000, 8000, 10000, 13000 |
| zq-calibration-period | 1000-100000 | 10000, 20000, 30000, 40000, 48000, 60000 |
| periodic-training-period | 1000-100000 | 5000, 10000, 20000, 24000, 40000 |
| temp-sensing-period | 1000-100000 | 5000, 10000, 20000, 32000, 40000 |
| t-refiab | 1000000-10000000 | 2000000, 3000000, 3904000, 5000000 |
| t-refipb | 100000-1000000 | 200000, 300000, 488000, 600000 |
| t-zqcal | 100000-5000000 | 500000, 800000, 1000000, 2000000 |
| dfs-lvl-t-ck-0 | 300-5000 | 500, 800, 938, 1200, 1600 |
| dfs-lvl-t-ck-1 | 300-5000 | 800, 1200, 1631, 2000, 2500 |
| dfs-lvl-t-ck-2 | 300-5000 | 1000, 1500, 2000, 2500, 3000 |
| dynamic-power-down-threshold | 0-1000000 | 10000, 50000, 100000, 500000 |
| dynamic-self-refresh-threshold | 0-1000000 | 10000, 50000, 100000, 500000 |
| phy-idle-cnt-th | 0-65535 | 100, 1000, 5000, 10000, 30000 |

### Dropdown Values (Traverse All)

| Dropdown | Values |
|----------|--------|
| dq-width | 4, 8, 16, 32 |
| orbit-config-density | 2, 3, 4, 6, 8, 12, 16 (LPDDR4) / 2-32 (LPDDR5) |
| orbit-byte-mode | 0, 1 |
| orbit-num-rank | 1, 2 |
| dram-type | lpddr4, lpddr5 |

### Detailed Workflow

```
Part A: Checkbox Testing (from Task 3)
  - Traverse all: 32 checkboxes × 2 values = 64 iterations
  
Part B: Numeric Field Testing
  For each numeric field (~25 fields):
    For each test value (5-10 values per field):
      1. Set field to test value
      2. Generate binary
      3. Parse binary
      4. Compare: parsed_value == input_value
      
  Total: ~25 fields × 8 values = ~200 test iterations
  
Part C: Dropdown Field Testing
  For each dropdown field (5 fields):
    For each option in dropdown:
      1. Set dropdown to option value
      2. Generate binary
      3. Parse binary
      4. Compare: parsed_value == input_value
      
  Total: ~5 dropdowns × ~6 options = ~30 test iterations

Summary: ~64 + ~200 + ~30 = ~294 test iterations
```

### Test Functions

1. `test_checkbox_traverse_all()` - Traverse all checkbox values (0 and 1)
2. `test_numeric_traverse_values()` - 5-10 values per numeric field
3. `test_dropdown_traverse_all()` - All dropdown options
4. `test_all_fields_integration()` - Combined test with random values

---

## Implementation Order

```
Phase 1: Add CLI Mappings (17 params)
  1a. Add 17 CLI args to gen_timing_params (16 checkboxes + 1 numeric)
  1b. Add 17 field_map entries to gen_timing_params  
  1c. Add 17 mapping blocks in gui.py
  
Phase 2: Enable JSON Override for C Code
  2a. gui.py generates orbit_config_override.json
  2b. gen_timing_params passes --orbit-config-json
  2c. ddr_config_init.py reads and applies JSON overrides
  
Phase 3: Create Tests
  3a. test_checkbox_flow.py - Traverse ALL checkbox values (0 and 1) - 64 iterations
  3b. test_random_value_flow.py - 
      - Checkboxes: traverse all (0,1) - 64 iterations
      - Numeric: test 5-10 values in valid range - ~200 iterations
      - Dropdowns: traverse all options - ~30 iterations
  
Phase 4: Verify
  4a. Run all tests (~294 iterations)
  4b. Compare Python vs C generated binaries
  4c. Fix any issues
```

---

## Files to Modify

1. **gen_timing_params** - Add 17 CLI args + 17 field_map entries
2. **gui.py** - Add 17 checkbox/numeric mappings + JSON generation
3. **ddr_config_init.py** - Add JSON override handling
4. **test_checkbox_flow.py** - New file (traverse ALL checkbox values - 64 iterations)
5. **test_random_value_flow.py** - New file (traverse all checkboxes, 5-10 numeric values, all dropdowns - ~294 iterations)