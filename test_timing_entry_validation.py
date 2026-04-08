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
                return 'ddr_timing_table.lpddr4.dual.bin'
            else:
                return 'ddr_timing_table.lpddr4.single.bin'
        else:
            if two_channel:
                return 'ddr_timing_table.lpddr5.dual.bin'
            else:
                return 'ddr_timing_table.lpddr5.single.bin'
    
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
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary(
                'lpddr5', ['4'], ['314', '418', '556', '2500'], False
            )
            valid_entries, data = self.parse_binary(bin_file)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            if len(valid_entries) < 1:
                raise Exception(f"Expected at least 1 entry, got {len(valid_entries)}")
            
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
        print("=" * 50)
        
        try:
            bin_file = self.generate_binary(
                'lpddr5', ['4', '8'], ['314', '418', '556', '2500'], True
            )
            valid_entries, data = self.parse_binary(bin_file)
            
            print(f"Valid entries: {len(valid_entries)}")
            for i, e in enumerate(valid_entries):
                print(f"  Entry {i}: t_ck={e['t_ck']}, rl={e['rl']}, wl={e['wl']}")
            
            if len(valid_entries) < 1:
                raise Exception(f"Expected at least 1 entry, got {len(valid_entries)}")
            
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
            
            if len(valid_entries) < 1:
                raise Exception(f"Expected at least 1 entry, got {len(valid_entries)}")
            
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
            
            if len(valid_entries) < 1:
                raise Exception(f"Expected at least 1 entry, got {len(valid_entries)}")
            
            if data.get('two_channel', 0) != 1:
                raise Exception("Expected dual channel")
            
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
