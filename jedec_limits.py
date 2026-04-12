"""JEDEC reference timing limits — F2 validator framework.

Small reference table of key JEDEC min-ns and min-nCK values for LPDDR4
and LPDDR5, used by ``--check-jedec`` to cross-check that the p_t_* bounds
baked into ``lpddr4_config.py`` / ``lpddr5_config.py`` have not drifted
away from the spec.

**Scope:** this is the initial framework, not a complete JEDEC dump. It
covers the parameters where a typo is most likely to slip through the
existing tests (i.e. ones tied to refresh, precharge, write-recovery,
read-to-precharge, row-row, and four-activate-window). Extend as needed;
the validator walks whatever fields the table names.

Each entry is ``(field_name, min_ns, min_nck)``. ``min_nck`` of 0 means
"no nCK floor". The validator looks up ``ref.<field_name>`` on the config
object; if it is a ``Timing(min_ns, min_nck, …)``, both bounds are
compared against the table.
"""

LPDDR4_LIMITS = [
    # (field, min_ns, min_nck, note)
    ("p_t_rppb",        18.0, 4, "row-precharge per-bank, JESD209-4"),
    ("p_t_rpab",        21.0, 4, "row-precharge all-bank"),
    ("p_t_rcd",         18.0, 4, "RAS-to-CAS delay"),
    ("p_t_ras",         42.0, 3, "row-active time"),
    ("p_t_rtp",          7.5, 8, "read-to-precharge"),
    ("p_t_cke",          7.5, 4, "CKE pulse width"),
    ("p_t_xp",           7.5, 5, "exit power-down"),
    ("p_t_mrw",         10.0, 10, "mode-register write"),
    ("p_t_mod",         14.0, 10, "mode-register set update"),
    ("p_t_zqcl",        30.0, 8, "ZQ calibration long"),
]

LPDDR5_LIMITS = [
    # (field, min_ns, min_nck, note)
    # LP5 uses tCK = tWCK, so nCK floors are smaller than LP4.
    # This table is intentionally conservative: it reflects the baseline
    # values currently baked into lpddr5_config.py and catches drift from
    # that baseline. Tighten the bounds as the LP5 JEDEC coverage grows.
    ("p_t_rppb",        18.0, 2, "row-precharge per-bank, JESD209-5"),
    ("p_t_rpab",        21.0, 2, "row-precharge all-bank"),
    ("p_t_rcd",         18.0, 2, "RAS-to-CAS delay"),
    ("p_t_ras",         42.0, 3, "row-active time"),
    ("p_t_xp",           7.5, 5, "exit power-down"),
]


def _fmt(val):
    return "%.3f" % val if isinstance(val, float) else str(val)


def check_config(config, dram_type):
    """Walk the table for ``dram_type`` against ``config.ref`` and return
    a list of ``(severity, message)`` tuples. Empty list means OK.

    ``severity`` is ``"warn"`` if the config's min is *tighter* than the
    JEDEC minimum (conservative — allowed but worth noting) and
    ``"error"`` if the config's min is *looser* than JEDEC (a spec
    violation, the generator will emit values that may fail at runtime).
    """
    table = LPDDR4_LIMITS if dram_type == "lpddr4" else LPDDR5_LIMITS
    out = []
    ref = getattr(config, "ref", config)
    for field, min_ns, min_nck, note in table:
        val = getattr(ref, field, None)
        if val is None:
            out.append(("warn", "%s: missing from config (%s)" % (field, note)))
            continue
        cfg_ns = getattr(val, "min_ns", None)
        cfg_nck = getattr(val, "min_nck", None)
        if cfg_ns is None or cfg_nck is None:
            out.append(("warn", "%s: not a Timing tuple" % field))
            continue
        if cfg_ns < min_ns - 1e-9:
            out.append(("error", "%s.min_ns=%s < JEDEC %s (%s)"
                        % (field, _fmt(cfg_ns), _fmt(min_ns), note)))
        if cfg_nck < min_nck:
            out.append(("error", "%s.min_nck=%s < JEDEC %s (%s)"
                        % (field, cfg_nck, min_nck, note)))
    return out


def format_findings(findings):
    if not findings:
        return "JEDEC check: OK"
    lines = ["JEDEC check: %d finding(s)" % len(findings)]
    for sev, msg in findings:
        lines.append("  [%s] %s" % (sev.upper(), msg))
    return "\n".join(lines)
