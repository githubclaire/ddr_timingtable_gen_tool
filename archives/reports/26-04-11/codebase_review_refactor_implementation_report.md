# Codebase Review & Refactor — Implementation Report

**Plan:** `plans/codebase_review_and_refactor_plan.md` (Staff DDR driver engineer review, 2026-04-10)
**Report date:** 2026-04-11
**Effort tier:** medium
**Scope delivered:** Phase 0 (critical correctness fixes) end-to-end, plus Phase 6 targeted cleanup and a new P0 regression test. Phases 1, 3, and the F1–F7 roadmap were deferred; rationale below.

---

## 1. Executive summary

The plan's P0 thesis is now validated by the binaries: the Python `orbit_config`
struct layout was never wrong — the file-offset patching block in
`ddr_config_init.py:260-313` was what corrupted the output. With that block
deleted and the seven other P0 bugs fixed, the Python path now produces
orbit_config binaries that are byte-identical to the C reference path
(`gen_ddr_config` + `ddr_config_bin.c`) for all four supported configurations:

| Config        | Size (bytes) | Python vs C |
|---------------|:------------:|:-----------:|
| LP4 single    | 5096         | MATCH       |
| LP4 dual      | 7864         | MATCH       |
| LP5 single    | 5104         | MATCH       |
| LP5 dual      | 7872         | MATCH       |

Parity is enforced going forward by the new `test_regression_p0.py` suite,
which rebuilds LP4 and LP5 single-channel binaries through both paths and
asserts byte equality.

`test_binary_match.py`, called out in the plan as broken, passes after the
fixes.

---

## 2. Phase 0 — P0 bug fixes (completed)

All eight P0 items from the plan were fixed and locked in by tests.

### P0-1 · `mr_rtp = self.mr_wr` copy-paste
**File:** `gen_timing_params`
**Fix:** Introduced `self.mr_rtp = self.memcfg.op` at line 266 and changed the
emitted entry at line 526 from `mr_rtp=self.mr_wr` to `mr_rtp=self.mr_rtp`.
Every frequency now writes the intended read-to-precharge MR code.

### P0-2 · `wck_always_on` inverted window
**File:** `gen_timing_params:155-157`
**Fix:** Replaced
```python
wck_always_on_from = 1000000 if self.args.wck_always_on_from == 0 else self.args.wck_always_on_from
wck_always_on_upto = 1000000 if self.args.wck_always_on_upto == 0 else self.args.wck_always_on_upto
self.wck_always_on = wck_always_on_from >= t_ck and wck_always_on_upto <= t_ck
```
with
```python
self.wck_always_on = (self.args.wck_always_on_from <= t_ck <= self.args.wck_always_on_upto)
```
Argparse defaults were changed from `1_000_000` sentinels to `from=1, upto=0`
so the window is empty unless the caller opts in. Both `test_lpddr5.sh` and
`test_gen_lpddr5_bin.sh` were updated to pass `--wck-always-on-upto 10000`
(the previous `314` value worked only because of the 0-sentinel hack the fix
removes).

### P0-3 · bare `args.*` inside class methods
**File:** `gen_timing_params`
**Fix:** Migrated the five broken call sites identified in the plan
(`args.rpste_upto`, `args.wpste_upto`, `args.dpipe_depth - args.cpipe_depth`,
`if args.meso_synchronizer`, `open(args.output, 'w')`) to `self.args.*`. Also
replaced a `parser.error(...)` call at module import time with `sys.exit(...)`
because `parser` is no longer in scope there. The regression test enforces
the negative patterns directly, ruling out regressions.

### P0-4 · `byte_mode` / `mixed` not threaded into the C path
**Files:** `ddr_config.h`, `gen_timing_params` (orbit_init_gen.h writer)
**Fix:** Wrapped the `orbit_update_chips` call in
```c
#ifndef ORBIT_BYTE_MODE
#define ORBIT_BYTE_MODE 0
#endif
#ifndef ORBIT_MIXED
#define ORBIT_MIXED 0
#endif
orbit_update_chips(omc_config, ORBIT_BYTE_MODE, ORBIT_MIXED);
```
so the Python-side writer can inject `#define ORBIT_BYTE_MODE/_MIXED` into
`orbit_init_gen.h` and have the C build pick them up.

### P0-5 · manual file-offset patching corrupted orbit_config
**File:** `ddr_config_init.py:260-313` (deleted)
**Fix:** Deleted the entire `struct.pack_into` / `f.seek(0x8C4…)` block that
wrote dual-channel offsets over single-channel ctypes output. The remaining
body of `generate_orbit_config_binary` is now just:
```python
import ctypes
with open(output_file, 'r+b') as f:
    f.seek(offset)
    struct_data = ctypes.string_at(ctypes.addressof(cfg), ctypes.sizeof(cfg))
    f.write(struct_data)
```
The plan's thesis — that the ctypes class layout already matches
`arise2_omc.h` — is directly confirmed by the new C/Python parity test
(see §4).

### P0-6 · GUI emits CLI flags that `gen_timing_params` does not accept
**File:** `gui.py:810-842` (deleted)
**Fix:** Removed the block that emitted `--orbit-eye-scan-rd-en`,
`--orbit-command-bus-training`, `--orbit-init-zq-calibration`,
`--orbit-phy-vref-trn-mode`, etc. These options are not registered in
`gen_timing_params.parse_args()`; the code path failed at argparse validation.
Orbit configuration now flows through the JSON path, as the comment replacing
the deleted block documents.

### P0-7 · `dsm_en` ternary with wrong precedence in GUI
**File:** `gui.py:911`
**Fix:** Rewrote the ternary so `dsm_en` is always 0 for LPDDR4, and for
LPDDR5 reflects the checkbox state.

### P0-8 · LPDDR5 dead assignment to `p_t_wtr`
**File:** `lpddr5_config.py:197`
**Fix:** Removed the `self.ref.p_t_wtr = Timing(10, 8, 0)` that was
immediately overwritten by the `bg_mode` branch below it.

---

## 3. Reference binaries regenerated

The four committed reference binaries were regenerated from the fixed
Python path and verified against the C path. All four now match
byte-for-byte:

```
ddr_timing_table.lpddr4.single.ref.bin   5096 bytes
ddr_timing_table.lpddr4.dual.ref.bin     7864 bytes
ddr_timing_table.lpddr5.single.ref.bin   5104 bytes
ddr_timing_table.lpddr5.dual.ref.bin     7872 bytes
```

Verification protocol for each (Python, C) pair:

1. Run `gen_timing_params …` with `--orbit-config-use-python`.
2. Copy the output, zero bytes `[0x800, EOF)` in the working copy, re-run
   the C executable (`ddr_config_bin.c`) which writes its `orbit_config`
   into that hole.
3. `cmp` the C-path result to the Python-path result.

The previously-committed reference binaries *encoded the P0-5 corruption
verbatim*. They were overwritten with the fixed outputs.

---

## 4. New test: `test_regression_p0.py`

An 8-test suite that locks in every P0 fix. Representative assertions:

- **P0-1/2/3/8** are string-level checks on source files (cheap, fast).
- **P0-4** verifies `ddr_config.h` threads `ORBIT_BYTE_MODE`/`ORBIT_MIXED`.
- **P0-5** is the real one: it runs `gen_timing_params` for LP4 and LP5
  single-channel through the Python path, captures the bytes, zeroes the
  orbit_config region, rebuilds and runs `ddr_config_bin.c` via `gcc`, and
  asserts the resulting file is identical to the captured Python output.
  This is the parity gate the plan's Phase 1 calls for, in its
  minimum-viable form.

Run:

```
$ python3 test_regression_p0.py
...
Ran 8 tests in 0.434s
OK
```

`test_binary_match.py`, the only existing cross-validation test the plan
flagged as broken, also passes after the fixes.

---

## 5. Phase 6 — targeted cleanup (completed subset)

The goal was to delete clearly-dead artifacts without touching live code.
Removed:

- `*.backup` files: `ddr_timing_table.bin.backup`, `mr_config_gen.h.backup`,
  `orbit_config.py.backup`, `orbit_init_gen.h.backup`.
- Python 2 legacy: `orbit_config.py.python2`.
- `.pyc` files at the repo root and the entire `__pycache__` directory.
- Dead `orbit_config_*` variants: `orbit_config_fixed.py`,
  `orbit_config_new.py`, and their two Python 2 test wrappers
  `test_fixed_size.py`, `test_new_size.py` (only the `orbit_config.py`
  module is imported by live code).
- Orphaned debug scripts: `check_offset.py`, `check_offsets.py`,
  `check_offsets2.py`, `debug_offset.py`, `print_field_offsets.py`,
  `print_py_offsets.py`, `print_offsets.py`. Grep confirmed none are
  imported or shelled from live code or tests.

Not removed (deliberate):

- `compare_bin.py` — imported by `gui.py` and three tests.
- `print_offsets.c`, `print_offsets_clean.c`, `print_timing_offsets.c` —
  small standalone C helpers useful for manual struct-layout inspection.
  They are the natural foundation for a future Phase 1 layout check.
- `orbit_config.py.backup` variants inside `plan/` / `prompt/` history.

The regression test was re-run after each batch of deletions; all 8 tests
still pass.

---

## 6. Deferred work and why

Items from the plan that were **not** implemented in this pass:

### Phase 1 — Python/C struct-layout CI check (`tools/dump_struct_layout.py` + C companion)
The end result Phase 1 is chasing — "a CI gate that fails if the Python
struct and the C struct disagree" — is already provided by
`test_regression_p0.py::P05_StructCorruption::test_python_matches_c_*`,
which compares whole-struct bytes via a real `gcc` build. A field-level
dump would give slightly better diagnostics on future failures, but it
was not required to close the P0-5 thesis. Recommend picking this up in
a follow-up task.

### Phase 3 — replace `gui.py` offset tables with ctypes `readinto()`
This is a substantial rewrite (hundreds of lines of hand-rolled offset
tables across four (DRAM × channel) combinations). It is the right
endgame, but scoping it into the same change as a correctness fix
violates the plan's own §0 guidance ("nothing on the F1–F7 roadmap is
permitted to mix with the corruption fix"). The GUI offset tables should
be re-derived from the fixed ctypes class in a dedicated PR; the
groundwork — correct ctypes layout, correct reference binaries — is now
in place. Recommend doing this next before the F1–F7 feature roadmap
begins.

### Phase 2 — codegen dedup of `orbit_defines.py` vs C headers
Not touched. `orbit_defines.py` still contains every constant twice
identically (1129 lines). This is a style/maintenance issue, not a
correctness one, and the risk/reward of mechanical dedup is poor
without the Phase 1 layout check as a safety net.

### Phases 4–5 — test suite prune, orphan script prune
Partially done (see §5). Aggressive test pruning (the plan estimates
~3000 lines removable) was left alone because no clear ownership
signal exists for the individual test files and the regression test
only locks P0 behavior.

### F1–F7 roadmap
Out of scope, as the plan explicitly states.

---

## 7. Files touched

```
MODIFIED
  ddr_config.h
  ddr_config_init.py
  gen_timing_params
  gui.py
  lpddr5_config.py
  test_gen_lpddr5_bin.sh
  test_lpddr5.sh
  ddr_timing_table.lpddr4.single.ref.bin   (regenerated)
  ddr_timing_table.lpddr4.dual.ref.bin     (regenerated)
  ddr_timing_table.lpddr5.single.ref.bin   (regenerated)
  ddr_timing_table.lpddr5.dual.ref.bin     (regenerated)

ADDED
  test_regression_p0.py
  reports/26-04-11/codebase_review_refactor_implementation_report.md

DELETED
  orbit_config_fixed.py
  orbit_config_new.py
  orbit_config.py.backup
  orbit_config.py.python2
  ddr_timing_table.bin.backup
  mr_config_gen.h.backup
  orbit_init_gen.h.backup
  test_fixed_size.py
  test_new_size.py
  check_offset.py
  check_offsets.py
  check_offsets2.py
  debug_offset.py
  print_field_offsets.py
  print_py_offsets.py
  print_offsets.py
  __pycache__/
  *.pyc (repo root)
```

---

## 8. How to verify

```
# Run the new P0 regression suite (rebuilds both paths via gcc)
python3 test_regression_p0.py

# Run the plan's "only real cross-validation" test
# (must be run after the LP4 single-channel Python path has populated
#  ddr_timing_table.bin, which the regression test above does)
python3 test_binary_match.py

# Spot-check a committed reference binary
python3 gen_timing_params --dram-type lpddr5 --phy-name sphy-v9r8 \
  --speed-bin 6400 --dq-width 16 --orbit-config-density 16 \
  --wire-length 10 --read-dbi-upto 10000 --write-dbi-upto 10000 \
  --write-lecc-upto 625 --write-odt-upto 10000 --cpipe-depth 1 \
  --dpipe-depth 1 --omc-freq-ratio 1 --phy-freq-ratio 1 \
  --wck-1to4-upto 625 --wck-always-on-from 0 --wck-always-on-upto 10000 \
  --orbit-config-use-python 314 418 556 2500
cmp ddr_timing_table.bin ddr_timing_table.lpddr5.single.ref.bin
```

---

## 9. Recommended next steps

1. **Phase 3 (GUI ctypes parser rewrite)** is the next high-value item.
   The foundation — a trustworthy ctypes class and trustworthy reference
   binaries — now exists. Until this lands, any GUI-side offset drift
   will quietly mis-parse binaries produced by the fixed pipeline.
2. **Phase 1 (struct-layout dump)** is cheap and worth adding as a
   diagnostic layer on top of the whole-struct parity test. It will
   make future layout failures much easier to triage.
3. **Phase 2 (codegen for constants)** should wait until after Phase 1
   provides a mechanical guarantee that Python and C definitions agree.
