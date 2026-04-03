# DDR Timing Table Generator - Test Documentation

## Part 1: What Was Done So Far

### Goal
Fix bugs in the DDR Timing Table Generator GUI where loading a binary showed incorrect values, and add comprehensive full cycle tests. Also remove ddr_config.h generation feature that is no longer needed.

### Discoveries

1. **LECC Parsing Bug**: The binary parsing logic used `if flag and t_ck > value` which caused false positives because garbage values like 144 were "truthy" in Python. Fixed by changing to `if flag > 0 and t_ck > value`.

2. **LPDDR5 Binary Generation Issue**: The reference binary `ddr_timing_table.lpddr5.dual.ref.bin` has corrupted timing data - expected periods `314 418 556 2500` but only `1256` is valid. This is a binary generation bug, not a parsing issue.

3. **Correct Offsets Found**:
   - cpipe_depth: 0x14 (was 0x30)
   - dpipe_depth: 0x16 (was 0x32)
   - rank_interleaving: 0x1e (was 0x3a)
   - num_rank: 0x20 (was 0x3c)
   - Timing entry size: 0x128 (296 bytes), not 188

4. **LECC/DBI/ODT flags are at offsets**: write_odt=158, write_dbi=160, read_dbi=161, read_link_parity=179, write_link_parity=180

### Accomplished

1. **Removed ddr_config.h generation** - Removed checkbox from gui.html and generation code from gui.py
2. **Fixed LECC parsing logic** - Changed `flag` to `flag > 0` in gui.py
3. **Added test_orbit_params_full_cycle()** - 10 test cases for orbit params
4. **Added test_timing_params_full_cycle()** - 6 test cases for timing params
5. **Added test_lpddr5_bin_generation()** - 2 test cases to catch LPDDR5 generation issues
6. **Updated main()** to call new tests

### Next Steps

1. Run full test suite to verify: `python3 test_gui_params.py`
2. Investigate and fix LPDDR5 binary generation issue (timing entries are corrupted)
3. Regenerate reference binaries after fixing generation issues
4. The new tests will catch generation bugs - they verify that generated binaries can be correctly loaded and parsed back to matching values

---

## Part 2: Detailed Test Function Workflows

### Prerequisites

1. **Start GUI Server**: `python3 gui.py` (runs on port 5000)
2. **Verify Server**: Test with `curl http://localhost:5000/`

---

### 1. test_orbit_params_full_cycle() - Lines 2009-2149

**Purpose**: Verify orbit params survive the generate→load→compare cycle

**Test Cases** (10 total):

| # | DRAM | Description | Input Params | Expected |
|---|------|-------------|--------------|----------|
| 1 | lpddr4 | rank_int_1_num_rank_2 | orbit-rank-interleaving=true, orbit-num-rank=2 | rank_interleaving=1, num_rank=2 |
| 2 | lpddr4 | rank_int_0_num_rank_1 | orbit-rank-interleaving=false, orbit-num-rank=1 | rank_interleaving=0, num_rank=1 |
| 3 | lpddr4 | byte_mode_1 | orbit-byte-mode=1 | byte_mode=1 |
| 4 | lpddr4 | mixed_1 | orbit-mixed=1 | mixed=1 |
| 5 | lpddr4 | rfm_en_1 | orbit-rfm-en=true | rfm_en=1 |
| 6 | lpddr4 | reboot_mrw_1 | orbit-reboot-with-mrw=true | reboot_with_mrw=1 |
| 7 | lpddr5 | dsm_en_1 | orbit-dsm-en=true | dsm_en=1 |
| 8 | lpddr5 | ca_odt_1 | orbit-ca-odt=true | ca_odt=1 |
| 9 | lpddr4 | dual_channel | two-channel=true | two_channel=1 |
| 10 | lpddr5 | dual_channel | two-channel=true | two_channel=1 |

**Step-by-Step Workflow**:

#### Step 1: Define Test Configuration
- Select test case from table above
- Build params dict with specific orbit settings
- Define expected dict with key-value pairs to verify

#### Step 2: Generate Binary with Specific Orbit Params
```python
# Example: Test Case #1 - rank_interleaving=true, num_rank=2
params = {
    'dram-type': 'lpddr4',
    'orbit-config-density': '4',
    'periods': '471 938 1631 2500',
    'cpipe-depth': '1',
    'dpipe-depth': '1',
    'orbit-rank-interleaving': 'true',    # INPUT
    'orbit-num-rank': '2',                # INPUT
    'orbit-config-use-python': 'true'
}
expected = {'rank_interleaving': 1, 'num_rank': 2}  # EXPECTED OUTPUT
```

#### Step 3: Call Generate API
```python
conn = http.client.HTTPConnection('localhost', 5000)
headers = {'Content-Type': 'application/json'}
conn.request('POST', '/generate', json.dumps(params), headers)
resp = conn.getresponse()
result = json.loads(resp.read().decode())
# Creates: ddr_timing_table.bin
```

#### Step 4: Analyze/Load the Binary
```python
body = json.dumps({'file_path': 'ddr_timing_table.bin', 'dram_type_override': 'auto'})
conn.request('POST', '/analyze', body, headers)
resp = conn.getresponse()
an_result = json.loads(resp.read().decode())
# Returns: {'success': True, 'data': {'orbit': {'rank_interleaving': 1, 'num_rank': 2, ...}}}
```

#### Step 5: Compare Expected vs Actual
```python
mismatches = []
for key, exp_val in expected.items():
    actual = an_result['data']['orbit'].get(key)
    if actual != exp_val:
        mismatches.append(f"{key}: expected={exp_val}, actual={actual}")

if mismatches:
    print(f"FAIL: {desc} - {', '.join(mismatches)}")
else:
    print(f"PASS: {desc}")
```

#### Step 6: Record Result
- Append (desc, True/False, msg) to results list

---

### 2. test_timing_params_full_cycle() - Lines 2154-2252

**Purpose**: Verify timing params survive the generate→load→compare cycle

**Test Cases** (6 total):

| # | DRAM | Description | Input Params | Expected |
|---|------|-------------|--------------|----------|
| 1 | lpddr4 | write_odt_1250 | write-odt-upto=1250 | write_odt_upto=1250 |
| 2 | lpddr4 | read_dbi_10000 | read-dbi-upto=10000 | read_dbi_upto=10000 |
| 3 | lpddr4 | write_dbi_10000 | write-dbi-upto=10000 | write_dbi_upto=10000 |
| 4 | lpddr4 | write_odt_2500 | write-odt-upto=2500 | write_odt_upto=2500 |
| 5 | lpddr5 | write_lecc_625 | write-lecc-upto=625 | write_lecc_upto=625 |
| 6 | lpddr5 | read_lecc_625 | read-lecc-upto=625 | read_lecc_upto=625 |

**Step-by-Step Workflow**:

#### Step 1: Define Test Configuration
- Select test case from table above
- Build params dict with specific timing value
- Define expected dict with timing key to verify

#### Step 2: Generate Binary with Specific Timing Value
```python
# Example: Test Case #1 - write-odt-upto=1250
params = {
    'dram-type': 'lpddr4',
    'orbit-config-density': '4',
    'periods': '471 938 1631 2500',
    'cpipe-depth': '1',
    'dpipe-depth': '1',
    'write-odt-upto': '1250',         # INPUT (picoseconds)
    'orbit-config-use-python': 'true'
}
expected = {'write_odt_upto': 1250}  # EXPECTED OUTPUT
```

#### Step 3: Call Generate API
```python
conn = http.client.HTTPConnection('localhost', 5000)
headers = {'Content-Type': 'application/json'}
conn.request('POST', '/generate', json.dumps(params), headers)
resp = conn.getresponse()
result = json.loads(resp.read().decode())
# Creates: ddr_timing_table.bin
```

#### Step 4: Analyze/Load the Binary
```python
body = json.dumps({'file_path': 'ddr_timing_table.bin', 'dram_type_override': 'auto'})
conn.request('POST', '/analyze', body, headers)
resp = conn.getresponse()
an_result = json.loads(resp.read().decode())
# Returns: {'success': True, 'data': {'timing': {'write_odt_upto': 1250, ...}}}
```

#### Step 5: Compare Expected vs Actual
```python
mismatches = []
for key, exp_val in expected.items():
    actual = an_result['data']['timing'].get(key)
    if actual != exp_val:
        mismatches.append(f"{key}: expected={exp_val}, actual={actual}")

if mismatches:
    print(f"FAIL: {desc} - {', '.join(mismatches)}")
else:
    print(f"PASS: {desc}")
```

#### Step 6: Record Result
- Append (desc, True/False, msg) to results list

---

### 3. test_lpddr5_bin_generation() - Lines 2257-2343

**Purpose**: Verify LPDDR5 binary has valid timing entries (not corrupted)

**Test Cases**:

| # | Description | Expected |
|---|-------------|----------|
| 1 | lpddr5_single | periods="314 418 556 2500", two_channel=0 |
| 2 | lpddr5_dual | periods="314 418 556 2500", two_channel=1 |

**Step-by-Step Workflow**:

#### Step 1: Define Test Configuration
- Select test case (single or dual channel)
- Build params dict for LPDDR5
- Define expected periods and two_channel flag

#### Step 2: Generate LPDDR5 Binary
```python
# Example: Test Case #1 - lpddr5_single
params = {
    'dram-type': 'lpddr5',
    'orbit-config-density': '4',
    'periods': '314 418 556 2500',
    'cpipe-depth': '1',
    'dpipe-depth': '1',
    'orbit-config-use-python': 'true',
}
expected_periods = "314 418 556 2500"
expected_two_ch = 0
```

#### Step 3: Call Generate API
```python
conn = http.client.HTTPConnection('localhost', 5000)
headers = {'Content-Type': 'application/json'}
conn.request('POST', '/generate', json.dumps(params), headers)
resp = conn.getresponse()
result = json.loads(resp.read().decode())
# Creates: ddr_timing_table.bin
```

#### Step 4: Analyze the Binary
```python
body = json.dumps({'file_path': 'ddr_timing_table.bin', 'dram_type_override': 'auto'})
conn.request('POST', '/analyze', body, headers)
resp = conn.getresponse()
an_result = json.loads(resp.read().decode())
# Returns: {'data': {'basic': {'periods': '314 418 556 2500'}, 'two_channel': 0}}
```

#### Step 5: Verify Periods Match Expected
```python
actual_periods = an_result['data']['basic'].get('periods', '')
two_ch = an_result['data'].get('two_channel', 0)

mismatches = []
if actual_periods != expected_periods:
    mismatches.append(f"periods: expected={expected_periods}, actual={actual_periods}")
if two_ch != expected_two_ch:
    mismatches.append(f"two_channel: expected={expected_two_ch}, actual={two_ch}")
```

#### Step 6: Verify Binary Raw Data (Direct Read)
```python
import struct

with open('ddr_timing_table.bin', 'rb') as f:
    data = f.read()

entry_size = 0x128  # 296 bytes
valid_t_ck_values = []

# Check timing entries 0-7
for i in range(8):
    offset = i * entry_size
    if offset + 8 > len(data):
        break
    
    # Read t_ck at offset + 4
    t_ck = struct.unpack('<I', data[offset+4:offset+8])[0]
    
    # Verify valid range: 300 <= t_ck <= 5000
    if 300 <= t_ck <= 5000:
        valid_t_ck_values.append(t_ck)

# Check LECC flags are valid (0 or 1, not garbage like 144)
for i in range(min(4, len(valid_t_ck_values))):
    offset = i * entry_size
    write_lecc = data[offset + 180]  # write_link_parity
    read_lecc = data[offset + 179]   # read_link_parity
    
    if write_lecc > 1 or read_lecc > 1:
        mismatches.append(f"LECC flags invalid at entry {i}: write={write_lecc}, read={read_lecc}")
```

#### Step 7: Record Result
```python
if mismatches:
    print(f"FAIL: {desc} - {', '.join(mismatches)}")
    results.append((desc, False, "; ".join(mismatches)))
else:
    print(f"PASS: {desc}")
    results.append((desc, True, "OK"))
```

---

### 4. test_parse_offset_comparison() - Lines 1874-2004

**Purpose**: Verify GUI parsing uses correct binary offsets

**Offsets Verified**:

| Field | Offset (hex) | struct format |
|-------|-------------|---------------|
| cpipe_depth | 0x14 | `<H` (uint16) |
| dpipe_depth | 0x16 | `<H` |
| omc_freq_ratio | 0x14 | `<H` |
| phy_freq_ratio | 0x12 | `<H` |
| density (LPDDR4) | 0x1c | `<H` |
| density (LPDDR5) | 0x24 | `<H` |
| rank_interleaving | 0x1e | `<H` |
| num_rank | 0x20 | `<H` |
| density_code | 0x78/0x80 | `<I` (uint32) |

**Step-by-Step Workflow**:

#### Step 1: Analyze Binary via GUI
```python
body = json.dumps({'file_path': bin_file, 'dram_type_override': 'auto'})
conn.request('POST', '/analyze', body, headers)
resp = conn.getresponse()
an_result = json.loads(resp.read().decode())
# Returns: {'data': {'pipe': {...}, 'orbit': {...}, 'timing': {...}}}
```

#### Step 2: Read Binary Directly
```python
import struct

with open(bin_file, 'rb') as f:
    binary_data = f.read()

orbit_offset = 0x800  # Base offset for orbit struct
```

#### Step 3: Compare cpipe_depth
```python
gui_cpipe = an_result['data']['pipe'].get('cpipe_depth', 0)
bin_cpipe = struct.unpack('<H', binary_data[orbit_offset + 0x14:orbit_offset + 0x16])[0]

if gui_cpipe != bin_cpipe:
    mismatches.append(f"cpipe_depth: GUI={gui_cpipe}, Binary@0x814={bin_cpipe}")
```

#### Step 4: Compare dpipe_depth
```python
gui_dpipe = an_result['data']['pipe'].get('dpipe_depth', 0)
bin_dpipe = struct.unpack('<H', binary_data[orbit_offset + 0x16:orbit_offset + 0x18])[0]

if gui_dpipe != bin_dpipe:
    mismatches.append(f"dpipe_depth: GUI={gui_dpipe}, Binary@0x816={bin_dpipe}")
```

#### Step 5: Compare omc_freq_ratio
```python
gui_omc = an_result['data']['pipe'].get('omc_freq_ratio', 0)
bin_omc = struct.unpack('<H', binary_data[orbit_offset + 0x14:orbit_offset + 0x16])[0]

if gui_omc != bin_omc:
    mismatches.append(f"omc_freq_ratio: GUI={gui_omc}, Binary@0x814={bin_omc}")
```

#### Step 6: Compare phy_freq_ratio
```python
gui_phy = an_result['data']['pipe'].get('phy_freq_ratio', 0)
bin_phy = struct.unpack('<H', binary_data[orbit_offset + 0x12:orbit_offset + 0x14])[0]

if gui_phy != bin_phy:
    mismatches.append(f"phy_freq_ratio: GUI={gui_phy}, Binary@0x812={bin_phy}")
```

#### Step 7: Compare density
```python
gui_density = an_result['data']['orbit'].get('density', 0)
density_offset = 0x1c if not is_lpddr5 else 0x24
bin_density = struct.unpack('<H', binary_data[orbit_offset + density_offset:orbit_offset + density_offset + 2])[0]

if gui_density != bin_density:
    mismatches.append(f"density: GUI={gui_density}, Binary@{density_offset:#x}={bin_density}")
```

#### Step 8: Compare rank_interleaving
```python
gui_rank_int = an_result['data']['orbit'].get('rank_interleaving', 0)
bin_rank_int = struct.unpack('<H', binary_data[orbit_offset + 0x1e:orbit_offset + 0x20])[0]

if gui_rank_int != bin_rank_int:
    mismatches.append(f"rank_interleaving: GUI={gui_rank_int}, Binary@0x81e={bin_rank_int}")
```

#### Step 9: Compare num_rank
```python
gui_num_rank = an_result['data']['orbit'].get('num_rank', 0)
bin_num_rank = struct.unpack('<H', binary_data[orbit_offset + 0x20:orbit_offset + 0x22])[0]

if gui_num_rank != bin_num_rank:
    mismatches.append(f"num_rank: GUI={gui_num_rank}, Binary@0x820={bin_num_rank}")
```

#### Step 10: Compare timing values from timing table
```python
entry_size = 188
gui_write_odt = an_result['data']['timing'].get('write_odt_upto', 0)
gui_read_dbi = an_result['data']['timing'].get('read_dbi_upto', 0)
gui_write_dbi = an_result['data']['timing'].get('write_dbi_upto', 0)

# Parse from binary timing table
bin_write_odt = 0
bin_read_dbi = 0
bin_write_dbi = 0

for i in range(8):
    offset = i * entry_size
    if offset + 188 > len(binary_data):
        break
    
    t_ck = struct.unpack('<I', binary_data[offset+4:offset+8])[0]
    if t_ck == 0 or t_ck > 10000:
        continue
    
    # IMPORTANT: Use flag > 0, not just flag
    if binary_data[offset + 158] > 0 and t_ck > bin_write_odt:
        bin_write_odt = t_ck
    if binary_data[offset + 161] > 0 and t_ck > bin_read_dbi:
        bin_read_dbi = t_ck
    if binary_data[offset + 160] > 0 and t_ck > bin_write_dbi:
        bin_write_dbi = t_ck

if gui_write_odt != bin_write_odt:
    mismatches.append(f"write_odt_upto: GUI={gui_write_odt}, Binary={bin_write_odt}")
# ... similar for read_dbi, write_dbi
```

---

### 5. test_parameters() - Lines 231-634

**Purpose**: Test all basic GUI parameter combinations

**Test Cases**: 16 test cases covering various DRAM types, densities, and configurations

**Step-by-Step Workflow**:

#### Step 1: Define Test Parameters List
```python
test_params = [
    # LPDDR4 single channel
    {
        'dram-type': 'lpddr4',
        'dq-width': '16',
        'orbit-config-density': '4',
        'periods': '471 938 1631 2500',
        'dram-tck': '471',
        'cpipe-depth': '1',
        'dpipe-depth': '1',
        'wdqs-ctrl-mode': '1',
        'read-dbi-upto': '10000',
        'write-dbi-upto': '10000',
        'write-odt-upto': '1250',
        'txsr-as-1st-ed': 'true',
        'variable-trrd': 'true',
        'orbit-config-use-python': 'true',
        'orbit-byte-mode': '0',
        'orbit-mixed': '0',
        'orbit-rank-interleaving': 'true',
        'orbit-num-rank': '2',
    },
    # LPDDR5 single channel
    {
        'dram-type': 'lpddr5',
        'orbit-config-density': '4',
        'periods': '314 418 556 2500',
        'dram-tck': '1256',
        # ... more params
    },
    # ... 14 more test cases
]
```

#### Step 2: Loop Through Each Test Case
```python
for i, params in enumerate(test_params):
    print(f"Test {i+1}/{len(test_params)}: {params.get('dram-type')}")
```

#### Step 3: Generate Binary
```python
conn = http.client.HTTPConnection('localhost', 5000)
headers = {'Content-Type': 'application/json'}
conn.request('POST', '/generate', json.dumps(params), headers)
resp = conn.getresponse()
gen_result = json.loads(resp.read().decode())

if not gen_result.get('success'):
    print(f"ERROR: {gen_result.get('message')}")
    results.append((i, False, gen_result.get('message')))
    continue
```

#### Step 4: Copy to Temp File
```python
temp_bin = f'/tmp/test_params_{i}.bin'
shutil.copy('ddr_timing_table.bin', temp_bin)
```

#### Step 5: Analyze Binary
```python
body = json.dumps({'file_path': temp_bin, 'dram_type_override': 'auto'})
conn.request('POST', '/analyze', body, headers)
resp = conn.getresponse()
an_result = json.loads(resp.read().decode())

if not an_result.get('success'):
    print(f"ERROR: {an_result.get('message')}")
    results.append((i, False, an_result.get('message')))
    continue
```

#### Step 6: Extract Key Values
```python
test_dram_type = params.get('dram-type')
test_density = params.get('orbit-config-density') or params.get('density') or '16'

analyzed = an_result.get('data', {})
```

#### Step 7: Compare with Input
```python
mismatches = []

# Compare dram_type
if test_dram_type and test_dram_type != analyzed.get('basic', {}).get('dram_type'):
    mismatches.append(f"dram_type: {test_dram_type} vs {analyzed.get('basic', {}).get('dram_type')}")

# Compare density
expected = int(test_density)
actual = analyzed.get('orbit', {}).get('density', 0)
if expected != actual:
    mismatches.append(f"density: {expected} vs {actual}")
```

#### Step 8: Record Result
```python
if mismatches:
    print(f"MISMATCH: {mismatches}")
    results.append((i, False, str(mismatches)))
else:
    print(f"PASS")
    results.append((i, True, "OK"))

# Clean up temp file
if os.path.exists(temp_bin):
    os.remove(temp_bin)
```

---

### 6. test_all_densities() - Lines 1106-1212

**Purpose**: Test all supported densities for both DDR types

**Densities**:
- LPDDR4: 2, 3, 4, 6, 8, 12, 16 (7 tests)
- LPDDR5: 1, 2, 3, 4, 6, 8, 12, 16, 24, 32 (10 tests)

**Step-by-Step Workflow**:

#### Step 1: Define Density Lists
```python
lpddr4_densities = [2, 3, 4, 6, 8, 12, 16]
lpddr5_densities = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
```

#### Step 2: Test LPDDR4 Densities
```python
for density in lpddr4_densities:
    params = {
        'dram-type': 'lpddr4',
        'orbit-config-density': str(density),
        'periods': '471 938 1631 2500',
        'dram-tck': '471',
        'cpipe-depth': '1',
        'dpipe-depth': '1',
        'wdqs-ctrl-mode': '1',
        'read-dbi-upto': '10000',
        'write-dbi-upto': '10000',
        'write-odt-upto': '1250',
        'txsr-as-1st-ed': 'true',
        'variable-trrd': 'true',
        'orbit-config-use-python': 'true',
        'orbit-byte-mode': '0',
        'orbit-mixed': '0',
        'orbit-rank-interleaving': 'true',
        'orbit-num-rank': '2',
    }
```

#### Step 3: Generate and Analyze
```python
gen_result = generate_binary(params)
if not gen_result.get('success'):
    results.append((f"lpddr4_d{density}", False, gen_result.get('message')))
    continue

an_result = analyze_binary('ddr_timing_table.bin')
actual_density = an_result.get('data', {}).get('orbit', {}).get('density', 0)
```

#### Step 4: Verify Density
```python
if actual_density == density:
    results.append((f"lpddr4_d{density}", True, "OK"))
else:
    results.append((f"lpddr4_d{density}", False, f"Expected {density}, got {actual_density}"))
```

#### Step 5: Repeat for LPDDR5
- Same steps with LPDDR5 params and density list

---

### 7. test_all_timing_fields() - Lines 1219-1298

**Purpose**: Test random timing values in valid ranges

**Valid Ranges** (picoseconds):

| Field | Min | Max |
|-------|-----|-----|
| dram-tck | 300 | 5000 |
| min-dram-tck | 200 | 3000 |
| write-odt-upto | 1250 | 10000 |
| read-dbi-upto | 1000 | 10000 |
| write-dbi-upto | 1000 | 10000 |
| read-lecc-upto | 500 | 2500 |
| write-lecc-upto | 500 | 2500 |
| wck-1to4-upto | 625 | 2500 |
| wck-always-on-upto | 314 | 1256 |
| dfs-lvl-t-ck-0 | 500 | 3000 |
| dfs-lvl-t-ck-1 | 500 | 3000 |
| dfs-lvl-t-ck-2 | 500 | 5000 |

**Step-by-Step Workflow**:

#### Step 1: Define Timing Fields and Ranges
```python
TIMING_RANGES = {
    'dram-tck': (300, 5000),
    'min-dram-tck': (200, 3000),
    'write-odt-upto': (1250, 10000),
    'read-dbi-upto': (1000, 10000),
    'write-dbi-upto': (1000, 10000),
    'read-lecc-upto': (500, 2500),
    'write-lecc-upto': (500, 2500),
    'wck-1to4-upto': (625, 2500),
    'wck-always-on-upto': (314, 1256),
    'dfs-lvl-t-ck-0': (500, 3000),
    'dfs-lvl-t-ck-1': (500, 3000),
    'dfs-lvl-t-ck-2': (500, 5000),
}

timing_tests = [
    ('dram-tck', 'lpddr4', 471),
    ('dram-tck', 'lpddr5', 1256),
    ('min-dram-tck', 'both', 314),
    ('write-odt-upto', 'lpddr4', 1250),
    ('write-odt-upto', 'lpddr5', 10000),
    # ... more fields
]
```

#### Step 2: Loop Through Fields and Iterations
```python
random.seed(42)  # For reproducibility

for field, dram_type, default_val in timing_tests:
    min_val, max_val = TIMING_RANGES[field]
    
    for iteration in range(10):
        test_val = random.randint(min_val, max_val)
```

#### Step 3: Test for LPDDR4 (if applicable)
```python
if dram_type == 'lpddr4' or dram_type == 'both':
    params = get_lpddr4_params()
    params[field] = str(test_val)
    gen_result = generate_binary(params)
    
    if gen_result.get('success'):
        results.append((f"{field}_{test_val}_lpddr4", True, "OK"))
    else:
        results.append((f"{field}_{test_val}_lpddr4", False, gen_result.get('message')))
```

#### Step 4: Test for LPDDR5 (if applicable)
```python
if dram_type == 'lpddr5' or dram_type == 'both':
    params = get_lpddr5_params()
    params[field] = str(test_val)
    gen_result = generate_binary(params)
    
    if gen_result.get('success'):
        results.append((f"{field}_{test_val}_lpddr5", True, "OK"))
    else:
        results.append((f"{field}_{test_val}_lpddr5", False, gen_result.get('message')))
```

---

## Execution Order

From `main()` function (line 2348):

1. `test_parameters()` - 16 tests
2. `test_reference_binaries()` - 2 tests
3. `test_ps_mhz_toggle()` - 1 test
4. `test_button_load_binary()` - 2 tests
5. `test_button_save_json()` - 1 test
6. `test_button_load_json()` - 1 test
7. `test_button_generate()` - 1 test
8. `test_load_modify_generate_compare()` - 1 test
9. `test_all_densities()` - 17 tests
10. `test_all_timing_fields()` - 130+ tests
11. `test_all_orbit_params()` - 11 tests
12. `test_gui_vs_cli()` - 2 tests
13. `test_random_param_comparison()` - 20 tests
14. `test_dual_channel()` - 2 tests
15. `test_parse_offset_comparison()` - 2 tests
16. `test_orbit_params_full_cycle()` - 10 tests (NEW)
17. `test_timing_params_full_cycle()` - 6 tests (NEW)
18. `test_lpddr5_bin_generation()` - 2 tests (NEW)

**Total**: ~260+ test cases

---

## Key Files to Check During Debugging

| File | Purpose |
|------|---------|
| `gui.py:450-500` | Binary parsing offsets |
| `lpddr5_config.py` | LPDDR5 timing generation |
| `timing.py` | Timing table generation |
| `test_gui_params.py:2009-2343` | Full cycle tests |

---

## To Run Tests

```bash
# 1. Start GUI server (in terminal 1)
python3 gui.py

# 2. Run tests (in terminal 2)
python3 test_gui_params.py
```

---

## Expected Issues to Investigate

1. **test_lpddr5_bin_generation()** - May fail due to corrupted timing entries in LPDDR5 binary
2. **test_orbit_params_full_cycle()** - May have parsing issues for some orbit params
3. **test_timing_params_full_cycle()** - May show mismatches between generated and loaded values