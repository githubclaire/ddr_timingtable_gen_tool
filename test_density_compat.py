#!/usr/bin/env python3
import sys
import os
import subprocess
import tempfile
import struct

def test_density_compatibility(dram_type, densities):
    print(f"\n=== Testing {dram_type.upper()} with densities {densities} ===")
    
    # Clean up
    for f in ['ddr_timing_table.bin', 'ddr_timing_table.c_ref.bin', 'orbit_init_gen.h']:
        if os.path.exists(f):
            os.remove(f)
    
    # Build command
    cmd = [
        sys.executable, 'gen_timing_params',
        '--dram-type', dram_type,
        '--phy-name', 'sphy-v9r8',
        '--speed-bin', '4266' if dram_type == 'lpddr4' else '6400',
        '--dq-width', '16',
        '--densities'
    ] + [str(d) for d in densities]
    
    # Add common args
    if dram_type == 'lpddr4':
        cmd += [
            '--wdqs-ctrl-mode', '1',
            '--wire-length', '10',
            '--read-dbi-upto', '10000',
            '--write-dbi-upto', '10000',
            '--write-odt-upto', '1250',
            '--cpipe-depth', '1',
            '--dpipe-depth', '1',
            '--txsr-as-1st-ed',
            '--variable-trrd',
            '--orbit-config-use-python',
            '471', '938', '1631', '2500'
        ]
    else:
        cmd += [
            '--wire-length', '10',
            '--read-dbi-upto', '10000',
            '--write-dbi-upto', '10000',
            '--write-lecc-upto', '625',
            '--write-odt-upto', '10000',
            '--cpipe-depth', '1',
            '--dpipe-depth', '1',
            '--omc-freq-ratio', '1',
            '--phy-freq-ratio', '1',
            '--wck-1to4-upto', '625',
            '--wck-always-on-from', '0',
            '--wck-always-on-upto', '314',
            '--orbit-config-use-python',
            '314', '418', '556', '2500'
        ]
    
    print("Running Python generation...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Python generation failed: {result.stderr}")
        return False
    
    # Read Python binary
    if not os.path.exists('ddr_timing_table.bin'):
        print("Python binary not generated")
        return False
    
    py_size = os.path.getsize('ddr_timing_table.bin')
    print(f"Python binary size: {py_size}")
    
    # Read density and density_code from Python binary
    # First determine offsets based on DRAM type
    if dram_type == 'lpddr4':
        density_offset = 0x1c
        density_code_offset = 0x78
    else:  # lpddr5
        density_offset = 0x24
        density_code_offset = 0x80
    
    with open('ddr_timing_table.bin', 'rb') as f:
        f.seek(0x800 + density_offset)
        py_density = struct.unpack('<H', f.read(2))[0]
        
        f.seek(0x800 + density_code_offset)
        py_density_code = struct.unpack('<I', f.read(4))[0]
    
    print(f"Python: density={py_density}, density_code={py_density_code}")
    
    # Now generate C reference
    print("\nGenerating C reference...")
    
    # First need orbit_init_gen.h from Python generation
    if not os.path.exists('orbit_init_gen.h'):
        print("orbit_init_gen.h not found")
        return False
    
    # Determine DDR_TYPE value
    ddr_type_val = 2 if dram_type == 'lpddr4' else 5
    density = densities[0]
    
    # Run gen_ddr_config for single channel
    cmd_c = [sys.executable, 'gen_ddr_config', str(ddr_type_val), '0', '--density', str(density)]
    result = subprocess.run(cmd_c, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"C generation failed: {result.stderr}")
        return False
    
    if not os.path.exists('ddr_timing_table.bin'):
        print("C binary not generated")
        return False
    
    c_size = os.path.getsize('ddr_timing_table.bin')
    print(f"C binary size: {c_size}")
    
    # Read C binary
    with open('ddr_timing_table.bin', 'rb') as f:
        f.seek(0x800 + density_offset)
        c_density = struct.unpack('<H', f.read(2))[0]
        
        f.seek(0x800 + density_code_offset)
        c_density_code = struct.unpack('<I', f.read(4))[0]
    
    print(f"C: density={c_density}, density_code={c_density_code}")
    
    # Compare
    match = (py_density == c_density) and (py_density_code == c_density_code)
    print(f"Match: {match}")
    
    if not match:
        print(f"MISMATCH: density {py_density} vs {c_density}, density_code {py_density_code} vs {c_density_code}")
    
    return match

# Run tests
if __name__ == '__main__':
    tests = [
        ('lpddr4', [2]),
        ('lpddr4', [3]),
        ('lpddr4', [4]),
        ('lpddr4', [6]),
        ('lpddr4', [8]),
        ('lpddr4', [12]),
        ('lpddr4', [16]),
        ('lpddr5', [1]),
        ('lpddr5', [2]),
        ('lpddr5', [3]),
        ('lpddr5', [4]),
        ('lpddr5', [6]),
        ('lpddr5', [8]),
        ('lpddr5', [12]),
        ('lpddr5', [16]),
        ('lpddr5', [24]),
        ('lpddr5', [32]),
    ]
    
    all_pass = True
    for dram_type, densities in tests:
        if not test_density_compatibility(dram_type, densities):
            all_pass = False
    
    if all_pass:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)