# Threshold Offsets Fix & Density Expansion Plan - 2026-04-10

## Investigation Results

### Issue 1: Threshold Parsing Still Wrong

**Roundtrip Test (dp=111, ds=222) Results:**

| Config | Expected | Actual | Status |
|--------|----------|--------|--------|
| LP4 Single | dp=111, ds=222 | dp=111, ds=222 | ✓ PASS |
| LP4 Dual | dp=111, ds=222 | dp=0, ds=0 | ✗ FAIL |
| LP5 Single | dp=111, ds=222 | dp=7274496, ds=14548992 | ✗ FAIL |
| LP5 Dual | dp=111, ds=222 | dp=7274496, ds=14548992 | ✗ FAIL |

**Root Cause:** gui.py uses hardcoded offsets that don't match actual ctypes struct layout for different configs.

**Current gui.py Offsets vs Expected:**

| Config | gui.py (lines 338-341, 422-423) | Expected (from ctypes) | Status |
|--------|-------------------------------|------------------------|-------|
| LP4 Single | ds=0xdc, dp=0xe0 | ds=0xdc, dp=0xe0 | ✓ |
| LP4 Dual | ds=0xdc, dp=0xe0 | ds=0xec, dp=0xf0 | ✗ |
| LP5 Single | ds=0xe2, dp=0xe6 | ds=0xe4, dp=0xe8 | ✗ |
| LP5 Dual | ds=0xf2, dp=0xf6 | ds=0xf4, dp=0xf8 | ✗ |

**ctypes struct offsets from create_orbit_config():**

```
LP4 Dual:        ds=0xec, dp=0xf0
LP5 Single:     ds=0xe4, dp=0xe8
LP5 Dual:       ds=0xf4, dp=0xf8
```

---

### Issue 2: Roundtrip Test with zq_calibration_period=555

**Test requirement:**
- Generate binary with zq_calibration_period=555
- Parse and verify the value roundtrips correctly
- Test across all 4 configs

---

### Issue 3: CLI vs GUI Comparison - Density Array Tests

**Current test_gui_params.py coverage:**

| Test Function | Tests | Configs Tested | CLI Compare? |
|---------------|-------|----------------|-------------|
| test_gui_vs_cli() | 2 | LP4 single, LP5 single | ✓ Yes |
| test_random_param_comparison() | 20 | LP4, LP5 random | ✓ Yes |
| test_dual_channel() | 2 | LP4 dual, LP5 dual | ✓ Yes |
| test_all_densities() | 17 | All densities | ✗ NO CLI |

**test_all_densities() limitation:**
- Only tests GUI generate → analyze → verify density value
- Does NOT compare CLI generated binary
- Missing: Density ARRAY tests (multiple densities in one binary)

**Missing tests:**
1. Density arrays: `--densities 2 4 8 16` (multiple in one binary)
2. All densities with CLI comparison
3. Full param combinations with density variations

---

## Fix Required

### Fix 1: Threshold Offsets in gui.py

**File:** gui.py
**Locations:** 
- Lines 338-341 (LP5)
- Lines 422-423 (LP4)

**Change LP4 section (lines 422-423):**
```python
# From:
dp_thresh_offset = 0xe0
ds_thresh_offset = 0xdc

# To (add dual channel handling):
dp_thresh_offset = 0xf0 if is_dual_channel else 0xe0
ds_thresh_offset = 0xec if is_dual_channel else 0xdc
```

**Change LP5 section (lines 340-341):**
```python
# From:
dp_thresh_offset = 0xf6 if is_dual_channel else 0xe6
ds_thresh_offset = 0xf2 if is_dual_channel else 0xe2

# To:
dp_thresh_offset = 0xf8 if is_dual_channel else 0xe8
ds_thresh_offset = 0xf4 if is_dual_channel else 0xe4
```

### Fix 2: Create Roundtrip Test

**File:** test_threshold.py (new)
**Test values:**
- dynamic_power_down_threshold = 111
- dynamic_self_refresh_threshold = 222
- zq_calibration_period = 555

**Test configs:** LP4 Single, LP4 Dual, LP5 Single, LP5 Dual

### Fix 3: Add CLI vs GUI Density Comparison

**File:** test_gui_params.py
**Options:**
- Option A: Modify test_all_densities() to add CLI comparison
- Option B: Add new test_density_arrays() for multi-density binaries

### Fix 4: Full Random Param Test with ALL GUI Params

**File:** test_gui_params.py

**Current Gap:**
- test_random_param_comparison() only tests: density (4,8,16), write_odt (1250,2500)
- periods: Only 2 fixed sets (4 values each), NOT random count
- Late fields: NOT tested at all
- Iterations: 10 × 2 = 20 tests only

**Required: FULL random for ALL params**

#### Complete Params List to Test:

| Category | Param | Valid Range | CLI Arg |
|----------|-------|------------|--------|
| **Timing** | periods | 1-4 values, random in range | positional |
| | dram_tck | 300-5000 ps | --dram-tck |
| | min_dram_tck | 200-3000 ps | --min-dram-tck |
| | write_odt_upto | 1250-10000 | --write-odt-upto |
| | read_dbi_upto | 1000-10000 | --read-dbi-upto |
| | write_dbi_upto | 1000-10000 | --write-dbi-upto |
| | read_lecc_upto | 500-2500 | --read-lecc-upto |
| | write_lecc_upto | 500-2500 | --write-lecc-upto |
| **LP4 specific** | wdqs-ctrl-mode | 0,1 | --wdqs-ctrl-mode |
| | variable-trrd | flag | --variable-trrd |
| | txsr-as-1st-ed | flag | --txsr-as-1st-ed |
| | rpste-upto | 625-2500 | --rpste-upto |
| | wpste-upto | 625-2500 | --wpste-upto |
| **LP5 specific** | wck-1to4-upto | 625-2500 | --wck-1to4-upto |
| | wck-always-on-from | 0-100 | --wck-always-on-from |
| | wck-always-on-upto | 314-1256 | --wck-always-on-upto |
| | nt-odt-upto | 625-2500 | --nt-odt-upto |
| | bg-mode-upto | 625-2500 | --bg-mode-upto |
| | wck-hf-upto | 625-2500 | --wck-hf-upto |
| | wck-pst1-upto | 625-2500 | --wck-pst1-upto |
| | wck-pst2-upto | 625-2500 | --wck-pst2-upto |
| | rdqs-pst1-upto | 625-2500 | --rdqs-pst1-upto |
| | rdqs-pst2-upto | 625-2500 | --rdqs-pst2-upto |
| **Orbit config** | density | LP4: 2,3,4,6,8,12,16 / LP5: 1,2,3,4,6,8,12,16,24,32 | --densities |
| | num_rank | 1,2 | --orbit-num-rank |
| | byte_mode | 0,1 | --orbit-byte-mode |
| | mixed | 0,1 | --orbit-mixed |
| | rank_interleaving | 0,1 | --orbit-rank-interleaving |
| | reboot_with_mrw | 0,1 | --orbit-reboot-with-mrw |
| | rfm_en | 0,1 | --orbit-rfm-en |
| | dsm_en | 0,1 | --orbit-dsm-en |
| | ca_odt | 0,1 | --orbit-ca-odt |
| **Late fields** | dynamic_power_down | 0,1 | --orbit-dynamic-power-down |
| | dynamic_power_down_threshold | 0-1000000 | --orbit-dynamic-power-down-threshold |
| | dynamic_self_refresh | 0,1 | --orbit-dynamic-self-refresh |
| | dynamic_self_refresh_threshold | 0-1000000 | --orbit-dynamic-self-refresh-threshold |
| | phy_low_power | 0,1 | --orbit-phy-low-power |
| | phy_idle_cnt_th | 0-100000 | --orbit-phy-idle-cnt-th |
| | periodic_training | 0,1 | --orbit-periodic-training |
| | periodic_training_period | 5000-50000 | --orbit-periodic-training-period |
| | temp_sensing | 0,1 | --orbit-temp-sensing |
| | temp_sensing_period | 5000-50000 | --orbit-temp-sensing-period |
| | zq_calibration_period | 10000-100000 | --orbit-zq-calibration-period |
| | t_refiab | 2000000-5000000 | --orbit-t-refiab |
| | t_refipb | 200000-600000 | --orbit-t-refipb |
| | t_zqcal | 500000-2000000 | --orbit-t-zqcal |
| **Pipe/Freq** | omc_freq_ratio | 1,2,4 | --omc-freq-ratio |
| | phy_freq_ratio | 1,2,4 | --phy-freq-ratio |
| | cpipe_depth | 1-8 | --cpipe-depth |
| | dpipe_depth | 1-8 | --dpipe-depth |
| **DFS** | dfs-lvl-t-ck-0 | 300-5000 | --dfs-lvl-t-ck-0 |
| | dfs-lvl-t-ck-1 | 300-5000 | --dfs-lvl-t-ck-1 |
| | dfs-lvl-t-ck-2 | 300-5000 | --dfs-lvl-t-ck-2 |

#### Implementation Changes:

1. **generate_random_params()** - FULL random for ALL params with random periods count

2. **build_cli_command()** - Add ALL CLI args for new params

3. **Increase iterations** (test_gui_params.py line 1703): from 10 to 100

**Verification:** With all params randomly varied, CLI and GUI binaries MUST match.

---

## Implementation Steps

### Step 1: Fix Threshold Offsets (gui.py)
1. Update LP4 offset handling (lines 422-423)
2. Update LP5 offset handling (lines 340-341)
3. Verify fix with roundtrip test

### Step 2: Create Threshold Roundtrip Test
1. Create test_threshold.py
2. Test dp=111, ds=222, zq=555 across 4 configs
3. Run tests and verify all pass

### Step 3: Add Density CLI vs GUI Comparison
1. Update test_all_densities() to include CLI comparison, OR
2. Create new test_density_arrays.py

### Step 4: Full Random Param Test with ALL GUI Params
1. Update generate_random_params() to use FULL random for ALL params (50+ params)
2. Add random periods count (1-4 values) with random values in valid range
3. Add ALL orbit config params, late field params, pipe/freq params
4. Update build_cli_command() to pass ALL new params to CLI
5. Increase iterations from 10 to 100 per DDR type
6. Run test_gui_params.py to verify CLI vs GUI match

---

## Verification

### After Fix 1 - Threshold Roundtrip Test:
```
test_threshold.py results:
LP4 Single: dp=111, ds=222, zq=555 ✓
LP4 Dual:   dp=111, ds=222, zq=555 ✓
LP5 Single: dp=111, ds=222, zq=555 ✓
LP5 Dual:   dp=111, ds=222, zq=555 ✓
```

### After Fix 3 - CLI vs GUI Density Comparison:
```
test_density_compat.py: 17/17 pass ✓
test_gui_params.py density tests: All pass with CLI compare ✓
```

---

## Dependencies

- Fix 1 must be completed BEFORE Fix 2 verification
- Fix 2 tests can be run independently
- Fix 3 requires understanding of how CLI --densities works