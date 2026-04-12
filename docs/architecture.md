# Architecture

## 1. System Purpose

This repository generates a combined DDR configuration binary for Glenfly Orbit memory controllers and the SPHY-V9R8 PHY.

The main product is `ddr_timing_table.bin`, which contains two logical regions:

- Timing table data at file offset `0x0000`
- `orbit_config` data at file offset `0x0800`

The codebase supports:

- LPDDR4 and LPDDR5
- Single-channel and dual-channel orbit-config layouts
- A Python orbit-config generation path and a legacy C reference path
- A local browser GUI for generation and reverse analysis

## 2. Main Entry Points

| Entry point | Role |
| --- | --- |
| `gen_timing_params` | Main CLI. Computes timing entries, writes helper headers/C output, creates `ddr_timing_table.bin`, then appends orbit-config data. |
| `gui.py` | Local HTTP server that serves `templates/gui.html`, calls the CLI, and parses existing binaries back into UI-friendly JSON. |
| `gen_ddr_config` | Wrapper that compiles and runs the C reference orbit-config generator. |

## 3. High-Level Component Model

### 3.1 Timing Generation Subsystem

- `gen_timing_params`
- `timing.py`
- `dram_config.py`
- `lpddr4_config.py`
- `lpddr5_config.py`
- `phy_config.py`
- `sphy_v9r8_config.py`
- `orbit_defines.py`

This subsystem converts user parameters into packed timing-table entries.

### 3.2 Orbit-Config Subsystem

- `orbit_config.py`
- `ddr_config_init.py`
- `ddr_config.h`
- `ddr_config_bin.c`
- `gen_ddr_config`
- `arise2_omc.h`
- `arise2_config.h`

This subsystem builds the `orbit_config` struct that starts at offset `0x800`.

### 3.3 GUI and Binary Analysis Subsystem

- `gui.py`
- `templates/gui.html`

This subsystem exposes the CLI through a browser and provides binary reverse parsing.

### 3.4 Validation and Reference Assets

- `test_*.py`
- `test_*.sh`
- committed `.ref.bin` binaries

This subsystem validates Python/C compatibility, GUI round-trips, parser correctness, and parameter coverage.

## 4. Runtime Flow

### 4.1 Generation Flow

```text
CLI or GUI request
  -> gen_timing_params
     -> parse_args()
     -> GenTimingParam(args)
        -> choose PHY model (sphy_v9r8_config)
        -> choose DRAM model (lpddr4_config or lpddr5_config)
     -> calculate timing entries for each requested period
     -> write orbit_timing_params.c
     -> write orbit_init_gen.h
     -> write mr_config_gen.h
     -> pack timing entries into ddr_timing_table.bin
     -> generate_orbit_config_bin(args)
        -> Python path: ddr_config_init.generate_orbit_config_binary(...)
        -> C path: gen_ddr_config -> gcc -> ddr_config_bin.c
```

### 4.2 GUI Flow

```text
Browser
  -> GET /
     -> gui.py serves templates/gui.html

Browser generate action
  -> POST /generate
     -> gui.py builds CLI args
     -> gui.py writes orbit_config_override.json
     -> gui.py runs gen_timing_params
     -> response returns stdout/stderr summary

Browser analyze action
  -> POST /analyze
     -> gui.py reads binary file
     -> infers DRAM type/channel mode
     -> parses timing entries and orbit-config fields
     -> returns JSON for the UI to display and refill
```

## 5. Binary Outputs and Layout

### 5.1 Timing Table Region

- Starts at offset `0x0000`
- Entry size depends on DRAM type because density-array lengths differ:
  - LPDDR4: `0x128` bytes (`296`)
  - LPDDR5: `0x15C` bytes (`348`)
- Each entry contains:
  - frequency and period metadata
  - 21 packed timing words
  - 2 derate words
  - 8 DFI timing words
  - density-dependent timing arrays
  - trailing per-entry flags and latency bytes

### 5.2 Orbit-Config Region

- Starts at offset `0x0800`
- Layout varies by DRAM type and channel mode because LPDDR5 adds header fields and dual-channel mode enlarges address/result arrays

| Variant | Struct size | Total file size |
| --- | ---: | ---: |
| LPDDR4 single | 3048 | 5096 |
| LPDDR5 single | 3056 | 5104 |
| LPDDR4 dual | 5816 | 7864 |
| LPDDR5 dual | 5824 | 7872 |

## 6. Directory and File Roles

### 6.1 Primary Runtime Files

- `gen_timing_params`: main CLI and timing binary writer
- `gui.py`: local server and binary analyzer
- `orbit_config.py`: Python `ctypes` struct factory for orbit-config variants
- `ddr_config_init.py`: Python equivalent of `ddr_config_init`
- `lpddr4_config.py` and `lpddr5_config.py`: DRAM-specific timing rules
- `sphy_v9r8_config.py`: PHY-specific timing behavior

### 6.2 C Reference Path

- `ddr_config.h`: C implementation of orbit-config initialization
- `ddr_config_bin.c`: writes the C struct into the binary at `0x800`
- `gen_ddr_config`: gcc wrapper script

### 6.3 Generated Artifacts in the Repo Root

- `ddr_timing_table.bin`
- `orbit_timing_params.c`
- `orbit_init_gen.h`
- `mr_config_gen.h`
- `orbit_config_override.json`

### 6.4 Non-Runtime or Historical Material

- `plan/`, `reports/`, `doc/`, `prompt/`
- offset/debug helpers such as `print_offsets.py`, `verify_offsets.py`, and the Python 2 compatibility scripts

These files are useful for investigation, but they are not part of the core generation path.

## 7. Architectural Characteristics

### 7.1 Strengths

- Domain logic is mostly table-driven rather than scattered through conditionals.
- Python and C orbit-config implementations are intentionally kept comparable.
- The GUI is dependency-light: Python standard library on the backend, plain HTML/JS on the frontend.
- The repository contains a large amount of compatibility and regression coverage.

### 7.2 Current Tradeoffs

- The codebase is script-oriented rather than package-oriented.
- The timing generator, orbit-config generator, GUI, and analyzer duplicate several pieces of schema knowledge.
- File-based integration is simple but causes a lot of root-level generated artifacts and implicit state.
- Reverse parsing is heuristic and offset-driven, not schema-driven.

## 8. External Dependencies

- Python 3 standard library for the main runtime
- `gcc` for the C reference orbit-config path
- A browser for the GUI
- `pytest` is useful for part of the test suite, though many tests are still script-style

