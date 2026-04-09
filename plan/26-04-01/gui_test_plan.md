# DDR Timing Table Generator GUI - Comprehensive Test Plan

## Overview

This plan covers comprehensive testing for the DDR Timing Table Generator GUI, including:
- Reference binary generation scripts
- ps/MHz toggle fix
- Button tests
- All density tests
- All timing field tests
- All orbit config tests

---

## Task 1: Generate Reference Binary Scripts

### 1.1 test_gen_lpddr4_bin.sh

Generates LPDDR4 reference binaries with `.ref.bin` suffix (no C comparison).

```bash
#!/bin/bash
set -e

ORBIT_DENSITY=4

echo "=== Generating LPDDR4 Reference Binaries ==="

# Single channel
echo "1. Generating LPDDR4 single channel..."
rm -f ddr_timing_table.bin
./gen_timing_params --dram-type lpddr4 --phy-name sphy-v9r8 --speed-bin 4266 --dq-width 16 \
    --orbit-config-density $ORBIT_DENSITY \
    --wdqs-ctrl-mode 1 --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-odt-upto 1250 \
    --cpipe-depth 1 --dpipe-depth 1 \
    --txsr-as-1st-ed --variable-trrd \
    --orbit-config-use-python --orbit-byte-mode 0 --orbit-mixed 0 --orbit-rank-interleaving 1 --orbit-num-rank 2 \
    471 938 1631 2500
cp ddr_timing_table.bin ddr_timing_table.lpddr4.single.ref.bin

# Dual channel
echo "2. Generating LPDDR4 dual channel..."
rm -f ddr_timing_table.bin
./gen_timing_params --dram-type lpddr4 --phy-name sphy-v9r8 --speed-bin 4266 --dq-width 16 \
    --orbit-config-density $ORBIT_DENSITY \
    --wdqs-ctrl-mode 1 --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-odt-upto 1250 \
    --cpipe-depth 1 --dpipe-depth 1 \
    --txsr-as-1st-ed --variable-trrd \
    --orbit-config-use-python --orbit-byte-mode 0 --orbit-mixed 0 --orbit-rank-interleaving 1 --orbit-num-rank 2 \
    --two-channel \
    471 938 1631 2500
cp ddr_timing_table.bin ddr_timing_table.lpddr4.dual.ref.bin

echo "=== Done ==="
```

### 1.2 test_gen_lpddr5_bin.sh

Generates LPDDR5 reference binaries with `.ref.bin` suffix (no C comparison).

```bash
#!/bin/bash
set -e

ORBIT_DENSITY=4

echo "=== Generating LPDDR5 Reference Binaries ==="

# Single channel
echo "1. Generating LPDDR5 single channel..."
rm -f ddr_timing_table.bin
./gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 --speed-bin 6400 --dq-width 16 \
    --orbit-config-density $ORBIT_DENSITY \
    --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-lecc-upto 625 --write-odt-upto 10000 \
    --cpipe-depth 1 --dpipe-depth 1 \
    --omc-freq-ratio 1 --phy-freq-ratio 1 --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 314 \
    --orbit-config-use-python --orbit-byte-mode 0 --orbit-mixed 0 --orbit-rank-interleaving 1 --orbit-num-rank 2 \
    314 418 556 2500
cp ddr_timing_table.bin ddr_timing_table.lpddr5.single.ref.bin

# Dual channel
echo "2. Generating LPDDR5 dual channel..."
rm -f ddr_timing_table.bin
./gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 --speed-bin 6400 --dq-width 16 \
    --orbit-config-density $ORBIT_DENSITY \
    --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 --write-lecc-upto 625 --write-odt-upto 10000 \
    --cpipe-depth 1 --dpipe-depth 1 \
    --omc-freq-ratio 1 --phy-freq-ratio 1 --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 314 \
    --orbit-config-use-python --orbit-byte-mode 0 --orbit-mixed 0 --orbit-rank-interleaving 1 --orbit-num-rank 2 \
    --two-channel \
    314 418 556 2500
cp ddr_timing_table.bin ddr_timing_table.lpddr5.dual.ref.bin

echo "=== Done ==="
```

---

## Task 2: Fix ps/MHz Toggle - Convert to ps (integer) Before Generate

### File: templates/gui.html

**Changes to `generate()` function:**

Add conversion logic to convert MHz values to ps (integer) before sending to CLI:

```javascript
async function generate() {
    const form = document.getElementById('paramsForm');
    const formData = new FormData(form);
    const params = {};
    
    for (let [key, value] of formData.entries()) {
        params[key] = value;
    }
    
    const checkboxes = form.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => {
        if (!cb.checked) params[cb.name] = 'false';
    });
    
    // ============================================================
    // FIX: Convert MHz values to ps before sending to CLI
    // ============================================================
    const isMHz = document.querySelector('input[name="timing-unit"]:checked')?.value === 'MHz';
    
    if (isMHz) {
        const fieldsToConvert = [
            'write-odt-upto', 'read-dbi-upto', 'write-dbi-upto',
            'read-lecc-upto', 'write-lecc-upto', 'wck-1to4-upto',
            'wck-always-on-from', 'wck-always-on-upto',
            'dfs-lvl-t-ck-0', 'dfs-lvl-t-ck-1', 'dfs-lvl-t-ck-2',
            'dram-tck', 'min-dram-tck',
            'periods-0', 'periods-1', 'periods-2', 'periods-3'
        ];
        
        fieldsToConvert.forEach(name => {
            const field = document.querySelector(`[name="${name}"]`);
            if (field && field.value) {
                const mhz = parseFloat(field.value);
                if (!isNaN(mhz) && mhz > 0) {
                    // Convert MHz to ps (integer), e.g., 2123MHz → 471ps
                    field.value = Math.round(1000000 / mhz);
                }
            }
        });
        
        // Reset toggle to ps mode
        document.querySelector('input[name="timing-unit"][value="ps"]').checked = true;
        
        // Update unit labels back to ps
        document.querySelectorAll('.unit-label').forEach(label => {
            label.textContent = 'ps';
        });
        
        // Re-extract form data after conversion
        const newFormData = new FormData(form);
        for (let [key, value] of newFormData.entries()) {
            params[key] = value;
        }
        checkboxes.forEach(cb => {
            if (!cb.checked) params[cb.name] = 'false';
        });
    }
    // ============================================================
    // END FIX
    // ============================================================
    
    const statusEl = document.getElementById('status');
    statusEl.className = 'status';
    statusEl.innerHTML = 'Generating...';
    
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        const result = await response.json();
        
        if (result.success) {
            statusEl.className = 'status success';
            statusEl.innerHTML = '<strong>Generated successfully!</strong><br><pre>' + result.message + '</pre>';
        } else {
            statusEl.className = 'status error';
            statusEl.innerHTML = '<strong>Error:</strong><br><pre>' + result.message + '</pre>';
        }
    } catch (e) {
        statusEl.className = 'status error';
        statusEl.innerHTML = '<strong>Error:</strong> ' + e.message;
    }
}
```

**List of timing fields to convert:**
1. write-odt-upto
2. read-dbi-upto
3. write-dbi-upto
4. read-lecc-upto
5. write-lecc-upto
6. wck-1to4-upto
7. wck-always-on-from
8. wck-always-on-upto
9. dfs-lvl-t-ck-0
10. dfs-lvl-t-ck-1
11. dfs-lvl-t-ck-2
12. dram-tck
13. min-dram-tck
14. periods-0, periods-1, periods-2, periods-3

---

## Task 3: Button Tests (test_button_*)

### test_button_load_binary()
- Load reference binary via `/analyze` endpoint
- Verify extracted params (dram_type, density, etc.)

### test_button_save_json()
- Extract form params
- Verify JSON structure has required fields

### test_button_load_json()
- Create JSON file with params
- Load via /generate endpoint
- Verify binary generated

### test_button_generate()
- Call `/generate` with valid params
- Verify binary created successfully

---

## Task 4: Load-Modify-Generate-Compare Test

### test_load_modify_generate_compare()
1. Load reference binary via `/analyze` → extract params
2. Modify params: density 4→8, num-rank 2→1
3. Generate binary via `/generate` with modified params
4. Generate reference binary via CLI with same modified params
5. Compare timing table sections (first 0x800 bytes)

---

## Task 5: All Densities Test

### test_all_densities()

| DDR Type | Densities to Test |
|----------|-------------------|
| LPDDR4 | 1, 2, 3, 4, 6, 8, 12, 16, 32 (9 tests) |
| LPDDR5 | 1, 2, 3, 4, 6, 8, 12, 16, 24, 32 (10 tests) |

**Total: 19 density tests**

---

## Task 6: All Timing Fields Test

### test_all_timing_fields()

Each field tested with ps value AND MHz value:

| Field | ps Value | MHz Value | DDR Type |
|-------|----------|-----------|----------|
| write-odt-upto | 1250 | 800 | LPDDR4 |
| write-odt-upto | 10000 | 100 | LPDDR5 |
| read-dbi-upto | 10000 | 100 | Both |
| write-dbi-upto | 10000 | 100 | Both |
| read-lecc-upto | 625 | 1600 | Both |
| write-lecc-upto | 625 | 1600 | Both |
| wck-1to4-upto | 625 | 1600 | LPDDR5 |
| wck-always-on-upto | 314 | 3185 | LPDDR5 |
| dram-tck | 471 | 2123 | LPDDR4 |
| dram-tck | 1256 | 796 | LPDDR5 |
| min-dram-tck | 314 | 3185 | Both |
| dfs-lvl-t-ck-0 | 938 | 1066 | Both |
| dfs-lvl-t-ck-1 | 1631 | 613 | Both |
| dfs-lvl-t-ck-2 | 2500 | 400 | Both |

**Method for each test:**
1. Set base params (LPDDR4 single or LPDDR5 single)
2. Modify one timing field to ps value
3. Generate via GUI
4. Generate via CLI with same params
5. Compare timing table sections

**Total: 26+ timing field tests**

---

## Task 7: All Orbit Config Tests

### test_all_orbit_params()

| Parameter | Values | DDR Type |
|-----------|--------|----------|
| byte-mode | 0, 1 | Both |
| mixed | 0, 1 | Both |
| rfm-en | 0, 1 | Both |
| dsm-en | 0, 1 | LPDDR5 only |
| ca-odt | 0, 1 | Both |
| num-rank | 1, 2 | Both |
| rank-interleaving | 0, 1 | Both |
| reboot-with-mrw | 0, 1 | Both |

**Total: ~15 orbit config tests**

---

## Task 8: GUI vs CLI Comparison Test

### test_gui_vs_cli()

1. Generate via GUI with specific params
2. Generate via CLI with exact same params
3. Compare full timing table section
4. Verify exact match

---

## Summary of Test Functions

| # | Function | Test Cases |
|---|----------|------------|
| 1 | `test_button_load_binary()` | 1 |
| 2 | `test_button_save_json()` | 1 |
| 3 | `test_button_load_json()` | 1 |
| 4 | `test_button_generate()` | 1 |
| 5 | `test_load_modify_generate_compare()` | 1 |
| 6 | `test_all_densities()` | 19 (9 LPDDR4 + 10 LPDDR5) |
| 7 | `test_all_timing_fields()` | 26+ |
| 8 | `test_all_orbit_params()` | ~15 |
| 9 | `test_gui_vs_cli()` | 1 |

**Total: ~65+ new test cases**

---

## Files to Create/Modify

| Task | Files |
|------|-------|
| 1. Reference scripts | New: `test_gen_lpddr4_bin.sh`, `test_gen_lpddr5_bin.sh` |
| 2. ps/MHz fix | Modify: `templates/gui.html` |
| 3-9. Tests | Modify: `test_gui_params.py` |

---

## Implementation Order

1. Create reference binary scripts (test_gen_lpddr4_bin.sh, test_gen_lpddr5_bin.sh)
2. Fix ps/MHz toggle in gui.html
3. Run reference scripts to generate .ref.bin files
4. Add all test functions to test_gui_params.py
5. Run tests and verify
6. Create implementation report

---

## Verification Commands

```bash
# Generate reference binaries
./test_gen_lpddr4_bin.sh
./test_gen_lpddr5_bin.sh

# Start GUI
python3 gui.py &

# Run tests
python3 test_gui_params.py

# Stop GUI
pkill -f "python3 gui.py"
```
