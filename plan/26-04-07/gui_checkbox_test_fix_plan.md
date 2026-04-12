# GUI Checkbox Integration Test - Fix Plan

## Consolidated Implementation Plan

### Part 1: Fix test_gui_checkbox_integration.py

| # | Issue | Location | Fix |
|---|-------|----------|-----|
| 1a | Test A6 only tests first 3 threshold values | Line 242 | Remove `[:3]` slice - test all 5 values |
| 1b | Test B1 only checks first 10 fields | Line 291 | Check all CHECKBOX_FIELDS |
| 1c | No test for all-unchecked display case | Test B section | Add Test B3: verify unchecked = unchecked |

### Part 2: Fix test_random_value_flow.py

| # | Issue | Location | Fix |
|---|-------|----------|-----|
| 2a | Missing threshold fields in numeric_tests | Lines 87-95 | Add `dynamic_power_down_threshold`, `dynamic_self_refresh_threshold` |
| 2b | Missing dsm_en in checkboxes | Line 53 | Add `dsm_en` to checkbox list |
| 2c | No zero value test for thresholds | Part B | Ensure 0 is tested for threshold fields |
| 2d | Only tests single config | Line 62 | Add tests for LP4 Dual, LP5 Single, LP5 Dual |

### Part 3: Fix gui.py (Bug Fix)

| # | Issue | Location | Fix |
|---|-------|----------|-----|
| 3a | regional_clock_gating wrong default | Line 439 | Change default from 1 to 0 |
| 3b | dram_clock_gating wrong default | Line 441 | Change default from 1 to 0 |

### Part 4: Run Verification Tests

After fixes, run:
- `python3 test_gui_checkbox_integration.py`
- `python3 test_random_value_flow.py`
- `python3 test_checkbox_flow.py`