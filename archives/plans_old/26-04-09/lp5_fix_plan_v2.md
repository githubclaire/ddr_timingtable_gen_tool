# LP5 Comprehensive Fix Plan - 2026-04-10

## ROOT CAUSE: Why LP4 Works But LP5 Doesn't

### Key Finding
**LP5 binary generation bug**: gen_timing_params uses CONVERTED t_ck for memcfg lookup instead of original t_wck input.

### Explanation
- **LP4**: input t_ck = stored t_ck (NO conversion)
  - memcfg lookup uses correct t_ck value
  - RL values decrease correctly with increasing t_ck

- **LP5**: input t_wck → CONVERTED to t_ck (t_ck = t_wck × wck_ratio)
  - memcfg lookup uses CONVERTED t_ck (WRONG!)
  - Example: Entry 0 input t_wck=314, converted t_ck=1256
  - memcfg looks up 1256ps instead of 314ps → gets wrong read_latency
  - This causes RL values to be completely wrong

### Evidence
```
LP4 Binary (CORRECT):
  Entry 0: t_ck=471, rl=40
  Entry 1: t_ck=938, rl=22  
  Entry 2: t_ck=1631, rl=16
  Entry 3: t_ck=2500, rl=12
  → RL decreases as t_ck increases ✓

LP5 Binary (WRONG):
  Entry 0: t_ck=1256, rl=53
  Entry 1: t_ck=1672, rl=233  ← WRONG! Should be ~20
  Entry 2: t_ck=2224, rl=175  ← WRONG! Should be ~16
  Entry 3: t_ck=5000, rl=78   ← WRONG! Should be ~10
  → RL order is completely wrong!
```

---

## Issues to Fix

### Issue 1: gen_timing_params - BINARY BUG (HIGH PRIORITY)
- **Problem**: Uses converted t_ck for memcfg lookup instead of t_wck
- **Location**: gen_timing_params line ~256-258
- **Fix**: Use t_wck (original input) for memcfg lookup, not t_ck (converted)
- **Impact**: This is the ROOT CAUSE of wrong RL/WL values in LP5 binary

### Issue 2: gui.py wck_ratio Offset Wrong
- **Current**: Reading at offset 0x88 (garbage: 104, 78, 59, 26)
- **Correct**: Reading at offset 0x13c (actual: 4, 4, 4, 2)
- **Location**: gui.py line 109

### Issue 3: Period Conversion Uses Fixed Ratio
- **Current**: Uses fixed wck_ratio=4 for all entries
- **Correct**: Use per-entry wck_ratio from offset 0x13c
- **Location**: gui.py lines 272-278

### Issue 4: Analysis Modal - Show Per-Entry wck_ratio
- **Current**: Shows wrong common param value
- **Correct**: Show per-entry wck_ratio in timing entry table

### Issue 5: Density Array Offsets Wrong for LP5
- **Current**: Reading at offset 0x80 (LP4 offset)
- **Correct**: Reading at offset 0x88 (within each LP5 entry)
- **Location**: gui.py lines 71-79
- **Issue**: LP5 density arrays are WITHIN each entry, not at file level
- **Also**: LP5 has 10 densities vs LP4 has 7

### Issue 6: Density Index Calculation
- **Current**: density_index = density - 1
- **Issue**: Needs verification against actual array indexing

---

## Files to Modify

| File | Changes | Issue |
|------|---------|-------|
| `gen_timing_params` | Use t_wck for memcfg lookup | #1 |
| `gui.py` | common_offset = 0x138 for LP5 | #2 |
| `gui.py` | Per-entry wck_ratio for period conversion | #3 |
| `gui.py` | Density array offsets 0x80→0x88 for LP5 | #5 |
| `gui.py` | Fix density index calculation | #6 |
| `templates/gui.html` | Show per-entry wck_ratio | #4 |

---

## NOT IMPLEMENTED - Just Planning
This plan documents the issues found during investigation. Implementation pending.

---

# TEST CASES TO ADD

## TC12: LP5 RL/WL Monotonicity Check
**Purpose**: Detect gen_timing_params bug - RL should decrease as t_ck increases

```python
def test_lp5_rl_wl_monotonicity(self):
    """TC12: LP5 RL/WL should decrease as t_ck increases"""
    bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
    valid_entries, _ = self.parse_binary(bin_file)
    
    rl_values = [e['rl'] for e in valid_entries]
    tck_values = [e['t_ck'] for e in valid_entries]
    
    # As t_ck increases, rl should DECREASE
    for i in range(len(tck_values) - 1):
        if tck_values[i] < tck_values[i+1] and rl_values[i] <= rl_values[i+1]:
            raise Exception(f"RL not decreasing: Entry {i} rl={rl_values[i]}, Entry {i+1} rl={rl_values[i+1]}")
```

## TC13: LP5 wck_ratio Per-Entry Check
**Purpose**: Verify wck_ratio is 2 or 4, not garbage

```python
def test_lp5_wck_ratio_per_entry(self):
    """TC13: LP5 wck_ratio should be 2 or 4"""
    bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
    valid_entries, _ = self.parse_binary(bin_file)
    
    for e in valid_entries:
        wck = e.get('wck_ratio', 0)
        if wck not in [2, 4]:
            raise Exception(f"Invalid wck_ratio: {wck} (should be 2 or 4)")
```

## TC14: LP5 Period Conversion Check
**Purpose**: Verify t_ck_display shows correct t_wck

```python
def test_lp5_period_conversion(self):
    """TC14: LP5 t_ck_display should equal input period"""
    bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
    valid_entries, _ = self.parse_binary(bin_file)
    
    input_periods = [314, 418, 556, 2500]
    for i, e in enumerate(valid_entries):
        t_ck_display = e.get('t_ck_display', e['t_ck'])
        if t_ck_display != input_periods[i]:
            raise Exception(f"Entry {i} t_ck_display: expected {input_periods[i]}, got {t_ck_display}")
```

## TC15: LP5 Density Array Check
**Purpose**: Verify density arrays parsed from correct offsets

```python
def test_lp5_density_arrays(self):
    """TC15: LP5 density arrays should be valid"""
    bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
    _, data = self.parse_binary(bin_file)
    
    density_arrays = data['timing_entries']['density_arrays']
    for arr_name in ['t_rfcab', 't_rfcpb', 't_rfmab', 't_rfmpb']:
        arr = density_arrays.get(arr_name, [])
        for val in arr:
            if val != 0 and (val < 10 or val > 1000):
                raise Exception(f"{arr_name} invalid value: {val}")
```

## TC16: LP4 Baseline (Regression)
**Purpose**: Verify LP4 still works

```python
def test_lp4_rl_wl_baseline(self):
    """TC16: LP4 RL/WL should work (baseline)"""
    bin_file = self.generate_binary('lpddr4', ['8'], ['471', '938', '1631', '2500'], False)
    valid_entries, _ = self.parse_binary(bin_file)
    
    rl_values = [e['rl'] for e in valid_entries]
    tck_values = [e['t_ck'] for e in valid_entries]
    
    for i in range(len(tck_values) - 1):
        if tck_values[i] < tck_values[i+1] and rl_values[i] <= rl_values[i+1]:
            raise Exception(f"LP4 RL not decreasing: Entry {i} rl={rl_values[i]}, Entry {i+1} rl={rl_values[i+1]}")
```

## Expected Results

| Test | Before Fix | After Fix |
|------|------------|-----------|
| TC12 (LP5 RL decreasing) | FAIL ✓ | PASS |
| TC13 (wck_ratio valid) | FAIL ✓ | PASS |
| TC14 (period conversion) | FAIL | PASS |
| TC15 (density arrays) | PASS | PASS |
| TC16 (LP4 baseline) | PASS ✓ | PASS |

**Test Results (Current - Before Fix):**
- TC12: FAIL - "RL not decreasing: Entry 0 t_ck=1256 rl=53, Entry 1 t_ck=1672 rl=233"
- TC13: FAIL - "Invalid wck_ratio: 104 (should be 2 or 4)"
- TC15: PASS
- TC16: PASS

Tests correctly detect the bugs!

---

# COMPREHENSIVE TIMING PARAM TESTS

## Analysis Modal Displayed Params

### Section 1: Per-Entry Params (24 fields + 3 arrays)
| Field | Description |
|-------|-------------|
| rl | Read latency |
| wl | Write latency |
| mr_rl | MR read latency |
| mr_wl | MR write latency |
| mr_wr | MR write |
| mr_cal | MR calibration |
| mr_tccd_l | MR CCD latency |
| bank_mode | Bank mode |
| wck_fm | WCK frequency mode |
| rdqs_pst_mode | RDQS post mode |
| rdqs_pst | RDQS post |
| rdqs_pre | RDQS pre |
| wck_pst | WCK post |
| wck_on | WCK on |
| read_link_parity | Read link parity (LP5) |
| write_link_parity | Write link parity (LP5) |
| t_rtw | Read to write |
| t_wtr_a | Write to read all |
| t_wtr | Write to read |
| t_rc | Row cycle |
| trddata_en | Read data enable |
| freq | Frequency |
| timing_zqcal | ZQ calibration timing |
| timing_param[0-20] | Timing parameters array (21 values) |
| timing_derate[0-1] | Timing derate array (2 values) |
| dfi_timing_param[0-7] | DFI timing parameters (8 values) |

### Section 2: Common Params (9 fields)
| Field | Description |
|-------|-------------|
| wck_ratio | WCK ratio |
| tlp_resp | TLP response |
| dll_enable | DLL enable |
| write_odt | Write ODT |
| nt_odt | Non-target ODT |
| write_dbi | Write DBI |
| read_dbi | Read DBI |
| wpste | WPSTE |
| rpste | RPSTE |

### Section 3: Density-Dependent Params (9 fields)
| Field | Description |
|-------|-------------|
| t_rfcab | Refresh all banks |
| t_rfcpb | Refresh per bank |
| t_rfmab | Refresh per bank all banks |
| t_rfmpb | Refresh per bank per bank |
| t_refdpr | Refresh DPR |
| tx_pbr2pbr | PBR to PBR |
| t_xsr | Self refresh exit |
| t_xsdll | DLL unlock |
| t_xs_fast | Fast exit |

### Section 4: Orbit Config (3 fields)
| Field | Description |
|-------|-------------|
| dram_t_ck | DRAM t_ck |
| rclk_t_ck | RCLK t_ck |
| boot_t_ck | Boot t_ck |

---

## Additional Test Cases to Add

### TC17: All Per-Entry Numeric Fields Present
**Purpose**: Verify all per-entry fields are parsed

```python
def test_lp5_all_per_entry_fields(self):
    """TC17: Verify all per-entry fields are parsed"""
    bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
    valid_entries, _ = self.parse_binary(bin_file)
    
    expected_fields = ['rl','wl','mr_rl','mr_wl','mr_wr','mr_cal','mr_tccd_l',
                       'bank_mode','wck_fm','rdqs_pst_mode','rdqs_pst','rdqs_pre',
                       'wck_pst','wck_on','read_link_parity','write_link_parity',
                       't_rtw','t_wtr_a','t_wtr','t_rc','trddata_en','freq','timing_zqcal']
    
    for e in valid_entries:
        for field in expected_fields:
            if field not in e:
                raise Exception(f"Missing field: {field}")
```

### TC18: Common Params Valid Values
**Purpose**: Common params should have valid values

```python
def test_lp5_common_params_valid(self):
    """TC18: Common params should be valid values"""
    bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
    _, data = self.parse_binary(bin_file)
    common = data['timing_entries']['common']
    
    # wck_ratio must be 2 or 4
    if common.get('wck_ratio', 0) not in [2, 4]:
        raise Exception(f"Invalid wck_ratio: {common.get('wck_ratio')}")
    
    # dll_enable should be 0 or 1
    if common.get('dll_enable', 0) not in [0, 1]:
        raise Exception(f"Invalid dll_enable: {common.get('dll_enable')}")
```

### TC19: Density-Dependent Params Range
**Purpose**: Density params should be in reasonable range

```python
def test_lp5_density_dependent_range(self):
    """TC19: Density params should be in reasonable range"""
    bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
    _, data = self.parse_binary(bin_file)
    dd = data['timing_entries']['density_dependent']
    
    for key, val in dd.items():
        if val != 0 and (val < 10 or val > 1000):
            raise Exception(f"{key} out of range: {val}")
```

### TC20: Timing Param Arrays Not Empty
**Purpose**: timing_param and dfi_timing_param arrays should have values

```python
def test_lp5_timing_arrays_not_empty(self):
    """TC20: timing_param arrays should have values"""
    bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
    valid_entries, _ = self.parse_binary(bin_file)
    
    for e in valid_entries:
        tp = e.get('timing_param', [])
        if not tp or all(v == 0 for v in tp):
            raise Exception("timing_param array is empty")
        
        dfi = e.get('dfi_timing_param', [])
        if not dfi or all(v == 0 for v in dfi):
            raise Exception("dfi_timing_param array is empty")
```

### TC21: LP4 vs LP5 Common Param Offset Difference
**Purpose**: Verify LP5 uses different offset than LP4

```python
def test_lp4_vs_lp5_common_params_offset(self):
    """TC21: LP5 should have different common param offset than LP4"""
    # LP4: common params at offset 0x106
    # LP5: common params at offset 0x138 (after fix)
    # Parse both and verify offsets are different
```

### TC22: Timing Entry Count
**Purpose**: Verify correct number of entries parsed

```python
def test_lp5_entry_count(self):
    """TC22: Should parse 4 timing entries"""
    bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
    valid_entries, _ = self.parse_binary(bin_file)
    
    if len(valid_entries) != 4:
        raise Exception(f"Expected 4 entries, got {len(valid_entries)}")
```

---

## Test Summary

| Test ID | Description | Expected |
|---------|-------------|----------|
| TC12 | LP5 RL decreasing | FAIL (detects gen bug) |
| TC13 | wck_ratio valid | FAIL (detects offset bug) |
| TC14 | Period conversion | FAIL |
| TC15 | Density arrays | PASS |
| TC16 | LP4 baseline | PASS |
| TC17 | All per-entry fields | PASS |
| TC18 | Common params valid | FAIL |
| TC19 | Density range | PASS |
| TC20 | Timing arrays not empty | PASS |
| TC21 | LP4 vs LP5 offset | PASS |
| TC22 | Entry count | PASS |

---

## NOT IMPLEMENTED - Just Planning
This plan documents all issues, fixes, and test cases. Implementation pending.

## Issue 1: gen_timing_params - BINARY BUG (ROOT CAUSE)
**Priority: HIGHEST** - This is the root cause of wrong RL/WL values

### Current Code Flow (WRONG):
```python
# gen_timing_params lines ~136-165
for t_ck in self.args.periods:  # These are t_wck for LP5!
    self.t_wck = t_ck  # Store as t_wck
    # ... later ...
    self.dram.update(t_ck)  # t_ck gets converted (multiplied by wck_ratio)
    # Line 258:
    self.read_latency = self.memcfg.read_latency[self.rl_set]
    # ^ Uses CONVERTED t_ck for lookup - WRONG!
```

### Fix Required:
```python
# In gen_timing_params line ~256:
# Change: self.dram.update(t_ck)
# To: self.dram.update(self.t_wck)  # Use original input
```

---

## Issue 2: gui.py - Fix wck_ratio Offset (Line 109)
**Priority: HIGH**

### Current:
```python
common_offset = 0x88 if dram_type == 'lpddr5' else 0x106
```

### Fix:
```python
common_offset = 0x138 if dram_type == 'lpddr5' else 0x106
```

---

## Issue 3: gui.py - Fix Period Conversion (Lines 272-278)
**Priority: HIGH**

### Current (WRONG):
```python
if is_lpddr5 and first_wck_ratio > 0:
    display_period = t_ck // first_wck_ratio  # Uses first entry ratio!
```

### Fix:
```python
# Use per-entry wck_ratio from correct offset 0x138
if is_lpddr5:
    wck_ratio = data[offset + 0x138]  # Per-entry wck_ratio
    if wck_ratio > 0:
        display_period = t_ck // wck_ratio
    else:
        display_period = t_ck
```

---

## Issue 4: gui.py - Fix Density Array Offsets (Lines 71-79)
**Priority: HIGH**

### Current (WRONG):
```python
density_arrays['t_rfcab'] = [struct.unpack('<H', data[0x80+i*2:0x82+i*2])[0] ...
# Same offset 0x80 for all densities - WRONG for LP5!
```

### Fix:
```python
# Add LP5/LP4 branch:
if is_lpddr5:
    # LP5: density arrays within each entry start at 0x88
    density_start = 0x88
else:
    # LP4: density arrays at file level start at 0x80
    density_start = 0x80

density_arrays['t_rfcab'] = [struct.unpack('<H', data[density_start+i*2:density_start+2+i*2])[0] for i in range(num_densities)]
# ... apply for all density arrays
```

---

## Issue 5: gui.py - Fix Density Index Calculation (Lines 65-66)
**Priority: MEDIUM**

### Current:
```python
density_index = min(max(density - 1, 0), num_densities - 1)
```

### Steps:
1. Verify density value from orbit config offset 0x824
2. Test if density_index = density - 1 is correct
3. If not, adjust to match actual array indexing

---

## Issue 6: gui.html - Show Per-Entry wck_ratio
**Priority: MEDIUM**

### Steps:
1. Edit templates/gui.html
2. Add wck_ratio field to per-entry row generation in analysis modal
3. Use value from offset 0x13c (per-entry)

---

## Implementation Order

| Step | Issue | File | Priority |
|------|-------|------|----------|
| 1 | wck_ratio offset | gui.py line 109 | HIGH |
| 2 | Period conversion | gui.py lines 272-278 | HIGH |
| 3 | Density offsets | gui.py lines 71-79 | HIGH |
| 4 | Density index | gui.py lines 65-66 | MEDIUM |
| 5 | Show wck_ratio | gui.html | MEDIUM |
| 6 | **gen_timing_params** | gen_timing_params line ~256 | **HIGHEST** |

---

## Verification Commands

After implementing fixes, run:

```bash
python3 -c "
from gui import analyze_binary_file
result = analyze_binary_file('ddr_timing_table.lpddr5.single.bin')
entries = result['data']['timing_entries']['entries']
print('Entry | t_ck | t_wck | rl | wl | wck_ratio')
for e in entries:
    t_wck = e.get('t_ck_display', e['t_ck'])
    print(f'{e[\"entry\"]:5} | {e[\"t_ck\"]:4} | {t_wck:4} | {e[\"rl\"]:2} | {e[\"wl\"]} | {e.get(\"wck_ratio\", 0)}')
"
```

### Expected After Fix:
```
Entry | t_ck | t_wck | rl | wl | wck_ratio
    0 | 1256 |  314 | 20 | 8 | 4
    1 | 1672 |  418 | 16 | 6 | 4  
    2 | 2224 |  556 | 14 | 4 | 4
    3 | 5000 | 2500 | 12 | 4 | 2
```

---

## Notes
- Issue 6 (gen_timing_params) is the ROOT CAUSE - fixing only gui.py will not fix the binary generation bug
- After fixing gen_timing_params, need to REGENERATE LP5 reference binaries to get correct RL/WL values
- gui.py fixes will make parsing match what IS in the binary (even if binary is wrong)
- Both need to be fixed for complete solution