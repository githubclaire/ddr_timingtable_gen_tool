# Detailed Design: Orbit Config

## 1. Scope

This document covers the code that builds the `orbit_config` struct written at offset `0x800` in `ddr_timing_table.bin`.

Primary files:

- `orbit_config.py`
- `ddr_config_init.py`
- `ddr_config.h`
- `ddr_config_bin.c`
- `gen_ddr_config`
- `arise2_omc.h`
- `arise2_config.h`

## 2. Design Goal

The repository maintains two compatible implementations of orbit-config generation:

- a Python implementation used by the modern CLI and GUI
- a C implementation used as a legacy reference and compatibility target

The Python code mirrors the C layout closely enough that the binary output can be compared directly.

## 3. Schema Source of Truth

The hardware-oriented structure definition lives in `arise2_omc.h` as `struct orbit_config`.

The Python side mirrors it by dynamically generating `ctypes.Structure` classes in `orbit_config.py`.

Key properties of the Python schema:

- `_pack_ = 8`
- LPDDR5 adds header fields such as `lp5_mr2`, `lp5_mr3`, and `zq_bg_mode`
- dual-channel mode enlarges OMC and PHY base-address arrays and training/prbs arrays

## 4. Python Struct Factory

`make_orbit_config_class(dram_type='lpddr4', two_channel=False)` builds the correct class at runtime.

Inputs:

- `dram_type`
- `two_channel`

Derived layout decisions:

- LPDDR5 includes the extra LP5-only header block
- `NUM_OF_OMC` is `2` for single-channel and `4` for dual-channel
- `NUM_OF_PHY` follows the same rule

`create_orbit_config()` then instantiates and zero-initializes the matching class.

## 5. Layout Variants

| Variant | Struct size |
| --- | ---: |
| LPDDR4 single | 3048 |
| LPDDR5 single | 3056 |
| LPDDR4 dual | 5816 |
| LPDDR5 dual | 5824 |

Representative field offsets from the start of the orbit-config region:

| Field | LPDDR4 single | LPDDR4 dual | LPDDR5 single | LPDDR5 dual |
| --- | ---: | ---: | ---: | ---: |
| `density_code` | `0x78` | `0x78` | `0x80` | `0x80` |
| `base_addr` | `0xC0` | `0xC0` | `0xC8` | `0xC8` |
| `dynamic_self_refresh_threshold` | `0xDC` | `0xEC` | `0xE4` | `0xF4` |
| `dynamic_power_down_threshold` | `0xE0` | `0xF0` | `0xE8` | `0xF8` |
| `mrr_byte_lane` | `0x100` | `0x110` | `0x108` | `0x118` |

## 6. Initialization Algorithm

`ddr_config_init(cfg, dram_type='lpddr5', two_channel=False, density=16, byte_mode=0, mixed=0, **kwargs)` is the Python equivalent of the C initializer.

### 6.1 Fixed Initialization

The function sets:

- boot timings such as `rclk_t_ck`, `boot_t_ck`, and `boot_t_ck_low`
- base DRAM timing (`dram_t_ck`)
- region start/end addresses
- OMC and PHY APB base addresses
- controller frequency ratios
- queue depth and basic widths
- default wakeup timings and unsupported feature defaults

### 6.2 Modifiable Fields

The function allows overrides through `kwargs` for:

- rank topology
- memory features such as `rfm_en`, `dsm_en`, `ca_odt`
- training enables
- periodic training
- power-management thresholds
- refresh and ZQ timing intervals

### 6.3 Density and Geometry

Density handling is split across two functions:

- `get_density_code(density)` resolves the encoded density value
- `orbit_update_chips(cfg, byte_mode, mixed, dram_type)` derives row/bank geometry per rank

`orbit_update_chips()` changes row geometry based on:

- DRAM family
- density
- byte mode
- mixed-density rank doubling for rank 1

## 7. Binary Writer

`generate_orbit_config_binary(...)` performs the actual file mutation.

Sequence:

1. Create the correct `ctypes` class with `create_orbit_config()`
2. Populate it through `ddr_config_init()`
3. Open `ddr_timing_table.bin` in `r+b` mode
4. Seek to `offset=0x800`
5. Write the raw struct bytes
6. Patch specific absolute file offsets for base-address fields

The patch step exists because compatibility is judged against pre-existing binaries, and the address-array layout differs between single-channel and dual-channel variants.

## 8. Density Mapping Flow

The density-code mapping is coordinated with the timing-generator stage.

Flow:

1. `gen_timing_params.write()` creates `orbit_init_gen.h`
2. The header contains `DENSITY_*` macros and `DEFAULT_DENSITY`
3. Python tries to read this file dynamically in `get_density_code()`
4. The C path includes the same header via `_ORBIT_GET_DENSITY_`

This design keeps Python and C density-code selection aligned.

## 9. Python vs C Generation Paths

### 9.1 Python Path

Used when `--orbit-config-use-python` is enabled.

`generate_orbit_config_bin(args)` in `gen_timing_params`:

- translates CLI arguments into orbit-config field names
- loads optional JSON overrides
- determines the selected density and density code
- calls `generate_orbit_config_binary(...)`

### 9.2 C Reference Path

Used when `--orbit-config-use-python` is not enabled.

`gen_ddr_config`:

- checks `gcc`
- compiles `ddr_config_bin.c`
- passes macros:
  - `DDR_TYPE`
  - `DDR_TWO_CHANNEL`
  - `ORBIT_DENSITY`
- executes the compiled binary

`ddr_config_bin.c`:

- allocates `struct orbit_config`
- calls the C `ddr_config_init(config)`
- seeks to `EMMC_CM4_TIME_TB_SIZE`
- writes the struct into `ddr_timing_table.bin`

## 10. Helper Headers Produced by the Timing Stage

| File | Why orbit-config generation needs it |
| --- | --- |
| `orbit_init_gen.h` | Density-code macros and `DEFAULT_DENSITY` |
| `mr_config_gen.h` | Mode register macros and table-size macros used by the C code |

This means orbit-config generation is downstream from timing generation even when the timing table itself is unchanged.

## 11. Observed Design Pattern

The orbit-config subsystem is intentionally compatibility-first.

You can see this in:

- dynamic `ctypes` layout construction
- field-by-field default parity with the C implementation
- explicit file-offset patching after raw struct writes
- multiple tests that compare Python and C binaries directly

