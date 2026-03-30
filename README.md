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
# Alternative using wrapper (identical arguments):
python3 ddr_config_ui.py --dram-type lpddr4 --densities 8 --phy-name sphy-v9r8 1000

# Use Python implementation with custom parameters
python3 gen_timing_params --dram-type lpddr4 --densities 8 --phy-name sphy-v9r8 \
    --orbit-config-use-python --orbit-rank-interleaving 0 --orbit-num-rank 1 1000
# Wrapper automatically uses Python implementation:
python3 ddr_config_ui.py --dram-type lpddr4 --densities 8 --phy-name sphy-v9r8 \
    --orbit-rank-interleaving 0 --orbit-num-rank 1 1000

# Use JSON overrides
python3 gen_timing_params --dram-type lpddr4 --densities 8 --phy-name sphy-v9r8 \
    --orbit-config-json custom_config.json 1000
# Wrapper equivalent:
python3 ddr_config_ui.py --dram-type lpddr4 --densities 8 --phy-name sphy-v9r8 \
    --orbit-config-json custom_config.json 1000
```

## Architecture

### Core Components
- `gen_timing_params`: Main unified UI (modified original + orbit config integration)
- `ddr_config_ui.py`: Alternative wrapper UI with identical CLI parameters
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
- `--orbit-config-json`: JSON file with field overrides
- `--orbit-config-use-python`: Use Python instead of C implementation

## JSON Configuration

Use `orbit_config_template.json` as a starting point for custom overrides:

```json
{
  "rank_interleaving": 1,
  "num_rank": 2,
  "rfm_en": 0,
  "dsm_en": 0,
  "ca_odt": 0,
  "eye_scan_rd_en": 0,
  "temp_sensing_period": 32000,
  "dynamic_self_refresh": 0,
  "regional_clock_gating": 1
}
```

## Testing

```bash
# Verify binary compatibility between Python and C implementations
python3 test_binary_match.py

# Generate and compare outputs
rm -f ddr_timing_table.bin
python3 gen_timing_params --dram-type lpddr4 --densities 8 --phy-name sphy-v9r8 1000
python3 gen_timing_params --dram-type lpddr4 --densities 8 --phy-name sphy-v9r8 \
    --orbit-config-use-python 1000
python3 test_binary_match.py  # Should report "SUCCESS: Binary matches exactly!"

# Test wrapper interface
rm -f ddr_timing_table.bin
python3 ddr_config_ui.py --dram-type lpddr4 --densities 8 --phy-name sphy-v9r8 1000
python3 test_binary_match.py  # Verify wrapper produces identical output

# Run comprehensive shell tests (delete binaries before generation)
chmod +x test_lpddr5.sh test_lpddr4.sh
./test_lpddr5.sh  # LPDDR5 compatibility test
./test_lpddr4.sh  # LPDDR4 compatibility test

# Test JSON override functionality
python3 test_json_override.py  # Verify JSON field overrides work
```

## Development

### Key Integration Points
1. **Modified `gen_timing_params`**: Added orbit config argument group and generation function
2. **Dynamic struct creation**: `make_orbit_config_class()` generates appropriate ctypes classes
3. **Density code mapping**: Enhanced `orbit_init_gen.h` generation for compatibility
4. **Binary assembly**: Orbit config written at offset 0x800 in output file

### File Structure
```
├── gen_timing_params              # Main unified UI
├── ddr_config_ui.py               # Alternative wrapper UI (identical CLI)
├── orbit_config.py                # Python orbit_config structures
├── ddr_config_init.py             # Python ddr_config_init
├── orbit_config_template.json     # JSON template
├── test_binary_match.py           # Compatibility test
├── gen_ddr_config                 # C wrapper
├── ddr_config_bin.c               # C binary generator
├── setup_github.sh                # GitHub repository setup helper
└── reports/                       # Documentation
```

## GitHub Repository Setup

Use `setup_github.sh` to easily create a GitHub repository and push your code:

```bash
# Make script executable
chmod +x setup_github.sh

# Run the setup script
./setup_github.sh
```

The script will guide you through:
1. Configuring remote origin (SSH or HTTPS)
2. Creating the repository on GitHub (if needed)
3. Pushing your code to GitHub

## License

Proprietary - Glenfly Technology

---

**Version**: glenfly_chin_rel7_230725  
**Generated**: 2026-03-30  
**Integration Status**: Complete - Unified timing and orbit config generation