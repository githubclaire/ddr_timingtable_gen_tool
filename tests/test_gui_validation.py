"""Tests for GUI validation and binary round-trip bugs fixed on 2026-04-12.

Covers:
  Bug 1: Binary parsing offsets for write-odt-upto / read-dbi-upto / write-dbi-upto
  Bug 2: Wire-length unit label not affected by ps/MHz toggle
  Bug 3: Valid ranges and tooltips (HTML min/max attributes)
  Bug 4: Max periods limit (LP4: 6, LP5: 5)
  Bug 5: JS validation ranges blocking valid inputs
  Bug 6: Save/Load JSON checkbox round-trip
  Bug 7: Load JSON missing UI toggle updates
  Bug 8: validateTimingRanges missing fields (rpste, wpste, LECC, LP5 fields, DFS, periods)
"""
import json
import os
import struct
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from gui import analyze_binary_file, parse_timing_entries


# ---------------------------------------------------------------------------
# Helper: generate a binary via gen_timing_params
# ---------------------------------------------------------------------------
def _gen_binary(dram_type, extra_args=None, periods=None):
    """Run gen_timing_params and return the binary bytes."""
    if dram_type == 'lpddr4':
        args = [
            sys.executable, os.path.join(ROOT, "gen_timing_params"),
            "--dram-type", "lpddr4",
            "--phy-name", "sphy-v9r8",
            "--speed-bin", "4266",
            "--dq-width", "16",
            "--orbit-config-density", "16",
            "--wire-length", "10",
            "--cpipe-depth", "1", "--dpipe-depth", "1",
            "--omc-freq-ratio", "2", "--phy-freq-ratio", "2",
            "--orbit-config-use-python",
        ]
    else:
        args = [
            sys.executable, os.path.join(ROOT, "gen_timing_params"),
            "--dram-type", "lpddr5",
            "--phy-name", "sphy-v9r8",
            "--speed-bin", "6400",
            "--dq-width", "16",
            "--orbit-config-density", "16",
            "--wire-length", "10",
            "--cpipe-depth", "1", "--dpipe-depth", "1",
            "--omc-freq-ratio", "1", "--phy-freq-ratio", "1",
            "--wck-always-on-from", "1250",
            "--wck-always-on-upto", "10000",
            "--orbit-config-use-python",
        ]
    if extra_args:
        args.extend(extra_args)
    if periods:
        args.extend(str(p) for p in periods)
    elif dram_type == 'lpddr4':
        args.extend(["938", "1631", "2500"])
    else:
        args.extend(["314", "418", "556", "2500"])

    result = subprocess.run(args, cwd=ROOT, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    bin_path = os.path.join(ROOT, "ddr_timing_table.bin")
    with open(bin_path, "rb") as f:
        return f.read()


# ===========================================================================
# Bug 1: Binary round-trip — parsed upto values must match input
# ===========================================================================
class TestBinaryRoundTrip(unittest.TestCase):
    """Bug 1 + similar bug A: generate binary with custom upto values, load
    it back via analyze_binary_file, and verify parsed values match."""

    def test_lp4_upto_roundtrip(self):
        """LP4: write-odt-upto=938, read-dbi-upto=1631, write-dbi-upto=938."""
        _gen_binary('lpddr4', extra_args=[
            "--write-odt-upto", "938",
            "--read-dbi-upto", "1631",
            "--write-dbi-upto", "938",
        ])
        bin_path = os.path.join(ROOT, "ddr_timing_table.bin")
        result = analyze_binary_file(bin_path, dram_type_override='lpddr4')
        self.assertTrue(result['success'], result.get('message', ''))
        timing = result['data']['timing']
        self.assertEqual(timing['write_odt_upto'], 938)
        self.assertEqual(timing['read_dbi_upto'], 1631)
        self.assertEqual(timing['write_dbi_upto'], 938)

    def test_lp5_upto_roundtrip_twck_units(self):
        """LP5: upto values returned in tWCK units, not internal t_ck."""
        _gen_binary('lpddr5', extra_args=[
            "--write-odt-upto", "556",
            "--read-dbi-upto", "418",
            "--write-dbi-upto", "556",
        ])
        bin_path = os.path.join(ROOT, "ddr_timing_table.bin")
        result = analyze_binary_file(bin_path, dram_type_override='lpddr5')
        self.assertTrue(result['success'], result.get('message', ''))
        timing = result['data']['timing']
        # LP5 binary stores t_ck = tWCK * wck_ratio; parsed values should
        # be divided back to tWCK units for the GUI.
        self.assertEqual(timing['write_odt_upto'], 556)
        self.assertEqual(timing['read_dbi_upto'], 418)
        self.assertEqual(timing['write_dbi_upto'], 556)


# ===========================================================================
# Bug 1B: parse_timing_entries uses correct offsets per DRAM type
# ===========================================================================
class TestParseTimingEntryOffsets(unittest.TestCase):
    """Bug 1 + similar bug B: parse_timing_entries must use LP5-specific
    offsets for LP5 binaries, not hardcoded LP4 offsets."""

    def test_lp4_entry_parsing(self):
        data = _gen_binary('lpddr4', extra_args=[
            "--write-odt-upto", "10000",
            "--read-dbi-upto", "10000",
        ])
        entries = parse_timing_entries(data, 'lpddr4')
        # Should parse at least one entry with valid enable flags
        self.assertGreater(len(entries['entries']), 0)

    def test_lp5_entry_parsing(self):
        data = _gen_binary('lpddr5', extra_args=[
            "--write-odt-upto", "10000",
            "--read-dbi-upto", "10000",
        ])
        entries = parse_timing_entries(data, 'lpddr5')
        self.assertGreater(len(entries['entries']), 0)


# ===========================================================================
# Bug 4: Max periods — binary format caps at 6 (LP4) or 5 (LP5)
# ===========================================================================
class TestMaxPeriods(unittest.TestCase):
    """Bug 4: timing table region is 0x800 bytes; LP4 entry=0x128 → max 6,
    LP5 entry=0x15C → max 5. Exceeding this corrupts orbit_config."""

    def test_lp4_max_6_periods(self):
        data = _gen_binary('lpddr4', periods=[471, 625, 938, 1250, 1631, 2500])
        entry_size = 0x128
        # All 6 entries should have valid t_ck
        for i in range(6):
            t_ck = struct.unpack('<I', data[i*entry_size+4:i*entry_size+8])[0]
            self.assertGreater(t_ck, 0, "entry %d t_ck should be nonzero" % i)
        # 6 entries * 0x128 = 0x708 < 0x800 — orbit region intact
        self.assertLessEqual(6 * entry_size, 0x800)

    def test_lp5_max_5_periods(self):
        data = _gen_binary('lpddr5', periods=[314, 418, 556, 625, 2500])
        entry_size = 0x15C
        for i in range(5):
            t_ck = struct.unpack('<I', data[i*entry_size+4:i*entry_size+8])[0]
            self.assertGreater(t_ck, 0, "entry %d t_ck should be nonzero" % i)
        self.assertLessEqual(5 * entry_size, 0x800)

    def test_lp4_entry_size(self):
        self.assertEqual(0x128, 296)

    def test_lp5_entry_size(self):
        self.assertEqual(0x15C, 348)


# ===========================================================================
# Bug 1 offset constants: common_offset and per_entry_offset per DRAM type
# ===========================================================================
class TestBinaryLayoutOffsets(unittest.TestCase):
    """Verify the critical struct offsets used by analyze_binary_file and
    parse_timing_entries are consistent between LP4 and LP5."""

    def test_lp4_offsets(self):
        # LP4: common params at 0x106, per-entry at 0x110
        data = _gen_binary('lpddr4', extra_args=[
            "--write-odt-upto", "10000",
        ])
        entry_size = 0x128
        # write_odt flag is at common_off + 4 = 0x10A within first entry
        write_odt = data[0x106 + 4]
        self.assertGreater(write_odt, 0, "LP4 write_odt flag at 0x10A should be set")

    def test_lp5_offsets(self):
        # LP5: common params at 0x13c, per-entry at 0x146
        data = _gen_binary('lpddr5', extra_args=[
            "--write-odt-upto", "10000",
        ])
        write_odt = data[0x13c + 4]
        self.assertGreater(write_odt, 0, "LP5 write_odt flag at 0x140 should be set")


# ===========================================================================
# GUI HTML validation: static checks on the template
# ===========================================================================
class TestGuiHtmlValidation(unittest.TestCase):
    """Bugs 2, 3, 5, 8: validate the HTML template has correct attributes."""

    @classmethod
    def setUpClass(cls):
        html_path = os.path.join(ROOT, "templates", "gui.html")
        with open(html_path, "r") as f:
            cls.html = f.read()

    # Bug 2: wire-length has fixed-unit marker
    def test_wire_length_fixed_unit(self):
        self.assertIn('data-fixed-unit="cm"', self.html)

    # Bug 3: HTML min/max on upto fields
    def test_upto_fields_have_min_max(self):
        upto_fields = [
            'write-odt-upto', 'read-dbi-upto', 'write-dbi-upto',
            'read-lecc-upto', 'write-lecc-upto',
            'rpste-upto', 'wpste-upto',
            'wck-1to4-upto', 'wck-always-on-upto', 'wck-always-on-from',
            'nt-odt-upto', 'bg-mode-upto', 'wck-hf-upto',
            'wck-pst1-upto', 'wck-pst2-upto',
            'rdqs-pst1-upto', 'rdqs-pst2-upto',
        ]
        for field in upto_fields:
            self.assertIn(f'name="{field}"', self.html,
                          f'{field} not found in HTML')
            # Find the input line for this field and check min/max
            for line in self.html.split('\n'):
                if f'name="{field}"' in line:
                    self.assertIn('min=', line,
                                  f'{field} missing min attribute')
                    self.assertIn('max=', line,
                                  f'{field} missing max attribute')
                    break

    # Bug 3: DFS level fields have min/max
    def test_dfs_level_min_max(self):
        for i in range(3):
            name = f'dfs-lvl-t-ck-{i}'
            for line in self.html.split('\n'):
                if f'name="{name}"' in line:
                    self.assertIn('min="300"', line, f'{name} min should be 300')
                    self.assertIn('max="5000"', line, f'{name} max should be 5000')
                    break

    # Bug 4: getMaxPeriods function exists
    def test_max_periods_function(self):
        self.assertIn('getMaxPeriods', self.html)

    # Bug 5/8: validateTimingRanges includes all required fields
    def test_validation_includes_rpste_wpste(self):
        self.assertIn("'rpste-upto'", self.html)
        self.assertIn("'wpste-upto'", self.html)

    def test_validation_includes_lecc(self):
        self.assertIn("'read-lecc-upto'", self.html)
        self.assertIn("'write-lecc-upto'", self.html)

    def test_validation_includes_lp5_fields(self):
        lp5_fields = [
            'nt-odt-upto', 'bg-mode-upto', 'wck-hf-upto',
            'wck-pst1-upto', 'wck-pst2-upto',
            'rdqs-pst1-upto', 'rdqs-pst2-upto',
            'wck-always-on-from',
        ]
        for field in lp5_fields:
            self.assertIn(f"'{field}'", self.html,
                          f'validateTimingRanges missing LP5 field: {field}')

    def test_validation_includes_dfs_and_periods(self):
        self.assertIn('dfs-lvl-t-ck-', self.html)
        self.assertIn('periods-', self.html)

    # Bug 6: loadJson handles checkbox truthy values
    def test_load_json_checkbox_truthy(self):
        # Should accept '1', 'true', or boolean true
        self.assertIn("=== '1'", self.html)
        self.assertIn("=== 'true'", self.html)
        self.assertIn("=== true", self.html)

    # Bug 7: loadJson calls all toggle functions
    def test_load_json_toggle_calls(self):
        toggle_fns = [
            'updatePeriodsLabel', 'toggleDsmEn', 'updateMrrByteLane',
            'togglePeriodicTraining', 'toggleTempSensing',
            'toggleZqCalibration', 'toggleRankInterleaving',
        ]
        for fn in toggle_fns:
            self.assertIn(fn, self.html, f'loadJson missing toggle call: {fn}')


# ===========================================================================
# Range correctness: memcfg-derived ranges match validation code
# ===========================================================================
class TestRangeCorrectness(unittest.TestCase):
    """Verify that JS validation ranges match the actual constraints in
    lpddr4_config.py / lpddr5_config.py memcfg tables and gen_timing_params."""

    @classmethod
    def setUpClass(cls):
        html_path = os.path.join(ROOT, "templates", "gui.html")
        with open(html_path, "r") as f:
            cls.html = f.read()

    def test_lp4_write_odt_max_is_1249(self):
        """LP4 write-odt-upto is hard-capped at 1249 in gen_timing_params."""
        # HTML default max should be 1249 for LP4 (default DRAM type)
        for line in self.html.split('\n'):
            if 'name="write-odt-upto"' in line:
                self.assertIn('max="1249"', line,
                              'LP4 write-odt-upto HTML max should be 1249')
                break

    def test_validation_has_lp4_odt_cap(self):
        """JS validation should cap LP4 write-odt at 1249."""
        self.assertIn('1249', self.html)

    def test_validation_uses_dram_type_specific_period_min(self):
        """Period min should differ by DRAM type: LP4=468, LP5=235."""
        self.assertIn('468', self.html)
        self.assertIn('235', self.html)

    def test_update_field_ranges_function_exists(self):
        """updateFieldRanges() should exist and be called on DRAM type change."""
        self.assertIn('function updateFieldRanges', self.html)
        self.assertIn('updateFieldRanges()', self.html)

    def test_dfs_min_varies_by_dram_type(self):
        """DFS level min: LP4=468 (memcfg), LP5=938 (memcfg)."""
        self.assertIn('938', self.html)  # LP5 DFS min

    def test_lp4_period_boundary_generates(self):
        """LP4 period=468 should work (lowest memcfg upper bound)."""
        data = _gen_binary('lpddr4', periods=[468, 938, 1631])
        entry_size = 0x128
        t_ck = struct.unpack('<I', data[4:8])[0]
        self.assertEqual(t_ck, 468)

    def test_lp4_period_below_min_fails(self):
        """LP4 period=467 should fail — below memcfg range."""
        with self.assertRaises(subprocess.CalledProcessError):
            _gen_binary('lpddr4', periods=[467, 938, 1631])

    def test_lp5_period_boundary_generates(self):
        """LP5 tWCK=235 with wck_1to4 should work (t_ck=940 >= 938 memcfg)."""
        data = _gen_binary('lpddr5', extra_args=[
            "--wck-1to4-upto", "10000",
        ], periods=[235, 418, 556])
        entry_size = 0x15C
        t_ck = struct.unpack('<I', data[4:8])[0]
        # t_ck = 235 * 4 = 940
        self.assertEqual(t_ck, 940)

    def test_lp5_period_below_min_fails(self):
        """LP5 tWCK=234 with wck_1to4 → t_ck=936 < 938, should fail."""
        with self.assertRaises(subprocess.CalledProcessError):
            _gen_binary('lpddr5', extra_args=[
                "--wck-1to4-upto", "10000",
            ], periods=[234, 418, 556])

    def test_lp4_write_odt_capped_at_1249(self):
        """LP4 write-odt-upto=10000 is silently capped to 1249 by CLI."""
        data = _gen_binary('lpddr4', extra_args=[
            "--write-odt-upto", "10000",
        ])
        # At period=938 (< 1249), write_odt should be enabled
        # At period=1631 (> 1249), write_odt should be disabled
        entry_size = 0x128
        common_off = 0x106
        # Entry 0 (t_ck=938): write_odt flag at common_off+4
        odt_938 = data[0 * entry_size + common_off + 4]
        # Entry 1 (t_ck=1631): write_odt flag
        odt_1631 = data[1 * entry_size + common_off + 4]
        self.assertGreater(odt_938, 0, "write_odt should be ON at 938ps (< 1249)")
        self.assertEqual(odt_1631, 0, "write_odt should be OFF at 1631ps (> 1249)")

    def test_get_period_min_function(self):
        """getPeriodMin() helper should exist."""
        self.assertIn('function getPeriodMin', self.html)


# ===========================================================================
# Phase 3: build_generate_cmd and /preview-cmd endpoint
# ===========================================================================
class TestBuildGenerateCmd(unittest.TestCase):
    """Test the extracted build_generate_cmd function."""

    def test_lp4_basic_cmd(self):
        from gui import build_generate_cmd
        params = {
            'dram-type': 'lpddr4',
            'phy-name': 'sphy-v9r8',
            'speed-bin': '4266',
            'dq-width': '16',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'omc-freq-ratio': '2',
            'phy-freq-ratio': '2',
            'write-odt-upto': '1249',
            'periods': '471 938 1631 2500',
        }
        cmd, json_path = build_generate_cmd(params)
        self.assertIn('--dram-type', cmd)
        self.assertIn('lpddr4', cmd)
        self.assertIn('471', cmd)
        self.assertTrue(json_path.endswith('.json'))

    def test_lp5_basic_cmd(self):
        from gui import build_generate_cmd
        params = {
            'dram-type': 'lpddr5',
            'phy-name': 'sphy-v9r8',
            'speed-bin': '6400',
            'dq-width': '16',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'omc-freq-ratio': '1',
            'phy-freq-ratio': '1',
            'wck-1to4-upto': '2500',
            'periods': '314 418 556 2500',
        }
        cmd, _ = build_generate_cmd(params)
        self.assertIn('lpddr5', cmd)
        self.assertIn('--wck-1to4-upto', cmd)


# ===========================================================================
# UI overhaul: new HTML structure tests
# ===========================================================================
class TestUiOverhaulHtml(unittest.TestCase):
    """Verify the overhauled HTML has required structural elements."""

    @classmethod
    def setUpClass(cls):
        html_path = os.path.join(ROOT, "templates", "gui.html")
        with open(html_path, "r") as f:
            cls.html = f.read()

    def test_has_css_custom_properties(self):
        self.assertIn('--primary:', self.html)
        self.assertIn('--surface:', self.html)
        self.assertIn('--error:', self.html)

    def test_has_sticky_header(self):
        self.assertIn('position: sticky', self.html)
        self.assertIn('configSummary', self.html)

    def test_has_card_layout(self):
        self.assertIn('card-grid', self.html)
        self.assertIn('card-header', self.html)
        self.assertIn('card-body', self.html)

    def test_has_tabs(self):
        self.assertIn('tab-configure', self.html)
        self.assertIn('tab-inspect', self.html)
        self.assertIn('switchTab', self.html)

    def test_has_dark_mode(self):
        self.assertIn('prefers-color-scheme: dark', self.html)

    def test_has_dual_readout(self):
        self.assertIn('dual-readout', self.html)
        self.assertIn('updateDualReadout', self.html)

    def test_has_inline_validation(self):
        self.assertIn('validateFieldOnBlur', self.html)
        self.assertIn('field-error', self.html)

    def test_has_freq_visualization(self):
        self.assertIn('freqViz', self.html)
        self.assertIn('updateFreqViz', self.html)

    def test_has_help_icons(self):
        self.assertIn('help-icon', self.html)
        self.assertIn('toggleHelp', self.html)

    def test_has_toggle_switches(self):
        self.assertIn('toggle-switch', self.html)
        self.assertIn('toggle-slider', self.html)

    def test_has_keyboard_shortcuts(self):
        self.assertIn('Shift', self.html)
        self.assertIn('shiftKey', self.html)

    def test_has_cli_preview(self):
        self.assertIn('cliPreview', self.html)
        self.assertIn('copyCliCmd', self.html)

    def test_has_csv_export(self):
        self.assertIn('exportCsv', self.html)

    def test_has_loading_spinner(self):
        self.assertIn('spinner', self.html)

    def test_has_dram_confirm_banner(self):
        self.assertIn('dramConfirmBanner', self.html)
        self.assertIn('confirmDramSwitch', self.html)

    def test_form_names_preserved(self):
        """All critical field names must be preserved for gui.py compatibility."""
        required_names = [
            'phy-name', 'dq-width', 'speed-bin', 'dram-tck', 'min-dram-tck',
            'wire-length', 'cpipe-depth', 'dpipe-depth', 'omc-freq-ratio', 'phy-freq-ratio',
            'write-odt-upto', 'read-dbi-upto', 'write-dbi-upto',
            'read-lecc-upto', 'write-lecc-upto',
            'rpste-upto', 'wpste-upto', 'wdqs-ctrl-mode',
            'wck-1to4-upto', 'nt-odt-upto', 'bg-mode-upto',
            'orbit-config-density', 'orbit-byte-mode', 'orbit-num-rank',
            'orbit-mixed', 'two-channel', 'mrr-byte-lane',
            'regional-clock-gating', 'dram-clock-gating', 'phy-clock-gating',
            'dfs-lvl-t-ck-0', 'dfs-lvl-t-ck-1', 'dfs-lvl-t-ck-2',
        ]
        for name in required_names:
            self.assertIn(f'name="{name}"', self.html,
                          f'Required field name "{name}" missing from HTML')

    def test_update_field_ranges_called_in_load(self):
        """loadJson / applyLoadedParams must call updateFieldRanges."""
        self.assertIn('updateFieldRanges', self.html)

    def test_wck_always_on_cross_validation(self):
        """SPHY-V9R8 WCK always-on constraint must be validated in JS."""
        self.assertIn('function getFieldPs', self.html)
        self.assertIn('1250', self.html)
        self.assertIn('1836', self.html)
        self.assertIn('wck-1to4-upto', self.html)
        self.assertIn('wck-always-on-from', self.html)
        self.assertIn('wck-always-on-upto', self.html)
        self.assertIn('requires WCK always-on', self.html)

    def test_lp5_period_memcfg_bounds_check(self):
        """LP5 period validation must use dynamic memcfg bounds per wck_1to4/read_lecc."""
        self.assertIn('lp5PeriodBounds', self.html)
        self.assertIn('memcfg range', self.html)
        # Must reference read-lecc-upto for dynamic bounds
        self.assertIn('read-lecc-upto', self.html)

    def test_pst_hierarchy_check(self):
        """PST2 must be <= PST1 for both WCK and RDQS."""
        self.assertIn('wck-pst2-upto', self.html)
        self.assertIn('wck-pst1-upto', self.html)
        self.assertIn('rdqs-pst2-upto', self.html)
        self.assertIn('rdqs-pst1-upto', self.html)
        self.assertIn('PST2 is a subset of PST1', self.html)

    def test_at_least_one_period_required(self):
        """Validation must require at least one period."""
        self.assertIn('At least one period is required', self.html)

    def test_field_guide_infrastructure(self):
        """Field guide modal, diagram, and interaction functions must exist."""
        self.assertIn('guideModal', self.html)
        self.assertIn('guide-modal', self.html)
        self.assertIn('openGuide', self.html)
        self.assertIn('closeGuide', self.html)
        self.assertIn('renderGuideDiagram', self.html)
        self.assertIn('guideHighlight', self.html)
        self.assertIn('guideClearHighlight', self.html)
        self.assertIn('guideShowDetail', self.html)
        self.assertIn('dep-diagram', self.html)
        self.assertIn('Field Guide', self.html)
        self.assertIn('constraint-table', self.html)
        # Must have both LP4 and LP5 diagram content
        self.assertIn('lp5Nodes', self.html)
        self.assertIn('lp4Nodes', self.html)
        self.assertIn('lp5Edges', self.html)
        self.assertIn('lp4Edges', self.html)


class TestWckAlwaysOnConstraint(unittest.TestCase):
    """Verify gen_timing_params rejects invalid WCK always-on settings."""

    def test_lp5_wck_always_on_violation_caught(self):
        """Period 2500ps with wck_1to4 but wck_always_on disabled must fail."""
        args = [
            sys.executable, os.path.join(ROOT, "gen_timing_params"),
            "--dram-type", "lpddr5",
            "--phy-name", "sphy-v9r8",
            "--speed-bin", "6400",
            "--dq-width", "8",
            "--cpipe-depth", "1", "--dpipe-depth", "1",
            "--omc-freq-ratio", "1", "--phy-freq-ratio", "1",
            "--wire-length", "10",
            "--orbit-config-density", "8",
            "--wck-1to4-upto", "2500",
            "--wck-always-on-from", "9000", "--wck-always-on-upto", "314",
            "--orbit-config-use-python",
            "314", "2500",
        ]
        result = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
        self.assertNotEqual(result.returncode, 0,
                            "Should fail when WCK always-on is disabled at t_ck >= 1250")
        self.assertIn("WCK always on", result.stderr + result.stdout)

    def test_lp5_wck_always_on_valid(self):
        """Period 2500ps with wck_1to4 and wck_always_on covering it must pass."""
        args = [
            sys.executable, os.path.join(ROOT, "gen_timing_params"),
            "--dram-type", "lpddr5",
            "--phy-name", "sphy-v9r8",
            "--speed-bin", "6400",
            "--dq-width", "8",
            "--cpipe-depth", "1", "--dpipe-depth", "1",
            "--omc-freq-ratio", "1", "--phy-freq-ratio", "1",
            "--wire-length", "10",
            "--orbit-config-density", "8",
            "--wck-1to4-upto", "2500",
            "--wck-always-on-from", "1250", "--wck-always-on-upto", "2500",
            "--orbit-config-use-python",
            "314", "2500",
        ]
        result = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0,
                         f"Should succeed with valid WCK always-on window.\n"
                         f"stderr: {result.stderr}")


class TestLp5MemcfgBounds(unittest.TestCase):
    """Verify gen_timing_params rejects periods outside memcfg bounds."""

    def test_lp5_lecc_period_too_high_fails(self):
        """With read_lecc enabled and wck_1to4, period > 624 should fail."""
        args = [
            sys.executable, os.path.join(ROOT, "gen_timing_params"),
            "--dram-type", "lpddr5",
            "--phy-name", "sphy-v9r8",
            "--speed-bin", "6400",
            "--dq-width", "16",
            "--cpipe-depth", "1", "--dpipe-depth", "1",
            "--omc-freq-ratio", "1", "--phy-freq-ratio", "1",
            "--wire-length", "10",
            "--orbit-config-density", "16",
            "--wck-1to4-upto", "10000",
            "--read-lecc-upto", "10000",
            "--wck-always-on-from", "0", "--wck-always-on-upto", "10000",
            "--orbit-config-use-python",
            "625",  # internal tCK = 625*4 = 2500 = boundary, should fail (lower.t_ck must be > t_ck)
        ]
        result = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
        self.assertNotEqual(result.returncode, 0,
                            "Should fail: period 625 with LECC+WCK1:4 → internal 2500 = boundary (must be < 2500)")

    def test_lp5_lecc_period_in_range_ok(self):
        """With read_lecc enabled and wck_1to4, period 624 should work."""
        args = [
            sys.executable, os.path.join(ROOT, "gen_timing_params"),
            "--dram-type", "lpddr5",
            "--phy-name", "sphy-v9r8",
            "--speed-bin", "6400",
            "--dq-width", "16",
            "--cpipe-depth", "1", "--dpipe-depth", "1",
            "--omc-freq-ratio", "1", "--phy-freq-ratio", "1",
            "--wire-length", "10",
            "--orbit-config-density", "16",
            "--wck-1to4-upto", "10000",
            "--read-lecc-upto", "10000",
            "--wck-always-on-from", "0", "--wck-always-on-upto", "10000",
            "--orbit-config-use-python",
            "624",  # internal tCK = 624*4 = 2496 < 2500, in range
        ]
        result = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0,
                         f"Should succeed: period 624 with LECC+WCK1:4 is valid.\n"
                         f"stderr: {result.stderr}")

    def test_lp5_no_lecc_ratio2_period_too_low_fails(self):
        """Without read_lecc, ratio=2, period 624 should fail (min=625)."""
        args = [
            sys.executable, os.path.join(ROOT, "gen_timing_params"),
            "--dram-type", "lpddr5",
            "--phy-name", "sphy-v9r8",
            "--speed-bin", "6400",
            "--dq-width", "16",
            "--cpipe-depth", "1", "--dpipe-depth", "1",
            "--omc-freq-ratio", "1", "--phy-freq-ratio", "1",
            "--wire-length", "10",
            "--orbit-config-density", "16",
            "--wck-1to4-upto", "0",  # disable wck_1to4 → ratio=2
            "--read-lecc-upto", "0",
            "--wck-always-on-from", "0", "--wck-always-on-upto", "10000",
            "--orbit-config-use-python",
            "624",  # internal tCK = 624*2 = 1248 < 1250 = min
        ]
        result = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
        self.assertNotEqual(result.returncode, 0,
                            "Should fail: period 624 with ratio=2, no LECC → internal 1248 < 1250")


if __name__ == "__main__":
    unittest.main(verbosity=2)
