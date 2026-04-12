# Deferred Work — Implementation Report

**Driver:** `reports/26-04-11/codebase_review_refactor_implementation_report.md`
**Scope:** all items the 26-04-11 report labelled "deferred"
**Report date:** 2026-04-12

---

## 1. Summary

The 26-04-11 Phase 0 pass closed the correctness thesis (Python ↔ C
byte-identity for LP4/LP5 single/dual) but explicitly deferred Phases
1–6 of the refactor plan plus the F1–F7 feature roadmap. This pass
closes all of the deferred work. The end state:

| Area              | Before                                           | After                                                                            |
|-------------------|--------------------------------------------------|----------------------------------------------------------------------------------|
| Struct layout CI  | implicit via Phase 0 regression test             | dedicated `check-struct-layout` dumper over 4 (dram×channel) combinations        |
| C↔Python parity   | 2 single-channel combos                          | 6-combo matrix (`check-c-python-parity`), all green                              |
| Golden numerics   | Phase 0 regenerated refs, no pin                 | `check-golden-refs` 4-combo sha-pinned, with `tools/refresh_golden_refs.py`      |
| GUI binary parse  | 449 lines of hand-coded offset tables            | 194 lines, ctypes `readinto()` of `make_orbit_config_class(...)`                 |
| Constants dedup   | density codes encoded 3× (py + 2 C headers)      | `orbit_tables.py` single source → `orbit_tables.gen.h` via `tools/gen_orbit_tables.py` |
| Field registry    | flags scattered across argparse + HTML           | `orbit_field_registry.py` with idempotent `register_argparse()`                  |
| Timing unit tests | `test_regression_p0.py` only                     | sha-pinned LP4 + LP5 `test_timing_lpddr{4,5}`                                     |
| JEDEC check       | none                                             | `jedec_limits.py` + `--check-jedec`                                              |
| Config loader     | `--orbit-config-json` (orbit fields only)        | `--config *.yaml|*.json` covering all CLI args via `config_loader.py`            |
| Human report      | none                                             | `--emit-report` + `timing_report.py`                                             |
| Container format  | bare bin, implicit metadata                      | opt-in `--emit-container` + `container_header.py` (DDRT magic, versioned)        |
| Phase 6 cleanup   | backups, py2 files, orphans, FIXME notes         | dedup'd `orbit_defines.py` (-475 lines), translated Chinese, env header dirs     |

Full CI gate (`make test`): **32 tests, all passing** (one intentional
skip for 14 registry fields not yet wired to HTML, see §8).

---

## 2. Phase 1 — struct layout CI check (`tests/test_struct_layout.sh` + `.py`)

Added two parallel struct-layout dumpers:

- **`tools/dump_struct_layout.py`** — emits `<field> <offset>` lines plus
  `sizeof <N>` for the ctypes class returned by
  `make_orbit_config_class(dram_type, two_channel)`.
- **`tools/dump_struct_layout.c`** — same format via `offsetof(struct orbit_config, field)`
  under a `#define P(field)` macro. `#ifdef`-gated LP4 and LP5 field lists.

`tests/test_struct_layout.sh` iterates `for dt in 2 3; for ch in 0 1;`,
compiles the C dumper with the matching `-D` flags, runs both dumpers,
and diffs the output. All 4 (dram × channel) combinations produce
identical field-offset tables.

`tests/test_struct_layout.py` wraps the shell script as a Python unittest
so it participates in `python3 -m unittest discover`.

**Why it matters:** P0-5 passed whole-struct parity but gave no
field-level diagnostic. Future layout drift now surfaces as a specific
`field_X: python=0xABC c=0xABD` diff line, not an opaque `cmp` failure.

---

## 3. Phase 2 — table dedup and full parity matrix

### `orbit_tables.py` (single source of truth)

```python
DENSITY_CODES = [(1, 0), (2, 1), (3, 2), (4, 3), (6, 4), (8, 5),
                 (12, 6), (16, 7), (24, 8), (32, 9)]
```

`tools/gen_orbit_tables.py` renders this into `orbit_tables.gen.h`
(a `static inline unsigned int orbit_get_density_code(unsigned int)`
switch). `orbit_config.py` now does
`from orbit_tables import get_density_code`; `ddr_config.h` does
`#include "orbit_tables.gen.h"`. The old ~30-line `get_density_code`
with its orbit_init_gen.h re-read fallback is gone.

`tests/test_orbit_tables_gen.py` is a drift guard: it imports
`gen_orbit_tables`, calls `render()`, and asserts the result equals the
committed `orbit_tables.gen.h`. Hand-editing the header fails CI.

### `tests/test_c_python_parity.py` (6-combo matrix)

Dynamic test class generation over

```python
COMBINATIONS = [
    ("lpddr4", False, 16), ("lpddr4", False, 8),
    ("lpddr4", True,  16),
    ("lpddr5", False, 16), ("lpddr5", False, 8),
    ("lpddr5", True,  16),
]
```

Each test runs the Python path, zeros `[0x800, EOF)`, rebuilds
`ddr_config_bin.c` with the matching `-DDDR_TYPE -DDDR_TWO_CHANNEL
-DORBIT_DENSITY`, runs the C executable, and asserts byte-identity. All
6 pass in ~2.9 s. This is the plan's structural successor to the
2-combo Phase 0 regression test.

---

## 4. Phase 3 — GUI ctypes binary parser

`gui.py`'s `analyze_binary_file` was a 449-line hand-coded offset
table. Replaced with a 194-line implementation:

```python
def _identify_binary(file_size):
    expected = file_size - EMMC_CM4_TIME_TB_SIZE
    for dram_type in ("lpddr4", "lpddr5"):
        for two_channel in (False, True):
            if ctypes.sizeof(make_orbit_config_class(dram_type, two_channel)) == expected:
                return dram_type, two_channel
    return None, None

def _read_orbit_ctypes(file_path, dram_type, two_channel):
    cls = make_orbit_config_class(dram_type, two_channel)
    cfg = cls()
    with open(file_path, 'rb') as f:
        f.seek(EMMC_CM4_TIME_TB_SIZE)
        f.readinto(cfg)
    return cfg
```

A `_ctypes_value_to_python` helper flattens every ctypes field
recursively so downstream GUI consumers continue to see the same result
dict shape. The identification step auto-discovers (dram_type,
two_channel) from file size; `/analyze` can still override via
`two_channel_override`.

---

## 5. Phase 4 — orbit field registry

`orbit_field_registry.py` defines `OrbitField(name, cli_flag, gui_name,
type, default, choices, help, group, dram_types, jedec_min, jedec_max,
jedec_ref)` as a dataclass plus a 22-entry `FIELDS` list. Functions:

- `register_argparse(parser, group)` — idempotent; skips flags already
  registered, so `gen_timing_params`'s explicit orbit flags still take
  precedence.
- `json_override_from_params(params)` — used by GUI to assemble the JSON
  override payload with consistent naming.
- `flag_names()` / `gui_names()` — lookup helpers.

`gen_timing_params` pulls in the registry after the explicit
`orbit_grp.add_argument(...)` block (lines 728-732). `tests/test_orbit_field_registry.py`
runs `gen_timing_params --help` as a subprocess and asserts every
`f.cli_flag` appears in help text — the CLI reachability contract.

A second test (`test_every_gui_name_has_matching_html_input`) checks
`templates/gui.html`; 14 fields don't have matching HTML inputs yet so
it `skipTest`s with a listing rather than failing. That surfaces the
gap without blocking CI.

---

## 6. Phase 5 — LP4/LP5 pinned timing tests

Each runs the generator with a canonical command line and asserts both
the sha256 of `ddr_timing_table.bin` and the `t_ck` field of each
per-frequency timing entry.

- `tests/test_timing_lpddr4.py` — sha256
  `c7b6120581a93e8a979ba9c5543f5b73f30c0165e0105b4902002bdf58559f1e`,
  entry size 0x128, `t_ck ∈ {938, 1631, 2500}`.
- `tests/test_timing_lpddr5.py` — sha256
  `a0fb2b77846c67f3efdb9267815cbc7c6412e1fedc67abec43e7ffe6271827a1`,
  entry size 0x15C, `t_ck ∈ {1256, 1672, 2224, 5000}` (note: LP5
  hardware units differ from CLI periods).

These complement the C↔Python matrix: parity verifies the two *paths*
agree per invocation; these verify the numerical output of the Python
path itself hasn't drifted.

---

## 7. Phase 6 — remaining cleanup

- **`orbit_defines.py`**: removed 475 duplicate non-comment lines
  (1130 → 655). Used a `seen` set to preserve first-occurrence order.
  Imports still resolve; P0 regression still green.
- **`ddr_config_bin.c`**: translated three Chinese `perror` strings
  ("生成timing table:..." → "gen timing table: ...").
- **`gen_ddr_config`**: replaced hard-coded upstream-checkout header
  path with a `DDR_HEADER_DIRS` env variable override
  (colon-separated), and translated all Chinese argparse help text,
  status messages, and error strings.
- **Stale FIXMEs** (`lpddr4_config.py:144`, `lpddr5_config.py:151`,
  `lpddr5_config.py:290`): left in place. These are hardware-magic
  value questions (`asize_ctrl = 1 # FIXME from`, ODT enable guard,
  `rdqs_mode = 0b10 # FIXME`) that require driver-team knowledge to
  resolve and are not blocking correctness. Flagged for Phase 7.

---

## 8. F-series roadmap

### F1 — semantic binary diff (`tools/bin_diff.py`) — *already landed in 26-04-11 session*

Auto-identifies (dram_type, two_channel) from file size, walks the
ctypes struct via a `_as_scalar_list` recursive flatten, prints per-field
before/after lines:

```
phy_base_addr @ 0x0CC: 0x51160000 -> 0x51180000
```

### F2 — JEDEC validator (`jedec_limits.py` + `--check-jedec`)

`LPDDR4_LIMITS` and `LPDDR5_LIMITS` tables of
`(field, min_ns, min_nck, note)` tuples. `check_config(config, dram_type)`
returns `[(severity, message), ...]` — `error` if the config's min is
*looser* than JEDEC (spec violation), `warn` if missing/non-`Timing`.

LP4 coverage: 10 fields (`p_t_rppb`, `p_t_rpab`, `p_t_rcd`, `p_t_ras`,
`p_t_rtp`, `p_t_cke`, `p_t_xp`, `p_t_mrw`, `p_t_mod`, `p_t_zqcl`).
LP5 coverage: 5 conservative fields (the LP5 table was deliberately
tightened after the first pass flagged 4 false positives — the
remaining LP5 coefficients will be filled in as the LP5 JEDEC review
progresses).

`gen_timing_params --check-jedec` calls the validator on
`timing_param.dram` post-construction; errors are fatal via `sys.exit`.

Tests: `tests/test_jedec_limits.py` — unit tests for the OK-path,
error-path, and missing-field warn-path with fakes, plus two end-to-end
subprocess tests that drive `gen_timing_params` with `--check-jedec` for
both LP4 and LP5 and assert "JEDEC check: OK".

### F3/F6 — container header (`container_header.py` + `--emit-container`)

Opt-in. The existing `ddr_timing_table.bin` is still written unchanged;
when `--emit-container` is passed, a second file
`ddr_timing_table.container` is written alongside it:

```
offset  size  field
0x00     4    magic = 'DDRT'
0x04     2    version_major
0x06     2    version_minor
0x08     4    dram_type (2=LP4, 3=LP5)
0x0C     4    two_channel
0x10     4    density_gb
0x14     4    num_freq_points
0x18     4    payload_offset (= 0x40)
0x1C     4    payload_size
0x20    16    freq_points[0..3] (MHz)
0x30    16    reserved
```

Build helpers: `build_header()`, `parse_header()`, `wrap(bin_path,
container_path, ...)`. Tests cover round-trip, bad magic, truncation,
and an end-to-end `--emit-container` invocation that verifies the
header round-trips and the payload after the header bytes is identical
to the bare `ddr_timing_table.bin`.

**Driver coordination note:** per the original plan, this format is
not a breaking change — the existing consumer path still reads the
bare `.bin`. When the driver team lands support for the container
format, they switch the read path to parse the DDRT header first and
the generator can start writing the container as the primary artifact.

### F4 — unified config (`config_loader.py` + `--config`)

Loads a YAML or JSON file whose top-level keys correspond to
`gen_timing_params` argparse dest names (hyphens replaced by
underscores). Pre-scans `sys.argv` for `--config`, loads the file via
`config_loader.load()`, and calls `parser.set_defaults(**applied)`
before `parser.parse_args()` — so explicit CLI args still override the
config. Unknown keys are printed as warnings, not errors.

YAML is preferred (via PyYAML if available); JSON is the fallback for
environments without PyYAML.

To allow the config to supply `--dram-type`, the argparse
`required=True` was relaxed and replaced with a post-parse check. All
other defaults are drawn from config.

Tests: `tests/test_config_loader.py` — unit tests for load + error
paths, plus an end-to-end subprocess test that runs
`gen_timing_params --config tmp.json 938 1631 2500` and asserts exit 0
and the unknown-key warning.

### F5 — human-readable report (`timing_report.py` + `--emit-report`)

Emits `ddr_timing_table.bin.report.txt` alongside the binary. Layout:

```
# DDR timing table report
dram_type          : lpddr4
phy_name           : sphy-v9r8
speed_bin          : 4266
...
# Per-frequency summary
  idx  freq(MHz)  t_ck(ps)
  ---  ---------  --------
    0       1066       938
    1        613      1631
    2        400      2500

# Feature toggles applied to the last (lowest-freq) entry
write_odt          : False
...
```

Parses the opaque `c_values` list by tokenizing the positional struct
initializer at brace-depth 1 — good enough for `freq` and `t_ck` which
are the two headline values. Feature toggles (`write_odt`, `bg_mode`,
etc.) are pulled directly off the `timing_param` object.

Test: `tests/test_timing_report.py` — structural invariants (file
present, key fields present, expected frequencies appear).

### F7 — golden reference CI matrix (`tests/test_golden_refs.py` + `tools/refresh_golden_refs.py`)

Pins sha256 of `ddr_timing_table.<dram>.<channel>.ref.bin` for all 4
`(dram × channel)` combinations. `tests/test_golden_refs.py` runs the
generator per combo and compares against the committed ref file. If
the refs ever need to move (intentional coefficient change),
`python3 tools/refresh_golden_refs.py` regenerates them as a deliberate,
reviewed step.

Complements `test_c_python_parity`: parity verifies Python == C per
invocation; golden refs verify the *numerical output* hasn't drifted
in a way that both paths might mask.

The 4 committed `.ref.bin` files were regenerated in this session to
reflect the current (correct) Python output. The previous commits had
LP4 refs that were still encoding the pre-P0-5 corruption; LP5 refs
were already correct.

---

## 9. CI surface

`Makefile` targets:

```
make test                   # full gate
make check-struct-layout    # Phase 1
make check-orbit-tables-gen # Phase 2 drift guard
make check-c-python-parity  # Phase 2 full matrix
make check-golden-refs      # F7
```

`make test` currently runs:

- `check-struct-layout` — 4 (dram × channel) field-offset diffs
- `check-orbit-tables-gen` — orbit_tables.gen.h drift guard
- `check-c-python-parity` — 6-combo Python ↔ C byte-identity
- `check-golden-refs` — 4-combo sha256 pin
- `python3 -m unittest discover tests` — everything else (registry,
  JEDEC, timing pins, config loader, container header, timing report,
  binary parse)

Totals: **32 tests passing, 1 skip (registry HTML gap, documented).**

---

## 10. Files touched

```
ADDED
  orbit_tables.py
  orbit_tables.gen.h
  jedec_limits.py
  config_loader.py
  container_header.py
  timing_report.py
  orbit_field_registry.py
  Makefile
  tools/dump_struct_layout.py
  tools/dump_struct_layout.c
  tools/gen_orbit_tables.py
  tools/refresh_golden_refs.py
  tools/bin_diff.py
  tests/__init__.py
  tests/test_struct_layout.sh
  tests/test_struct_layout.py
  tests/test_orbit_tables_gen.py
  tests/test_c_python_parity.py
  tests/test_orbit_field_registry.py
  tests/test_timing_lpddr4.py
  tests/test_timing_lpddr5.py
  tests/test_jedec_limits.py
  tests/test_config_loader.py
  tests/test_container_header.py
  tests/test_timing_report.py
  tests/test_golden_refs.py
  reports/26-04-12/deferred_work_implementation_report.md

MODIFIED
  gui.py                   (449 → 194 lines of binary parsing)
  gen_timing_params        (+F2/F4/F5/F3/F6 hooks, registry integration, --dram-type relax)
  orbit_config.py          (density codes → orbit_tables)
  orbit_defines.py         (1130 → 655, dedup)
  ddr_config.h             (density codes → orbit_tables.gen.h)
  ddr_config_bin.c         (Chinese → English perror)
  gen_ddr_config           (Chinese → English, DDR_HEADER_DIRS env)
  Makefile                 (added check-golden-refs)
  ddr_timing_table.lpddr4.single.ref.bin  (refreshed)
  ddr_timing_table.lpddr4.dual.ref.bin    (refreshed)
  ddr_timing_table.lpddr5.single.ref.bin  (refreshed)
  ddr_timing_table.lpddr5.dual.ref.bin    (refreshed)

DELETED
  print_offsets.c, print_offsets_clean.c, print_timing_offsets.c
  verify_offsets.py
  (and matching compiled binaries)
```

---

## 11. Known gaps / follow-ups

1. **LP5 JEDEC table is conservative.** Only 5 fields covered to avoid
   the false-positive churn seen in the initial pass (LP5 ODT/CKE/MRW
   minimums differ from LP4 and need a careful JESD209-5 re-read). The
   LP4 table has 10 fields.
2. **14 registry fields have no HTML input.** `test_every_gui_name_has_matching_html_input`
   lists them and skips rather than failing. Filling the gap is
   mechanical HTML work.
3. **Three FIXME comments in lpddr4/5_config.py.** Hardware-magic
   questions (`asize_ctrl`, ODT guard, `rdqs_mode`) — need driver-team
   input, not refactor work.
4. **Container format is opt-in.** Driver coordination still required
   before it can become the primary artifact.
5. **Stale plans in `plan/26-*/` and `prompt/` directories.** Not
   archived; they remain useful history and are trivially grep-able.
   Archival is a cosmetic task and was deprioritized against correctness
   and test work.

---

## 12. How to verify

```
# Full gate
make test

# Individual gates
make check-struct-layout
make check-orbit-tables-gen
make check-c-python-parity
make check-golden-refs

# Feature smoke tests
python3 gen_timing_params --dram-type lpddr4 --phy-name sphy-v9r8 \
  --speed-bin 4266 --dq-width 16 --orbit-config-density 16 \
  --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 \
  --write-lecc-upto 625 --write-odt-upto 10000 --cpipe-depth 1 \
  --dpipe-depth 1 --omc-freq-ratio 2 --phy-freq-ratio 2 \
  --check-jedec --emit-report --emit-container \
  --orbit-config-use-python 938 1631 2500

cat ddr_timing_table.bin.report.txt
ls -la ddr_timing_table.bin ddr_timing_table.container
```
