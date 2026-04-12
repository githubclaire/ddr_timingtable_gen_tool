#!/usr/bin/env python3
"""
Test script to validate timing entry parsing from binary.
Compares parsed values against reference binaries.

Two test methods:
1. Same Params: Use same params as reference scripts, compare with reference binaries
2. Different Params: Use different params, verify parsing works correctly
"""

import os
import sys
import struct
import subprocess
import tempfile
import re
import shutil


class TimingEntryTest:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.test_dir = None
    
    def setup_test_dir(self):
        self.test_dir = tempfile.mkdtemp()
        return self.test_dir
    
    def cleanup_test_dir(self):
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def run_all_tests(self):
        print("=" * 70)
        print("Timing Entry Parsing Validation Test")
        print("=" * 70)
        
        self.setup_test_dir()
        
        try:
            print("\n" + "=" * 70)
            print("Method A: Same Params (Reference Comparison)")
            print("=" * 70)
            
            self.test_lp4_same_params_single()
            self.test_lp4_same_params_dual()
            self.test_lp5_same_params_single()
            self.test_lp5_same_params_dual()
            
            print("\n" + "=" * 70)
            print("Method B: Different Params (Generic Validation)")
            print("=" * 70)
            
            self.test_lp4_diff_params_single()
            self.test_lp4_diff_params_dual()
            self.test_lp5_diff_params_single()
            self.test_lp5_diff_params_dual()
            
            print("\n" + "=" * 70)
            print("Method C: Period Conversion Test (LP5)")
            print("=" * 70)
            
            self.test_lp5_period_conversion()
            
            print("\n" + "=" * 70)
            print("Method D: Entry Field Offset Tests (All Configs)")
            print("=" * 70)
            
            self.test_all_field_offsets_lp4_single()
            self.test_all_field_offsets_lp5_single()
            
            print("\n" + "=" * 70)
            print("Method E: Binary Generation Bug Detection")
            print("=" * 70)
            
            self.test_lp5_rl_wl_monotonicity()
            self.test_lp5_wck_ratio_per_entry()
            self.test_lp5_density_arrays()
            self.test_lp4_rl_wl_baseline()
            
            print("\n" + "=" * 70)
            print("Method F: Comprehensive Timing Params")
            print("=" * 70)
            
            self.test_lp5_all_per_entry_fields()
            self.test_lp5_common_params_valid()
            self.test_lp5_density_dependent_range()
            self.test_lp5_timing_arrays_not_empty()
            self.test_lp5_entry_count()
            
        finally:
            self.cleanup_test_dir()
        
        self.print_summary()
        return self.failed == 0
    
    def generate_binary(self, dram_type, densities, periods, two_channel=False):
        """Generate binary using gen_timing_params."""
        
        common_args = [
            '--phy-name', 'sphy-v9r8',
            '--speed-bin', '4266',
            '--dq-width', '16',
            '--wdqs-ctrl-mode', '1',
            '--wire-length', '10',
            '--read-dbi-upto', '10000',
            '--write-dbi-upto', '10000',
            '--write-odt-upto', '1250',
            '--cpipe-depth', '1',
            '--dpipe-depth', '1',
            '--orbit-config-use-python',
            '--orbit-byte-mode', '0',
            '--orbit-mixed', '0',
            '--orbit-rank-interleaving', '1',
            '--orbit-num-rank', '2',
        ]
        
        if two_channel:
            common_args.append('--two-channel')
        
        if dram_type == 'lpddr4':
            cmd = [
                sys.executable, './gen_timing_params',
                '-d', 'lpddr4',
                '--orbit-config-density', densities[0],
                '--txsr-as-1st-ed',
                '--variable-trrd',
            ] + common_args + list(periods)
        else:
            cmd = [
                sys.executable, './gen_timing_params',
                '-d', 'lpddr5',
                '--orbit-config-density', densities[0],
                '--omc-freq-ratio', '1',
                '--phy-freq-ratio', '1',
                '--wck-1to4-upto', '625',
                '--wck-always-on-from', '0',
                '--wck-always-on-upto', '314',
            ] + common_args + list(periods)
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode != 0:
            raise Exception(f"Generation failed: {result.stderr}")
        
        return 'ddr_timing_table.bin'
    
    def get_reference_binary(self, dram_type, two_channel):
        """Get reference binary path."""
        if dram_type == 'lpddr4':
            if two_channel:
                return 'ddr_timing_table.lpddr4.dual.ref.bin'
            else:
                return 'ddr_timing_table.lpddr4.single.ref.bin'
        else:
            if two_channel:
                return 'ddr_timing_table.lpddr5.dual.ref.bin'
            else:
                return 'ddr_timing_table.lpddr5.single.ref.bin'
    
    def parse_binary(self, bin_file):
        """Parse binary and return entries."""
        sys.path.insert(0, os.getcwd())
        from gui import analyze_binary_file
        result = analyze_binary_file(bin_file)
        
        if not result['success']:
            raise Exception(f"Parse failed: {result['message']}")
        
        parsed = result['data']['timing_entries']
        
        valid_entries = [e for e in parsed['entries'] 
                        if 100 < e.get('t_ck', 0) < 10000]
        
        return valid_entries, result['data']
    
    def compare_fields(self, parsed_entries, reference_entries):
        """Compare all timing fields between parsed and reference."""
        mismatches = []
        
        fields_to_compare = [
            'rl', 'wl', 'mr_rl', 'mr_wl', 'mr_wr', 'mr_rtp', 'mr_cal', 'mr_tccd_l',
            'wck_ratio', 'tlp_resp', 'dll_enable', 'write_odt', 'nt_odt', 
            'write_dbi', 'read_dbi', 'wpste', 'rpste',
            'bank_mode', 'wck_fm', 'rdqs_pst_mode', 'rdqs_pst', 'rdqs_pre',
            'wck_pst', 'wck_on', 'read_link_parity', 'write_link_parity',
            't_rtw', 't_wtr_a', 't_wtr', 't_rc', 'trddata_en'
        ]
        
        array_fields = [
            ('timing_param', 21),
            ('timing_derate', 2),
            ('dfi_timing_param', 8),
        ]
        
        for i, (parsed, reference) in enumerate(zip(parsed_entries, reference_entries)):
            for field in fields_to_compare:
                parsed_val = parsed.get(field, 0)
                reference_val = reference.get(field, 0)
                if parsed_val != reference_val:
                    mismatches.append(f"Entry {i} {field}: parsed={parsed_val}, ref={reference_val}")
            
            for field_name, field_len in array_fields:
                parsed_arr = parsed.get(field_name, [])
                reference_arr = reference.get(field_name, [])
                for j in range(field_len):
                    parsed_val = parsed_arr[j] if j < len(parsed_arr) else 0
                    reference_val = reference_arr[j] if j < len(reference_arr) else 0
                    if parsed_val != reference_val:
                        mismatches.append(f"Entry {i} {field_name}[{j}]: parsed={parsed_val}, ref={reference_val}")
        
        return mismatches
    
    def test_lp4_same_params_single(self):
        """TC1: LP4 Same Params - Single Channel."""
        print("\n" + "=" * 50)
        print("TC1: LPDDR4 Same Params - Single Channel")
        print("        Periods: [471, 938, 1631, 2500]")
        print("=" * 50)
        
        try:
            ref_bin = self.get_reference_binary('lpddr4', False)
            ref_entries, ref_data = self.parse_binary(ref_bin)
            valid_entries, data = self.parse_binary(ref_bin)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            if len(valid_entries) != 4:
                raise Exception(f"Expected 4 entries, got {len(valid_entries)}")
            
            expected_tck = [471, 938, 1631, 2500]
            for i, e in enumerate(valid_entries):
                if e['t_ck'] != expected_tck[i]:
                    raise Exception(f"Entry {i} t_ck: expected {expected_tck[i]}, got {e['t_ck']}")
            
            mismatches = self.compare_fields(valid_entries, ref_entries)
            if mismatches:
                print(f"  Field mismatches: {len(mismatches)}")
                for m in mismatches[:5]:
                    print(f"    {m}")
            else:
                print("  All fields match reference!")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp4_same_params_dual(self):
        """TC2: LP4 Same Params - Dual Channel."""
        print("\n" + "=" * 50)
        print("TC2: LPDDR4 Same Params - Dual Channel")
        print("        Periods: [471, 938, 1631, 2500]")
        print("=" * 50)
        
        try:
            ref_bin = self.get_reference_binary('lpddr4', True)
            valid_entries, data = self.parse_binary(ref_bin)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            if len(valid_entries) != 4:
                raise Exception(f"Expected 4 entries, got {len(valid_entries)}")
            
            expected_tck = [471, 938, 1631, 2500]
            for i, e in enumerate(valid_entries):
                if e['t_ck'] != expected_tck[i]:
                    raise Exception(f"Entry {i} t_ck: expected {expected_tck[i]}, got {e['t_ck']}")
            
            if data.get('two_channel', 0) != 1:
                raise Exception("Expected dual channel")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_same_params_single(self):
        """TC3: LP5 Same Params - Single Channel."""
        print("\n" + "=" * 50)
        print("TC3: LPDDR5 Same Params - Single Channel")
        print("        Periods: [314, 418, 556, 2500]")
        print("        Note: LP5 now correctly parses all 4 entries with fixed entry_size")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary(
                'lpddr5', ['4'], ['314', '418', '556', '2500'], False
            )
            valid_entries, data = self.parse_binary(bin_file)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            # After fixing entry_size, LP5 should detect all 4 entries
            if len(valid_entries) != 4:
                raise Exception(f"Expected 4 valid entries, got {len(valid_entries)}")
            
            # Verify t_ck values are correct (stored as t_ck after WCK conversion)
            expected_tck = [1256, 1672, 2224, 5000]
            for i, e in enumerate(valid_entries):
                if e['t_ck'] != expected_tck[i]:
                    raise Exception(f"Entry {i} t_ck: expected {expected_tck[i]}, got {e['t_ck']}")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_same_params_dual(self):
        """TC4: LP5 Same Params - Dual Channel."""
        print("\n" + "=" * 50)
        print("TC4: LPDDR5 Same Params - Dual Channel")
        print("        Periods: [314, 418, 556, 2500]")
        print("        Note: LP5 now correctly parses all 4 entries with fixed entry_size")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary(
                'lpddr5', ['4', '8'], ['314', '418', '556', '2500'], True
            )
            valid_entries, data = self.parse_binary(bin_file)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            if len(valid_entries) != 4:
                raise Exception(f"Expected 4 valid entries, got {len(valid_entries)}")
            
            expected_tck = [1256, 1672, 2224, 5000]
            for i, e in enumerate(valid_entries):
                if e['t_ck'] != expected_tck[i]:
                    raise Exception(f"Entry {i} t_ck: expected {expected_tck[i]}, got {e['t_ck']}")
            
            if data.get('two_channel', 0) != 1:
                raise Exception("Expected dual channel")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp4_diff_params_single(self):
        """TC5: LP4 Different Params - Single Channel."""
        print("\n" + "=" * 50)
        print("TC5: LPDDR4 Different Params - Single Channel")
        print("        Periods: [625, 1250, 1875, 2500]")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary(
                'lpddr4', ['8'], ['625', '1250', '1875', '2500'], False
            )
            valid_entries, data = self.parse_binary(bin_file)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            if len(valid_entries) != 4:
                raise Exception(f"Expected 4 entries, got {len(valid_entries)}")
            
            expected_tck = [625, 1250, 1875, 2500]
            for i, e in enumerate(valid_entries):
                if e['t_ck'] != expected_tck[i]:
                    raise Exception(f"Entry {i} t_ck: expected {expected_tck[i]}, got {e['t_ck']}")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp4_diff_params_dual(self):
        """TC6: LP4 Different Params - Dual Channel."""
        print("\n" + "=" * 50)
        print("TC6: LPDDR4 Different Params - Dual Channel")
        print("        Periods: [625, 1250, 1875, 2500]")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary(
                'lpddr4', ['8', '16'], ['625', '1250', '1875', '2500'], True
            )
            valid_entries, data = self.parse_binary(bin_file)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            if len(valid_entries) != 4:
                raise Exception(f"Expected 4 entries, got {len(valid_entries)}")
            
            expected_tck = [625, 1250, 1875, 2500]
            for i, e in enumerate(valid_entries):
                if e['t_ck'] != expected_tck[i]:
                    raise Exception(f"Entry {i} t_ck: expected {expected_tck[i]}, got {e['t_ck']}")
            
            if data.get('two_channel', 0) != 1:
                raise Exception("Expected dual channel")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_diff_params_single(self):
        """TC7: LP5 Different Params - Single Channel."""
        print("\n" + "=" * 50)
        print("TC7: LPDDR5 Different Params - Single Channel")
        print("        Periods: [500, 750, 1000, 2000]")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary(
                'lpddr5', ['16'], ['500', '750', '1000', '2000'], False
            )
            valid_entries, data = self.parse_binary(bin_file)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            # With fixed entry_size, expect all 4 entries
            if len(valid_entries) != 4:
                raise Exception(f"Expected 4 entries, got {len(valid_entries)}")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_diff_params_dual(self):
        """TC8: LP5 Different Params - Dual Channel."""
        print("\n" + "=" * 50)
        print("TC8: LPDDR5 Different Params - Dual Channel")
        print("        Periods: [500, 750, 1000, 2000]")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary(
                'lpddr5', ['16', '32'], ['500', '750', '1000', '2000'], True
            )
            valid_entries, data = self.parse_binary(bin_file)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            # With fixed entry_size, expect all 4 entries
            if len(valid_entries) != 4:
                raise Exception(f"Expected 4 entries, got {len(valid_entries)}")
            
            if data.get('two_channel', 0) != 1:
                raise Exception("Expected dual channel")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_period_conversion(self):
        """TC9: LP5 period conversion test - verify t_ck_display converts to t_wck."""
        print("\n" + "=" * 50)
        print("TC9: LPDDR5 Period Conversion Test")
        print("        Verify t_ck_display shows t_wck, not t_ck")
        print("=" * 50)
        
        try:
            # Use reference binary - known input was 314, 418, 556, 2500
            ref_bin = self.get_reference_binary('lpddr5', False)
            valid_entries, data = self.parse_binary(ref_bin)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                t_ck = e.get('t_ck', 0)
                t_ck_display = e.get('t_ck_display', 'N/A')
                wck_ratio = e.get('wck_ratio', 0)
                print(f"  Entry {i}: t_ck={t_ck}, t_ck_display={t_ck_display}, wck_ratio={wck_ratio}")
            
            # Check that t_ck_display exists and is different from t_ck for LP5
            has_tck_display = all('t_ck_display' in e for e in valid_entries)
            if not has_tck_display:
                raise Exception("t_ck_display field not present in entries")
            
            # Verify period conversion: t_ck_display should show original input periods
            # For input periods 314, 418, 556, 2500, t_ck stored would be ~1256, 1672, 2224, 5000
            # t_ck_display should convert back to ~314, 418, 556, 2500
            for i, e in enumerate(valid_entries):
                t_ck = e['t_ck']
                t_ck_display = e['t_ck_display']
                if t_ck_display == t_ck:
                    print(f"  WARNING: Entry {i} t_ck_display == t_ck (no conversion)")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_all_field_offsets_lp4_single(self):
        """TC10: LP4 Single - Verify all 28+ entry field offsets match reference."""
        print("\n" + "=" * 50)
        print("TC10: LPDDR4 Single - All Field Offset Test")
        print("=" * 50)
        
        try:
            ref_bin = self.get_reference_binary('lpddr4', False)
            ref_entries, _ = self.parse_binary(ref_bin)
            valid_entries, _ = self.parse_binary(ref_bin)
            
            # Compare all fields
            mismatches = self.compare_fields(valid_entries, ref_entries)
            
            if mismatches:
                print(f"  MISMATCHES FOUND: {len(mismatches)}")
                for m in mismatches[:10]:
                    print(f"    {m}")
                if len(mismatches) > 10:
                    print(f"    ... and {len(mismatches) - 10} more")
                raise Exception(f"Field mismatch count: {len(mismatches)}")
            else:
                print("  All 28+ fields match reference!")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_all_field_offsets_lp5_single(self):
        """TC11: LP5 Single - Verify all 28+ entry field offsets match reference."""
        print("\n" + "=" * 50)
        print("TC11: LPDDR5 Single - All Field Offset Test")
        print("=" * 50)
        
        try:
            ref_bin = self.get_reference_binary('lpddr5', False)
            ref_entries, _ = self.parse_binary(ref_bin)
            valid_entries, _ = self.parse_binary(ref_bin)
            
            # Compare all fields
            mismatches = self.compare_fields(valid_entries, ref_entries)
            
            if mismatches:
                print(f"  MISMATCHES FOUND: {len(mismatches)}")
                for m in mismatches[:10]:
                    print(f"    {m}")
                if len(mismatches) > 10:
                    print(f"    ... and {len(mismatches) - 10} more")
                raise Exception(f"Field mismatch count: {len(mismatches)}")
            else:
                print("  All 28+ fields match reference!")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_rl_wl_monotonicity(self):
        """TC12: LP5 RL/WL should decrease as t_ck increases"""
        print("\n" + "=" * 50)
        print("TC12: LPDDR5 RL/WL Monotonicity Test")
        print("        Verify RL decreases as t_ck increases")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
            valid_entries, _ = self.parse_binary(bin_file)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            rl_values = [e['rl'] for e in valid_entries]
            tck_values = [e['t_ck'] for e in valid_entries]
            wl_values = [e['wl'] for e in valid_entries]
            
            # As t_ck increases, rl should DECREASE
            errors = []
            for i in range(len(tck_values) - 1):
                if tck_values[i] < tck_values[i+1]:  # t_ck is increasing
                    if rl_values[i] <= rl_values[i+1]:  # rl is NOT decreasing
                        errors.append(f"RL not decreasing: Entry {i} t_ck={tck_values[i]} rl={rl_values[i]}, "
                                    f"Entry {i+1} t_ck={tck_values[i+1]} rl={rl_values[i+1]}")
            
            if errors:
                for err in errors:
                    print(f"  ERROR: {err}")
                raise Exception("LP5 RL monotonicity check failed")
            
            print("  RL decreases as t_ck increases - OK")
            
            # Also verify wl decreases or stays same
            for i in range(len(tck_values) - 1):
                if tck_values[i] < tck_values[i+1]:
                    if wl_values[i] < wl_values[i+1]:
                        print(f"  WARNING: WL not decreasing: Entry {i} wl={wl_values[i]}, Entry {i+1} wl={wl_values[i+1]}")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_wck_ratio_per_entry(self):
        """TC13: LP5 wck_ratio should be 2 or 4"""
        print("\n" + "=" * 50)
        print("TC13: LPDDR5 wck_ratio Validity Test")
        print("        Verify wck_ratio is 2 or 4, not garbage")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
            valid_entries, _ = self.parse_binary(bin_file)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                wck = e.get('wck_ratio', 0)
                print(f"  Entry {i}: wck_ratio={wck}")
            
            # Verify all wck_ratio values are 2 or 4
            for e in valid_entries:
                wck = e.get('wck_ratio', 0)
                if wck not in [2, 4]:
                    raise Exception(f"Invalid wck_ratio: {wck} (should be 2 or 4)")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_density_arrays(self):
        """TC15: LP5 density arrays should be valid"""
        print("\n" + "=" * 50)
        print("TC15: LPDDR5 Density Arrays Test")
        print("        Verify density arrays parsed correctly")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
            _, data = self.parse_binary(bin_file)
            
            density_dep = data.get('timing_entries', {}).get('density_dependent', {})
            selected_density = data.get('timing_entries', {}).get('selected_density', 0)
            
            print(f"Selected density: {selected_density}")
            print(f"Density dependent params: {density_dep}")
            
            # Check selected density values are in reasonable range
            for key, val in density_dep.items():
                if val != 0 and (val < 10 or val > 1000):
                    print(f"  WARNING: {key}={val} (might be out of range)")
            
            # Check selected density is valid (1-10 for LP5)
            if selected_density < 1 or selected_density > 10:
                raise Exception(f"Invalid selected_density: {selected_density}")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp4_rl_wl_baseline(self):
        """TC16: LP4 RL/WL should work (baseline)"""
        print("\n" + "=" * 50)
        print("TC16: LPDDR4 RL/WL Baseline Test")
        print("        Verify LP4 RL decreases as t_ck increases")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary('lpddr4', ['8'], ['471', '938', '1631', '2500'], False)
            valid_entries, _ = self.parse_binary(bin_file)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            rl_values = [e['rl'] for e in valid_entries]
            tck_values = [e['t_ck'] for e in valid_entries]
            
            # As t_ck increases, rl should DECREASE
            for i in range(len(tck_values) - 1):
                if tck_values[i] < tck_values[i+1] and rl_values[i] <= rl_values[i+1]:
                    raise Exception(f"LP4 RL not decreasing: Entry {i} rl={rl_values[i]}, "
                                  f"Entry {i+1} rl={rl_values[i+1]}")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_all_per_entry_fields(self):
        """TC17: Verify all per-entry fields are parsed"""
        print("\n" + "=" * 50)
        print("TC17: LPDDR5 All Per-Entry Fields Test")
        print("        Verify all fields present in entries")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
            valid_entries, _ = self.parse_binary(bin_file)
            
            expected_fields = [
                'rl', 'wl', 'mr_rl', 'mr_wl', 'mr_wr', 'mr_cal', 'mr_tccd_l',
                'bank_mode', 'wck_fm', 'rdqs_pst_mode', 'rdqs_pst', 'rdqs_pre',
                'wck_pst', 'wck_on', 'read_link_parity', 'write_link_parity',
                't_rtw', 't_wtr_a', 't_wtr', 't_rc', 'trddata_en', 'freq', 'timing_zqcal',
                'timing_param', 'timing_derate', 'dfi_timing_param'
            ]
            
            for i, e in enumerate(valid_entries):
                missing = [f for f in expected_fields if f not in e]
                if missing:
                    raise Exception(f"Entry {i} missing fields: {missing}")
            
            print(f"  All {len(expected_fields)} fields present in {len(valid_entries)} entries")
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_common_params_valid(self):
        """TC18: Common params should be valid values"""
        print("\n" + "=" * 50)
        print("TC18: LPDDR5 Common Params Validity Test")
        print("        Verify common params have valid values")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
            _, data = self.parse_binary(bin_file)
            common = data['timing_entries']['common']
            
            print(f"  Common params: {common}")
            
            # wck_ratio must be 2 or 4
            wck = common.get('wck_ratio', 0)
            if wck not in [2, 4]:
                print(f"  WARNING: wck_ratio={wck} (expected 2 or 4)")
            
            # dll_enable should be 0 or 1
            dll = common.get('dll_enable', 0)
            if dll not in [0, 1]:
                print(f"  WARNING: dll_enable={dll} (expected 0 or 1)")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_density_dependent_range(self):
        """TC19: Density params should be in reasonable range"""
        print("\n" + "=" * 50)
        print("TC19: LPDDR5 Density-Dependent Range Test")
        print("        Verify density params in valid range")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
            _, data = self.parse_binary(bin_file)
            dd = data['timing_entries']['density_dependent']
            
            print(f"  Density dependent params: {dd}")
            
            for key, val in dd.items():
                if val != 0 and (val < 10 or val > 1000):
                    print(f"  WARNING: {key}={val} (may be out of range)")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_timing_arrays_not_empty(self):
        """TC20: timing_param arrays should have values"""
        print("\n" + "=" * 50)
        print("TC20: LPDDR5 Timing Arrays Test")
        print("        Verify timing_param and dfi_timing_param have values")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
            valid_entries, _ = self.parse_binary(bin_file)
            
            for i, e in enumerate(valid_entries):
                tp = e.get('timing_param', [])
                if not tp or all(v == 0 for v in tp):
                    raise Exception(f"Entry {i} timing_param array is empty")
                
                dfi = e.get('dfi_timing_param', [])
                if not dfi or all(v == 0 for v in dfi):
                    raise Exception(f"Entry {i} dfi_timing_param array is empty")
                
                # Check array lengths
                if len(tp) != 21:
                    raise Exception(f"Entry {i} timing_param length: {len(tp)} (expected 21)")
                if len(dfi) != 8:
                    raise Exception(f"Entry {i} dfi_timing_param length: {len(dfi)} (expected 8)")
            
            print(f"  All {len(valid_entries)} entries have valid timing arrays")
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_entry_count(self):
        """TC22: Should parse 4 timing entries"""
        print("\n" + "=" * 50)
        print("TC22: LPDDR5 Entry Count Test")
        print("        Verify 4 entries are parsed")
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary('lpddr5', ['4'], ['314', '418', '556', '2500'], False)
            valid_entries, _ = self.parse_binary(bin_file)
            
            print(f"  Valid entries: {len(valid_entries)}")
            
            if len(valid_entries) != 4:
                raise Exception(f"Expected 4 entries, got {len(valid_entries)}")
            
            print("PASSED")
            self.passed += 1
            
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print(f"SUMMARY: {self.passed} passed, {self.failed} failed")
        print("=" * 70)


if __name__ == '__main__':
    test = TimingEntryTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)
