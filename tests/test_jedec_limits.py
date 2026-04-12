"""F2 — tests for ``jedec_limits.check_config``."""
import os
import subprocess
import sys
import unittest

import jedec_limits

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _FakeTiming:
    def __init__(self, min_ns, min_nck):
        self.min_ns = min_ns
        self.min_nck = min_nck


class _FakeRef:
    pass


class _FakeConfig:
    def __init__(self, **fields):
        self.ref = _FakeRef()
        for k, v in fields.items():
            setattr(self.ref, k, v)


class JedecLimitsUnit(unittest.TestCase):
    def test_ok_config_produces_no_findings(self):
        cfg = _FakeConfig(**{
            f: _FakeTiming(ns, nck) for f, ns, nck, _ in jedec_limits.LPDDR4_LIMITS
        })
        self.assertEqual(jedec_limits.check_config(cfg, "lpddr4"), [])

    def test_looser_than_jedec_is_error(self):
        fields = {f: _FakeTiming(ns, nck)
                  for f, ns, nck, _ in jedec_limits.LPDDR4_LIMITS}
        # Break p_t_rppb to violate spec:
        fields["p_t_rppb"] = _FakeTiming(10.0, 4)
        cfg = _FakeConfig(**fields)
        findings = jedec_limits.check_config(cfg, "lpddr4")
        self.assertTrue(any(
            sev == "error" and "p_t_rppb.min_ns" in msg for sev, msg in findings
        ))

    def test_missing_field_warns(self):
        # Intentionally omit p_t_rppb
        fields = {f: _FakeTiming(ns, nck)
                  for f, ns, nck, _ in jedec_limits.LPDDR4_LIMITS
                  if f != "p_t_rppb"}
        cfg = _FakeConfig(**fields)
        findings = jedec_limits.check_config(cfg, "lpddr4")
        self.assertTrue(any(
            sev == "warn" and "p_t_rppb" in msg for sev, msg in findings
        ))


class JedecLimitsEndToEnd(unittest.TestCase):
    """Actually drive ``gen_timing_params --check-jedec`` for LP4 and LP5
    and assert the baked-in reference values pass."""

    def _run(self, args):
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "gen_timing_params")] + args,
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
        )

    def test_lp4_baked_refs_pass_jedec(self):
        r = self._run([
            "--dram-type", "lpddr4", "--phy-name", "sphy-v9r8",
            "--speed-bin", "4266", "--dq-width", "16",
            "--orbit-config-density", "16", "--wire-length", "10",
            "--read-dbi-upto", "10000", "--write-dbi-upto", "10000",
            "--write-lecc-upto", "625", "--write-odt-upto", "10000",
            "--cpipe-depth", "1", "--dpipe-depth", "1",
            "--omc-freq-ratio", "2", "--phy-freq-ratio", "2",
            "--check-jedec", "--orbit-config-use-python",
            "938", "1631", "2500",
        ])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("JEDEC check: OK", r.stdout)

    def test_lp5_baked_refs_pass_jedec(self):
        r = self._run([
            "--dram-type", "lpddr5", "--phy-name", "sphy-v9r8",
            "--speed-bin", "6400", "--dq-width", "16",
            "--orbit-config-density", "16", "--wire-length", "10",
            "--read-dbi-upto", "10000", "--write-dbi-upto", "10000",
            "--write-lecc-upto", "625", "--write-odt-upto", "10000",
            "--cpipe-depth", "1", "--dpipe-depth", "1",
            "--omc-freq-ratio", "1", "--phy-freq-ratio", "1",
            "--wck-1to4-upto", "625", "--wck-always-on-from", "0",
            "--wck-always-on-upto", "10000",
            "--check-jedec", "--orbit-config-use-python",
            "314", "418", "556", "2500",
        ])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("JEDEC check: OK", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
