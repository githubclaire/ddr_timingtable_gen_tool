# Known Limitations

## Density Support

### LPDDR4
Supported densities: **2, 3, 4, 6, 8, 12, 16** Gb

Not supported: 1, 32 Gb

Source: `lpddr4_config.py` line 28

### LPDDR5
Supported densities: **1, 2, 3, 4, 6, 8, 12, 16, 24, 32** Gb

All densities supported in library.

Source: `lpddr5_config.py` line 61

## WCK Specification

### wck-always-on-from
This field has a special constraint: it must always be 0. Setting non-zero values may cause unexpected behavior in timing table generation.

### wck-1to4-upto
Valid range: 625-2500 ps

## Input Validation Ranges

Timing field valid ranges (in picoseconds):

| Field | Min (ps) | Max (ps) |
|-------|----------|----------|
| dram-tck | 300 | 5000 |
| min-dram-tck | 200 | 3000 |
| write-odt-upto | 1250 | 10000 |
| read-dbi-upto | 1000 | 10000 |
| write-dbi-upto | 1000 | 10000 |
| read-lecc-upto | 500 | 2500 |
| write-lecc-upto | 500 | 2500 |
| wck-1to4-upto | 625 | 2500 |
| wck-always-on-upto | 314 | 1256 |
| dfs-lvl-t-ck-0 | 500 | 3000 |
| dfs-lvl-t-ck-1 | 500 | 3000 |
| dfs-lvl-t-ck-2 | 500 | 5000 |

Note: Ranges computed from MHz = 1000000/ps formula.
