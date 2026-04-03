# Implementation Plan - DDR Timing Table Generator Fixes

## Date: 2026-04-02

---

## Issues to Fix

### 1. CLI/GUI Binary Match
- Update test params to match GUI
- Regenerate reference binaries
- Binary comparison should be IDENTICAL

### 2. Pipe Configuration Cleanup
- Remove two-channel (keep in Orbit Configuration)
- Remove orbit-config-density (keep in Orbit Configuration as dropdown)

### 3. UI Reorganization
- Move `reboot-with-training` from Training Enable to Mode Control
- Move "Generate ddr_config.h" checkbox from button area to Feature Flags
- Rename button: "Generate Binary & Header" → "Generate Binary"

### 4. Save JSON - Periods
- Fix saveJson() to include periods as "471 938 1631 2500"

### 5. Checkbox Values
- Change ALL checkboxes from 'true'/'false' to 1/0

---

## Implementation Order

1. Fix checkbox values in gui.html
2. Fix saveJson periods in gui.html
3. Remove two-channel/density from Pipe Config
4. Move reboot-with-training to Mode Control
5. Move Generate checkbox to Feature Flags
6. Rename button
7. Update test params in test_gui_params.py
8. Regenerate reference binaries
9. Run tests and verify

---

## Files to Modify

| File | Changes |
|------|---------|
| gui.html | All UI changes, checkbox values, saveJson fix |
| test_gui_params.py | Update reference test params |
| Reference binaries | Regenerate |