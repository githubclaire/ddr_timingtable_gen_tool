"""F5 — human-readable timing report.

Emits a ``.report.txt`` sibling file summarizing the configuration and
per-frequency headline numbers. The goal is not to dump every field, but
to give a reviewing engineer a 30-second grasp of *what* was generated
without having to parse a binary.
"""
import os
import re


def _scalars(c_value):
    """Extract top-level scalar tokens from a positional struct initializer.

    The formatter in gen_timing_params emits one scalar per line at the
    top level, and brace-wrapped arrays for aggregate fields. Splitting
    on newlines and stripping non-numeric tokens yields the scalars in
    their declared order (freq, t_ck, ... wck_ratio, ..., rl, wl, ...).
    """
    out = []
    depth = 0
    current = []
    # Tokenize respecting brace nesting so array contents are skipped.
    for ch in c_value:
        if ch == '{':
            if depth > 0:
                current.append(ch)
            depth += 1
            continue
        if ch == '}':
            depth -= 1
            if depth > 0:
                current.append(ch)
            continue
        if depth != 1:
            continue
        if ch == ',':
            tok = "".join(current).strip()
            if tok:
                out.append(tok)
            current = []
        else:
            current.append(ch)
    tok = "".join(current).strip()
    if tok:
        out.append(tok)
    return out


def _int(s, default=0):
    try:
        return int(s, 0)
    except (TypeError, ValueError):
        return default


def _summarize_entry(c_value):
    # Scalars at top level (index-based, brittle to template changes but
    # good enough for a summary; the full binary is still the source of
    # truth).
    toks = _scalars(c_value)
    freq = _int(toks[0]) if len(toks) > 0 else 0
    t_ck = _int(toks[1]) if len(toks) > 1 else 0
    # The first brace-wrapped block is timing_zqcal (hex); skipped by the
    # tokenizer. Next scalars after the arrays start at wck_ratio. Rather
    # than indexing past the arrays, we grep for the two headline values
    # only: freq and t_ck are enough for a per-row summary.
    return freq, t_ck


def write_report(timing_param, c_values, output_path):
    args = timing_param.args
    lines = []
    lines.append("# DDR timing table report")
    lines.append("#")
    lines.append("dram_type          : %s" % args.dram_type)
    lines.append("phy_name           : %s" % getattr(args, "phy_name", "?"))
    lines.append("speed_bin          : %s" % getattr(args, "speed_bin", "?"))
    lines.append("dq_width           : %s" % args.dq_width)
    lines.append("orbit_density_Gb   : %s" % getattr(args, "orbit_config_density", "?"))
    lines.append("two_channel        : %s" % bool(getattr(args, "two_channel", False)))
    lines.append("omc_freq_ratio     : %s" % args.omc_freq_ratio)
    lines.append("phy_freq_ratio     : %s" % args.phy_freq_ratio)
    lines.append("")
    lines.append("# Per-frequency summary")
    lines.append("#   freq is in MHz, t_ck in ps, rl/wl in tCK")
    lines.append("#")
    lines.append("  idx  freq(MHz)  t_ck(ps)")
    lines.append("  ---  ---------  --------")
    for idx, cv in enumerate(c_values):
        freq, t_ck = _summarize_entry(cv)
        lines.append("  %3d  %9d  %8d" % (idx, freq, t_ck))
    lines.append("")
    lines.append("# Feature toggles applied to the last (lowest-freq) entry")
    lines.append("write_odt          : %s" % getattr(timing_param, "write_odt", "?"))
    lines.append("write_dbi          : %s" % getattr(timing_param, "write_dbi", "?"))
    lines.append("read_dbi           : %s" % getattr(timing_param, "read_dbi", "?"))
    lines.append("write_lecc         : %s" % getattr(timing_param, "write_lecc", "?"))
    lines.append("bg_mode            : %s" % getattr(timing_param, "bg_mode", "?"))
    lines.append("wck_1to4           : %s" % getattr(timing_param, "wck_1to4", "?"))
    lines.append("wck_always_on      : %s" % getattr(timing_param, "wck_always_on", "?"))
    lines.append("")
    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return output_path
