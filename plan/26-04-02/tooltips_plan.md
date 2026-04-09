# Implementation Plan - Add Tooltips to GUI Fields

## Date: 2026-04-02

---

## Overview

Add `title` attribute (tooltips) to all label elements in Pipe Configuration and Orbit Configuration sections.

---

## Implementation

### Pipe Configuration (5 fields)

| Field | Tooltip |
|-------|---------|
| cpipe-depth | Command pipe depth (auto-set based on DDR type) |
| dpipe-depth | Data pipe depth (auto-set based on DDR type) |
| omc-freq-ratio | OMC frequency ratio (auto-set: LPDDR4=2, LPDDR5=1) |
| phy-freq-ratio | PHY frequency ratio (auto-set: LPDDR4=2, LPDDR5=1) |
| wire-length | Wire length in mil (milli-inch), not ps |

### Orbit Configuration (~28 fields)

**Basic/Geometry**:
- two-channel: Enable dual channel mode
- orbit-config-density: DRAM density in Gb
- orbit-byte-mode: Byte mode: x16 (0) or x8 (1)
- orbit-mixed: Mixed mode doubles total density

**Mode Control**:
- orbit-rank-interleaving: Enable rank interleaving
- orbit-num-rank: Number of ranks (1 or 2)
- orbit-reboot-with-mrw: Reboot with MRW (Mode Register Write)
- reboot-with-training: Reboot with training

**Training Enable** (11 fields):
- eye-scan-rd-en: Eye scan read enable
- eye-scan-wr-en: Eye scan write enable
- eye-scan-prbs-rd-en: Eye scan PRBS read enable
- eye-scan-prbs-wr-en: Eye scan PRBS write enable
- phy-vref-trn-mode: PHY Vref training mode
- phy-duty-trn-mode: PHY duty training mode
- dram-vref-trn-mode: DRAM Vref training mode
- dram-duty-trn-mode: DRAM duty training mode
- command-bus-training: Command bus training enable
- ca-vref-training: CA Vref training enable
- prbs-training: PRBS training enable

**Power Management** (4 fields):
- regional-clock-gating: Regional clock gating enable
- dram-clock-gating: DRAM clock gating enable
- phy-clock-gating: PHY clock gating enable
- phy-low-power: PHY low power mode

**Timing Intervals** (5 fields):
- zq-calibration-period: ZQ calibration period in tCK
- periodic-training-period: Periodic training period in tCK
- temp-sensing-period: Temperature sensing period in tCK
- t-refi-ab: Average refresh interval in tCK
- t-refi-pb: Per-bank refresh interval in tCK

---

## Status

- [ ] Plan saved
- [ ] Pipe Configuration tooltips added
- [ ] Orbit Configuration tooltips added
- [ ] Tests executed
- [ ] Report generated