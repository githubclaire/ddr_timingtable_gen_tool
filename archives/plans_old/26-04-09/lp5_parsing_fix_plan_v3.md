# LP5 Binary Parsing Fix Plan - Updated 2026-04-09

## Summary of Analysis

### Root Cause: gui.py PARSING BUGS - NOT gen_timing_params!

The binary generation is CORRECT! The bug is in gui.py parsing at wrong offsets.

---

## Issues Found

### Issue 1: RL/WL Parsing Offsets Wrong (gui.py)

| Field | Current (Wrong) | Correct |
|-------|-----------------|---------|
| common_offset | 0x138 | **0x13c** |
| per_entry_offset | 0x110 | **0x146** |

**Evidence**:
- Binary stores: rl=18, wl=9 at offsets 0x146, 0x147
- gui.py reads: rl=53, wl=0 at offsets 0x110, 0x111

**File**: gui.py lines 112-113

---

### Issue 2: wck_ratio Offset Wrong (gui.py)

| Field | Current | Correct |
|-------|---------|---------|
| wck_ratio reading | 0x138 | **0x13c** |

**Evidence**:
- Binary at 0x13c: wck_ratio=4 (entries 0-2), wck_ratio=2 (entry 3)
- gui.py reads 0x138: 0, 0, 0...

**File**: gui.py line 117

---

### Issue 3: Density Arrays Offset Wrong for LP5 (gui.py)

| DRAM Type | Current | Correct |
|-----------|---------|---------|
| LP5 | density_start = 0x88 | **0x80** |
| LP4 | density_start = 0x80 | 0x80 (correct) |

**Evidence**:
- LP5 density arrays are at file-level offsets 0x80-0xF2 (SAME as LP4)
- Current code incorrectly uses 0x88 (within each entry - wrong!)

**File**: gui.py line 70

---

### Issue 4: Density Index Calculation (gui.py)

| Field | Current | Issue |
|-------|---------|-------|
| density | at 0x81C | Binary stores 1, meaning density index = 0 (1Gb) |
| density_index | density - 1 | If density=1, index=0 |

**Note**: Binary stores density=1 in orbit config, which seems wrong (should be 16 for 16Gb?)
Need to verify what density value should be.

**File**: gui.py lines 58-66

---

### Issue 5: LP5 Orbit Config Offsets Wrong (gui.py)

| Field | Current (LP4 offsets) | Correct (LP5) |
|-------|----------------------|---------------|
| dram_t_ck | 0x90 | **0x864** |
| rclk_t_ck | 0x94 | **0x868** |
| boot_t_ck | 0x98 | **0x890** |

**Evidence**:
- Binary stores boot_t_ck=1256 at offset 0x890
- gui.py reads garbage at 0x98

**File**: gui.py lines 354-356

---

## Per-Entry wck_ratio Display

**Change Required**: Move wck_ratio from "Common Params" to "Per-Entry Params" in analysis modal

- Each of 4 entries should show its own wck_ratio (4, 4, 4, 2)
- Currently shows common wck_ratio (all entries show same value)

**File**: templates/gui.html - showAnalysisModal function

---

## Binary vs orbit_timing_params.c Comparison

### Input Periods
| Entry | Binary (t_ck stored) | Binary (t_wck calculated) | orbit_timing_params.c |
|-------|---------------------|--------------------------|---------------------|
| 0 | 1256 | 314 (÷4) | 471 |
| 1 | 1672 | 418 (÷4) | 938 |
| 2 | 2224 | 556 (÷4) | 1631 |
| 3 | 5000 | 2500 (÷2) | 2500 |

**Note**: The orbit_timing_params.c appears to be from LP4, not LP5. The periods don't match.

### RL/WL Values (CORRECT IN BINARY!)
| Entry | Binary rl | Binary wl | memcfg lookup result |
|-------|-----------|-----------|----------------------|
| 0 | 18 | 9 | RL=18 (memcfg index 11, rl_set=1) ✓ |
| 1 | 14 | 7 | RL=14 (memcfg index 10, rl_set=1) ✓ |
| 2 | 11 | 6 | RL=11 (memcfg index 9, rl_set=1) ✓ |
| 3 | 8 | 4 | RL=8 (memcfg index 6, rl_set=0) ✓ |

**Conclusion**: Binary is 100% CORRECT! The bug is gui.py parsing at wrong offsets.

---

## Implementation Plan

### gui.py Changes

| Line | Change |
|------|--------|
| 70 | `density_start = 0x80 if dram_type == 'lpddr5' else 0x80` (was 0x88 for LP5) |
| 112 | `common_offset = 0x13c if dram_type == 'lpddr5' else 0x106` (was 0x138) |
| 113 | `per_entry_offset = 0x146 if dram_type == 'lpddr5' else 0x110` (was 0x110) |
| 117 | `wck_ratio = data[entry_offset + 0x13c]` (was 0x138) |
| 354-356 | Add LP5-specific orbit config offsets: dram_t_ck=0x864, rclk_t_ck=0x868, boot_t_ck=0x890 |

### gui.html Changes

| Change |
|--------|
| Remove wck_ratio from common params section |
| Add wck_ratio column to per-entry params table |

---

## Verification Commands

```bash
# Test LP5 parsing after fix
python3 -c "
from gui import analyze_binary_file
result = analyze_binary_file('ddr_timing_table.lpddr5.single.bin')
entries = result['data']['timing_entries']['entries']
print('Entry | t_ck | t_ck_display | rl | wl | wck_ratio')
for e in entries:
    print(f'{e[\"entry\"]:5} | {e[\"t_ck\"]:4} | {e.get(\"t_ck_display\", \"N/A\"):12} | {e[\"rl\"]:2} | {e[\"wl\"]} | {e.get(\"wck_ratio\", 0)}')
"
```

**Expected After Fix**:
```
Entry | t_ck | t_ck_display | rl | wl | wck_ratio
    0 | 1256 | 314          | 18 | 9  | 4
    1 | 1672 | 418          | 14 | 7  | 4
    2 | 2224 | 556          | 11 | 6  | 4
    3 | 5000 | 2500         | 8  | 4  | 2
```

---

## Status: NOT IMPLEMENTED

This plan documents the issues found. Implementation pending.