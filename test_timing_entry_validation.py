#!/usr/bin/env python3
"""
Test script to validate timing entry parsing from binary.
Compares parsed values against generated C timing table.
"""

import os
import sys
import struct
import subprocess
import tempfile
import re


class TimingEntryTest:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def run_all_tests(self):
        print("=" * 70)
        print("Timing Entry Parsing Validation Test")
        print("=" * 70)
        
        self.test_lp4_single_8gb()
        self.test_lp4_dual_8_16gb()
        self.test_lp5_single_16gb()
        self.test_lp5_dual_16_32gb()
        
        self.print_summary()
        return self.failed == 0
    
    def generate_binary(self, dram_type, densities, periods, two_channel=False):
        if dram_type == 'lpddr4':
            if two_channel:
                bin_file = 'ddr_timing_table.lpddr4.dual.ref.bin'
            else:
                bin_file = 'ddr_timing_table.lpddr4.single.ref.bin'
        else:
            if two_channel:
                bin_file = 'ddr_timing_table.lpddr5.dual.ref.bin'
            else:
                bin_file = 'ddr_timing_table.lpddr5.single.ref.bin'
        
        c_file = 'timing_params.c'
        
        if not os.path.exists(bin_file):
            raise Exception(f"Binary not found: {bin_file}")
        
        return bin_file, c_file
    
    def extract_expected_from_c(self, c_file):
        with open(c_file, 'r') as f:
            content = f.read()
        
        expected_entries = []
        
        # Extract timing_param arrays
        tp_matches = re.findall(r'\.timing_param\s*=\s*\{([^}]+)\}', content)
        
        for i, match in enumerate(tp_matches):
            tp_values = [int(x.strip(), 0) for x in match.split(',')]
            entry = {'entry': i, 'timing_param': tp_values}
            expected_entries.append(entry)
        
        # Extract other fields
        rl_matches = re.findall(r'\.rl\s*=\s*(\d+)', content)
        wl_matches = re.findall(r'\.wl\s*=\s*(\d+)', content)
        freq_matches = re.findall(r'\.freq\s*=\s*(\d+)', content)
        tck_matches = re.findall(r'\.t_ck\s*=\s*(\d+)', content)
        tp_resp_matches = re.findall(r'\.tlp_resp\s*=\s*(\d+)', content)
        derate_matches = re.findall(r'\.timing_derate\s*=\s*\{([^}]+)\}', content)
        dfi_matches = re.findall(r'\.dfi_timing_param\s*=\s*\{([^}]+)\}', content)
        t_rfcab_matches = re.findall(r'\.t_rfcab\s*=\s*\{([^}]+)\}', content)
        
        for i in range(len(expected_entries)):
            if i < len(tck_matches):
                expected_entries[i]['t_ck'] = int(tck_matches[i])
            if i < len(freq_matches):
                expected_entries[i]['freq'] = int(freq_matches[i])
            if i < len(rl_matches):
                expected_entries[i]['rl'] = int(rl_matches[i])
            if i < len(wl_matches):
                expected_entries[i]['wl'] = int(wl_matches[i])
            if i < len(tp_resp_matches):
                expected_entries[i]['tlp_resp'] = int(tp_resp_matches[i])
            
            if i < len(derate_matches):
                derate_vals = [int(x.strip(), 0) for x in derate_matches[i].split(',')]
                expected_entries[i]['timing_derate'] = derate_vals
            else:
                expected_entries[i]['timing_derate'] = [0, 0]
            
            if i < len(dfi_matches):
                dfi_vals = [int(x.strip(), 0) for x in dfi_matches[i].split(',')]
                expected_entries[i]['dfi_timing_param'] = dfi_vals
            else:
                expected_entries[i]['dfi_timing_param'] = [0] * 8
            
            if i < len(t_rfcab_matches):
                rfcab_vals = [int(x.strip(), 0) for x in t_rfcab_matches[i].split(',')]
                expected_entries[i]['t_rfcab'] = rfcab_vals
        
        return expected_entries
    
    def test_lp4_single_8gb(self):
        print("\n" + "="*50)
        print("TC1: LPDDR4 Single Channel - 8Gb")
        print("="*50)
        
        try:
            bin_file, c_file = self.generate_binary(
                dram_type='lpddr4',
                densities=['8'],
                periods=['471', '938', '1631', '2500'],
                two_channel=False
            )
            
            sys.path.insert(0, os.getcwd())
            from gui import analyze_binary_file
            result = analyze_binary_file(bin_file)
            
            if not result['success']:
                print(f"FAILED: {result['message']}")
                self.failed += 1
                return
            
            parsed = result['data']['timing_entries']
            
            valid_entries = [e for e in parsed['entries'] 
                           if e.get('t_ck', 0) > 0 and e.get('t_ck', 10000) < 10000]
            
            print(f"Parsed entries: {len(parsed['entries'])}, valid: {len(valid_entries)}")
            
            self._validate_entry_count(valid_entries, 4)
            self._validate_tck_values(valid_entries, [471, 938, 1631, 2500])
            self._validate_rl_decreasing(valid_entries)
            
            print("PASSED")
            self.passed += 1
                
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1
    
    def test_lp4_dual_8_16gb(self):
        print("\n" + "="*50)
        print("TC2: LPDDR4 Dual Channel - 8/16Gb")
        print("="*50)
        
        try:
            bin_file, c_file = self.generate_binary(
                dram_type='lpddr4',
                densities=['8', '16'],
                periods=['471', '938', '1631', '2500'],
                two_channel=True
            )
            
            sys.path.insert(0, os.getcwd())
            from gui import analyze_binary_file
            result = analyze_binary_file(bin_file)
            
            if not result['success']:
                print(f"FAILED: {result['message']}")
                self.failed += 1
                return
            
            parsed = result['data']['timing_entries']
            
            valid_entries = [e for e in parsed['entries'] 
                           if e.get('t_ck', 0) > 0 and e.get('t_ck', 10000) < 10000]
            
            self._validate_entry_count(valid_entries, 4)
            self._validate_tck_values(valid_entries, [471, 938, 1631, 2500])
            self._validate_rl_decreasing(valid_entries)
            
            if result['data']['two_channel'] != 1:
                raise Exception("Expected dual channel")
            
            print("PASSED")
            self.passed += 1
                
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_single_16gb(self):
        print("\n" + "="*50)
        print("TC3: LPDDR5 Single Channel - 16Gb")
        print("="*50)
        
        try:
            bin_file, c_file = self.generate_binary(
                dram_type='lpddr5',
                densities=['16'],
                periods=['1256', '796', '556', '2500'],
                two_channel=False
            )
            
            sys.path.insert(0, os.getcwd())
            from gui import analyze_binary_file
            result = analyze_binary_file(bin_file)
            
            if not result['success']:
                print(f"FAILED: {result['message']}")
                self.failed += 1
                return
            
            parsed = result['data']['timing_entries']
            
            valid_entries = [e for e in parsed['entries'] 
                           if e.get('t_ck', 0) > 0 and e.get('t_ck', 10000) < 10000]
            
            print(f"Parsed entries: {len(parsed['entries'])}, valid: {len(valid_entries)}")
            
            self._validate_entry_count(valid_entries, 1)
            self._validate_tck_values(valid_entries, [1256])
            self._validate_rl_decreasing(valid_entries)
            
            print("PASSED")
            self.passed += 1
                
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def test_lp5_dual_16_32gb(self):
        print("\n" + "="*50)
        print("TC4: LPDDR5 Dual Channel - 16/32Gb")
        print("="*50)
        
        try:
            bin_file, c_file = self.generate_binary(
                dram_type='lpddr5',
                densities=['16', '32'],
                periods=['1256', '796', '556', '2500'],
                two_channel=True
            )
            
            sys.path.insert(0, os.getcwd())
            from gui import analyze_binary_file
            result = analyze_binary_file(bin_file)
            
            if not result['success']:
                print(f"FAILED: {result['message']}")
                self.failed += 1
                return
            
            parsed = result['data']['timing_entries']
            
            valid_entries = [e for e in parsed['entries'] 
                           if e.get('t_ck', 0) > 0 and e.get('t_ck', 10000) < 10000]
            
            self._validate_entry_count(valid_entries, 1)
            self._validate_tck_values(valid_entries, [1256])
            self._validate_rl_decreasing(valid_entries)
            
            if result['data']['two_channel'] != 1:
                raise Exception("Expected dual channel")
            
            print("PASSED")
            self.passed += 1
                
        except Exception as e:
            print(f"ERROR: {e}")
            self.failed += 1
    
    def _validate_entry_count(self, entries, expected):
        actual = len(entries)
        if actual != expected:
            raise Exception(f"Entry count: expected {expected}, got {actual}")
    
    def _validate_tck_values(self, entries, expected_tck):
        for i, entry in enumerate(entries):
            if entry['t_ck'] != expected_tck[i]:
                raise Exception(f"Entry {i} t_ck: expected {expected_tck[i]}, got {entry['t_ck']}")
    
    def _validate_rl_decreasing(self, entries):
        for i in range(1, len(entries)):
            if entries[i]['rl'] >= entries[i-1]['rl']:
                raise Exception(f"RL not decreasing: entry {i-1}={entries[i-1]['rl']}, entry {i}={entries[i]['rl']}")
    
    def _validate_density(self, timing_entries, expected_density):
        if timing_entries['selected_density'] != expected_density:
            raise Exception(f"Density: expected {expected_density}, got {timing_entries['selected_density']}")
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print(f"SUMMARY: {self.passed} passed, {self.failed} failed")
        print("=" * 70)
        
        if hasattr(self, 'last_tmpdir') and os.path.exists(self.last_tmpdir):
            import shutil
            shutil.rmtree(self.last_tmpdir)


if __name__ == '__main__':
    test = TimingEntryTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)