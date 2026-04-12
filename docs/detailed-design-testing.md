# Detailed Design: Testing and Validation

## 1. Scope

This document summarizes how the repository validates generation, binary compatibility, GUI behavior, and reverse parsing.

The test suite is broad, but it is not uniform. It mixes:

- shell scripts
- standalone Python scripts
- pytest-compatible test modules
- manual debug utilities

## 2. Test Layers

### 2.1 Reference Binary Generation

Representative files:

- `test_gen_lpddr4_bin.sh`
- `test_gen_lpddr5_bin.sh`

Purpose:

- regenerate committed reference binaries for LPDDR4 and LPDDR5
- produce single-channel and dual-channel reference artifacts

### 2.2 Python vs C Compatibility

Representative files:

- `test_lpddr4.sh`
- `test_lpddr5.sh`
- `test_binary_match.py`
- `compare_bin.py`
- `test_density_compat.py`

Purpose:

- verify that Python orbit-config generation matches the legacy C path
- compare full binaries for single-channel cases
- compare timing-table sections where layout differences are expected
- confirm density-code behavior across supported density values

### 2.3 GUI Integration

Representative files:

- `test_gui_params.py`
- `test_gui_checkbox_integration.py`
- `test_checkbox_flow.py`

Purpose:

- start the local server
- drive `/generate` and `/analyze`
- verify round-trip behavior between UI parameters and binaries
- validate checkbox and form-field wiring

### 2.4 Binary Parser Validation

Representative files:

- `test_binary_parse.py`
- `test_threshold.py`
- `test_timing_entry_validation.py`

Purpose:

- validate field extraction from generated/reference binaries
- check late-field offsets and threshold parsing
- confirm timing-entry parsing for LPDDR4 and LPDDR5 layouts

### 2.5 Parameter Variation and Regression Coverage

Representative files:

- `test_cli_bin_compare.py`
- `test_random_value_flow.py`
- `test_density_arrays.py`
- `test_dual_channel.py`

Purpose:

- exercise many parameter combinations
- check that changing parameters changes the binary
- confirm dual-channel handling
- validate density-array coverage

### 2.6 Layout and Offset Inspection Helpers

Representative files:

- `verify_offsets.py`
- `print_offsets.py`
- `print_field_offsets.py`
- `debug_offset.py`
- `test_size.py`
- `test_new_size.py`
- `test_fixed_size.py`

Purpose:

- inspect struct sizes and field offsets
- debug binary layout mismatches

## 3. What the Test Suite Proves Well

- Python and C orbit-config generation are intentionally compared.
- The GUI path is not isolated from validation; it has direct integration tests.
- Binary parsing regressions have dedicated coverage, especially around LPDDR5 fixes.
- Density handling and threshold-field behavior are covered by targeted tests.

## 4. Current Test Style

The repository uses two different test styles.

### 4.1 Script-Style Tests

Characteristics:

- print progress to stdout
- read and write files in the repository root
- use committed binaries as fixtures
- sometimes return booleans instead of using pure assertions

This style is common in:

- `test_gui_params.py`
- `test_cli_bin_compare.py`
- shell-based compatibility tests

### 4.2 Pytest-Friendly Tests

Characteristics:

- can be collected directly by `pytest`
- use `assert` statements for validation

Examples:

- `test_binary_parse.py`
- `test_threshold.py`

Even here, some tests still return `True`, which currently passes but raises `PytestReturnNotNoneWarning`.

## 5. Runtime Assumptions in Tests

Most tests assume:

- execution from the repository root
- write access to root-level generated files
- availability of reference binaries already in the repository
- availability of Python 3
- optional availability of `gcc` for C-path comparison

GUI tests also assume:

- port `5000` is available
- a server process can be started and queried locally

## 6. Validation Strategy by Artifact

| Artifact | How it is validated |
| --- | --- |
| `ddr_timing_table.bin` | direct byte comparison, size checks, parser checks |
| timing-entry layout | parser tests and offset validation scripts |
| `orbit_config` layout | Python/C binary comparisons and field-offset inspection |
| GUI form mapping | generate/analyze round-trip tests |
| density mapping | density compatibility and density-array tests |

## 7. Current Gaps

From the code structure, the main gaps are:

- no unified fixture layer for temporary output directories
- partial dependence on manual stdout review
- inconsistent pytest style
- substantial reliance on shared root-level mutable files

The repository still has useful coverage, but it behaves more like an integration-test toolbox than a cleanly isolated unit-test suite.

