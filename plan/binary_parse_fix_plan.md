# Binary Parse Fix Plan - Comprehensive

## Date: 2026-04-03

## Goal

Fix gui.py binary parsing to parse ALL fields from binary instead of using hardcoded values.

---

## Part 1: Original Issues (Previously Fixed)

### 1. Timing Features - LECC Offsets Wrong
- `read_link_parity`: Currently at `offset + 179`, should be `offset + 0x11F` (191)
- `write_link_parity`: Currently at `offset + 180`, should be `offset + 0x120` (192)

### 2. Basic Parameters - Hardcoded
- `dq_width`: Hardcoded to 16, should parse from binary

### 3. Orbit Config - Almost ALL Hardcoded
Only 11 fields parsed, 37+ fields hardcoded

---

## Part 2: New Issues - LPDDR5 Parsing Wrong (2026-04-03)

### Problem: LPDDR5 Offsets Incorrect

When parsing LPDDR5 binary, values are completely wrong:

| Field | Expected | Got | Issue |
|-------|----------|-----|-------|
| `dq_width` (basic) | 16 | **0** | Wrong offset |
| `omc_freq_ratio` (pipe) | 1 | **0** | Wrong offset |
| `phy_freq_ratio` (pipe) | 1 | **0** | Wrong offset |
| `density` (orbit) | 4 | 2 | Wrong offset |
| `num_rank` (orbit) | 2 | 16 | Wrong offset |
| `density_code` | 3 | 41666 | Wrong offset |
| `dfs_lvl_t_ck` | [556,...] | [1672, 2224, 5000] | Wrong offset |

### Root Cause: LPDDR5 Offset Calculation Wrong

**Current (WRONG):**
```python
lp5_shift = 0x0C if is_lpddr5 else 0x00  # WRONG!
```

**LPDDR5 has 9-byte extra header** (lp5_mr2-18 + zq_bg_mode), so shift should be **+0x09** for most fields.

**BUT**: Not ALL fields shift equally! The struct layout is:

| Group | Fields | Offset Behavior |
|-------|--------|-----------------|
| A | `dram_boot` to `ca_vref` | LPDDR5: starts at 0x0D (shifted by +0x0D for lp5_mr* + zq_bg_mode) |
| B | `phy_freq_ratio`, `omc_freq_ratio` | **NO SHIFT** - same position in both |
| C | `density` onwards | Shifted by +0x09 |

### Fix: Split Fields into 3 Groups

#### Group A: Early fields (with lp5 header shift)
| Field | LPDDR4 | LPDDR5 |
|-------|--------|--------|
| lp5_mr2 | N/A | 0x0D |
| ... | ... | ... |
| zq_bg_mode | N/A | 0x15 |
| density | 0x1C | **0x28** (+0x0C = 12 bytes, but actually starts after 9-byte header) |

Wait, let me recalculate:
- LPDDR4: `dram_boot` at 0x00
- LPDDR5: `lp5_mr2` at 0x0D (after 12 bytes of lp5 fields), then `density` starts at...

Actually the struct is:
- LPDDR5 has 9 bytes at start (lp5_mr2-18: 8 bytes + zq_bg_mode: 1 byte)
- So `density` which is at 0x1C in LPDDR4 should be at 0x1C + 9 = **0x25** in LPDDR5

Let me verify by checking the binary:
- density at 0x81C in LPDDR4 = 4 (0x0004)
- density at 0x825 in LPDDR5 = 2 (0x0002)

So LPDDR5 density is at **0x825** (file offset), which is struct offset **0x25**.

In LPDDR4: density at **0x81C** (file offset), struct offset **0x1C**.

So shift = 0x25 - 0x1C = **0x09** (9 bytes) ✓

### Correct Fix: Use correct offset per field

```python
# Group B: No shift needed (same position in both)
('phy_freq_ratio', 0x0c, '<H'),  # 0x80C - same
('omc_freq_ratio', 0x0e, '<H'),  # 0x80E - same
('cpipe_depth', 0x14, '<H'),     # 0x814 - same
('dpipe_depth', 0x16, '<H'),     # 0x816 - same

# Group C: Shift by 0x09 for LPDDR5
('density', 0x1c + lp5_shift, '<H'),        # 0x81C vs 0x825
('rank_interleaving', 0x1e + lp5_shift, '<H'),
('num_rank', 0x20 + lp5_shift, '<H'),
('reboot_with_mrw', 0x22 + lp5_shift, '<H'),
...
```

### Also Fix Late Fields (after chip config)

| Field | LPDDR4 Offset | LPDDR5 Offset | Shift |
|-------|---------------|---------------|-------|
| zq_calibration_period | 0xE4 | 0xEE | +0x0A |
| temp_sensing_period | 0xEC | 0xF6 | +0x0A |
| t_refipb | 0xF0 | 0xFA | +0x0A |
| t_refiab | 0xF4 | 0xFE | +0x0A |
| t_zqcal | 0xF8 | 0x102 | +0x0A |
| mrr_byte_lane | 0x100 | 0x106 | +0x06 |

Actually need to verify these. The chip config is 20 bytes per chip × 2 = 40 bytes.

For LPDDR5, base_addr starts at 0xC8 (vs 0xC0 in LPDDR4), so shift = 8 bytes for base_addr onwards.

But late fields need specific offsets.

---

## Implementation

### 1. Fix gui.py - Correct LPDDR5 Offset Handling

Split fields into groups with appropriate offsets.

### 2. Hide LECC for LPDDR4 in GUI

Add logic to toggleDramOptions() to show/hide LECC fields.

### 3. Hardcode LECC Values

- LPDDR4: read_lecc_upto = 0, write_lecc_upto = 0
- LPDDR5: read_lecc_upto = 625, write_lecc_upto = 625

### 4. Update test_binary_parse.py

Add actual value validation for LPDDR5.

---

## Test Cases

### test_binary_parse.py

| # | Test Function | Description |
|---|---------------|-------------|
| 1 | test_lpddr4_dual_all_fields_parsed | Verify fields parsed from LPDDR4 dual |
| 2 | test_lpddr4_single_all_fields_parsed | Verify fields parsed from LPDDR4 single |
| 3 | test_lpddr5_dual_all_fields_parsed | Verify fields parsed from LPDDR5 dual |
| 4 | test_lpddr5_single_all_fields_parsed | Verify fields parsed from LPDDR5 single |
| 5 | test_no_hardcoded_defaults | Verify no hardcoded values |
| 6 | test_orbit_config_field_values | Verify field values match binary |
| 7 | test_timing_features_from_binary | Verify timing features parsed |

---

## Files to Modify

1. **gui.py** - Fix LPDDR5 offsets, hide LECC for LPDDR4, hardcode LECC values
2. **templates/gui.html** - Add CSS/JS to hide LECC for LPDDR4
3. **test_binary_parse.py** - Add value validation
