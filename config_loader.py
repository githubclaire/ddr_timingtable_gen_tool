"""F4 — unified config loader.

Supports loading a YAML or JSON file whose top-level keys correspond to
``gen_timing_params`` CLI long-flag names (with hyphens replaced by
underscores, matching argparse dest naming). Values become argparse
defaults; explicit CLI arguments still take precedence.

Example YAML::

    dram_type: lpddr4
    phy_name: sphy-v9r8
    speed_bin: "4266"
    dq_width: 16
    orbit_config_density: 16
    periods: [938, 1631, 2500]
    # boolean flags use their argparse dest names
    orbit_config_use_python: true

Invocation::

    gen_timing_params --config my_config.yaml

YAML is preferred; JSON is accepted as a fallback for environments
without ``pyyaml`` installed. The loader is format-detected by extension
(``.yaml``/``.yml`` vs ``.json``).
"""
import json
import os


def load(path):
    """Return a dict loaded from ``path``. Raises ``IOError`` or
    ``ValueError`` on failure."""
    if not os.path.exists(path):
        raise IOError("config file not found: %s" % path)
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r") as f:
        text = f.read()
    if ext in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except ImportError:
            raise ValueError(
                "YAML config requires PyYAML; install it or use JSON")
        data = yaml.safe_load(text)
    elif ext == ".json":
        data = json.loads(text)
    else:
        # Try YAML first, then JSON
        try:
            import yaml  # type: ignore
            data = yaml.safe_load(text)
        except ImportError:
            data = json.loads(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("config file top level must be a mapping")
    return data


def apply_to_parser(parser, config_dict):
    """Feed ``config_dict`` into ``parser`` as defaults. Only keys that
    correspond to known dests are applied; unknown keys are returned in a
    list so the caller can warn about typos."""
    known = {a.dest for a in parser._actions}
    applied = {}
    unknown = []
    for key, val in config_dict.items():
        dest = key.replace("-", "_")
        if dest in known:
            applied[dest] = val
        else:
            unknown.append(key)
    parser.set_defaults(**applied)
    return applied, unknown
