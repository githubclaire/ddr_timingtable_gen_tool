# GUI Fix Plan - DDR Timing Table Generator

## Current Issues Identified

### 1. Binary Comparison Failure
**Problem:**
- GUI binary (with use-python): 7872 bytes (full with orbit config)
- Reference binary ddr_timing_table.lpddr4.single.bin: 1182 bytes (C only)
- Sizes don't match because of orbit config section

**Root Cause:**
- GUI has "use-python" checkbox unchecked by default
- Without --orbit-config-use-python, only timing table is generated
- test_lpddr4.sh uses --orbit-config-use-python, generates full binary

**Solution:**
- Check "use-python" by default in GUI
- Compare only timing table section (first 0x800 bytes)

### 2. Test Coverage Issues
- test_gui_params.py compares full binary vs C-only binary (wrong)
- Need to compare timing table sections only
- Need more comprehensive test cases for orbit config params

### 3. Unused Feature
- DDR type override dropdown not needed
- Use dram-type selector only

### 4. ps/MHz Toggle Issues
- dram_t_ck not dynamic with ps/MHz change
- Value conversion not handling float strings properly

### 5. Missing Tests
- No orbit config param auto tests
- No ps/MHz toggle auto test

---

## Implementation Completed

### Phase 1: Fix Binary Comparison ✅

#### 1.1 Fixed test_gui_params.py to compare timing table only
- Uses compare_binaries_timing() for reference comparison
- Compares only first 0x800 bytes

#### 1.2 Checked "use-python" by default in GUI
- Set checkbox checked by default in gui.html
- GUI now generates full binary (timing + orbit config)

### Phase 2: Remove Unused Features ✅

#### 2.1 Removed DDR type override dropdown
- Hidden from gui.html
- Removed from gui.py

### Phase 3: Fix ps/MHz Toggle ✅

#### 3.1 Fixed dram_t_ck dynamic update
- dram_tck is in fieldsToConvert list
- updateDramTckDefault() called on DRAM type change

#### 3.2 Fixed value conversion
- Python has safe_int() for handling float strings
- JavaScript uses float for conversion

### Phase 4: Add Orbit Config Tests ✅

#### 4.1 Added orbit config param test cases (12 tests)
1. LPDDR4 single - base config (density=4)
2. LPDDR5 single - base config (density=4)
3. LPDDR4 dual channel
4. LPDDR5 dual channel
5. LPDDR4 density=8
6. LPDDR5 density=16
7. LPDDR5 dsm-en on
8. LPDDR4 num-rank=1 (no rank-interleaving)
9. LPDDR4 byte-mode=1
10. LPDDR5 mixed=1
11. LPDDR4 rfm-en on
12. LPDDR5 ca-odt on

#### 4.2 Added ps/MHz toggle test
- Test clicking MHz converts all timing values
- Test clicking ps converts back
- Verify values are correct after conversion

### Phase 5: Improve Test Coverage ✅

#### 5.1 Added comprehensive param tests
- All GUI params tested with valid combinations
- Uses params from test_lpddr4.sh/test_lpddr5.sh as reference

---

## Files Modified

| File | Changes |
|------|---------|
| gui.html | Check use-python default, hide DDR type override |
| gui.py | Remove DDR type override handling |
| test_gui_params.py | Fix comparison, add orbit config tests, add ps/MHz test |
| plan/gui_fix_plan.md | Updated with implementation status |
| reports/summary.md | Updated with implementation report |

---

## Test Commands

```bash
# Run LPDDR4 test
./test_lpddr4.sh

# Run LPDDR5 test  
./test_lpddr5.sh

# Run GUI tests
python3 test_gui_params.py
```

---

## Verification Checklist

- [x] Binary size matches when using same params
- [x] Timing table section matches between GUI and test script
- [x] All orbit config params generate correctly
- [x] ps/MHz toggle works correctly
- [x] dram_t_ck updates dynamically with toggle
- [x] All test cases pass

---

## Orbit Config Parameters Tested

| Param | Type | Values Tested |
|-------|------|--------------|
| orbit-config-density | int | 4, 8, 16 |
| orbit-byte-mode | int | 0, 1 |
| orbit-mixed | int | 0, 1 |
| orbit-rank-interleaving | bool | true, false |
| orbit-num-rank | int | 1, 2 |
| orbit-reboot-with-mrw | bool | true |
| orbit-rfm-en | bool | true |
| orbit-dsm-en | bool | true (LPDDR5) |
| orbit-ca-odt | bool | true |
| orbit-config-use-python | bool | true (default) |

## ps/MHz Toggle Test Parameters

| Field | Tested |
|-------|--------|
| write-odt-upto | ✅ |
| read-dbi-upto | ✅ |
| write-dbi-upto | ✅ |
| read-lecc-upto | ✅ |
| write-lecc-upto | ✅ |
| wck-1to4-upto | ✅ |
| wck-always-on-from | ✅ |
| wck-always-on-upto | ✅ |
| dfs-lvl-t-ck-0 | ✅ |
| dfs-lvl-t-ck-1 | ✅ |
| dfs-lvl-t-ck-2 | ✅ |
| dram-tck | ✅ |
| min-dram-tck | ✅ |
| periods | ✅ |

---

**Status**: Implementation Complete
**Date**: 2026-03-31
