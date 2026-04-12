# DDR Binary Parameter Offsets Reference

## Overview

This document lists all parameter offsets in the DDR timing table binary format.

## Binary Structure

The binary file consists of two main sections:
1. **Timing Table** (offset 0x0000): Array of `timing_param` structs
2. **Orbit Config** (offset 0x0800): `orbit_config` struct

---

## Timing Table (Offset 0x0000)

### Entry Structure

Each `timing_param` entry is **296 bytes (0x128)**.

**Timing entries are indexed by period (t_ck value):**
- Entry 0: offset 0x0000 (t_ck = fastest / lowest period)
- Entry 1: offset 0x0128 (t_ck = next period)
- Entry 2: offset 0x0250, etc.

**Orbit config always starts at offset 0x0800** (fixed).

### Per-Entry Field Offsets

| Field | Offset | Size | Type | Notes |
|-------|--------|------|------|-------|
| freq | 0x00 | 4 | uint32 | Frequency in MHz |
| t_ck | 0x04 | 4 | uint32 | Clock period in ps |
| timing_zqcal | 0x08 | 4 | uint32 | ZQ calibration time |
| timing_param | 0x0C | 84 | uint32[21] | Array of 21 timing params |
| timing_param_derate | 0x54 | 8 | uint32[2] | Derate params |
| dfi_timing_param | 0x60 | 32 | uint32[8] | DFI timing params |

### Per-Density Arrays (indexed by density, not period)

**IMPORTANT**: These are arrays indexed by DRAM density (e.g., 2Gb, 4Gb, 8Gb), NOT by timing period.

| Field | Offset | Array Size | Element Size | Total Size | Notes |
|-------|--------|-------------|--------------|------------|-------|
| t_rfcab | 0x80 | OMC_NUM_DENSITIES | 2 | 14/20 bytes | RFC all banks (7/10 densities) |
| t_rfcpb | 0x8E | OMC_NUM_DENSITIES | 2 | 14/20 bytes | RFC per bank |
| t_rfmab | 0x9C | OMC_NUM_DENSITIES | 2 | 14/20 bytes | RFMR all banks |
| t_rfmpb | 0xAA | OMC_NUM_DENSITIES | 2 | 14/20 bytes | RFMR per bank |
| t_refdpr | 0xB8 | OMC_NUM_DENSITIES | 2 | 14/20 bytes | Refresh duty cycle |
| tx_pbr2pbr | 0xC6 | OMC_NUM_DENSITIES | 2 | 14/20 bytes | PBR to PBR |
| t_xsr | 0xD4 | OMC_NUM_DENSITIES | 2 | 14/20 bytes | Self refresh exit |
| t_xsdll | 0xE2 | OMC_NUM_DENSITIES | 2 | 14/20 bytes | DLL exit |
| t_xs_fast | 0xF0 | OMC_NUM_DENSITIES | 2 | 14/20 bytes | Fast exit |

**Density mapping:**
- LPDDR4: densities = [2, 3, 4, 6, 8, 12, 16] Gb (7 entries)
- LPDDR5: densities = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32] Gb (10 entries)

### Single-Value Fields

| Field | Offset | Size | Type | Notes |
|-------|--------|------|------|-------|
| wck_ratio | 0xFE | 1 | uint8 | WCK ratio |
| tlp_resp | 0xFF | 1 | uint8 | TLP response |
| auto_dqs_clean | 0x100 | 1 | uint8 | Auto DQS clean |
| dll_enable | 0x101 | 1 | uint8 | DLL enable |
| write_odt | 0x102 | 1 | uint8 | Write ODT enable flag |
| nt_odt | 0x103 | 1 | uint8 | Non-target ODT |
| write_dbi | 0x104 | 1 | uint8 | Write DBI enable flag |
| read_dbi | 0x105 | 1 | uint8 | Read DBI enable flag |
| wpste | 0x106 | 1 | uint8 | Write preamble training |
| rpste | 0x107 | 1 | uint8 | Read preamble training |
| rl | 0x108 | 1 | uint8 | Read latency |
| wl | 0x109 | 1 | uint8 | Write latency |
| mr_rl | 0x10A | 1 | uint8 | MR read latency |
| mr_wl | 0x10B | 1 | uint8 | MR write latency |
| mr_wr | 0x10C | 1 | uint8 | MR write |
| mr_rtp | 0x10D | 1 | uint8 | MR RTP |
| mr_cal | 0x10E | 1 | uint8 | MR calibration |
| mr_tccd_l | 0x10F | 1 | uint8 | MR CCD_L |
| bank_mode | 0x110 | 1 | uint8 | Bank mode |
| wck_fm | 0x111 | 1 | uint8 | WCK frequency mode |
| rdqs_pst_mode | 0x112 | 1 | uint8 | RDQS post mode |
| rdqs_pst | 0x113 | 1 | uint8 | RDQS post |
| rdqs_pre | 0x114 | 1 | uint8 | RDQS pre |
| wck_pst | 0x115 | 1 | uint8 | WCK post |
| wck_on | 0x116 | 1 | uint8 | WCK on |
| **read_link_parity** | **0x117** | **1** | **uint8** | **Read link ECC flag** |
| **write_link_parity** | **0x118** | **1** | **uint8** | **Write link ECC flag** |
| t_rtw | 0x119 | 1 | uint8 | Read to write |
| t_wtr_a | 0x11A | 1 | uint8 | Write to read auto |
| t_wtr | 0x11B | 1 | uint8 | Write to read |
| t_rc | 0x11C | 1 | uint8 | Read cycle |
| trddata_en | 0x11D | 1 | uint8 | Read data enable |
| (padding) | 0x11E-0x127 | 10 | - | Padding to 296 bytes |

### Timing Feature Calculation

To calculate timing feature "upto" values:
- For each timing entry (at offset 0x00, 0x128, 0x250, etc.), check the enable flag at entry-specific offset
- Find the maximum t_ck (offset +0x04) where the flag is enabled

| Feature | Entry+Offset | Notes |
|---------|-------------|-------|
| write_odt_upto | +0x102 (258) | Enable if value > 0 |
| write_dbi_upto | +0x104 (260) | Enable if value > 0 |
| read_dbi_upto | +0x105 (261) | Enable if value > 0 |
| read_lecc_upto | +0x117 (279) | LPDDR5 only |
| write_lecc_upto | +0x118 (280) | LPDDR5 only |

---

## Orbit Config (Offset 0x0800)

### LPDDR4 Offsets (DDR_TYPE=2)

| Field | Struct Offset | File Offset | Size | Type |
|-------|---------------|-------------|------|------|
| dram_boot | 0x00 | 0x800 | 1 | uint8 |
| ch_intr_size | 0x01 | 0x801 | 1 | uint8 |
| bg_intr_size | 0x02 | 0x802 | 1 | uint8 |
| fsp_op | 0x03 | 0x803 | 1 | uint8 |
| fsp_wr | 0x04 | 0x804 | 1 | uint8 |
| dq_vref_byte0 | 0x05 | 0x805 | 2 | uint8[2] |
| dq_vref_byte1 | 0x07 | 0x807 | 2 | uint8[2] |
| ca_vref | 0x09 | 0x809 | 2 | uint8[2] |
| **phy_freq_ratio** | **0x0C** | **0x80C** | **2** | **uint16** |
| **omc_freq_ratio** | **0x0E** | **0x80E** | **2** | **uint16** |
| int_cpipe_depth | 0x10 | 0x810 | 2 | uint16 |
| int_dpipe_depth | 0x12 | 0x812 | 2 | uint16 |
| **cpipe_depth** | **0x14** | **0x814** | **2** | **uint16** |
| **dpipe_depth** | **0x16** | **0x816** | **2** | **uint16** |
| reboot | 0x18 | 0x818 | 2 | uint16 |
| reqq_depth | 0x1A | 0x81A | 2 | uint16 |
| **density** | **0x1C** | **0x81C** | **2** | **uint16** |
| **rank_interleaving** | **0x1E** | **0x81E** | **2** | **uint16** |
| **num_rank** | **0x20** | **0x820** | **2** | **uint16** |
| reboot_with_mrw | 0x22 | 0x822 | 2 | uint16 |
| ctrl_dq_width | 0x24 | 0x824 | 2 | uint16 |
| dq_width | 0x26 | 0x826 | 2 | uint16 |
| use_dfi_train_if | 0x28 | 0x828 | 2 | uint16 |
| phy_ind_mode_en | 0x2A | 0x82A | 2 | uint16 |
| phy_low_power | 0x2C | 0x82C | 2 | uint16 |
| phy_idle_cnt_th | 0x2E | 0x82E | 2 | uint16 |
| lp_wakeup | 0x30 | 0x830 | 6 | uint16[3] |
| half_dq_en | 0x36 | 0x836 | 2 | uint16 |
| lpddr4_rpre | 0x38 | 0x838 | 2 | uint16 |
| rfm_en | 0x3A | 0x83A | 2 | uint16 |
| dsm_en | 0x3C | 0x83C | 2 | uint16 |
| eye_scan_rd_en | 0x3E | 0x83E | 2 | uint16 |
| eye_scan_wr_en | 0x40 | 0x840 | 2 | uint16 |
| eye_scan_prbs_rd_en | 0x42 | 0x842 | 2 | uint16 |
| eye_scan_prbs_wr_en | 0x44 | 0x844 | 2 | uint16 |
| ca_odt | 0x46 | 0x846 | 2 | uint16 |
| phy_odt | 0x48 | 0x848 | 2 | uint16 |
| init_zq_calibration | 0x4A | 0x84A | 2 | uint16 |
| temp_sensing | 0x4C | 0x84C | 2 | uint16 |
| zq_calibration | 0x4E | 0x84E | 2 | uint16 |
| periodic_training | 0x50 | 0x850 | 2 | uint16 |
| periodic_training_period | 0x52 | 0x852 | 2 | uint16 |
| dynamic_power_down | 0x54 | 0x854 | 2 | uint16 |
| dynamic_self_refresh | 0x56 | 0x856 | 2 | uint16 |
| regional_clock_gating | 0x58 | 0x858 | 2 | uint16 |
| phy_clock_gating | 0x5A | 0x85A | 2 | uint16 |
| dram_clock_gating | 0x5C | 0x85C | 2 | uint16 |
| dfs_lvl_t_ck[0] | 0x5E | 0x85E | 2 | uint16 |
| dfs_lvl_t_ck[1] | 0x60 | 0x860 | 2 | uint16 |
| dfs_lvl_t_ck[2] | 0x62 | 0x862 | 2 | uint16 |
| num_of_region | 0x64 | 0x864 | 2 | uint16 |
| command_bus_training | 0x66 | 0x866 | 2 | uint16 |
| ca_vref_training | 0x68 | 0x868 | 2 | uint16 |
| prbs_training | 0x6A | 0x86A | 2 | uint16 |
| reboot_with_training | 0x6C | 0x86C | 2 | uint16 |
| dfs_training | 0x6E | 0x86E | 2 | uint16 |
| phy_vref_trn_mode | 0x72 | 0x872 | 2 | uint16 |
| phy_duty_trn_mode | 0x74 | 0x874 | 2 | uint16 |
| dram_vref_trn_mode | 0x76 | 0x876 | 2 | uint16 |
| dram_duty_trn_mode | 0x78 | 0x878 | 2 | uint16 |
| **density_code** | **0x78** | **0x878** | **4** | **uint32** |
| rclk_t_ck | 0x7C | 0x87C | 4 | uint32 |
| boot_t_ck | 0x80 | 0x880 | 4 | uint32 |
| boot_t_ck_low | 0x84 | 0x884 | 4 | uint32 |
| dram_t_ck | 0x88 | 0x888 | 4 | uint32 |
| prev_dram_t_ck | 0x8C | 0x88C | 4 | uint32 |
| chip[0] | 0x90 | 0x890 | 20 | chip_config |
| chip[1] | 0xA4 | 0x8A4 | 20 | chip_config |
| num_of_ch | 0xB8 | 0x8B8 | 8 | uint32[2] |
| base_addr | 0xC0 | 0x8C0 | 4 | uint32 |
| base_addr_id[0] | 0xC4 | 0x8C4 | 4 | uint32 |
| base_addr_id[1] | 0xC8 | 0x8C8 | 4 | uint32 |
| base_addr_id[2] | 0xCC | 0x8CC | 4 | uint32 |
| base_addr_id[3] | 0xD0 | 0x8D0 | 4 | uint32 |
| phy_base_addr | 0xD4 | 0x8D4 | 4 | uint32 |
| phy_base_addr_id[0] | 0xD8 | 0x8D8 | 4 | uint32 |
| phy_base_addr_id[1] | 0xDC | 0x8DC | 4 | uint32 |
| phy_base_addr_id[2] | 0xE0 | 0x8E0 | 4 | uint32 |
| phy_base_addr_id[3] | 0xE4 | 0x8E4 | 4 | uint32 |

### LPDDR5 Offsets (DDR_TYPE=5)

The LPDDR5 struct has additional fields at the beginning (9 bytes for lp5_mr* and zq_bg_mode).

| Field | Struct Offset | File Offset | Size | Type |
|-------|---------------|-------------|------|------|
| lp5_mr2 | 0x0D | 0x80D | 1 | uint8 |
| lp5_mr3 | 0x0E | 0x80E | 1 | uint8 |
| lp5_mr10 | 0x0F | 0x80F | 1 | uint8 |
| lp5_mr11 | 0x10 | 0x810 | 1 | uint8 |
| lp5_mr12 | 0x11 | 0x811 | 1 | uint8 |
| lp5_mr16 | 0x12 | 0x812 | 1 | uint8 |
| lp5_mr17 | 0x13 | 0x813 | 1 | uint8 |
| lp5_mr18 | 0x14 | 0x814 | 1 | uint8 |
| zq_bg_mode | 0x15 | 0x815 | 1 | uint8 |
| **phy_freq_ratio** | **0x0C** | **0x80C** | **2** | **uint16** |
| **omc_freq_ratio** | **0x0E** | **0x80E** | **2** | **uint16** |
| ... (rest similar to LPDDR4, but shifted by 9 bytes) ... |
| **density** | **0x24** | **0x824** | **2** | **uint16** |
| **rank_interleaving** | **0x1E** | **0x81E** | **2** | **uint16** |
| **num_rank** | **0x20** | **0x820** | **2** | **uint16** |
| **density_code** | **0x80** | **0x880** | **4** | **uint32** |
| dfs_lvl_t_ck[0] | 0x64 | 0x864 | 2 | uint16 |
| dfs_lvl_t_ck[1] | 0x66 | 0x866 | 2 | uint16 |
| dfs_lvl_t_ck[2] | 0x68 | 0x868 | 2 | uint16 |

---

## GUI Parsing Reference

### Current GUI Implementation (gui.py)

| Param | Current Offset | Status |
|-------|-----------------|--------|
| density | 0x1c (LP4) / 0x24 (LP5) | ✅ Correct |
| density_code | Not parsed | ❌ Hardcoded |
| cpipe_depth | 0x30 | ❌ Wrong (should be 0x14) |
| dpipe_depth | 0x32 | ❌ Wrong (should be 0x16) |
| rank_interleaving | 0x3a | ❌ Wrong (should be 0x1e) |
| num_rank | 0x3c | ❌ Wrong (should be 0x20) |
| dfs_lvl_t_ck | 0x5e/0x60/0x62 | ✅ Correct |
| omc_freq_ratio | Hardcoded | ❌ Not parsed |
| phy_freq_ratio | Hardcoded | ❌ Not parsed |
| write_odt_upto | Hardcoded | ❌ Not parsed |
| read_dbi_upto | Hardcoded | ❌ Not parsed |
| write_dbi_upto | Hardcoded | ❌ Not parsed |
| read_lecc_upto | Hardcoded 0 | ✅ Fixed |
| write_lecc_upto | Hardcoded 0 | ✅ Fixed |

---

## File Size Reference

| Configuration | Size (bytes) |
|---------------|---------------|
| LPDDR4 Single | 5096 |
| LPDDR5 Single | 5104 |
| LPDDR4 Dual | 7864 |
| LPDDR5 Dual | 7872 |

---

## Generated: 2026-04-03