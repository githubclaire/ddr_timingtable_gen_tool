# Bug Fix Report - 2026-04-12

## Summary

Fixed 4 reported bugs and 5 additional similar bugs discovered during investigation.

---

## Bug 1: Binary Parsing Offsets for write-odt-upto / read-dbi-upto / write-dbi-upto

**Symptom**: Set write-odt-upto/read-dbi-upto/write-dbi-upto in GUI, generate binary, load binary back — parsed values did not match the original settings.

**Root Cause**: `analyze_binary_file()` in `gui.py` used incorrect decimal offsets (158, 160, 161) to read the write_odt, write_dbi, and read_dbi flags from timing entries. The correct offsets are:
- LP4: `0x10A` (266), `0x10C` (268), `0x10D` (269) — common params start at `0x106`
- LP5: `0x140` (320), `0x142` (322), `0x143` (323) — common params start at `0x13c`

Additionally, the `read_link_parity` and `write_link_parity` offsets were hardcoded to LP4 offsets (`0x11F`, `0x120`) and wrong for LP5.

**Fix** (gui.py):
- `analyze_binary_file()`: Replaced hardcoded offsets with `common_off + 4/6/7` pattern using the correct base offset per DRAM type. Also fixed per-entry offsets for link parity flags.
- `parse_timing_entries()`: Same fix for entry validation — was using LP4 offsets `0x10A/0x10C/0x10D` unconditionally.

**Similar Bug Found**: LP5 "upto" values were returned in internal t_ck units instead of tWCK units. Added conversion (`t_ck // wck_ratio`) for LP5 so the GUI receives values matching what the user originally entered.

### Files Changed
- `gui.py`: Lines ~300-345 (`analyze_binary_file`), Lines ~150-165 (`parse_timing_entries`)

### Verification
- LP4 round-trip: write-odt-upto=938, read-dbi-upto=1631, write-dbi-upto=938 → parsed correctly
- LP5 round-trip: write-odt-upto=556, read-dbi-upto=418, write-dbi-upto=556 → parsed correctly (tWCK units)

---

## Bug 2: Wire-Length Unit Toggle

**Symptom**: Toggling ps/MHz in Timing Features changed the wire-length label from "mil" to "MHz" or "ps".

**Root Cause**: `handleTimingUnitChange()` in `gui.html` updated ALL `.unit-label` spans on the page, including the wire-length field which uses "mil" (milli-inch) units.

**Fix** (templates/gui.html):
- Rewrote `handleTimingUnitChange()` to only update unit labels for the specific timing fields being converted, not all `.unit-label` elements.
- Added `data-fixed-unit="mil"` attribute to wire-length's unit label as a semantic marker.
- Also fixed: dynamic period inputs were handled separately since they use `name^="periods-"` pattern.

### Files Changed
- `templates/gui.html`: `handleTimingUnitChange()` function

---

## Bug 3: Valid Ranges and Tooltips

**Symptom**: GUI parameter tooltips had incorrect or inconsistent range information, and no HTML min/max validation.

**Changes Made**:

| Parameter | Old Tooltip | Updated Tooltip | HTML min/max |
|-----------|------------|-----------------|--------------|
| write-odt-upto | "LPDDR4: 1250ps max, LPDDR5: 10000ps max" | "LPDDR4: capped at 1249ps. Range: 0-10000ps" | min=0 max=10000 |
| read-dbi-upto | "Range: 1000-10000ps (100-1000MHz)" | "Range: 0-10000ps" | min=0 max=10000 |
| write-dbi-upto | "Range: 1000-10000ps (100-1000MHz)" | "Range: 0-10000ps" | min=0 max=10000 |
| read-lecc-upto | "Range: 500-2500ps (400-2000MHz)" | "Range: 0-10000ps" | min=0 max=10000 |
| write-lecc-upto | "Range: 500-2500ps (400-2000MHz)" | "Range: 0-10000ps" | min=0 max=10000 |
| wire-length | "Wire length in mil, not ps" | "PCB trace length in mil. Used for board delay (0.07 ns/mil)" | min=0 |
| wdqs-ctrl-mode | (none) | "Write DQS control mode. Range: 0-3" | min=0 max=3 |
| rpste-upto | "Max tCK to enable extended read post-amble" | "Range: 0-10000ps" | min=0 max=10000 |
| wpste-upto | "Max tCK to enable extended write post-amble" | "Range: 0-10000ps" | min=0 max=10000 |
| min-dram-tck | "Range: 200-3000ps" | "Range: 100-5000ps" | min=100 max=5000 |
| dram-tck | "Range: 300-5000ps" | "Range: 100-5000ps" | min=100 max=5000 |
| dfs_lvl_t_ck[*] | "Range: 500-3000ps" / "500-5000ps" | "Range: 300-5000ps" | min=300 max=5000 |
| All LP5 upto fields | Various inaccurate ranges | "Range: 0-10000ps" with defaults | min=0 max=10000 |
| Periods | (none) | "Range: 100-10000ps" | min=100 max=10000 |

**Rationale**: The old tooltips had arbitrary range restrictions (e.g., read-dbi-upto "1000-10000") that didn't match the actual code. The `gen_timing_params` code uses simple `>= t_ck` comparisons with no lower bound validation. Only LP4 write-odt-upto has a hard cap (1249) enforced in code.

### Files Changed
- `templates/gui.html`: All tooltip `title` attributes and `min`/`max` HTML attributes

---

## Bug 4: Max Periods Limit

**Symptom**: GUI allowed unlimited periods, but the binary format has a fixed 0x800-byte timing table region, limiting how many entries can fit.

**Root Cause**: The timing table occupies offsets 0x0000–0x07FF (2048 bytes). Orbit config starts at 0x0800.
- LP4 entry size: 0x128 (296 bytes) → **max 6 periods** (6 × 296 = 1776 < 2048)
- LP5 entry size: 0x15C (348 bytes) → **max 5 periods** (5 × 348 = 1740 < 2048)

Adding more periods would overflow into the orbit config region, corrupting the binary.

**Fix** (templates/gui.html):
- Added `getMaxPeriods()` function that returns 6 (LP4) or 5 (LP5)
- `addPeriod()` now checks the limit and shows an alert if exceeded
- `renderPeriodsFromString()` truncates to the max when loading from binary
- Added a visual hint (`max 6` / `max 5`) next to the "Add Period" button
- `updatePeriodsLabel()` updates the hint when DRAM type changes
- Period inputs now have `min=100 max=10000` HTML validation

### Files Changed
- `templates/gui.html`: `getMaxPeriods()`, `addPeriod()`, `addPeriodInput()`, `renderPeriodsFromString()`, `updatePeriodsLabel()`, periods HTML

---

## Additional Similar Bugs Found & Fixed

### A. LP5 tWCK-to-tCK Conversion in Binary Parsing

The binary stores LP5 timing as internal t_ck (= tWCK × wck_ratio), but the GUI uses tWCK units. The `analyze_binary_file()` function returned raw t_ck values for write_odt_upto/read_dbi_upto/write_dbi_upto, causing a mismatch when loading LP5 binaries.

**Fix**: Added tWCK conversion (divide by wck_ratio) after extracting upto values from LP5 binaries.

### B. LP5 Entry Validation Using LP4 Offsets

`parse_timing_entries()` used hardcoded LP4 offsets (`0x10A`, `0x10C`, `0x10D`, `0x11F`, `0x120`) to check if entries were valid, even for LP5 binaries. This could cause LP5 entries to be skipped or misidentified.

**Fix**: Used the correct `common_offset_base` and `per_entry_base` variables per DRAM type.

---

## Bug 5: JS Validation Ranges Blocking Valid Inputs (Found During Chrome Testing)

**Symptom**: Setting write-odt-upto=938 and clicking "Generate Binary" showed "Validation Error: write-odt-upto: 938 (valid: 1250-1250ps)" — generation was blocked by JS validation.

**Root Cause**: `validateTimingRanges()` in gui.html had incorrect min/max ranges:
- write-odt-upto: min=1250, lpddr4_max=1250 (only allowed exactly 1250!)
- read-dbi-upto: min=1000 (rejected values below 1000)
- write-dbi-upto: min=1000
- min-dram-tck: max=3000 (should be 5000)
- dram-tck: min=300 (should be 100)
- wck-1to4-upto: min=625 (should be 0)
- wck-always-on-upto: 314-1256 (should be 0-10000)

**Fix**: Updated all ranges to match the actual gen_timing_params constraints (all "upto" fields accept 0-10000ps).

### Files Changed
- `templates/gui.html`: `validateTimingRanges()` function

---

## Bug 6: Save/Load JSON Checkbox Round-Trip (Found During Chrome Testing)

**Symptom**: After Save JSON → Load JSON, all checkboxes were reset to unchecked regardless of their saved state.

**Root Cause**: `saveJson()` stores checkbox values as `'1'`/`'0'`, but `loadJson()` compared against `'true'` — which never matches, so all checkboxes loaded as unchecked.

**Fix**: Changed loadJson checkbox handling to accept all truthy formats: `'1'`, `'true'`, or boolean `true`.

### Files Changed
- `templates/gui.html`: `loadJson()` function

---

## Bug 7: Load JSON Missing UI Toggle Updates (Found During Chrome Testing)

**Symptom**: After loading a JSON with different DRAM type or checkbox states, conditional UI sections (DSM, periodic training period, etc.) didn't update visibility.

**Root Cause**: `loadJson()` only called 3 toggle functions after loading. Many conditional UI sections depended on additional toggles that weren't called.

**Fix**: Added all missing toggle calls after loading: `updatePeriodsLabel()`, `toggleDsmEn()`, `updateMrrByteLane()`, `togglePeriodicTraining()`, `toggleTempSensing()`, `toggleZqCalibration()`, `toggleRankInterleaving()`, `togglePhyLowPower()`, `toggleDynamicPowerDown()`, `toggleDynamicSelfRefresh()`.

Also replaced the `alert()` error handler with inline status display to avoid blocking the browser.

### Files Changed
- `templates/gui.html`: `loadJson()` function

---

## Test Results

- **Unit tests**: 31 passed, 1 skipped (all existing tests pass)
- **LP4 round-trip**: Generate with custom odt/dbi values → analyze → values match exactly
- **LP5 round-trip**: Generate with custom odt/dbi values → analyze → values match exactly (tWCK units)
- **GUI HTML verification**: All 9 programmatic checks pass (fixed-unit markers, max limits, min/max attributes)
- **Chrome browser verification**: All 4 bugs verified, Save/Load JSON round-trip verified with checkboxes
- **GIF recording**: Exported as bugfix_verification.gif
