# Plan: Fix GUI Validation and Add Dynamic Params

## Date: 2026-04-03

## Issues to Fix

### Issue 1: MHz Mode Validation Broken
- validateTimingRanges() always validates using ps ranges
- When user selects MHz mode, validation fails

### Issue 2: Skip LECC Validation for LPDDR4
- LPDDR4 doesn't support ECC
- Validation still checks read-lecc-upto/write-lecc-upto ranges

### Issue 3: Add 5 Dynamic Params Parse Test
- Add tests for: phy_low_power, phy_idle_cnt_th, dynamic_power_down, dynamic_self_refresh, dynamic_power_down_threshold, dynamic_self_refresh_threshold

---

## Implementation

### 1. gui.html - Fix validateTimingRanges()

```javascript
function validateTimingRanges() {
    const dramType = document.querySelector('select[name="dram-type"]').value;
    const timingUnit = document.querySelector('input[name="timing-unit"]:checked').value;
    const isMhz = timingUnit === 'MHz';
    
    // Skip LECC validation for LPDDR4
    if ((fieldName === 'read-lecc-upto' || fieldName === 'write-lecc-upto') && dramType === 'lpddr4') {
        continue;
    }
    
    // For MHz mode, convert to ps for validation
    if (isMhz && val > 0 && fieldName.includes('-upto')) {
        val = Math.round(1000000 / val);
    }
}
```

### 2. gui.html - Change LECC default value from 625 to 1

### 3. gui.py - Add dynamic fields to fields_to_read

### 4. test_binary_parse.py - Add tests for dynamic fields

---

## Files to Modify

1. templates/gui.html
2. gui.py
3. test_binary_parse.py
