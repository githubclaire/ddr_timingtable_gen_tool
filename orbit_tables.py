"""
Phase 2 — canonical source of truth for orbit_config lookup tables.

This module is the *only* place in the repo where density codes,
MR defaults, and any other orbit_config constant table lives. The C side
(orbit_tables.gen.h) is mechanically generated from this file by
``tools/gen_orbit_tables.py``, and a CI test asserts the checked-in header
is in sync with this Python source.

Adding a new density code or MR default:

    1. Edit this file.
    2. Run ``python3 tools/gen_orbit_tables.py`` to regenerate
       ``orbit_tables.gen.h``.
    3. Run ``python3 -m unittest tests/test_orbit_tables_gen.py`` to confirm
       both sides agree.
    4. Commit all three.
"""

# density (Gb) -> density_code used by orbit_config.density_code
DENSITY_CODES = [
    (1, 0),
    (2, 1),
    (3, 2),
    (4, 3),
    (6, 4),
    (8, 5),
    (12, 6),
    (16, 7),
    (24, 8),
    (32, 9),
]

DENSITY_CODE_MAP = dict(DENSITY_CODES)


def get_density_code(density, default=1):
    """Return the density code for ``density`` Gb (defaulting to DENSITY_2)."""
    return DENSITY_CODE_MAP.get(density, default)
