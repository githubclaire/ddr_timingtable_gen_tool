# GUI Display Issues - Fix Plan

## Analysis Summary

### Root Cause: GUI fillOrbitConfig Missing Field Mappings

The `fillOrbitConfig` function in `templates/gui.html` is missing calls to set values for many checkbox fields and numeric fields. The Python backend (`analyze_binary_file`) correctly parses values, but the JavaScript frontend doesn't display them.

---

## Issue 1: Missing Checkbox Set Calls (17 total)

**Location**: `templates/gui.html` - fillOrbitConfig function (around line 863-908)

**Missing Checkboxes**:
| # | Field Name (HTML) | Notes |
|---|-------------------|-------|
| 1 | variable-trrd | LP4 specific |
| 2 | txsr-as-1st-ed | LP4 specific |
| 3 | enhanced-nt-odt | LP5 specific |
| 4 | reboot-with-training | |
| 5 | eye-scan-prbs-rd-en | |
| 6 | eye-scan-prbs-wr-en | |
| 7 | phy-vref-trn-mode | |
| 8 | phy-duty-trn-mode | |
| 9 | dram-vref-trn-mode | |
| 10 | dram-duty-trn_mode | |
| 11 | ca-vref-training | |
| 12 | prbs-training | |
| 13 | init-zq-calibration | |
| 14 | zq-calibration | |
| 15 | dfs-training | |
| 16 | periodic-training | |
| 17 | temp-sensing | |

**Fix**: Add these lines in fillOrbitConfig after line 886:
```javascript
// LP4/LP5 specific
setCheckboxValue('variable-trrd', data.orbit.variable_trrd);
setCheckboxValue('txsr-as-1st-ed', data.orbit.txsr_as_1st_ed);
setCheckboxValue('enhanced-nt-odt', data.orbit.enhanced_nt_odt);

// Training
setCheckboxValue('eye-scan-prbs-rd-en', data.orbit.eye_scan_prbs_rd_en);
setCheckboxValue('eye-scan-prbs-wr-en', data.orbit.eye_scan_prbs_wr_en);
setCheckboxValue('phy-vref-trn-mode', data.orbit.phy_vref_trn_mode);
setCheckboxValue('phy-duty-trn-mode', data.orbit.phy_duty_trn_mode);
setCheckboxValue('dram-vref-trn-mode', data.orbit.dram_vref_trn_mode);
setCheckboxValue('dram-duty-trn-mode', data.orbit.dram_duty_trn_mode);
setCheckboxValue('ca-vref-training', data.orbit.ca_vref_training);
setCheckboxValue('prbs-training', data.orbit.prbs_training);
setCheckboxValue('reboot-with-training', data.orbit.reboot_with_training);
setCheckboxValue('init-zq-calibration', data.orbit.init_zq_calibration);
setCheckboxValue('zq-calibration', data.orbit.zq_calibration);
setCheckboxValue('dfs-training', data.orbit.dfs_training);
setCheckboxValue('periodic-training', data.orbit.periodic_training);
setCheckboxValue('temp-sensing', data.orbit.temp_sensing);
```

---

## Issue 2: Missing Numeric Field Set Calls

### Fields That CAN Be Parsed from Binary (4 fields) - Need JS Display Mapping

These ARE parsed from binary but not displayed in GUI:

| # | Field | Data Location | Python Parse Status |
|---|-------|---------------|---------------------|
| 1 | dram-tck | data.basic | ✓ Parsed from timing table |
| 2 | periodic-training-period | data.orbit | ✓ Parsed |
| 3 | temp-sensing-period | data.orbit | ✓ Parsed |
| 4 | t-zqcal | data.orbit | ✓ Parsed |

**Fix for dran-tck** (add to fillBasic or fillGuiFromAnalysis):
```javascript
setFieldValue('dram-tck', data.basic.dram_tck);
```

**Fix for orbit fields** (add to fillOrbitConfig):
```javascript
setFieldValue('periodic-training-period', data.orbit.periodic_training_period);
setFieldValue('temp-sensing-period', data.orbit.temp_sensing_period);
setFieldValue('t-zqcal', data.orbit.t_zqcal);
```

### Fields That CANNOT Be Parsed from Binary (14 timing params)

These are threshold values NOT stored in binary - computed at generation time, not stored:

| # | Field | Reason |
|---|-------|--------|
| 1 | wdqs-ctrl-mode | Threshold computed at generation |
| 2 | rpste-upto | Threshold not in binary |
| 3 | wpste-upto | Threshold not in binary |
| 4 | wck-1to4-upto | Threshold not in binary |
| 5 | wck-always-on-from | Threshold not in binary |
| 6 | wck-always-on-upto | Threshold not in binary |
| 7 | nt-odt-upto | Threshold not in binary |
| 8 | bg-mode-upto | Threshold not in binary |
| 9 | wck-hf-upto | Threshold not in binary |
| 10 | wck-pst1-upto | Threshold not in binary |
| 11 | wck-pst2-upto | Threshold not in binary |
| 12 | rdqs-pst1-upto | Threshold not in binary |
| 13 | rdqs-pst2-upto | Threshold not in binary |

**Note**: These 14 fields cannot be loaded from binary in current implementation. They would need to be added to the orbit_config struct and stored in binary for full round-trip support.

---

## Issue 3: Test Coverage Gaps

**Why current tests don't catch these bugs**:
1. Tests only verify binary parsing (`analyze_binary_file`) returns correct values in `orbit_data`
2. Tests do NOT verify GUI's `fillOrbitConfig` function properly maps those values to HTML fields
3. The GUI display issue is at the HTML/JS layer, not the Python parsing layer

**Tests needed**:
- Verify full data['data'] structure includes all fields
- Add tests that check GUI's field mapping logic

---

## Files to Modify

| File | Changes |
|------|---------|
| templates/gui.html | Add ~17 missing `setCheckboxValue` calls |
| templates/gui.html | Add ~4 missing `setFieldValue` calls (dram-tck, periodic-training-period, temp-sensing-period, t-zqcal) |
| test scripts | Expand test coverage |

---

## Verification Checklist

### Checkboxes (17 missing)
- [ ] variable-trrd
- [ ] txsr-as-1st-ed
- [ ] enhanced-nt-odt
- [ ] reboot-with-training
- [ ] eye-scan-prbs-rd-en
- [ ] eye-scan-prbs-wr-en
- [ ] phy-vref-trn-mode
- [ ] phy-duty-trn-mode
- [ ] dram-vref-trn-mode
- [ ] dram-duty-trn_mode
- [ ] ca-vref-training
- [ ] prbs-training
- [ ] init-zq-calibration
- [ ] zq-calibration
- [ ] dfs-training
- [ ] periodic-training
- [ ] temp-sensing

### Numeric Fields - CAN Parse from Binary (4 fields)
- [ ] dram-tck
- [ ] periodic-training-period
- [ ] temp-sensing-period
- [ ] t-zqcal

### Numeric Fields - CANNOT Parse from Binary (14 fields)
These cannot be loaded from binary in current implementation:
- [ ] wdqs-ctrl-mode
- [ ] rpste-upto
- [ ] wpste-upto
- [ ] wck-1to4-upto
- [ ] wck-always-on-from
- [ ] wck-always-on-upto
- [ ] nt-odt-upto
- [ ] bg-mode-upto
- [ ] wck-hf-upto
- [ ] wck-pst1-upto
- [ ] wck-pst2-upto
- [ ] rdqs-pst1-upto
- [ ] rdqs-pst2-upto