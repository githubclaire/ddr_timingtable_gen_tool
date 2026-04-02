# Implementation Plan - GUI Enhancements and Test Cases

## Date: 2026-04-02

---

## Overview

Comprehensive GUI enhancements and test case additions for DDR Timing Table Generator.

---

## Part 1: GUI Fixes (templates/gui.html)

### 1a. Fix saveJson - Remove Duplicate Periods
- **Location**: ~line 977-979
- **Change**: Skip `periods-0/1/2/3` fields, keep only `periods` string
- **Code**:
```javascript
for (let [key, value] of formData.entries()) {
    if (!key.startsWith('periods-')) {
        params[key] = value;
    }
}
```

### 1b. Fix loadJson - Render Periods
- **Location**: ~line 1217-1220
- **Change**: Add `renderPeriodsFromString(params.periods)` after loading params

### 1c. Add updateSpeedBin() Function
- **Location**: ~line 540
- **Function**:
```javascript
function updateSpeedBin() {
    const dramType = document.querySelector('select[name="dram-type"]').value;
    const speedBin = dramType === 'lpddr4' ? '4266' : '6400';
    document.querySelector('select[name="speed-bin"]').value = speedBin;
}
```

### 1d. Add updateMinDramTck() Function
- **Location**: ~line 543
- **Function**:
```javascript
function updateMinDramTck() {
    const speedBin = parseInt(document.querySelector('select[name="speed-bin"]').value);
    const minTck = Math.round(2000000 / speedBin);
    document.querySelector('input[name="min-dram-tck"]').value = minTck;
}
```

### 1e. Add updatePeriodsFromDefaults() Function
- **Location**: ~line 546
- **Function**:
```javascript
function updatePeriodsFromDefaults() {
    const dramType = document.querySelector('select[name="dram-type"]').value;
    const periods = dramType === 'lpddr4' 
        ? ['471', '938', '1631', '2500'] 
        : ['314', '418', '556', '2500'];
    renderPeriodsFromString(periods.join(' '));
}
```

### 1f. Update DRAM Type onchange
- **Location**: line 104
- **Change**: Add `updateSpeedBin(); updateMinDramTck(); updatePeriodsFromDefaults();`

### 1g. Add speed-bin onchange
- **Location**: ~line 147
- **Change**: Add `onchange="updateMinDramTck();"`

### 1h. Update LPDDR5 Default Values
- **Location**: ~line 272-310
- **Changes**:
  - nt-odt-upto: 0 → 625
  - wck-hf-upto: 624 → 625
  - wck-pst1-upto: 0 → 625
  - wck-pst2-upto: 0 → 1250
  - rdqs-pst1-upto: 0 → 625
  - rdqs-pst2-upto: 0 → 1250

### 1i. Add orbit-mixed Tooltip
- **Location**: ~line 331-333
- **Change**: Add `title="Mixed mode doubles total density"`

---

## Part 2: Test Cases (test_gui_params.py)

### Add to test_parameters() function:

**Test Case 1 - LPDDR4 rpste/wpste:**
```python
{
    'dram-type': 'lpddr4',
    'rpste-upto': '625',
    'wpste-upto': '625',
    # ... other params
}
```

**Test Case 2 - LPDDR5 timing options:**
```python
{
    'dram-type': 'lpddr5',
    'nt-odt-upto': '625',
    'bg-mode-upto': '625',
    'wck-hf-upto': '625',
    'wck-pst1-upto': '625',
    'wck-pst2-upto': '1250',
    'rdqs-pst1-upto': '625',
    'rdqs-pst2-upto': '1250',
    # ... other params
}
```

**Test Case 3 - orbit-mixed:**
```python
{
    'dram-type': 'lpddr4',
    'orbit-mixed': '1',
    # ... other params
}
```

---

## Test Sequence

```bash
# 1. Generate reference binaries
bash test_gen_lpddr4_bin.sh
bash test_gen_lpddr5_bin.sh

# 2. Run tests
python3 test_gui_params.py

# 3. Verify binary match
bash test_lpddr4.sh
bash test_lpddr5.sh

# 4. Commit
```

---

## Status

- [ ] Plan saved
- [ ] GUI fixes implemented
- [ ] Test cases added
- [ ] Tests executed
- [ ] Report generated
- [ ] Committed