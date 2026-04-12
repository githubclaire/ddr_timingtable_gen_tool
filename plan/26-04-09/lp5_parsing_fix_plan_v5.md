# LP5 Binary Parsing Fix Plan - Complete (v5)

## Issues Already Fixed (Earlier Implementation)

1. ✅ gui.py density_start = 0x80 (LP5)
2. ✅ gui.py common_offset = 0x13c (LP5)
3. ✅ gui.py per_entry_offset = 0x146 (LP5)
4. ✅ gui.py wck_ratio offset = 0x13c (LP5 periods detection)
5. ✅ gui.py LP5 orbit config offsets (0x88, 0x8C, 0x90)
6. ✅ gui.html wck_ratio moved to per-entry
7. ✅ gui.html t_ck display uses t_ck instead of t_ck_display
8. ✅ test_timing_entry_validation.py binary names with .ref.bin

---

## Remaining Issues (NOT FIXED)

### Issue 1: dram_t_ck and boot_t_ck Swapped in LP5 Analysis Modal

**Problem**: LP5 shows wrong values in analysis modal:
- Current: dram_t_ck = 20000, boot_t_ck = 1256
- Expected: dram_t_ck = 1256, boot_t_ck = 20000

**Root Cause**: gui.py uses same offsets (0x88, 0x8C, 0x90) for LP5 as LP4, but LP5 binary has different field positions.

**Binary Values**:
- 0x888 = 20000 (should be boot_t_ck based on struct)
- 0x890 = 1256 (should be dram_t_ck based on struct)
- But gui.py reads at: 0x888 → dram_t_ck, 0x890 → boot_t_ck (SWAPPED!)

**Location**: gui.py lines 348-350

**Fix Needed**:
```python
# Need to determine correct LP5-specific offsets
# Option 1: Use different offsets for LP5
# Option 2: Read from correct struct positions
```

---

### Issue 2: Different orbit-config-density - GUI Not Update

**Problem**: When loading binary with different densities, the GUI may not correctly update density-dependent params.

**Location**: gui.py density parsing (line ~61)

**Fix Needed**: Verify density parsing works for all density values.

---

### Issue 3: LP5 vs LP4 Orbit Config Differences

**Problem**: LP5 is missing some fields that LP4 has:
- LP4 has: ctrl_dq_width, dram_clock_gating
- LP5 missing these fields in parsed output
- LP5 has extra field: rclk_t_ck showing wrong value (83333)

**Location**: gui.py orbit config field parsing (lines 342-380+)

**Fix Needed**: Add missing LP5 fields or correct the parsing offsets.

---

### Issue 4: test_gui_params.py Python Compatibility

**Problem**: TypeError with subprocess.run() when parameters are int instead of str

**Location**: test_gui_params.py line ~1079

**Fix Needed**:
```python
# Add type casting before subprocess.run():
for key in modified_params:
    if modified_params[key] is not None and not isinstance(modified_params[key], str):
        modified_params[key] = str(modified_params[key])
```

---

### Issue 5: C Binary Comparison Mismatch (PRE-EXISTING)

**Problem**: test_lpddr5.py, test_dual_channel.py show struct mismatches between Python and C

**Note**: Pre-existing issue, not related to LP5 parsing fixes.

---

## Files to Modify (Remaining)

| File | Lines | Change | Status |
|------|-------|--------|--------|
| gui.py | ~61 | Density offset: 0x1C for LP4, 0x24 for LP5 | NOT FIXED |
| gui.py | 348-350 | Fix LP5 dram_t_ck/boot_t_ck swap | NOT FIXED |
| gui.py | 342-380+ | Add missing LP5 orbit config fields | NOT FIXED |
| test_gui_params.py | ~1079 | Type casting for subprocess params | NOT FIXED |

---

## Verification Commands

```bash
# Verify LP5 parsing
python3 -c "
import sys
sys.path.insert(0, '.')
from gui import analyze_binary_file
result = analyze_binary_file('ddr_timing_table.lpddr5.single.ref.bin')
print('LP5:')
print(f'  density: {result[\"data\"][\"orbit\"].get(\"density\")}')
print(f'  selected_density: {result[\"data\"][\"timing_entries\"][\"selected_density\"]}')
print(f'  t_rfcab: {result[\"data\"][\"timing_entries\"][\"density_dependent\"][\"t_rfcab\"]}')
print(f'  dram_t_ck: {result[\"data\"][\"orbit\"].get(\"dram_t_ck\")}')
print(f'  boot_t_ck: {result[\"data\"][\"orbit\"].get(\"boot_t_ck\")}')
"

# Verify LP4 (regression check)
python3 -c "
import sys
sys.path.insert(0, '.')
from gui import analyze_binary_file
result = analyze_binary_file('ddr_timing_table.lpddr4.single.ref.bin')
print('LP4:')
print(f'  density: {result[\"data\"][\"orbit\"].get(\"density\")}')
print(f'  selected_density: {result[\"data\"][\"timing_entries\"][\"selected_density\"]}')
print(f'  t_rfcab: {result[\"data\"][\"timing_entries\"][\"density_dependent\"][\"t_rfcab\"]}')
print(f'  dram_t_ck: {result[\"data\"][\"orbit\"].get(\"dram_t_ck\")}')
print(f'  boot_t_ck: {result[\"data\"][\"orbit\"].get(\"boot_t_ck\")}')
"

# Run tests
python3 test_timing_entry_validation.py
python3 test_binary_parse.py
```

---

## Summary

**Completed**: 8 fixes from earlier implementation
**Remaining**: 5 issues to fix

The main issues are:
1. LP5 dram_t_ck/boot_t_ck swapped
2. Density offset needs DRAM-type specific
3. Missing LP5 orbit config fields
4. test_gui_params.py type compatibility
5. C binary comparison (pre-existing)