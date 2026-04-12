# DDR Timing Table Tool — Codebase Review, Bug Fix Plan & Refactoring Strategy

**Author:** Staff DDR driver engineer review
**Date:** 2026-04-10
**Scope:** Complete audit of `gen_timing_params`, `gui.py`, `orbit_config.py`,
`ddr_config_init.py`, `lpddr{4,5}_config.py`, `orbit_defines.py`, `ddr_config.h`,
`ddr_config_bin.c`, `gen_ddr_config`, `arise2_omc.h`, and the test suite.

---

## 0. Executive Summary

The tool has a real working core — timing calculations for LPDDR4/5 are plausible and
the C reference path (`gen_ddr_config` + `ddr_config_bin.c`) produces sane binaries for
the default case. But on top of that core, several layers have been patched incrementally
without addressing root causes, producing a brittle structure:

- **The Python ctypes orbit_config layout is correct; the manual file-offset patching
  in `ddr_config_init.py:260-313` is what corrupts the output.** Verified this session
  by compiling `print_offsets.c` for LP4 single (`DDR_TYPE=2 DDR_TWO_CHANNEL=0`) and
  comparing field offsets to `ctypes.offsetof(make_orbit_config_class('lpddr4', False))`
  — every field agrees, `sizeof == 3048` both sides. The manual patch hardcodes
  *dual-channel* offsets (`base_addr_id[0..3]` at `0x8C4..0x8D0`, `phy_base_addr` at
  `0x8D4`, `phy_base_addr_id[0..3]` at `0x8D8..0x8E4`) and writes them over the
  correctly-placed single-channel fields, clobbering `phy_base_addr` (0xCC),
  `phy_base_addr_id` (0xD0), `tphyupd_resp` (0xD8),
  `dynamic_self_refresh_threshold` (0xDC) and zeroing `dynamic_power_down_threshold`
  (0xE0) and `zq_calibration_period` (0xE4). For LP5 the same patch also clobbers
  `base_addr` itself because the 8 extra `lp5_*` bytes shift `base_addr` from `0xC0`
  to `0xC8`.
- **`test_binary_match.py` is currently FAILING** (11 mismatches at offsets
  `0xCE..0xE5`, exactly the bytes touched by the manual patch — verified this session).
  The test is the only real cross-validation in the suite, and it is broken.
- **The committed reference binaries are wrong.** `ddr_timing_table.lpddr4.single.ref.bin`
  contains the manual-patch corruption verbatim (zeros at `0x8CC..0x8D3`, wrong
  `phy_base_addr` location, zeroed `zq_calibration_period`). Every recent
  "fix LP4/LP5 binary parsing: offset X→Y" commit (`7d74799`, `ddf6a16`, `d7e443c`)
  has been chasing the manual-patch corruption into new fields without realising the
  ctypes struct was already correct.
- **Binary parsing in the GUI is done via hand-coded absolute byte offsets** for every
  (DRAM type × channel) combination, instead of being derived from the struct layout.
  The GUI offset tables currently agree with the corrupted reference binary, not with
  the correct C layout — once the manual patch is removed, every GUI offset that lands
  in the `0xCC..0xE8` region must be re-derived from ctypes.
- **The GUI sends CLI flags that `gen_timing_params` does not accept.** The GUI emits
  `--orbit-eye-scan-rd-en`, `--orbit-command-bus-training`, `--orbit-init-zq-calibration`,
  `--orbit-phy-vref-trn-mode` etc. at `gui.py:812-836`. None are registered in
  `gen_timing_params.parse_args()`. Those code paths fail at argparse validation.
- **Several correctness bugs** in timing calculation: inverted `wck_always_on` logic,
  `mr_rtp = self.mr_wr` copy-paste, and bare `args` references that rely on module-level
  global state instead of `self.args`.
- **Tests have weak coverage.** `test_random_value_flow.py` writes a ctypes struct and
  reads it back via the GUI offset tables — it verifies the GUI parser agrees with the
  ctypes writer, but cannot detect C/Python divergence or timing-calculation bugs.
  `test_gui_params.py` is 2513 lines and mostly validates the offset tables against
  fixtures the tests themselves generate.
- **Structural waste.** `orbit_defines.py` (1129 lines) defines every constant
  *twice identically*. Test suite is 6035 lines across 22 files, much of it redundant.
  Repo root also contains 12+ orphaned debug scripts, multiple `orbit_config*.py`
  variants, `.pyc` files, and `*.backup` files.

The right fix is not more offset patches. The Python struct layout is already correct
— delete the manual patching, regenerate the reference binaries, and replace GUI
offset tables with `ctypes.readinto()` against the authoritative ctypes class.

**One revision to the original refactor direction:** Phase 2 has been rewritten.
The original plan proposed deleting the C path (`gen_ddr_config` +
`ddr_config_bin.c`) outright. That intent is reversed — the C path is retained
as a CI-only second source of truth (via a new `make check-c-python-parity`
gate), and only the *duplication* of tables/constants between Python and C is
eliminated (via codegen, Python as source). Rationale: the C reference is the
cheapest independent oracle against the GPU/MC RTL expectations, and the class
of bug that P0-5 represents is exactly the kind that a second source catches
at commit time. See revised §3 Phase 2 and §7 Q1 for details.

A post-refactor feature roadmap is in §8. It is deliberately **out of scope
for Phases 0–6** — nothing on that list is permitted to mix with the
corruption fix — but it documents the v2 plan so readers of this document
know where the work goes next.

---

## 1. Bug Inventory

Severity: **P0** (correctness, data corruption, or tool failure), **P1** (wrong behavior
under supported use), **P2** (maintenance, code smell, user experience).

### P0 — Critical correctness bugs

#### P0-1: `mr_rtp` is set to the value of `mr_wr` (copy-paste bug)
- **File:** `gen_timing_params:526`
- **Symptom:** Every emitted timing entry has `mr_rtp == mr_wr`. RTP (read-to-precharge)
  timing is written with the wr value. Wrong MR register value downstream; potentially
  corrupts real hardware behavior at certain frequencies.
- **Fix:** `mr_rtp=self.mr_rtp,`
- **Risk:** Existing reference binaries were generated with this bug. A golden-binary
  regeneration is required after fixing, and the old reference bins committed to the
  repo (`ddr_timing_table.lpddr4.single.ref.bin`, `.lpddr5.single.ref.bin`) must be
  regenerated.

#### P0-2: `wck_always_on` logic is inverted
- **File:** `gen_timing_params:155-157`
- **Current code:**
  ```python
  wck_always_on_from = 1000000 if self.args.wck_always_on_from == 0 else self.args.wck_always_on_from
  wck_always_on_upto = 1000000 if self.args.wck_always_on_upto == 0 else self.args.wck_always_on_upto
  self.wck_always_on = wck_always_on_from >= t_ck and wck_always_on_upto <= t_ck
  ```
- **Symptom:** `from >= t_ck AND upto <= t_ck` can only be true when `from == upto == t_ck`
  exactly, which is not what "always-on between from and upto" means. The semantic is
  "enable when `from <= t_ck <= upto`", so both comparisons are flipped. Additionally,
  the "0 means unset → default to 1_000_000" fallback is applied inconsistently with the
  `--wck-always-on-upto` default of 314 in test_cli_bin_compare.py — the two code paths
  disagree on what "unset" means.
- **Fix:**
  ```python
  self.wck_always_on = (self.args.wck_always_on_from <= t_ck <= self.args.wck_always_on_upto)
  ```
  Remove the 0-sentinel. If "unset" is a valid state, encode it as `None`, not as 0 or
  1_000_000.
- **Secondary fix:** argparse default for `--wck-always-on-from` is 1000000 and
  `--wck-always-on-upto` is 1000000, so by default the window is degenerate. Pick sensible
  defaults that mean "disabled" unambiguously (e.g. `from=1, upto=0` so from > upto is
  always false).

#### P0-3: Module-level `args` used instead of `self.args` inside `GenTimingParam.calculate()` and `.write()`
- **File:** `gen_timing_params:148, 149, 200, 216, 556`
- **Instances (verified line numbers):**
  ```python
  self.rpste = args.rpste_upto >= t_ck                         # line 148
  self.wpste = args.wpste_upto >= t_ck                         # line 149
  self.pipe_depth_diff = args.dpipe_depth - args.cpipe_depth   # line 200
  if args.meso_synchronizer:                                   # line 216
      self.twrdata_delay += 4*self.args.phy_freq_ratio
  with open(args.output, 'w') as f:                            # line 556
  ```
- **Symptom:** Works only because `args = parse_args()` is a module-level global in
  `if __name__ == '__main__':` (line 981). Import the module from another tool (e.g.
  a test harness that constructs `GenTimingParam(args)` directly), and every one of
  those lines raises `NameError: name 'args' is not defined`.
- **Fix:** `self.args.rpste_upto`, `self.args.wpste_upto`, etc. — always.
- **Also:** `parser.error('DQ width...')` at `gen_timing_params:41` references a
  `parser` global that doesn't exist inside `GenTimingParam.__init__`. Dead branch
  (only triggered for `ddr3`/`ddr4`, which are not registered as valid `choices` for
  `--dram-type`), but wrong nonetheless. Either delete the block or replace with
  `sys.exit("DQ width ...")`.

#### P0-4: C `ddr_config_init` hardcodes `byte_mode=0, mixed=0`, ignoring CLI flags
- **File:** `ddr_config.h:282`
- **Current code:** `orbit_update_chips(omc_config, 0, 0);`
- **Symptom:** `gen_timing_params --orbit-byte-mode 1 --orbit-mixed 1` silently has no
  effect on the C path. Only the Python path (`--orbit-config-use-python`) respects
  these flags. Users running the default (C) path get wrong `num_row`/`chip[i].size`.
- **Fix:** Either (a) thread the two flags in through generated `#define`s in the same
  way `DEFAULT_DENSITY` is threaded via `orbit_init_gen.h`, or (b) add `ORBIT_BYTE_MODE`
  and `ORBIT_MIXED` preprocessor symbols via `-D` in `gen_ddr_config`, then:
  ```c
  orbit_update_chips(omc_config, ORBIT_BYTE_MODE, ORBIT_MIXED);
  ```
- **Preferred long-term fix:** Generate `ddr_config.h`'s tables from the Python
  source (density codes, MR defaults, field enums) so the two paths cannot
  drift on this class of flag — see revised refactor §3 Phase 2. The C path
  itself is retained as a CI-only validator.

#### P0-5: `ddr_config_init.py` manual file-offset patching corrupts the struct it just wrote
- **File:** `ddr_config_init.py:260-313` (post-write patching block),
  `ddr_config_init.py:106-129` (pre-write "base address configuration" block with the
  "reference binary format" comment at line 107)
- **Symptom:** `generate_orbit_config_binary()` builds the `orbit_config` struct via
  ctypes, serializes it correctly with `ctypes.string_at`, writes the entire struct to
  the output file — **then** seeks back to hardcoded file offsets `0x8C0`, `0x8C4`, …
  `0x8E4` and overwrites bytes that were already correct. For single-channel builds,
  the "fill remaining with 0" branch (lines 293-297, 309-313) writes zeros at
  `0x8CC, 0x8D0, 0x8E0, 0x8E4` — which, in the single-channel layout, are
  `phy_base_addr`, `phy_base_addr_id[0]`, `dynamic_power_down_threshold`, and part of
  `zq_calibration_period`. These get zeroed. The following `phy_base_addr` /
  `phy_base_addr_id` writes at `0x8D4, 0x8D8, 0x8DC` then land on top of
  `phy_base_addr_id[1]`, `tphyupd_resp`, and `dynamic_self_refresh_threshold`.
- **Verification performed this session:**
  1. Compiled `print_offsets.c` for `DDR_TYPE=2, DDR_TWO_CHANNEL=0` and compared to
     `ctypes.offsetof(make_orbit_config_class('lpddr4', False))` — every field offset
     agrees, `sizeof == 3048` on both sides. The Python ctypes struct layout is
     **already identical** to the C struct layout for LP4 single.
  2. Ran `test_binary_match.py`: 11 mismatches at file offsets `0x08CE, 0x08CF, 0x08D2,
     0x08D3, 0x08D6, 0x08DA, 0x08DB, 0x08DE, 0x08DF, 0x08E4, 0x08E5`. All eleven land
     exactly inside the `0x8CC..0x8E5` region the manual patch touches. Outside that
     region the Python and C binaries match byte-for-byte.
  3. Reference `ddr_timing_table.lpddr4.single.ref.bin` has the same corruption
     (zeros at `0x8CC..0x8D3`, `phy_base_addr` at the dual-channel slot, zeroed
     `zq_calibration_period`), confirming the committed reference binary was produced
     by this same buggy patching path — not by the C implementation.
- **Root cause:** The patching block was written assuming the *dual-channel* layout
  (`base_addr_id[0..3]` at `0xC4..0xD0`, `phy_base_addr` at `0xD4`,
  `phy_base_addr_id[0..3]` at `0xD8..0xE4`) and then retrofitted with
  "if not two_channel: write zeros" for the offsets that "don't exist" in single-channel.
  But single-channel does not have those offsets as *gaps*; the single-channel ctypes
  struct reuses them for `phy_base_addr`, `phy_base_addr_id`, `tphyupd_resp`, etc.
  Zeroing them corrupts real data.
- **For LP5** (any channel config) there's an additional bug: `base_addr` itself lives
  at struct offset `0xC8` (not `0xC0`) because of the 8 extra `lp5_mr2..18` + `zq_bg_mode`
  bytes. The patch writes `base_addr` at `0x8C0` regardless of dram_type, so for LP5 it
  clobbers `reboot_with_mrw`/`ctrl_dq_width`/etc. region instead of `base_addr`.
- **Fix:** Delete lines 260-313 of `ddr_config_init.py` — the ctypes write at lines
  272-276 is already correct and complete. No patching is needed. Then:
  1. Regenerate all four reference binaries
     (`ddr_timing_table.lpddr4.{single,dual}.ref.bin`,
     `ddr_timing_table.lpddr5.{single,dual}.ref.bin`) and commit them.
  2. Re-run `test_binary_match.py` and `test_lpddr5_match.py` to confirm byte-for-byte
     parity with the C path.
  3. Audit `gui.py` offset tables (P1-3): the committed offsets were tuned to the
     corrupted reference. Anything in the `0xCC..0xE8` region must be re-derived
     against the correct ctypes layout.

#### P0-6: GUI emits CLI flags that `gen_timing_params` does not define
- **File:** `gui.py:812-836` (the "training enable" subsection of the generate handler)
- **Symptom:** The GUI unconditionally emits `--orbit-eye-scan-rd-en`,
  `--orbit-eye-scan-wr-en`, `--orbit-eye-scan-prbs-rd-en`, `--orbit-eye-scan-prbs-wr-en`,
  `--orbit-phy-vref-trn-mode`, `--orbit-command-bus-training`,
  `--orbit-init-zq-calibration` (lines 812, 814, 816, 818, 820, 828, 836 respectively).
  None of these flags are registered in `gen_timing_params.parse_args()` (verified by
  `grep -n "orbit-eye-scan\|orbit-command-bus\|orbit-init-zq\|orbit-phy-vref-trn"` →
  zero hits in `gen_timing_params`). Whenever any of those checkboxes is ticked in the
  GUI, `gen_timing_params` fails with `error: unrecognized arguments`, the subprocess
  returns non-zero, and the GUI reports the failure to the user.
  The JSON-override path at lines 890-928 writes `orbit_config_override.json` with the
  same fields under their struct names (`eye_scan_rd_en`, `command_bus_training`, etc.)
  and works correctly when `--orbit-config-json` is used alone — but the GUI
  *also* emits the broken individual flags alongside the JSON path, so both paths are
  executed and the run still fails.
- **Fix:** Decide on one of two approaches:
  1. **JSON-only interface** — delete lines 812-836 of `gui.py` entirely and rely on
     the existing JSON-override block. Keep only the structural CLI flags
     (`--two-channel`, `--orbit-byte-mode`, `--orbit-mixed`, `--orbit-num-rank`,
     `--orbit-config-density`) because those drive struct shape, not field values.
  2. **Full flag parity** — register every orbit field as a flag in
     `gen_timing_params.parse_args()`. Ideally auto-generate the argparse entries from
     the struct spec (see §3.4 Phase 4).
     Option 1 is smaller, reversible, and the GUI's JSON path already emits every
     field correctly; prefer it.

#### P0-7: Broken ternary precedence in `dsm_en`
- **File:** `gui.py:911`
- **Current code:**
  ```python
  'dsm_en': 1 if is_checked(params.get('orbit-dsm-en')) else 0 if dram_type == 'lpddr4' else (1 if is_checked(params.get('orbit-dsm-en')) else 0),
  ```
- **Symptom:** Python parses this as `1 if X else (0 if dram_type == 'lpddr4' else Y)`,
  so when `X` is truthy, `dsm_en` = 1 regardless of dram_type. But the intent is clearly
  "force dsm_en=0 for LP4 because LP4 has no DSM". The fix should zero it for LP4.
- **Fix:**
  ```python
  'dsm_en': (1 if is_checked(params.get('orbit-dsm-en')) else 0) if dram_type == 'lpddr5' else 0,
  ```

#### P0-8: `lpddr5_config.py` dead assignment to `p_t_wtr`
- **File:** `lpddr5_config.py:197`
- **Current code:**
  ```python
  else:                                                    # line 196 (x16 path)
      self.ref.p_t_wr = Timing(34 + 4*self.ref.write_lecc, 3, 0)
      self.ref.p_t_wtr = Timing(10, 8, 0)                  # line 197 — DEAD
      if self.ref.bg_mode:
          self.ref.p_t_wtr = Timing(6.25 + 4*self.ref.write_lecc, 4, 0)
      else:
          self.ref.p_t_wtr = Timing(12 + 4*self.ref.write_lecc, 4, 0)
  ```
- **Symptom:** Line 197 is immediately overwritten by one of the two branches that
  follow. Only a maintenance trap on its own, but the `Timing(10, 8, 0)` value
  doesn't match either LPDDR5 JEDEC figure (which depends on bank-group mode), so the
  dead line also represents a stale edit that someone started and abandoned.
- **Fix:** Delete line 197. Cross-check the live values against JEDEC JESD209-5
  (tWTR typically `max(4nCK, 7.5ns)` for same-BG, `max(2nCK, 2.5ns)` for different-BG
  — the bg_mode branch should correspond to different-BG, not same-BG, so the
  assignment order deserves a closer look).

### P1 — Major behavioral bugs

#### P1-1: `orbit_config.py::get_density_code` reads `orbit_init_gen.h` relative to cwd
- **Files:** `orbit_config.py:42-72`, `gen_timing_params:590-609` (generator),
  `gen_timing_params:906-931` (second reader)
- **Symptom:** `orbit_init_gen.h` is *generated* fresh by every `gen_timing_params`
  run at `gen_timing_params:590` (`with open('orbit_init_gen.h', 'w') as f`), using a
  plain relative path. `orbit_config.py::get_density_code` later reads it back with
  another plain relative path (`os.path.exists('orbit_init_gen.h')`). The same pattern
  is repeated a third time in `gen_timing_params:906-924`
  (`generate_orbit_config_bin`). All three sites share the same bug: if the caller's
  cwd is not the repo root, the generator writes the header into the wrong directory,
  the reader silently falls back to the hardcoded map, and the density_code emitted
  in the binary may not match the density_code the C build compiles against.
  Worse, if a stale `orbit_init_gen.h` from a prior run is sitting in the new cwd,
  it is consumed silently.
- **Fix:** Make the density→code mapping a single pure dict in Python (exported from
  `orbit_config.py`), and have *both* `gen_timing_params.write()` and
  `orbit_config.py::get_density_code` read it from Python, not from the generated
  `.h`. The generated `orbit_init_gen.h` should remain a write-only output for the C
  compiler (via `gen_ddr_config`) and never be re-read inside the Python process.
  All relative-path `open('orbit_init_gen.h', ...)` calls should become
  `os.path.join(os.path.dirname(os.path.abspath(__file__)), 'orbit_init_gen.h')` so
  that cwd is irrelevant.

#### P1-2: `analyze_binary_file()` in `gui.py` uses file size to guess DRAM type
- **File:** `gui.py:196-244` (the `analyze_binary_file` function)
- **Symptom:** The detector differentiates by raw `file_size` with hardcoded
  thresholds (verified in code): `>= 7860` → dual, `>= 7870` → LP5-dual;
  `5090..5200` → single, `>= 5100` → LP5-single; `3050..4000` → LP5-single (small
  variant). The actual file sizes are **LP4 single 5096, LP5 single 5104, LP4 dual
  7864, LP5 dual 7872** (0x800 timing table + struct size). Single-channel LP4 vs LP5
  differ by only 8 bytes (5096 vs 5104), and dual-channel by 8 bytes (7864 vs 7872).
  A single trailing null or stray byte from unrelated code shifts the file across
  the boundary and the parser picks the wrong layout. The user already has a
  "DRAM type override" dropdown in the GUI as a workaround, which proves the
  auto-detect is unreliable.
- **Fix:** Either (a) always require the caller (test / GUI form) to pass
  `dram_type` and `two_channel` explicitly, deleting the size-based branch, or
  (b) add a 16-byte header at file offset 0 (or at `0x7F0`, in the reserved area
  before `EMMC_CM4_TIME_TB_SIZE`) with magic bytes + version + dram_type + channel
  mode. (a) is the simpler fix and the GUI already has the override dropdown to
  feed it. See also P2-9.

#### P1-3: Hardcoded offset tables for binary parsing
- **File:** `gui.py` (the `parse_timing_entries` and `analyze_binary_file` functions,
  plus the LP4/LP5 single/dual offset maps)
- **Symptom:** Four separate tables of hardcoded field-offset pairs, one per
  (dram_type, channel) combination. Every recent fix commit adds or tweaks offsets.
  This is the single largest source of ongoing bugs in the repo.
- **Fix:** Replace with a single function that, given a struct class from
  `make_orbit_config_class(dram_type, two_channel)`, reads the binary *into* that struct
  via ctypes:
  ```python
  cls = make_orbit_config_class(dram_type, two_channel)
  cfg = cls()
  with open(path, 'rb') as f:
      f.seek(EMMC_CM4_TIME_TB_SIZE)
      f.readinto(cfg)
  # Now access cfg.density, cfg.rank_interleaving, etc. directly
  ```
  No offset tables. No magic. But this only works *after* P0-5 (struct layout
  mismatch) is resolved.

#### P1-4: (merged into P0-5)
- **Note:** Previously this entry claimed the manual patching was *a workaround for*
  a Python/C layout mismatch. Verification this session (see P0-5) shows the layouts
  already agree — the manual patching is itself the corruption, not a workaround for
  it. This is now covered in full by P0-5. Fix: delete lines 260-313 of
  `ddr_config_init.py` and regenerate reference binaries.

#### P1-5: No automated check that `make_orbit_config_class` matches `arise2_omc.h`
- **File:** `orbit_config.py:142-267`, `arise2_omc.h` (436 lines, **checked in** at
  repo root, verified via `git ls-files arise2_omc.h`)
- **Symptom:** `arise2_omc.h` *is* in the repo, with `struct orbit_config` under
  `#pragma pack(8)`. This session's cross-check (compile `print_offsets.c` with
  `-DDDR_TYPE=2 -DDDR_TWO_CHANNEL=0`, diff vs `ctypes.offsetof`) shows every field
  agrees — the Python ctypes layout is currently correct. **But nothing in the
  build/test path actually verifies this.** `test_binary_match.py` comes close
  (it compiles the C path and diffs the bytes) but today it fails for the wrong
  reason (the manual-patch corruption in P0-5) and has been mistakenly "fixed" by
  tuning Python offsets toward a corrupted reference. If any future commit to
  `arise2_omc.h` adds, removes, or reorders a field, nothing in CI will catch it
  until someone notices wrong values months later.
- **Fix:** Add a standalone offset-diff test that (1) compiles a tiny C program
  against `arise2_omc.h` with `offsetof(struct orbit_config, field)` for every
  field, (2) enumerates `cls._fields_` on `make_orbit_config_class(dram_type,
  two_channel)`, and (3) asserts the two lists agree field-name by field-name and
  offset-by-offset, for all four (dram_type × channel) combinations. Run it in CI.
  Existing scratch scripts `print_offsets.c` / `print_offsets.py` already do most
  of this — consolidate them into one gated test and delete the rest. This is the
  harness described in Phase 1 Option B.

#### P1-6: `--wck-always-on-from` default conflicts between argparse and test harness
- **File:** `gen_timing_params:674` (default=1000000), `test_cli_bin_compare.py:67`
  (passes 0)
- **Symptom:** Test harness passes `--wck-always-on-from 0`, which triggers the "0 means
  unset → 1000000" branch in `calculate()`. Because the default is also 1000000, there's
  no way to tell if a user meant "1000000" or "unset". Related to P0-2.
- **Fix:** Change default to `None`. Test for `is None` explicitly.

#### P1-7: Density code mapping is defined in four places
- **Files (verified line numbers):**
  - `gen_timing_params:571-582` (inside `write()`, `density_code_mapping` dict)
  - `gen_timing_params:590-609` (inside `write()`, emits `DENSITY_N` `#define`s and
    the `get_density_code` function body into `orbit_init_gen.h`)
  - `orbit_config.py:60-71` (inside `get_density_code` fallback dict)
  - `ddr_config.h:58-74` (C `get_density_code` function, guarded by
    `#ifndef _ORBIT_GET_DENSITY_`; only used when `ddr_config.h` is included without
    the sentinel macro)
- **Symptom:** Four implementations of the same `{1:0, 2:1, 3:2, 4:3, 6:4, 8:5, 12:6,
  16:7, 24:8, 32:9}` mapping, plus a run-time fallback in `orbit_config.py` that
  silently re-parses the generated header (see P1-1). They happen to agree today,
  but there's nothing preventing drift, and P1-1 can cause them to disagree
  *at runtime* in the same process if cwd is wrong.
- **Fix:** Define the mapping once in `orbit_config.py` as a module-level dict.
  - `gen_timing_params:571-582` imports that dict instead of redefining it.
  - `gen_timing_params:590-609` emits both the `#define` list and the
    `get_density_code` C function body by iterating the dict, not by hardcoding.
  - `orbit_config.py::get_density_code` looks up the dict directly — delete the
    `orbit_init_gen.h` re-read path entirely.
  - `ddr_config.h:58-74`: either keep as a failsafe and add a CI check that compares
    it to the emitted `orbit_init_gen.h`, or delete it and always take the mapping
    from `orbit_init_gen.h` (preferred).

#### P1-8: `get_type_format_list()` assumes C struct natural alignment matches `struct.pack` with no padding
- **File:** `gen_timing_params:791-803`, `gen_timingtable_bin()`
- **Symptom:** Builds a `struct.pack` format string by mapping C types to Python
  format codes (`'unsigned int' → 'I'`, `'unsigned short int' → 'H'`, `'unsigned char' → 'B'`),
  then concatenates them. This only works because:
  1. The format string starts without `'<'` or `'='`, so Python uses native byte order
     and **native alignment with padding**.
  2. The C struct `timing_param` is 4-byte aligned for `unsigned int` fields, and
     the fields happen to align the same way Python would native-align them.
  Any accidental field reordering, or any change that breaks alignment, produces silent
  binary corruption. There is no validation that the resulting byte string matches any
  C reference.
- **Fix:** Explicit format prefix (`'='` = native, no alignment; `'<'` = little-endian, no
  alignment), then add explicit padding. Or, better, mirror the timing_param struct
  as a ctypes class with explicit fields — same fix strategy as orbit_config.

#### P1-9: GUI generate path has no structured failure reporting
- **File:** `gui.py:945-954`
- **Current code (verified):**
  ```python
  try:
      result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
      if result.returncode != 0:
          message.append(f"gen_timing_params failed: {result.stderr}")
          success = False
      else:
          message.append("ddr_timing_table.bin generated successfully")
  except Exception as e:
      message.append(f"Error running gen_timing_params: {e}")
      success = False
  ```
- **Status:** `success` is correctly flipped to `False` on both non-zero exit and
  exceptions — the original claim in this plan that the GUI may return success=True
  after a failed subprocess was wrong. The try/except correctly propagates to the
  response JSON at `gui.py:959`.
- **Remaining nit (P2-level):** stderr is appended as a single blob without separating
  argparse errors from Python tracebacks; if the user typo'd a CLI flag vs the tool
  actually crashed, the GUI message looks the same. Also, `timeout=120` is arbitrary
  and a timeout exception will reach the generic `except Exception` path with a
  vague message. Neither is a P1 bug. Downgrade this entry to P2 or remove it entirely
  after P0-6 (undefined CLI flags) is fixed, since that is the realistic trigger for
  non-zero exits today.

#### P1-10: `generate_orbit_config_bin` CLI defaults cannot be recovered; JSON silently wins over every CLI value
- **Files:** `gen_timing_params:899-903` (CLI → overrides), `gen_timing_params:935-940`
  (JSON → overrides, applied *after*)
- **Current code (verified):**
  ```python
  for arg_name, field_name in field_map.items():
      if hasattr(args, arg_name):
          value = getattr(args, arg_name)
          # Only add if not default (to allow CLI defaults to work)
          overrides[field_name] = value               # line 903
  ...
  if args.orbit_config_json:
      with open(args.orbit_config_json, 'r') as f:
          json_overrides = json.load(f)
          overrides.update(json_overrides)            # line 940
  ```
- **Symptom:**
  1. The comment at line 902 says "Only add if not default", but the code adds every
     field unconditionally. There is no way to distinguish "user didn't pass
     `--orbit-t-refiab`" from "user passed `--orbit-t-refiab 3904000`" because
     argparse returns the default for both cases. So every orbit field is written
     into `overrides` on every run.
  2. JSON is applied *after* CLI with `overrides.update(json_overrides)` — which means
     **JSON values always win over CLI values**, including CLI values the user
     explicitly set. The precedence is actually `JSON > CLI`, not `CLI > JSON`. An
     earlier version of this plan claimed the direction was reversed; the direction
     is correct in the code, but neither direction is reachable today because (1)
     erases the distinction between "user set" and "default".
- **Fix:** Use `argparse`'s `default=argparse.SUPPRESS` (or a sentinel like `None`)
  for every `--orbit-*` field that is allowed to be JSON-overridden. Then the loop
  at line 899 only copies fields the user actually typed on the command line.
  Precedence becomes "CLI (if set) > JSON (if set) > struct-class default". Swap
  the ordering at 935-940 so JSON is applied *before* the CLI loop if we want CLI
  to win, or keep the order and document "JSON wins" — pick one and test it
  (see P2-11 coverage gap #6).

### P2 — Code smell and maintenance debt

#### P2-1: `orbit_defines.py` is 1129 lines of duplicate definitions
- **File:** `orbit_defines.py`
- **Symptom:** Nearly every constant (e.g. `DRAM_TYPE_SHIFT = 0`) is defined twice
  identically. Half the file is wasted space. `grep -c` on a spot-check of
  `ROW_WIDTH_SHIFT` shows each constant twice.
- **Fix:** `awk '!seen[$0]++'` or equivalent, verify semantic equivalence, commit the
  deduplicated file.

#### P2-2: Orphaned debug scripts and `.backup` files in the repo root
- **Debug scripts (verified present):** `check_offset.py`, `check_offsets.py`,
  `check_offsets2.py`, `compare_bin.py`, `debug_offset.py`, `print_field_offsets.py`,
  `print_offsets.c`, `print_offsets.py`, `print_offsets_clean.c`, `print_py_offsets.py`,
  `print_timing_offsets.c`, `verify_offsets.py` (12 files total).
- **Backup files (verified present):** `ddr_timing_table.bin.backup`,
  `mr_config_gen.h.backup`, `orbit_config.py.backup`, `orbit_init_gen.h.backup`
  (all from March 27-30 — multiple weeks old).
- **Symptom:** 12 debugging scripts from the offset-chasing saga, most with no
  docstring, no test, and no clear owner; plus 4 `.backup` files that reflect a
  manual "save a copy before editing" workflow that git already provides. Inflates
  repo surface area and makes it unclear which files are authoritative.
- **Fix:**
  - Debug scripts: keep exactly **one** canonical struct-layout dumper (probably a
    consolidated `tools/dump_struct_layout.py` that replaces `print_offsets.py` +
    `print_field_offsets.py` + `verify_offsets.py`), wire it into CI per P1-5, and
    delete the rest.
  - `.backup` files: delete all four. Git is the backup.
  - Move the kept tool to `tools/` with a README line documenting what it does and
    how CI consumes it.

#### P2-3: Multiple orbit_config.py variants
- **Files:** `orbit_config.py`, `orbit_config.py.python2`, `orbit_config_fixed.py`,
  `orbit_config_new.py`
- **Symptom:** Four versions of the same file. Unclear which is canonical.
- **Fix:** Delete all but one. Use git history for the others.

#### P2-4: LPDDR4 `# FIXME from` incomplete comment
- **File:** `lpddr4_config.py:144`
- **Symptom:** `# FIXME from` appears mid-file with no follow-up text. Indicates
  someone was about to note a bug and was interrupted.
- **Fix:** Either resolve or delete the comment. The line below it should be reviewed
  against LPDDR4 JESD209-4.

#### P2-5: LPDDR5 stubbed-out FIXMEs
- **File:** `lpddr5_config.py:151` (`if True: # FIXME CA or CS ODT is enabled`),
  `lpddr5_config.py:291` (`rdqs_mode = 0b10 # FIXME`)
- **Symptom:** Two unresolved FIXMEs stub out what should be conditional logic.
  Line 151: the feature check (is CA ODT or CS ODT enabled at this frequency?) is
  hardcoded true. Line 291: `rdqs_mode` is pinned to `0b10` with no rationale,
  even though downstream it feeds into `use_rdqs_as_input` and t_rtw/t_rtw_odt
  calculations.
- **Fix:**
  - Line 151: replace `if True` with the correct condition. Cross-reference with
    `--orbit-ca-odt` flag and `nt_odt_upto` / `bg_mode_upto` for LPDDR5.
  - Line 291: derive `rdqs_mode` from a CLI flag (or the existing
    `--orbit-rdqs-mode` struct field if present) and document the allowed values.
  - Both should land in the LPDDR5 timing unit tests added in Phase 5.

#### P2-6: Chinese-language error messages in C code
- **File:** `ddr_config_bin.c:21, 27, 34` (also `gen_ddr_config:83-127` has Chinese
  strings in the shell-script main)
- **Current:** `perror("生成timing table:文件打开失败");`,
  `perror("生成timing table:文件指针定位失败");`,
  `perror("生成timing table:数据写入失败");`
- **Symptom:** Mixed-language errors confuse both English-only and Chinese-only
  maintainers. Not a bug per se but unusual for a tool targeted at multi-team use.
- **Fix:** Standardize on English error messages; or add i18n if the team's OS locale
  is Chinese. Pick one. Either way, apply consistently across `ddr_config_bin.c` and
  `gen_ddr_config`.

#### P2-7: `gen_ddr_config` has hardcoded include path
- **File:** `gen_ddr_config`
- **Symptom:** `../../arise2_gpu/product/arise2/module/arise2_omc/include` is a path
  that only works if this repo is cloned into a specific parent directory. Portable
  machines, CI, other developers — all break.
- **Fix:** Make include paths configurable via environment variable
  (`ARISE2_INCLUDE_DIR`) or a simple `--include-dir` flag on `gen_ddr_config`.

#### P2-8: `gui.py` uses relative path for `gen_timing_params`
- **File:** `gui.py:681` (the generate handler)
- **Current:** `cmd = [sys.executable, 'gen_timing_params']`
- **Symptom:** Works when GUI is launched from the repo root, breaks otherwise. The
  GUI does `os.path.dirname(__file__)` elsewhere but not here.
- **Fix:** `cmd = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gen_timing_params')]`

#### P2-9: No version/compatibility marker in generated binaries
- **Symptom:** A binary generated today, and a binary generated by next year's tool
  with a different struct layout, are byte-identical in appearance. No way to tell them
  apart. No way for the GUI parser to refuse an unknown-version binary.
- **Fix:** Add a 16-byte header at offset 0 (before the timing table) or at offset
  0x7F0 (before the orbit config) with magic + version + struct layout hash. Very cheap
  insurance against the next layout migration.

#### P2-10: `plan/` directory is full of 40+ stale plan docs
- **Files:** `plan/26-03-31/`, `plan/26-04-01/`, ... through `plan/26-04-10/`
- **Symptom:** The user's directory tree shows 40+ plan files in dated subdirectories,
  most marked modified. Indicates chaotic iteration without pruning completed plans.
- **Fix:** Archive completed plans under `plan/archive/` or delete them after the
  corresponding commit is merged. Keep only the currently-active plan in `plan/current/`.
  (This plan lives in `plans/` — a new directory — to avoid confusion with the existing
  `plan/` tree.)

#### P2-11: 22 test files, 6035 lines, high redundancy
- Several tests are single-purpose size checks (`test_size.py`, `test_new_size.py`,
  `test_fixed_size.py` — 8, 15, 13 lines each). These should be consolidated into one
  `test_struct_sizes.py`.
- `test_gui_params.py` is 2513 lines and effectively tests the GUI's offset tables
  against fixtures it generates itself — a tautology.
- `test_random_value_flow.py` runs 452 cases that write a ctypes struct and read it
  back with the same ctypes struct — cannot catch any real bug.
- **Fix:** See §4.

#### P2-12: `wck_ratio` CLI type is set to char but value range is 1-4
- **File:** `gen_timing_params:757` (`'unsigned char wck_ratio'`)
- **Observation:** Not a bug, but worth calling out — 1 byte is fine for a 1..4 enum.
  However, at P0-5 resolution time, re-verify that all 1-byte enum fields are still
  correctly aligned.

---

## 2. Test suite assessment

| Test | Lines | What it actually tests | Verdict |
|------|------:|------------------------|---------|
| `test_binary_match.py` | 68 | Python LP4 single (density=16) vs C binary | Useful — the only real cross-validation. **Currently FAILING** this session with 11 byte mismatches at offsets `0x08CE..0x08E5`, all caused by the manual-patch corruption in P0-5. |
| `test_lpddr5_match.py` | 69 | Same for LP5 | Useful; same P0-5 corruption expected, not re-run this session. |
| `test_cli_bin_compare.py` | 308 | CLI runs with varying params, checks binary is generated and nonzero | Weak — doesn't validate *what* is in the binary |
| `test_binary_parse.py` | 398 | Parses binary via GUI offset tables, checks values | Circular — tests that offset tables parse binaries that were laid out using those offsets |
| `test_random_value_flow.py` | 199 | Python struct → write → Python parse | **Tautological** — cannot fail unless ctypes is broken |
| `test_gui_params.py` | 2513 | GUI generates binaries, checks fields | Mostly circular; some value is in catching regressions |
| `test_gui_checkbox_integration.py` | 400 | Checkbox → binary → parse | Circular unless cross-checked with C |
| `test_checkbox_flow.py` | 99 | Subset of above | Redundant |
| `test_density_compat.py` | 166 | Density→code mapping | Useful but duplicates logic under test |
| `test_density_arrays.py` | 218 | Density arrays in timing table | Useful |
| `test_threshold.py` | 145 | power-down / self-refresh threshold passthrough | Useful |
| `test_timing_entry_validation.py` | 882 | Validates timing entry structure | Useful |
| `test_json_override.py` | 99 | JSON override applied | Useful |
| `test_dual_channel.py` | 53 | Dual channel binary generation | Useful-ish |
| `test_lpddr5.py` | 51 | LP5 binary generation | Redundant with test_lpddr5_match.py |
| `test_size.py`, `test_new_size.py`, `test_fixed_size.py` | 8+15+13 | sizeof assertions | Consolidate |
| `test_lpddr4.sh`, `test_lpddr5.sh` | 132+131 | Shell integration test: Python binary vs C binary | **Most useful** — genuine end-to-end |
| `test_gen_lpddr4_bin.sh`, `test_gen_lpddr5_bin.sh` | 34+34 | Simpler versions of above | Redundant |

**Critical coverage gaps:**

1. **Timing calculations themselves are not unit-tested.** There is no test that says
   "for LP4 at tCK=938 and speed-bin=4266, expect `t_rcd=X, t_rrd=Y, t_faw=Z`". Every
   calculation bug (P0-1 mr_rtp, P0-2 wck_always_on) would pass every test in the suite.
2. **No property-based tests** on calculated timings (e.g. "tRCD must be ≥ tRP", "write
   latency must be ≥ read latency + N", invariants from JESD spec).
3. **No test validates the GUI form against the CLI arg list.** A test could grep both
   `gui.html` and `gen_timing_params` and fail if they disagree on flag names — would
   catch P0-6.
4. **No test validates Python struct layout against C struct layout.** Would catch
   P0-5 and every recent "fix offset" bug.
5. **No regression test for P0-4** — the C `orbit_update_chips(0,0)` bug silently passes
   every test that runs the C path without `--orbit-byte-mode 1`.
6. **No test for `--orbit-config-json` precedence** (P1-10).

---

## 3. Refactoring plan

The goal is to stop playing whack-a-mole with offsets and make the tool's core
representable in one place. Work in this order; each phase is independently shippable.

### Phase 0: Stop the bleeding (P0 fixes, no refactor)

**Scope:** Fix the correctness bugs without changing architecture.
**Deliverable:** All P0 bugs closed. All P0 items have a regression test added to
`test_regression_p0.py`. `test_binary_match.py` and `test_lpddr5_match.py` pass.

1. `ddr_config_init.py:260-313` — **delete the manual file-offset patching block
   entirely** (P0-5). The ctypes `f.write(struct_data)` call at lines 272-276
   already produces a correct binary; no post-write patching is required. Also
   remove the stale comment at line 107 ("Note: Using direct file offset writes for
   compatibility with reference binary format") since that "compatibility" was with
   a corrupted reference.
2. **Regenerate all four reference binaries** after step 1:
   - `ddr_timing_table.lpddr4.single.ref.bin`
   - `ddr_timing_table.lpddr4.dual.ref.bin`
   - `ddr_timing_table.lpddr5.single.ref.bin`
   - `ddr_timing_table.lpddr5.dual.ref.bin`
   The current committed binaries are corrupted by the manual patch (verified this
   session: single-channel LP4 reference has zeros at `0x8CC..0x8D3`, `phy_base_addr`
   in the dual-channel slot, zeroed `zq_calibration_period`). Every "fix offset"
   commit since `5e1b3b3` has been tuning Python to match the corruption. The
   regeneration is prerequisite for every subsequent fix.

   **Regeneration protocol** (to keep downstream consumers unbroken and the bug
   bisectable):
   1. Before regenerating, grep the wider org for these filenames:
      `git log --all -- 'ddr_timing_table.*.ref.bin'` in this repo, and a code
      search across any repo that might consume these as a build artifact or a
      test fixture. If any hit is found, coordinate with that team before the
      commit lands.
   2. Tag the current HEAD as `refs-pre-p05-corruption-fix` *before* the
      regeneration commit so the corrupted bytes remain reproducible for
      bisection and for external consumers who have not yet migrated.
   3. Land the regeneration as a **standalone commit** containing only the four
      `.bin` files. The commit message must:
      - State that the previous binaries were corrupted by P0-5, not golden.
      - List the affected byte ranges per DRAM type / channel mode (for LP4
        single: `0xCC..0xE7` region — `phy_base_addr`, `phy_base_addr_id`,
        `tphyupd_resp`, `dynamic_self_refresh_threshold`,
        `dynamic_power_down_threshold`, `zq_calibration_period`; for LP5 also
        `base_addr` shift).
      - Include a bisect breadcrumb: "If your tests fail on these offsets after
        this commit, you were comparing against P0-5 corruption — see
        `plans/codebase_review_and_refactor_plan.md` §1 P0-5."
      - Reference the `refs-pre-p05-corruption-fix` tag for the old bytes.
   4. Open Question 3 in §7 is a blocker for this step — do not commit the
      regenerated binaries until the user has confirmed there are no downstream
      consumers, or the migration has been coordinated.
3. `gen_timing_params:526` — fix `mr_rtp=self.mr_rtp` (P0-1).
4. `gen_timing_params:155-157` — rewrite `wck_always_on` logic (P0-2).
5. `gen_timing_params:148, 149, 200, 216, 556` — replace bare `args` with `self.args`
   everywhere inside `GenTimingParam`. Also fix `gen_timing_params:41`
   (`parser.error` → `sys.exit` or delete dead branch) (P0-3).
6. `ddr_config.h:282` — wire `ORBIT_BYTE_MODE` / `ORBIT_MIXED` through
   `orbit_init_gen.h` the same way `DEFAULT_DENSITY` is wired (P0-4).
7. `gui.py:812-836` — delete the broken `--orbit-eye-scan-*`,
   `--orbit-command-bus-training`, `--orbit-init-zq-calibration`,
   `--orbit-phy-vref-trn-mode` CLI emissions; rely on the existing JSON override
   path at lines 890-928 (P0-6).
8. `gui.py:911` — fix `dsm_en` ternary (P0-7).
9. `lpddr5_config.py:197` — delete dead `p_t_wtr = Timing(10, 8, 0)` assignment (P0-8).
10. Write `test_regression_p0.py` that exercises each bug:
    - `test_binary_match.py` and `test_lpddr5_match.py` must pass (P0-5).
    - Assert `mr_rtp != mr_wr` in a generated binary when run with distinct upstream
      conditions (P0-1).
    - Assert `wck_always_on=True` at `t_ck=500` with `--wck-always-on-from=400
      --wck-always-on-upto=600` (P0-2).
    - Import `GenTimingParam` directly without going through `__main__`, verify it
      runs (P0-3).
    - Assert that `--orbit-byte-mode 1` changes `chip[0].num_row` in the C-path
      binary (P0-4).
    - Assert that every GUI-emitted CLI flag is a valid `gen_timing_params` argument,
      by parsing `gui.py` for `--orbit-*` string literals and cross-checking against
      `gen_timing_params --help` (P0-6).
    - Assert that LP4 always has `dsm_en=0` regardless of form input (P0-7).

### Phase 1: Lock the struct layout with a CI check

**Scope:** Make it impossible for `orbit_config.py` to silently drift from the C
`struct orbit_config` in `arise2_omc.h`.
**Deliverable:** A CI gate that fails if any field name, offset, or total size
disagrees between the Python ctypes class and the C header, for all four
(dram_type × channel) combinations.

**Important:** The Python ctypes layout is **currently correct**. The real bug
(P0-5) was that `ddr_config_init.py` wrote a correct struct and then overwrote
chunks of it with hardcoded dual-channel offsets. After P0-5 is fixed in Phase 0,
there is no layout problem to solve. This phase is preventative: it ensures no
future edit to `arise2_omc.h` or `orbit_config.py` can re-introduce the problem.

No `ctypesgen` / `pycparser` is needed. We can keep `orbit_config.py` as a
human-maintained ctypes module and gate it with a diff test.

**Steps:**

1. Consolidate the existing scratch dumpers into a single
   `tools/dump_struct_layout.py` (Python side) and `tools/dump_struct_layout.c`
   (C side). The Python version enumerates `cls._fields_` on
   `make_orbit_config_class(dram_type, two_channel)` and prints
   `"<field> <offset>"` plus `"sizeof <N>"`. The C version uses `offsetof` on
   `struct orbit_config` after including `arise2_omc.h` with the appropriate
   `-DDDR_TYPE=<2|3> -DDDR_TWO_CHANNEL=<0|1>`. Delete `print_offsets.c`,
   `print_offsets_clean.c`, `print_offsets.py`, `print_py_offsets.py`,
   `print_field_offsets.py`, `verify_offsets.py`, `check_offset.py`,
   `check_offsets.py`, `check_offsets2.py`, `debug_offset.py` once consolidated.

2. Write `tests/test_struct_layout.sh` that runs both dumpers for each
   (dram_type × channel) combination and diffs them:
   ```sh
   for dt in 2 3; do
     for ch in 0 1; do
       make dump_struct_layout DDR_TYPE=$dt DDR_TWO_CHANNEL=$ch
       ./dump_struct_layout > c_layout.txt
       python tools/dump_struct_layout.py --dram-type=$dt --two-channel=$ch > py_layout.txt
       diff c_layout.txt py_layout.txt || exit 1
     done
   done
   ```

3. Run this test in CI. It is cheap (~100ms per combination), deterministic, and
   catches the entire class of "offset drift" bugs at commit time.

4. In the same phase, delete:
   - `ddr_config_init.py:260-313` (already done in Phase 0 step 1, listed here
     for documentation).
   - `orbit_config.py:42-57` (the `orbit_init_gen.h` re-read path inside
     `get_density_code`).
   - The stale `orbit_init_gen.h` re-read in `gen_timing_params:906-931`.
   - All `.backup` files (P2-2).

5. **Treat `arise2_omc.h` as a vendored upstream header with an explicit sync
   workflow.** It is already checked in at the repo root (436 lines, verified
   this session), but there is no record of which upstream revision it came
   from, which means any future "who updated the header and forgot the struct"
   incident is unbisectable. Add the following in this phase:
   - `scripts/sync_omc_header.sh` — a one-line wrapper that copies the header
     from its canonical upstream path (to be confirmed with the GPU/MC team —
     see §7 Open Question 2) and rewrites the `SOURCE` marker described below
     from the upstream `HEAD` SHA + date.
   - A **SOURCE marker** as the first non-license comment block in
     `arise2_omc.h`:
     ```c
     // SOURCE: <upstream-repo-url>@<40-char-sha> <YYYY-MM-DD>
     // Synced by scripts/sync_omc_header.sh — do not edit by hand.
     ```
     This is the single source of truth for "which upstream revision are we
     pinned to".
   - A CI rule (`tests/test_omc_header_marker.sh`): if `git diff HEAD~1 HEAD --
     arise2_omc.h` is non-empty, the SOURCE marker's SHA field must also have
     changed. Otherwise fail with "arise2_omc.h was edited by hand — use
     scripts/sync_omc_header.sh". This catches the exact failure mode where an
     engineer edits the vendored header in place to "just fix one struct field"
     and loses the upstream provenance.
   - The Phase 1 layout CI check (step 2 above) must run **after**
     `sync_omc_header.sh` on branches that touch the header, so the Python
     ctypes class is diffed against the freshly-synced header, not a stale
     copy.
   - Open Question 2 in §7 asks the user for the canonical upstream path. Until
     that is confirmed, the sync script is written against a placeholder path
     and the SOURCE marker is stubbed with `UNCONFIRMED` — this still catches
     hand edits via the CI rule even before the path is known.

### Phase 2: Freeze the C path as a CI-only second source of truth

**Scope:** `ddr_config_init.py` is a line-by-line translation of `ddr_config.h`.
The original plan proposed deleting the C path outright. **Revised:** don't.
In DRAM driver work the C reference is the cheapest independent oracle against
the GPU/MC RTL expectations — the day `ctypes.readinto()` and the silicon
disagree, you want `gen_ddr_config` + `print_offsets.c` still building so you
can arbitrate. Deleting it turns a five-minute diagnosis into a two-week
bisect through deleted history.

**Deliverable:** The Python implementation is the **primary production output**
consumed by the driver. The C implementation is retained in-tree, built in CI
only, and used exclusively to cross-validate the Python output. Duplication of
*tables and constants* (density codes, MR values, field enums) is eliminated.
Duplication of the *binary writer* is deliberately retained.

**Rationale:**
- The Python implementation already has `generate_orbit_config_binary()`. It
  becomes the single production path.
- `ddr_config_bin.c` adds 41 lines of dependency on `arise2_config.h`,
  `orbit_init_gen.h`, `mr_config_gen.h`, `arise2_omc.h`, `ddr_config.h`, plus
  a cross-compiler toolchain. That's acceptable for a CI-only validator: the
  toolchain already exists (the GPU build needs it) and the second source is
  the thing that would have caught P0-5 at commit time.
- The C path's *real* cost is not the code — it's the four-way duplication of
  density codes, MR tables, and field enums (P1-7). That is what this phase
  removes, while the writer code stays.
- `--orbit-config-use-python` becomes the default and only production mode
  (CLI flag dropped after one release of deprecation warning), but the C build
  target remains as `make check-c-python-parity`.

**Migration:**
1. **Audit every caller of the C path.** In-repo: `test_lpddr4.sh`,
   `test_lpddr5.sh`, `test_gen_lpddr4_bin.sh`, `test_gen_lpddr5_bin.sh`,
   `test_binary_match.py`, `test_lpddr5_match.py`. Any production build
   systems referencing the C path (check `gen_ddr_config` callers — Open
   Question 1 in §7) must be updated to call the Python entry point instead.
2. **Switch the production path to Python.** Make `--orbit-config-use-python`
   the default. Emit a one-release deprecation warning if a caller passes
   `--no-orbit-config-use-python` (or whatever the opt-out is). Remove the
   flag entirely in the release after.
3. **Add `make check-c-python-parity` as a CI gate.** This target:
   - Builds `gen_ddr_config` for each of the four
     `(lp4, lp5) × (single, dual)` combinations.
   - Runs the Python generator for the same four combinations and a fixed
     matrix of representative configs (at minimum: one density per supported
     density code, one period per supported speed bin, every feature flag that
     has a non-identity effect on the binary — `byte_mode`, `mixed`,
     `dsm_en`, `wck_always_on`, `variable_trrd`, `txsr_as_1st_ed`).
   - Diffs the resulting `.bin` files byte-for-byte and fails on any
     mismatch.
   - Runs on every PR. This is the structural replacement for "Phase 0
     regression test" — once this exists, it's the single highest-value test
     in the suite, because it catches every class of Python/C divergence
     without anyone writing a new test case.
4. **Collapse the four-way-duplicated tables** into one source:
   - Density code mapping (P1-7): define once in
     `orbit_tables.py`. `orbit_defines.py` imports from it. `ddr_config.h`
     gets a generated `orbit_tables.gen.h` produced by
     `tools/gen_orbit_tables.py` at build time; CI fails if the generated
     header is out of sync with the Python source (same pattern as Phase 1's
     layout CI check).
   - MR defaults, field enums, and any other table that currently lives in
     both Python and C: same pattern. **Python is the source. C gets a
     generated header.**
   - This is the only surgical way to kill P1-7, P2-1 (duplicate
     orbit_defines), and a family of "I added a density code to Python but
     forgot the C header" bugs, without paying the cost of deleting the
     second source of truth.
5. **What stays in C:**
   - `ddr_config_bin.c` (the writer).
   - `ddr_config.h` (struct layout, but its tables become `#include`s of the
     generated header).
   - The `gen_ddr_config` build.
   - `print_offsets.c` is already slated for deletion/consolidation into
     `tools/dump_struct_layout.c` in Phase 1 — that still applies.
6. **What goes away:**
   - The four-way-duplicated tables (step 4).
   - `--orbit-config-use-python` as a user-facing toggle (step 2).
   - `test_binary_match.py` in its current form — replaced by the broader
     `check-c-python-parity` matrix, which is a strict superset.

**Explicit non-deletion list** (kept for the CI validator to build):
`ddr_config.h`, `ddr_config_bin.c`, `ddr_config.h.template`,
`gen_ddr_config` Makefile target, `arise2_config.h`, `mr_config_gen.h`,
`arise2_omc.h`, `orbit_init_gen.h`.

**Retirement criterion:** The C path may be deleted in a future cycle if and
only if (a) the Python path has been production for at least one full silicon
validation cycle with zero Python-vs-C diffs flagged by
`check-c-python-parity`, AND (b) the GPU/MC team confirms they do not need
the C path for their own independent validation. Neither condition holds
today.

### Phase 3: Binary parser cleanup

**Scope:** `gui.py` binary analyzer.
**Deliverable:** No more hand-coded offset tables.

After Phase 0 (which makes the ctypes struct the single authoritative layout)
and Phase 1 (which gates it in CI), the parser becomes:
```python
def analyze_binary_file(path, dram_type, two_channel):
    cls = make_orbit_config_class(dram_type, two_channel)
    cfg = cls()
    with open(path, 'rb') as f:
        f.seek(EMMC_CM4_TIME_TB_SIZE)
        f.readinto(cfg)
    return {name: getattr(cfg, name) for name, _ in cls._fields_}
```

Also:
- Delete the four hardcoded LP4/LP5 × single/dual offset tables in `gui.py`
  (verified at `gui.py:340-500+`). Every value the GUI today reads by offset is
  available as an attribute on the ctypes struct.
- Delete the file-size-based auto-detect at `gui.py:196-244` (P1-2). Require the
  caller to pass `dram_type` and `two_channel` explicitly — the GUI already has
  the dropdown.
- Re-run `test_binary_parse.py` and `test_gui_params.py` after the switch; expect
  both to need minor updates because they currently encode the old offset-table
  assumptions.
- Optionally add a magic-header fallback (P2-9).

### Phase 4: CLI/GUI argument registry

**Scope:** P0-6 (GUI sending undefined flags).
**Deliverable:** GUI form fields and CLI flags are derived from one registry.

Define a single registry:
```python
# orbit_field_registry.py
FIELDS = [
    OrbitField('rank_interleaving', type=int, default=1, choices=[0,1],
               cli_flag='--orbit-rank-interleaving', gui_label='Rank interleaving'),
    OrbitField('num_rank', type=int, default=2, choices=[1,2], ...),
    # ... every orbit_config field
]
```
- `gen_timing_params.parse_args()` iterates this registry and calls
  `parser.add_argument(...)` for each.
- `gui.py` iterates the same registry to emit form fields in the HTML template.
- `gui.py` constructs the JSON override dict by reading form values and matching them
  against the registry (by field name), not hardcoded form-input-name strings.
- A single unit test asserts `argparse` accepts every flag, and the HTML has a matching
  form input for every flag.

This closes P0-6, P1-10, P1-7 and prevents the next "I added a field and forgot to
update the other side" bug.

### Phase 5: Timing calculation unit tests

**Scope:** §2 coverage gap #1. No refactor; just tests.
**Deliverable:** `test_lpddr4_timing.py`, `test_lpddr5_timing.py`.

Each test instantiates `GenTimingParam` with a fixed config and asserts specific output
timing values against a known-good reference table (e.g. JESD209-4 figures for a
specific speed-bin). These tests would catch bugs like P0-1 (mr_rtp), P0-2 (wck_always_on),
and any future arithmetic regression.

At minimum:
- LP4-4266 at tCK=938ps: pin every emitted value in the c_value string.
- LP4-4266 at tCK=1631ps: same.
- LP5-6400 at tCK=314ps: same.
- Variable-tRRD and txsr-as-1st-ed feature-flag combinations.

### Phase 6: Cleanup and delete

- Delete dead debug scripts (P2-2).
- Delete orbit_config variants (P2-3).
- Deduplicate `orbit_defines.py` (P2-1).
- Archive stale plans (P2-10).
- Consolidate trivial test files (P2-11).
- Fix `gui.py` relative path (P2-8).
- Fix `gen_ddr_config` hardcoded include path (P2-7).
- Resolve or delete FIXME comments (P2-4, P2-5).
- Translate Chinese perror strings (P2-6).

---

## 4. Recommended test suite (target state)

Replace the current 22 files with these:

| File | Purpose |
|------|---------|
| `tests/test_timing_lpddr4.py` | Pinned LP4 timing calculations (unit tests) |
| `tests/test_timing_lpddr5.py` | Pinned LP5 timing calculations (unit tests) |
| `tests/test_struct_layout.py` | Python ctypes vs C offsetof (Phase 1 harness) |
| `tests/test_binary_roundtrip.py` | write orbit_config → read back via ctypes, check equality |
| `tests/test_c_python_binary_match.py` | Existing test_binary_match.py, expanded: all densities, both DRAM types, both channel modes, multiple periods |
| `tests/test_cli_args.py` | Assert gui.html and gen_timing_params flags agree |
| `tests/test_json_override_precedence.py` | After fixing P1-10, whatever precedence order is chosen (recommended: CLI > JSON > struct defaults), test it |
| `tests/test_regression_p0.py` | One case per P0 bug |
| `tests/integration/test_lpddr4.sh` | Current test_lpddr4.sh (keep) |
| `tests/integration/test_lpddr5.sh` | Current test_lpddr5.sh (keep) |

Delete: `test_size.py`, `test_new_size.py`, `test_fixed_size.py`, `test_lpddr5.py`,
`test_checkbox_flow.py` (consolidate), `test_random_value_flow.py` (tautological — its
passing cases aren't testing anything real), `test_gen_lpddr4_bin.sh`,
`test_gen_lpddr5_bin.sh`.

---

## 5. Execution order and risk

| Phase | Dependencies | Risk | Value |
|-------|--------------|------|-------|
| 0 | — | Medium (deletes manual patching, regenerates four reference binaries, fixes 8 bugs) | Very high (stops shipping corrupted binaries, unfreezes `test_binary_match.py`) |
| 1 | 0 | Low (pure additive CI check; Phase 0 already removed the corruption; adds vendor sync workflow) | High (structurally prevents future layout drift, makes `arise2_omc.h` provenance bisectable) |
| 2 | 1 | Low–Medium (Python becomes primary; C path retained as CI validator, not deleted; table duplication removed via codegen) | High (kills P1-7 / P2-1 table duplication, adds `check-c-python-parity` gate, preserves second source of truth) |
| 3 | 1 | Low | High (GUI becomes maintainable) |
| 4 | 0 | Low | High (audience is DRAM integrators per §7 Q4 — full registry, validation, and structured failure reporting; closes P0-6, P1-7, P1-9, P1-10 structurally) |
| 5 | 0 | Low | High (actual correctness coverage) |
| 6 | — | Low | Low individually, medium in aggregate |

**Suggested ordering:** 0 → 1 (lock the layout + vendor sync) → 5 (catch future
arithmetic regressions) → 3 → 4 → 2 → 6.

Phase 0 is bigger than it looks: it deletes the manual-patch corruption *and*
regenerates four reference binaries. Expect one commit per (P0-1..P0-8) bug plus
one standalone commit for the patch-deletion + reference regeneration, in that
order, so each step is independently revertable if a downstream consumer turns
out to depend on the old corrupted bytes. The regeneration commit is gated on
§7 Open Question 3.

Phase 2 is deliberately ordered late, but its **intent has changed from the
original plan**: it no longer deletes the C path. It freezes the C path as a
CI-only validator and focuses on removing table duplication. That drops its
risk from Medium to Low–Medium and makes it independently revertable — the
C build target is preserved throughout.

---

## 6. Non-goals

- **Feature additions — for this cycle only.** Phases 0–6 are pure bug-fix +
  structural cleanup. No new timing options, no new DRAM types, no new GUI
  features are permitted inside these phases, because mixing feature work with
  a corruption fix makes the fix unbisectable. A post-refactor feature roadmap
  is documented in §8; any feature on that list must wait until at least
  Phase 0 + Phase 1 + Phase 2 have landed and stabilized.
- **Deletion of the C path.** The original plan proposed deleting
  `gen_ddr_config` + `ddr_config_bin.c` in Phase 2. That intent has been
  reversed — see revised Phase 2. The C path is retained as a CI-only second
  source of truth and is the single cheapest regression net against future
  P0-5-class bugs. Only table duplication is removed.
- **Performance.** The tool runs once at build time; no optimization is
  needed.
- **API compatibility for the `--orbit-config-use-python` flag.** It will
  become the default in Phase 2 and disappear one release later, with
  deprecation warning.

---

## 7. Open questions for the user

Each question has a **recommended default** — the answer I will proceed with
absent a reply from the user — plus the specific action items it triggers, and
whether it blocks any phase from landing. Questions 1 and 4 do not block; 2
blocks the final form of Phase 1's vendor sync script; 3 blocks the Phase 0
reference-binary regeneration commit.

---

**Q1. Is the C path depended on by any downstream production build script
outside this repo?**

- **Recommended default:** Assume yes *somewhere*, and don't delete it. Phase 2
  has been rewritten to freeze the C path as a CI-only validator rather than
  remove it, so even if the downstream audit turns up nothing this cycle, the
  cost of keeping it is the CI time to build + diff, which is cheap.
- **Action items (landing regardless of the answer):**
  - Run a code search for `gen_ddr_config`, `ddr_config_bin`, and the four
    `.ref.bin` filenames across the wider org.
  - Document every caller found in `docs/c_path_consumers.md` so the next
    cycle's retirement criterion (Phase 2, end) can be evaluated.
- **Blocks:** Nothing in Phases 0–6. If the answer comes back as "yes, three
  downstream consumers", that only raises the bar for the eventual retirement
  of the C path — it does not change any Phase 0–6 work.

---

**Q2. Is `arise2_omc.h` a frozen vendored snapshot, or is it meant to be
re-synced from the upstream GPU repo?**

- **Recommended default:** Treat it as vendored-with-sync. Every DDR driver
  tool I've seen that depends on an upstream GPU/MC header ends up needing a
  sync workflow, because the struct drifts and someone eventually edits the
  vendored copy in place to "just fix one field" and destroys provenance.
- **Action items (landing regardless of the answer):**
  - Add the `SOURCE:` marker comment block to `arise2_omc.h` (Phase 1 step 5).
    Until the upstream path is confirmed, stub the SHA field with
    `UNCONFIRMED`.
  - Add `scripts/sync_omc_header.sh` with a placeholder upstream path.
  - Add `tests/test_omc_header_marker.sh` — the CI rule that fails if the
    header content changes without the SHA field changing. This catches
    hand-edits independent of whether the upstream path is known.
- **Blocks:** Only the final "put the real upstream path in
  `sync_omc_header.sh`" step. Everything else in Phase 1 lands before the
  answer arrives and is useful on its own.

---

**Q3. The committed reference binaries contain the P0-5 corruption. Is any
downstream consumer comparing against these exact bytes today?**

- **Recommended default:** Assume at least one consumer exists (test fixture
  in a sibling repo, SoC team's expected-output check, etc.) and do the
  coordination work before committing regenerated binaries. It's cheap
  insurance; a silent 20-byte diff in a production timing table is expensive
  to diagnose.
- **Action items (already in Phase 0 step 2):**
  - `git log --all -- 'ddr_timing_table.*.ref.bin'` plus an org-wide search
    for the filenames.
  - Tag `refs-pre-p05-corruption-fix` before the regeneration commit.
  - Standalone commit with byte-range diff and bisect breadcrumb.
- **Blocks:** **Yes — this blocks the standalone reference-regeneration
  commit in Phase 0.** All other Phase 0 work (P0-1..P0-4, P0-6..P0-8, and
  the deletion of the manual-patching block itself) can land independently
  of this question; only the commit that updates the four `.bin` files is
  gated. If the answer is delayed, the fix stack can still make forward
  progress — `test_binary_match.py` will stay red until the binaries land,
  but everything else unblocks.

---

**Q4. Is the GUI form meant for end-users (DRAM integrators) or only for the
driver team?**

- **Answer (confirmed by user):** DRAM integrators. **Locked.**
- **Implication for Phase 4 scope:** Full build, not stub. Phase 4 is now
  the single highest-leverage structural phase in the plan for this
  audience:
  - Build the full `orbit_field_registry.py` and derive both the argparse
    parser in `gen_timing_params` and the HTML form in `gui.py` from it.
  - Add per-field validation (ranges, enum membership, type checks).
  - Wire in JEDEC spec floors/ceilings (§8 F2) as registry metadata, so
    integrator-provided values are checked at form-submit time *and* at
    CLI-parse time, with one source of truth.
  - Add structured failure reporting (P1-9) — integrators cannot read
    Python tracebacks in the browser console; errors must be rendered
    inline against the offending field.
  - Every GUI-emitted CLI flag is asserted against `gen_timing_params.parse_args()`
    in a unit test (closes P0-6 structurally, not just the symptom).
- **Blocks:** None — answer is locked, Phase 4 proceeds at full scope.
- **Downstream effect:** §8 F2 (JEDEC validator) and §8 F5 (human-readable
  timing report) are both promoted in priority because their value is
  highest when the user is an integrator who will not read source code to
  diagnose a bad binary. §8 F4 (YAML config) loses its Q4 gate and becomes
  unconditionally on the roadmap.

---

## 8. Feature roadmap (post-refactor, v2)

**Scope:** Features deliberately excluded from Phases 0–6 but worth queuing
for the next cycle. **Prerequisite for all items:** Phase 0 + Phase 1 +
Phase 2 must be landed and stable. No feature on this list is permitted to
mix with the corruption fix, because a feature-shaped change sitting on top
of an in-flight structural fix makes bisection across the corruption boundary
impossible.

These are ordered by `value ÷ cost`, with the cheapest high-value items first.
Items F1–F3 are pure quality investments that should almost certainly happen.
Items F4–F6 depend on audience (§7 Q4) or upstream driver capability. F7 is
CI infrastructure, not a feature, but it belongs in the roadmap because
shipping it alongside the features is how you prevent the next P0-5.

---

**F1. Semantic binary diff.**

- **What:** Extend `compare_bin.py` into a tool that maps byte offsets back
  to ctypes field names via `make_orbit_config_class(dram_type, two_channel)`,
  and prints field-level diffs:
  ```
  phy_base_addr @ 0xCC: 0x80000000 → 0x90000000
  zq_calibration_period @ 0xE4: 0 → 100   (was zeroed by P0-5 manual patch)
  ```
- **Why:** This single tool would have prevented the entire chain of
  "fix LP4/LP5 binary parsing: offset X→Y" commits (`7d74799`, `ddf6a16`,
  `d7e443c`) that were tuning Python to match the P0-5 corruption without
  realizing the ctypes struct was already correct. The diagnostic cost of
  P0-5 was *hours of bisection per commit*; with a semantic diff it would
  have been *one run*.
- **Prerequisite:** Phase 3 (ctypes-driven binary parser). Trivial once the
  parser is unified.
- **Cost:** Small. Maybe 100 lines on top of the existing `compare_bin.py`.
- **Priority:** Highest. Build this immediately after Phase 3 lands.

---

**F2. JEDEC spec floor/ceiling validator.**

- **What:** A `--check-jedec` mode on `gen_timing_params` that verifies every
  emitted timing value is within the JEDEC JESD209-4 (LPDDR4) or JESD209-5
  (LPDDR5) min/max for the chosen speed bin. Example checks:
  `tRCD ≥ JEDEC_min(freq, density)`, `tRP ≥ 18 ns`, `tWR ≥ 18 ns`,
  `tRFC ≥ density_dependent_min`, and so on. Emits one line per violation
  with the field name, the emitted value, the JEDEC floor/ceiling, and the
  spec reference (e.g. `JESD209-4 Table 68`).
- **Why:** DRAM integrators routinely plug in values from untuned datasheets
  or copy values across speed bins without re-checking. A floor/ceiling
  check is the cheapest catch-net you can build and it fits naturally on top
  of the Phase 5 timing unit tests — the JEDEC reference tables Phase 5
  already needs become the source for this validator.
- **Prerequisite:** Phase 5 (timing unit tests against JEDEC reference).
- **Cost:** Medium. The JEDEC min/max tables are a few hundred entries per
  DRAM type, and they don't change often. Most of the effort is the data
  entry, not the code.
- **Priority:** Critical. §7 Q4 is resolved as DRAM integrators, which turns
  this from "nice safety net" into "the single feature most likely to prevent
  a silicon-level timing bug from reaching tape-out". It must be wired into
  Phase 4's registry (as per-field metadata) so violations are caught both
  at form-submit time in the GUI and at CLI-parse time, with the same error
  messages in both places.

---

**F3. Binary header with version + git SHA + DRAM type + channel mode
(multi-entry-aware for F6).**

- **What:** Prepend a 32-byte fixed container header to every generated
  `.bin`, followed by N per-entry sub-headers + payloads. **The schema is
  designed multi-entry from day one** so F6 (frequency-point sweep, now
  mandatory) can land on top of it without a second format break:
  ```
  Container header (32 bytes):
    magic:        4 bytes ("DDRT")
    version:      2 bytes (uint16, bump on any schema change)
    header_size:  2 bytes (uint16, size of this container header, = 32)
    ctypes_hash:  4 bytes (CRC32 of sorted _fields_ tuples — detects layout drift)
    build_sha:    8 bytes (first 8 bytes of gen_timing_params git SHA)
    dram_type:    1 byte  (2=LP4, 3=LP5)
    channels:     1 byte  (0=single, 1=dual)
    num_entries:  2 bytes (uint16, ≥1; =1 for single-frequency, >1 for F6 sweep)
    entry_stride: 4 bytes (uint32, bytes from one entry header to the next)
    reserved:     4 bytes (zero)

  Per-entry (repeated num_entries times):
    entry_header (16 bytes):
      freq_khz:    4 bytes (uint32, 0 if not applicable)
      density_mb:  4 bytes (uint32)
      entry_flags: 2 bytes (uint16, bit0=default_op_point for F6)
      reserved:    6 bytes
    payload:
      orbit_config struct (ctypes payload, already correct after Phase 0)
  ```
  Consumers that want a single entry read `num_entries=1` and skip to the
  first payload. Consumers that support F6 iterate the entry table.
- **Why:** This upgrades P2-9 (no version marker in generated binaries) from
  a code smell to a real feature, solves **P1-2** (GUI analyzer guessing
  DRAM type from file size), *and* provides the framing that F6 needs. The
  GUI reads the container header and picks a dropdown per entry; the CLI
  stamps both the container and the entries; the `check-c-python-parity`
  target verifies the container `ctypes_hash` matches the struct class it
  was built for.
- **Prerequisite:** Phase 0 (reference binaries must be regenerated anyway,
  so the header format change piggybacks on the same compatibility break —
  this is the last free compatibility break the tool gets, which is exactly
  why F3 must land the multi-entry layout now rather than after a second
  break for F6).
- **Driver coordination (required, not gating):** The driver-side consumer
  of the binary must either (a) already skip a fixed prefix, in which case
  we set that prefix to be the container header, or (b) be updated to read
  from offset 0 as container. Open a ticket with the driver team *at the
  start of v2* so their change lands in the same release as F3. Since §7 Q4
  confirmed integrators use the tool, F3 is not optional and this
  coordination must happen — it is not a "build only if confirmed" gate,
  it is a "sequence the driver change and the F3 commit together" gate.
- **Cost:** Medium. The code is small; the coordination is the work.
- **Priority:** High, and **must land before F6** so F6 can write
  multi-entry binaries without re-breaking the format. F3 also subsumes
  part of P1-2's GUI cleanup work, which is an added win.

---

**F4. Unified config input (YAML, schema-validated).**

- **What:** Collapse the three-way input mess (CLI flags + JSON override
  file + GUI form state) into a single YAML schema with layered overrides:
  `defaults.yaml → project.yaml → CLI flags`. Last layer wins. The schema
  is generated from the `orbit_field_registry.py` built in Phase 4 (single
  source of truth).
- **Why:** Today, P1-10 documents that JSON silently overrides every CLI
  flag — i.e. the precedence is undocumented and counter-intuitive. Phase 4
  lands a field registry. YAML is the natural output format for a registry:
  one schema, one validator, one precedence order, one format for
  integrators to hand back as a diff.
- **Prerequisite:** Phase 4 (the registry is the source for the schema).
- **Cost:** Medium. YAML parsing + schema validation is ~200 lines; the work
  is deciding the precedence and migrating existing `orbit_config_template.json`
  callers.
- **Priority:** High. §7 Q4 is resolved as DRAM integrators, and a
  YAML-with-diff workflow is exactly what integrators need to hand a config
  back and forth with the driver team without either side decoding byte
  offsets by hand.

---

**F5. Human-readable timing report alongside the `.bin`.**

- **What:** Dump a sibling `ddr_timing_table.lpddr5.single.report.txt` that
  lists every field with its raw register value, its resolved ns/tCK value,
  its JEDEC check verdict, and the line in `lpddr5_config.py` / `gen_timing_params`
  where the value was computed. Example:
  ```
  tRCD:          18 ns (14 cycles @ 1.28 GHz) [JEDEC min: 18 ns] OK
                 src: gen_timing_params.py:412
  wck_always_on:  1     [period=500ps, from=400, upto=600]       OK
                 src: gen_timing_params.py:155
  ```
- **Why:** Integrators will actually read this. It's how they catch bugs we
  don't catch. It also doubles as a human-readable regression snapshot —
  `diff` two reports across commits and you can see exactly which timings
  changed without decoding bytes.
- **Prerequisite:** Phase 5 (need the unit-tested reference table so the
  JEDEC verdicts are trustworthy) and F2 (the validator provides the
  verdicts).
- **Cost:** Small — a dump loop over the ctypes struct plus a lookup table
  for units.
- **Priority:** High. Strong cost/benefit ratio.

---

**F6. Frequency-point sweep (multi-table output). — Mandatory.**

- **What:** `--freq-points 533,1066,2133,3200` emits a multi-entry binary
  (one orbit_config per frequency point) using the container header
  schema defined in F3. Each frequency point gets its own entry header
  with `freq_khz` populated, and the full timing calculation pipeline is
  rerun per point (not copied or interpolated). One entry is tagged as the
  default operating point via `entry_flags` bit 0.
- **Why:** LPDDR5 platforms in production today run DVFS with multiple
  timing tables per boot. Generating them one at a time via a build script
  is workable but slow and error-prone. **This is a direct user request
  and is committed**, not conditional on further confirmation.
- **Prerequisite:** Phase 2 (the C path must be a stable CI validator so
  the multi-entry binary can be diffed byte-for-byte against the C
  reference via `check-c-python-parity`) AND **F3 must land first** so
  F6 writes into the container format rather than breaking it again.
- **Driver coordination:** The request source (driver team or integrator
  who asked for it) must be recorded in the F6 commit message along with
  the confirmed ingestion format on the driver side — a sequence of
  entries vs. an indexed table vs. per-point separate files. This is
  traceability, not a gate; the request is already confirmed per user
  direction.
- **Cost:** Medium. The writer change is small because F3 already
  landed the container format. The validation matrix
  `(dram_type, channels, freq_point, density)` explodes combinatorially
  and needs CI budget — expect `check-c-python-parity` runtime to grow by
  roughly the average number of frequency points per config.
- **Priority:** Mandatory. This is the one item on the roadmap that is a
  committed user-facing feature. It must land in v2 and it must land
  after F3 (which supplies the container format) but before F5 (so the
  human-readable report can render all entries in one file).
- **Scope boundaries:** F6 covers only the *output format and writer*.
  It does **not** include DVFS policy logic (which frequency point to
  use when), runtime switching primitives (the driver's job), or any
  per-operating-point training data (belongs in the PHY path, not
  orbit_config). If any of these creep into the request, push back and
  keep F6 strictly as "emit N timing tables per invocation".

---

**F7. Golden-reference CI matrix.**

- **What:** After Phase 0 regenerates the four `.ref.bin` files, expand the
  committed golden set to a matrix:
  ```
  (dram_type)  × (channel)  × (freq_bin)      × (density)
  {LP4, LP5}   × {single, dual} × {low, mid, high} × {one per supported code}
  ```
  That's roughly 24–48 golden binaries. Each is byte-compared in CI.
- **Why:** This is the structural replacement for "Phase 0 regression
  test". Four hand-picked references cannot cover the config space; a full
  matrix can. This is what prevents the next P0-5-class bug by turning a
  whole class of "one code path is wrong" bugs into a CI failure at commit
  time.
- **Prerequisite:** Phase 0 (regenerate the initial four) and Phase 2's
  `check-c-python-parity` (which provides the Python↔C oracle used to
  decide whether a new golden is trustworthy).
- **Cost:** Low code, medium CI storage/time. The generation script is a
  one-liner; the ongoing cost is disk + CI minutes.
- **Priority:** High. Not a user-facing feature, but the single biggest
  future-bug-prevention lever.

---

### Will not build (even if asked)

- **LPDDR5X support** without a concrete upstream driver request. Speculative
  DRAM type support is how you end up with three half-finished code paths.
- **A GUI "wizard" mode.** The existing form plus JEDEC validation (F2) plus
  the human-readable report (F5) is enough. A wizard adds surface area
  without closing any real failure mode.
- **Auto-tuning of tCK or margin values.** That work belongs in a silicon
  characterization tool, not a timing-table generator. Mixing them would
  create a tool that is neither a deterministic build artifact nor a
  trustworthy characterization result.
- **A "convert old corrupted .bin to new layout" shim.** The regeneration
  commit in Phase 0 is the one-time migration; anything that makes the old
  corrupted layout reachable after Phase 0 re-introduces the exact failure
  mode Phase 0 was built to eliminate.

---

### Priority summary

| ID | Feature | Priority | Prerequisite | Gate |
|----|---------|----------|--------------|------|
| F1 | Semantic binary diff | Highest | Phase 3 | — |
| F2 | JEDEC spec validator | Critical | Phase 5, wired into Phase 4 registry | — |
| F3 | Binary header (container + per-entry, F6-ready) | High | Phase 0 | Driver-side consumer change sequenced with F3 commit |
| F4 | Unified YAML config | High | Phase 4 | — (Q4 resolved: integrators) |
| F5 | Human-readable timing report (multi-entry-aware) | High | Phase 5, F2, F6 (for per-entry rendering) | — |
| F6 | Frequency-point sweep | **Mandatory** | Phase 2, **F3** | — (committed per user request) |
| F7 | Golden reference CI matrix | High | Phase 0, Phase 2 | — |

**Suggested v2 ordering:** F1 → F7 → F3 → F6 → F2 → F5 → F4.

Rationale for the ordering change (from the previous
`F1 → F7 → F2 → F5 → F3 → F4 → F6`):

- F3 is pulled forward because it is now the foundation F6 lands on, and
  F6 is mandatory. Landing F3 late would force a second binary-format
  compatibility break when F6 arrives — exactly what the multi-entry
  container header was designed to prevent.
- F6 follows F3 immediately. It is the only committed user-facing feature
  on the roadmap and it blocks F5's final form (the human-readable report
  must render all entries, so F5 is moved after F6).
- F2 stays after F6 because the JEDEC validator must check every entry
  in a multi-entry binary, so building it before F6 would mean shipping
  a single-entry-only validator and then retrofitting it.
- F5 is after F2 (so verdicts are available) and after F6 (so it can
  iterate the entries).
- F4 is last because it depends on Phase 4 landing first, and Phase 4 is
  itself gated on several earlier phases.
- F1 and F7 still come first because they are the cheapest
  bug-prevention investments and they make every subsequent feature
  safer to build.
