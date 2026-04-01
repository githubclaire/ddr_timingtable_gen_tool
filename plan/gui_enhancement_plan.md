# GUI Enhancement Plan

## Date: 2026-04-01

---

## 1. Density Support

### Supported Densities (from library config files)

**LPDDR4** (lpddr4_config.py line 28):
```python
self.ref.densities = (2, 3, 4, 6, 8, 12, 16)
```
- Supported: 2, 3, 4, 6, 8, 12, 16
- NOT supported: 1, 32

**LPDDR5** (lpddr5_config.py line 61):
```python
self.ref.densities = (1, 2, 3, 4, 6, 8, 12, 16, 24, 32)
```
- Supported: 1, 2, 3, 4, 6, 8, 12, 16, 24, 32

---

## 2. Timing Field Valid Ranges

### Calculation Method
- For ps→MHz: `MHz = 1000000 / ps`
- Valid MHz range = `[1000000/max_ps, 1000000/min_ps]`

### Valid Ranges Table

| Field | ps Range | MHz Range | DDR Type |
|-------|----------|-----------|----------|
| dram-tck | 300-5000 | 200-3333 | Both |
| min-dram-tck | 200-3000 | 333-5000 | Both |
| write-odt-upto | 1250-10000 | 100-800 | LPDDR4 (max 1250) |
| write-odt-upto | 1000-10000 | 100-1000 | LPDDR5 |
| read-dbi-upto | 1000-10000 | 100-1000 | Both |
| write-dbi-upto | 1000-10000 | 100-1000 | Both |
| read-lecc-upto | 500-2500 | 400-2000 | Both |
| write-lecc-upto | 500-2500 | 400-2000 | Both |
| wck-1to4-upto | 625-2500 | 400-1600 | LPDDR5 |
| wck-always-on-upto | 314-1256 | 796-3185 | LPDDR5 |
| dfs-lvl-t-ck-0 | 500-3000 | 333-2000 | Both |
| dfs-lvl-t-ck-1 | 500-3000 | 333-2000 | Both |
| dfs-lvl-t-ck-2 | 500-5000 | 200-2000 | Both |

---

## 3. Implementation Tasks

### 3.1 Density Dropdown Update
- When DDR type changes, update density field validation
- Show tooltip with valid densities
- Clamp current value to valid range

### 3.2 Timing Field Tooltips
- Add title attribute to all timing field labels
- Show usage and valid range on mouse hover

### 3.3 Input Validation
- Block generation if invalid values
- Show error message with valid range

### 3.4 Test Script Updates
- Fix densities: LPDDR4 [2,3,4,6,8,12,16], LPDDR5 [1,2,3,4,6,8,12,16,24,32]
- Add progress prints
- Randomize test values (10 iterations per field)

---

## 4. Files to Modify

| # | File | Changes |
|---|------|---------|
| 1 | templates/gui.html | Density update, tooltips, validation |
| 2 | test_gui_params.py | Fix densities, add progress, randomize |
| 3 | plan/gui_enhancement_plan.md | This plan |
| 4 | reports/known_limitations.md | Document limitations |
| 5 | reports/test_script_logic.md | Document test logic |

---

## 5. Implementation Order

1. Save plan to ./plan/gui_enhancement_plan.md
2. Implement density dropdown update in gui.html
3. Add tooltips for timing fields
4. Add input validation
5. Fix test densities in test_gui_params.py
6. Add progress prints
7. Randomize test values
8. Create documentation
