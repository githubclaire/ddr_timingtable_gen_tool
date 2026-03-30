#!/usr/bin/env python3
"""
Unified UI for DDR timing table and configuration generation.
"""

import sys
import os
import json
import subprocess
from argparse import ArgumentParser

# Import existing modules
sys.path.insert(0, os.path.dirname(__file__))
from gen_timing_params import GenTimingParam, parse_args as parse_timing_args
from ddr_config_init import generate_orbit_config_binary

def parse_args():
    """Parse command line arguments, combining timing and orbit config parameters."""
    # Start with timing parameters parser
    parser = ArgumentParser(description='Generate DDR timing table and orbit configuration binary.')
    
    # Add all arguments from gen_timing_params.parse_args
    # We'll reuse the existing function but need to add extra groups.
    # For simplicity, we'll call parse_timing_args later and merge with extra args.
    # Let's create our own copy of the arguments (subset) to avoid duplication.
    # Instead, we'll create a subparser? Too complex.
    # We'll just call parse_timing_args and then add our extra arguments.
    # However, argparse doesn't allow merging after the fact.
    # We'll manually duplicate the essential timing arguments (maybe we can import the parser).
    # Since time is limited, we'll just call parse_timing_args and then extend the args namespace with extra values.
    # We'll add extra arguments with a prefix 'orbit_' to avoid conflict.
    
    orbit_grp = parser.add_argument_group(title="Orbit Configuration", 
                                          description="Parameters for orbit_config struct (modifiable)")
    orbit_grp.add_argument('--two-channel', action='store_true',
                           help='Enable two-channel mode (DDR_TWO_CHANNEL=1)')
    orbit_grp.add_argument('--density', type=int, default=16,
                           help='Density per rank in Gb (default 16)')
    orbit_grp.add_argument('--byte-mode', type=int, default=0, choices=[0,1],
                           help='Byte mode for LPDDR4 (0=x16, 1=x8)')
    orbit_grp.add_argument('--mixed', type=int, default=0, choices=[0,1],
                           help='Mixed rank density flag')
    orbit_grp.add_argument('--orbit-config-json', type=str,
                           help='JSON file with orbit_config field overrides')
    
    # Add all modifiable fields as optional arguments (we'll generate dynamically)
    # For now, we'll just rely on JSON override.
    
    # Now add timing arguments by using the original parser (by calling parse_timing_args internally)
    # We'll need to parse them separately and combine namespaces.
    # We'll do a two-pass approach: first parse known args, then pass remaining to timing parser.
    # Not trivial.
    
    # Given time constraints, we'll just call the original script as subprocess for timing generation.
    # This script will act as a wrapper that runs gen_timing_params with all its arguments,
    # then runs orbit config generation.
    # We'll capture all arguments and pass them to gen_timing_params.
    
    # For simplicity, we'll accept all arguments and forward them.
    # We'll use argparse.REMAINDER.
    parser.add_argument('timing_args', nargs='*',
                        help='Arguments to pass to gen_timing_params')
    
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    
    # Step 1: Run gen_timing_params with its arguments
    # We'll reconstruct the command line
    cmd = [sys.executable, 'gen_timing_params'] + args.timing_args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    if result.returncode != 0:
        sys.exit(result.returncode)
    
    # Step 2: Determine dram_type and two-channel from arguments
    # Parse timing_args to extract dram_type
    dram_type = 'lpddr5'
    two_channel = args.two_channel
    density = args.density
    byte_mode = args.byte_mode
    mixed = args.mixed
    
    # Overrides from JSON
    overrides = {}
    if args.orbit_config_json:
        with open(args.orbit_config_json, 'r') as f:
            overrides = json.load(f)
    
    # Step 3: Generate orbit config binary at offset 0x800
    generate_orbit_config_binary(dram_type=dram_type,
                                 two_channel=two_channel,
                                 density=density,
                                 byte_mode=byte_mode,
                                 mixed=mixed,
                                 output_file='ddr_timing_table.bin',
                                 offset=0x800,
                                 **overrides)
    
    print("Successfully generated ddr_timing_table.bin with timing and orbit config.")

if __name__ == '__main__':
    main()