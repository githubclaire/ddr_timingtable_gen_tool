# DDR Timing Table Generator - Offset Fix Plan

## Tasks

### 1. Update offset_reference_v2.md
- Add complete offset tables for all 4 configurations:
  - LPDDR4 Single Channel
  - LPDDR4 Dual Channel
  - LPDDR5 Single Channel
  - LPDDR5 Dual Channel
- Document differences in base_addr_id and phy_base_addr_id arrays (2 vs 4 elements)
- Update all affected offsets from base_addr onwards

### 2. Fix gui.py dual channel detection
- Line 432 hardcodes offset 0x8E0 for phy_base_addr_id[2]
- This fails for LPDDR5 (should be 0x8E8 due to 9-byte header shift)
- Make offset dynamic based on DRAM type detection
- Use correct offset: LPDDR4=0x8E0, LPDDR5=0x8E8

## Implementation Steps

1. Read current offset_reference_v2.md
2. Add LPDDR5 offset tables to document
3. Update gui.py to use dynamic offset for dual channel detection
4. Verify changes with test parsing
5. Create implementation report in ./reports