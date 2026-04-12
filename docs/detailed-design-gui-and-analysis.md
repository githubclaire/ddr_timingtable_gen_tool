# Detailed Design: GUI and Binary Analysis

## 1. Scope

This document covers the local web interface and the reverse parser used to inspect generated binaries.

Primary files:

- `gui.py`
- `templates/gui.html`

## 2. Backend Design

The backend deliberately uses only the Python standard library:

- `http.server`
- `socketserver`
- `subprocess`
- `json`
- `struct`

There is no framework dependency such as Flask.

`ReuseAddrTCPServer` enables local development restarts on port `5000`.

## 3. HTTP Endpoints

| Endpoint | Method | Role |
| --- | --- | --- |
| `/` | `GET` | Serves the single-page HTML UI from `templates/gui.html`. |
| `/generate` | `POST` | Converts form JSON into CLI args, invokes `gen_timing_params`, and reports success/failure. |
| `/analyze` | `POST` | Reads a binary, infers its format, parses timing/orbit fields, and returns JSON. |

## 4. Frontend Design

`templates/gui.html` is a single-file UI that combines:

- layout and styling
- form controls for both timing and orbit-config settings
- client-side validation
- unit conversion between ps and MHz
- JSON save/load helpers
- binary analysis modal

The UI is organized by collapsible sections:

- basic parameters
- pipe configuration
- timing features
- LPDDR4 options
- LPDDR5 options
- orbit-config options
- training and power-management options

## 5. Generate Flow

### 5.1 Frontend

The frontend `generate()` function:

1. validates the form
2. validates timing ranges
3. collects form fields and checkbox states
4. flattens dynamic period inputs into a space-separated `periods` string
5. converts MHz values back to ps when needed
6. POSTs the JSON payload to `/generate`

### 5.2 Backend

`DDRHandler.do_POST()` handles `/generate` by:

1. reading the JSON request body
2. building a `gen_timing_params` command line
3. mapping frontend fields into CLI arguments
4. writing `orbit_config_override.json`
5. adding `--orbit-config-json` and `--orbit-config-use-python`
6. invoking the CLI with `subprocess.run(...)`
7. returning a JSON result with a human-readable message

### 5.3 Backend Design Choice

The GUI does not directly call the low-level generator classes.

Instead it reuses the CLI as the integration boundary. That keeps the browser flow close to the command-line flow, but it also means the GUI inherits every CLI behavior and mismatch.

## 6. Analyze Flow

### 6.1 Binary Type Inference

`analyze_binary_file()` first reads the whole file and infers:

- LPDDR4 vs LPDDR5
- single-channel vs dual-channel

It mainly uses:

- file size thresholds
- selected base-address slots as a secondary signal

### 6.2 Timing Entry Parsing

`parse_timing_entries(data, dram_type)`:

- chooses entry size by DRAM type
- reads the selected density from the orbit-config region
- selects the density-indexed values from the density arrays
- scans entries and filters out invalid ones
- returns:
  - parsed per-entry timing fields
  - density-dependent values for the selected density
  - the detected density

### 6.3 Orbit-Config Parsing

`analyze_binary_file()` also reads orbit-config fields using hardcoded offsets.

It builds grouped JSON sections:

- `basic`
- `pipe`
- `timing`
- `timing_entries`
- `orbit`

Not every original generation parameter can be recovered from the binary, so the response includes a `non_parseable_fields` list.

## 7. Data Returned to the UI

The frontend uses the analysis JSON in two ways:

1. to populate the analysis modal for inspection
2. to refill the form for an edit-and-regenerate workflow

The returned payload is not a raw dump of binary fields. It is already grouped into UI-centric sections.

## 8. UI-Specific Helpers

The frontend contains custom logic for:

- dynamic add/remove period inputs
- DRAM-family-specific field visibility
- unit label updates
- binary file analysis trigger
- JSON import/export
- conditional display for options like periodic training, temp sensing, and rank interleaving

## 9. Design Characteristics

### 9.1 Strengths

- very small dependency footprint
- easy local usage
- the UI stays close to the actual CLI behavior
- reverse analysis is built into the same tool, which is useful for firmware bring-up and debugging

### 9.2 Current Constraints

- generation is mediated through shelling out to the CLI, not through a shared service layer
- binary parsing duplicates layout knowledge already present in the `ctypes` schema
- some fields are reconstructed heuristically rather than read from a typed schema
- analyzer output intentionally mixes parsed values and defaults because the binary does not preserve every original form input

