# DDR Timing Table Generation Tool

Unified tool for generating DDR timing tables and orbit configuration binaries for Glenfly's Orbit memory controllers and SPHY-V9R8 PHY.

## Features

- **Unified CLI**: Single command generates both timing parameters and orbit configuration
- **Binary Compatibility**: Python and C implementations produce identical output
- **Flexible Configuration**: CLI arguments, JSON overrides, or Python/C implementation choice
- **DRAM Support**: LPDDR4 and LPDDR5 with single/dual channel configurations
- **Dynamic Structs**: Python implementation creates orbit_config classes based on DRAM type

## Quick Start

```bash
# Generate timing table with default orbit config (C implementation)
python3 gen_timing_params --dram-type lpddr4 --densities 8 --phy-name sphy-v9r8 1000

# Use Python implementation with custom parameters
python3 gen_timing_params --dram-type lpddr4 --densities 8 --phy-name sphy-v9r8 \
    --orbit-config-use-python --orbit-rank-interleaving 0 --orbit-num-rank 1 1000

# Use JSON overrides
python3 gen_timing_params --dram-type lpddr4 --densities 8 --phy-name sphy-v9r8 \
    --orbit-config-json custom_config.json 1000
```

## Architecture

### Core Components
- `gen_timing_params`: Main unified UI (modified original + orbit config integration)
- `gui.py`: Web-based GUI (runs in browser at http://localhost:5000)
- `orbit_config.py`: Python ctypes implementation of orbit_config struct
- `ddr_config_init.py`: Python implementation of ddr_config_init() 
- `gen_ddr_config`: Original C compiler wrapper
- `ddr_config_bin.c`: C binary generator

### Binary Output
- **Timing tables**: Written at offset 0 in `ddr_timing_table.bin`
- **Orbit config**: Written at offset 0x800 (EMMC_CM4_TIME_TB_SIZE) in same file
- **Struct sizes**: 3048 bytes (LPDDR4 single), 5816 bytes (LPDDR4 dual)

## CLI Parameters

### Timing Parameters (Original)
All original `gen_timing_params` arguments supported:
- `--dram-type`: LPDDR4 or LPDDR5
- `--densities`: List of target densities (Gb)
- `--phy-name`: PHY name (e.g., sphy-v9r8)
- `--periods`: Target tCK/tWCK values (ps)
- Plus timing feature flags, LPDDR4/5 options, etc.

### Orbit Configuration (New)
- `--two-channel`: Enable two-channel mode
- `--orbit-byte-mode`: Byte mode for LPDDR4 (0=x16, 1=x8)
- `--orbit-mixed`: Mixed rank density flag
- `--orbit-rank-interleaving`: Rank interleaving enable
- `--orbit-num-rank`: Number of ranks (max 2)
- `--orbit-reboot-with-mrw`: Reboot with MRW
- `--orbit-rfm-en`: RFM enable (LPDDR4/LPDDR5)
- `--orbit-dsm-en`: DSM enable (LPDDR5 Deep Sleep Mode)
- `--orbit-ca-odt`: CA ODT enable
- `--orbit-config-density`: Density (Gb) for orbit_config (defaults to first --densities or 16)
- `--orbit-config-json`: JSON file with field overrides
- `--orbit-config-use-python`: Use Python instead of C implementation

## Web GUI

Run the web-based GUI:

```bash
python3 gui.py
```

Then open http://localhost:5000 in your browser.

Features:
- All CLI parameters exposed in categorized sections
- Dynamic periods with add/remove buttons
- ps/MHz unit toggle for timing values
- dram_t_ck field (base timing cycle: 471ps LPDDR4, 1256ps LPDDR5)
- DRAM type override dropdown for manual selection
- Tooltips on all labels
- Load/Save JSON configuration
- Generate binary and header with modified parameters
- Analyze generated binary (timing table + orbit config)
- zq_bg_mode field (LPDDR5)
- Visibility toggles:
  - zq-calibration-period (shows when zq-calibration checked)
  - periodic-training-period (shows when periodic-training checked)
  - temp-sensing-period (shows when temp-sensing checked)
  - dsm-en (shows only for LPDDR5)
  - rank-interleaving (shows when num-rank=2)

## Testing

```bash
# Run LPDDR4 binary generation test
./test_lpddr4.sh

# Run LPDDR5 binary generation test
./test_lpddr5.sh

# Run GUI parameter tests
python3 test_gui_params.py
```

## JSON Configuration

Use `orbit_config_template.json` as a starting point for custom overrides:

```json
{
  "rank_interleaving": 1,
  "num_rank": 2,
  "dfs_lvl_t_ck": [938, 1631, 2500]
}
```

## File Structure

```
├── gen_timing_params              # Main unified UI
├── gui.py                         # Web-based GUI
├── templates/gui.html             # GUI HTML template
├── orbit_config.py                # Python orbit_config structures
├── ddr_config_init.py             # Python ddr_config_init
├── orbit_config_template.json     # JSON template
├── test_binary_match.py           # Compatibility test
├── gen_ddr_config                 # C wrapper
├── ddr_config_bin.c               # C binary generator
├── ddr_config.h.template          # C header template
└── reports/                       # Documentation
```

## Testing

```bash
# Test binary compatibility
python3 test_binary_match.py

# Test LPDDR4
chmod +x test_lpddr4.sh
./test_lpddr4.sh

# Test LPDDR5
chmod +x test_lpddr5.sh
./test_lpddr5.sh
```

## Recent Updates (2026-04-09)

### LP5 Binary Parsing Fixes

Fixed several issues in `gui.py` for correct LPDDR5 binary parsing:

1. **Entry Size**: LP5 uses different entry size (0x15C/348 bytes) than LP4 (0x128/296 bytes)
2. **Orbit Config Offsets**: Fixed LP5-specific offsets for:
   - `dfs_lvl_t_ck`: 0x63→0x64, 0x65→0x66, 0x67→0x68
   - `density_code`: 0xA5→0x80
3. **LP5 Default Periods**: Updated to use t_wck values (314, 418, 556, 2500)

### Test Coverage

```bash
# Timing entry validation test (8 tests)
python3 test_timing_entry_validation.py

# Random value flow test (452 tests)
python3 test_random_value_flow.py
```

All tests pass:
- `test_timing_entry_validation.py`: 8/8 passed
- `test_random_value_flow.py`: 452/452 passed

## Density Code Mapping

| Density (Gb) | Density Code |
|--------------|--------------|
| 1 | 0 |
| 2 | 1 |
| 3 | 2 |
| 4 | 3 |
| 6 | 4 |
| 8 | 5 |
| 12 | 6 |
| 16 | 7 |
| 24 | 8 |
| 32 | 9 |

Use `--orbit-config-density` to set the orbit config density (defaults to first `--densities` value or 16).

## License

Proprietary - Glenfly Technology

---

**Version**: glenfly_chin_rel7_230725  
**Generated**: 2026-03-31  
**Integration Status**: Complete - Unified timing and orbit config generation
