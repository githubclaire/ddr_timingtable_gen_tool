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
- **Per-DRAM image**: 4096 bytes, matching the SCP build
  - Timing table: offset 0x000..0x7FF (max 6 LP4 / 5 LP5 entries)
  - Orbit config prefix: offset 0x800, length 360 bytes (single) / 408 bytes (dual)
  - Remaining bytes: zero padding to 4 KiB
- **Runtime-only data**: `prbs_result` / `train_result` are not written to the image
- **Config prefix**: ends at `offsetof(struct orbit_config, prbs_result)`

The full `orbit_config` ctypes struct is still 3112 bytes (single) / 5912 bytes (dual);
only the configuration prefix is serialized.  The GUI accepts both the 4 KiB SCP
image and older full-struct images, identifying DRAM type/channel from the
orbit prefix content instead of file size.

### Source of truth
The orbit_config layout and defaults track these SCP-firmware headers:

- `product/arise2/module/arise2_omc/include/arise2_omc.h` (struct layout)
- `product/arise2/module/arise2_omc/include/ddr_config.h` (defaults / boot-frequency logic)

`tests/test_struct_layout.sh` compiles the C header and diffs every field offset against `orbit_config.py`, so layout drift is caught automatically. `tests/test_c_python_parity.py` checks the Python and C generators produce byte-identical binaries.

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
- `--orbit-num-rank`: Number of ranks (max 2, default 1)
- `--orbit-reboot-with-mrw`: Reboot with MRW (default 1)
- `--orbit-rfm-en`: RFM enable (LPDDR4/LPDDR5, default 1)
- `--orbit-dsm-en`: DSM enable (LPDDR5 Deep Sleep Mode)
- `--orbit-ca-odt`: CA ODT enable (default 1)
- `--orbit-phy-odt`: PHY ODT value (default 5)
- `--orbit-otd-ck/--orbit-otd-cs/--orbit-otd-ca`: CK/CS/CA ODT termination (default 1)
- `--orbit-zq-bg-mode`: LPDDR5 ZQ background mode (default 1)
- `--orbit-default-ch`: Single-channel default OMC (0 or 1)
- `--orbit-freq-level`: `DDR_FREQ_LEVEL` 0-3; drops that many fastest boot points
- `--orbit-lp5-freq-set`: LPDDR5 boot table `6000` (default) or `6400`
- `--orbit-initial-training`, `--orbit-command-bus-training`, `--orbit-ca-vref-training`,
  `--orbit-prbs-training`, `--orbit-reboot-with-training`: training controls (default 1)
- `--orbit-phy-vref-trn-mode`, `--orbit-phy-duty-trn-mode`,
  `--orbit-dram-vref-trn-mode`, `--orbit-dram-duty-trn-mode`: calibration modes (default 1)
- `--orbit-init-zq-calibration`, `--orbit-zq-calibration`: ZQ calibration (default 1)
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
- Boot frequency controls: `freq-level` (0-3) and LP5 `6000/6400` table selector;
  DFS levels auto-fill from the selected table
- Training/ODT controls matching current `ddr_config.h` defaults
  (initial/command-bus/CA-vref/PRBS/reboot training, PHY ODT, OTD CK/CS/CA)
- Visibility toggles:
  - zq-calibration-period (shows when zq-calibration checked)
  - periodic-training-period (shows when periodic-training checked)
  - temp-sensing-period (shows when temp-sensing checked)
  - dsm-en (shows only for LPDDR5)
  - rank-interleaving (shows when num-rank=2)

## Testing

```bash
# Run the full suite (struct layout, C/Python parity, golden refs, GUI checks)
python3 -m unittest discover -v tests

# Specific gates
./tests/test_struct_layout.sh
python3 -m unittest tests.test_c_python_parity -v
python3 -m unittest tests.test_golden_refs -v
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
python3 -m unittest tests.test_c_python_parity -v

# Test LPDDR4 / LPDDR5 pinned outputs
python3 -m unittest tests.test_timing_lpddr4 tests.test_timing_lpddr5 -v
```

## Recent Updates (2026-11-06)

### 4 KiB images and timing parser fixes

- Generated images now match the SCP build layout: 4096 bytes, timing table
  at 0x000, orbit_config prefix at 0x800 (360 B single / 408 B dual), zero
  padded. Runtime `prbs_result`/`train_result` data is not stored.
- GUI binary analysis identifies DRAM type and channel from the orbit prefix
  content, not file size (all per-DRAM images are 4 KiB).
- Fixed timing_param parsing offsets:
  - density arrays start at 0x88, with per-density stride (LP4 7x2 B,
    LP5 10x2 B) instead of a fixed 0x14 stride
  - each timing entry now exposes all nine density arrays
  - common/per-entry offsets derived from density count (0x106/0x110 LP4,
    0x13C/0x146 LP5)
  - entries are no longer dropped when ODT/DBI/Link-ECC flags are all zero
- Added `tools/compare_timing_parse.py` and
  `tests/test_timing_parse_compare.py`: an independent ctypes parser compares
  every `struct timing_param` field against the GUI parser.
- Added `tests/test_gui_matrix.py`: end-to-end GUI case matrix (LP4/LP5,
  single/dual, ranks, densities, byte/mixed, all frequency levels, 6000/6400,
  training toggles, thresholds, custom DFS, low power, timing-only images,
  original SCP 4 KiB artifacts).
- Added `tests/test_ui_roundtrip.py`: every form control is classified as
  exact-roundtrip, derived-roundtrip, or non-roundtrip (with reason); a
  completeness gate fails if a new control has no case.
- Added `tests/test_ui_param_coverage.py`: executes every UI parameter,
  every select option, every timing threshold, each period slot, and the
  ps/MHz conversion list.
- Added `tests/test_gui_server.py`: HTTP-level tests for the real server
  endpoints (`/preview-cmd`, `/generate`, `/analyze`, `/save-json`,
  `/load-json-path`, `/browse`).
- Added `tests/test_ddr_config_init.py`: direct defaults/override/
  serialization tests.
- Added `tests/test_build_scp_parity.py`: parses the timing-table
  command/frequency tables directly from `arise2/build/scp.mk`, runs the
  build-style CLI and the GUI form path, and asserts byte-identical 4 KiB
  images for LP4/LP5, single/dual channel and all DDR_FREQ_LEVELs.
- Added `tests/test_original_toolchain_compare.py`: runs the original
  `arise2/toolchains/ddr_timingtable_gen_tool`, assembles the image exactly
  like scp.mk, and compares it with the GUI image field-by-field. Only two
  intentional fixes are tolerated (LPDDR5 WCK always-on window and LPDDR4
  canonical density_code); any other difference fails.
- Test suite: 138 tests, all passing.
- Coverage (`make coverage`): overall 92%, gui.py 88%,
  ddr_config_init.py 95%, orbit_config.py 100%.

### SCP-firmware layout/default sync

- Rebuilt `orbit_config.py` from the 2026-10-26 struct: per-PHY DQ/CA vref
  arrays, `phy_dq_vref_*`, `dcm_mr30`, `omc_channel`, `ca_vref_valid`,
  `dram_vref_valid`, `ca_vref_vwm_sum`, LP4/LP5 MR fields, `otd_ck/cs/ca`,
  `initial_training`, DRAM-vref caches and the relocated
  `timingtable_size`.
- Updated defaults to the 2026-11-05 `ddr_config.h`: `rclk_t_ck=20000`,
  `num_rank=1`, training on by default, `phy_odt=5`, OTD on,
  periodic training 50000us, dynamic power thresholds 2048,
  LP5 `link_err_cnt_th=2`, boot table 1332/1428/1672/2512 (max6000).
- Added `DDR_FREQ_LEVEL`, LP5 max6400 table selection, single-channel OMC
  selection, byte-mode/mixed and DQ width to both C and Python paths.
- Struct sizes are now 3112 B (single) / 5912 B (dual).
- GUI updated with boot-frequency/DFS controls and training/ODT options;
  binary analysis reads all fields through ctypes (no hand-maintained
  orbit offsets).
- Removed fields no longer present in the struct (`eye_scan_*`,
  `dfs_training`).
- All 92 tests pass; `test_c_python_parity` verifies byte identity across
  LP4/LP5, single/dual, densities 8/16/32, and frequency levels.

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
