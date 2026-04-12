# Implementation Report: DDR Binary Offset Fix

**Date:** 2026-04-03

## Summary

Fixed dual channel detection in gui.py to use correct offset based on DRAM type (LPDDR4 vs LPDDR5), and updated offset_reference_v2.md with complete offset tables distinguishing single/dual channel for both LPDDR4 and LPDDR5.

## Changes Made

### 1. gui.py (line 425-437)

**Problem:** Hardcoded offset 0x8E0 for dual channel detection failed for LPDDR5 (correct offset is 0x8E8 due to 9-byte header shift).

**Fix:** Made dual channel detection offset dynamic based on DRAM type:
- LPDDR4: check offset 0x8E0
- LPDDR5: check offset 0x8E8

### 2. offset_reference_v2.md

**Problem:** LPDDR4 section showed all 4 base_addr_id and phy_base_addr_id entries without distinguishing single vs dual channel, causing misunderstanding.

**Fix:** Split LPDDR4 section into two separate tables (same as LPDDR5):
- **LPDDR4 Offsets - Single Channel** (2 OMC/PHY) - indices [2,3] marked as N/A (0)
- **LPDDR4 Offsets - Dual Channel** (4 OMC/PHY) - all 4 indices valid

## Verification Results

| Binary | Expected | Result |
|--------|----------|--------|
| LPDDR4 Single | dual=False | ✅ dual=False |
| LPDDR4 Dual | dual=True | ✅ dual=True |
| LPDDR5 Single | dual=False | ✅ dual=False |
| LPDDR5 Dual | dual=True | ✅ dual=True |

All 4 reference binaries correctly detected.

## Key Offset Findings Documented

| Config | base_addr_id[0,1] | base_addr_id[2,3] | phy_base_addr_id[0,1] | phy_base_addr_id[2,3] |
|--------|-------------------|--------------------|-----------------------|-----------------------|
| LPDDR4 Single | 0x8C4,0x8C8 | 0x8CC,0x8D0 = N/A | 0x8D8,0x8DC | 0x8E0,0x8E4 = N/A |
| LPDDR4 Dual | 0x8C4-0x8D0 | valid | 0x8D8-0x8E4 | valid |
| LPDDR5 Single | 0x8CC,0x8D0 | 0x8D4,0x8D8 = N/A | 0x8E0,0x8E4 | 0x8E8,0x8EC = N/A |
| LPDDR5 Dual | 0x8CC-0x8D8 | valid | 0x8E0-0x8EC | valid |