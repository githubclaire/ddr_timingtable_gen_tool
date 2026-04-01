# DDR Timing Table Generator - Implementation Plan

## Date: 2026-04-01

## Issues to Fix

### 1. LPDDR5 dfs_lvl_t_ck Parsing Bug
- **Problem**: GUI reads from wrong offsets for LPDDR5
- **Current**: Reads from 0x85e, 0x860, 0x862 (orbit config area)
- **Should read**: 0x062, 0x070, 0x072 (timing table area) for LPDDR5
- **Result**: Shows [1, 0, 1] instead of [4147, 1034, 1612]

### 2. Single Channel Binary Periods Parsing (FIXED)
- Single channel binaries only store 1 valid period at offset 0x04
- Other period entries contain garbage data
- Fixed by using default periods when only 1 valid period found

### 3. Reference Binaries Need Regeneration
- After fixing parsing, reference binaries need to be regenerated
- Must match test params (density=4)

## Offset Analysis Summary

### dfs_lvl_t_ck Offsets

| Type | Current GUI Reads | Should Read | Expected Values |
|------|------------------|-------------|-----------------|
| **LPDDR4** | 0x85e, 0x860, 0x862 | 0x85e, 0x860, 0x862 ✓ | [938, 1631, 2500] |
| **LPDDR5** | 0x85e, 0x860, 0x862 | 0x062, 0x070, 0x072 | [4147, 1034, 1612] |

### Periods Offsets

| Type | Storage | Notes |
|------|---------|-------|
| **Dual Channel** | 0x004, 0x12c, 0x254, 0x37c | All 4 valid |
| **Single Channel** | Only 0x004 valid | Rest are garbage |

## Implementation Steps

1. **Fix gui.py**: Change dfs_lvl_t_ck offset parsing to use different offsets based on DRAM type
2. **Verify other offsets**: Check density, cpipe_depth, dpipe_depth for both types
3. **Regenerate reference binaries**: With correct parsing
4. **Run tests**: Verify all tests pass
5. **Create report**: Document findings

## Test Strategy

- Reference Binary Tests: 2/2
- Random Param Tests: 20/20
- Dual Channel Tests: 2/2
- All Densities: 17/17
- All Timing Fields: 140/140
- ps/MHz Toggle: PASS

## Success Criteria

- All tests pass
- Load bin → Analyze → Convert → Generate → Compare = IDENTICAL for both LPDDR4 and LPDDR5
