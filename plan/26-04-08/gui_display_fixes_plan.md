# GUI Display Fixes Implementation Plan - 2026-04-08

## Issues Identified

### Issue 1: Numeric fields not visible after loading binary

**Problem**: When loading binary, the toggle functions (`toggleZqCalibration`, `toggleDynamicPowerDown`, etc.) are not called. This causes numeric fields like `dynamic-power-down-threshold`, `zq-calibration-period` to remain hidden even when their associated checkboxes are checked.

**Root Cause**: The `fillOrbitConfig()` function populates values but doesn't trigger the toggle functions that control field visibility based on checkbox state.

---

### Issue 2: Non-parseable fields warning not displayed

**Problem**: 17 fields are generated at runtime (not stored in binary), but there's no warning when loading binary to inform users these fields cannot be parsed.

**Non-parseable fields**:
- LP4 specific: variable-trrd, txsr-as-1st-ed
- LP5 specific: enhanced-nt-odt, wck-*, rdqs-*, nt-odt-upto, bg-mode-upto
- Common: wire-length

**Display location**: Status div (bottom of page, same as generate logs)

**Display format**: Grouped by category (LP4, LP5, Timing, Common)

---

### Issue 3: Parsed params not visible in analysis modal

**Problem**: Users want to see timing params parsed from binary (gen_timing_params lines 496-542), NOT the GUI params.

**What to show** (3 sections):
1. **Per-Entry Params** (table: rows=params, cols=entries) - only enabled entries
2. **Common Params** (same for all entries) - displayed once
3. **Density-Dependent Params** (for selected density) - displayed once

**Entry Enable Check**: Use OR logic - entry is enabled if ANY of these flags > 0:
- write_odt (+0x10A)
- write_dbi (+0x10C)
- read_dbi (+0x10D)
- read_link_parity (+0x11F) - LP5 only
- write_link_parity (+0x120) - LP5 only

---

## Implementation Plan

### Issue 1 Fix: Call toggle functions after binary load

**File**: `templates/gui.html`

**Location**: In `fillGuiFromAnalysis()` function, after `fillOrbitConfig()` completes (around line 900)

**Code to add**:
```javascript
// Call toggle functions to show/hide dependent numeric fields
toggleZqCalibration();
togglePeriodicTraining();
toggleTempSensing();
toggleDynamicPowerDown();
toggleDynamicSelfRefresh();
togglePhyLowPower();
```

---

### Issue 2 Fix: Non-parseable fields warning in status div

**File**: `templates/gui.html`

**Location**: In `analyzeBinaryFile()` function, after successful load (around line 815)

**Code to add**:
```javascript
if (result.data.orbit.non_parseable_fields?.length > 0) {
    const fields = result.data.orbit.non_parseable_fields;
    const lp4 = fields.filter(f => ['variable-trrd','txsr-as-1st-ed'].includes(f));
    const lp5 = fields.filter(f => ['enhanced-nt-odt','wck-always-on-from','wck-always-on-upto','wck-1to4-upto','wck-hf-upto','wck-pst1-upto','wck-pst2-upto','rdqs-pst1-upto','rdqs-pst2-upto','nt-odt-upto','bg-mode-upto'].includes(f));
    const timing = fields.filter(f => ['wdqs-ctrl-mode','rpste-upto','wpste-upto'].includes(f));
    const common = ['wire-length'];
    
    let warning = '\n⚠️ Non-parseable fields (generated at runtime):\n';
    if (lp4.length) warning += '  LP4: ' + lp4.join(', ') + '\n';
    if (lp5.length) warning += '  LP5: ' + lp5.join(', ') + '\n';
    if (timing.length) warning += '  Timing: ' + timing.join(', ') + '\n';
    warning += '  Common: ' + common.join(', ');
    
    statusEl.innerHTML += '<pre style="margin-top:10px;">' + warning + '</pre>';
}
```

---

### Issue 3 Fix: Display parsed params in analysis modal (COMPLETE REWRITE)

#### Part A: Parse ALL timing entry params from binary

**File**: `gui.py`

**Location**: In `analyze_binary_file()` function, after period parsing (~line 142)

**Entry enable check**: Entry is enabled if ANY of these > 0:
- write_odt (+0x10A)
- write_dbi (+0x10C) 
- read_dbi (+0x10D)
- read_link_parity (+0x11F) - LP5 only
- write_link_parity (+0x120) - LP5 only

**Timing table structure** (each entry 296 bytes = 0x128, first at offset 0):
| Offset (rel) | Field | Size | gen_timing_params line |
|--------------|-------|------|------------------------|
| +0x00 | freq | 4 | 496 |
| +0x04 | t_ck | 4 | 497 |
| +0x08 | timing_zqcal | 4 | 508 |
| +0x0C to +0x5C | timing_param[0-20] | 84 | 506 |
| +0x60 | timing_derate[0] | 4 | 507 |
| +0x64 | timing_derate[1] | 4 | 507 |
| +0x68 to +0x84 | dfi_timing_param[0-7] | 32 | 509 |
| +0x106 | wck_ratio | 1 | uint8 | WCK ratio (gen_timing_params line 498) |
| +0x107 | tlp_resp | 1 | uint8 | TLP response (line 510) |
| +0x108 | auto_dqs_clean (adc) | 1 | uint8 | Auto DQS clean (line 521) |
| +0x109 | dll_enable | 1 | uint8 | DLL enable (line 499) |
| +0x10A | write_odt | 1 | uint8 | Write ODT (line 500) |
| +0x10B | nt_odt | 1 | uint8 | Non-target ODT (line 501) |
| +0x10C | write_dbi | 1 | uint8 | Write DBI (line 502) |
| +0x10D | read_dbi | 1 | uint8 | Read DBI (line 503) |
| +0x10E | wpste | 1 | uint8 | Write preamble training (line 504) |
| +0x10F | rpste | 1 | uint8 | Read preamble training (line 505) |
| +0x110 | rl (read_latency) | 1 | uint8 | Read latency (line 520) |
| +0x111 | wl (write_latency) | 1 | uint8 | Write latency (line 522) |
| +0x112 | mr_rl | 1 | uint8 | MR read latency (line 523) |
| +0x113 | mr_wl | 1 | uint8 | MR write latency (line 524) |
| +0x114 | mr_wr | 1 | uint8 | MR write (line 525) |
| +0x115 | mr_rtp | 1 | uint8 | MR RTP (line 526) |
| +0x116 | mr_cal | 1 | uint8 | MR calibration (line 527) |
| +0x117 | mr_tccd_l | 1 | uint8 | MR CCD_L (line 528) |
| +0x118 | bank_mode | 1 | uint8 | Bank mode (line 529) |
| +0x119 | wck_fm | 1 | uint8 | WCK frequency mode (line 530) |
| +0x11A | rdqs_pst_mode | 1 | uint8 | RDQS post mode (line 531) |
| +0x11B | rdqs_pst | 1 | uint8 | RDQS post (line 532) |
| +0x11C | rdqs_pre | 1 | uint8 | RDQS pre (line 533) |
| +0x11D | wck_pst | 1 | uint8 | WCK post (line 534) |
| +0x11E | wck_on | 1 | uint8 | WCK on (line 535) |
| +0x11F | read_link_parity | 1 | uint8 | Read link ECC (line 536) |
| +0x120 | write_link_parity | 1 | uint8 | Write link ECC (line 537) |
| +0x121 | t_rtw | 1 | uint8 | Read to write (line 538) |
| +0x122 | t_wtr_a | 1 | uint8 | Write to read auto (line 539) |
| +0x123 | t_wtr | 1 | uint8 | Write to read (line 540) |
| +0x124 | t_rc | 1 | uint8 | Read cycle (line 541) |
| +0x125 | trddata_en | 1 | uint8 | Read data enable (line 542) |

**timing_param decoded names**:
| Index | Name | Index | Name |
|-------|------|-------|------|
| 0 | t_rp | 11 | t_rtw |
| 1 | t_rcd | 12 | t_wtr |
| 2 | t_ras | 13 | t_wtr_l |
| 3 | t_rc | 14 | t_wr |
| 4 | t_rrd | 15 | t_rp_ab |
| 5 | t_rrd_l | 16 | t_rcd_wr |
| 6 | t_faw | 17 | t_cke |
| 7 | t_ccd_l | 18 | t_ckesr |
| 8 | t_ccd_l_wr | 19 | t_xs |
| 9 | t_ccd_s | 20 | t_dqs0_qs |

**Code to add in gui.py**:
```python
# Parse all timing entries (296 bytes each = 0x128)
entry_size = 0x128
timing_entries = []
num_entries = len(data) // entry_size

for idx in range(num_entries):
    entry_offset = idx * entry_size
    if entry_offset + 0x126 > len(data):
        break
    
    # Check enable flags (OR logic)
    write_odt = data[entry_offset + 0x10A]
    write_dbi = data[entry_offset + 0x10C] if entry_offset + 0x10C < len(data) else 0
    read_dbi = data[entry_offset + 0x10D] if entry_offset + 0x10D < len(data) else 0
    read_link_parity = data[entry_offset + 0x11F] if entry_offset + 0x11F < len(data) else 0
    write_link_parity = data[entry_offset + 0x120] if entry_offset + 0x120 < len(data) else 0
    
    if not (write_odt > 0 or write_dbi > 0 or read_dbi > 0 or read_link_parity > 0 or write_link_parity > 0):
        continue  # Skip disabled entries
    
    entry = {
        'entry': idx,
        't_ck': struct.unpack('<I', data[entry_offset+0x04:entry_offset+0x08])[0],
        'freq': struct.unpack('<I', data[entry_offset+0x00:entry_offset+0x04])[0],
        'timing_zqcal': struct.unpack('<I', data[entry_offset+0x08:entry_offset+0x0C])[0],
        'timing_param': [struct.unpack('<I', data[entry_offset+0x0C+i*4:entry_offset+0x10+i*4])[0] for i in range(21)],
        'timing_derate': [struct.unpack('<I', data[entry_offset+0x60:entry_offset+0x64])[0],
                          struct.unpack('<I', data[entry_offset+0x64:entry_offset+0x68])[0]],
        'dfi_timing_param': [struct.unpack('<I', data[entry_offset+0x68+i*4:entry_offset+0x6C+i*4])[0] for i in range(8)],
        # Common params (lines 498-510) - same for all entries
        'wck_ratio': data[entry_offset + 0x106],
        'tlp_resp': data[entry_offset + 0x107],
        'adc': data[entry_offset + 0x108],
        'dll_enable': data[entry_offset + 0x109],
        'write_odt': data[entry_offset + 0x10A],
        'nt_odt': data[entry_offset + 0x10B],
        'write_dbi': data[entry_offset + 0x10C],
        'read_dbi': data[entry_offset + 0x10D],
        'wpste': data[entry_offset + 0x10E],
        'rpste': data[entry_offset + 0x10F],
        # Per-entry params (lines 520-542)
        'rl': data[entry_offset + 0x110],
        'wl': data[entry_offset + 0x111],
        'mr_rl': data[entry_offset + 0x112],
        'mr_wl': data[entry_offset + 0x113],
        'mr_wr': data[entry_offset + 0x114],
        'mr_rtp': data[entry_offset + 0x115],
        'mr_cal': data[entry_offset + 0x116],
        'mr_tccd_l': data[entry_offset + 0x117],
        'bank_mode': data[entry_offset + 0x118],
        'wck_fm': data[entry_offset + 0x119],
        'rdqs_pst_mode': data[entry_offset + 0x11A],
        'rdqs_pst': data[entry_offset + 0x11B],
        'rdqs_pre': data[entry_offset + 0x11C],
        'wck_pst': data[entry_offset + 0x11D],
        'wck_on': data[entry_offset + 0x11E],
        'read_link_parity': data[entry_offset + 0x11F],
        'write_link_parity': data[entry_offset + 0x120],
        't_rtw': data[entry_offset + 0x121],
        't_wtr_a': data[entry_offset + 0x122],
        't_wtr': data[entry_offset + 0x123],
        't_rc': data[entry_offset + 0x124],
        'trddata_en': data[entry_offset + 0x125],
    }
    timing_entries.append(entry)
```

**Parse common params** (from first enabled entry):
```python
common_params = {}
if timing_entries:
    first = timing_entries[0]
    common_params = {
        'wck_ratio': first.get('wck_ratio', 0),
        'dll_enable': first.get('dll_enable', 0),
        'write_odt': first.get('write_odt', 0),
        'nt_odt': first.get('nt_odt', 0),
        'write_dbi': first.get('write_dbi', 0),
        'read_dbi': first.get('read_dbi', 0),
        'wpste': first.get('wpste', 0),
        'rpste': first.get('rpste', 0),
        'tlp_resp': first.get('tlp_resp', 0),
    }
```

**Parse density from orbit config** (offset 0x81C):
```python
orbit_offset = 0x800
density = struct.unpack('<H', data[orbit_offset+0x1C:orbit_offset+0x1E])[0]
```

**Parse density-dependent params** (at fixed offsets 0x80-0xFE):
```python
# Determine number of densities (LP4: 7, LP5: 10)
num_densities = 7 if dram_type == 'lpddr4' else 10
density_arrays = {
    't_rfcab': [struct.unpack('<H', data[0x80+i*2:0x82+i*2])[0] for i in range(num_densities)],
    't_rfcpb': [struct.unpack('<H', data[0x8E+i*2:0x90+i*2])[0] for i in range(num_densities)],
    't_rfmab': [struct.unpack('<H', data[0x9C+i*2:0x9E+i*2])[0] for i in range(num_densities)],
    't_rfmpb': [struct.unpack('<H', data[0xAA+i*2:0xAC+i*2])[0] for i in range(num_densities)],
    't_refdpr': [struct.unpack('<H', data[0xB8+i*2:0xBA+i*2])[0] for i in range(num_densities)],
    'tx_pbr2pbr': [struct.unpack('<H', data[0xC6+i*2:0xC8+i*2])[0] for i in range(num_densities)],
    't_xsr': [struct.unpack('<H', data[0xD4+i*2:0xD6+i*2])[0] for i in range(num_densities)],
    't_xsdll': [struct.unpack('<H', data[0xE2+i*2:0xE4+i*2])[0] for i in range(num_densities)],
    't_xs_fast': [struct.unpack('<H', data[0xF0+i*2:0xF2+i*2])[0] for i in range(num_densities)],
}

# Get value for selected density
density_index = min(density, num_densities) - 1  # Assuming density 1,2,3... mapping
density_dependent = {k: v[density_index] if density_index < len(v) else 0 for k, v in density_arrays.items()}
```

**Update result['data']['timing']**:
```python
'timing': {
    'entries': timing_entries,           # Per-entry params (array of entries)
    'common': common_params,              # Common params (same for all)
    'density_dependent': density_dependent,  # For selected density
    'selected_density': density,          # Density from binary
    'write_odt_upto': write_odt_upto,
    'read_dbi_upto': read_dbi_upto,
    'write_dbi_upto': write_dbi_upto,
    'read_lecc_upto': read_lecc_upto,
    'write_lecc_upto': write_lecc_upto,
},
```

#### Part B: Display in Analysis Modal

**File**: `templates/gui.html`

**Location**: In `showAnalysisModal()` function (around line 1044)

**Display format**: 3 sections

**Section 1: Per-Entry Params (table: rows=params, cols=entries)**

```javascript
if (data.timing.entries?.length > 0) {
    html += '<div class="analysis-section"><h3>Timing Table - Per-Entry Params</h3>';
    html += '<div style="overflow-x:auto;"><table class="analysis-table">';
    
    // Header row: Entry# and t_ck
    html += '<tr><th>Parameter</th>';
    data.timing.entries.forEach((e, i) => {
        html += `<th>Entry ${i}<br>t_ck=${e.t_ck}</th>`;
    });
    html += '</tr>';
    
    // timing_param decoded names
    const tp_names = ['t_rp','t_rcd','t_ras','t_rc','t_rrd','t_rrd_l','t_faw','t_ccd_l','t_ccd_l_wr','t_ccd_s',
                      't_rtw','t_wtr','t_wtr_l','t_wr','t_rp_ab','t_rcd_wr','t_cke','t_ckesr','t_xs','t_dqs0_qs','t_??'];
    
    // Per-entry fields
    const perEntryFields = ['rl','wl','mr_rl','mr_wl','mr_wr','mr_cal','mr_tccd_l','bank_mode','wck_fm',
                           'rdqs_pst_mode','rdqs_pst','rdqs_pre','wck_pst','wck_on','read_link_parity','write_link_parity',
                           't_rtw','t_wtr_a','t_wtr','t_rc','trddata_en','freq','timing_zqcal'];
    
    perEntryFields.forEach(field => {
        html += `<tr><td>${field}</td>`;
        data.timing.entries.forEach(e => {
            html += `<td>${e[field]}</td>`;
        });
        html += '</tr>';
    });
    
    // timing_param rows
    for (let i = 0; i < 21; i++) {
        html += `<tr><td>tp[${i}] ${tp_names[i]}</td>`;
        data.timing.entries.forEach(e => {
            html += `<td>0x${e.timing_param[i].toString(16).padStart(8,'0')}</td>`;
        });
        html += '</tr>';
    }
    
    // timing_derate
    html += '<tr><td>derate[0]</td>';
    data.timing.entries.forEach(e => { html += `<td>0x${e.timing_derate[0].toString(16).padStart(8,'0')}</td>`; });
    html += '</tr>';
    html += '<tr><td>derate[1]</td>';
    data.timing.entries.forEach(e => { html += `<td>0x${e.timing_derate[1].toString(16).padStart(8,'0')}</td>`; });
    html += '</tr>';
    
    // dfi_timing_param
    for (let i = 0; i < 8; i++) {
        html += `<tr><td>dfi[${i}]</td>`;
        data.timing.entries.forEach(e => {
            html += `<td>0x${e.dfi_timing_param[i].toString(16).padStart(8,'0')}</td>`;
        });
        html += '</tr>';
    }
    
    html += '</table></div></div>';
}
```

**Section 2: Common Params** (same for all entries):
```javascript
if (data.timing.common) {
    html += '<div class="analysis-section"><h3>Common Params (Same for All Entries)</h3>';
    html += '<table class="analysis-table"><tr><th>Parameter</th><th>Value</th></tr>';
    for (const [key, val] of Object.entries(data.timing.common)) {
        html += `<tr><td>${key}</td><td>${val}</td></tr>`;
    }
    html += '</table></div>';
}
```

**Section 3: Density-Dependent Params** (for selected density):
```javascript
if (data.timing.density_dependent) {
    html += '<div class="analysis-section"><h3>Density-Dependent Params (Density: ' + data.timing.selected_density + ' Gb)</h3>';
    html += '<table class="analysis-table"><tr><th>Parameter</th><th>Value</th></tr>';
    for (const [key, val] of Object.entries(data.timing.density_dependent)) {
        html += `<tr><td>${key}</td><td>${val}</td></tr>`;
    }
    html += '</table></div>';
}
```

---

### Issue 4 Fix: Remove density print code

**File**: `gen_timing_params`

**Location**: Lines 611-618

**Action**: Delete these lines (as shown above)

---

## Files to Modify

| File | Changes |
|------|---------|
| gen_timing_params | Remove density print code (lines 611-618) |
| gui.py | Add timing params parsing (timing_param, dfi_timing_param, timing_zqcal, timing_derate) |
| templates/gui.html | Issue 1: Add toggle function calls |
| templates/gui.html | Issue 2: Add non-parseable warning |
| templates/gui.html | Issue 3: Add Timing Table + New Orbit Fields to modal |

---

## Expected Output Examples

### Analysis Modal Display (3 Sections)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Binary Analysis                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Binary Info                                                          │   │
│  │ File              test.bin                                          │   │
│  │ Size              5096 bytes                                         │   │
│  │ DRAM Type         LPDDR4                                            │   │
│  │ Dual Channel      No                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Timing Table - Per-Entry Params                                     │   │
│  │ ┌─────────┬─────────┬─────────┬─────────┬─────────┐                  │   │
│  │ │Param    │Entry 0  │Entry 1  │Entry 2  │Entry 3  │                  │   │
│  │ │         │t_ck=471│t_ck=938 │t_ck=1631│t_ck=2500│                  │   │
│  │ ├─────────┼─────────┼─────────┼─────────┼─────────┤                  │   │
│  │ │freq     │2123     │1066     │613      │400      │                  │   │
│  │ │rl       │14       │10       │8        │6        │                  │   │
│  │ │wl       │10       │8        │6        │4        │                  │   │
│  │ │mr_rl    │14       │10       │8        │6        │                  │   │
│  │ │mr_wl    │14       │10       │8        │6        │                  │   │
│  │ │mr_wr    │14       │10       │8        │6        │                  │   │
│  │ │mr_cal   │5        │5        │5        │5        │                  │   │
│  │ │mr_tccd_l│8        │8        │8        │8        │                  │   │
│  │ │t_rtw    │6        │5        │4        │3        │                  │   │
│  │ │t_wtr_a  │4        │3        │2        │2        │                  │   │
│  │ │t_rc     │50       │40       │34       │28       │                  │   │
│  │ │tp[0]    │0x0000A  │0x0000D  │0x00014  │0x00021  │ (t_rp)          │   │
│  │ │tp[1]    │0x00014  │0x00021  │0x00035  │0x00050  │ (t_rcd)         │   │
│  │ │...      │...      │...      │...      │...      │                  │   │
│  │ │dfi[0]   │0x4      │0x4      │0x4      │0x4      │                  │   │
│  │ │dfi[1]   │0x14     │0x14     │0x14     │0x14     │                  │   │
│  │ └─────────┴─────────┴─────────┴─────────┴─────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Common Params (Same for All Entries)                               │   │
│  │ wck_ratio    2    │ dll_enable  1    │ write_odt   1              │   │
│  │ nt_odt       1    │ write_dbi   1    │ read_dbi    1              │   │
│  │ wpste        0    │ rpste       0    │ tlp_resp   16              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Density-Dependent Params (Density: 16 Gb)                         │   │
│  │ t_rfcab    468   │ t_rfcpb    58    │ t_rfmab    520              │   │
│  │ t_rfmpb    65    │ t_refdpr   234   │ tx_pbr2pbr  43              │   │
│  │ t_xsr      530   │ t_xsdll    0     │ t_xs_fast  0               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Orbit Config (New Fields)                                          │   │
│  │ dram_t_ck    471    │ rclk_t_ck   0    │ boot_t_ck   0           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│                                    [OK]                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Status Div Warning

```
Generated successfully!

⚠️ Non-parseable fields (generated at runtime):
  LP4: variable-trrd, txsr-as-1st-ed
  LP5: enhanced-nt-odt, wck-*, rdqs-*, nt-odt-upto, bg-mode-upto
  Timing: wdqs-ctrl-mode, rpste-upto, wpste-upto
  Common: wire-length
```

---

## Test Plan

After implementation, test:

1. **Issue 1**: Load binary with dynamic-power-down=1, verify threshold field becomes visible
2. **Issue 2**: Load any binary, verify non-parseable warning appears in status div
3. **Issue 3**: Load binary, open analysis modal, verify:
   - **Section 1**: Per-Entry table shows rows=params, cols=entries (only enabled entries)
   - **Section 2**: Common params displayed (wck_ratio, dll_enable, write_odt, nt_odt, write_dbi, read_dbi, wpste, rpste, tlp_resp)
   - **Section 3**: Density-Dependent params for selected density (t_rfcab, t_rfcpb, t_rfmab, t_rfmpb, t_refdpr, tx_pbr2pbr, t_xsr, t_xsdll, t_xs_fast)
   - **Orbit Config**: Shows dram_t_ck, rclk_t_ck, boot_t_ck
4. **Issue 4**: Run gen_timing_params, verify no density print output

---

## Test Cases for Timing Entry Params Validation

### Test Script: test_timing_entry_validation.py

| ID | Test Case | Edge Case | Validation |
|----|-----------|-----------|------------|
| TC1 | Basic LP4 single channel | Normal | 4 entries, rl/wl decrease with t_ck |
| TC2 | LP5 single channel | LP5 specific | read/write_link_parity > 0 |
| TC3 | Partial entries | Some disabled | Only enabled entries parsed |
| TC4 | Dual channel | Multi-rank | num_rank, density values |
| TC5 | All densities | Max density count | Arrays: 7 (LP4) / 10 (LP5) |
| TC6 | Min t_ck (250) | High freq | rl = max (~20+) |
| TC7 | Max t_ck (10000) | Low freq | rl = min (4-6) |
| TC8 | Single entry | Min entries | 1 entry works |
| TC9 | Empty density arrays | Corrupted | Graceful handling |
| TC10 | Common params consistency | Same across entries | wck_ratio, dll_enable identical |
| TC11 | Timing param decoding | JEDEC validity | t_rcd >= t_ck, t_rc >= t_ras + t_rp |
| TC12 | DFI params validity | Reasonable range | dfi values > 0, reasonable |

### gen_timing_params lines 548-624 Function Summary

| Part | Lines | Can Remove? | Reason |
|------|-------|-------------|--------|
| Write timing_params.c | 549-559 | NO | Creates C timing table header |
| Determine density | 561-567 | NO | Sets orbit config density |
| Density code mapping | 569-582 | NO | Maps density->code |
| Collect densities | 584-588 | NO | Gathers needed densities |
| Generate orbit_init_gen.h | 590-609 | NO | Creates C header for build |
| **Debug print** | **611-619** | **YES** | **Issue 4 - to remove** |
| Generate mr_config_gen.h | 621-624 | NO | Creates C header for build |

**Conclusion**: Only lines 611-619 (debug print) can be removed. Rest generates essential C headers needed by firmware build.