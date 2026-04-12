#!/usr/bin/env python3
"""
Phase 4 — single registry driving CLI flags, GUI form inputs, and JSON
override keys for the orbit_config struct.

Every user-visible orbit_config field is defined here exactly once; callers
iterate ``FIELDS`` to register argparse arguments, emit HTML form inputs, and
translate form/JSON values back into gen_timing_params's internal dict.

This replaces the scattered hand-maintained lists in gen_timing_params and
gui.py and is the hook point for:

- F2 JEDEC validator metadata (per-field min/max)
- F4 YAML schema generation
- P0-6 regression prevention ("GUI emits a flag the CLI doesn't know")
"""
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple


@dataclass
class OrbitField:
    name: str                     # canonical orbit_config field name
    cli_flag: str                 # --orbit-... flag used by gen_timing_params
    gui_name: str                 # HTML form input name used by gui.py
    type: Callable[[str], Any] = int
    default: Any = 0
    choices: Optional[Tuple] = None
    help: str = ""
    group: str = "orbit"          # argparse group
    dram_types: Tuple[str, ...] = ("lpddr4", "lpddr5")
    # F2 hook points, populated gradually:
    jedec_min: Optional[int] = None
    jedec_max: Optional[int] = None
    jedec_ref: Optional[str] = None


# Order preserved so argparse --help output is stable.
FIELDS: List[OrbitField] = [
    OrbitField("byte_mode", "--orbit-byte-mode", "orbit-byte-mode",
               default=0, choices=(0, 1),
               help="Byte mode for LPDDR4 (0=x16, 1=x8)",
               dram_types=("lpddr4",)),
    OrbitField("mixed", "--orbit-mixed", "orbit-mixed",
               default=0, choices=(0, 1),
               help="Mixed rank density flag"),
    OrbitField("rank_interleaving", "--orbit-rank-interleaving",
               "orbit-rank-interleaving",
               default=1, choices=(0, 1),
               help="Rank interleaving enable"),
    OrbitField("num_rank", "--orbit-num-rank", "orbit-num-rank",
               default=2, choices=(1, 2),
               help="Number of ranks (max 2)"),
    OrbitField("reboot_with_mrw", "--orbit-reboot-with-mrw",
               "orbit-reboot-with-mrw",
               default=0, choices=(0, 1),
               help="Reboot with MRW"),
    OrbitField("rfm_en", "--orbit-rfm-en", "orbit-rfm-en",
               default=0, choices=(0, 1),
               help="RFM enable (LPDDR4/LPDDR5)"),
    OrbitField("dsm_en", "--orbit-dsm-en", "orbit-dsm-en",
               default=0, choices=(0, 1),
               help="DSM enable (LPDDR5 Deep Sleep Mode)",
               dram_types=("lpddr5",)),
    OrbitField("ca_odt", "--orbit-ca-odt", "orbit-ca-odt",
               default=0, choices=(0, 1),
               help="CA ODT enable"),
    OrbitField("dynamic_power_down", "--orbit-dynamic-power-down",
               "orbit-dynamic-power-down",
               default=0, choices=(0, 1),
               help="Dynamic power down enable"),
    OrbitField("dynamic_power_down_threshold",
               "--orbit-dynamic-power-down-threshold",
               "orbit-dynamic-power-down-threshold",
               default=0,
               help="Dynamic power down threshold (cycles)"),
    OrbitField("dynamic_self_refresh", "--orbit-dynamic-self-refresh",
               "orbit-dynamic-self-refresh",
               default=0, choices=(0, 1),
               help="Dynamic self refresh enable"),
    OrbitField("dynamic_self_refresh_threshold",
               "--orbit-dynamic-self-refresh-threshold",
               "orbit-dynamic-self-refresh-threshold",
               default=0,
               help="Dynamic self refresh threshold (cycles)"),
    OrbitField("phy_idle_cnt_th", "--orbit-phy-idle-cnt-th",
               "orbit-phy-idle-cnt-th", default=0,
               help="PHY idle counter threshold"),
    OrbitField("phy_low_power", "--orbit-phy-low-power",
               "orbit-phy-low-power", default=0, choices=(0, 1),
               help="PHY low power enable"),
    OrbitField("periodic_training", "--orbit-periodic-training",
               "orbit-periodic-training", default=0, choices=(0, 1),
               help="Periodic training enable"),
    OrbitField("periodic_training_period",
               "--orbit-periodic-training-period",
               "orbit-periodic-training-period", default=24000,
               help="Periodic training period (us)",
               jedec_min=1000, jedec_max=10_000_000),
    OrbitField("temp_sensing", "--orbit-temp-sensing", "orbit-temp-sensing",
               default=0, choices=(0, 1),
               help="Temperature sensing enable"),
    OrbitField("temp_sensing_period", "--orbit-temp-sensing-period",
               "orbit-temp-sensing-period", default=32000,
               help="Temperature sensing period (us)",
               jedec_min=1000, jedec_max=10_000_000),
    OrbitField("zq_calibration_period", "--orbit-zq-calibration-period",
               "orbit-zq-calibration-period", default=48000,
               help="ZQ calibration period (us)",
               jedec_min=1000, jedec_max=10_000_000),
    OrbitField("t_refiab", "--orbit-t-refiab", "orbit-t-refiab",
               default=3904000, help="tREFI AB (in ps)",
               jedec_min=100_000, jedec_max=10_000_000),
    OrbitField("t_refipb", "--orbit-t-refipb", "orbit-t-refipb",
               default=488000, help="tREFI PB (in ps)",
               jedec_min=50_000, jedec_max=10_000_000),
    OrbitField("t_zqcal", "--orbit-t-zqcal", "orbit-t-zqcal",
               default=1000000, help="tZQCAL (in ps)",
               jedec_min=100_000, jedec_max=10_000_000),
]


def register_argparse(parser, group=None):
    """Add every FIELDS entry as a ``--orbit-*`` argument on ``parser``.

    Skips fields whose CLI flag has already been registered (idempotent —
    the existing gen_timing_params code still hand-adds these, so this
    function's job is to *cover the gap*).
    """
    target = group if group is not None else parser
    existing = set()
    for act in getattr(parser, "_actions", []):
        for opt in getattr(act, "option_strings", []):
            existing.add(opt)
    for f in FIELDS:
        if f.cli_flag in existing:
            continue
        kwargs = dict(type=f.type, default=f.default, help=f.help)
        if f.choices is not None:
            kwargs["choices"] = list(f.choices)
        target.add_argument(f.cli_flag, **kwargs)


def json_override_from_params(params, is_checked=None, to_int=None):
    """Build a JSON override dict from an arbitrary GUI form dict.

    The GUI's form inputs use hyphen-delimited names (``orbit-dsm-en``).
    Returns a dict keyed by canonical struct field name.
    """
    if is_checked is None:
        def is_checked(v): return v in ("1", "true", True)
    if to_int is None:
        def to_int(v):
            if v in (None, ""):
                return None
            try:
                return int(float(v))
            except (TypeError, ValueError):
                return None

    out = {}
    for f in FIELDS:
        raw = params.get(f.gui_name)
        if raw is None:
            continue
        if f.choices == (0, 1):
            out[f.name] = 1 if is_checked(raw) else 0
        else:
            v = to_int(raw)
            if v is not None:
                out[f.name] = v
    return out


def flag_names():
    return [f.cli_flag for f in FIELDS]


def gui_names():
    return [f.gui_name for f in FIELDS]
