# Improvement Plan

## 1. Summary

The codebase already contains strong domain knowledge and a good amount of compatibility testing. The main problem is not missing functionality. The main problem is duplicated knowledge:

- parameter definitions are duplicated across CLI, GUI, JSON override flow, and analyzer
- binary layouts are duplicated across `ctypes`, C headers, and hardcoded parser offsets
- generation logic, file emission, and process orchestration are tightly coupled

The highest-value improvements are the ones that remove duplication and make the binary schema shared instead of copied.

## 2. Prioritized Improvements

| Priority | Area | Current issue | Recommended direction |
| --- | --- | --- | --- |
| P0 | GUI/CLI contract | `gui.py` emits CLI flags such as `--orbit-eye-scan-rd-en`, `--orbit-command-bus-training`, and similar options that `gen_timing_params` does not accept. If those controls are used, generation fails before JSON overrides can help. | Define one shared parameter schema for all orbit-config options. Make the GUI send only supported CLI flags plus one structured override payload. |
| P0 | Hidden global state | `GenTimingParam` methods read module-level `args` in multiple places instead of using only `self.args`. This makes the generator hard to reuse safely outside the script entry point. | Remove module-global `args` access. Pass configuration explicitly and make the generator a pure object/service. |
| P0 | Binary schema duplication | `gui.py` hardcodes orbit-config offsets separately from the `ctypes` schema. The copies have already drifted; for example, LPDDR5 pipe-depth offsets in the analyzer do not match the actual `ctypes` field offsets. | Generate parser metadata from `make_orbit_config_class()` and use it in both write and read paths. Keep one authoritative field map. |
| P0 | Timing serialization path | The timing table is generated as formatted C text, then re-parsed into integers, then packed into bytes. This is hard to reason about and easy to break. | Introduce a typed in-memory `TimingEntry` model and serialize directly from structured data to both C and binary outputs. |
| P1 | Packaging and module boundaries | The repo is script-oriented, with large root-level files and cross-cutting responsibilities inside `gen_timing_params` and `gui.py`. | Split into a small package with modules such as `config_schema`, `timing_generator`, `orbit_generator`, `binary_io`, and `web_ui`. Keep thin CLI/UI wrappers on top. |
| P1 | Output hygiene | Generation writes transient files directly into the repository root: binaries, helper headers, override JSON, and generated C. This makes state implicit and pollutes the worktree. | Use a dedicated output directory or temporary work directory. Keep generated artifacts explicit and isolated. |
| P1 | Test architecture | Many tests are script-style, mutate shared files, and sometimes return booleans instead of asserting. This reduces CI quality and makes failures noisier. | Convert the main regression suite to pytest fixtures and temp directories. Treat shell scripts as smoke tests and move most logic into Python tests. |
| P2 | Legacy file cleanup | The repo still carries Python 2 variants and old debug scripts alongside the active runtime path. | Mark legacy files clearly or move them under `legacy/` or `tools/`. Decide and document the supported runtime version. |
| P2 | GUI code cleanup | `templates/gui.html` contains duplicate function definitions such as `generate()`. The second definition wins, but the duplication increases maintenance risk. | Deduplicate the frontend script and move reusable logic into smaller functions or modules. |
| P2 | Feature-surface clarity | Some UI-visible concepts are only partially implemented or ambiguous, such as multi-density support in the GUI and the relationship between `dq_width` and orbit-config fields. | Document what is timing-table-only vs orbit-config-relevant, then either wire the field through fully or remove it from the affected surface. |

## 3. Recommended Refactoring Sequence

### Phase 1: Stabilize Interfaces

1. Create a shared parameter schema module.
2. Use it to drive:
   - CLI argument registration
   - GUI field mapping
   - JSON override validation
3. Remove unsupported GUI-emitted CLI flags.

### Phase 2: Centralize Binary Knowledge

1. Add a typed orbit-config field map generated from `ctypes`.
2. Replace hardcoded analyzer offsets with that map.
3. Introduce a typed timing-entry model and direct serializers.

### Phase 3: Separate Orchestration from Calculation

1. Move timing calculation into a reusable service layer.
2. Keep `gen_timing_params` as a thin wrapper.
3. Let the GUI call the service layer directly or through a minimal internal API instead of rebuilding a long shell command.

### Phase 4: Modernize Validation

1. Move root-file tests to temp directories.
2. Convert print-and-return tests into assert-driven pytest tests.
3. Add CI jobs for:
   - parser tests
   - Python orbit-config generation
   - GUI endpoint smoke tests

## 4. Concrete Near-Term Wins

If only a few changes can be made soon, the highest-return subset is:

1. Fix the GUI/CLI mismatch for unsupported orbit-config flags.
2. Remove global `args` usage from `gen_timing_params`.
3. Replace analyzer hardcoded offsets with offsets derived from `ctypes`.
4. Stop writing transient override files into the repository root by default.

Those four changes would reduce the largest correctness and maintainability risks without changing the core timing math.

