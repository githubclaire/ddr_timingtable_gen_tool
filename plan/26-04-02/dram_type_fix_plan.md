# Implementation Plan - Fix DRAM Type Dynamic Update

## Date: 2026-04-02

---

## Problem

When changing DRAM type from LPDDR4 to LPDDR5:
- omc-freq-ratio does not change from 2→1
- phy-freq-ratio does not change from 2→1
- orbit-config-density does not update to show LPDDR5 options

Need to manually refresh page to see changes.

---

## Root Cause

Current implementation uses `setTimeout(..., 0)` which runs asynchronously but may execute before `toggleDramOptions()` completes DOM updates.

---

## Solution

### Fix: Use requestAnimationFrame instead of setTimeout

**File**: `templates/gui.html`
**Line**: 104

**Change**:
```html
<!-- From -->
onchange="toggleDramOptions(); setTimeout(function() { setFreqRatios(); updateDensityOptions(); ... }, 0);"

<!-- To -->
onchange="toggleDramOptions(); requestAnimationFrame(function() { setFreqRatios(); updateDensityOptions(); updatePeriodsLabel(); updateDramTckDefault(); toggleDsmEn(); });"
```

**Why**: `requestAnimationFrame` waits for the browser to complete the current paint cycle, ensuring DOM updates from `toggleDramOptions()` are complete before running the update functions.

---

## Test Plan

1. Generate reference binaries:
   - bash test_gen_lpddr4_bin.sh
   - bash test_gen_lpddr5_bin.sh

2. Run test:
   - python3 test_gui_params.py

3. Verify all tests pass, especially reference binary comparison

---

## Changes

| # | Item | File | Change |
|---|------|------|--------|
| 1 | Fix timing issue | templates/gui.html:104 | Use requestAnimationFrame instead of setTimeout(..., 0) |

---

## Expected Result

When switching DRAM type:
- omc-freq-ratio: 2 (LPDDR4) → 1 (LPDDR5)
- phy-freq-ratio: 2 (LPDDR4) → 1 (LPDDR5)
- orbit-config-density: LPDDR4 options (2-16) → LPDDR5 options (2-32)