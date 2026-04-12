# Plan: Fix LPDDR5 Binary Parsing and Dynamic Power Fields

## Status: COMPLETED

## Implementation Summary

### 1. LPDDR4/LPDDR5 offsets corrected in gui.py
Fixed based on C struct analysis - updated late field offsets:

**LPDDR4:**
- `density_code`: 0x81 → 0x91
- `zq_calibration_period`: 0xe4 → 0xf4
- `temp_sensing_period`: 0xec → 0xfc
- `t_refipb`: 0xf0 → 0x100
- `t_refiab`: 0xf4 → 0x104
- `t_zqcal`: 0xf8 → 0x108
- `mrr_byte_lane`: 0x100 → 0x110

**LPDDR5:**
- `density_code`: 0x88 → 0xa5
- `zq_calibration_period`: 0xec → 0xfc
- `temp_sensing_period`: 0xf4 → 0x104
- `t_refipb`: 0xf8 → 0x108
- `t_refiab`: 0xfc → 0x10c
- `t_zqcal`: 0x100 → 0x110
- `mrr_byte_lane`: 0x108 → 0x118

### 2. Dynamic power fields added to GUI
Added 6 dynamic power fields to templates/gui.html:
- `phy-low-power` checkbox + `phy-idle-cnt-th` number field
- `dynamic-power-down` checkbox + threshold field
- `dynamic-self-refresh` checkbox + threshold field

### 3. LECC validation removed from templates/gui.html
- Removed range validation for read-lecc-upto and write-lecc-upto
- Changed default values from "1" to "0"

### 4. Fixed num_rank and dq_width offsets (2026-04-03)
**LPDDR4:**
- `num_rank`: 0x1b → 0x0c (struct offset 12)
- `dq_width`: 0x21 → 0x24 (struct offset 36)

**LPDDR5:**
- `num_rank`: 0x24 → 0x28 (struct offset 40)
- `dq_width`: 0x2a → 0x2c (struct offset 44)

Verification:
- LPDDR4 dual: num_rank=2, dq_width=16 @ 0x80c, 0x824
- LPDDR5 dual: num_rank=2, dq_width=16 @ 0x828, 0x82c

## Test Results
```
============================================================
Binary Parse Test Suite
============================================================

Results: 10 passed, 0 failed
============================================================
```

## Verification
- zq_calibration_period now parses correctly (48000 for both LPDDR4 and LPDDR5)
- All dynamic power fields parsed and displayed in GUI
- LECC fields no longer have range validation
- num_rank and dq_width now parse correctly from binary