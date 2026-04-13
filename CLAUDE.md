# CLAUDE.md

## Project Overview

DDR Timing Table Generator — generates LPDDR4/LPDDR5 timing table binaries via `gen_timing_params` CLI tool, with a web GUI (`gui.py` serving `templates/gui.html`) for configuration and binary analysis.

## Build & Test

```bash
# Run all tests
python3 -m pytest tests/ -q

# Run specific test file
python3 -m pytest tests/test_gui_validation.py -v

# Start GUI server (port 5010)
python3 gui.py
```

## Key Rules

### GUI Validation Must Cover All Numeric Inputs

When adding or modifying numeric input fields in `templates/gui.html`:

1. **HTML attributes**: Every `<input type="number">` must have `min` and `max` attributes matching the valid range.
2. **JS validation**: Every validated field must be listed in `validateTimingRanges()`. This includes:
   - Common fields: `dram-tck`, `min-dram-tck`, all `*-upto` fields, all `*-from` fields
   - LP4-specific: `rpste-upto`, `wpste-upto`
   - LP5-specific: `wck-1to4-upto`, `wck-always-on-from`, `wck-always-on-upto`, `nt-odt-upto`, `bg-mode-upto`, `wck-hf-upto`, `wck-pst1-upto`, `wck-pst2-upto`, `rdqs-pst1-upto`, `rdqs-pst2-upto`
   - Dynamic inputs: DFS level fields (`dfs-lvl-t-ck-*`), period inputs (`periods-*`)
3. **Tooltips**: Update the `title` attribute to reflect the actual valid range.
4. **Test coverage**: Add corresponding checks in `tests/test_gui_validation.py`.
5. **Dynamic ranges**: `updateFieldRanges()` must update HTML min/max on DRAM type change.

### Valid Ranges Derived from memcfg Tables

Ranges must match the memcfg tables in `lpddr4_config.py` / `lpddr5_config.py`:

| Parameter | LP4 | LP5 | Source |
|---|---|---|---|
| Periods (tCK/tWCK) | 468-5000ps | 235-5000ps | `search_memcfgs()` crashes outside range |
| write-odt-upto | 0-1249ps | 0-10000ps | LP4 hard cap at 1249 in `gen_timing_params` line 786 |
| All other upto/from | 0-10000ps | 0-10000ps | No constraint in code |
| DFS levels (internal t_ck) | 468-5000ps | 938-5000ps | LP5 min t_ck=938 from memcfg |
| dram-tck, min-dram-tck | 100-5000ps | 100-5000ps | Not fed to search_memcfgs; UI guard only |

LP4 period min = 468 from: `Boundary(2133, 468)` in lpddr4_config.py (highest frequency memcfg upper bound).
LP5 period min = 235 from: `ceil(938 / 4)` where 938 is the memcfg upper bound and 4 is wck_ratio with wck_1to4 enabled.

### Binary Layout Constants

LP4 and LP5 have different struct layouts — never hardcode one type's offsets for both:

| | LP4 | LP5 |
|---|---|---|
| Entry size | 0x128 (296 bytes) | 0x15C (348 bytes) |
| Common params offset | 0x106 | 0x13c |
| Per-entry params offset | 0x110 | 0x146 |
| Max periods (0x800 / entry_size) | 6 | 5 |

### LP5 Unit Conversion

LP5 binary stores internal `t_ck = tWCK * wck_ratio`. The GUI uses tWCK units. Always convert when reading LP5 binary values back for display (divide by `wck_ratio`).

### Wire-Length Unit

Wire-length is in cm (centimeter), not ps/MHz. It must never be affected by the timing unit toggle. The unit label has `data-fixed-unit="cm"` to prevent accidental conversion.
