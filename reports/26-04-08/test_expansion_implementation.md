# Test Expansion Implementation Report - 2026-04-08

## Summary

Implemented test expansion for 4 DRAM configs (LP4 Single/Dual, LP5 Single/Dual) and fixed GUI parsing for `dram_t_ck` field. Added non-parseable fields warning list.

---

## Changes Made

### 1. gui.py - dram_t_ck Parsing Fix

**Problem**: GUI derived `dram_tck` from timing table periods instead of reading from orbit config.

**Solution**: Added parsing of `dram_t_ck`, `rclk_t_ck`, `boot_t_ck` from binary:

| DRAM Type | Offset | Field |
|-----------|--------|-------|
| LPDDR4 | 0x88 | dram_t_ck |
| LPDDR4 | 0x8C | rclk_t_ck |
| LPDDR4 | 0x90 | boot_t_ck |
| LPDDR5 | 0x90 | dram_t_ck |
| LPDDR5 | 0x94 | rclk_t_ck |
| LPDDR5 | 0x98 | boot_t_ck |

**Code Changes**:
- Added field reads at gui.py:180-182 (LP5) and gui.py:262-264 (LP4)
- Updated `basic.dram_tck` to use parsed value: `orbit_data.get('dram_t_ck', periods[0] if periods else 471)`
- Added `dram_t_ck`, `rclk_t_ck`, `boot_t_ck` to orbit output

### 2. gui.py - Non-Parseable Fields List

**Problem**: 17 fields are generated at runtime, not stored in binary - need warning when loading binary.

**Solution**: Added `non_parseable_fields` list to orbit data:

```python
non_parseable_fields = [
    'variable-trrd', 'txsr-as-1st-ed', 'enhanced-nt-odt', 'wire-length',
    'wdqs-ctrl-mode', 'rpste-upto', 'wpste-upto', 'nt-odt-upto',
    'bg-mode-upto', 'wck-always-on-from', 'wck-always-on-upto',
    'wck-1to4-upto', 'wck-hf-upto', 'wck-pst1-upto', 'wck-pst2-upto',
    'rdqs-pst1-upto', 'rdqs-pst2-upto',
]
```

### 3. test_random_value_flow.py - Already Updated (Previous Session)

- Tests 27 checkbox fields across 4 configs (224 tests)
- Tests 12 numeric fields across 4 configs (204 tests)
- Tests 2 dropdown fields across 4 configs (24 tests)

### 4. test_gui_checkbox_integration.py - Already Updated (Previous Session)

- Tests A1-A6: Forward flow (generate -> parse) across 4 configs
- Tests B1-B3: Reverse flow (load -> display) across 4 configs

---

## Test Results

```
test_random_value_flow.py:
  Checkbox results: 224 passed, 0 failed
  Numeric results: 204 passed, 0 failed
  Dropdown results: 24 passed, 0 failed

test_gui_checkbox_integration.py:
  Tests: 21 passed, 0 failed
```

---

## Verification

dram_t_ck parsing verified:
```
Input: cfg.dram_t_ck = 555
Output: result['data']['orbit']['dram_t_ck'] = 555
Output: result['data']['basic']['dram_tck'] = 555
```

---

## Files Modified

| File | Changes |
|------|---------|
| gui.py | Added dram_t_ck/rclk_t_ck/boot_t_ck parsing + non_parseable_fields list |
| test_random_value_flow.py | Already updated (4 configs) |
| test_gui_checkbox_integration.py | Already updated (4 configs) |