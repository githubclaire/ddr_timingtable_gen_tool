# LP5 Binary Generation Bug Investigation Plan - 2026-04-09

## Problem Statement

After WCK 4:1 conversion (t_ck × 4), the generated binary only shows 1 valid timing entry instead of 4. The t_ck values for entries 1-3 are corrupted.

### Observed Behavior

| Entry | Input Period | Expected t_ck (×4) | Actual in Binary |
|-------|--------------|-------------------|------------------|
| 0 | 314 | 1256 | **1256** ✓ |
| 1 | 418 | 1672 | **0** ✗ |
| 2 | 556 | 2224 | **1179666** ✗ |
| 3 | 2500 | 5000 | **11206782** ✗ |

## Investigation Summary

### 1. Root Cause: Entry Size Mismatch

**NOT a packing bug in gen_timingtable_bin()** - the issue is entry SIZE mismatch between LP4 and LP5:

| DRAM Type | Correct Entry Size | GUI Uses | Result |
|-----------|-------------------|----------|--------|
| LP4 | 0x128 (296 bytes) | 0x128 ✓ | PASS |
| LP5 | 0x15C (348 bytes) | 0x128 ✗ | FAIL |

**LP5 binary stores entries at 348-byte intervals:**
```
Entry 0: offset 0     → freq=796, t_ck=1256 ✓
Entry 1: offset 348   → freq=598, t_ck=1672 ✓ (but GUI reads at offset 296)
Entry 2: offset 696   → freq=449, t_ck=2224 ✓ (but GUI reads at offset 592)
Entry 3: offset 1044  → freq=200, t_ck=5000 ✓ (but GUI reads at offset 888)
```

GUI uses `entry_size = 0x128` for both LP4 and LP5, but LP5 entries are actually spaced 348 bytes apart.

### 2. LP4 vs LP5 Period Display

**LP4: No change needed** - periods should be t_ck (input = output, no WCK conversion)
**LP5: Needs fix** - periods should show t_wck (convert from t_ck using wck_ratio)

For LP5:
- Binary stores: t_ck (converted: input × wck_ratio)
- Current GUI shows: t_ck
- Should show: t_wck (original input period)

Example:
| Input Period | wck_ratio | t_ck stored | Current GUI | Should Show |
|--------------|-----------|-------------|-------------|-------------|
| 314 | 4 | 1256 | 1256 | 314 |
| 418 | 4 | 1672 | 1672 | 418 |
| 556 | 4 | 2224 | 2224 | 556 |
| 2500 | 2 | 5000 | 5000 | 2500 |

### 3. LP5 Orbit Config Offset Bugs in gui.py

gui.py uses wrong offsets for LP5 orbit config fields:

| Field | gui.py Uses | Correct Offset | Current Value | Correct Value | Status |
|-------|-------------|----------------|---------------|---------------|--------|
| dfs_lvl_t_ck_0 | 0x63 | **0x64** | 34816 | 1672 | **WRONG** |
| dfs_lvl_t_ck_1 | 0x65 | **0x66** | 45062 | 2224 | **WRONG** |
| dfs_lvl_t_ck_2 | 0x67 | **0x68** | 34824 | 5000 | **WRONG** |
| density_code | 0xA5 | **0x80** | 0 | 3 | **WRONG** |

LP4 orbit config offsets are correct - only LP5 has these issues.

## Fix Plan

### Root Cause Correction

The binary generation is **NOT buggy** - LP5 entries are correctly stored at 348-byte (0x15C) intervals. The bug is that **gui.py uses wrong entry_size for LP5**.

### Step 1: Fix LP5 Entry Size in gui.py

In `parse_timing_entries()` and period parsing, use dynamic entry size based on DRAM type:

```python
# Determine entry size based on DRAM type
# LP4: 0x128 (296 bytes)
# LP5: 0x15C (348 bytes)
entry_size = 0x15C if dram_type == 'lpddr5' else 0x128
```

Also in `parse_binary()` period parsing (line 241):
```python
entry_size = 0x15C if is_lpddr5 else 0x128
```

### Step 2: Fix LP5 Period Parsing in gui.py (convert t_ck to t_wck)

For LP5 only, convert t_ck back to t_wck using wck_ratio:

```python
t_ck = struct.unpack('<I', data[offset+4:offset+8])[0]
# For LP5: convert t_ck to t_wck
if is_lpddr5:
    wck_ratio = data[offset + 0x106] if offset + 0x106 < len(data) else 0
    if wck_ratio > 0:
        period_value = t_ck // wck_ratio  # Convert to input period
    else:
        period_value = t_ck
else:
    period_value = t_ck  # LP4: no conversion needed

if 300 <= period_value <= 5000:
    periods.append(period_value)
```

**LP4 behavior**: periods = t_ck (correct - no WCK conversion)
**LP5 behavior**: periods = t_wck (convert t_ck ÷ wck_ratio)

### Step 3: Update Test Expectations

After fixing entry size, LP5 should detect 4 entries. Update test expectations:

| Test Case | Current Expectation | Updated Expectation |
|-----------|---------------------|---------------------|
| TC3 (LP5 Same) | 1 entry | 4 entries |
| TC4 (LP5 Same) | 1 entry | 4 entries |
| TC7 (LP5 Diff) | at least 1 | 4 entries |
| TC8 (LP5 Diff) | at least 1 | 4 entries |

### Step 4: Fix LP5 Orbit Config Offsets in gui.py

Fix wrong offsets for LP5 orbit config fields (currently uses LP4 offsets):

**Current (WRONG for LP5):**
```python
# In parse_binary() around line 303
dfs_offsets = (0x63, 0x65, 0x67)  # LP5
...
('density_code', 0xA5 + (0x10 if is_dual_channel else 0), '<I'),
```

**Fix (use correct LP5 offsets):**
```python
# In parse_binary() around line 303
# LP5: dfs_lvl_t_ck at 0x64, 0x66, 0x68 (not 0x63, 0x65, 0x67)
dfs_offsets = (0x64, 0x66, 0x68)  # Correct for LP5
...
# LP5: density_code at 0x80 (not 0xA5)
('density_code', 0x80, '<I'),  # Correct for LP5
```

| Field | Current (Wrong) | Correct |
|-------|-----------------|---------|
| dfs_lvl_t_ck_0 | 0x63 | **0x64** |
| dfs_lvl_t_ck_1 | 0x65 | **0x66** |
| dfs_lvl_t_ck_2 | 0x67 | **0x68** |
| density_code | 0xA5 | **0x80** |

### Step 4: Verify All LP5 GUI Display Params

| File | Change |
|------|--------|
| `gui.py` - `parse_timing_entries()` | Add dynamic entry_size based on DRAM type (0x15C for LP5, 0x128 for LP4) |
| `gui.py` - `parse_binary()` period parsing | Add DRAM-type-aware entry_size and convert t_ck to t_wck for LP5 |
| `gui.py` - orbit config offsets | Fix LP5 dfs_lvl_t_ck offsets (0x63→0x64, etc.) and density_code offset (0xA5→0x80) |
| `test_timing_entry_validation.py` | Update LP5 test expectations from 1 to 4 entries |

## Expected Result After Fix

After fixing entry_size in gui.py, LP5 should detect all 4 valid entries:

| Entry | Input Period (t_wck) | t_ck (stored) | In Range | wck_ratio |
|-------|---------------------|---------------|----------|-----------|
| 0 | 314 | 1256 | ✓ | 4 |
| 1 | 418 | 1672 | ✓ | 4 |
| 2 | 556 | 2224 | ✓ | 4 |
| 3 | 2500 | 5000 | ✓ | 2 |

The timing entry validation test should pass with 8/8 tests.

The GUI should display correct LP5 periods (t_wck) in the input field:
- Input periods: [314, 418, 556, 2500] (t_wck, as user entered)
- Stored t_ck: [1256, 1672, 2224, 5000] (after WCK conversion)

## Test Commands

```bash
# Generate LP5 binary (unchanged - generation is correct)
python3 ./gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 --speed-bin 6400 \
  --orbit-config-density 4 --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 \
  --write-lecc-upto 625 --write-odt-upto 10000 --cpipe-depth 1 --dpipe-depth 1 \
  --omc-freq-ratio 1 --phy-freq-ratio 1 --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 314 \
  314 418 556 2500

# Verify entries (with correct entry_size 0x15C for LP5)
python3 -c "
import struct
with open('ddr_timing_table.bin', 'rb') as f:
    data = f.read()
for i in range(4):
    offset = i * 0x15C  # Use 0x15C for LP5, 0x128 for LP4
    t_ck = struct.unpack('<I', data[offset+4:offset+8])[0]
    print(f'Entry {i}: t_ck={t_ck}')

# Expected after fix:
# Entry 0: t_ck=1256
# Entry 1: t_ck=1672
# Entry 2: t_ck=2224
# Entry 3: t_ck=5000
"

# Run timing entry validation test
python3 test_timing_entry_validation.py
```

Expected output: `SUMMARY: 8 passed, 0 failed`

## Notes

- **No changes needed to gen_timing_params** - binary generation is correct
- **gui.py needs multiple fixes for LP5**:
  1. Entry size: 0x128 → 0x15C
  2. Period conversion: t_ck → t_wck using wck_ratio
  3. dfs_lvl_t_ck offsets: 0x63/0x65/0x67 → 0x64/0x66/0x68
  4. density_code offset: 0xA5 → 0x80

- **LP4 is correct** - no changes needed for LP4 parsing

### Test Coverage Gaps

**test_random_value_flow.py** only tests checkbox/numeric/dropdown values, NOT:
- Timing entry parsing (entry_size, field offsets)
- LP5 vs LP4 structural differences
- Offset verification

**Recommendation**: Extend test_random_value_flow.py to verify offset correctness by:
1. Generating binary with known reference values
2. Verifying parsed values match expected (not just "some value returned")
3. Adding LP5-specific offset tests

### Analysis Modal Impact

The analysis modal (templates/gui.html) displays data from `analyze_binary_file()`, which is affected by:
1. Wrong entry_size → entries 1-3 show garbage
2. Wrong dfs_lvl_t_ck → shows wrong values
3. Wrong density_code → shows 0 instead of 3

After fixes, the modal should display correct LP5 data.