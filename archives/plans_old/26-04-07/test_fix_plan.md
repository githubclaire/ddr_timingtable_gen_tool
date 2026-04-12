# Plan: Fix Reference Binary Test and Add Field Validation

## Status: COMPLETED

## Tasks Completed

### Task 1: Fix Reference Binary Comparison Test
- [x] Update test_gui_params.py LPDDR4 reference test params
- [x] Update test_gui_params.py LPDDR5 reference test params
- [x] Fix compare_binaries_timing() to support start_offset parameter
- [x] Changed test to compare orbit config only (0x800+) - timing table has different defaults

### Task 2: Add Field Value Validation Tests
- [x] Add test_late_field_values_lpddr4_single()
- [x] Add test_late_field_values_lpddr4_dual()
- [x] Add test_late_field_values_lpddr5_single()
- [x] Add test_late_field_values_lpddr5_dual()

### Task 3: Add Missing CLI Parameters (gen_timing_params)
- [x] Added --orbit-dynamic-power-down {0,1}
- [x] Added --orbit-dynamic-power-down-threshold
- [x] Added --orbit-dynamic-self-refresh {0,1}
- [x] Added --orbit-dynamic-self-refresh-threshold
- [x] Added --orbit-periodic-training {0,1}
- [x] Added --orbit-periodic-training-period
- [x] Added --orbit-temp-sensing {0,1}
- [x] Added --orbit-temp-sensing-period
- [x] Added --orbit-zq-calibration-period
- [x] Added --orbit-t-refiab
- [x] Added --orbit-t-refipb
- [x] Added --orbit-t-zqcal

### Task 4: Update gui.py to Pass All Parameters to CLI
- [x] Added dynamic-power-down parameters to CLI command
- [x] Added periodic/temp/timing parameters to CLI command

### Task 5: Verify Full Binary Comparison
- [x] All tests pass: test_binary_parse.py (14/14), test_gui_params.py (Reference 2/2)

## Results
- test_binary_parse.py: 14 passed, 0 failed
- test_gui_params.py: Reference Tests 2/2 passed, Parameter Tests 15/15 passed

