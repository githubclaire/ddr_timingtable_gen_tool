# LP4/LP5 Binary Issues Fix - Complete Plan - 2026-04-10

## Investigation Summary

### 1. DENSITY-DEPENDENT Parameters - ✅ CORRECT
Binary values match GUI parsed values.

---

### 2. THRESHOLD OFFSET BUG - CONFIRMED

**Reference Binary Analysis:**

| Config | gui.py reads | Expected at 0x8DC/0x8E0 | Result |
|--------|-------------|------------------------|-------|
| LP4 Single | @0x8EC=32000, @0x8F0=488000 | ds=1360461824, dp=0 | **WRONG** |
| LP4 Dual | @0x8EC=0, @0x8F0=0 | ds=garbage, dp=garbage | **WRONG** |
| LP5 Single | @0x824=0, @0x828=0 | ds=0, dp=0 | ✓ Correct |

**Root Cause:** gui.py lines 435-436 use WRONG offsets:
- LP4 single: reads 0x8EC/0x8F0 (temp_sensing/t_refipb)
- LP4 dual: reads 0x8EC/0x8F0 (but these happen to be 0)

**Correct Offsets:**
- LP4: Same as LP5 single → ds=0xDC, dp=0xE0
- LP4 dual: Should also be 0xDC/0xE0 (based on struct)

---

### 3. C vs Python Path Binary Generation

| Path | ds_thresh @ 0x8DC | dp_thresh @ 0x8E0 | Status |
|------|-------------------|-------------------|--------|
| C (default) | 0 | 0 | ✓ Correct |
| Python (--orbit-config-use-python) | garbage | 0 | ❌ Wrong |

---

## Fix Required

### Fix gui.py lines 435-436

**From:**
```python
dp_thresh_offset = 0xf0 if is_dual_channel else 0xe0
ds_thresh_offset = 0xec if is_dual_channel else 0xdc
```

**To:**
```python
dp_thresh_offset = 0xe0
ds_thresh_offset = 0xdc
```

These offsets are SAME for all LP4 configs (single and dual).

---

## Verification After Fix

| Config | ds_thresh | dp_thresh |
|--------|----------|-----------|
| LP4 Single | 0 | 0 |
| LP4 Dual | 0 | 0 |
| LP5 Single | 0 | 0 |
| LP5 Dual | 0 | 0 |

All should be 0 (default values).

---

## Implementation Steps

1. Fix gui.py lines 435-436
2. Regenerate reference binaries with C path (default)
3. Verify all 4 configs parse correctly
4. Run test scripts