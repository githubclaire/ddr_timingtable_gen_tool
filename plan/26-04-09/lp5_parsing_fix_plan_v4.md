# LP5 Binary Parsing Fix Plan - Updated 2026-04-09 (v4)

## Summary

The binary generation is CORRECT for timing values (rl=18, wl=9, etc.). 
The bugs are in:
1. **gui.py** - wrong parsing offsets for LP5
2. **gui.py** - wrong wck_ratio offset for periods detection (Issue 5)
3. **ddr_config_init.py** - wrong density_code calculation
4. **orbit_config.py** - LP5 struct field order mismatch with LP4

---

## Issue 1: gui.py Parsing Offsets (LP5)

### 1.1 Density Arrays Offset (gui.py:70)

| Current | Correct | Note |
|---------|---------|------|
| `density_start = 0x88 if dram_type == 'lpddr5' else 0x80` | `density_start = 0x80` (both LP4/LP5) | LP5 density arrays at file-level 0x80 |

### 1.2 Common Params Offset (gui.py:112-113)

| Field | Current | Correct | Note |
|-------|---------|---------|------|
| common_offset | 0x138 | **0x13c** | wck_ratio, tlp_resp, etc. |
| per_entry_offset | 0x110 | **0x146** | rl, wl, mr_*, etc. |

### 1.3 wck_ratio Reading (gui.py:117)

| Current | Correct |
|---------|---------|
| `data[entry_offset + 0x138]` | `data[entry_offset + 0x13c]` |

### 1.4 LP5 Orbit Config Timing Fields (gui.py:354-356)

| Field | Current (LP5) | Correct | Match LP4 |
|-------|--------------|---------|-----------|
| dram_t_ck | 0x90 | **0x88** | ✓ |
| rclk_t_ck | 0x94 | **0x8C** | ✓ |
| boot_t_ck | 0x98 | **0x90** | ✓ |

---

## Issue 2: Binary Generation - density_code Bug

### Problem

When `--orbit-config-density` is set, the binary stores wrong `density_code`.

**Example**:
- Input: `--orbit-config-density 4` (4Gb)
- Binary stores: density=1, density_code=0 (WRONG!)
- Should store: density=4, density_code=3

### Location

`ddr_config_init.py` lines 85-89:

```python
# Current (WRONG):
cfg.density = density
if 'density_code' in kwargs:
    cfg.density_code = kwargs['density_code']
else:
    cfg.density_code = get_density_code(cfg.density)

# Should be:
cfg.density = density  # This is the --orbit-config-density value
cfg.density_code = get_density_code(cfg.density)  # Always compute from density
```

### Correct Density Mapping

| Density (Gb) | density_code |
|--------------|--------------|
| 1 | 0 |
| 2 | 1 |
| 3 | 2 |
| 4 | 3 |
| 6 | 4 |
| 8 | 5 |
| 12 | 6 |
| 16 | 7 |
| 24 | 8 |
| 32 | 9 |

---

## Issue 3: Binary Generation - LP5 Orbit Config Timing Fields

### Problem

LP5 struct has different field order than LP4, causing timing values at wrong offsets.

**Current LP5 Binary**:
- 0x888 = 20000 (should be dram_t_ck, but is boot_t_ck value)
- 0x890 = 1256 (should NOT be here)

**Should match LP4**:
- 0x888 = dram_t_ck
- 0x890 = boot_t_ck

### Root Cause

`orbit_config.py` has different field order between LP4 and LP5 structs.

### Location

- `orbit_config.py`: Make LP5 struct fields match LP4 order
- `ddr_config_init.py` lines 78-84: Write timing values to correct offsets

### LP5 ddr_config_init.py Current Values (Hardcoded)

```python
cfg.rclk_t_ck = 41666
cfg.boot_t_ck = 20000
cfg.boot_t_ck_low = 83333
if dram_type == 'lpddr5':
    cfg.dram_t_ck = 1256
else:
    cfg.dram_t_ck = 471
```

These should be written to correct struct offsets that match LP4.

---

## Issue 4: wck_ratio Display in Analysis Modal

### Change

In `templates/gui.html` `showAnalysisModal` function:
- Remove wck_ratio from "Common Params" section
- Add wck_ratio column to "Per-Entry Params" table

---

## Issue 5: LP5 Periods Display (t_wck vs t_ck)

### Problem

LP5 periods show t_ck values instead of t_wck values because wck_ratio offset is wrong.

**Current (Wrong)**:
- Periods display: "1256 1672 2224 5000" (t_ck values)
- t_ck_display in entries: "314 418 556 1250" (entry 3 is wrong, should be 2500)

**Expected (Correct)**:
- Periods display: "314 418 556 2500" (t_wck values - user input)
- t_ck_display in entries: "314 418 556 2500" (all correct)

### Root Cause

gui.py uses wrong offset (0x138) for reading wck_ratio in LP5 binary:
- Line 267: `common_offset = 0x88` - used for first entry, but wrong
- Line 284: `data[offset + 0x138]` - wrong offset, should be 0x13c

### Bug Flow

```
Line 267: common_offset = 0x88  (WRONG - should be 0x13c)
         ↓
Line 284: wck_ratio = data[offset + 0x138]  (READS 0!)
         ↓
         Since wck_ratio=0, line 288: display_period = t_ck
         ↓
Result: periods = [1256, 1672, 2224, 5000] (t_ck, not t_wck)
```

### Location

| Line | Current | Correct |
|------|---------|---------|
| gui.py:267 | `common_offset = 0x88` | `0x13c` |
| gui.py:284 | `data[offset + 0x138]` | `data[offset + 0x13c]` |

### Note

The code calculates per-entry wck_ratio in the loop (line 284), but uses wrong offset.
Also, line 267's `first_wck_ratio` variable is calculated but never used - can be removed or ignored.

---

## Issue 6: Analysis Modal Entry Display - Use t_ck, Not t_ck_display

### Problem

In analysis modal, the entry header shows `t_ck_display` (converted t_wck) but should show `t_ck` (actual stored value in binary).

**Current (gui.html:1096)**:
```javascript
const display_t_ck = e.t_ck_display !== undefined ? e.t_ck_display : e.t_ck;
```

This shows t_ck_display if available, which is wrong for LP5.

### Expected

The entry column header should show `t_ck` (the value stored in binary that the timing parameters are based on).

```javascript
const display_t_ck = e.t_ck;
```

### Location

`templates/gui.html` line 1096

### Rationale

- Entry timing parameters (rl, wl, etc.) are based on stored `t_ck` value
- Display should show `t_ck` (e.g., 1256, 1672, 2224, 5000) not `t_ck_display` (314, 418, 556, 2500)
- Periods field (in basic section) should show `t_wck` (user input)

---

## Verification Commands

### After Fix - Test LP5 Parsing

```bash
python3 -c "
from gui import analyze_binary_file
result = analyze_binary_file('ddr_timing_table.lpddr5.single.ref.bin')

# Check periods display
print('Periods (should be t_wck):', result['data']['basic']['periods'])

# Check entries
entries = result['data']['timing_entries']['entries']
print()
print('Entry | t_ck | t_ck_display | rl | wl | wck_ratio')
for e in entries:
    print(f'{e[\"entry\"]:5} | {e[\"t_ck\"]:4} | {e.get(\"t_ck_display\", \"N/A\"):12} | {e[\"rl\"]:2} | {e[\"wl\"]} | {e.get(\"wck_ratio\", 0)}')
"
```

**Expected After Fix**:
```
Periods (should be t_wck): 314 418 556 2500

Entry | t_ck | t_ck_display | rl | wl | wck_ratio
    0 | 1256 | 314          | 18 | 9  | 4
    1 | 1672 | 418          | 14 | 7  | 4
    2 | 2224 | 556          | 11 | 6  | 4
    3 | 5000 | 2500         | 8  | 4  | 2
```

---

## Files to Modify

| File | Lines | Change |
|------|-------|--------|
| gui.py | 70 | density_start = 0x80 (remove LP5 special case) |
| gui.py | 112 | common_offset = 0x13c for LP5 |
| gui.py | 113 | per_entry_offset = 0x146 for LP5 |
| gui.py | 117 | wck_ratio offset = 0x13c |
| gui.py | 267 | first_wck_ratio offset = 0x13c (or remove unused var) |
| gui.py | 284 | wck_ratio offset = 0x13c (periods detection) |
| gui.py | 354-356 | LP5 orbit config offsets: 0x88, 0x8C, 0x90 |
| ddr_config_init.py | 85-89 | Fix density_code calculation |
| ddr_config_init.py | 78-84 | Ensure correct struct offsets for LP5 |
| orbit_config.py | ~220-232 | Align LP5 struct field order with LP4 |
| gui.html | showAnalysisModal | Move wck_ratio to per-entry |
| gui.html | 1096 | Use t_ck instead of t_ck_display for entry header |

---

## Status: NOT IMPLEMENTED

This plan documents all issues found. Implementation pending.