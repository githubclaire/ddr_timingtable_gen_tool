# Implementation Plan: Debug GUI Issues

## Date: 2026-04-01

---

## Issues to Fix

### Issue 1: dram_t_ck and min_tck Not Converting with MHz Click

**Problem:** When clicking MHz radio button, dram_t_ck and min_tck values don't convert (stay at 471, 314 instead of converting to MHz)

**Debug Plan:**
1. Add console.log statements to JavaScript to trace execution
2. Check if radio button event handler is firing
3. Check if field selectors find correct elements
4. Verify conversion function is being called

**Changes Made:**
- Added debug logging to handleTimingUnitChange() function in gui.html

---

### Issue 2: LPDDR5 Binary - periods and dfs_lvl_t_ck Wrong

**Problem:** 
- When loading LPDDR5 binary, periods shows just 1 value (should be 4)
- dfs_lvl_t_ck values are wrong

**Debug Plan:**
1. Generate LPDDR5 binary via GUI
2. Check analyze output - what does it return for:
   - basic.periods
   - orbit.dfs_lvl_t_ck
3. If analyze is wrong → fix parsing in gui.py
4. If generation is wrong → fix params
5. Regenerate reference binary

---

### Issue 3: Default Values Wrong

**Problem:** read-lecc-upto and write-lecc-upto default to 0 instead of 625

**Fix Applied:**
- gui.html Line 207: changed value="0" to value="625"
- gui.html Line 212: changed value="0" to value="625"

---

## Files Modified

| File | Changes |
|------|---------|
| templates/gui.html | Added console.log debug, fixed default values |
| test_gui_params.py | To be updated with ref binary fix |

---

## Next Steps

1. Start GUI and test in browser
2. Check browser console for debug output
3. Fix JavaScript conversion if needed
4. Debug LPDDR5 binary issue
5. Regenerate reference binary if needed
6. Run tests to verify

---

## Expected Outcome

- dram_t_ck and min_tck convert when clicking MHz
- LPDDR5 binary loads correctly with proper periods and dfs values
- Default ECC values are 625
- All tests pass
