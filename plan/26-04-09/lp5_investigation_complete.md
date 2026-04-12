# LP5 Comprehensive Investigation Report - 2026-04-10

## Root Cause: Why LP4 Works But LP5 Doesn't

### Key Finding
**LP5 binary generation bug**: gen_timing_params uses CONVERTED t_ck for memcfg lookup instead of original t_wck input.

### Explanation
- **LP4**: input t_ck = stored t_ck (NO conversion)
  - memcfg lookup uses correct t_ck value
  - RL values decrease correctly with increasing t_ck

- **LP5**: input t_wck → CONVERTED to t_ck (t_ck = t_wck × wck_ratio)
  - memcfg lookup uses CONVERTED t_ck (WRONG!)
  - Example: Entry 0 input t_wck=314, converted t_ck=1256
  - memcfg looks up 1256ps instead of 314ps → gets wrong read_latency
  - This causes RL values to be completely wrong

### Evidence
```
LP4 Binary (CORRECT):
  Entry 0: t_ck=471, rl=40
  Entry 1: t_ck=938, rl=22  
  Entry 2: t_ck=1631, rl=16
  Entry 3: t_ck=2500, rl=12
  → RL decreases as t_ck increases ✓

LP5 Binary (WRONG):
  Entry 0: t_ck=1256, rl=53
  Entry 1: t_ck=1672, rl=233  ← WRONG! Should be ~20
  Entry 2: t_ck=2224, rl=175  ← WRONG! Should be ~16
  Entry 3: t_ck=5000, rl=78   ← WRONG! Should be ~10
  → RL order is completely wrong!
```

## All Issues Found

### 1. gui.py wck_ratio Offset (WRONG)
- **Current**: Reading at offset 0x88 (garbage: 104, 78, 59, 26)
- **Correct**: Reading at offset 0x13c (actual: 4, 4, 4, 2)

### 2. Period Conversion (WRONG)
- **Current**: Uses fixed wck_ratio=4
- **Correct**: Use per-entry wck_ratio from offset 0x13c

### 3. gen_timing_params RL/WL Bug (BINARY BUG)
- Root cause: Uses converted t_ck for memcfg lookup instead of t_wck
- This affects: rl, wl, and related timing params

### 4. Analysis Modal Display
- Shows wrong wck_ratio (from wrong offset)
- Should show per-entry wck_ratio in table

### 5. Density Dependent Params (WRONG OFFSETS)
- **Current**: Reading at offset 0x80 (LP4 offset)
- **Correct for LP5**: Should read at offset 0x88 (within entry)
- Issue: LP5 density arrays are WITHIN each entry, not at file level
- Also: LP5 has 10 densities vs LP4 has 7

### 6. Density Selection (WRONG)
- **Current**: Reads from wrong orbit offset (0x1C)
- **Issue**: density_index = density - 1 logic doesn't match actual array

## Files That Need Fixing

| File | Issue | Priority |
|------|-------|-----------|
| gen_timing_params | Use t_wck for memcfg lookup, not converted t_ck | HIGH |
| gui.py | Fix wck_ratio offset (0x88→0x138) | HIGH |
| gui.py | Fix period conversion (use per-entry wck_ratio) | HIGH |
| gui.py | Fix density array offsets for LP5 (0x80→0x88) | HIGH |
| gui.py | Fix density index calculation | HIGH |
| templates/gui.html | Show per-entry wck_ratio in analysis modal | MEDIUM |

## Why LP4 Works (For Reference)

1. No wck_ratio conversion - input = stored
2. Correct offset for common params (0x106)
3. Correct offset for density arrays (0x80)
4. Correct density parsing

## Notes
- The gui.py parsing is correct in reading what's IN the binary
- The binary ITSELF is wrong for LP5 due to gen_timing_params bug
- LP4 works because it has no wck conversion step