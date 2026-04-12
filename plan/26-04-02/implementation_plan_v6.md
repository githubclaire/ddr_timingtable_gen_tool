# Implementation Plan - DDR Timing Table Generator Fixes

## Date: 2026-04-02

---

## Issues to Fix

### 1. ddr_config.h Optional Generation
- Currently: Always generated (no option to disable)
- Request: Add checkbox to enable/disable, default no generate

### 2. Checkbox Values in ddr_config.h
- Need to verify all checkbox params are correctly converted
- Fix any parsing issues

### 3. orbit-config-density Dropdown
- Current: Same dropdown for both LPDDR4/LPDDR5
- Need: DRAM-type-specific options
- LPDDR4: 2, 3, 4, 6, 8, 12, 16 Gb
- LPDDR5: 1, 2, 3, 4, 6, 8, 12, 16, 24, 32 Gb

### 4. omc-freq-ratio / phy-freq-ratio Defaults
- Current: Always 2
- Need: LPDDR5=1, LPDDR4=2

### 5. Add New Test Functions
1. test_ps_mhz_toggle_button() - Button click test
2. test_periods_add_delete() - Periods add/delete
3. test_random_timing_with_mhz_toggle() - Combined test

---

## Implementation Phases

### Phase 1: ddr_config.h Optional Generation
- Add generate-config checkbox to GUI
- Modify gui.py to only generate when enabled

### Phase 2: Fix Checkbox Values
- Verify all ddr_config.h checkbox values
- Fix any parsing issues

### Phase 3: DRAM-type-specific Density Dropdown
- Update dropdown options based on selected DRAM type

### Phase 4: Fix omc/phy-freq-ratio Defaults
- Use DRAM-type-aware defaults

### Phase 5: Add New Tests
- Add 3 new test functions to test_gui_params.py

### Phase 6: Regenerate Reference Binaries & Run Tests

---

## Files to Modify

| File | Changes |
|------|---------|
| `gui.html` | Add generate-config checkbox, fix density dropdown |
| `gui.py` | Fix omc/phy-freq-ratio defaults, add optional config generation |
| `test_gui_params.py` | Add 3 new test functions |
| `ddr_timing_table.lpddr4.single.ref.bin` | Regenerate |
| `ddr_timing_table.lpddr5.single.ref.bin` | Regenerate |

---

## Success Criteria

- All tests pass
- ddr_config.h generation is optional
- Density dropdown shows correct options per DRAM type
- GUI generates identical binaries to CLI