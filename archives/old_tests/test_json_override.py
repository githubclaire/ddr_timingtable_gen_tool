#!/usr/bin/env python2
import sys
import json
import ctypes
sys.path.insert(0, '.')
from orbit_config import make_orbit_config_class
from ddr_config_init import create_orbit_config, ddr_config_init

print("=== Testing JSON Override Functionality ===")

# Create config with default values
cfg_default = create_orbit_config('lpddr4', False)
ddr_config_init(cfg_default, dram_type='lpddr4', two_channel=False, density=16, 
                rank_interleaving=1, num_rank=2)

print("Default values:")
print("  rank_interleaving:", cfg_default.rank_interleaving)
print("  num_rank:", cfg_default.num_rank)
print("  reboot_with_mrw:", cfg_default.reboot_with_mrw)
print("  rfm_en:", cfg_default.rfm_en)
print("  ca_odt:", cfg_default.ca_odt)
print("  t_refiab:", cfg_default.t_refiab)
print("  link_err_cnt_th:", cfg_default.link_err_cnt_th)

# Create config with JSON overrides
cfg_override = create_orbit_config('lpddr4', False)
# Simulate what gen_timing_params does: pass overrides as kwargs
overrides = {
    'rank_interleaving': 0,
    'num_rank': 1,
    'reboot_with_mrw': 1,
    'rfm_en': 1,
    'dsm_en': 0,
    'ca_odt': 1,
    'eye_scan_rd_en': 1,
    'eye_scan_wr_en': 1,
    'zq_calibration_period': 24000,
    't_refiab': 2000000,
    't_refipb': 250000,
    'link_err_cnt_th': 10
}
ddr_config_init(cfg_override, dram_type='lpddr4', two_channel=False, density=16, **overrides)

print("\nOverride values:")
print("  rank_interleaving:", cfg_override.rank_interleaving)
print("  num_rank:", cfg_override.num_rank)
print("  reboot_with_mrw:", cfg_override.reboot_with_mrw)
print("  rfm_en:", cfg_override.rfm_en)
print("  ca_odt:", cfg_override.ca_odt)
print("  t_refiab:", cfg_override.t_refiab)
print("  link_err_cnt_th:", cfg_override.link_err_cnt_th)

# Verify overrides applied correctly
assert cfg_override.rank_interleaving == 0, "rank_interleaving not overridden"
assert cfg_override.num_rank == 1, "num_rank not overridden"
assert cfg_override.reboot_with_mrw == 1, "reboot_with_mrw not overridden"
assert cfg_override.rfm_en == 1, "rfm_en not overridden"
assert cfg_override.ca_odt == 1, "ca_odt not overridden"
assert cfg_override.t_refiab == 2000000, "t_refiab not overridden"
assert cfg_override.link_err_cnt_th == 10, "link_err_cnt_th not overridden"

print("\nOK All JSON overrides applied correctly!")

# Test actual JSON file loading
print("\n=== Testing JSON file loading ===")
with open('test_override.json', 'r') as f:
    json_overrides = json.load(f)
print("Loaded JSON keys:", list(json_overrides.keys()))

# Create config with JSON file overrides
cfg_json = create_orbit_config('lpddr4', False)
ddr_config_init(cfg_json, dram_type='lpddr4', two_channel=False, density=16, **json_overrides)

print("JSON file override values:")
print("  rank_interleaving:", cfg_json.rank_interleaving)
print("  num_rank:", cfg_json.num_rank)
print("  reboot_with_mrw:", cfg_json.reboot_with_mrw)
print("  rfm_en:", cfg_json.rfm_en)
print("  ca_odt:", cfg_json.ca_odt)
print("  t_refiab:", cfg_json.t_refiab)
print("  link_err_cnt_th:", cfg_json.link_err_cnt_th)

# Verify
assert cfg_json.rank_interleaving == 0
assert cfg_json.num_rank == 1
assert cfg_json.reboot_with_mrw == 1
assert cfg_json.rfm_en == 1
assert cfg_json.ca_odt == 1
assert cfg_json.t_refiab == 2000000
assert cfg_json.link_err_cnt_th == 10

print("\nOK JSON file overrides work correctly!")

# Test integration with gen_timing_params (simulate)
print("\n=== Simulating gen_timing_params integration ===")
# This would be tested by actually running gen_timing_params with --orbit-config-json
# For now, just confirm the JSON is valid
print("JSON file is valid and contains expected fields.")

print("\n=== JSON Override Test PASSED ===")