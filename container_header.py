"""F3/F6 — opt-in binary container header and freq-point metadata.

The existing ``ddr_timing_table.bin`` format is a bare concatenation of
the timing entry region and the ``orbit_config`` struct. Consumers
(the driver, the GUI) rely on *implicit* knowledge of which DRAM type
and channel configuration produced it. The F3/F6 plan calls for a small
versioned header that makes this explicit.

Because production consumers still expect the bare layout, this module
is *opt-in* via ``--emit-container``: the generator continues to write
``ddr_timing_table.bin`` unchanged, and additionally writes
``ddr_timing_table.container`` alongside it. Driver coordination can
land later to start consuming the container file.

Header layout (little-endian, 64 bytes, reserved tail zero-filled):

    offset  size  field
    0x00     4    magic = 'DDRT'
    0x04     2    version_major
    0x06     2    version_minor
    0x08     4    dram_type (2=LP4, 3=LP5)
    0x0C     4    two_channel (0/1)
    0x10     4    density_gb
    0x14     4    num_freq_points
    0x18     4    payload_offset (== 0x40)
    0x1C     4    payload_size   (bytes of the bare bin that follows)
    0x20    16    freq_points[0..3] (MHz, little-endian u32, 0 = unused)
    0x30    16    reserved
"""
import struct

MAGIC = b"DDRT"
VERSION_MAJOR = 1
VERSION_MINOR = 0
HEADER_SIZE = 0x40
MAX_FREQS = 4


def _dram_type_code(dram_type):
    return 2 if dram_type == "lpddr4" else 3


def build_header(dram_type, two_channel, density_gb, freq_points, payload_size):
    freqs = list(freq_points)[:MAX_FREQS]
    while len(freqs) < MAX_FREQS:
        freqs.append(0)
    hdr = bytearray(HEADER_SIZE)
    hdr[0:4] = MAGIC
    struct.pack_into("<HH", hdr, 4, VERSION_MAJOR, VERSION_MINOR)
    struct.pack_into("<IIIIII", hdr, 8,
                     _dram_type_code(dram_type),
                     1 if two_channel else 0,
                     int(density_gb),
                     len(freq_points),
                     HEADER_SIZE,
                     int(payload_size))
    struct.pack_into("<IIII", hdr, 0x20, *freqs)
    return bytes(hdr)


def parse_header(data):
    if len(data) < HEADER_SIZE:
        raise ValueError("buffer too short for DDRT header")
    if data[0:4] != MAGIC:
        raise ValueError("bad magic: expected %r, got %r" % (MAGIC, data[0:4]))
    major, minor = struct.unpack_from("<HH", data, 4)
    dram_code, two_ch, density, nfreq, off, psize = struct.unpack_from("<IIIIII", data, 8)
    freqs = list(struct.unpack_from("<IIII", data, 0x20))[:nfreq]
    return {
        "version": (major, minor),
        "dram_type": "lpddr4" if dram_code == 2 else "lpddr5",
        "two_channel": bool(two_ch),
        "density_gb": density,
        "num_freq_points": nfreq,
        "payload_offset": off,
        "payload_size": psize,
        "freq_points": freqs,
    }


def wrap(bin_path, container_path, dram_type, two_channel, density_gb, periods_ps):
    with open(bin_path, "rb") as f:
        payload = f.read()
    # Convert periods (ps) to frequencies (MHz). int(1000000/ps) matches
    # the generator's internal freq_MHz computation.
    freqs = [int(1000000 / p) for p in periods_ps if p]
    hdr = build_header(dram_type, two_channel, density_gb, freqs, len(payload))
    with open(container_path, "wb") as f:
        f.write(hdr)
        f.write(payload)
    return container_path
