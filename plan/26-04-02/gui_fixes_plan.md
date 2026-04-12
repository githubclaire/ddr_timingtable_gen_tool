# Implementation Plan - DDR Timing Table Generator GUI Fixes

## Date: 2026-04-02

---

## Issues to Fix

### 1. Save JSON - Choose Path
- Use File System Access API (showSaveFilePicker) with blob fallback
- Allow user to choose save location

### 2. Button Sequence Adjustment
Current: Load Binary | Save JSON | Load JSON | Generate Binary
Required: Save JSON | Load JSON | Load Binary | Generate Binary

### 3. orbit-config-density Dynamic Adjustment
- Preserve current value if valid for new DDR type
- Otherwise use highest valid value
- LPDDR4: 2,3,4,6,8,12,16 Gb
- LPDDR5: 2,3,4,6,8,12,16,24,32 Gb

### 4. Remove zq-bg-mode, Auto-calculate
- Remove zq-bg-mode dropdown from LPDDR5 options (gui.html)
- Auto-calculate zq_bg_mode in gui.py based on bg_mode_upto >= min_dram_tck

### 5. Field Sequence Adjustment
- LPDDR4: Numbers first, then checkboxes
- LPDDR5: Numbers first, then checkboxes (after removing zq-bg-mode)

---

## Implementation Items

| # | Issue | File | Lines | Change |
|----|-------|------|-------|--------|
| 1 | Save JSON path | gui.html | ~1005-1026 | Add File System Access API with fallback |
| 2 | Button sequence | gui.html | 474-477 | Reorder: Save JSON, Load JSON, Load Binary, Generate |
| 3 | Density dropdown | gui.html | ~547-563 | Preserve selection when switching DDR types |
| 4a | Remove zq-bg-mode | gui.html | ~272-278 | Remove dropdown from LPDDR5 options |
| 4b | Auto-calc zq_bg_mode | gui.py | ~107-113 | Calculate based on bg_mode_upto >= min_dram_tck |
| 5a | LPDDR4 field order | gui.html | ~225-246 | Numbers first, then checkboxes |
| 5b | LPDDR5 field order | gui.html | ~257-320 | Numbers first, then checkboxes |

---

## zq_bg_mode Calculation Logic

From gen_timing_params (line 152):
```python
self.bg_mode = self.args.bg_mode_upto >= t_ck
```

Logic:
- If bg_mode_upto >= min_dram_tck → bg_mode = true → zq_bg_mode = 1
- If bg_mode_upto < min_dram_tck → bg_mode = false → zq_bg_mode = 0

Implementation in gui.py:
```python
min_dram_tck = safe_int(params.get('min-dram-tck'), 471)
bg_mode_upto = safe_int(params.get('bg-mode-upto'), 0)
zq_bg_mode = 1 if bg_mode_upto >= min_dram_tck else 0
```

---

## Test Plan
1. Run test_lpddr4.sh - verify binary match
2. Run test_lpddr5.sh - verify binary match
3. If tests pass, update docs and commit

---

## Test Results (2026-04-02)

### LPDDR4 Test
```
SUCCESS: Timing table matches C implementation! (compared 1182 bytes)
=== Test Complete ===
```

### LPDDR5 Test
```
SUCCESS: Timing table matches C implementation! (compared 1392 bytes)
=== Test Complete ===
```

---

## Implementation Status

- [x] 1. Save JSON path - Added File System Access API with fallback
- [x] 2. Button sequence - Reordered: Save JSON, Load JSON, Load Binary, Generate
- [x] 3. Density dropdown - Preserves selection when switching DDR types
- [x] 4a. Remove zq-bg-mode - Removed dropdown from LPDDR5 options
- [x] 4b. Auto-calc zq_bg_mode - Calculated based on bg_mode_upto >= min_dram_tck
- [x] 5a. LPDDR4 field order - Numbers first, then checkboxes
- [x] 5b. LPDDR5 field order - Numbers first, then checkboxes

All tests passed! Ready for commit.