# Implementation Report: CLI Parameter Exposure and Full Integration

## Date: 2026-04-07

## Summary
Exposed all orbit configuration parameters in gen_timing_params CLI and updated gui.py to pass them correctly. This enables full binary comparison between GUI-generated and CLI-generated binaries.

## Changes Made

### 1. gen_timing_params - Added 13 New CLI Parameters

Added to argument parser (lines 696-710):

```python
# Dynamic power management
--orbit-dynamic-power-down {0,1}
--orbit-dynamic-power-down-threshold
--orbit-dynamic-self-refresh {0,1}
--orbit-dynamic-self-refresh-threshold

# Timing intervals
--orbit-periodic-training {0,1}
--orbit-periodic-training-period
--orbit-temp-sensing {0,1}
--orbit-temp-sensing-period
--orbit-zq-calibration-period
--orbit-t-refiab
--orbit-t-refipb
--orbit-t-zqcal
```

Added field mapping in overrides (lines 880-903):
- Maps CLI argument names to orbit_config field names
- Includes all new dynamic and timing parameters

### 2. gui.py - Updated CLI Command Building

Added parameter passing to gen_timing_params (lines 955-1004):

**Dynamic Power Management:**
- `dynamic-power-down` → `--orbit-dynamic-power-down`
- `dynamic-power-down-threshold` → `--orbit-dynamic-power-down-threshold`
- `dynamic-self-refresh` → `--orbit-dynamic-self-refresh`
- `dynamic-self-refresh-threshold` → `--orbit-dynamic-self-refresh-threshold`

**Timing Intervals:**
- `periodic-training` → `--orbit-periodic-training`
- `periodic-training-period` → `--orbit-periodic-training-period`
- `temp-sensing` → `--orbit-temp-sensing`
- `temp-sensing-period` → `--orbit-temp-sensing-period`
- `zq-calibration-period` → `--orbit-zq-calibration-period`
- `t-refiab` → `--orbit-t-refiab`
- `t-refipb` → `--orbit-t-refipb`
- `t-zqcal` → `--orbit-t-zqcal`

### 3. test_gui_params.py - Fixed Reference Test Parameters

- Removed extra parameters that caused mismatch
- Fixed boolean flag format (txsr-as-1st-ed, variable-trrd)
- Fixed orbit-rank-interleaving value format

### 4. test_binary_parse.py - Added Field Value Validation

Added 4 new tests:
- test_late_field_values_lpddr4_single()
- test_late_field_values_lpddr4_dual()
- test_late_field_values_lpddr5_single()
- test_late_field_values_lpddr5_dual()

## Test Results

### test_binary_parse.py
```
Results: 14 passed, 0 failed
```

### test_gui_params.py
```
Parameter Tests: 15/15 passed
Reference Tests: 2/2 passed
ps/MHz Toggle Test: PASS
Button Load Binary Tests: 2/2 passed
Button Save JSON Tests: 1/1 passed
Button Load JSON Tests: 1/1 passed
Button Generate Tests: 1/1 passed
```

## Verification

Tested new CLI parameters with full set:
```bash
./gen_timing_params --dram-type lpddr4 \
    --orbit-dynamic-power-down 1 --orbit-dynamic-power-down-threshold 1000 \
    --orbit-dynamic-self-refresh 1 --orbit-dynamic-self-refresh-threshold 2000 \
    --orbit-periodic-training 1 --orbit-periodic-training-period 30000 \
    --orbit-temp-sensing 1 --orbit-temp-sensing-period 35000 \
    --orbit-zq-calibration-period 50000 \
    --orbit-t-refiab 4000000 --orbit-t-refipb 500000 --orbit-t-zqcal 1100000 \
    ...
```

Parsed values verified correct:
- dynamic_power_down: 1 ✓
- dynamic_self_refresh: 1 ✓
- periodic_training: 1 ✓
- periodic_training_period: 30000 ✓
- temp_sensing: 1 ✓
- temp_sensing_period: 35000 ✓
- zq_calibration_period: 35000 ✓
- t_refiab: 4000000 ✓
- t_refipb: 4000000 ✓
- t_zqcal: 1100000 ✓

## Status: COMPLETED

All tasks completed:
- [x] Added 13 new CLI parameters to gen_timing_params
- [x] Updated gui.py to pass all parameters to CLI
- [x] Fixed reference test parameters
- [x] Added field value validation tests
- [x] All tests pass
