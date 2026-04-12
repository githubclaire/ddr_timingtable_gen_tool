# DDR Timing Table Generator — Web UI Overhaul Plan

**Target users:** ODM/OEM application engineers who configure DDR timing parameters  
**Current state:** Functional but utilitarian single-page form (flat sections, raw parameter names, no workflow guidance)  
**Goal:** Professional-grade tool UI that reduces errors, accelerates the configure → generate → verify cycle, and makes the tool approachable for engineers who may not have the JEDEC spec memorized

---

## 1. Design Principles

| Principle | Rationale |
|---|---|
| **Progressive disclosure** | Show only what's relevant — LP4 users never see LP5 fields, advanced orbit config is collapsed by default |
| **Speak the engineer's language** | Replace raw param names (`rpste-upto`) with human labels + param name in secondary text. Show frequency alongside period automatically |
| **Prevent errors, don't just catch them** | Inline validation on blur, visual range indicators, dependent fields auto-disable |
| **Workflow, not just a form** | Guide through: Configure → Generate → Inspect → Export |
| **Zero external dependencies** | Keep the "no internet, Python stdlib" constraint. All CSS/JS stays inline or bundled |

---

## 2. Information Architecture Redesign

### Current structure (accordion sections with subsections):
```
Basic Parameters (DRAM type, PHY name, DQ width, speed bin, periods, min-tck, dram-tck)
Pipe Configuration (cpipe/dpipe depth, omc/phy-freq-ratio, wire-length)
Timing Features (ps/MHz unit toggle, write-odt, read/write-dbi, LP5-only LECC fields)
LPDDR4 Options (wdqs-ctrl-mode, rpste/wpste-upto, variable-trrd, txsr)
LPDDR5 Options (wck-1to4, wck-always-on, nt-odt, bg-mode, wck-hf, pst/rdqs, enhanced-nt-odt)
Orbit Configuration (8 subsections:
    Basic/Geometry, Mode Control, Training Enable, Power Management,
    Timing Intervals, DFS Timing, Feature Flags, MRR)
[Buttons bar: Save JSON, Load JSON, Load Binary, Generate Binary]
```

### Proposed structure (tabbed workflow + grouped cards):

```
┌─────────────────────────────────────────────────────────┐
│ DDR Timing Table Generator          [LPDDR4 ▼]  [LP4]  │  ← Sticky header with DRAM type as primary control
├─────────────────────────────────────────────────────────┤
│  [Configure]   [Generate & Inspect]                     │  ← Two-tab workflow
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─ PHY & Clock ──────┐  ┌─ Timing Thresholds ───────┐ │
│  │ PHY Name           │  │ ps ◉ / MHz ○    [dual     │ │
│  │ DQ Width           │  │                  readout]  │ │
│  │ Speed Bin          │  │ Write ODT ≤ ___ps          │ │
│  │ dram_t_ck  ___ps   │  │ Read DBI  ≤ ___ps         │ │
│  │ min_t_ck   ___ps   │  │ Write DBI ≤ ___ps         │ │
│  │ Wire Length ___mil  │  │ [LP5: LECC, NT-ODT, ...]  │ │
│  └────────────────────┘  └────────────────────────────┘ │
│                                                         │
│  ┌─ Frequency Plan ──────────────────────────────────┐  │
│  │ Periods (tCK):  [471] [938] [1631] [2500]  [+]   │  │
│  │                                                   │  │
│  │ DFS Levels (internal tCK — not tWCK for LP5):     │  │
│  │   [938] [1631] [2500]                             │  │
│  │                            ← visual freq bar →    │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─ Memory Topology ─────┐  ┌─ Power Management ────┐  │
│  │ Density    [16Gb ▼]   │  │ ☑ Regional clk gate   │ │
│  │ Byte Mode  [x16  ▼]   │  │ ☑ DRAM clk gate       │ │
│  │ Ranks      [2    ▼]   │  │ ☐ PHY clk gate        │ │
│  │ Channels   [1ch  ▼]   │  │ ☐ PHY low power       │ │
│  │ Mixed      [No   ▼]   │  │   └ idle threshold: _ │ │
│  └────────────────────────┘  │ ☐ Dynamic power-down  │ │
│                              │ ☐ Dynamic self-refresh│ │
│  ▸ Training Options          └────────────────────────┘ │
│  ▸ Calibration & Refresh                                │
│  ▸ LP4/LP5-Specific Options                             │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ [Save JSON]  [Load JSON]  [Load Binary]          │   │
│  │                           [▶ Generate Binary]    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Key field movements** (vs. current structure):
- Wire Length: moves from Pipe Configuration → PHY & Clock card
- DFS Levels: moves from Orbit Config → DFS Timing → Frequency Plan card
- Density, Byte Mode, Ranks, Channels, Mixed: moves from Orbit Config → Basic/Geometry → Memory Topology card
- Power Management: stays as its own card, extracted from Orbit Config subsection
- Pipe Configuration fields (cpipe/dpipe depth, omc/phy-freq-ratio): auto-set/readonly — collapse into a hidden "Pipe Config" section or fold into PHY & Clock

**Unit labeling for Frequency Plan card:** Periods use tCK (LP4) or tWCK (LP5). DFS levels always use internal tCK, which differs from tWCK for LP5. Must label each sub-group clearly to avoid confusion: "DFS Levels (always internal tCK, even for LP5)".

---

## 3. Existing Bugs to Fix During Overhaul

These bugs exist in the current `gui.html` (1643 lines) and should be fixed as part of the relevant phase:

| Bug | Current behavior | Fix in phase |
|---|---|---|
| **Duplicate `generate()` function** | Two definitions at line 1052 and line 1487 — second shadows the first, first is dead code | Phase 1 (cleanup) |
| **MHz conversion misses periods 4-5** | `generate()` hardcodes `periods-0..3` but LP4 allows 6 periods; extra periods sent as MHz | Phase 2 (dual readout eliminates in-place conversion entirely) |
| **`loadJson()` skips `updateFieldRanges()`** | Loading a config that changes DRAM type leaves HTML min/max attributes stale | Phase 1 (add call) |
| **Binary load `file.path` undefined in web** | Line 869: `this.files[0].path` is Electron-only; standard browsers don't expose it | ~~Phase 3~~ **FIXED** (file path dialog) |

---

## 2.5. Completed Pre-Overhaul Changes

### File Path Dialog for All Four Action Buttons (completed)

All four buttons (Save JSON, Load JSON, Load Binary, Generate Binary) now open a **server-side file path dialog** instead of using browser file pickers or blind downloads:

- **Modal dialog** with text input for file path, directory browser (navigable), and "Remember this path" checkbox (persisted in localStorage per action)
- **Server endpoints added to `gui.py`:**
  - `POST /browse` — lists directory contents with optional file extension filter (`.json`, `.bin`)
  - `POST /save-json` — writes JSON config to a user-specified path
  - `POST /load-json-path` — reads JSON from a user-specified path
  - `POST /generate` — now accepts `output_path` param; copies binary to chosen location after generation
- **Bug fixed:** Binary load no longer relies on `this.files[0].path` (Electron-only). All file I/O now goes through server-side path-based endpoints.
- **Removed:** hidden `<input type="file" id="binFileInput">` element; `loadJson()` no longer creates ephemeral file inputs.

This change is independent of the Phase 1-4 overhaul and should be preserved during restructuring.

---

## 4. Phased Implementation

### Phase 1 — Visual & Layout Foundation

**Files:** `templates/gui.html` (styles + body + script)

> **Note:** Despite being "visual," this phase requires HTML restructuring (moving fields between sections) and minor JS (config summary in header, loadJson bugfix). It is not CSS-only.

1. **Color system & typography**
   - Define CSS custom properties for a cohesive palette:
     - `--primary: #1a56db` (action blue), `--surface: #f9fafb`, `--border: #e5e7eb`
     - `--success: #059669`, `--error: #dc2626`, `--warning: #d97706`
   - Migrate all existing hardcoded colors (`#3498db`, `#2c3e50`, `#27ae60`, etc.) to custom property references
   - Monospace for numeric inputs, system sans-serif for labels
   - Base font 14px, labels 12px, section headers 15px semibold

2. **Card-based layout**
   - Replace accordion `.section` with `.card` — white bg, subtle shadow, 8px radius
   - 2-column responsive grid (`grid-template-columns: repeat(auto-fit, minmax(420px, 1fr))`)
   - Cards for: PHY & Clock, Timing Thresholds, Frequency Plan, Memory Topology, Power Management
   - Collapsible cards for: Training Options, Calibration & Refresh, LP4/LP5-Specific
   - **HTML restructuring:** move Wire Length from Pipe Config section, DFS levels from Orbit Config, etc. (see field movement table in Section 2)

3. **Sticky header bar**
   - DRAM type selector moves to header (always visible)
   - Config summary line: "LPDDR4 · x16 · 2-rank · 4266 MT/s" — requires a small JS function that reads current form values and updates on field change
   - Replaces the plain `<h1>` header

4. **Form field styling**
   - Taller inputs (40px), clear focus ring (2px blue outline)
   - Unit labels inside input field (right-aligned, gray) — already exists, polish it
   - Key boolean toggles (regional-clock-gating, dram-clock-gating, etc.): style as pill toggles using `<label>` wrapper + CSS. Requires wrapping existing `<input type="checkbox">` in a `<label class="toggle">` container — this is HTML+CSS, no behavior change.

5. **Cleanup**
   - Remove duplicate `generate()` function (lines 1052-1142 — dead code shadowed by the second definition at line 1487)
   - Add `updateFieldRanges()` call to `loadJson()` function (after the existing toggle calls, around line 1617)

**Estimated scope:** ~250 lines CSS, ~200 lines HTML restructuring, ~30 lines JS (summary line + bugfix)

---

### Phase 2 — UX Improvements (JS logic + HTML)

**Files:** `templates/gui.html` (script + body)

1. **Dual readout for timing fields**
   - Instead of a global ps/MHz toggle that destructively converts all values in-place, show *both* units simultaneously
   - Primary input stays in ps (canonical), secondary read-only `<span>` shows MHz equivalent
   - Toggling the radio button swaps which is the input vs. the readout (primary unit preference), but the canonical stored value is always ps
   - **Remove:** the existing `handleTimingUnitChange()` in-place conversion logic
   - **Remove:** the MHz→ps conversion block in `generate()` (lines 1504-1552) — no longer needed since the form always holds ps values
   - This eliminates the bug where `generate()` hardcodes `periods-0..3` and misses dynamically added periods 4-5

2. **Inline validation on blur**
   - Current: validation runs only on "Generate" click via `validateForm()` + `validateTimingRanges()`
   - New: validate each field on blur, show red border + tooltip immediately
   - Reuse the range definitions from `validateTimingRanges()` — extract into a shared `FIELD_RANGES` object used by both blur handlers and the Generate-click validation
   - Range indicator bar under numeric inputs (thin colored bar showing where value sits within min..max)

3. **Smart defaults on DRAM type switch**
   - When DRAM type changes, show a confirmation message (styled inline banner, NOT a `window.confirm()` or alert — those block the extension/automation) before resetting fields
   - The existing `onchange` handler (line 105) calls 10+ functions — wrap these in a confirmation flow that lets the user cancel
   - No "JEDEC defaults / conservative / aggressive" presets in this phase — deferred until preset values are defined with engineering input

4. **Frequency plan visualization**
   - Below the periods list, render a simple horizontal bar chart (CSS `width` on colored `<div>` elements) showing the frequency points
   - Mark DFS transition levels on the same bar
   - At-a-glance view of the operating frequency range

5. **Contextual help**
   - Add click-to-expand help icons `(?)` next to field labels
   - **Keep** existing `title` attributes for native tooltip on hover (progressive enhancement)
   - Click `(?)` → expand a help `<div>` below the field with richer text
   - Help text should explain what the parameter does, not just the valid range
   - Example: "Write ODT — On-die termination for write operations. Enable at higher frequencies to improve signal integrity. LP4 spec caps this at 1249ps."

6. **Dependent field visibility**
   - Already partially implemented (hidden fields for thresholds) — extend to:
     - Gray out + disable LP4 fields when LP5 is selected (instead of hiding entire section)
     - Auto-collapse sections that have no user-editable fields (e.g., Pipe Configuration readonly fields)

**Estimated scope:** ~350 lines JS, ~120 lines HTML

---

### Phase 3 — Generate & Inspect Tab

**Files:** `templates/gui.html`, `gui.py`

1. **Split into two views**
   - Tab 1: "Configure" — the form
   - Tab 2: "Generate & Inspect" — output and analysis
   - Tab switching via JS (no page reload), both tabs stay inside the same `<form>` so no state loss
   - The **Generate** button lives in the Configure tab's button bar. The Inspect tab is read-only output — no duplicate Generate button there. Clicking Generate auto-switches to the Inspect tab on success.

2. **Generation panel (Inspect tab)**
   - Show the assembled CLI command (read-only, copyable `<pre>` block) before running
   - "Generate" triggers the generation and lands on the Inspect tab with:
     - Spinner during generation, success/error banner
     - Output log in a styled terminal-like block (dark bg, monospace, using CSS custom properties for dark mode compatibility — no hardcoded colors in innerHTML)

3. **`/preview-cmd` endpoint**
   - New endpoint in `gui.py` that accepts the same POST body as `/generate` but returns only the CLI command string without executing
   - Extracted from the existing command-building logic in the `/generate` handler (not written from scratch)

4. **Binary inspector overhaul**
   - Current: modal (`showAnalysisModal`) with raw tables built via innerHTML string concatenation
   - New: embedded panel (not modal) in the Inspect tab with:
     - **Summary card** at top: file size, DRAM type, channel config, entry count
     - **Timing entries** as a horizontally scrollable comparison table with alternating row colors and sticky first column
     - **Use CSS classes** for all styling (not inline styles) so dark mode in Phase 4 works automatically
     - **Export**: "Copy as CSV" button using `navigator.clipboard.writeText()` for the timing table
   - No diff view in this phase — comparing against previous generation would require a storage mechanism (localStorage or server-side). Deferred to a future phase if needed.

5. **Binary load workflow**
   - ~~Current: file input triggers `analyzeBinaryFile()` which calls `/analyze`, fills GUI form via `fillGuiFromAnalysis()`, AND shows the modal~~ **Partially done:** file path dialog now handles path selection via server-side `/browse` endpoint (no more `this.files[0].path` bug)
   - Remaining: Load binary → auto-switch to Inspect tab → show analysis inline → "Apply to form" button that imports values back into Configure tab (separating inspect from import, so users can review before overwriting their form)

**Estimated scope:** ~250 lines HTML, ~200 lines JS, ~40 lines Python

---

### Phase 4 — Polish & Accessibility

**Files:** `templates/gui.html`

1. **Keyboard navigation**
   - Tab order follows visual layout (set `tabindex` on card containers if needed)
   - **Shift+Enter** in any field triggers "Generate" (not plain Enter — plain Enter should submit the current input or move to the next field, not trigger generation)
   - Escape closes any expanded help panel

2. **Responsive layout**
   - Single-column layout below 768px
   - Touch-friendly input sizes for tablet use in lab environments

3. **Dark mode**
   - CSS media query `prefers-color-scheme: dark` with inverted palette using the custom properties from Phase 1
   - **Prerequisite:** Phase 3's inspector must use CSS classes (not inline styles) — otherwise dynamically generated HTML won't respond to dark mode. Verify this before implementing.
   - Lab engineers often work in dimly-lit environments
   - Test all validation status colors (success green, error red, warning yellow) against both light and dark backgrounds

4. **Status persistence**
   - Remember last-used DRAM type and collapsed/expanded card state in localStorage
   - **Do NOT auto-load previous config** on page load — this tool runs on `localhost:5010` which means multiple projects/configs share the same localStorage origin. Instead, offer a "Restore last config" button that loads from localStorage on explicit click.

5. **Loading states**
   - Skeleton placeholders during binary analysis
   - Disable form during generation to prevent double-submit

**Estimated scope:** ~150 lines CSS, ~100 lines JS

---

## 5. Detailed File Change Map

| File | Phase | Changes |
|---|---|---|
| `templates/gui.html` — `<style>` | 1 | CSS custom properties, card layout, sticky header, input styling, migrate hardcoded colors |
| `templates/gui.html` — `<body>` | 1 | Restructure sections into cards, move fields between sections, add header bar, checkbox toggle wrappers |
| `templates/gui.html` — `<script>` | 1 | Config summary updater, remove duplicate `generate()`, add `updateFieldRanges()` to `loadJson()` |
| `templates/gui.html` — `<script>` | 2 | Dual readout, remove destructive unit conversion, inline validation, freq visualization, help system |
| `templates/gui.html` — `<body>` + `<script>` | 3 | Tab switching, CLI preview, inline inspector (CSS classes not inline styles), binary upload via FormData |
| `templates/gui.html` — `<script>` | 4 | Keyboard nav (Shift+Enter for Generate), localStorage restore button, dark mode |
| `gui.py` | pre-overhaul | **Done:** Added `/browse`, `/save-json`, `/load-json-path` endpoints; `/generate` accepts `output_path` |
| `gui.py` | 3 | Add `/preview-cmd` endpoint (extracted from `/generate` command-building logic) |
| `tests/test_gui_validation.py` | 1 | Update if HTML structure changes break selectors (field `name` attrs preserved) |
| `tests/test_gui_validation.py` | 3 | Add tests for `/preview-cmd` endpoint, verify binary upload path |

---

## 6. What Does NOT Change

- **`gui.py` server architecture** — stays as stdlib `http.server`, no Flask/FastAPI
- **Form field `name` attributes** — all `name="write-odt-upto"` etc. stay identical so `gui.py` parsing is untouched
- **`gen_timing_params` CLI interface** — the GUI is a frontend; the backend binary generation is not in scope
- **Validation rules and ranges** — same min/max constraints from CLAUDE.md. Phase 2 changes *when* validation runs (blur instead of only on Generate-click) but the rules themselves are unchanged.
- **Binary analysis logic** — Python-side parsing stays the same, only the display changes

---

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Large HTML file gets unwieldy (1643 lines currently, will grow) | Hard to maintain | Extract JS into `<script>` blocks by concern (validation, UI, generation) — still inline, but organized with clear section comments |
| Dual readout complicates value handling | Conversion bugs | Keep canonical value always in ps internally; secondary display is computed, never submitted. Remove the existing destructive conversion entirely |
| Moving fields between sections breaks toggle logic | Hidden fields become permanently visible or vice versa | Audit every `toggleDramOptions()`, `toggleDsmEn()`, etc. after restructuring. Use DRAM-type CSS classes on cards rather than per-field style.display |
| Tab switching may lose unsaved form state | Data loss | Both tabs share the same `<form>` — no state loss on tab switch |
| Dark mode color clashes with validation colors | Readability | All dynamic HTML (inspector tables, status messages) must use CSS classes, not inline styles. Test all status colors against both backgrounds |
| Phase 1 field regrouping is larger than expected | Timeline slip | Phase 1 is the foundation — accept that it's the heaviest phase. Don't cut HTML restructuring short or Phase 2-4 build on a bad foundation |

---

## 8. Success Criteria

1. An engineer unfamiliar with the tool can generate a valid LP4 binary in < 2 minutes with zero documentation
2. All validation errors are surfaced before clicking Generate (not after)
3. Switching between LP4 and LP5 is a one-click operation with clear visual feedback
4. The binary inspector is usable without opening a separate hex editor
5. The tool looks professional enough to screenshot into a customer-facing report
6. No existing bugs remain: duplicate generate(), stale field ranges on JSON load, MHz conversion for >4 periods
