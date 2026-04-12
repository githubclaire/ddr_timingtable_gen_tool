# Plan: Dynamic Parameter Extraction for Reference Binary Test

## Date: 2026-04-01

---

## Problem

Reference binary comparison test fails because:
- GUI test uses explicit `omc-freq-ratio: 1, phy-freq-ratio: 1`
- Shell script uses CLI defaults (omc-freq-ratio: 2, phy-freq-ratio: 2)
- This causes timing table mismatches at offsets 136-147

---

## Solution: Dynamic Parameter Extraction

### Approach
1. Generate reference binary via CLI shell script (already exists)
2. Load binary via GUI /analyze endpoint - extracts parameters GUI would use
3. Use those extracted params to generate binary via GUI
4. Compare binaries - should match exactly since they use same params

### Implementation Steps

#### Step 1: Add Helper Function
**Function:** `convert_analyze_to_generate_params()`

Converts analyze result to params that can be used by /generate endpoint.

#### Step 2: Update test_reference_binaries()
**File:** `test_gui_params.py` lines 438-512

New logic:
```python
def test_reference_binaries():
    results = []
    
    test_cases = [
        ('ddr_timing_table.lpddr4.single.ref.bin', "LPDDR4 single"),
        ('ddr_timing_table.lpddr5.single.ref.bin', "LPDDR5 single"),
    ]
    
    for ref_file, desc in test_cases:
        if not os.path.exists(ref_file):
            print(f"  SKIP: {ref_file} not found")
            continue
        
        # Step 1: Analyze to get params (dynamic extraction!)
        an_result = analyze_binary(ref_file)
        if not an_result.get('success'):
            print(f"  FAIL: {desc} - analyze failed")
            results.append((desc, False, "Analyze failed"))
            continue
        
        # Step 2: Convert to generate params
        params = convert_analyze_to_generate_params(an_result)
        
        # Step 3: Generate via GUI using extracted params
        gen_result = generate_binary(params)
        if not gen_result.get('success'):
            print(f"  FAIL: {desc} - GUI generate failed")
            results.append((desc, False, "Generate failed"))
            continue
        
        # Step 4: Compare binaries
        match, msg = compare_binaries_timing(BINARY_FILE, ref_file, 0x1000)
        
        if match:
            print(f"  PASS: {desc}")
            results.append((desc, True, "OK"))
        else:
            print(f"  FAIL: {desc} - {msg}")
            results.append((desc, False, msg))
    
    return results
```

#### Step 3: Add to main() summary check
- Add reference binary results to failure summary

---

## Expected Result

After implementation:
- Reference binary comparison should **PASS** (2/2)
- Test uses dynamic params extracted from GUI analysis
- No hardcoded values in test

---

## Files to Modify

| File | Changes |
|------|---------|
| test_gui_params.py | Add `convert_analyze_to_generate_params()`, update `test_reference_binaries()` |
