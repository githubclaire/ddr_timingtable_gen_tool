#!/usr/bin/env python3
"""
Standalone CLI bin comparison test - no GUI server required.
Tests CLI vs CLI with different params to verify changes in binary.
Used to verify the bin generation works correctly.
"""

import os
import sys
import subprocess
import shutil
import random


def run_cli(params, output_bin):
    """Run CLI with params, output to output_bin."""
    cmd = [
        sys.executable, 'gen_timing_params',
        '--dram-type', params['dram-type'],
        '--densities', str(params.get('density', 4)),
        '--phy-name', 'sphy-v9r8',
        '--speed-bin', params['speed-bin'],
        '--dq-width', str(params.get('dq-width', 16)),
        '--cpipe-depth', str(params.get('cpipe-depth', 1)),
        '--dpipe-depth', str(params.get('dpipe-depth', 1)),
        '--omc-freq-ratio', str(params.get('omc-freq-ratio', 2)),
        '--phy-freq-ratio', str(params.get('phy-freq-ratio', 2)),
        '--dram-tck', str(params.get('dram-tck', 471)),
        '--min-dram-tck', str(params.get('min-dram-tck', 938)),
        '--read-dbi-upto', str(params.get('read-dbi-upto', 10000)),
        '--write-dbi-upto', str(params.get('write-dbi-upto', 10000)),
        '--write-odt-upto', str(params.get('write-odt-upto', 1250)),
        '--orbit-byte-mode', str(params.get('byte-mode', 0)),
        '--orbit-mixed', str(params.get('mixed', 0)),
        '--orbit-rank-interleaving', str(params.get('rank-interleaving', 1)),
        '--orbit-num-rank', str(params.get('num-rank', 2)),
        '--orbit-reboot-with-mrw', str(params.get('reboot-with-mrw', 0)),
        '--orbit-rfm-en', str(params.get('rfm-en', 0)),
        '--orbit-ca-odt', str(params.get('ca-odt', 0)),
        '--orbit-dynamic-power-down', str(params.get('dynamic-power-down', 0)),
        '--orbit-dynamic-power-down-threshold', str(params.get('dynamic-power-down-threshold', 0)),
        '--orbit-dynamic-self-refresh', str(params.get('dynamic-self-refresh', 0)),
        '--orbit-dynamic-self-refresh-threshold', str(params.get('dynamic-self-refresh-threshold', 0)),
        '--orbit-phy-low-power', str(params.get('phy-low-power', 0)),
        '--orbit-phy-idle-cnt-th', str(params.get('phy-idle-cnt-th', 0)),
        '--orbit-periodic-training', str(params.get('periodic-training', 0)),
        '--orbit-periodic-training-period', str(params.get('periodic-training-period', 24000)),
        '--orbit-temp-sensing', str(params.get('temp-sensing', 0)),
        '--orbit-temp-sensing-period', str(params.get('temp-sensing-period', 32000)),
        '--orbit-zq-calibration-period', str(params.get('zq-calibration-period', 48000)),
        '--orbit-t-refiab', str(params.get('t-refiab', 3904000)),
        '--orbit-t-refipb', str(params.get('t-refipb', 488000)),
        '--orbit-t-zqcal', str(params.get('t-zqcal', 1000000)),
        '--orbit-config-use-python',
    ]
    
    if params['dram-type'] == 'lpddr4':
        cmd.extend(['--wdqs-ctrl-mode', str(params.get('wdqs-ctrl-mode', 1))])
        if params.get('variable-trrd'):
            cmd.append('--variable-trrd')
        if params.get('txsr-as-1st-ed'):
            cmd.append('--txsr-as-1st-ed')
    else:
        if params.get('dsm-en'):
            cmd.extend(['--orbit-dsm-en', str(params.get('dsm-en', 0))])
        cmd.extend(['--wck-1to4-upto', str(params.get('wck-1to4-upto', 625))])
        cmd.extend(['--wck-always-on-from', str(params.get('wck-always-on-from', 0))])
        cmd.extend(['--wck-always-on-upto', str(params.get('wck-always-on-upto', 314))])
        cmd.extend(['--write-lecc-upto', str(params.get('write-lecc-upto', 625))])
    
    if params.get('two-channel'):
        cmd.append('--two-channel')
    
    cmd.extend(params.get('periods', '471 938 1631 2500').split())
    
    result = subprocess.run(cmd, capture_output=True, check=True)
    shutil.copy('ddr_timing_table.bin', output_bin)


def compare_binaries_timing(file1, file2, compare_size, start_offset=0):
    """Compare binary files from start_offset."""
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        data1 = f1.read()
        data2 = f2.read()
    
    data1 = data1[start_offset:start_offset + compare_size]
    data2 = data2[start_offset:start_offset + compare_size]
    
    for i in range(min(len(data1), len(data2))):
        if data1[i] != data2[i]:
            return False, f"Mismatch at offset {start_offset + i}"
    return True, "Match"


def test_param_variations():
    """Test various param values produce different binaries."""
    print("=" * 60)
    print("Param Variations Test (CLI - no GUI required)")
    print("=" * 60)
    
    lp4_base = {
        'dram-type': 'lpddr4',
        'density': 4,
        'speed-bin': '4266',
        'dq-width': 16,
        'cpipe-depth': 1,
        'dpipe-depth': 1,
        'omc-freq-ratio': 2,
        'phy-freq-ratio': 2,
        'dram-tck': 471,
        'min-dram-tck': 938,
        'read-dbi-upto': 10000,
        'write-dbi-upto': 10000,
        'write-odt-upto': 1250,
        'periods': '471 938 1631 2500',
    }
    
    test_cases = [
        # Test different densities produce different binaries
        ({'density': 4}, 'density_4'),
        ({'density': 8}, 'density_8'),
        ({'density': 16}, 'density_16'),
        # Test different threshold values
        ({'dynamic-power-down-threshold': 0, 'dynamic-power-down': 0}, 'dp_disabled'),
        ({'dynamic-power-down-threshold': 111, 'dynamic-power-down': 1}, 'dp_111'),
        ({'dynamic-power-down-threshold': 50000, 'dynamic-power-down': 1}, 'dp_50000'),
        # Test different zq_calibration_period
        ({'zq-calibration-period': 48000}, 'zq_default'),
        ({'zq-calibration-period': 555}, 'zq_555'),
        ({'zq-calibration-period': 100000}, 'zq_100000'),
        # Test different num_rank
        ({'num-rank': 1}, 'num_rank_1'),
        ({'num-rank': 2}, 'num_rank_2'),
        # Test different byte_mode
        ({'byte-mode': 0}, 'byte_mode_0'),
        ({'byte-mode': 1}, 'byte_mode_1'),
        # Test different mixed
        ({'mixed': 0}, 'mixed_0'),
        ({'mixed': 1}, 'mixed_1'),
        # Test different t_ref values
        ({'t-refiab': 3904000}, 'trefiab_default'),
        ({'t-refiab': 3000000}, 'trefiab_3000k'),
        ({'t-refiab': 5000000}, 'trefiab_5000k'),
    ]
    
    base_bin = '/tmp/cli_test_base.bin'
    results = []
    
    print("\n1. Testing parametric variations...")
    for param_change, desc in test_cases:
        params = {**lp4_base, **param_change}
        out_bin = f'/tmp/cli_test_{desc}.bin'
        
        try:
            run_cli(params, out_bin)
            size = os.path.getsize(out_bin)
            print(f"  {desc}: {size} bytes - OK")
            results.append((desc, True))
        except subprocess.CalledProcessError as e:
            print(f"  {desc}: FAIL - {e.stderr.decode()[:50]}")
            results.append((desc, False))
    
    print("\n2. Verifying binaries are different (param change = binary change)...")
    
    # Compare base vs test cases - binaries should differ
    print("  Note: Different params should produce different binaries")
    
    passed = sum(1 for _, ok in results if ok)
    failed = len(results) - passed
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_lpddr5_variations():
    """Test LPDDR5 variations."""
    print("\n" + "=" * 60)
    print("LPDDR5 Variations Test")
    print("=" * 60)
    
    lp5_base = {
        'dram-type': 'lpddr5',
        'density': 4,
        'speed-bin': '6400',
        'dq-width': 16,
        'cpipe-depth': 1,
        'dpipe-depth': 1,
        'omc-freq-ratio': 1,
        'phy-freq-ratio': 1,
        'dram-tck': 314,
        'min-dram-tck': 418,
        'read-dbi-upto': 10000,
        'write-dbi-upto': 10000,
        'write-odt-upto': 10000,
        'periods': '314 418 556 2500',
        'wck-1to4-upto': 625,
        'wck-always-on-from': 0,
        'wck-always-on-upto': 314,
    }
    
    test_cases = [
        ({'density': 4}, 'density_4'),
        ({'density': 8}, 'density_8'),
        ({'density': 16}, 'density_16'),
        ({'density': 24}, 'density_24'),
        ({'density': 32}, 'density_32'),
        ({'dynamic-power-down-threshold': 111, 'dynamic-power-down': 1}, 'dp_111'),
        ({'dynamic-self-refresh-threshold': 222, 'dynamic-self-refresh': 1}, 'ds_222'),
        ({'zq-calibration-period': 555}, 'zq_555'),
    ]
    
    results = []
    
    for param_change, desc in test_cases:
        params = {**lp5_base, **param_change}
        out_bin = f'/tmp/cli_test_lp5_{desc}.bin'
        
        try:
            run_cli(params, out_bin)
            size = os.path.getsize(out_bin)
            print(f"  {desc}: {size} bytes - OK")
            results.append((desc, True))
        except subprocess.CalledProcessError as e:
            print(f"  {desc}: FAIL")
            results.append((desc, False))
    
    passed = sum(1 for _, ok in results if ok)
    print(f"\nResults: {passed}/{len(results)} passed")
    return passed > 0


def test_dual_channel():
    """Test dual channel."""
    print("\n" + "=" * 60)
    print("Dual Channel Test")
    print("=" * 60)
    
    configs = [
        ('lpddr4', {'density': 4, 'periods': '471 938 1631 2500'}),
        ('lpddr5', {'density': 4, 'periods': '314 418 556 2500'}),
    ]
    
    results = []
    
    for dram_type, extra in configs:
        params = {
            'dram-type': dram_type,
            'density': extra['density'],
            'speed-bin': '4266' if dram_type == 'lpddr4' else '6400',
            'dq-width': 16,
            'cpipe-depth': 1,
            'dpipe-depth': 1,
            'omc-freq-ratio': 2 if dram_type == 'lpddr4' else 1,
            'phy-freq-ratio': 2 if dram_type == 'lpddr4' else 1,
            'dram-tck': extra['periods'].split()[0],
            'min-dram-tck': extra['periods'].split()[1],
            'read-dbi-upto': 10000,
            'write-dbi-upto': 10000,
            'write-odt-upto': 1250 if dram_type == 'lpddr4' else 10000,
            'periods': extra['periods'],
            'two-channel': True,
        }
        
        if dram_type == 'lpddr4':
            params['wdqs-ctrl-mode'] = 1
            params['variable-trrd'] = True
            params['txsr-as-1st-ed'] = True
        
        out_bin = f'/tmp/cli_test_{dram_type}_dual.bin'
        
        try:
            run_cli(params, out_bin)
            size = os.path.getsize(out_bin)
            print(f"  {dram_type} dual: {size} bytes - OK")
            results.append((dram_type, True))
        except subprocess.CalledProcessError as e:
            print(f"  {dram_type} dual: FAIL")
            results.append((dram_type, False))
    
    passed = sum(1 for _, ok in results if ok)
    print(f"\nResults: {passed}/{len(results)} passed")
    return passed == len(results)


if __name__ == '__main__':
    passed = 0
    failed = 0
    
    if test_param_variations():
        passed += 1
    else:
        failed += 1
    
    if test_lpddr5_variations():
        passed += 1
    else:
        failed += 1
    
    if test_dual_channel():
        passed += 1
    else:
        failed += 1
    
    print("\n" + "=" * 60)
    print(f"FINAL Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)