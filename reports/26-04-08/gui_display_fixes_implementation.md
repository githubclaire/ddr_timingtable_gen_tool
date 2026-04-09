# GUI Display Fixes Implementation Report - 2026-04-08

## Summary

Implemented 4 fixes to improve GUI display of binary analysis data:

| Issue | Status | Files Modified |
|-------|--------|----------------|
| Issue 1: Toggle functions after binary load | ✅ Complete | templates/gui.html |
| Issue 2: Non-parseable fields warning | ✅ Complete | templates/gui.html |
| Issue 3: Parsed params in analysis modal | ✅ Complete | gui.py, templates/gui.html |
| Issue 4: Remove density print code | ✅ Complete | gen_timing_params |

---

## Issue 1: Toggle Functions After Binary Load

### Problem
When loading binary, numeric fields like `dynamic-power-down-threshold`, `zq-calibration-period` remained hidden even when their checkboxes were checked.

### Root Cause
`fillOrbitConfig()` populated values but didn't call toggle functions that control field visibility.

### Solution
Added toggle function calls at the end of `fillGuiFromAnalysis()`:

```javascript
// Call toggle functions to show/hide dependent numeric fields
toggleZqCalibration();
togglePeriodicTraining();
toggleTempSensing();
toggleDynamicPowerDown();
toggleDynamicSelfRefresh();
togglePhyLowPower();
```

### Location
`templates/gui.html` lines 931-937 (end of fillGuiFromAnalysis function)

---

## Issue 2: Non-parseable Fields Warning

### Problem
17 fields are generated at runtime (not stored in binary), but there was no warning when loading binary.

### Solution
Added warning display in status div after successful binary load:

```javascript
if (result.data.orbit?.non_parseable_fields?.length > 0) {
    const fields = result.data.orbit.non_parseable_fields;
    const lp4 = fields.filter(f => ['variable-trrd','txsr-as-1st-ed'].includes(f));
    const lp5 = fields.filter(f => ['enhanced-nt-odt','wck-always-on-from',...].includes(f));
    const timing = fields.filter(f => ['wdqs-ctrl-mode','rpste-upto','wpste-upto'].includes(f));
    const common = ['wire-length'];
    
    let warning = '\n⚠️ Non-parseable fields (generated at runtime):\n';
    // ... display grouped by category
}
```

### Location
`templates/gui.html` lines 814-840 (in analyzeBinaryFile success handler)

---

## Issue 3: Parsed Params in Analysis Modal

### Problem
Users wanted to see timing params parsed from binary (gen_timing_params lines 496-542), NOT the GUI params.

### Solution
Implemented 3-section display in analysis modal:

#### Part A: Parse timing params (gui.py)

Added `parse_timing_entries()` function that parses:
- **Per-entry params**: t_ck, freq, rl, wl, mr_*, timing_param[0-20], timing_derate[0-1], dfi_timing_param[0-7], etc.
- **Common params**: wck_ratio, dll_enable, write_odt, nt_odt, write_dbi, read_dbi, wpste, rpste, tlp_resp
- **Density-dependent params**: t_rfcab, t_rfcpb, t_rfmab, t_rfmpb, t_refdpr, tx_pbr2pbr, t_xsr, t_xsdll, t_xs_fast

Entry enable check uses OR logic - entry is enabled if ANY of these flags > 0:
- write_odt (+0x10A)
- write_dbi (+0x10C)
- read_dbi (+0x10D)
- read_link_parity (+0x11F) - LP5 only
- write_link_parity (+0x120) - LP5 only

#### Part B: Display in analysis modal (gui.html)

Updated `showAnalysisModal()` to show 3 sections:

1. **Per-Entry Params Table**: rows=params, cols=entries
2. **Common Params**: single values (same for all entries)
3. **Density-Dependent Params**: for selected density from binary

### Location
- `gui.py` lines 47-169: `parse_timing_entries()` function
- `gui.py` line 536: calling parse_timing_entries()
- `templates/gui.html` lines 1072-1150: showAnalysisModal() updated

---

## Issue 4: Remove Density Print Code

### Problem
gen_timing_params printed density info at end (lines 611-618), which is just debug output.

### Solution
Removed the print block:

```python
# REMOVED:
print("\n=== Supported Densities and Density Codes ===")
for d in orbit_densities:
    code = density_code_mapping.get(d, 0)
    print(f"  Density {d:2d} Gb -> density_code {code}")
print("=============================================")
print(f"  DEFAULT_DENSITY = {orbit_config_density}")
print(f"  Orbit config density = {orbit_config_density}")
print(f"  Orbit config density_code = {density_code_mapping.get(orbit_config_density, 0)}")
print("=============================================\n")
```

### Location
`gen_timing_params` lines 611-619 (removed)

---

## Test Plan

After implementation, test:

1. **Issue 1**: Load binary with dynamic-power-down=1, verify threshold field becomes visible
2. **Issue 2**: Load any binary, verify non-parseable warning appears in status div
3. **Issue 3**: Load binary, open analysis modal, verify:
   - Section 1: Per-Entry table shows rows=params, cols=entries (only enabled entries)
   - Section 2: Common params displayed
   - Section 3: Density-Dependent params for selected density
   - Orbit Config: Shows dram_t_ck, rclk_t_ck, boot_t_ck
4. **Issue 4**: Run gen_timing_params, verify no density print output

---

## Files Modified

| File | Changes |
|------|---------|
| `templates/gui.html` | Issue 1: Added toggle calls; Issue 2: Added warning; Issue 3: Updated modal display |
| `gui.py` | Issue 3: Added parse_timing_entries() function |
| `gen_timing_params` | Issue 4: Removed density print code |