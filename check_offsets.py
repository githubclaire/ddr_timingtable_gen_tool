import struct
import re

# Read gui.py and extract offsets
with open('gui.py', 'r') as f:
    content = f.read()

# Extract LPDDR4 and LPDDR5 sections
lp5_start = content.find('if is_lpddr5:')
lp5_else = content.find('else:', lp5_start)
lp5_section = content[lp5_start:lp5_else]

# Find the LPDDR4 section (after the else:)
lp4_start = lp5_else
lp4_section = content[lp4_start:lp4_start+4000]

# Parse fields from gui.py
fields_lp4 = {}
fields_lp5 = {}

for match in re.findall(r"\('(\w+)',\s*(0x[0-9a-fA-F]+),", lp5_section):
    fields_lp5[match[0]] = int(match[1], 16)
    
for match in re.findall(r"\('(\w+)',\s*(0x[0-9a-fA-F]+),", lp4_section):
    fields_lp4[match[0]] = int(match[1], 16)

# Reference offsets from offset_reference_v2.md
ref_lp4 = {
    'phy_freq_ratio': 0x0C, 'omc_freq_ratio': 0x0E, 'cpipe_depth': 0x14, 'dpipe_depth': 0x16,
    'density': 0x1C, 'rank_interleaving': 0x1E, 'num_rank': 0x20, 'ctrl_dq_width': 0x24,
    'dq_width': 0x26, 'reboot_with_mrw': 0x22, 'rfm_en': 0x3A, 'dsm_en': 0x3C, 'ca_odt': 0x46,
    'eye_scan_rd_en': 0x3E, 'eye_scan_wr_en': 0x40, 'eye_scan_prbs_rd_en': 0x42,
    'eye_scan_prbs_wr_en': 0x44, 'init_zq_calibration': 0x4A, 'command_bus_training': 0x66,
    'ca_vref_training': 0x68, 'prbs_training': 0x6A, 'reboot_with_training': 0x6C,
    'dfs_training': 0x6E, 'phy_vref_trn_mode': 0x72, 'phy_duty_trn_mode': 0x74,
    'dram_vref_trn_mode': 0x76, 'dram_duty_trn_mode': 0x78,
    'regional_clock_gating': 0x58, 'phy_clock_gating': 0x5A, 'dram_clock_gating': 0x5C,
    'phy_low_power': 0x2C, 'phy_idle_cnt_th': 0x2E, 'dynamic_power_down': 0x54,
    'dynamic_self_refresh': 0x56, 'temp_sensing': 0x4C, 'zq_calibration': 0x4E,
    'periodic_training': 0x50, 'periodic_training_period': 0x52,
    'dfs_lvl_t_ck_0': 0x5E, 'dfs_lvl_t_ck_1': 0x60, 'dfs_lvl_t_ck_2': 0x62,
}

ref_lp5 = {
    'phy_freq_ratio': 0x14, 'omc_freq_ratio': 0x16, 'cpipe_depth': 0x18, 'dpipe_depth': 0x1A,
    'density': 0x20, 'rank_interleaving': 0x22, 'num_rank': 0x28, 'ctrl_dq_width': 0x2A,
    'dq_width': 0x2C, 'reboot_with_mrw': 0x26, 'rfm_en': 0x3C, 'dsm_en': 0x3E, 'ca_odt': 0x48,
    'eye_scan_rd_en': 0x40, 'eye_scan_wr_en': 0x42, 'eye_scan_prbs_rd_en': 0x44,
    'eye_scan_prbs_wr_en': 0x46, 'init_zq_calibration': 0x4C, 'command_bus_training': 0x75,
    'ca_vref_training': 0x77, 'prbs_training': 0x79, 'reboot_with_training': 0x7B,
    'dfs_training': 0x7D, 'phy_vref_trn_mode': 0x81, 'phy_duty_trn_mode': 0x83,
    'dram_vref_trn_mode': 0x85, 'dram_duty_trn_mode': 0x87,
    'regional_clock_gating': 0x5A, 'phy_clock_gating': 0x5C, 'dram_clock_gating': 0x5E,
    'phy_low_power': 0x30, 'phy_idle_cnt_th': 0x32, 'dynamic_power_down': 0x56,
    'dynamic_self_refresh': 0x58, 'temp_sensing': 0x4E, 'zq_calibration': 0x50,
    'periodic_training': 0x52, 'periodic_training_period': 0x54,
    'dfs_lvl_t_ck_0': 0x63, 'dfs_lvl_t_ck_1': 0x65, 'dfs_lvl_t_ck_2': 0x67,
}

print('=== LPDDR4 Offset Comparison ===')
print('Field                | gui.py  | Reference | Match')
print('-' * 55)
for field in sorted(ref_lp4.keys()):
    gui_offset = fields_lp4.get(field, None)
    ref_offset = ref_lp4[field]
    match = 'OK' if gui_offset == ref_offset else 'WRONG'
    gui_str = f'0x{gui_offset:02X}' if gui_offset is not None else 'MISSING'
    print(f'{field:20} | {gui_str:7} | 0x{ref_offset:02X}     | {match}')

print()
print('=== LPDDR5 Offset Comparison ===')
print('Field                | gui.py  | Reference | Match')
print('-' * 55)
for field in sorted(ref_lp5.keys()):
    gui_offset = fields_lp5.get(field, None)
    ref_offset = ref_lp5[field]
    match = 'OK' if gui_offset == ref_offset else 'WRONG'
    gui_str = f'0x{gui_offset:02X}' if gui_offset is not None else 'MISSING'
    print(f'{field:20} | {gui_str:7} | 0x{ref_offset:02X}     | {match}')

print()
print('=== Fields in gui.py NOT in reference ===')
for field in fields_lp4:
    if field not in ref_lp4:
        print(f'LPDDR4: {field} @ 0x{fields_lp4[field]:02X}')

for field in fields_lp5:
    if field not in ref_lp5:
        print(f'LPDDR5: {field} @ 0x{fields_lp5[field]:02X}')