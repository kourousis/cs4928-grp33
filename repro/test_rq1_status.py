"""
Tests for rq1_status.py (task 7b). Synthetic notebook outputs only - no study data is read.

    python -m unittest repro/test_rq1_status.py -v

The fake outputs copy the exact print formats of the authors' four notebooks,
including the Task 1 sections after each Phase 2 block that reuse its labels.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rq1_status as st  # noqa: E402

# Values as the notebooks print them when they agree with the paper.
GOOD = {
    "completion_time": dict(p="5.6436e-01", effect="-0.0793", t="136.1", c="172.6",
                            tci=("105.5", "180.0"), cci=("118.1", "210.0")),
    "perceived_productivity": dict(p="3.7134e-01", effect="-0.2128", t="3.95", c="4.06",
                                   tci=("3.77", "4.12"), cci=("3.88", "4.24")),
    "codehealth": dict(p="2.3673e-01", effect="0.2761", t="8.49", c="8.44",
                       tci=("8.43", "8.54"), cci=("8.39", "8.49")),
    "coverage": dict(p="4.9001e-01", effect="0.0929", t="0.70", c="0.70",
                     tci=("0.69", "0.71"), cci=("0.69", "0.71")),
}
# Full-precision values as the 6b recompute writes them.
RECOMPUTE = {
    "completion_time": {"p": 0.5643572899014769, "effect_size": -0.07925407925407925,
                        "treatment_centre": 136.06666666666666, "control_centre": 172.63333333333333,
                        "treatment_ci95": [105.45, 180.0], "control_ci95": [118.08, 210.0]},
    "perceived_productivity": {"p": 0.37134417265146946, "welch_p": 0.367546835800754,
                               "effect_size": -0.21281066027050208,
                               "treatment_centre": 3.9461538461538455, "control_centre": 4.0636363636363635,
                               "treatment_ci95": [3.7667, 4.1231], "control_ci95": [3.8848, 4.2364]},
    "codehealth": {"p": 0.2367313141270534, "welch_p": 0.23478399391069485, "effect_size": 0.27612653131746967,
                   "treatment_centre": 8.48725, "control_centre": 8.44085714285714,
                   "treatment_ci95": [8.43475, 8.54025], "control_ci95": [8.3889, 8.4949]},
    "coverage": {"p": 0.4900102525346619, "effect_size": 0.09285714285714286,
                 "treatment_centre": 0.7, "control_centre": 0.7,
                 "treatment_ci95": [0.695, 0.71], "control_ci95": [0.69, 0.71]},
}


def fake_outputs(metric, p, effect, t, c, tci, cci, status="OK"):
    """One notebook's <name>.outputs.txt in the runner's format."""
    unit = " min" if metric == "completion_time" else ""
    ci = (f"Treatment (AI-assisted): {t}{unit}  (95% CI: {tci[0]} - {tci[1]}{unit})\n"
          f"Control (Manual):       {c}{unit}  (95% CI: {cci[0]} - {cci[1]}{unit})\n")
    body = {
        "completion_time": (f"Wilcoxon Rank-Sum Test (Completion Time in seconds):\n  Statistic = -0.5764\n"
                            f"  p-value   = {p}\nCliff’s Delta: δ={effect}\n{ci}"
                            "Bootstrap CI for the median difference (Treatment - Control):\n"
                            # Task 1 reuses the same labels after the end marker
                            "Wilcoxon Rank-Sum Test (Completion Time in seconds):\n  Statistic = -2.9\n"
                            "  p-value   = 2.9451e-03\nCliff’s Delta: δ=-0.4201\n"),
        "perceived_productivity": (f"Welch’s t-test on Perceived Productivity (PP):\n  t-statistic = -0.8997\n"
                                   f"  p-value     = {p}\n"
                                   f"Cohen's d for Perceived Productivity (PP Mean): {effect}\n{ci}"),
        "codehealth": (f"Welch’s t-test (unequal variances assumed):\n  t-statistic = 1.1930\n"
                       f"  p-value     = {p}\nCohen's d for CodeHealth: {effect}\n{ci}"
                       "Bootstrap CI for the mean CodeHealth difference (Treatment - Control):\n"
                       "Cliff’s Delta: δ=0.0852\n"),
        "coverage": (f"Wilcoxon Rank-Sum Test: Statistic=0.6903, p-value={p}\n"
                     f"Cliff's Delta for Code Coverage: {effect}\n{ci}"
                     "Bootstrap CI for the median Test Coverage difference (Treatment - Control):\n"),
    }[metric]
    return f"STATUS: {status}\n--- cell 0 (execution_count=1) ---\n{body}"


def failed_outputs():
    return "STATUS: FAILED\nCells after the failing cell were NOT executed.\nERROR FileNotFoundError: data\n"


class Rounding(unittest.TestCase):
    def test_exact_match_after_rounding(self):
        self.assertEqual(st.primary_match("2.3673e-01", 0.24, 2), (True, "0.24", False))
        self.assertEqual(st.primary_match("-0.0793", -0.079, 3), (True, "-0.079", False))
        self.assertEqual(st.primary_match("172.6", 173, 0), (True, "173", False))

    def test_mismatch(self):
        self.assertEqual(st.primary_match("2.3478e-01", 0.24, 2), (False, "0.23", False))

    def test_boundary_matches_either_neighbour(self):
        # 0.125 is exact in binary, so format gives banker's-style 0.12; the paper printing 0.13 still matches
        self.assertEqual(st.primary_match("0.125", 0.13, 2), (True, "0.12", True))
        self.assertEqual(st.primary_match("0.125", 0.12, 2), (True, "0.12", False))
        self.assertFalse(st.primary_match("0.125", 0.14, 2)[0])
        self.assertFalse(st.on_boundary("0.1251", 2))


class Parsing(unittest.TestCase):
    def test_reads_phase2_block_not_task1(self):
        for metric, v in GOOD.items():
            got = st.parse_outputs(metric, fake_outputs(metric, **v))
            self.assertEqual(got["p"], v["p"], metric)
            self.assertEqual(got["effect"], v["effect"], metric)
            self.assertEqual((got["treatment"], got["control"]), (v["t"], v["c"]), metric)
            self.assertEqual(got["control_ci"], list(v["cci"]), metric)

    def test_duplicate_phase2_line_is_an_error(self):
        text = fake_outputs("coverage", **GOOD["coverage"])
        text = text.replace("Cliff's Delta", "Cliff's Delta for Code Coverage: 0.5\nCliff's Delta", 1)
        with self.assertRaises(ValueError):
            st.parse_outputs("coverage", text)

    def test_missing_end_marker_is_an_error(self):
        text = fake_outputs("codehealth", **GOOD["codehealth"]).replace("Bootstrap CI for the mean", "x")
        with self.assertRaises(ValueError):
            st.parse_outputs("codehealth", text)


class Decision(unittest.TestCase):
    def test_paper_values_reproduce(self):
        for metric, v in GOOD.items():
            checks = st.decide(metric, st.parse_outputs(metric, fake_outputs(metric, **v)), RECOMPUTE[metric])
            self.assertTrue(all(c["match"] for c in checks), metric)
            self.assertTrue(all(c["cross_check_agrees"] for c in checks), metric)

    def test_significant_p_fails_two_criteria(self):
        v = dict(GOOD["codehealth"], p="4.0000e-02")
        checks = {c["value"]: c for c in st.decide("codehealth", st.parse_outputs(
            "codehealth", fake_outputs("codehealth", **v)), RECOMPUTE["codehealth"])}
        self.assertFalse(checks["p"]["match"])
        self.assertFalse(checks["significance"]["match"])
        self.assertTrue(checks["effect"]["match"])

    def test_cross_check_flags_printed_vs_full_precision(self):
        rec = dict(RECOMPUTE["codehealth"], effect_size=0.2851)  # rounds to 0.29, the printed 0.2761 to 0.28
        checks = {c["value"]: c for c in st.decide("codehealth", st.parse_outputs(
            "codehealth", fake_outputs("codehealth", **GOOD["codehealth"])), rec)}
        self.assertTrue(checks["effect"]["match"])
        self.assertFalse(checks["effect"]["cross_check_agrees"])

    def test_headline_order(self):
        self.assertEqual(st.headline(["REPRODUCED"] * 4), "REPRODUCED")
        self.assertEqual(st.headline(["REPRODUCED", "INCONCLUSIVE/BLOCKED", "NOT REPRODUCED"]), "NOT REPRODUCED")
        self.assertEqual(st.headline(["NOT REPRODUCED", "IN PROGRESS"]), "IN PROGRESS")
        self.assertEqual(st.headline(["REPRODUCED", "INCONCLUSIVE/BLOCKED"]), "INCONCLUSIVE/BLOCKED")


class Ladder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_dir(self, stamp, files):
        d = self.root / stamp
        d.mkdir()
        (d / "run_log.txt").write_text("log\n", encoding="utf-8")
        for name, text in files.items():
            (d / name).write_text(text, encoding="utf-8")
        return d

    def pp(self):
        return fake_outputs("perceived_productivity", **GOOD["perceived_productivity"])

    def test_ladder_steps(self):
        self.assertEqual(st.ladder("codehealth"), [("AS SHIPPED", "")])
        self.assertEqual([t for _, t in st.ladder("perceived_productivity")],
                         ["", ".repaired-R1", ".repaired-R1-R2"])

    def test_as_shipped_ok(self):
        a = self.run_dir("20261101T100000Z", {"codehealth.outputs.txt": "STATUS: OK\n"})
        chosen, steps, complete = st.pick_run("codehealth", [a])
        self.assertEqual((chosen["step"], len(steps), complete), ("AS SHIPPED", 1, True))

    def test_repairs_in_order(self):
        a = self.run_dir("20261101T100000Z", {"perceived_productivity.outputs.txt": failed_outputs()})
        b = self.run_dir("20261101T110000Z", {"perceived_productivity.repaired-R1.outputs.txt": failed_outputs()})
        c = self.run_dir("20261101T120000Z", {"perceived_productivity.repaired-R1-R2.outputs.txt": self.pp()})
        chosen, steps, _ = st.pick_run("perceived_productivity", [a, b, c])
        self.assertEqual(chosen["step"], "REPAIRS R1,R2")
        self.assertEqual([s["status"] for s in steps], ["FAILED", "FAILED", "OK"])

    def test_missing_next_repair_is_in_progress(self):
        a = self.run_dir("20261101T100000Z", {"perceived_productivity.outputs.txt": failed_outputs()})
        self.assertEqual(st.pick_run("perceived_productivity", [a])[::2], (None, False))

    def test_all_steps_failed_is_blocked(self):
        a = self.run_dir("20261101T100000Z", {"codehealth.outputs.txt": failed_outputs()})
        self.assertEqual(st.pick_run("codehealth", [a])[::2], (None, True))

    def test_no_run_is_in_progress(self):
        self.assertEqual(st.pick_run("coverage", [])[::2], (None, False))

    def test_repair_before_as_shipped_is_refused(self):
        a = self.run_dir("20261101T100000Z", {"perceived_productivity.repaired-R1.outputs.txt": self.pp()})
        b = self.run_dir("20261101T110000Z", {"perceived_productivity.outputs.txt": failed_outputs()})
        with self.assertRaises(ValueError):
            st.pick_run("perceived_productivity", [a, b])

    def test_repair_after_ok_is_refused(self):
        a = self.run_dir("20261101T100000Z", {"perceived_productivity.outputs.txt": self.pp()})
        b = self.run_dir("20261101T110000Z", {"perceived_productivity.repaired-R1.outputs.txt": self.pp()})
        with self.assertRaises(ValueError):
            st.pick_run("perceived_productivity", [a, b])

    def test_same_step_in_two_runs_is_refused(self):
        a = self.run_dir("20261101T100000Z", {"coverage.outputs.txt": "STATUS: OK\n"})
        b = self.run_dir("20261101T110000Z", {"coverage.outputs.txt": "STATUS: OK\n"})
        with self.assertRaises(ValueError):
            st.pick_run("coverage", [a, b])


if __name__ == "__main__":
    unittest.main()
