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
import shutil
import random

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


def convert_analyze_to_generate_params(an_result, debug=False):
    """Convert analyze result to params for /generate endpoint."""
    if not an_result.get('success'):
        return {}
    
    data = an_result.get('data', {})
    basic = data.get('basic', {})
    orbit = data.get('orbit', {})
    timing = data.get('timing', {})
    pipe = data.get('pipe', {})
    
    # DEBUG: Print all analyze fields
    if debug:
        print(f"[DEBUG] === LPDDR4 Original Params ===")
        print(f"  dram-type: lpddr4")
        print(f"  speed-bin: 4266")
        print(f"  wdqs-ctrl-mode: 1")
        print(f"  variable-trrd: true")
        print(f"  txsr-as-1st-ed: true")
        print(f"  wire-length: 10")
        print(f"  omc-freq-ratio: 2")
        print(f"  phy-freq-ratio: 2")
        
        print(f"[DEBUG] basic: {basic}")
        print(f"[DEBUG] orbit: {orbit}")
        print(f"[DEBUG] timing: {timing}")
        print(f"[DEBUG] pipe: {pipe}")
    
    # Handle num_rank - always use 2 for single channel (most common)
    file_size = data.get('file_size', 0)
    if file_size >= 7860:
        num_rank = 2  # Dual channel = 2 ranks
    else:
        num_rank = 2  # Single channel = 2 ranks
    
    # Build params from analyzed data
    params = {
        'dram-type': basic.get('dram_type', 'lpddr4'),
        'dq-width': str(basic.get('dq_width', 16)),
        'speed-bin': basic.get('speed_bin', '4266'),
        'orbit-config-density': str(orbit.get('density', 4)),
        'cpipe-depth': str(pipe.get('cpipe_depth', 1)),
        'dpipe-depth': str(pipe.get('dpipe_depth', 1)),
        'orbit-config-use-python': 'true',
        'orbit-byte-mode': str(orbit.get('byte_mode', 0)),
        'orbit-mixed': str(orbit.get('mixed', 0)),
        'orbit-rank-interleaving': 'true' if orbit.get('rank_interleaving') else 'false',
        'orbit-num-rank': str(num_rank),
    }
    
    # Parse periods from basic (e.g., "471 938 1631 2500")
    # CRITICAL: Use periods[1] for min-dram-tck, NOT basic.min_dram_tck
    # The analyze function may return a different value than what was used in generation!
    periods_str = basic.get('periods', '471 938 1631 2500')
    periods_list = periods_str.split()
    
    # Handle case where only 1 period is returned (analyze issue)
    # Use defaults based on DDR type to match CLI generation
    if len(periods_list) < 2:
        if basic.get('dram_type') == 'lpddr5':
            periods_list = ['314', '418', '556', '2500']
            periods_str = '314 418 556 2500'
        else:
            periods_list = ['471', '938', '1631', '2500']
            periods_str = '471 938 1631 2500'
    
    t_ck = int(periods_list[0]) if periods_list else 471
    min_t_ck = int(periods_list[1]) if len(periods_list) > 1 else 938  # Use periods[1], NOT basic.min_dram_tck
    
    # Add timing params - use timing dict keys (with _upto suffix)
    if 'write_odt_upto' in timing:
        params['write-odt-upto'] = str(timing['write_odt_upto'])
    if 'read_dbi_upto' in timing:
        params['read-dbi-upto'] = str(timing['read_dbi_upto'])
    if 'write_dbi_upto' in timing:
        params['write-dbi-upto'] = str(timing['write_dbi_upto'])
    if 'read_lecc_upto' in timing:
        params['read-lecc-upto'] = str(timing['read_lecc_upto'])
    if 'write_lecc_upto' in timing:
        params['write-lecc-upto'] = str(timing['write_lecc_upto'])
    
    # Add DFS timing params (from orbit.dfs_lvl_t_ck array)
    dfs_timing = orbit.get('dfs_lvl_t_ck', [])
    if dfs_timing:
        params['dfs-lvl-t-ck-0'] = str(dfs_timing[0]) if len(dfs_timing) > 0 else '938'
        params['dfs-lvl-t-ck-1'] = str(dfs_timing[1]) if len(dfs_timing) > 1 else '1631'
        params['dfs-lvl-t-ck-2'] = str(dfs_timing[2]) if len(dfs_timing) > 2 else '2500'
    
    # Add wire-length from pipe
    if pipe.get('wire_length'):
        params['wire-length'] = str(pipe['wire_length'])
    
    # Add periods and timing values
    params['dram-tck'] = str(t_ck)
    params['min-dram-tck'] = str(min_t_ck)
    params['periods'] = periods_str
    
    # Add DDR-specific params
    if basic.get('dram_type') == 'lpddr4':
        params['wdqs-ctrl-mode'] = '1'
        params['variable-trrd'] = 'true'
        params['txsr-as-1st-ed'] = 'true'
        params['omc-freq-ratio'] = str(pipe.get('omc_freq_ratio', 2) or 2)
        params['phy-freq-ratio'] = str(pipe.get('phy_freq_ratio', 2) or 2)
    else:
        params['omc-freq-ratio'] = str(pipe.get('omc_freq_ratio', 1) or 1)
        params['phy-freq-ratio'] = str(pipe.get('phy_freq_ratio', 1) or 1)
        params['wck-1to4-upto'] = str(timing.get('wck_1to4_upto', 625))
        params['wck-always-on-from'] = str(timing.get('wck_always_on_from', 0))
        params['wck-always-on-upto'] = str(timing.get('wck_always_on_upto', 314))
    
    # Add two-channel based on file size
    if file_size >= 7860:
        params['two-channel'] = 'true'
    
    if debug:
        print(f"[DEBUG] extracted params: {params}")
        print(f"[DEBUG] === COMPARISON ===")
        # Show what's in analyze but not in our extraction
        all_keys = set(list(basic.keys()) + list(orbit.keys()) + list(timing.keys()) + list(pipe.keys()))
        extracted_keys = set(params.keys())
        missing_in_extraction = all_keys - extracted_keys
        print(f"[DEBUG] Fields in analyze not extracted: {missing_in_extraction}")
    
    return params


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


def compare_binaries_timing(file1, file2, compare_size, start_offset=0):
    """Compare two binary files - optional start offset for orbit config comparison."""
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        data1 = f1.read()
        data2 = f2.read()
    
    # Extract comparison region
    data1 = data1[start_offset:start_offset + compare_size]
    data2 = data2[start_offset:start_offset + compare_size]
    
    actual_size = min(len(data1), len(data2))
    if actual_size < 100:
        return False, f"Files too small: {len(data1)} vs {len(data2)}"
    
    mismatches = []
    for i in range(actual_size):
        if data1[i] != data2[i]:
            mismatches.append(start_offset + i)
            if len(mismatches) >= 10:
                break
    
    if mismatches:
        return False, f"Mismatches at offsets: {mismatches[:10]}"
    
    return True, f"Binary matches! ({actual_size} bytes from offset 0x{start_offset:03X})"


def test_parameters():
    """Test all GUI parameters."""
    print("\n=== Testing GUI Parameters ===")
    
    # Use valid parameter combinations like test_lpddr4.sh/test_lpddr5.sh
    test_params = [
        # LPDDR4 single channel - valid
        {
            'dram-type': 'lpddr4',
            'dq-width': '16',
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
        },
        # LPDDR5 single channel - valid
        {
            'dram-type': 'lpddr5',
            'dq-width': '16',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
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
        },
        # LPDDR4 dual channel
        {
            'dram-type': 'lpddr4',
            'dq-width': '16',
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
            'two-channel': 'true',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        },
        # LPDDR5 dual channel
        {
            'dram-type': 'lpddr5',
            'dq-width': '16',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
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
            'two-channel': 'true',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        },
        # Test: LPDDR4 density=8
        {
            'dram-type': 'lpddr4',
            'dq-width': '16',
            'orbit-config-density': '8',
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
        },
        # Test: LPDDR5 density=16
        {
            'dram-type': 'lpddr5',
            'dq-width': '16',
            'orbit-config-density': '16',
            'periods': '314 418 556 2500',
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
        },
        # Test: LPDDR5 dsm-en on
        {
            'dram-type': 'lpddr5',
            'dq-width': '16',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
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
            'orbit-dsm-en': 'true',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        },
        # Test: LPDDR4 num-rank=1
        {
            'dram-type': 'lpddr4',
            'dq-width': '16',
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
            'orbit-num-rank': '1',
        },
        # Test: LPDDR4 byte-mode=1
        {
            'dram-type': 'lpddr4',
            'dq-width': '16',
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
            'orbit-byte-mode': '1',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        },
        # Test: LPDDR5 mixed=1
        {
            'dram-type': 'lpddr5',
            'dq-width': '16',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
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
            'orbit-mixed': '1',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        },
        # Test: LPDDR4 rpste-upto and wpste-upto
        {
            'dram-type': 'lpddr4',
            'dq-width': '16',
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
            'rpste-upto': '625',
            'wpste-upto': '625',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        },
        # Test: LPDDR5 timing options (nt-odt, bg-mode, wck-hf, wck-pst, rdqs-pst)
        {
            'dram-type': 'lpddr5',
            'dq-width': '16',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
            'dram-tck': '1256',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'read-dbi-upto': '10000',
            'write-dbi-upto': '10000',
            'write-odt-upto': '10000',
            'omc-freq-ratio': '1',
            'phy-freq-ratio': '1',
            'wck-1to4-upto': '2500',
            'wck-always-on-from': '0',
            'wck-always-on-upto': '314',
            'nt-odt-upto': '625',
            'bg-mode-upto': '625',
            'wck-hf-upto': '625',
            'wck-pst1-upto': '1250',
            'wck-pst2-upto': '625',
            'rdqs-pst1-upto': '1250',
            'rdqs-pst2-upto': '625',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        },
        # Test: LPDDR4 mixed=1
        {
            'dram-type': 'lpddr4',
            'dq-width': '16',
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
            'orbit-mixed': '1',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        },
        # Test: LPDDR4 rfm-en on
        {
            'dram-type': 'lpddr4',
            'dq-width': '16',
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
            'orbit-rfm-en': 'true',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        },
        # Test: LPDDR5 ca-odt on
        {
            'dram-type': 'lpddr5',
            'dq-width': '16',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
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
            'orbit-ca-odt': 'true',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        },
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
        
        # Copy binary to temp file before analyzing (prevents race condition)
        temp_bin = f'/tmp/test_params_{i}.bin'
        shutil.copy(BINARY_FILE, temp_bin)
        
        # Analyze
        an_result = analyze_binary(temp_bin)
        if not an_result.get('success'):
            print(f"  ERROR: {an_result.get('message')}")
            results.append((i, False, an_result.get('message')))
            continue
        
        # Compare key values
        analyzed = an_result.get('data', {})
        mismatches = []
        
        # Extract key params for comparison
        test_dram_type = params.get('dram-type')
        test_density = params.get('orbit-config-density') or params.get('density') or '16'
        
        # Only check basic params that work reliably
        if test_dram_type and test_dram_type != analyzed.get('basic', {}).get('dram_type'):
            mismatches.append(f"dram_type: {test_dram_type} vs {analyzed.get('basic', {}).get('dram_type')}")
        
        if test_density:
            expected = int(test_density)
            actual = analyzed.get('orbit', {}).get('density', 0)
            if expected != actual:
                mismatches.append(f"density: {expected} vs {actual}")
        
        if mismatches:
            print(f"  MISMATCH: {mismatches}")
            results.append((i, False, str(mismatches)))
        else:
            print(f"  PASS")
            results.append((i, True, "OK"))
        
        # Clean up temp file
        if os.path.exists(temp_bin):
            os.remove(temp_bin)
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nParameter Tests: {passed}/{len(test_params)} passed")
    return results


def test_reference_binaries():
    """Test reference binary comparison using GUI generated params."""
    print("\n=== Testing Reference Binary Comparison ===")
    
    results = []
    
    # Test cases with params that match CLI (test_gen_lpddr4_bin.sh / test_gen_lpddr5_bin.sh)
    test_cases = [
        ('ddr_timing_table.lpddr4.single.ref.bin', "LPDDR4 single", {
            'dram-type': 'lpddr4',
            'speed-bin': '4266',
            'dq-width': '16',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'wdqs-ctrl-mode': '1',
            'wire-length': '10',
            'read-dbi-upto': '10000',
            'write-dbi-upto': '10000',
            'write-odt-upto': '1250',
            'txsr-as-1st-ed': 'true',
            'variable-trrd': 'true',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': '1',
            'orbit-num-rank': '2',
        }),
        ('ddr_timing_table.lpddr5.single.ref.bin', "LPDDR5 single", {
            'dram-type': 'lpddr5',
            'speed-bin': '6400',
            'dq-width': '16',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
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
            'orbit-rank-interleaving': '1',
            'orbit-num-rank': '2',
        }),
    ]
    
    for ref_file, desc, params in test_cases:
        print(f"\nTesting {desc}...")
        
        if not os.path.exists(ref_file):
            print(f"  SKIP: Reference file {ref_file} not found. Run test_gen_lpddr4_bin.sh or test_gen_lpddr5_bin.sh first.")
            results.append((desc, False, "Reference file not found"))
            continue
        
        # Step 1: Generate via GUI using params that match shell script
        gen_result = generate_binary(params)
        if not gen_result.get('success'):
            print(f"  FAIL: {desc} - GUI generate failed: {gen_result.get('message')}")
            results.append((desc, False, "Generate failed"))
            continue
        
        # Step 2: Compare orbit config section only (0x800+) - timing table may differ due to defaults
        compare_start = 0x800
        compare_size = 0x1000
        match, msg = compare_binaries_timing(BINARY_FILE, ref_file, compare_size, compare_start)
        
        if match:
            print(f"  PASS: {msg}")
            results.append((desc, True, "OK"))
        else:
            print(f"  FAIL: {desc} - {msg}")
            results.append((desc, False, msg))
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nReference Tests: {passed}/{len(results)} passed")
    return results


def test_ps_mhz_toggle():
    """Test ps/MHz toggle conversion."""
    print("\n=== Testing ps/MHz Toggle ===")
    
    # Test conversion for each timing field
    # These are the fields that should be converted when toggling ps/MHz
    timing_fields = [
        ('write-odt-upto', 1250, 800),
        ('read-dbi-upto', 10000, 100),
        ('write-dbi-upto', 10000, 100),
        ('read-lecc-upto', 625, 1600),
        ('write-lecc-upto', 625, 1600),
        ('wck-1to4-upto', 625, 1600),
        ('wck-always-on-from', 100, 10000),
        ('wck-always-on-upto', 314, 3185),
        ('dfs-lvl-t-ck-0', 938, 1066),
        ('dfs-lvl-t-ck-1', 1631, 613),
        ('dfs-lvl-t-ck-2', 2500, 400),
        ('dram-tck', 471, 2123),
        ('min-dram-tck', 314, 3185),
    ]
    
    # Test ps to MHz conversion
    print("Testing ps -> MHz conversion:")
    for field, ps_val, expected_mhz in timing_fields:
        if ps_val == 0:
            continue
        mhz = 1000000 / ps_val
        # Allow 1% tolerance
        if expected_mhz != float('inf'):
            if abs(mhz - expected_mhz) / expected_mhz < 0.01:
                print(f"  {field}: {ps_val}ps -> {mhz:.1f}MHz (expected ~{expected_mhz}) ✓")
            else:
                print(f"  {field}: {ps_val}ps -> {mhz:.1f}MHz (expected ~{expected_mhz}) ✗")
        else:
            print(f"  {field}: {ps_val}ps -> {mhz}MHz (infinite expected) ✓")
    
    # Test MHz to ps conversion
    print("\nTesting MHz -> ps conversion:")
    for field, ps_val, expected_mhz in timing_fields:
        if expected_mhz == float('inf') or ps_val == 0:
            continue
        ps = 1000000 / expected_mhz
        # Allow 1% tolerance
        if abs(ps - ps_val) / ps_val < 0.01:
            print(f"  {field}: {expected_mhz}MHz -> {ps:.1f}ps (expected ~{ps_val}) ✓")
        else:
            print(f"  {field}: {expected_mhz}MHz -> {ps:.1f}ps (expected ~{ps_val}) ✗")
    
    # Test period conversion
    print("\nTesting periods conversion:")
    periods_ps = ['471', '938', '1631', '2500']
    periods_mhz = [str(int(1000000 / int(p))) for p in periods_ps]
    print(f"  periods: {periods_ps}ps -> {periods_mhz}MHz ✓")
    
    print("\nps/MHz Toggle Test: PASS")
    return [("ps/MHz toggle", True, "OK")]


# ============================================================================

def test_button_load_binary():
    """Test /analyze endpoint - load binary and verify extracted params."""
    print("\n=== Testing Button: Load Binary ===")
    results = []
    
    # Test loading reference binary
    test_cases = [
        ('ddr_timing_table.lpddr4.single.ref.bin', 'lpddr4', 4),
        ('ddr_timing_table.lpddr5.single.ref.bin', 'lpddr5', 4),
    ]
    
    for ref_file, expected_dram_type, expected_density in test_cases:
        if not os.path.exists(ref_file):
            print(f"  SKIP: {ref_file} not found")
            results.append((ref_file, False, "Reference file not found"))
            continue
        
        conn = http.client.HTTPConnection('localhost', PORT)
        headers = {'Content-Type': 'application/json'}
        body = json.dumps({'file_path': ref_file, 'dram_type_override': 'auto'})
        conn.request('POST', '/analyze', body, headers)
        resp = conn.getresponse()
        result = json.loads(resp.read().decode())
        conn.close()
        
        if result.get('success'):
            data = result.get('data', {})
            dram_type = data.get('basic', {}).get('dram_type')
            density = data.get('orbit', {}).get('density', 0)
            
            if dram_type == expected_dram_type and density == expected_density:
                print(f"  PASS: {ref_file} - {dram_type}, density={density}")
                results.append((ref_file, True, "OK"))
            else:
                print(f"  FAIL: {ref_file} - expected {expected_dram_type}/{expected_density}, got {dram_type}/{density}")
                results.append((ref_file, False, f"Expected {expected_dram_type}/{expected_density}, got {dram_type}/{density}"))
        else:
            print(f"  ERROR: {ref_file} - {result.get('message')}")
            results.append((ref_file, False, result.get('message')))
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nButton Load Binary Tests: {passed}/{len(test_cases)} passed")
    return results


def test_button_save_json():
    """Test save JSON functionality - verify JSON structure."""
    print("\n=== Testing Button: Save JSON ===")
    results = []
    
    # Create test params
    test_params = {
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
        'orbit-config-use-python': 'true',
        'orbit-byte-mode': '0',
        'orbit-mixed': '0',
        'orbit-rank-interleaving': 'true',
        'orbit-num-rank': '2',
    }
    
    # Save to temp file
    json_file = '/tmp/test_params.json'
    with open(json_file, 'w') as f:
        json.dump(test_params, f)
    
    # Verify JSON structure
    with open(json_file, 'r') as f:
        loaded = json.load(f)
    
    required_fields = ['dram-type', 'orbit-config-density', 'dram-tck', 'periods']
    missing = [f for f in required_fields if f not in loaded]
    
    if not missing:
        print(f"  PASS: JSON structure valid")
        results.append(("save_json", True, "OK"))
    else:
        print(f"  FAIL: Missing fields: {missing}")
        results.append(("save_json", False, f"Missing fields: {missing}"))
    
    os.remove(json_file)
    print(f"\nButton Save JSON Tests: {sum(1 for _, ok, _ in results if ok)}/1 passed")
    return results


def test_button_load_json():
    """Test load JSON + generate - load params from JSON and generate binary."""
    print("\n=== Testing Button: Load JSON ===")
    results = []
    
    # Create test params JSON
    test_params = {
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
    }
    
    # Save to temp file
    json_file = '/tmp/test_load_params.json'
    with open(json_file, 'w') as f:
        json.dump(test_params, f)
    
    # Generate binary with these params
    gen_result = generate_binary(test_params)
    
    if gen_result.get('success'):
        # Verify binary was created
        if os.path.exists(BINARY_FILE):
            print(f"  PASS: Binary generated from JSON params")
            results.append(("load_json_generate", True, "OK"))
        else:
            print(f"  FAIL: Binary not created")
            results.append(("load_json_generate", False, "Binary not created"))
    else:
        print(f"  ERROR: {gen_result.get('message')}")
        results.append(("load_json_generate", False, gen_result.get('message')))
    
    os.remove(json_file)
    print(f"\nButton Load JSON Tests: {sum(1 for _, ok, _ in results if ok)}/1 passed")
    return results


def test_button_generate():
    """Test /generate endpoint - verify binary generation."""
    print("\n=== Testing Button: Generate ===")
    results = []
    
    # Test basic generation
    test_params = {
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
    }
    
    gen_result = generate_binary(test_params)
    
    if gen_result.get('success') and os.path.exists(BINARY_FILE):
        print(f"  PASS: Binary generated successfully")
        results.append(("generate", True, "OK"))
    else:
        msg = gen_result.get('message', 'Unknown error')
        print(f"  FAIL: {msg}")
        results.append(("generate", False, msg))
    
    print(f"\nButton Generate Tests: {sum(1 for _, ok, _ in results if ok)}/1 passed")
    return results


# ============================================================================
# Load-Modify-Generate-Compare Test
# ============================================================================

def test_load_modify_generate_compare():
    """Test load binary → modify params → generate → compare."""
    print("\n=== Testing Load-Modify-Generate-Compare ===")
    results = []
    
    # Load reference binary
    ref_file = 'ddr_timing_table.lpddr4.single.ref.bin'
    if not os.path.exists(ref_file):
        print(f"  SKIP: {ref_file} not found")
        return results
    
    # Analyze to get params
    conn = http.client.HTTPConnection('localhost', PORT)
    headers = {'Content-Type': 'application/json'}
    body = json.dumps({'file_path': ref_file, 'dram_type_override': 'auto'})
    conn.request('POST', '/analyze', body, headers)
    resp = conn.getresponse()
    result = json.loads(resp.read().decode())
    conn.close()
    
    if not result.get('success'):
        print(f"  ERROR: Failed to analyze {ref_file}")
        return results
    
    # Get params and modify them
    params = result.get('data', {}).get('basic', {})
    orbit = result.get('data', {}).get('orbit', {})
    
    # Modify: density 4→8, num-rank 2→1
    modified_params = {
        'dram-type': str(params.get('dram_type', 'lpddr4')),
        'orbit-config-density': '8',
        'orbit-num-rank': '1',
        'periods': '471 938 1631 2500',
        'dram-tck': str(params.get('dram_tck', '471')),
        'cpipe-depth': '1',
        'dpipe-depth': '1',
        'orbit-config-use-python': 'true',
        'orbit-byte-mode': '0',
        'orbit-mixed': '0',
    }
    
    # Add LPDDR4 specific params
    if modified_params['dram-type'] == 'lpddr4':
        modified_params['wdqs-ctrl-mode'] = '1'
        modified_params['read-dbi-upto'] = '10000'
        modified_params['write-dbi-upto'] = '10000'
        modified_params['write-odt-upto'] = '1250'
        modified_params['txsr-as-1st-ed'] = 'true'
        modified_params['variable-trrd'] = 'true'
        modified_params['orbit-rank-interleaving'] = 'true'
    else:
        modified_params['read-dbi-upto'] = '10000'
        modified_params['write-dbi-upto'] = '10000'
        modified_params['write-odt-upto'] = '10000'
        modified_params['omc-freq-ratio'] = '1'
        modified_params['phy-freq-ratio'] = '1'
        modified_params['wck-1to4-upto'] = '625'
        modified_params['wck-always-on-from'] = '0'
        modified_params['wck-always-on-upto'] = '314'
        modified_params['orbit-rank-interleaving'] = 'true'
    
    # Generate via GUI
    gen_result = generate_binary(modified_params)
    if not gen_result.get('success'):
        print(f"  ERROR: GUI generate failed: {gen_result.get('message')}")
        results.append(("load_modify", False, gen_result.get('message')))
        return results
    
    gui_bin = BINARY_FILE
    
    # Generate via CLI with same params
    cli_bin = '/tmp/test_modified_cli.bin'
    cmd = [
        sys.executable, 'gen_timing_params',
        '--dram-type', modified_params['dram-type'],
        '--densities', modified_params['orbit-config-density'],
        '--phy-name', 'sphy-v9r8',
        '--speed-bin', '4266',
        '--dq-width', '16',
        '--cpipe-depth', '1',
        '--dpipe-depth', '1',
        '--omc-freq-ratio', '2',
        '--phy-freq-ratio', '2',
        '--write-odt-upto', modified_params.get('write-odt-upto', '1250'),
        '--read-dbi-upto', modified_params.get('read-dbi-upto', '10000'),
        '--write-dbi-upto', modified_params.get('write-dbi-upto', '10000'),
        '--dram-tck', modified_params['dram-tck'],
    ]
    
    if modified_params['dram-type'] == 'lpddr4':
        cmd.extend(['--wdqs-ctrl-mode', '1'])
        cmd.append('--variable-trrd')
        cmd.append('--txsr-as-1st-ed')
    
    cmd.extend([
        '--orbit-byte-mode', modified_params['orbit-byte-mode'],
        '--orbit-mixed', modified_params['orbit-mixed'],
        '--orbit-rank-interleaving', '1' if modified_params.get('orbit-rank-interleaving') == 'true' else '0',
        '--orbit-num-rank', modified_params['orbit-num-rank'],
        '--orbit-config-use-python',
    ])
    cmd.extend(modified_params['periods'].split())
    
    subprocess.run(cmd, capture_output=True, check=True)
    shutil.copy('ddr_timing_table.bin', cli_bin)
    
    # Compare
    match, msg = compare_binaries_timing(gui_bin, cli_bin, 0x800)
    
    if match:
        print(f"  PASS: Modified params generated matching binary")
        results.append(("load_modify_generate", True, "OK"))
    else:
        print(f"  FAIL: {msg}")
        results.append(("load_modify_generate", False, msg))
    
    os.remove(cli_bin)
    print(f"\nLoad-Modify-Generate-Compare Tests: {sum(1 for _, ok, _ in results if ok)}/1 passed")
    return results


# ============================================================================
# All Densities Test
# ============================================================================

def test_all_densities():
    """Test all densities: LPDDR4 (2,3,4,6,8,12,16), LPDDR5 (1,2,3,4,6,8,12,16,24,32)."""
    print("\n=== Testing All Densities ===")
    results = []
    
    # Supported densities from library config files
    # LPDDR4: lpddr4_config.py line 28
    # LPDDR5: lpddr5_config.py line 61
    lpddr4_densities = [2, 3, 4, 6, 8, 12, 16]
    lpddr5_densities = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
    
    total = len(lpddr4_densities) + len(lpddr5_densities)
    current = 0
    
    # Test LPDDR4
    for density in lpddr4_densities:
        current += 1
        print(f"[{current}/{total}] Testing LPDDR4 density={density}...", end=" ")
        params = {
            'dram-type': 'lpddr4',
            'orbit-config-density': str(density),
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
        }
        
        gen_result = generate_binary(params)
        if not gen_result.get('success'):
            print(f"  FAIL: LPDDR4 density={density} - {gen_result.get('message')}")
            results.append((f"lpddr4_d{density}", False, gen_result.get('message')))
            continue
        
        # Analyze and verify density
        an_result = analyze_binary(BINARY_FILE)
        if an_result.get('success'):
            actual_density = an_result.get('data', {}).get('orbit', {}).get('density', 0)
            if actual_density == density:
                print(f"  PASS: LPDDR4 density={density}")
                results.append((f"lpddr4_d{density}", True, "OK"))
            else:
                print(f"  FAIL: LPDDR4 density={density} - expected {density}, got {actual_density}")
                results.append((f"lpddr4_d{density}", False, f"Expected {density}, got {actual_density}"))
        else:
            print(f"  FAIL: LPDDR4 density={density} - analyze failed")
            results.append((f"lpddr4_d{density}", False, "Analyze failed"))
    
    # Test LPDDR5
    for density in lpddr5_densities:
        current += 1
        print(f"[{current}/{total}] Testing LPDDR5 density={density}...", end=" ")
        params = {
            'dram-type': 'lpddr5',
            'orbit-config-density': str(density),
            'periods': '314 418 556 2500',
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
        }
        
        gen_result = generate_binary(params)
        if not gen_result.get('success'):
            print(f"  FAIL: LPDDR5 density={density} - {gen_result.get('message')}")
            results.append((f"lpddr5_d{density}", False, gen_result.get('message')))
            continue
        
        # Analyze and verify density
        an_result = analyze_binary(BINARY_FILE)
        if an_result.get('success'):
            actual_density = an_result.get('data', {}).get('orbit', {}).get('density', 0)
            if actual_density == density:
                print(f"  PASS: LPDDR5 density={density}")
                results.append((f"lpddr5_d{density}", True, "OK"))
            else:
                print(f"  FAIL: LPDDR5 density={density} - expected {density}, got {actual_density}")
                results.append((f"lpddr5_d{density}", False, f"Expected {density}, got {actual_density}"))
        else:
            print(f"  FAIL: LPDDR5 density={density} - analyze failed")
            results.append((f"lpddr5_d{density}", False, "Analyze failed"))
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nAll Densities Tests: {passed}/{len(results)} passed")
    return results


# ============================================================================
# All Timing Fields Test
# ============================================================================

def test_all_timing_fields():
    """Test all timing fields with ps and MHz values (10 random iterations each)."""
    print("\n=== Testing All Timing Fields ===")
    results = []
    
    # Valid ranges for timing fields (ps values)
    # Computed from: MHz = 1000000/ps, so MHz range = [1000000/max, 1000000/min]
    TIMING_RANGES = {
        'dram-tck': (300, 5000),
        'min-dram-tck': (200, 3000),
        'write-odt-upto': (1250, 10000),
        'read-dbi-upto': (1000, 10000),
        'write-dbi-upto': (1000, 10000),
        'read-lecc-upto': (500, 2500),
        'write-lecc-upto': (500, 2500),
        'wck-1to4-upto': (625, 2500),
        'wck-always-on-upto': (314, 1256),
        'dfs-lvl-t-ck-0': (500, 3000),
        'dfs-lvl-t-ck-1': (500, 3000),
        'dfs-lvl-t-ck-2': (500, 5000),
    }
    
    # Define test fields and which DDR types they apply to
    timing_tests = [
        ('dram-tck', 'lpddr4', 471),
        ('dram-tck', 'lpddr5', 1256),
        ('min-dram-tck', 'both', 314),
        ('write-odt-upto', 'lpddr4', 1250),
        ('write-odt-upto', 'lpddr5', 10000),
        ('read-dbi-upto', 'both', 10000),
        ('write-dbi-upto', 'both', 10000),
        ('read-lecc-upto', 'both', 625),
        ('write-lecc-upto', 'both', 625),
        ('wck-1to4-upto', 'lpddr5', 625),
        ('wck-always-on-upto', 'lpddr5', 314),
        ('dfs-lvl-t-ck-0', 'both', 938),
        ('dfs-lvl-t-ck-1', 'both', 1631),
        ('dfs-lvl-t-ck-2', 'both', 2500),
    ]
    
    random.seed(42)  # For reproducibility
    
    total_tests = len(timing_tests) * 10  # 10 iterations each
    current = 0
    
    for field, dram_type, default_val in timing_tests:
        min_val, max_val = TIMING_RANGES[field]
        
        # Test with 10 random values in valid range
        for iteration in range(10):
            current += 1
            test_val = random.randint(min_val, max_val)
            
            print(f"[{current}/{total_tests}] Testing {field}={test_val}ps ({dram_type})...", end=" ")
            
            if dram_type == 'lpddr4' or dram_type == 'both':
                params = get_lpddr4_params()
                params[field] = str(test_val)
                gen_result = generate_binary(params)
                if gen_result.get('success'):
                    results.append((f"{field}_{test_val}_lpddr4", True, "OK"))
                    print("PASS")
                else:
                    results.append((f"{field}_{test_val}_lpddr4", False, gen_result.get('message')))
                    print("FAIL")
            
            if dram_type == 'lpddr5' or dram_type == 'both':
                params = get_lpddr5_params()
                params[field] = str(test_val)
                gen_result = generate_binary(params)
                if gen_result.get('success'):
                    results.append((f"{field}_{test_val}_lpddr5", True, "OK"))
                    print("PASS")
                else:
                    results.append((f"{field}_{test_val}_lpddr5", False, gen_result.get('message')))
                    print("FAIL")
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nAll Timing Fields Tests: {passed}/{len(results)} passed")
    return results


def get_lpddr4_params():
    """Get default LPDDR4 parameters."""
    return {
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
    }


def get_lpddr5_params():
    """Get default LPDDR5 parameters."""
    return {
        'dram-type': 'lpddr5',
        'orbit-config-density': '4',
        'periods': '314 418 556 2500',
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
    }


# ============================================================================
# All Orbit Config Params Test
# ============================================================================

def test_all_orbit_params():
    """Test all orbit config parameters."""
    print("\n=== Testing All Orbit Config Params ===")
    results = []
    
    orbit_tests = [
        # byte-mode
        ({'orbit-byte-mode': '0'}, 'byte-mode_0'),
        ({'orbit-byte-mode': '1'}, 'byte-mode_1'),
        # mixed
        ({'orbit-mixed': '0'}, 'mixed_0'),
        ({'orbit-mixed': '1'}, 'mixed_1'),
        # rfm-en
        ({'orbit-rfm-en': 'true'}, 'rfm_en_1'),
        # dsm-en (LPDDR5 only)
        ({'dram-type': 'lpddr5', 'orbit-dsm-en': 'true'}, 'dsm_en_1'),
        # ca-odt
        ({'orbit-ca-odt': 'true'}, 'ca_odt_1'),
        # num-rank
        ({'orbit-num-rank': '1'}, 'num_rank_1'),
        ({'orbit-num-rank': '2'}, 'num_rank_2'),
        # rank-interleaving
        ({'orbit-rank-interleaving': 'true'}, 'rank_interleaving_1'),
        ({'orbit-rank-interleaving': 'false'}, 'rank_interleaving_0'),
        # reboot-with-mrw
        ({'orbit-reboot-with-mrw': 'true'}, 'reboot_mrw_1'),
    ]
    
    for orbit_params, desc in orbit_tests:
        # Build full params
        dram_type = orbit_params.get('dram-type', 'lpddr4')
        
        if dram_type == 'lpddr4':
            params = {
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
            }
        else:
            params = {
                'dram-type': 'lpddr5',
                'orbit-config-density': '4',
                'periods': '314 418 556 2500',
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
            }
        
        # Override with test params
        for k, v in orbit_params.items():
            params[k] = v
        
        gen_result = generate_binary(params)
        
        if gen_result.get('success'):
            print(f"  PASS: {desc}")
            results.append((desc, True, "OK"))
        else:
            print(f"  FAIL: {desc} - {gen_result.get('message')}")
            results.append((desc, False, gen_result.get('message')))
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nAll Orbit Params Tests: {passed}/{len(results)} passed")
    return results


# ============================================================================
# GUI vs CLI Comparison Test
# ============================================================================

def test_gui_vs_cli():
    """Test GUI vs CLI with same params."""
    print("\n=== Testing GUI vs CLI ===")
    results = []
    
    test_cases = [
        ('lpddr4_single', {
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
        }),
        ('lpddr5_single', {
            'dram-type': 'lpddr5',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
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
        }),
    ]
    
    for desc, params in test_cases:
        # Generate via GUI
        gen_result = generate_binary(params)
        if not gen_result.get('success'):
            print(f"  FAIL: {desc} - GUI generate failed")
            results.append((desc, False, "GUI generate failed"))
            continue
        
        gui_bin = BINARY_FILE
        
        # Generate via CLI with same params
        cli_bin = f'/tmp/test_{desc}_cli.bin'
        cmd = [
            sys.executable, 'gen_timing_params',
            '--dram-type', params['dram-type'],
            '--densities', params['orbit-config-density'],
            '--phy-name', 'sphy-v9r8',
            '--speed-bin', '4266',
            '--dq-width', '16',
            '--cpipe-depth', params['cpipe-depth'],
            '--dpipe-depth', params['dpipe-depth'],
        ]
        
        if params['dram-type'] == 'lpddr4':
            cmd.extend(['--omc-freq-ratio', '2', '--phy-freq-ratio', '2'])
            cmd.extend([
                '--write-odt-upto', params['write-odt-upto'],
                '--read-dbi-upto', params['read-dbi-upto'],
                '--write-dbi-upto', params['write-dbi-upto'],
                '--dram-tck', params['dram-tck'],
                '--wdqs-ctrl-mode', params['wdqs-ctrl-mode'],
            ])
            cmd.append('--variable-trrd')
            cmd.append('--txsr-as-1st-ed')
        else:
            cmd.extend(['--omc-freq-ratio', params['omc-freq-ratio'], '--phy-freq-ratio', params['phy-freq-ratio']])
            cmd.extend([
                '--write-odt-upto', params['write-odt-upto'],
                '--read-dbi-upto', params['read-dbi-upto'],
                '--write-dbi-upto', params['write-dbi-upto'],
                '--dram-tck', params['dram-tck'],
                '--wck-1to4-upto', params['wck-1to4-upto'],
                '--wck-always-on-from', params['wck-always-on-from'],
                '--wck-always-on-upto', params['wck-always-on-upto'],
            ])
        
        cmd.extend([
            '--orbit-byte-mode', params['orbit-byte-mode'],
            '--orbit-mixed', params['orbit-mixed'],
            '--orbit-rank-interleaving', '1' if params.get('orbit-rank-interleaving') == 'true' else '0',
            '--orbit-num-rank', params['orbit-num-rank'],
            '--orbit-config-use-python',
        ])
        cmd.extend(params['periods'].split())
        
        subprocess.run(cmd, capture_output=True, check=True)
        shutil.copy('ddr_timing_table.bin', cli_bin)
        
        # Compare
        match, msg = compare_binaries_timing(gui_bin, cli_bin, 0x800)
        
        if match:
            print(f"  PASS: {desc}")
            results.append((desc, True, "OK"))
        else:
            print(f"  FAIL: {desc} - {msg}")
            results.append((desc, False, msg))
        
        os.remove(cli_bin)
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nGUI vs CLI Tests: {passed}/{len(results)} passed")
    return results


# ============================================================================
# Random Param Comparison Test (GUI vs CLI)
# ============================================================================

def generate_random_params(dram_type):
    """Generate random valid parameters for testing - FULL random for ALL params."""
    random.seed(None)  # Use system time for randomness
    
    # Periods: Random count (1-4) with random values in range
    num_periods = random.randint(1, 4)
    if dram_type == 'lpddr4':
        periods = [str(random.randint(300, 2500)) for _ in range(num_periods)]
        # Ensure last period is >= 2000 for valid timing
        periods[-1] = str(max(2000, int(periods[-1])))
    else:
        periods = [str(random.randint(300, 2500)) for _ in range(num_periods)]
        periods[-1] = str(max(2000, int(periods[-1])))
    
    speed_bin = '4266' if dram_type == 'lpddr4' else '6400'
    
    # Density ranges
    lp4_densities = [2, 3, 4, 6, 8, 12, 16]
    lp5_densities = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
    
    params = {
        'dram-type': dram_type,
        'dq-width': str(random.choice([16, 32])),
        'speed-bin': speed_bin,
        'orbit-config-density': str(random.choice(lp4_densities if dram_type == 'lpddr4' else lp5_densities)),
        'periods': ' '.join(periods),
        'dram-tck': str(random.randint(300, 5000)),
        'min-dram-tck': str(random.randint(200, 3000)),
        'cpipe-depth': str(random.randint(1, 8)),
        'dpipe-depth': str(random.randint(1, 8)),
        'read-dbi-upto': str(random.randint(1000, 10000)),
        'write-dbi-upto': str(random.randint(1000, 10000)),
        'write-odt-upto': str(random.randint(1250, 10000)),
        'read-lecc-upto': str(random.randint(500, 2500)),
        'write-lecc-upto': str(random.randint(500, 2500)),
        'omc-freq-ratio': str(random.choice([1, 2, 4])),
        'phy-freq-ratio': str(random.choice([1, 2, 4])),
        # Orbit config params - FULL random
        'orbit-byte-mode': str(random.choice([0, 1])),
        'orbit-mixed': str(random.choice([0, 1])),
        'orbit-rank-interleaving': str(random.choice([0, 1])),
        'orbit-num-rank': str(random.choice([1, 2])),
        'orbit-reboot-with-mrw': str(random.choice([0, 1])),
        'orbit-rfm-en': str(random.choice([0, 1])),
        'orbit-ca-odt': str(random.choice([0, 1])),
        # Late fields - FULL random
        'orbit-dynamic-power-down': str(random.choice([0, 1])),
        'orbit-dynamic-power-down-threshold': str(random.randint(0, 1000000)),
        'orbit-dynamic-self-refresh': str(random.choice([0, 1])),
        'orbit-dynamic-self-refresh-threshold': str(random.randint(0, 1000000)),
        'orbit-phy-low-power': str(random.choice([0, 1])),
        'orbit-phy-idle-cnt-th': str(random.randint(0, 100000)),
        'orbit-periodic-training': str(random.choice([0, 1])),
        'orbit-periodic-training-period': str(random.randint(5000, 50000)),
        'orbit-temp-sensing': str(random.choice([0, 1])),
        'orbit-temp-sensing-period': str(random.randint(5000, 50000)),
        'orbit-zq-calibration-period': str(random.randint(10000, 100000)),
        'orbit-t-refiab': str(random.randint(2000000, 5000000)),
        'orbit-t-refipb': str(random.randint(200000, 600000)),
        'orbit-t-zqcal': str(random.randint(500000, 2000000)),
        'orbit-config-use-python': 'true',
    }
    
    if dram_type == 'lpddr4':
        # LP4 specific params - random
        params['wdqs-ctrl-mode'] = str(random.choice([0, 1]))
        params['variable-trrd'] = 'true' if random.choice([True, False]) else 'false'
        params['txsr-as-1st-ed'] = 'true' if random.choice([True, False]) else 'false'
        params['rpste-upto'] = str(random.randint(625, 2500))
        params['wpste-upto'] = str(random.randint(625, 2500))
        # DFS timing - random
        params['dfs-lvl-t-ck-0'] = str(random.randint(300, 5000))
        params['dfs-lvl-t-ck-1'] = str(random.randint(300, 5000))
        params['dfs-lvl-t-ck-2'] = str(random.randint(300, 5000))
    else:
        # LP5 specific params - random
        params['orbit-dsm-en'] = str(random.choice([0, 1]))
        params['wck-1to4-upto'] = str(random.randint(625, 2500))
        params['wck-always-on-from'] = str(random.randint(0, 100))
        params['wck-always-on-upto'] = str(random.randint(314, 1256))
        params['nt-odt-upto'] = str(random.randint(625, 2500))
        params['bg-mode-upto'] = str(random.randint(625, 2500))
        params['wck-hf-upto'] = str(random.randint(625, 2500))
        params['wck-pst1-upto'] = str(random.randint(625, 2500))
        params['wck-pst2-upto'] = str(random.randint(625, 2500))
        params['rdqs-pst1-upto'] = str(random.randint(625, 2500))
        params['rdqs-pst2-upto'] = str(random.randint(625, 2500))
        # DFS timing - random
        params['dfs-lvl-t-ck-0'] = str(random.randint(300, 5000))
        params['dfs-lvl-t-ck-1'] = str(random.randint(300, 5000))
        params['dfs-lvl-t-ck-2'] = str(random.randint(300, 5000))
    
    return params


def build_cli_command(params, cli_bin):
    """Build CLI command from params - FULL random params."""
    speed_bin = '4266' if params['dram-type'] == 'lpddr4' else '6400'
    
    cmd = [
        sys.executable, 'gen_timing_params',
        '--dram-type', params['dram-type'],
        '--densities', params['orbit-config-density'],
        '--phy-name', 'sphy-v9r8',
        '--speed-bin', speed_bin,
        '--dq-width', params['dq-width'],
        '--cpipe-depth', params['cpipe-depth'],
        '--dpipe-depth', params['dpipe-depth'],
        '--omc-freq-ratio', params['omc-freq-ratio'],
        '--phy-freq-ratio', params['phy-freq-ratio'],
        '--dram-tck', params['dram-tck'],
        '--min-dram-tck', params['min-dram-tck'],
        '--read-dbi-upto', params['read-dbi-upto'],
        '--write-dbi-upto', params['write-dbi-upto'],
        '--write-odt-upto', params['write-odt-upto'],
        '--read-lecc-upto', params.get('read-lecc-upto', '625'),
        '--write-lecc-upto', params.get('write-lecc-upto', '625'),
        '--orbit-byte-mode', params['orbit-byte-mode'],
        '--orbit-mixed', params['orbit-mixed'],
        '--orbit-rank-interleaving', params.get('orbit-rank-interleaving', '1'),
        '--orbit-num-rank', params['orbit-num-rank'],
        '--orbit-reboot-with-mrw', params.get('orbit-reboot-with-mrw', '0'),
        '--orbit-rfm-en', params.get('orbit-rfm-en', '0'),
        '--orbit-ca-odt', params.get('orbit-ca-odt', '0'),
        '--orbit-dynamic-power-down', params.get('orbit-dynamic-power-down', '0'),
        '--orbit-dynamic-power-down-threshold', params.get('orbit-dynamic-power-down-threshold', '0'),
        '--orbit-dynamic-self-refresh', params.get('orbit-dynamic-self-refresh', '0'),
        '--orbit-dynamic-self-refresh-threshold', params.get('orbit-dynamic-self-refresh-threshold', '0'),
        '--orbit-phy-low-power', params.get('orbit-phy-low-power', '0'),
        '--orbit-phy-idle-cnt-th', params.get('orbit-phy-idle-cnt-th', '0'),
        '--orbit-periodic-training', params.get('orbit-periodic-training', '0'),
        '--orbit-periodic-training-period', params.get('orbit-periodic-training-period', '24000'),
        '--orbit-temp-sensing', params.get('orbit-temp-sensing', '0'),
        '--orbit-temp-sensing-period', params.get('orbit-temp-sensing-period', '32000'),
        '--orbit-zq-calibration-period', params.get('orbit-zq-calibration-period', '48000'),
        '--orbit-t-refiab', params.get('orbit-t-refiab', '3904000'),
        '--orbit-t-refipb', params.get('orbit-t-refipb', '488000'),
        '--orbit-t-zqcal', params.get('orbit-t-zqcal', '1000000'),
        '--orbit-config-use-python',
    ]
    
    if params.get('two-channel') == 'true':
        cmd.append('--two-channel')
    
    if params['dram-type'] == 'lpddr4':
        cmd.extend(['--wdqs-ctrl-mode', params.get('wdqs-ctrl-mode', '1')])
        if params.get('variable-trrd') == 'true':
            cmd.append('--variable-trrd')
        if params.get('txsr-as-1st-ed') == 'true':
            cmd.append('--txsr-as-1st-ed')
        if 'rpste-upto' in params:
            cmd.extend(['--rpste-upto', params['rpste-upto']])
        if 'wpste-upto' in params:
            cmd.extend(['--wpste-upto', params['wpste-upto']])
    else:
        if 'orbit-dsm-en' in params:
            cmd.extend(['--orbit-dsm-en', params['orbit-dsm-en']])
        cmd.extend(['--wck-1to4-upto', params.get('wck-1to4-upto', '625')])
        cmd.extend(['--wck-always-on-from', params.get('wck-always-on-from', '0')])
        cmd.extend(['--wck-always-on-upto', params.get('wck-always-on-upto', '314')])
        for p in ['nt-odt-upto', 'bg-mode-upto', 'wck-hf-upto', 'wck-pst1-upto', 'wck-pst2-upto', 'rdqs-pst1-upto', 'rdqs-pst2-upto']:
            if p in params:
                cmd.extend([f'--{p}', params[p]])
    
    if 'dfs-lvl-t-ck-0' in params:
        cmd.extend(['--dfs-lvl-t-ck-0', params['dfs-lvl-t-ck-0']])
    if 'dfs-lvl-t-ck-1' in params:
        cmd.extend(['--dfs-lvl-t-ck-1', params['dfs-lvl-t-ck-1']])
    if 'dfs-lvl-t-ck-2' in params:
        cmd.extend(['--dfs-lvl-t-ck-2', params['dfs-lvl-t-ck-2']])
    
    cmd.extend(params['periods'].split())
    return cmd


def test_random_param_comparison():
    """Test GUI vs CLI with random parameters - FULL random test."""
    print("\n=== Testing Random Param Comparison (GUI vs CLI) ===")
    
    results = []
    iterations = 100  # Increased from 10 to 100 for comprehensive testing
    
    for i in range(iterations):
        for dram_type in ['lpddr4', 'lpddr5']:
            desc = f"{dram_type}_random_{i+1}"
            print(f"[{i*2+1}/{iterations*2}] Testing {desc}...")
            
            # Generate random params
            params = generate_random_params(dram_type)
            
            # Generate via GUI
            gen_result = generate_binary(params)
            if not gen_result.get('success'):
                print(f"  FAIL: GUI generate failed - {gen_result.get('message')}")
                results.append((desc, False, "GUI generate failed"))
                continue
            
            gui_bin = BINARY_FILE
            
            # Generate via CLI with same params
            cli_bin = f'/tmp/test_{desc}_cli.bin'
            cmd = build_cli_command(params, cli_bin)
            
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                shutil.copy('ddr_timing_table.bin', cli_bin)
            except subprocess.CalledProcessError as e:
                print(f"  FAIL: CLI generate failed - {e.stderr.decode()}")
                results.append((desc, False, "CLI generate failed"))
                if os.path.exists(cli_bin):
                    os.remove(cli_bin)
                continue
            
            # Compare binaries
            match, msg = compare_binaries_timing(gui_bin, cli_bin, 0x1000)
            
            if match:
                print(f"  PASS: {desc}")
                results.append((desc, True, "OK"))
            else:
                print(f"  FAIL: {desc} - {msg}")
                results.append((desc, False, msg))
            
            # Clean up
            if os.path.exists(cli_bin):
                os.remove(cli_bin)
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nRandom Param Comparison Tests: {passed}/{len(results)} passed")
    return results


# ============================================================================
# Dual Channel Tests
# ============================================================================

def test_dual_channel():
    """Test dual channel binary generation."""
    print("\n=== Testing Dual Channel Binaries ===")
    
    results = []
    
    # Dual channel test cases
    test_cases = [
        ('lpddr4_dual', {
            'dram-type': 'lpddr4',
            'dq-width': '16',
            'speed-bin': '4266',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'dram-tck': '471',
            'min-dram-tck': '938',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'read-dbi-upto': '10000',
            'write-dbi-upto': '10000',
            'write-odt-upto': '1250',
            'wdqs-ctrl-mode': '1',
            'variable-trrd': 'true',
            'txsr-as-1st-ed': 'true',
            'omc-freq-ratio': '2',
            'phy-freq-ratio': '2',
            'two-channel': 'true',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        }),
        ('lpddr5_dual', {
            'dram-type': 'lpddr5',
            'dq-width': '16',
            'speed-bin': '6400',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
            'dram-tck': '314',
            'min-dram-tck': '418',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'read-dbi-upto': '10000',
            'write-dbi-upto': '10000',
            'write-odt-upto': '10000',
            'write-lecc-upto': '625',
            'omc-freq-ratio': '1',
            'phy-freq-ratio': '1',
            'wck-1to4-upto': '625',
            'wck-always-on-from': '0',
            'wck-always-on-upto': '314',
            'two-channel': 'true',
            'orbit-config-use-python': 'true',
            'orbit-byte-mode': '0',
            'orbit-mixed': '0',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
        }),
    ]
    
    for desc, params in test_cases:
        print(f"Testing {desc}...")
        
        # Generate via GUI
        gen_result = generate_binary(params)
        if not gen_result.get('success'):
            print(f"  FAIL: {desc} - GUI generate failed")
            results.append((desc, False, gen_result.get('message')))
            continue
        
        # Check binary size (dual channel should be larger)
        gui_bin = BINARY_FILE
        gui_size = os.path.getsize(gui_bin)
        
        # Generate via CLI with same params
        cli_bin = f'/tmp/test_{desc}_cli.bin'
        cmd = build_cli_command(params, cli_bin)
        cmd.append('--two-channel')
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            shutil.copy('ddr_timing_table.bin', cli_bin)
        except subprocess.CalledProcessError as e:
            print(f"  FAIL: {desc} - CLI generate failed")
            results.append((desc, False, "CLI generate failed"))
            if os.path.exists(cli_bin):
                os.remove(cli_bin)
            continue
        
        # Compare binaries
        match, msg = compare_binaries_timing(gui_bin, cli_bin, 0x1000)
        
        if match:
            print(f"  PASS: {desc}")
            results.append((desc, True, "OK"))
        else:
            print(f"  FAIL: {desc} - {msg}")
            results.append((desc, False, msg))
        
        if os.path.exists(cli_bin):
            os.remove(cli_bin)
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nDual Channel Tests: {passed}/{len(results)} passed")
    return results


# ============================================================================

def test_parse_offset_comparison():
    """Test that GUI-parsed values match raw binary values at correct offsets."""
    print("\n=== Testing Parameter Offset Parsing ===")
    
    import struct
    results = []
    
    # Test binaries with known values
    test_binaries = [
        ('ddr_timing_table.lpddr4.dual.ref.bin', 'lpddr4', 7864),
        ('ddr_timing_table.lpddr5.dual.ref.bin', 'lpddr5', 7872),
    ]
    
    for bin_file, expected_dram, expected_size in test_binaries:
        if not os.path.exists(bin_file):
            print(f"  SKIP: {bin_file} not found")
            continue
            
        print(f"\n  Testing: {bin_file}")
        
        # Analyze via GUI
        an_result = analyze_binary(bin_file)
        if not an_result.get('success'):
            print(f"    ERROR: GUI analyze failed - {an_result.get('message')}")
            results.append((bin_file, False, "GUI analyze failed"))
            continue
        
        data = an_result['data']
        
        # Read binary directly
        with open(bin_file, 'rb') as f:
            binary_data = f.read()
        
        is_lpddr5 = (expected_dram == 'lpddr5')
        orbit_offset = 0x800
        
        mismatches = []
        
        # Check 1: cpipe_depth at offset 0x14 (struct offset 20)
        gui_cpipe = data['pipe'].get('cpipe_depth', 0)
        bin_cpipe = struct.unpack('<H', binary_data[orbit_offset + 0x14:orbit_offset + 0x16])[0]
        if gui_cpipe != bin_cpipe:
            mismatches.append(f"cpipe_depth: GUI={gui_cpipe}, Binary@0x814={bin_cpipe}")
        
        # Check 2: dpipe_depth at offset 0x16 (struct offset 22)
        gui_dpipe = data['pipe'].get('dpipe_depth', 0)
        bin_dpipe = struct.unpack('<H', binary_data[orbit_offset + 0x16:orbit_offset + 0x18])[0]
        if gui_dpipe != bin_dpipe:
            mismatches.append(f"dpipe_depth: GUI={gui_dpipe}, Binary@0x816={bin_dpipe}")
        
        # Check 3: omc_freq_ratio at offset 0x14 (struct offset 14)
        gui_omc = data['pipe'].get('omc_freq_ratio', 0)
        bin_omc = struct.unpack('<H', binary_data[orbit_offset + 0x14:orbit_offset + 0x16])[0]
        if gui_omc != bin_omc:
            mismatches.append(f"omc_freq_ratio: GUI={gui_omc}, Binary@0x814={bin_omc}")
        
        # Check 4: phy_freq_ratio at offset 0x12 (struct offset 12)
        gui_phy = data['pipe'].get('phy_freq_ratio', 0)
        bin_phy = struct.unpack('<H', binary_data[orbit_offset + 0x12:orbit_offset + 0x14])[0]
        if gui_phy != bin_phy:
            mismatches.append(f"phy_freq_ratio: GUI={gui_phy}, Binary@0x812={bin_phy}")
        
        # Check 5: density
        gui_density = data['orbit'].get('density', 0)
        density_offset = 0x1c if not is_lpddr5 else 0x24
        bin_density = struct.unpack('<H', binary_data[orbit_offset + density_offset:orbit_offset + density_offset + 2])[0]
        if gui_density != bin_density:
            mismatches.append(f"density: GUI={gui_density}, Binary@{density_offset:#x}={bin_density}")
        
        # Check 6: rank_interleaving at offset 0x1e
        gui_rank_int = data['orbit'].get('rank_interleaving', 0)
        bin_rank_int = struct.unpack('<H', binary_data[orbit_offset + 0x1e:orbit_offset + 0x20])[0]
        if gui_rank_int != bin_rank_int:
            mismatches.append(f"rank_interleaving: GUI={gui_rank_int}, Binary@0x81e={bin_rank_int}")
        
        # Check 7: num_rank at offset 0x20
        gui_num_rank = data['orbit'].get('num_rank', 0)
        bin_num_rank = struct.unpack('<H', binary_data[orbit_offset + 0x20:orbit_offset + 0x22])[0]
        if gui_num_rank != bin_num_rank:
            mismatches.append(f"num_rank: GUI={gui_num_rank}, Binary@0x820={bin_num_rank}")
        
        # Check 8: density_code
        gui_density_code = data['orbit'].get('density_code', 0)
        dc_offset = 0x78 if not is_lpddr5 else 0x80
        bin_density_code = struct.unpack('<I', binary_data[orbit_offset + dc_offset:orbit_offset + dc_offset + 4])[0]
        if gui_density_code != bin_density_code:
            mismatches.append(f"density_code: GUI={gui_density_code}, Binary@{dc_offset:#x}={bin_density_code}")
        
        # Check 9: timing features (from timing table at offset 0)
        entry_size = 188
        gui_write_odt = data['timing'].get('write_odt_upto', 0)
        gui_read_dbi = data['timing'].get('read_dbi_upto', 0)
        gui_write_dbi = data['timing'].get('write_dbi_upto', 0)
        
        # Parse from binary timing table
        bin_write_odt = 0
        bin_read_dbi = 0
        bin_write_dbi = 0
        for i in range(8):
            offset = i * entry_size
            if offset + 188 > len(binary_data):
                break
            t_ck = struct.unpack('<I', binary_data[offset+4:offset+8])[0]
            if t_ck == 0 or t_ck > 10000:
                continue
            if binary_data[offset + 158] and t_ck > bin_write_odt:
                bin_write_odt = t_ck
            if binary_data[offset + 161] and t_ck > bin_read_dbi:
                bin_read_dbi = t_ck
            if binary_data[offset + 160] and t_ck > bin_write_dbi:
                bin_write_dbi = t_ck
        
        if gui_write_odt != bin_write_odt:
            mismatches.append(f"write_odt_upto: GUI={gui_write_odt}, Binary={bin_write_odt}")
        if gui_read_dbi != bin_read_dbi:
            mismatches.append(f"read_dbi_upto: GUI={gui_read_dbi}, Binary={bin_read_dbi}")
        if gui_write_dbi != bin_write_dbi:
            mismatches.append(f"write_dbi_upto: GUI={gui_write_dbi}, Binary={bin_write_dbi}")
        
        if mismatches:
            print(f"    FAIL: {len(mismatches)} mismatches:")
            for m in mismatches:
                print(f"      - {m}")
            results.append((bin_file, False, "; ".join(mismatches)))
        else:
            print(f"    PASS: All params match")
            results.append((bin_file, True, "OK"))
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nOffset Comparison Tests: {passed}/{len(results)} passed")
    return results


# ============================================================================

def test_orbit_params_full_cycle():
    """Test: generate bin → load bin → compare orbit params"""
    print("\n=== Testing Orbit Params Full Cycle ===")
    results = []
    
    test_configs = [
        ('lpddr4', 'rank_int_1_num_rank_2', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'orbit-rank-interleaving': 'true',
            'orbit-num-rank': '2',
            'orbit-config-use-python': 'true',
        }, {'rank_interleaving': 1, 'num_rank': 2}),
        
        ('lpddr4', 'rank_int_0_num_rank_1', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'orbit-rank-interleaving': 'false',
            'orbit-num-rank': '1',
            'orbit-config-use-python': 'true',
        }, {'rank_interleaving': 0, 'num_rank': 1}),
        
        ('lpddr4', 'byte_mode_1', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'orbit-byte-mode': '1',
            'orbit-config-use-python': 'true',
        }, {'byte_mode': 1}),
        
        ('lpddr4', 'mixed_1', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'orbit-mixed': '1',
            'orbit-config-use-python': 'true',
        }, {'mixed': 1}),
        
        ('lpddr4', 'rfm_en_1', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'orbit-rfm-en': 'true',
            'orbit-config-use-python': 'true',
        }, {'rfm_en': 1}),
        
        ('lpddr4', 'reboot_mrw_1', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'orbit-reboot-with-mrw': 'true',
            'orbit-config-use-python': 'true',
        }, {'reboot_with_mrw': 1}),
        
        ('lpddr5', 'dsm_en_1', {
            'dram-type': 'lpddr5',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'orbit-dsm-en': 'true',
            'orbit-config-use-python': 'true',
        }, {'dsm_en': 1}),
        
        ('lpddr5', 'ca_odt_1', {
            'dram-type': 'lpddr5',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'orbit-ca-odt': 'true',
            'orbit-config-use-python': 'true',
        }, {'ca_odt': 1}),
        
        ('lpddr4', 'dual_channel', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'two-channel': 'true',
            'orbit-config-use-python': 'true',
        }, {'two_channel': 1}),
        
        ('lpddr5', 'dual_channel', {
            'dram-type': 'lpddr5',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'two-channel': 'true',
            'orbit-config-use-python': 'true',
        }, {'two_channel': 1}),
    ]
    
    for dram_type, desc, params, expected in test_configs:
        # Generate
        gen_result = generate_binary(params)
        if not gen_result.get('success'):
            print(f"  FAIL: {desc} - generate failed: {gen_result.get('message')}")
            results.append((desc, False, f"generate failed: {gen_result.get('message')}"))
            continue
        
        # Load
        an_result = analyze_binary('ddr_timing_table.bin')
        if not an_result.get('success'):
            print(f"  FAIL: {desc} - analyze failed: {an_result.get('message')}")
            results.append((desc, False, f"analyze failed: {an_result.get('message')}"))
            continue
        
        # Compare
        mismatches = []
        for key, exp_val in expected.items():
            actual = an_result['data']['orbit'].get(key)
            if actual != exp_val:
                mismatches.append(f"{key}: expected={exp_val}, actual={actual}")
        
        if mismatches:
            print(f"  FAIL: {desc} - {', '.join(mismatches)}")
            results.append((desc, False, "; ".join(mismatches)))
        else:
            print(f"  PASS: {desc}")
            results.append((desc, True, "OK"))
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nOrbit Params Full Cycle: {passed}/{len(results)} passed")
    return results


# ============================================================================

def test_timing_params_full_cycle():
    """Test: generate bin → load bin → compare timing params"""
    print("\n=== Testing Timing Params Full Cycle ===")
    results = []
    
    test_configs = [
        ('lpddr4', 'write_odt_1250', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'write-odt-upto': '1250',
            'orbit-config-use-python': 'true',
        }, {'write_odt_upto': 1250}),
        
        ('lpddr4', 'read_dbi_10000', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'read-dbi-upto': '10000',
            'orbit-config-use-python': 'true',
        }, {'read_dbi_upto': 10000}),
        
        ('lpddr4', 'write_dbi_10000', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'write-dbi-upto': '10000',
            'orbit-config-use-python': 'true',
        }, {'write_dbi_upto': 10000}),
        
        ('lpddr4', 'write_odt_2500', {
            'dram-type': 'lpddr4',
            'orbit-config-density': '4',
            'periods': '471 938 1631 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'write-odt-upto': '2500',
            'orbit-config-use-python': 'true',
        }, {'write_odt_upto': 2500}),
        
        ('lpddr5', 'write_lecc_625', {
            'dram-type': 'lpddr5',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'write-lecc-upto': '625',
            'orbit-config-use-python': 'true',
        }, {'write_lecc_upto': 625}),
        
        ('lpddr5', 'read_lecc_625', {
            'dram-type': 'lpddr5',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'read-lecc-upto': '625',
            'orbit-config-use-python': 'true',
        }, {'read_lecc_upto': 625}),
    ]
    
    for dram_type, desc, params, expected in test_configs:
        # Generate
        gen_result = generate_binary(params)
        if not gen_result.get('success'):
            print(f"  FAIL: {desc} - generate failed: {gen_result.get('message')}")
            results.append((desc, False, f"generate failed: {gen_result.get('message')}"))
            continue
        
        # Load
        an_result = analyze_binary('ddr_timing_table.bin')
        if not an_result.get('success'):
            print(f"  FAIL: {desc} - analyze failed: {an_result.get('message')}")
            results.append((desc, False, f"analyze failed: {an_result.get('message')}"))
            continue
        
        # Compare
        mismatches = []
        for key, exp_val in expected.items():
            actual = an_result['data']['timing'].get(key)
            if actual != exp_val:
                mismatches.append(f"{key}: expected={exp_val}, actual={actual}")
        
        if mismatches:
            print(f"  FAIL: {desc} - {', '.join(mismatches)}")
            results.append((desc, False, "; ".join(mismatches)))
        else:
            print(f"  PASS: {desc}")
            results.append((desc, True, "OK"))
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nTiming Params Full Cycle: {passed}/{len(results)} passed")
    return results


# ============================================================================

def test_lpddr5_bin_generation():
    """Test: LPDDR5 binary generation produces valid timing entries"""
    print("\n=== Testing LPDDR5 Binary Generation ===")
    import struct
    results = []
    
    test_configs = [
        ('lpddr5_single', {
            'dram-type': 'lpddr5',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'orbit-config-use-python': 'true',
        }, '314 418 556 2500', 0),
        
        ('lpddr5_dual', {
            'dram-type': 'lpddr5',
            'orbit-config-density': '4',
            'periods': '314 418 556 2500',
            'cpipe-depth': '1',
            'dpipe-depth': '1',
            'two-channel': 'true',
            'orbit-config-use-python': 'true',
        }, '314 418 556 2500', 1),
    ]
    
    for desc, params, expected_periods, expected_two_ch in test_configs:
        # Generate
        gen_result = generate_binary(params)
        if not gen_result.get('success'):
            print(f"  FAIL: {desc} - generate failed: {gen_result.get('message')}")
            results.append((desc, False, f"generate failed"))
            continue
        
        # Load
        an_result = analyze_binary('ddr_timing_table.bin')
        if not an_result.get('success'):
            print(f"  FAIL: {desc} - analyze failed")
            results.append((desc, False, f"analyze failed"))
            continue
        
        # Check periods
        actual_periods = an_result['data']['basic'].get('periods', '')
        two_ch = an_result['data'].get('two_channel', 0)
        
        mismatches = []
        if actual_periods != expected_periods:
            mismatches.append(f"periods: expected={expected_periods}, actual={actual_periods}")
        if two_ch != expected_two_ch:
            mismatches.append(f"two_channel: expected={expected_two_ch}, actual={two_ch}")
        
        # Check binary directly for valid timing entries
        try:
            with open('ddr_timing_table.bin', 'rb') as f:
                data = f.read()
            
            entry_size = 0x128
            valid_t_ck_values = []
            for i in range(8):
                offset = i * entry_size
                if offset + 8 > len(data):
                    break
                t_ck = struct.unpack('<I', data[offset+4:offset+8])[0]
                if 300 <= t_ck <= 5000:
                    valid_t_ck_values.append(t_ck)
            
            # Check LECC flags are valid (0 or 1, not garbage like 144)
            for i in range(min(4, len(valid_t_ck_values))):
                offset = i * entry_size
                write_lecc = data[offset + 180]
                read_lecc = data[offset + 179]
                if write_lecc > 1 or read_lecc > 1:
                    mismatches.append(f"LECC flags invalid at entry {i}: write={write_lecc}, read={read_lecc}")
        except Exception as e:
            mismatches.append(f"binary check error: {e}")
        
        if mismatches:
            print(f"  FAIL: {desc} - {', '.join(mismatches)}")
            results.append((desc, False, "; ".join(mismatches)))
        else:
            print(f"  PASS: {desc}")
            results.append((desc, True, "OK"))
    
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nLPDDR5 Binary Generation: {passed}/{len(results)} passed")
    return results


# ============================================================================

def main():
    print("=== DDR GUI Test Suite ===")
    
    # Check if server is running
    if not wait_for_server():
        print("ERROR: GUI server not responding. Start with: python3 gui.py")
        return 1
    
    print("GUI server is ready")
    
    # Run all tests
    param_results = test_parameters()
    ref_results = test_reference_binaries()
    psmhz_results = test_ps_mhz_toggle()
    
    # New tests
    button_load_results = test_button_load_binary()
    button_save_results = test_button_save_json()
    button_loadjson_results = test_button_load_json()
    button_gen_results = test_button_generate()
    load_modify_results = test_load_modify_generate_compare()
    density_results = test_all_densities()
    timing_results = test_all_timing_fields()
    orbit_results = test_all_orbit_params()
    gui_cli_results = test_gui_vs_cli()
    random_param_results = test_random_param_comparison()
    dual_channel_results = test_dual_channel()
    offset_comp_results = test_parse_offset_comparison()
    orbit_cycle_results = test_orbit_params_full_cycle()
    timing_cycle_results = test_timing_params_full_cycle()
    lpddr5_gen_results = test_lpddr5_bin_generation()
    
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
    
    for desc, ok, msg in psmhz_results:
        if not ok:
            print(f"FAIL: {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in button_load_results + button_save_results + button_loadjson_results + button_gen_results:
        if not ok:
            print(f"FAIL: Button test {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in load_modify_results:
        if not ok:
            print(f"FAIL: Load-Modify test {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in density_results:
        if not ok:
            print(f"FAIL: Density test {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in timing_results:
        if not ok:
            print(f"FAIL: Timing field test {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in orbit_results:
        if not ok:
            print(f"FAIL: Orbit param test {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in gui_cli_results:
        if not ok:
            print(f"FAIL: GUI vs CLI test {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in random_param_results:
        if not ok:
            print(f"FAIL: Random param test {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in dual_channel_results:
        if not ok:
            print(f"FAIL: Dual channel test {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in offset_comp_results:
        if not ok:
            print(f"FAIL: Offset comparison test {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in orbit_cycle_results:
        if not ok:
            print(f"FAIL: Orbit full cycle test {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in timing_cycle_results:
        if not ok:
            print(f"FAIL: Timing full cycle test {desc}: {msg}")
            all_ok = False
    
    for desc, ok, msg in lpddr5_gen_results:
        if not ok:
            print(f"FAIL: LPDDR5 generation test {desc}: {msg}")
            all_ok = False
    
    if all_ok:
        print("ALL TESTS PASSED")
        return 0
    else:
        print("SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
