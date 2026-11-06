#!/usr/bin/env python3
"""Cross-check GUI timing-table parsing against the real C struct layout.

This is a deliberately independent reference parser: it builds a ctypes
``struct timing_param`` with the same field order/sizes as
``arise2_omc.h`` and reads every entry directly from the binary.  It then
compares the result field-by-field with ``gui.parse_timing_entries()`` --
the parser used by the web UI.

Usage:
    python3 tools/compare_timing_parse.py --bin ddr_timing_table.bin \
        --dram-type lpddr5 [--density 16]
    python3 tools/compare_timing_parse.py --bin ddr_timing_table.bin \
        --dram-type lpddr4 --verbose

Exit code 0 = identical, 1 = mismatch, 2 = cannot parse input.
"""
import argparse
import ctypes
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from gui import parse_timing_entries  # noqa: E402
from orbit_config import EMMC_CM4_TIME_TB_SIZE  # noqa: E402

# Field names in struct timing_param order.
SCALAR_FIELDS = [
    'freq', 't_ck', 'timing_zqcal',
    'timing_param', 'timing_param_derate', 'dfi_timing_param',
    't_rfcab', 't_rfcpb', 't_rfmab', 't_rfmpb', 't_refdpr',
    'tx_pbr2pbr', 't_xsr', 't_xsdll', 't_xs_fast',
    'wck_ratio', 'tlp_resp', 'auto_dqs_clean', 'dll_enable',
    'write_odt', 'nt_odt', 'write_dbi', 'read_dbi', 'wpste', 'rpste',
    'rl', 'wl', 'mr_rl', 'mr_wl', 'mr_wr', 'mr_rtp', 'mr_cal',
    'mr_tccd_l', 'bank_mode', 'wck_fm', 'rdqs_pst_mode', 'rdqs_pst',
    'rdqs_pre', 'wck_pst', 'wck_on', 'read_link_parity',
    'write_link_parity', 't_rtw', 't_wtr_a', 't_wtr', 't_rc',
    'trddata_en',
]

DENSITY_ARRAYS = [
    't_rfcab', 't_rfcpb', 't_rfmab', 't_rfmpb', 't_refdpr',
    'tx_pbr2pbr', 't_xsr', 't_xsdll', 't_xs_fast',
]

U8_FIELDS = [
    'wck_ratio', 'tlp_resp', 'auto_dqs_clean', 'dll_enable',
    'write_odt', 'nt_odt', 'write_dbi', 'read_dbi', 'wpste', 'rpste',
    'rl', 'wl', 'mr_rl', 'mr_wl', 'mr_wr', 'mr_rtp', 'mr_cal',
    'mr_tccd_l', 'bank_mode', 'wck_fm', 'rdqs_pst_mode', 'rdqs_pst',
    'rdqs_pre', 'wck_pst', 'wck_on', 'read_link_parity',
    'write_link_parity', 't_rtw', 't_wtr_a', 't_wtr', 't_rc',
    'trddata_en',
]


def num_densities(dram_type):
    return 10 if dram_type == 'lpddr5' else 7


def entry_size(dram_type):
    n = num_densities(dram_type)
    raw = 0x88 + 9 * n * 2 + 10 + 22
    return (raw + 3) & ~3


def make_timing_struct(dram_type):
    n = num_densities(dram_type)
    fields = [
        ('freq', ctypes.c_uint32),
        ('t_ck', ctypes.c_uint32),
        ('timing_zqcal', ctypes.c_uint32),
        ('timing_param', ctypes.c_uint32 * 21),
        ('timing_param_derate', ctypes.c_uint32 * 2),
        ('dfi_timing_param', ctypes.c_uint32 * 8),
    ]
    for name in DENSITY_ARRAYS:
        fields.append((name, ctypes.c_uint16 * n))
    for name in U8_FIELDS:
        fields.append((name, ctypes.c_uint8))
    cls = type('timing_param_%s' % dram_type, (ctypes.Structure,),
               {'_fields_': fields})
    expected = entry_size(dram_type)
    actual = ctypes.sizeof(cls)
    if actual != expected:
        raise AssertionError("ctypes timing_param size %d != C size %d"
                             % (actual, expected))
    return cls


def _flatten(value):
    if isinstance(value, int):
        return value
    return list(value)


def parse_reference(data, dram_type):
    cls = make_timing_struct(dram_type)
    size = ctypes.sizeof(cls)
    max_entries = EMMC_CM4_TIME_TB_SIZE // size
    entries = []
    for idx in range(max_entries):
        off = idx * size
        if off + size > len(data):
            break
        cfg = cls.from_buffer_copy(data, off)
        if not (10 <= cfg.freq <= 20000 and 100 < cfg.t_ck <= 20000):
            continue
        entries.append((off, cfg))
    return entries


def compare(data, dram_type, density=None, verbose=False):
    """Return a list of human-readable mismatches."""
    ref = parse_reference(data, dram_type)
    parsed = parse_timing_entries(data, dram_type, density=density)
    got = parsed['entries']

    problems = []
    if len(ref) != len(got):
        problems.append("entry count: reference=%d gui=%d"
                        % (len(ref), len(got)))

    if not parsed['density_dependent']:
        problems.append("GUI returned empty density_dependent arrays")

    for i, ((off, cfg), entry) in enumerate(zip(ref, got)):
        # Top-level scalar/array fields.
        for name in SCALAR_FIELDS:
            ref_val = _flatten(getattr(cfg, name))
            gui_val = entry.get(name)
            if name == 'timing_param_derate':
                gui_val = entry.get('timing_derate')
            if gui_val != ref_val:
                problems.append("entry %d @0x%x %s: reference=%r gui=%r"
                                % (i, off, name, ref_val, gui_val))
        # Per-entry density arrays (all nine, every density).
        for name in DENSITY_ARRAYS:
            ref_val = list(getattr(cfg, name))
            gui_val = entry.get(name)
            if gui_val != ref_val:
                problems.append("entry %d @0x%x %s: reference=%r gui=%r"
                                % (i, off, name, ref_val, gui_val))
        if verbose:
            print("entry %d @0x%x: freq=%d t_ck=%d t_rfcab=%r"
                  % (i, off, cfg.freq, cfg.t_ck, list(cfg.t_rfcab)))

    # Selected-density values must come from the first entry.
    if ref:
        n = num_densities(dram_type)
        dens = density if density is not None else 16
        if dram_type == 'lpddr5':
            dens_list = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32]
        else:
            dens_list = [2, 3, 4, 6, 8, 12, 16]
        try:
            idx = dens_list.index(dens)
        except ValueError:
            idx = 0
        first = ref[0][1]
        for name in DENSITY_ARRAYS:
            ref_val = list(getattr(first, name))[idx]
            gui_val = parsed['density_dependent'].get(name)
            if gui_val != ref_val:
                problems.append("density_dependent[%s]@%dGb: reference=%r gui=%r"
                                % (name, dens, ref_val, gui_val))

    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bin', default='ddr_timing_table.bin',
                    help='timing-table image (4 KiB or larger)')
    ap.add_argument('--dram-type', required=True,
                    choices=['lpddr4', 'lpddr5'])
    ap.add_argument('--density', type=int, default=None)
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    if not os.path.exists(args.bin):
        print("ERROR: %s not found" % args.bin, file=sys.stderr)
        return 2
    with open(args.bin, 'rb') as f:
        data = f.read()
    if len(data) < EMMC_CM4_TIME_TB_SIZE:
        print("ERROR: %s is smaller than 0x800" % args.bin, file=sys.stderr)
        return 2

    problems = compare(data, args.dram_type, args.density, args.verbose)
    if problems:
        print("FAIL: %d mismatch(es) in %s" % (len(problems), args.bin))
        for p in problems:
            print("  " + p)
        return 1

    print("OK: %s (%s) - every timing_param field matches"
          % (args.bin, args.dram_type))
    return 0


if __name__ == '__main__':
    sys.exit(main())
