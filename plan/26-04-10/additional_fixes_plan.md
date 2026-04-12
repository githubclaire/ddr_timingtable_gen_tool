# Additional Fixes Plan - 2026-04-10

## Issue 1: Test ALL Densities

### Current State
test_density_compat.py only tests 6 of 17 densities:
- LP4: [16, 4, 8] - MISSING: 2, 3, 6, 12
- LP5: [16, 4, 8] - MISSING: 1, 2, 3, 6, 12, 24, 32

### Fix Required
Update test_density_compat.py line 138-145:

```python
tests = [
    # LP4: all 7 densities
    ('lpddr4', [2]),
    ('lpddr4', [3]),
    ('lpddr4', [4]),
    ('lpddr4', [6]),
    ('lpddr4', [8]),
    ('lpddr4', [12]),
    ('lpddr4', [16]),
    # LP5: all 10 densities
    ('lpddr5', [1]),
    ('lpddr5', [2]),
    ('lpddr5', [3]),
    ('lpddr5', [4]),
    ('lpddr5', [6]),
    ('lpddr5', [8]),
    ('lpddr5', [12]),
    ('lpddr5', [16]),
    ('lpddr5', [24]),
    ('lpddr5', [32]),
]
```

### Verification
After fix, run: `python3 test_density_compat.py`
Expected: 17 tests pass

---

## Issue 2: Analysis Modal Per-Entry Params

### Current State
These params are parsed per-entry at different offsets (gui.py lines 147-157):
- wck_ratio
- tlp_resp, dll_enable, write_odt, nt_odt
- write_dbi, read_dbi, wpste, rpste

But displayed as "common" in Analysis Modal (single value for all entries).

### Expected Behavior
Show per-entry in Analysis Modal - each entry should display its own values because they CAN differ:
- LP4: wck_ratio = 2
- LP5: wck_ratio = 4

### Files to Modify

1. **gui.py** lines 185-199:
   - Remove these fields from "common" dict, OR
   - Add BOTH "common" and per-entry display
   
   Current:
   ```python
   common = {
       'tlp_resp': first.get('tlp_resp', 0),
       'dll_enable': first.get('dll_enable', 0),
       ...
   }
   ```
   
   Option A: Remove completely from common:
   ```python
   common = {}  # Don't include per-entry params in common
   ```
   
   Option B: Keep but also pass per-entry in each entry:
   - Already handled - entries[] contains these per-entry

2. **templates/gui.html** lines 1151-1165:
   - Change Analysis Modal to loop through entries and show these fields per-entry
   
   Current shows single "common" block:
   ```javascript
   if (data.timing_entries?.common) {
       const common = data.timing_entries.common;
       // show common params
   }
   ```
   
   Need to show in entry list instead:

### Implementation Steps

#### Step 1: gui.py - Remove from common (or keep for backward compat)
- Line 185-199: Optional - don't need to change if just the display changes

#### Step 2: gui.html - Update Analysis Modal
- Lines 490-600: Find where "common" params displayed
- Change to show these in the entry list for each timing entry:
  ```
  Entry 1: t_ck=X, rl=Y, wl=Z, wck_ratio=W, tlp_resp=T, dll_enable=D, ...
  Entry 2: t_ck=X, rl=Y, wl=Z, wck_ratio=W, tlp_resp=T, dll_enable=D, ...
  ```

### Verification
1. Open any binary in GUI
2. Click "Analysis" button
3. Verify each timing entry shows its own values for these fields

---

## Test Scripts Summary

| Script | Purpose | Current Status |
|--------|---------|---------------|
| test_binary_parse.py | Orbit config parsing | 14 passed ✓ |
| test_timing_entry_validation.py | Timing entry parsing | 20 passed ✓ |
| test_density_compat.py | Density compatibility | 6/17 tested |

---

## Dependencies
- Issue 2 requires understanding of how entries[] structure is passed to template