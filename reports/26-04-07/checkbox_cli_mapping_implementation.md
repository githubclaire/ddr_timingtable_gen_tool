# Checkbox CLI Mapping Implementation Report

## Summary

This report documents the implementation of the checkbox CLI mapping plan from `./plan/checkbox_cli_mapping_plan.md`.

## Implementation Results

### Phase 1: Add CLI Mappings

**1a. Added 17 CLI arguments to gen_timing_params**
- File: `gen_timing_params` lines 711-729
- Added new orbit arguments:
  - Training enable: eye-scan-rd-en, eye-scan-wr-en, eye-scan-prbs-rd-en, eye-scan-prbs-wr-en
  - Training modes: phy-vref-trn-mode, phy-duty-trn-mode, dram-vref-trn-mode, dram-duty-trn-mode
  - Additional: command-bus-training, ca-vref-training, prbs-training, reboot-with-training
  - ZQ/Training: init-zq-calibration, zq-calibration, dfs-training, phy-clock-gating
  - Numeric: phy-idle-cnt-th
  - JSON override: orbit-config-json

**1b. Added field_map entries to gen_timing_params**
- File: `gen_timing_params` lines 891-918
- Added mapping from CLI arg names to orbit_config field names

**1c. Added mapping blocks in gui.py**
- File: `gui.py` lines 627-665
- Added is_checked() mappings for all 16 checkboxes + 1 numeric param
- Also added JSON override generation code

### Phase 2: Enable JSON Override

**2a. gui.py generates orbit_config_override.json**
- File: `gui.py` lines 704-746
- Generates JSON with all orbit config params before calling CLI

**2b. gen_timing_params passes --orbit-config-json**
- Already supported in existing code (line 970-974)

**2c. ddr_config_init.py reads JSON**
- Already supported in existing code (reads json_path and applies overrides)

### Phase 3: Create Tests

**3a. test_checkbox_flow.py - Checkbox-only test**
- 28 checkboxes × 2 values = 56 test iterations
- Tests traverse ALL possible values (0 and 1) for each checkbox
- **Result: 56 passed, 0 failed**

**3b. test_random_value_flow.py - Comprehensive test**
- Part A: Checkboxes - 54 test iterations (27 checkboxes × 2 values)
- Part B: Numeric fields - 33 test iterations (7 fields × 5-10 values)
- Part C: Dropdowns - 6 test iterations (2 fields × all options)
- **Result: All tests PASS**

### Phase 4: Verify

**Test Results:**
- test_binary_parse.py: 14 passed, 0 failed
- test_checkbox_flow.py: 56 passed, 0 failed
- test_random_value_flow.py: All PASS

### Additional Fix: gui.py parsing offsets

Fixed incorrect offsets for training mode fields in gui.py:
- LPDDR4 section: phy_vref_trn_mode at 0x70 (was 0x76)
- LPDDR5 section: phy_vref_trn_mode at 0x76 (was 0x72)

## Files Modified

1. **gen_timing_params** - Added 17 CLI args + field_map entries
2. **gui.py** - Added 17 checkbox/numeric mappings + JSON generation + fixed offsets
3. **test_checkbox_flow.py** - New file
4. **test_random_value_flow.py** - New file

## Test Summary

| Test | Passed | Failed |
|------|--------|--------|
| test_binary_parse.py | 14 | 0 |
| test_checkbox_flow.py | 56 | 0 |
| test_random_value_flow.py | 93 | 0 |

## Remaining Issues

None - all tests pass.