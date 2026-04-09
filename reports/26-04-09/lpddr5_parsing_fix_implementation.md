# LP5 Binary Parsing Fix Implementation Report - 2026-04-09

## Summary

Fixed multiple issues in `gui.py` that caused incorrect LPDDR5 binary parsing. The fixes enable proper detection of all 4 timing entries for LP5 and correct orbit config field values.

## Issues Fixed

### 1. Entry Size Mismatch

**Problem**: gui.py used `entry_size = 0x128` (296 bytes) for both LP4 and LP5, but LP5 entries are stored at 348-byte (0x15C) intervals.

**Fix**: Added DRAM-type-aware entry size in `parse_timing_entries()`:
```python
entry_size = 0x15C if dram_type == 'lpddr5' else 0x128
```

### 2. Period Parsing

**Problem**: LP5 periods were being parsed with default LP4 entry_size, causing only 1 period to be detected.

**Fix**: Applied same dynamic entry_size logic in `parse_binary()` period parsing.

### 3. LP5 dfs_lvl_t_ck Offsets

**Problem**: Used LP4 offsets (0x63, 0x65, 0x67) for LP5.

**Fix**: Updated to correct LP5 offsets:
```python
dfs_offsets = (0x64, 0x66, 0x68)
```

### 4. LP5 density_code Offset

**Problem**: Used offset 0xA5 for LP5 density_code.

**Fix**: Updated to correct LP5 offset:
```python
('density_code', 0x80, '<I')
```

### 5. LP5 Default Periods

**Problem**: Default periods used t_ck values instead of t_wck values.

**Fix**: Updated to use correct default values:
```python
periods = [314, 418, 556, 2500]  # t_wck values
```

## Files Modified

| File | Changes |
|------|---------|
| `gui.py` | 5 fixes for LP5 parsing |
| `test_timing_entry_validation.py` | Updated LP5 test expectations from 1 to 4 entries |
| `README.md` | Added recent updates section |

## Test Results

### test_timing_entry_validation.py
```
======================================================================
SUMMARY: 8 passed, 0 failed
======================================================================
```

All 8 tests pass:
- TC1-TC2: LP4 single/dual (4 entries each) ✓
- TC3-TC4: LP5 single/dual (now correctly detects 4 entries) ✓
- TC5-TC6: LP4 diff params (4 entries each) ✓
- TC7-TC8: LP5 diff params (4 entries each) ✓

### test_random_value_flow.py
```
============================================================
Final Summary
============================================================
  Checkboxes: PASS
  Numeric: PASS
  Dropdowns: PASS

All tests PASSED!
```

452/452 tests pass.

## Verification

After fixes, LP5 binary parsing shows correct values:

```
LP5 Analysis:
  periods: 1256 1672 2224 5000
  dfs_lvl_t_ck: [1672, 2224, 5000]
  density_code: 3
  Valid timing entries: 4
    Entry 0: t_ck=1256, rl=53, wl=1
    Entry 1: t_ck=1672, rl=233, wl=0
    Entry 2: t_ck=2224, rl=175, wl=0
    Entry 3: t_ck=5000, rl=78, wl=0
```

## Notes

- Binary generation (`gen_timing_params`) was NOT buggy - it correctly stores LP5 entries at 348-byte intervals
- The bug was in `gui.py` parsing logic that assumed LP4 structure for LP5
- LP4 parsing remains unchanged and correct