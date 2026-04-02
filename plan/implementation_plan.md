# Implementation Plan - DDR Timing Table Generator GUI Enhancements

## Date: 2026-04-02

---

## Overview

Comprehensive implementation of GUI enhancements including:
- Read-only fields (cpipe-depth, dpipe-depth, omc-freq-ratio, phy-freq-ratio)
- orbit-config-density dropdown with DDR-type-specific options
- New LPDDR4/LPDDR5 timing options
- Bug fixes (wire-length ps/MHz toggle, save JSON)

---

## Implementation Items

### A. Previously Discussed Items

| # | Item | File | Line(s) | Change |
|----|------|------|---------|--------|
| A1 | cpipe-depth read-only | gui.html | 156-157 | Add `readonly` attribute |
| A2 | dpipe-depth read-only | gui.html | ~158 | Add new field with `readonly` |
| A3 | omc-freq-ratio read-only | gui.html | 160-161 | Add `readonly` attribute |
| A4 | phy-freq-ratio read-only | gui.html | 164-165 | Add `readonly` attribute |
| A5 | wire-length - remove from conversion | gui.html | 538-545 | Remove from `fieldsToConvert` array |
| A6 | orbit-config-density dropdown | gui.html | 282-285 | Replace input with select + add `updateDensityOptions()` |
| A7 | updateDensityOptions() in onchange | gui.html | 104 | Add function call |

### B. New LPDDR4 Options

| # | Item | File | Line(s) | Change |
|----|------|------|---------|--------|
| B1 | rpste-upto field | gui.html | ~230 | Add to LPDDR4 Options section |
| B2 | wpste-upto field | gui.html | ~230 | Add to LPDDR4 Options section |
| B3 | rpste-upto handling | gui.py | ~673 | Add in generate endpoint |
| B4 | wpste-upto handling | gui.py | ~673 | Add in generate endpoint |

### C. New LPDDR5 Options

| # | Item | File | Line(s) | Change |
|----|------|------|---------|--------|
| C1 | nt-odt-upto field | gui.html | ~260 | Add to LPDDR5 Options |
| C2 | enhanced-nt-odt checkbox | gui.html | ~260 | Add to LPDDR5 Options |
| C3 | bg-mode-upto field | gui.html | ~260 | Add to LPDDR5 Options |
| C4 | wck-hf-upto field | gui.html | ~260 | Add to LPDDR5 Options |
| C5 | wck-pst1-upto field | gui.html | ~260 | Add to LPDDR5 Options |
| C6 | wck-pst2-upto field | gui.html | ~260 | Add to LPDDR5 Options |
| C7 | rdqs-pst1-upto field | gui.html | ~260 | Add to LPDDR5 Options |
| C8 | rdqs-pst2-upto field | gui.html | ~260 | Add to LPDDR5 Options |
| C9 | LPDDR5 params handling | gui.py | ~685 | Add in generate endpoint |

### D. Common Updates

| # | Item | File | Line(s) | Change |
|----|------|------|---------|--------|
| D1 | New fields in ps/MHz toggle | gui.html | 538-545 | Add to `fieldsToConvert` |
| D2 | New fields in saveJson | gui.html | 926-947 | Handle in saveJson |
| D3 | New fields in loadJson | gui.html | ~1160 | Handle in loadJson |

### E. Testing

| # | Item | File | Change |
|----|------|------|--------|
| E1 | Add test cases | test_lpddr4.sh / test_lpddr5.sh | Add test cases with new params |
| E2 | Generate new ref binaries | test scripts | Run test scripts to regenerate |

---

## Default Values (from gen_timing_params)

**LPDDR4:**
| Field | Default |
|-------|---------|
| rpste-upto | 0 |
| wpste-upto | 0 |

**LPDDR5:**
| Field | Default |
|-------|---------|
| nt-odt-upto | 0 |
| enhanced-nt-odt | unchecked |
| bg-mode-upto | 625 |
| wck-hf-upto | 624 |
| wck-pst1-upto | 0 |
| wck-pst2-upto | 0 |
| rdqs-pst1-upto | 0 |
| rdqs-pst2-upto | 0 |

**Density Options:**
| DDR Type | Options (Gb) |
|----------|--------------|
| LPDDR4 | 2, 3, 4, 6, 8, 12, 16 |
| LPDDR5 | 2, 3, 4, 6, 8, 12, 16, 24, 32 |

---

## Implementation Status

- [ ] A1-A7: Read-only fields, wire-length fix, density dropdown
- [ ] B1-B4: LPDDR4 rpste/wpste fields
- [ ] C1-C9: LPDDR5 new timing options
- [ ] D1-D3: Common updates (toggle, save/load)
- [ ] E1-E2: Testing and reference binaries