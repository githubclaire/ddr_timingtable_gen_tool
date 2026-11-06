"""Direct unit coverage for ddr_config_init / orbit_config serialization."""
import ctypes
import os
import struct
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from orbit_config import (  # noqa: E402
    create_orbit_config, make_orbit_config_class, orbit_config_prefix_size,
    EMMC_CM4_TIME_TB_SIZE, TIMING_TABLE_BIN_SIZE,
)
from ddr_config_init import (  # noqa: E402
    ddr_config_init, generate_orbit_config_binary, _t_ck_set,
)
from gui import _load_cfg_from_data  # noqa: E402


class DefaultsAndOverrides(unittest.TestCase):
    def test_lp5_defaults(self):
        cfg = create_orbit_config('lpddr5', False)
        ddr_config_init(cfg, dram_type='lpddr5', density=16)
        self.assertEqual(cfg.rclk_t_ck, 20000)
        self.assertEqual(cfg.dram_t_ck, 1332)
        self.assertEqual(cfg.timingtable_size, 4)
        self.assertEqual(list(cfg.dfs_lvl_t_ck), [1428, 1672, 2512])
        self.assertEqual(cfg.density, 16)
        self.assertEqual(cfg.density_code, 7)  # LP5 positional == canonical
        self.assertEqual(cfg.num_rank, 1)
        self.assertEqual(cfg.phy_odt, 5)
        self.assertEqual(cfg.link_err_cnt_th, 2)
        self.assertEqual(cfg.bg_intr_size, 3)
        self.assertEqual(cfg.initial_training, 1)
        self.assertEqual(cfg.periodic_training_period, 50000)
        self.assertEqual(cfg.dynamic_power_down_threshold, 2048)

    def test_lp4_defaults(self):
        cfg = create_orbit_config('lpddr4', False)
        ddr_config_init(cfg, dram_type='lpddr4', density=8)
        # Original SCP toolchain positional mapping: [2,3,4,6,8,12,16]
        self.assertEqual(cfg.density_code, 4)
        self.assertEqual(cfg.dram_t_ck, 471)
        self.assertEqual(cfg.bg_intr_size, 0)
        self.assertEqual(cfg.link_err_cnt_th, 0)
        self.assertEqual(cfg.lpddr4_rpre, 0)
        self.assertEqual(list(cfg.dfs_lvl_t_ck), [938, 1631, 2500])

    def test_freq_levels_and_tables(self):
        for level in range(4):
            cfg = create_orbit_config('lpddr5', False)
            ddr_config_init(cfg, dram_type='lpddr5', ddr_freq_level=level)
            table = [1332, 1428, 1672, 2512]
            self.assertEqual(cfg.dram_t_ck, table[level])
            self.assertEqual(cfg.timingtable_size, 4 - level)
            self.assertEqual(
                list(cfg.dfs_lvl_t_ck),
                (table[level + 1:] + [0, 0, 0])[:3])
        cfg = create_orbit_config('lpddr5', False)
        ddr_config_init(cfg, dram_type='lpddr5', lp5_freq_set='6400')
        self.assertEqual(cfg.dram_t_ck, 1256)

    def test_two_channel_and_default_ch(self):
        cfg = create_orbit_config('lpddr5', True)
        ddr_config_init(cfg, dram_type='lpddr5', two_channel=True)
        self.assertEqual(cfg.omc_channel, 2)
        self.assertEqual(cfg.base_addr_id[0], 0x51120000)
        self.assertEqual(cfg.base_addr_id[2], 0x51140000)
        self.assertEqual(cfg.region_start[0], 0x0040000000)

        cfg = create_orbit_config('lpddr4', False)
        ddr_config_init(cfg, dram_type='lpddr4', default_ch=1)
        self.assertEqual(cfg.omc_channel, 1)
        self.assertEqual(cfg.base_addr, 0x51140000)
        self.assertEqual(cfg.base_addr_id[0], 0x51140000)

    def test_geometry_and_mixed(self):
        cfg = create_orbit_config('lpddr5', True)
        ddr_config_init(cfg, dram_type='lpddr5', density=16,
                        num_rank=2, byte_mode=1, mixed=1, dq_width=8)
        self.assertEqual(cfg.chip[0].num_row, 17)
        self.assertEqual(cfg.chip[1].num_row, 18)
        self.assertEqual(cfg.dq_width, 8)
        self.assertEqual(cfg.mrr_byte_lane, 0xFF)
        self.assertEqual(cfg.chip[0].size, 32)

    def test_scalar_overrides(self):
        cfg = create_orbit_config('lpddr5', False)
        ddr_config_init(cfg, dram_type='lpddr5', dfs_lvl_t_ck=[1500, 1700, 2600],
                        dynamic_power_down_threshold=4096,
                        t_refiab=1234567, zq_bg_mode=0)
        self.assertEqual(list(cfg.dfs_lvl_t_ck), [1500, 1700, 2600])
        self.assertEqual(cfg.dynamic_power_down_threshold, 4096)
        self.assertEqual(cfg.t_refiab, 1234567)
        self.assertEqual(cfg.zq_bg_mode, 0)

    def test_invalid_inputs(self):
        cfg = create_orbit_config('lpddr5', False)
        with self.assertRaises(ValueError):
            ddr_config_init(cfg, dram_type='lpddr5', ddr_freq_level=4)
        with self.assertRaises(ValueError):
            ddr_config_init(cfg, dram_type='lpddr5', lp5_freq_set='1111')
        with self.assertRaises(ValueError):
            _t_ck_set('lpddr5', 0, 'bad')


class Serialization(unittest.TestCase):
    def test_prefix_sizes(self):
        self.assertEqual(orbit_config_prefix_size('lpddr4', False), 360)
        self.assertEqual(orbit_config_prefix_size('lpddr4', True), 408)
        self.assertEqual(orbit_config_prefix_size('lpddr5', False), 360)
        self.assertEqual(orbit_config_prefix_size('lpddr5', True), 408)

    def test_binary_is_4k_and_prefix_only(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'ddr.bin')
            with open(path, 'wb') as f:
                f.write(b'\0' * 0x700)  # timing-table stub
            generate_orbit_config_binary('lpddr5', False, 16, output_file=path)
            self.assertEqual(os.path.getsize(path), TIMING_TABLE_BIN_SIZE)
            with open(path, 'rb') as f:
                data = f.read()
            cfg = _load_cfg_from_data(data, 'lpddr5', False)
            self.assertEqual(cfg.density, 16)
            # bytes after the prefix are zero padding
            self.assertEqual(data[0x800 + 360:0x1000], b'\0' * (0x1000 - 0x800 - 360))

    def test_rejects_oversized_timing_table(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'ddr.bin')
            with open(path, 'wb') as f:
                f.write(b'\0' * 0x900)
            with self.assertRaises(ValueError):
                generate_orbit_config_binary('lpddr5', False, 16, output_file=path)

    def test_rejects_wrong_offset(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'ddr.bin')
            with open(path, 'wb') as f:
                f.write(b'\0' * 0x700)
            with self.assertRaises(ValueError):
                generate_orbit_config_binary('lpddr5', False, 16,
                                             output_file=path, offset=0x1000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
