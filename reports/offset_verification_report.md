# Report: GUI Binary Parsing Offset Fixes

## Date: 2026-04-03

## Summary
Fixed all binary parsing offsets in gui.py to correctly handle all 4 configurations:
- LPDDR4 Single Channel
- LPDDR4 Dual Channel  
- LPDDR5 Single Channel
- LPDDR5 Dual Channel

## Key Offsets Fixed

### LPDDR4 Fields (no header - struct starts directly at offset 0x800)
| Field | Offset (struct) | Notes |
|-------|----------------|-------|
| phy_freq_ratio | 0x0C | |
| omc_freq_ratio | 0x0E | |
| cpipe_depth | 0x14 | |
| dpipe_depth | 0x16 | |
| density | 0x1C | |
| rank_interleaving | 0x1E | |
| num_rank | 0x20 | Fixed from 0x0C |
| ctrl_dq_width | 0x24 | |
| dq_width | 0x24 | Same as ctrl_dq_width |
| dfs_lvl_t_ck[0-2] | 0x5E, 0x60, 0x62 | |

### Late Fields - Different by DDR type AND channel count

**LPDDR4 Single:**
- temp_sensing_period: 0xEC
- t_refipb/t_refiab: 0xF4
- t_zqcal: 0xF8
- mrr_byte_lane: 0x100

**LPDDR4 Dual:**
- zq_calibration_period: 0xF4
- temp_sensing_period: 0xFC
- t_refipb/t_refiab: 0x104
- t_zqcal: 0x108
- mrr_byte_lane: 0x110

**LPDDR5 Single (has 9-byte header):**
- zq_calibration_period: 0xEC
- temp_sensing_period: 0xF4
- t_refipb/t_refiab: 0xF8
- t_zqcal: 0x100
- mrr_byte_lane: 0x108

**LPDDR5 Dual:**
- zq_calibration_period: 0xFC
- temp_sensing_period: 0x104
- t_refipb/t_refiab: 0x108
- t_zqcal: 0x110
- mrr_byte_lane: 0x118

## Test Results
```
Binary Parse Test Suite: 10 passed, 0 failed
All late field tests: PASS for all 4 configurations
```

## Verification
All late fields now parse correctly:
- LP4 Single: temp=32000, t_ref=3904000, t_zq=1000000, mrr=0x55
- LP4 Dual: zq=48000, temp=32000, t_ref=3904000, t_zq=1000000, mrr=0x55
- LP5 Single: zq=48000, temp=32000, t_ref=488000, t_zq=1000000, mrr=0x55
- LP5 Dual: zq=48000, temp=32000, t_ref=488000, t_zq=1000000, mrr=0x55

## Status: COMPLETED