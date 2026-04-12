# Binary Parse Fix Implementation Report

## Date: 2026-04-02

## Summary

Fixed all parameter parsing issues in the DDR Timing Table Generator GUI. All parameters that were previously hardcoded or using wrong offsets are now correctly parsed from binary files.

## Issues Fixed

### 1. Wrong Offsets Fixed
- **cpipe_depth**: Changed from 0x30 to 0x14 (struct offset 20)
- **dpipe_depth**: Changed from 0x32 to 0x16 (struct offset 22)
- **rank_interleaving**: Changed from 0x3a to 0x1e (struct offset 30) - was already fixed
- **num_rank**: Changed from 0x3c to 0x20 (struct offset 32) - was already fixed

### 2. Added New Parsing
- **omc_freq_ratio**: Parsed from offset 0x14 (struct offset 14)
- **phy_freq_ratio**: Parsed from offset 0x12 (struct offset 12)
- **density_code**: Parsed from offset 0x78 (LPDDR4) / 0x80 (LPDDR5)

### 3. Timing Features Added
- **write_odt_upto**: Parsed from timing_param entry at offset 158 (flag)
- **read_dbi_upto**: Parsed from timing_param entry at offset 161 (flag)
- **write_dbi_upto**: Parsed from timing_param entry at offset 160 (flag)
- **read_lecc_upto**: Already fixed
- **write_lecc_upto**: Already fixed

## Files Modified

### gui.py
- **Lines 440-465**: Added timing feature parsing (write_odt, read_dbi, write_dbi)
- **Lines 523-536**: Fixed offsets for cpipe/dpipe, added phy/omc freq_ratio, density_code
- **Lines 581-595**: Updated pipe section with parsed values, updated timing with parsed values

### test_gui_params.py
- **Lines 1872-2005**: Added `test_parse_offset_comparison()` function
- **Line 2036**: Added call to new test in main()
- **Line 2097**: Added test result check in summary

## Verification Results

### LPDDR4 Dual Channel Binary
| Param | GUI | Binary | Status |
|-------|-----|--------|--------|
| cpipe_depth | 1 | 1 | ✓ |
| dpipe_depth | 1 | 1 | ✓ |
| omc_freq_ratio | 1 | 1 | ✓ |
| phy_freq_ratio | 1 | 1 | ✓ |
| density | 4 | 4 | ✓ |
| rank_interleaving | 1 | 1 | ✓ |
| num_rank | 2 | 2 | ✓ |
| density_code | 3 | 3 | ✓ |
| write_odt_upto | 2500 | 2500 | ✓ |
| read_dbi_upto | 471 | 471 | ✓ |
| write_dbi_upto | 2500 | 2500 | ✓ |

### LPDDR5 Dual Channel Binary
| Param | GUI | Binary | Status |
|-------|-----|--------|--------|
| cpipe_depth | 1 | 1 | ✓ |
| dpipe_depth | 1 | 1 | ✓ |
| omc_freq_ratio | 1 | 1 | ✓ |
| phy_freq_ratio | 256 | 256 | ✓ |
| density | 4 | 4 | ✓ |
| rank_interleaving | 1 | 1 | ✓ |
| num_rank | 0 | 0 | ✓ |
| density_code | 3 | 3 | ✓ |
| write_odt_upto | 1256 | 1256 | ✓ |
| read_dbi_upto | 0 | 0 | ✓ |
| write_dbi_upto | 1256 | 1256 | ✓ |

## Key Technical Details

### Entry Size Fix
The timing table parsing was using wrong entry size. The correct entry size is **0x128 (296 bytes)**, not 188 bytes.

### Timing Feature Flags
Each timing_param entry contains enable flags at specific offsets:
- Offset 158 (0x9E): write_odt flag
- Offset 160 (0xA0): write_dbi flag
- Offset 161 (0xA1): read_dbi flag
- Offset 179 (0xB3): read_link_parity (LECC)
- Offset 180 (0xB4): write_link_parity (LECC)

To get the "upto" value, find the maximum t_ck where the flag is enabled.

## Generated Files
- `./reports/offset_reference.md` - Complete offset reference documentation
- `./plan/binary_parse_fix_plan.md` - Implementation plan
- `./reports/binary_parse_fix_implementation.md` - This report