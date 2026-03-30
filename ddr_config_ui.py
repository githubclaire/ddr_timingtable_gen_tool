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
# No imports needed from gen_timing_params since we call it via subprocess



def parse_args():
    """Parse command line arguments, combining timing and orbit config parameters."""
    enable_opts = ('lpddr4-byte-mode', 'additive-latency')

    parser = ArgumentParser(description='Generate DDR timing table and orbit configuration binary.')
    
    # Required arguments from gen_timing_params
    parser.add_argument('-d', '--dram-type', required=True, choices=('lpddr4', 'lpddr5'), help='target memory type')
    parser.add_argument('--densities', type=str, nargs='+', help='list of target densities as Gb. It should be 1 in case of DDR3.')
    parser.add_argument('--phy-name', type=str, help='name of phy')
    parser.add_argument('--project-name', type=str, help='name of project')
    parser.add_argument('-l', '--langugage', choices=('c',), default='c', help='target language')
    parser.add_argument('-o', '--output', default='orbit_timing_params.c', help='output file name')
    parser.add_argument('--cpipe-depth', default=0, type=int, help='pipe line differences between command channel')
    parser.add_argument('--dpipe-depth', default=0, type=int, help='pipe line differences between data channel')
    parser.add_argument('-s', '--speed-bin', type=str, help='speed-bin of DDR3 or DDR4 dram devices')
    parser.add_argument('-w', '--dq-width', default=16, type=int, choices=[4, 8, 16, 32], help='DQ width of a die (not a package). Set 8 when at least one x8 die is used in a LPDDR4 or LPDDR5 package')
    parser.add_argument('-e', '--enable', default=[], type=str, action='append', choices=enable_opts, help='enable additional timing options')
    parser.add_argument('--wire-length', default=0, type=float, help='largest length of DQ and DQS wires from PHY I/O to DRAM I/O')
    parser.add_argument('--omc-freq-ratio', default=2, type=int, help='Clock ratio of dfi_clk and memory clock in terms of OMC')
    parser.add_argument('--phy-freq-ratio', default=2, type=int, help='Clock ratio of dfi_clk and memory clock in terms of PHY')
    parser.add_argument('--meso-synchronizer', action='store_true', help='meso-synchronizer is implemented')
    parser.add_argument('--pl-en', default=0, type=int, help='parity latency enable')
    parser.add_argument('--min-dram-tck', default=314, type=int, help='Perioid of maximum operating frequency (as pico-seconds) / tWCK in case of LPDDR5')
    parser.add_argument('periods', type=int, nargs='+', help='list of target tCK of DRAM (as pico-seconds) / tWCK in case of LPDDR5')

    timing_grp = parser.add_argument_group(title="Timing features", description="Options can be enabled based on frequency. tWCK for LPDDR5 and tCK for others")
    timing_grp.add_argument('--write-odt-upto', type=int, default=0, help='maximum tCK/tWCK (ps) to enable write ODT')
    timing_grp.add_argument('--read-dbi-upto', type=int, default=0, help='maximum tCK/tWCK (ps) to enable read DBI')
    timing_grp.add_argument('--write-dbi-upto', type=int, default=0, help='maximum tCK/tWCK (ps) to enable write DBI')
    timing_grp.add_argument('--read-lecc-upto', type=int, default=0, help='maximum tCK/tWCK (ps) to enable read link ECC')
    timing_grp.add_argument('--write-lecc-upto', type=int, default=0, help='maximum tCK/tWCK (ps) to enable write link ECC')
    timing_grp.add_argument('--emulation', action='store_true', help='Setting emulation sequence')

    ddr4_grp = parser.add_argument_group(title="DDR4 options", description="Options for DDR4")
    ddr4_grp.add_argument('--geardown-upto', action='store_true', help='maximum tCK (ps) to enable geardown mode')

    lp4_grp = parser.add_argument_group(title="LPDDR4 options", description="Options for LPDDR4")
    lp4_grp.add_argument('--variable-trrd', action='store_true', help='use tRRD of 10 ns for LPDDR4-4267 devices when tCK is 535 ps or higher')
    lp4_grp.add_argument('--wdqs-ctrl-mode', type=int, default=0, help='set WDQS control mode')
    lp4_grp.add_argument('--txsr-as-1st-ed', action='store_true', help='use SRX to ACT/REF commands constraints based on 1st edition')
    lp4_grp.add_argument('--rpste-upto', type=int, default=0, help='maximum tCK (ps) to enable extended read post-amble')
    lp4_grp.add_argument('--wpste-upto', type=int, default=0, help='maximum tCK (ps) to enable extended write post-amble')

    lp5_grp = parser.add_argument_group(title="LPDDR5 options", description="Options for LPDDR5")
    lp5_grp.add_argument('--nt-odt-upto', type=int, default=0, help='maximum tWCK (ps) to enable NT-ODT')
    lp5_grp.add_argument('--enhanced-nt-odt', action='store_true', help='devices support the enhanced NT-ODT')
    lp5_grp.add_argument('--bg-mode-upto', type=int, default=625, help='maximum tWCK (ps) to enable bank-group mode')
    lp5_grp.add_argument('--wck-always-on-from', type=int, default=1000000, help='minimum tWCK (ps) to enable WCK always-on mode')
    lp5_grp.add_argument('--wck-always-on-upto', type=int, default=1000000, help='maximum tWCK (ps) to enable WCK always-on mode')
    lp5_grp.add_argument('--wck-1to4-upto', type=int, default=625, help='maximum tWCK (ps) to enable WCK 1:4 mode')
    lp5_grp.add_argument('--wck-hf-upto', type=int, default=624, help='maximum tWCK (ps) to enable WCK high-frequency mode')
    lp5_grp.add_argument('--wck-pst1-upto', type=int, default=0, help='maximum tWCK (ps) to set WCK PST as 4.5*tWCK')
    lp5_grp.add_argument('--wck-pst2-upto', type=int, default=0, help='maximum tWCK (ps) to set WCK PST as 6.5*tWCK')
    lp5_grp.add_argument('--rdqs-pst1-upto', type=int, default=0, help='maximum tWCK (ps) to set RDQS PST as 2.5*tWCK')
    lp5_grp.add_argument('--rdqs-pst2-upto', type=int, default=0, help='maximum tWCK (ps) to set RDQS PST as 4.5*tWCK')

    orbit_grp = parser.add_argument_group(title="Orbit configuration", description="Parameters for orbit_config binary generation")
    orbit_grp.add_argument('--two-channel', action='store_true', help='Enable two-channel mode (DDR_TWO_CHANNEL=1)')
    orbit_grp.add_argument('--macro-ddr-type', type=int, help='Override DDR_TYPE macro value (2 for LPDDR4, other for LPDDR5)')
    orbit_grp.add_argument('--orbit-byte-mode', type=int, default=0, choices=[0,1], help='Byte mode for LPDDR4 (0=x16, 1=x8)')
    orbit_grp.add_argument('--orbit-mixed', type=int, default=0, choices=[0,1], help='Mixed rank density flag')
    orbit_grp.add_argument('--orbit-rank-interleaving', type=int, default=1, choices=[0,1], help='Rank interleaving enable')
    orbit_grp.add_argument('--orbit-num-rank', type=int, default=2, choices=[1,2], help='Number of ranks (max 2)')
    orbit_grp.add_argument('--orbit-reboot-with-mrw', type=int, default=0, choices=[0,1], help='Reboot with MRW')
    orbit_grp.add_argument('--orbit-rfm-en', type=int, default=0, choices=[0,1], help='RFM enable (LPDDR4/LPDDR5)')
    orbit_grp.add_argument('--orbit-dsm-en', type=int, default=0, choices=[0,1], help='DSM enable (LPDDR5 Deep Sleep Mode)')
    orbit_grp.add_argument('--orbit-ca-odt', type=int, default=0, choices=[0,1], help='CA ODT enable')
    orbit_grp.add_argument('--orbit-config-json', type=str, help='JSON file with orbit_config field overrides')
    orbit_grp.add_argument('--orbit-config-use-python', action='store_true', help='Use Python implementation instead of gen_ddr_config')

    args = parser.parse_args()

    # Convert densities from strings to integers
    if args.densities:
        args.densities = [int(d) for d in args.densities]

    # Determine macro_ddr_type if not provided
    if args.macro_ddr_type is None:
        # Use 2 for LPDDR4, 5 for LPDDR5 (any value != 2)
        if args.dram_type == 'lpddr4':
            args.macro_ddr_type = 2
        else:
            args.macro_ddr_type = 5

    for opt in enable_opts:
        name = opt.replace('-', '_')
        if opt in args.enable:
            setattr(args, name, True)
        else:
            setattr(args, name, False)

    # lpddr4 write ODT
    if args.dram_type == "lpddr4" and args.write_odt_upto > 1249:
        print("[Info] write-odt-upto({}) value is overrided as 1250 following the limitation of the LPDDR4 SDRAM.".format(args.write_odt_upto))
        args.write_odt_upto = 1249

    return args

def build_command_line_args(args, original_args):
    """Build command line arguments list for gen_timing_params."""
    cmd_args = list(original_args)  # start with original arguments
    
    # Helper to add argument if not already present
    def add_if_not_present(arg_name, arg_value=None):
        if arg_name in cmd_args:
            return
        cmd_args.append(arg_name)
        if arg_value is not None:
            cmd_args.append(str(arg_value))
    
    # Map wrapper orbit config arguments to gen_timing_params arguments
    # Add --two-channel if enabled
    if args.two_channel:
        add_if_not_present('--two-channel')
    
    # Add orbit-specific arguments if not already present
    if args.orbit_byte_mode != 0:  # default is 0, only add if non-default
        add_if_not_present('--orbit-byte-mode', args.orbit_byte_mode)
    
    if args.orbit_mixed != 0:  # default is 0
        add_if_not_present('--orbit-mixed', args.orbit_mixed)
    
    if args.orbit_rank_interleaving != 1:  # default is 1
        add_if_not_present('--orbit-rank-interleaving', args.orbit_rank_interleaving)
    
    if args.orbit_num_rank != 2:  # default is 2
        add_if_not_present('--orbit-num-rank', args.orbit_num_rank)
    
    if args.orbit_reboot_with_mrw != 0:  # default is 0
        add_if_not_present('--orbit-reboot-with-mrw', args.orbit_reboot_with_mrw)
    
    if args.orbit_rfm_en != 0:  # default is 0
        add_if_not_present('--orbit-rfm-en', args.orbit_rfm_en)
    
    if args.orbit_dsm_en != 0:  # default is 0
        add_if_not_present('--orbit-dsm-en', args.orbit_dsm_en)
    
    if args.orbit_ca_odt != 0:  # default is 0
        add_if_not_present('--orbit-ca-odt', args.orbit_ca_odt)
    
    if args.orbit_config_json:
        add_if_not_present('--orbit-config-json', args.orbit_config_json)
    
    # Optionally, user can add --orbit-config-use-python to use Python implementation
    # (default is C implementation via gen_ddr_config)
    # add_if_not_present('--orbit-config-use-python')
    
    return cmd_args

def main():
    args = parse_args()
    original_args = sys.argv[1:]
    
    cmd_args = build_command_line_args(args, original_args)
    
    # Step 1: Run gen_timing_params with all arguments
    cmd = [sys.executable, 'gen_timing_params'] + cmd_args
    print("Running: {}".format(' '.join(cmd)))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)
    
    print("Successfully generated ddr_timing_table.bin with timing and orbit config.")
    print("Note: orbit configuration generated using gen_timing_params (Python or C based on flags).")

if __name__ == '__main__':
    main()