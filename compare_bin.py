#!/usr/bin/env python3
import struct
import os
from orbit_config import orbit_config
from ddr_config_init import ddr_config_init

def read_c_binary():
    """Read orbit_config from ddr_timing_table.bin at offset 0x800."""
    with open('ddr_timing_table.bin', 'rb') as f:
        f.seek(0x800)
        data = f.read()
    return data

def generate_python_binary():
    """Generate orbit_config binary using Python implementation."""
    cfg = orbit_config()
    # Initialize with same parameters as C (LPDDR4, two-channel, density=16)
    ddr_config_init(cfg, dram_type='lpddr4', two_channel=True, density=16,
                    byte_mode=0, mixed=0)
    # Convert to bytes
    return bytes(cfg)

def compare_binaries(c_data, py_data):
    print(f"C binary size: {len(c_data)} bytes")
    print(f"Python binary size: {len(py_data)} bytes")
    
    if len(c_data) != len(py_data):
        print("Size mismatch!")
        # Pad or truncate for comparison
        min_len = min(len(c_data), len(py_data))
        c_data = c_data[:min_len]
        py_data = py_data[:min_len]
    
    mismatches = []
    for i in range(len(c_data)):
        if c_data[i] != py_data[i]:
            mismatches.append((i, c_data[i], py_data[i]))
            if len(mismatches) > 20:
                mismatches.append(("...", "...", "..."))
                break
    
    if mismatches:
        print(f"Found {len(mismatches)} byte mismatches:")
        for i, c_byte, py_byte in mismatches[:20]:
            print(f"  Offset 0x{i:04x}: C=0x{c_byte:02x}, Python=0x{py_byte:02x}")
    else:
        print("Binaries match!")
    
    # Also print first 64 bytes for visual comparison
    print("\nFirst 64 bytes (C vs Python):")
    for i in range(0, min(64, len(c_data)), 16):
        c_line = ' '.join(f'{b:02x}' for b in c_data[i:i+16])
        py_line = ' '.join(f'{b:02x}' for b in py_data[i:i+16])
        print(f"C  {i:04x}: {c_line}")
        print(f"Py {i:04x}: {py_line}")
        if c_line != py_line:
            print("   ^ mismatch")

if __name__ == '__main__':
    c_data = read_c_binary()
    py_data = generate_python_binary()
    compare_binaries(c_data, py_data)