#!/usr/bin/env python3
"""
Test script for DDR Timing Table Generator GUI
- Tests all GUI parameters
- Compares with reference binaries from test_lpddr4.sh/test_lpddr5.sh
"""

import os
import sys
import json
import time
import subprocess
import http.client
import struct

PORT = 5000
BINARY_FILE = 'ddr_timing_table.bin'


def wait_for_server(timeout=10):
    """Wait for GUI server to start."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            conn = http.client.HTTPConnection('localhost', PORT, timeout=2)
            conn.request('GET', '/')
            conn.getresponse()
            return True
        except:
            time.sleep(0.5)
    return False


def generate_binary(params):
    """Generate binary via /generate endpoint."""
    conn = http.client.HTTPConnection('localhost', PORT)
    headers = {'Content-Type': 'application/json'}
    conn.request('POST', '/generate', json.dumps(params), headers)
    resp = conn.getresponse()
    result = json.loads(resp.read().decode())
    conn.close()
    return result


def analyze_binary(file_path, override='auto'):
    """Analyze binary via /analyze endpoint."""
    conn = http.client.HTTPConnection('localhost', PORT)
    headers = {'Content-Type': 'application/json'}
    body = json.dumps({'file_path': file_path, 'dram_type_override': override})
    conn.request('POST', '/analyze', body, headers)
    resp = conn.getresponse()
    result = json.loads(resp.read().decode())
    conn.close()
    return result


def compare_binaries(file1, file2):
    """Compare two binary files byte by byte."""
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        data1 = f1.read()
        data2 = f2.read()
    
    if len(data1) != len(data2):
        return False, f"Size mismatch: {len(data1)} vs {len(data2)}"
    
    mismatches = []
    for i in range(len(data1)):
        if data1[i] != data2[i]:
            mismatches.append(i)
            if len(mismatches) >= 10:
                break
    
    if mismatches:
        return False, f"Mismatches at offsets: {mismatches[:10]}"
    
    return True, "Exact match"


def test_parameters():
    """Test all GUI parameters."""
    print("\n=== Testing GUI Parameters ===")
    
    test_params = [
        # Basic params
        {'dram-type': 'lpddr4', 'dq-width': '16', 'periods': '471 938 1631 2500', 'dram-tck': '471'},
        {'dram-type': 'lpddr5', 'dq-width': '16', 'periods': '314 556 1256 2500', 'dram-tck': '1256'},
        {'dram-type': 'lpddr4', 'dq-width': '32', 'periods': '471 938 1631', 'dram-tck': '471'},
        {'dram-type': 'lpddr5', 'dq-width': '8', 'periods': '314 556 1256', 'dram-tck': '1256'},
        # Pipe params
        {'dram-type': 'lpddr4', 'cpipe-depth': '2', 'dpipe-depth': '2'},
        {'dram-type': 'lpddr5', 'cpipe-depth': '4', 'dpipe-depth': '4'},
        # Timing params
        {'dram-type': 'lpddr4', 'write-odt-upto': '1000'},
        {'dram-type': 'lpddr5', 'write-odt-upto': '8000'},
        # Orbit params
        {'dram-type': 'lpddr4', 'orbit-config-density': '8'},
        {'dram-type': 'lpddr5', 'orbit-config-density': '16'},
    ]
    
    results = []
    for i, params in enumerate(test_params):
        print(f"Test {i+1}/{len(test_params)}: {params.get('dram-type')}, density={params.get('orbit-config-density', 16)}")
        
        # Generate
        gen_result = generate_binary(params)
        if not gen_result.get('success'):
            print(f"  ERROR: {gen_result.get('message')}")
            results.append((i, False, gen_result.get('message')))
            continue
        
        # Analyze
        an_result = analyze_binary(BINARY_FILE)
        if not an_result.get('success'):
            print(f"  ERROR: {an_result.get('message')}")
            results.append((i, False, an_result.get('message')))
            continue
        
        # Compare key values
        analyzed = an_result.get('data', {})
        mismatches = []
        
        if params.get('dram-type') != analyzed.get('basic', {}).get('dram_type'):
            mismatches.append(f"dram_type: {params.get('dram-type')} vs {analyzed.get('basic', {}).get('dram_type')}")
        
        if params.get('orbit-config-density'):
            expected = int(params.get('orbit-config-density'))
            actual = analyzed.get('orbit', {}).get('density', 0)
            if expected != actual:
                mismatches.append(f"density: {expected} vs {actual}")
        
        if mismatches:
            print(f"  MISMATCH: {mismatches}")
            results.append((i, False, str(mismatches)))
        else:
            print(f"  PASS")
            results.append((i, True, "OK"))
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nParameter Tests: {passed}/{len(test_params)} passed")
    return results


def test_reference_binaries():
    """Compare GUI-generated binaries with reference binaries."""
    print("\n=== Testing Reference Binary Comparison ===")
    
    results = []
    
    # Test cases: (ref_file, params, description)
    test_cases = [
        ('ddr_timing_table.lpddr4.single.bin', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'dram-tck': '471',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'wdqs-ctrl-mode': '1',
            'read-dbi-upto': '10000',
            'write-dbi-upto': '10000',
            'write-odt-upto': '1250',
            'txsr-as-1st-ed': 'true',
            'variable-trrd': 'true',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        }, "LPDDR4 single"),
        
        ('ddr_timing_table.lpddr5.single.bin', {
            'dram-type': 'lpddr5',
            'orbit-config-density': '4',
            'periods': '314 556 1256 2500',
            'dram-tck': '1256',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'read-dbi-upto': '10000',
            'write-dbi-upto': '10000',
            'write-odt-upto': '10000',
            'omc-freq-ratio': '1',
            'phy-freq-ratio': '1',
            'wck-1to4-upto': '625',
            'wck-always-on-from': '0',
            'wck-always-on-upto': '314',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        }, "LPDDR5 single"),
    ]
    
    for ref_file, params, desc in test_cases:
        print(f"\nTesting {desc}...")
        
        if not os.path.exists(ref_file):
            print(f"  SKIP: Reference file {ref_file} not found. Run test_lpddr4.sh or test_lpddr5.sh first.")
            results.append((desc, False, "Reference file not found"))
            continue
        
        # Generate binary with GUI
        gen_result = generate_binary(params)
        if not gen_result.get('success'):
            print(f"  ERROR generating: {gen_result.get('message')}")
            results.append((desc, False, gen_result.get('message')))
            continue
        
        # Compare
        match, msg = compare_binaries(BINARY_FILE, ref_file)
        
        if match:
            print(f"  PASS: {msg}")
            results.append((desc, True, "OK"))
        else:
            print(f"  MISMATCH: {msg}")
            results.append((desc, False, msg))
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nReference Tests: {passed}/{len(results)} passed")
    return results


def main():
    print("=== DDR GUI Test Suite ===")
    
    # Check if server is running
    if not wait_for_server():
        print("ERROR: GUI server not responding. Start with: python3 gui.py")
        return 1
    
    print("GUI server is ready")
    
    # Run tests
    param_results = test_parameters()
    ref_results = test_reference_binaries()
    
    # Summary
    print("\n" + "="*50)
    print("=== TEST SUMMARY ===")
    all_ok = True
    
    for i, ok, msg in param_results:
        if not ok:
            print(f"FAIL: Param test {i+1}: {msg}")
            all_ok = False
    
    for desc, ok, msg in ref_results:
        if not ok:
            print(f"FAIL: {desc}: {msg}")
            all_ok = False
    
    if all_ok:
        print("ALL TESTS PASSED")
        return 0
    else:
        print("SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
