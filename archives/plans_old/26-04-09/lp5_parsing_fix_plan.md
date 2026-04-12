# LP5 Parsing Fix Plan - 2026-04-10

## Problem Summary

After initial fixes, LP5 binary parsing still has issues:
1. Periods display shows t_ck (stored values) instead of t_wck (user input)
2. Many analysis modal fields have incorrect values due to wrong offsets
3. rclk_t_ck/boot_t_ck not displayed in analysis modal
4. Test scripts didn't catch these bugs because they don't verify offset correctness
5. Timing entry params (rl, wl, etc.) have wrong offsets for LP5 - values are incorrect

## Issue 1: Period Display (t_ck → t_wck)

### Current State
- LP5 binary stores t_ck (after WCK conversion: input × wck_ratio)
- GUI displays periods as t_ck values: [1256, 1672, 2224, 5000]
- User wants: [314, 418, 556, 2500] (original input)

### Root Cause
- Previous attempt used offset 0x106 for wck_ratio (LP4 offset)
- LP5 has different entry structure, wck_ratio is at offset 0x88

### Fix
```python
# In parse_binary() period parsing
if is_lpddr5:
    wck_ratio_offset = entry_offset + 0x88  # Correct for LP5
    wck_ratio = data[wck_ratio_offset] if wck_ratio_offset < len(data) else 0
    if wck_ratio > 0:
        period_value = t_ck // wck_ratio
    else:
        period_value = t_ck
else:
    period_value = t_ck
```

## Issue 2: Analysis Modal Field Order

### Current Order
```
Header: Entry i t_ck=value
Rows: rl, wl, mr_rl, mr_wl, ..., freq, timing_zqcal
```

### Requested Order (User)
Move freq to top, below t_ck:
```
Header: Entry i t_ck=value, freq=value  
Rows: (other params after)
```

## Issue 3: All Entry Param Offsets Are Wrong for LP5

### Problem
LP5 entry structure is DIFFERENT from LP4. Common params are at different offsets.

### Current Issues Found
| Field | LP4 Offset | Current LP5 | Correct LP5 |
|-------|------------|-------------|-------------|
| wck_ratio | 0x106 | 150 (wrong!) | Should be ~4 |
| rl | 0x110 | 53 (by luck correct?) | Need verify |
| wl | 0x111 | 1 (by luck correct?) | Need verify |
| write_odt | 0x10A | 174 (wrong!) | Should be small |
| write_dbi | 0x10C | 229 (wrong!) | Should be small |

### Verified Working (by luck)
- t_ck at offset 0x04: CORRECT
- freq at offset 0x00: CORRECT  
- rl at offset 0x110: CORRECT
- wl at offset 0x111: CORRECT

### Need to Fix
- wck_ratio (currently shows 150, should be 4)
- tlp_resp
- dll_enable
- write_odt (currently 174, should be small)
- nt_odt
- write_dbi (currently 229, should be small)
- read_dbi
- wpste
- rpste
- All mr_* fields
- All wck_* fields
- All rdqs_* fields
- t_rtw, t_wtr_a, t_wtr, t_rc, trddata_en

The issue is LP5 entry has different byte ordering/structure than LP4. Need to find correct offsets by comparing with reference binary.

## Issue 3: Add rclk_t_ck/boot_t_ck to Analysis Modal

### Current State
- `rclk_t_ck` is parsed at offset 0x94 (LP5)
- `boot_t_ck` is parsed at offset 0x98 (LP5)
- Values are stored in `orbit_data`
- NOT displayed in analysis modal

### Fix
In `templates/gui.html`, add to "Orbit Config" section:
```html
<tr><td>rclk_t_ck</td><td>{orbit.rclk_t_ck}</td></tr>
<tr><td>boot_t_ck</td><td>{orbit.boot_t_ck}</td></tr>
```

Also check if there's a `boot_t_ck_low` field - need to verify if it exists in binary.

## Issue 5: Test Coverage Gaps

### Current test_random_value_flow.py
- Only tests checkbox fields (26 types × 2 values × 4 configs = 208 tests)
- Only tests numeric fields (12 types × multiple values × 4 configs = ~200 tests)
- Does NOT test: offset correctness, timing entry params, period conversion

### Current test_timing_entry_validation.py  
- Tests timing entry count
- Tests t_ck values
- Tests reference binary comparison for some fields
- Does NOT test: all entry param offsets, period conversion, LP5-specific fields

### Tests to Add

1. **Period Conversion Test**
   - Generate LP5 binary with known input periods [314, 418, 556, 2500]
   - Verify parsed periods = t_wck (314, 418, 556, 2500), not t_ck (1256, 1672, 2224, 5000)

2. **ALL Entry Field Offset Tests** (28+ fields)
   - Compare each timing entry field with reference binary
   - Fields: wck_ratio, tlp_resp, dll_enable, write_odt, nt_odt, write_dbi, read_dbi, wpste, rpste
   - Fields: rl, wl, mr_rl, mr_wl, mr_wr, mr_rtp, mr_cal, mr_tccd_l
   - Fields: bank_mode, wck_fm, rdqs_pst_mode, rdqs_pst, rdqs_pre, wck_pst, wck_on
   - Fields: read_link_parity, write_link_parity
   - Fields: t_rtw, t_wtr_a, t_wtr, t_rc, trddata_en
   - Fields: freq, timing_zqcal
   - Fields: timing_param[21], timing_derate[2], dfi_timing_param[8]

3. **All 4 DRAM Configs**
   - LP4 single, LP4 dual, LP5 single, LP5 dual
   - Each config test all 4 entries
   - Compare all 28+ fields per entry

4. **Analysis Modal Field Verification**
   - Verify displayed values match parsed values
   - Verify field ordering (freq at top)
   - Verify rclk_t_ck, boot_t_ck are displayed

5. **Reference Binary Comprehensive Test**
   - Load each reference binary
   - Parse all fields
   - Compare each field against known correct values
   - Report any mismatches

### Test Count Estimate
- Period conversion: 4 tests (LP5 single/dual × same/diff params)
- Entry fields: 4 configs × 4 entries × 28 fields = 448 field comparisons
- Modal display: 4 configs
- Reference binary: 4 reference files

**Total new test cases: 100+**

## Implementation Steps

### Step 1: Fix Period Display
- Find correct LP5 wck_ratio offset (should be around 0x88 based on earlier analysis)
- Update period parsing to convert t_ck → t_wck
- Test with reference binary

### Step 2: Verify/Fix Entry Common Params
- Compare each field with reference binary
- Create LP5-specific offset map
- Update gui.py for LP5 case

### Step 3: Verify Density-Dependent Params
- Check t_rfcab, t_rfcpb, etc. offsets for LP5
- Compare with reference values

### Step 4: Add rclk_t_ck/boot_t_ck to Modal
- Add fields to gui.html analysis modal
- Verify correct values

### Step 5: Update Tests
- Add period conversion verification
- Add LP5-specific offset tests

## Files to Modify

| File | Changes |
|------|---------|
| `gui.py` | Fix LP5 period conversion, entry param offsets (28+ fields), density-dependent offsets |
| `templates/gui.html` | Move freq to top (below t_ck in header), add rclk_t_ck, boot_t_ck to analysis modal |
| `test_timing_entry_validation.py` | Add period conversion tests, all entry field offset tests (28+ fields), modal verification |
| `test_random_value_flow.py` | (Optional) Could add reference binary comparison tests |

## Verification Commands

```bash
# After fix, LP5 should show:
# periods: 314 418 556 2500 (t_wck, not t_ck)
# timing entries: 4 entries with correct values
# analysis modal: all fields match reference

python3 -c "
import sys
sys.path.insert(0, '.')
from gui import analyze_binary_file
result = analyze_binary_file('ddr_timing_table.lpddr5.single.ref.bin')
print('Periods:', result['data']['basic']['periods'])
print('dfs_lvl_t_ck:', result['data']['orbit']['dfs_lvl_t_ck'])
print('density_code:', result['data']['orbit']['density_code'])
entries = result['data']['timing_entries']['entries']
for e in entries:
    print(f\"t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}\")
"
```

## Expected Results After Fix

### Before vs After

| Field | Before | After | Notes |
|-------|--------|-------|-------|
| periods | 1256 1672 2224 5000 | 314 418 556 2500 | t_ck → t_wck conversion |
| freq in header | (in middle of table) | (at top, below t_ck) | Move to top |
| wck_ratio | 150 | 4 | Wrong offset fixed |
| write_odt | 174 | (small value) | Wrong offset fixed |
| write_dbi | 229 | (small value) | Wrong offset fixed |
| rl | 53 | 53 | Already correct (by luck) |
| wl | 1 | 1 | Already correct (by luck) |
| dfs_lvl_t_ck | [1672, 2224, 5000] | [1672, 2224, 5000] | ✓ Already fixed |
| density_code | 3 | 3 | ✓ Already fixed |
| timing entries | 4 entries | 4 entries | ✓ Already fixed |
| rclk_t_ck | (not displayed) | Show value | Add to modal |
| boot_t_ck | (not displayed) | Show value | Add to modal |

### All Entry Fields to Verify (28+ per entry)

For each of 4 entries × 4 configs:
1. wck_ratio - NEEDS FIX
2. tlp_resp - NEEDS FIX
3. dll_enable - NEEDS FIX
4. write_odt - NEEDS FIX
5. nt_odt - NEEDS FIX
6. write_dbi - NEEDS FIX
7. read_dbi - NEEDS FIX
8. wpste - NEEDS FIX
9. rpste - NEEDS FIX
10. rl - OK
11. wl - OK
12. mr_rl - NEEDS VERIFY
13. mr_wl - NEEDS VERIFY
14. mr_wr - NEEDS VERIFY
15. mr_rtp - NEEDS VERIFY
16. mr_cal - NEEDS VERIFY
17. mr_tccd_l - NEEDS VERIFY
18. bank_mode - NEEDS VERIFY
19. wck_fm - NEEDS VERIFY
20. rdqs_pst_mode - NEEDS VERIFY
21. rdqs_pst - NEEDS VERIFY
22. rdqs_pre - NEEDS VERIFY
23. wck_pst - NEEDS VERIFY
24. wck_on - NEEDS VERIFY
25. read_link_parity - NEEDS VERIFY
26. write_link_parity - NEEDS VERIFY
27. t_rtw - NEEDS VERIFY
28. t_wtr_a - NEEDS VERIFY
29. t_wtr - NEEDS VERIFY
30. t_rc - NEEDS VERIFY
31. trddata_en - NEEDS VERIFY
32. freq - OK
33. timing_zqcal - NEEDS VERIFY
34. timing_param[21] - NEEDS VERIFY
35. timing_derate[2] - NEEDS VERIFY
36. dfi_timing_param[8] - NEEDS VERIFY