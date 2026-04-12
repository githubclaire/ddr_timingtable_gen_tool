#!/usr/bin/env python3
"""
Dump orbit_config ctypes struct layout.

Prints one line per field:
    <field_name> <offset>
followed by a final:
    sizeof <total_size>

Output is deterministic and can be diff'd against the C-side dumper in
tools/dump_struct_layout.c to detect layout drift between Python and C.
"""
import argparse
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orbit_config import make_orbit_config_class  # noqa: E402


def dump(dram_type, two_channel, stream=sys.stdout):
    cls = make_orbit_config_class(dram_type, two_channel)
    for name, _ in cls._fields_:
        offset = getattr(cls, name).offset
        stream.write("%s %d\n" % (name, offset))
    stream.write("sizeof %d\n" % ctypes.sizeof(cls))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dram-type", required=True,
                    help="lpddr4|lpddr5 or numeric 2|3")
    ap.add_argument("--two-channel", required=True, type=int, choices=[0, 1])
    args = ap.parse_args()

    dt = args.dram_type
    if dt in ("2", "lp4", "lpddr4"):
        dt = "lpddr4"
    elif dt in ("3", "lp5", "lpddr5"):
        dt = "lpddr5"
    else:
        ap.error("unknown --dram-type %r" % args.dram_type)

    dump(dt, bool(args.two_channel))


if __name__ == "__main__":
    main()
