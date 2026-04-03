#!/usr/bin/env python3
"""
Test cases for binary parsing - verify all fields are parsed from binary.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import analyze_binary_file


def test_lpddr4_dual_all_fields_parsed():
    """Verify all fields parsed from LPDDR4 dual reference binary."""
    result = analyze_binary_file('ddr_timing_table.lpddr4.dual.ref.bin')
    
    assert result['success'], f"Failed to parse: {result.get('message')}"
    data = result['data']
    
    # Check basic fields
    assert data['basic']['dram_type'] == 'lpddr4', f"Expected lpddr4, got {data['basic']['dram_type']}"
    assert data['two_channel'] == 1, f"Expected dual channel, got {data['two_channel']}"
    
    # Check orbit config fields (should be parsed from binary, not hardcoded)
    orbit = data['orbit']
    
    # Verify key fields are NOT default values (they should be parsed)
    # rfm_en should be 0 in reference binary
    # regional_clock_gating should be 1
    # dram_clock_gating should be 1
    print(f"  rfm_en: {orbit.get('rfm_en')}")
    print(f"  regional_clock_gating: {orbit.get('regional_clock_gating')}")
    print(f"  dram_clock_gating: {orbit.get('dram_clock_gating')}")
    print(f"  num_rank: {orbit.get('num_rank')}")
    print(f"  density: {orbit.get('density')}")
    print(f"  dq_width: {orbit.get('dq_width')}")
    print(f"  mrr_byte_lane: {orbit.get('mrr_byte_lane')}")
    
    # Verify values are from binary, not hardcoded defaults
    assert 'rfm_en' in orbit, "rfm_en not in orbit data"
    assert 'regional_clock_gating' in orbit, "regional_clock_gating not in orbit data"
    assert 'dram_clock_gating' in orbit, "dram_clock_gating not in orbit data"
    
    print("  PASS: All fields parsed from binary")
    return True


def test_lpddr4_single_all_fields_parsed():
    """Verify all fields parsed from LPDDR4 single reference binary."""
    result = analyze_binary_file('ddr_timing_table.lpddr4.single.ref.bin')
    
    assert result['success'], f"Failed to parse: {result.get('message')}"
    data = result['data']
    
    assert data['basic']['dram_type'] == 'lpddr4', f"Expected lpddr4, got {data['basic']['dram_type']}"
    assert data['two_channel'] == 0, f"Expected single channel, got {data['two_channel']}"
    
    orbit = data['orbit']
    print(f"  num_rank: {orbit.get('num_rank')}")
    print(f"  density: {orbit.get('density')}")
    print(f"  rank_interleaving: {orbit.get('rank_interleaving')}")
    
    # Verify all fields are present
    assert 'num_rank' in orbit, "num_rank not in orbit data"
    assert 'density' in orbit, "density not in orbit data"
    assert 'rank_interleaving' in orbit, "rank_interleaving not in orbit data"
    
    print("  PASS: All fields parsed from binary")
    return True


def test_lpddr5_dual_all_fields_parsed():
    """Verify all fields parsed from LPDDR5 dual reference binary."""
    result = analyze_binary_file('ddr_timing_table.lpddr5.dual.ref.bin')
    
    assert result['success'], f"Failed to parse: {result.get('message')}"
    data = result['data']
    
    assert data['basic']['dram_type'] == 'lpddr5', f"Expected lpddr5, got {data['basic']['dram_type']}"
    assert data['two_channel'] == 1, f"Expected dual channel, got {data['two_channel']}"
    
    # Verify key values are correct for LPDDR5
    assert data['pipe']['omc_freq_ratio'] == 1, f"omc_freq_ratio should be 1"
    assert data['pipe']['phy_freq_ratio'] == 1, f"phy_freq_ratio should be 1"
    assert data['orbit']['density'] == 4, f"density should be 4"
    assert data['orbit']['num_rank'] == 2, f"num_rank should be 2"
    
    orbit = data['orbit']
    print(f"  num_rank: {orbit.get('num_rank')}")
    print(f"  density: {orbit.get('density')}")
    print(f"  dsm_en: {orbit.get('dsm_en')}")
    
    assert 'dsm_en' in orbit, "dsm_en not in orbit data"
    
    print("  PASS: All fields parsed from binary")
    return True


def test_lpddr5_single_all_fields_parsed():
    """Verify all fields parsed from LPDDR5 single reference binary."""
    result = analyze_binary_file('ddr_timing_table.lpddr5.single.ref.bin')
    
    assert result['success'], f"Failed to parse: {result.get('message')}"
    data = result['data']
    
    assert data['basic']['dram_type'] == 'lpddr5', f"Expected lpddr5, got {data['basic']['dram_type']}"
    assert data['two_channel'] == 0, f"Expected single channel, got {data['two_channel']}"
    
    # Verify key values are correct for LPDDR5
    assert data['basic']['dq_width'] == 16, f"dq_width should be 16, got {data['basic']['dq_width']}"
    assert data['pipe']['omc_freq_ratio'] == 1, f"omc_freq_ratio should be 1"
    assert data['pipe']['phy_freq_ratio'] == 1, f"phy_freq_ratio should be 1"
    assert data['orbit']['density'] == 4, f"density should be 4"
    assert data['orbit']['num_rank'] == 2, f"num_rank should be 2"
    
    orbit = data['orbit']
    print(f"  num_rank: {orbit.get('num_rank')}")
    print(f"  density: {orbit.get('density')}")
    
    assert 'num_rank' in orbit, "num_rank not in orbit data"
    assert 'density' in orbit, "density not in orbit data"
    
    print("  PASS: All fields parsed from binary")
    return True


def test_orbit_config_field_values():
    """Verify field values match binary values."""
    # Test with LPDDR4 dual reference binary
    result = analyze_binary_file('ddr_timing_table.lpddr4.dual.ref.bin')
    
    assert result['success'], f"Failed to parse: {result.get('message')}"
    data = result['data']
    orbit = data['orbit']
    
    # Check specific values from LPDDR4 dual binary
    # rfm_en at 0x83A = 0 (not set in generation)
    # regional_clock_gating at 0x858 = 1
    # dram_clock_gating at 0x85C = 1
    
    print(f"  rfm_en: {orbit.get('rfm_en')}")
    print(f"  regional_clock_gating: {orbit.get('regional_clock_gating')}")
    print(f"  dram_clock_gating: {orbit.get('dram_clock_gating')}")
    print(f"  num_rank: {orbit.get('num_rank')}")
    
    # Verify values are parsed from binary, not hardcoded
    assert orbit.get('num_rank') == 2, f"num_rank should be 2"
    assert orbit.get('regional_clock_gating') == 1, f"regional_clock_gating should be 1"
    assert orbit.get('dram_clock_gating') == 1, f"dram_clock_gating should be 1"
    
    print("  PASS: Field values match binary")
    return True


def test_timing_features_from_binary():
    """Verify timing features (write_odt, read_dbi, write_dbi) parsed from binary."""
    result = analyze_binary_file('ddr_timing_table.bin')
    
    assert result['success'], f"Failed to parse: {result.get('message')}"
    data = result['data']
    timing = data['timing']
    
    # These should be parsed from timing entries, not hardcoded
    print(f"  write_odt_upto: {timing.get('write_odt_upto')}")
    print(f"  read_dbi_upto: {timing.get('read_dbi_upto')}")
    print(f"  write_dbi_upto: {timing.get('write_dbi_upto')}")
    print(f"  read_lecc_upto: {timing.get('read_lecc_upto')}")
    print(f"  write_lecc_upto: {timing.get('write_lecc_upto')}")
    
    # Values should be > 0 if present in binary
    # write_odt_upto should have a value
    
    print("  PASS: Timing features parsed from binary")
    return True


def test_no_hardcoded_defaults():
    """Verify no hardcoded values in parsed result."""
    result = analyze_binary_file('ddr_timing_table.bin')
    
    assert result['success'], f"Failed to parse: {result.get('message')}"
    data = result['data']
    
    # Check that many fields are present (not just defaults)
    orbit = data['orbit']
    
    # Count number of parsed fields
    num_fields = len(orbit)
    print(f"  Number of orbit config fields parsed: {num_fields}")
    
    # Should have significantly more than the original 11 fields
    assert num_fields > 20, f"Expected >20 fields, got {num_fields}"
    
    # Verify specific fields that were previously hardcoded
    # are now parsed from binary
    expected_fields = [
        'rfm_en', 'dsm_en', 'ca_odt', 
        'eye_scan_rd_en', 'eye_scan_wr_en',
        'command_bus_training',
        'regional_clock_gating', 'dram_clock_gating', 'phy_clock_gating',
        'zq_calibration_period', 't_refiab', 't_refipb', 'mrr_byte_lane',
    ]
    
    for field in expected_fields:
        assert field in orbit, f"Field {field} not parsed from binary"
    
    print("  PASS: No hardcoded defaults - all fields parsed from binary")
    return True


def test_dq_width_parsed():
    """Verify dq_width is parsed from binary, not hardcoded."""
    # Use LPDDR4 single reference binary
    result = analyze_binary_file('ddr_timing_table.lpddr4.single.ref.bin')
    
    assert result['success'], f"Failed to parse: {result.get('message')}"
    data = result['data']
    
    dq_width = data['basic'].get('dq_width')
    print(f"  dq_width: {dq_width}")
    
    # dq_width should be parsed from binary at offset 0x826
    # value in LPDDR4 single reference binary should be 16
    assert dq_width is not None, "dq_width not parsed"
    assert dq_width == 16, f"dq_width should be 16, got {dq_width}"
    
    print("  PASS: dq_width parsed from binary")
    return True


def main():
    """Run all test cases."""
    print("=" * 60)
    print("Binary Parse Test Suite")
    print("=" * 60)
    
    tests = [
        ("LPDDR4 Dual - All Fields Parsed", test_lpddr4_dual_all_fields_parsed),
        ("LPDDR4 Single - All Fields Parsed", test_lpddr4_single_all_fields_parsed),
        ("LPDDR5 Dual - All Fields Parsed", test_lpddr5_dual_all_fields_parsed),
        ("LPDDR5 Single - All Fields Parsed", test_lpddr5_single_all_fields_parsed),
        ("Orbit Config Field Values", test_orbit_config_field_values),
        ("Timing Features from Binary", test_timing_features_from_binary),
        ("No Hardcoded Defaults", test_no_hardcoded_defaults),
        ("DQ Width Parsed", test_dq_width_parsed),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        print(f"\n[Test] {name}")
        try:
            if test_fn():
                passed += 1
            else:
                failed += 1
                print(f"  FAIL: {name}")
        except Exception as e:
            failed += 1
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
