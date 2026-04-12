#!/usr/bin/env python3
"""
Semantic binary diff (F1).

Given two ddr_timing_table.bin files, identify the (dram_type, two_channel)
combo by matching file size to the ctypes orbit_config struct size, then print
a field-by-field diff of the orbit_config region.

Example output:

    phy_base_addr @ 0x0CC: 0x51160000 -> 0x51180000
    zq_calibration_period @ 0x0E4:        48000 -> 0

Usage:
    python3 tools/bin_diff.py a.bin b.bin
    python3 tools/bin_diff.py --dram-type lpddr5 --two-channel 0 a.bin b.bin
"""
import argparse
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orbit_config import make_orbit_config_class, EMMC_CM4_TIME_TB_SIZE  # noqa: E402


def _identify(size):
    want = size - EMMC_CM4_TIME_TB_SIZE
    for dt in ("lpddr4", "lpddr5"):
        for tc in (False, True):
            if ctypes.sizeof(make_orbit_config_class(dt, tc)) == want:
                return dt, tc
    return None, None


def _read_cfg(path, dram_type, two_channel):
    cls = make_orbit_config_class(dram_type, two_channel)
    cfg = cls()
    with open(path, "rb") as f:
        f.seek(EMMC_CM4_TIME_TB_SIZE)
        f.readinto(cfg)
    return cfg


def _as_scalar_list(value):
    """Return a list of (sub-index path, scalar int) for a ctypes field value."""
    if isinstance(value, int):
        return [((), value)]
    # ctypes arrays
    try:
        out = []
        for i, item in enumerate(value):
            for sub, scalar in _as_scalar_list(item):
                out.append(((i,) + sub, scalar))
        return out
    except TypeError:
        pass
    # Nested Structure
    try:
        out = []
        for name, _ in value._fields_:
            for sub, scalar in _as_scalar_list(getattr(value, name)):
                out.append(((name,) + sub, scalar))
        return out
    except AttributeError:
        return [((), repr(value))]


def diff(a_path, b_path, dram_type=None, two_channel=None):
    a_size = os.path.getsize(a_path)
    b_size = os.path.getsize(b_path)

    if dram_type is None or two_channel is None:
        dt_a, tc_a = _identify(a_size)
        dt_b, tc_b = _identify(b_size)
        if dt_a is None or dt_a != dt_b or tc_a != tc_b:
            print("ERROR: cannot identify matching struct layout for both files",
                  file=sys.stderr)
            print("  %s size=%d layout=%s" % (a_path, a_size, (dt_a, tc_a)),
                  file=sys.stderr)
            print("  %s size=%d layout=%s" % (b_path, b_size, (dt_b, tc_b)),
                  file=sys.stderr)
            return 2
        dram_type, two_channel = dt_a, tc_a

    cls = make_orbit_config_class(dram_type, two_channel)
    a_cfg = _read_cfg(a_path, dram_type, two_channel)
    b_cfg = _read_cfg(b_path, dram_type, two_channel)

    print("# layout: %s %s" % (dram_type, "dual" if two_channel else "single"))
    any_diff = False
    for name, _ in cls._fields_:
        offset = getattr(cls, name).offset
        a_val = getattr(a_cfg, name)
        b_val = getattr(b_cfg, name)
        a_flat = _as_scalar_list(a_val)
        b_flat = _as_scalar_list(b_val)
        for (path, av), (_, bv) in zip(a_flat, b_flat):
            if av == bv:
                continue
            any_diff = True
            ident = name + "".join(
                "[%s]" % (p if isinstance(p, int) else p) for p in path
            )
            print("%-42s @ 0x%04X: %s -> %s" % (ident, offset, av, bv))

    if not any_diff:
        print("# no field-level differences")
    return 0 if not any_diff else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--dram-type", choices=["lpddr4", "lpddr5"])
    ap.add_argument("--two-channel", type=int, choices=[0, 1])
    args = ap.parse_args()
    tc = None if args.two_channel is None else bool(args.two_channel)
    sys.exit(diff(args.a, args.b, args.dram_type, tc))


if __name__ == "__main__":
    main()
