# Detailed Design: Timing Generation

## 1. Scope

This document covers the subsystem that turns CLI input into packed timing-table entries and the helper files that support later orbit-config generation.

Primary files:

- `gen_timing_params`
- `timing.py`
- `dram_config.py`
- `lpddr4_config.py`
- `lpddr5_config.py`
- `phy_config.py`
- `sphy_v9r8_config.py`
- `orbit_defines.py`

## 2. Core Design Idea

The timing generator is a table-driven calculator. It combines:

- user-selected global options
- DRAM-family timing tables
- PHY-specific timing adjustments
- per-period feature enable thresholds

It then serializes the result twice:

- as C source in `orbit_timing_params.c`
- as packed binary bytes in `ddr_timing_table.bin`

## 3. Main Abstractions

| Type or class | Purpose |
| --- | --- |
| `Timing` | Represents a timing constraint as `min_ns`, `min_nck`, and `add_tck`, then converts it into integer cycles with `calc_ceil()` and `calc_floor()`. |
| `Boundary` | Frequency/period boundaries for a memory operating point. |
| `WCK` | LPDDR5 WCK-related per-state metadata. |
| `Memcfg` | A complete operating-point record: RL/WL/nWR/ODT/WCK behavior for one timing range. |
| `dram_config` | Base class that stores `memcfgs` and provides the lookup function. |
| `lpddr4_config` | LPDDR4 timing rules, density tables, and per-period calculations. |
| `lpddr5_config` | LPDDR5 timing rules, WCK mode logic, density tables, and per-period calculations. |
| `phy_config` | Base PHY hook interface. |
| `sphy_v9r8_config` | SPHY-V9R8-specific timing adjustments. |
| `GenTimingParam` | Top-level coordinator used by the CLI. |

## 4. Input Normalization

`parse_args()` defines the public CLI surface.

It performs several normalization steps:

- converts `--densities` from strings to integers
- derives `macro_ddr_type` from `--dram-type`
- maps `--enable` options into boolean attributes
- clamps LPDDR4 `write-odt-upto` to the supported maximum

The CLI surface is split into:

- common timing-generator options
- LPDDR4-specific options
- LPDDR5-specific options
- orbit-config options that will later be passed into the second subsystem

## 5. Generator Initialization

`GenTimingParam.__init__()` is responsible for:

1. storing the parsed args
2. zero-initializing shared timing fields through `initialize()`
3. constructing the PHY model
4. constructing the DRAM model
5. deciding helper flags such as `has_converter` and `byte_mode`
6. calling `dram.initialize()` to load DRAM-specific timing tables and density dictionaries

At this point the object is ready to evaluate one or more requested periods.

## 6. Per-Period Calculation Flow

`GenTimingParam.calculate()` loops over `self.args.periods`.

For each period it does the following:

1. Derives mode flags from threshold options.
   - examples: write ODT, DBI, link ECC, NT-ODT, bank-group mode, WCK 1:4 mode

2. Derives clock ratios.
   - LPDDR4 operates on `tCK`
   - LPDDR5 accepts user periods as `tWCK`, then derives `data_freq_ratio` and later converts to `tCK`

3. Calls `phy.update_conf(t_ck)` to let the PHY react to the operating point.

4. Calculates density-dependent arrays.
   - `t_rfcab`
   - `t_rfcpb`
   - `t_rfmab`
   - `t_rfmpb`
   - `t_refdpr`
   - `tx_pbr2pbr`
   - `t_xsr`
   - `t_xsdll`
   - `t_xs_fast`

5. Calls `dram.update(t_ck)`.
   - selects the correct `Memcfg`
   - chooses RL/WL/NWR sets
   - updates DRAM-family-specific intermediate values

6. Converts `Timing` objects into integer cycle counts.
   - refresh timings
   - activate/precharge timings
   - mode register timings
   - derating timings
   - WCK and RDQS control timings for LPDDR5

7. Calls both calculation hooks:
   - `dram.calculate(t_ck)`
   - `phy.calculate_mc_timing_param(t_ck)`
   - `phy.calculate_phy_timing_param(t_ck)`

8. Packs the result into:
   - 21 `timing_param` words
   - 2 `timing_param_derate` words
   - 8 `dfi_timing_param` words
   - trailing byte-sized flags and per-entry metadata

The packed values are first emitted as a C-style string representation and stored in `self.c_values`.

## 7. DRAM-Family Specialization

### 7.1 LPDDR4

`lpddr4_config.py` models:

- one `memcfgs` table spanning the supported period ranges
- density sets `{2, 3, 4, 6, 8, 12, 16}`
- byte-mode effects
- `rpste` and `wpste`
- WDQS control mode
- variable `tRRD`

Key behavior:

- `search_memcfgs()` selects the operating point
- `update()` chooses RL/WL/NWR sets and refreshes dynamic timing helpers
- `calculate()` computes LPDDR4-specific relationships like `t_rtw`, `t_wtrcr`, and `tdram_clk_enable`

### 7.2 LPDDR5

`lpddr5_config.py` is more complex because it must model:

- multiple `memcfgs_map` tables
- WCK:CK ratios `2:1` and `4:1`
- link ECC variants
- bank-group mode
- WCK pre/post toggle timings
- NT-ODT and WCK always-on interactions

Density sets are `{1, 2, 3, 4, 6, 8, 12, 16, 24, 32}`.

Key behavior:

- the selected `memcfgs` table depends on link ECC and data-frequency ratio
- user periods are treated as `tWCK` inputs
- `update()` derives WCK and RDQS mode-dependent state
- `calculate()` computes LPDDR5-specific WCK enable/off/toggle timings and ODT interactions

## 8. PHY Specialization

`sphy_v9r8_config.py` contains SPHY-V9R8 lookup tables and helper logic.

Responsibilities:

- translate period and ratio into DFS level
- derive read adjustment and read duration adjustment
- derive RDQS pre/post type values
- compute PHY-visible timing parameters such as `trddata_en`, `tphy_wrlat`, and `tlp_resp`

The generator delegates PHY-specific behavior here instead of mixing PHY logic into the DRAM-family files.

## 9. Packing and Emission

### 9.1 C Output

`GenTimingParam.write()` emits:

- `orbit_timing_params.c`
- `orbit_init_gen.h`
- `mr_config_gen.h`

`orbit_init_gen.h` contains:

- density-to-density-code mapping macros
- `DEFAULT_DENSITY`
- a small C helper for density-code lookup when `_ORBIT_GET_DENSITY_` is defined

`mr_config_gen.h` contains mode-register-related macros and the table-size constants needed by the C orbit-config path.

### 9.2 Binary Output

`gen_timingtable_bin(my_values)` converts the C-style text representation back into packed bytes.

This is driven by:

- `type_arr`: logical field order
- `type_mapping`: Python `struct` type codes
- the generated `c_values`

The binary is written to `ddr_timing_table.bin`.

The orbit-config region is not written here; it is appended later at offset `0x800`.

## 10. Output Characteristics

| DRAM type | Density count | Timing entry size |
| --- | ---: | ---: |
| LPDDR4 | 7 | `0x128` / `296` |
| LPDDR5 | 10 | `0x15C` / `348` |

The difference comes from the larger density-dependent arrays in LPDDR5.

## 11. Extension Points

To add support for another DRAM family or PHY, the current design expects:

1. a new DRAM config class with `initialize()`, `update()`, and `calculate()`
2. a new PHY config class implementing the PHY hook interface
3. new CLI argument definitions where needed
4. updated packing/parsing logic if the emitted struct shape changes

