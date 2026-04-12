# Report: num_rank and dq_width Offset Fix

## Date: 2026-04-03

## Problem
The GUI was parsing incorrect values for `num_rank` and `dq_width` fields due to wrong offsets in gui.py.

## Root Cause
- Current gui.py had incorrect offsets for these fields:
  - **LPDDR4**: num_rank=0x1b (wrong), dq_width=0x21 (wrong)
  - **LPDDR5**: num_rank=0x24 (wrong), dq_width=0x2a (wrong)

- Correct offsets from C struct analysis:
  - **LPDDR4**: num_rank=0x0c, dq_width=0x24
  - **LPDDR5**: num_rank=0x28, dq_width=0x2c

## Fix Applied
Updated gui.py with correct struct offsets:

**LPDDR4 section (line ~598-603):**
- num_rank: 0x1b → 0x0c
- dq_width: 0x21 → 0x24

**LPDDR5 section (line ~524-529):**
- num_rank: 0x24 → 0x28
- dq_width: 0x2a → 0x2c

## Verification
Binary values verified from reference files:
```
LPDDR4 dual: num_rank@0x80c=2, dq_width@0x824=16
LPDDR5 dual: num_rank@0x828=2, dq_width@0x82c=16
```

## Test Results
```
============================================================
Binary Parse Test Suite
============================================================

Results: 10 passed, 0 failed
============================================================
```

## Status: COMPLETED