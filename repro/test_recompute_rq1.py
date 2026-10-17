"""
Tests for recompute_rq1.py (task 6b). Synthetic data only - no study data is read.

    python -m unittest repro/test_recompute_rq1.py -v

The reference functions below are copied from the authors' frequentist notebooks
(Cliff's delta loop, Cohen's d), so passing means our vectorised versions give the
same numbers as the code the paper used.
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recompute_rq1 as rq1  # noqa: E402


def authors_cliffs_delta(x, y):  # coverage.ipynb / completion_time.ipynb
    more = sum(i > j for i in x for j in y)
    less = sum(i < j for i in x for j in y)
    return (more - less) / (len(x) * len(y))


def authors_cohens_d(group1, group2):  # codehealth.ipynb / perceived_productivity.ipynb
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    pooled_std = np.sqrt(((len(group1) - 1) * std1**2 + (len(group2) - 1) * std2**2)
                         / (len(group1) + len(group2) - 2))
    return (mean1 - mean2) / pooled_std


def synthetic_frame(seed=0):
    """75 rows shaped like task2_preprocessed.csv: 40 ai, 35 human, some NaNs, plus junk rows."""
    g = np.random.default_rng(seed)
    n = 75
    df = pd.DataFrame({
        "treatment": ["ai"] * 40 + ["human"] * 35,
        "clean_time": g.integers(3000, 15000, n).astype(float),
        "pp_mean": np.round(g.uniform(2, 5, n), 1),
        "codehealth": np.round(g.normal(8.45, 0.2, n), 2),
        "coverage": np.round(g.uniform(0.6, 0.8, n), 2),
    })
    df.loc[[3, 50, 51], ["clean_time", "pp_mean"]] = np.nan
    junk = pd.DataFrame({"treatment": [np.nan, np.nan], "clean_time": [np.nan, 33.0]})
    return pd.concat([df, junk], ignore_index=True)


class EffectSizes(unittest.TestCase):
    def test_cliffs_delta_matches_authors_loop_with_ties(self):
        g = np.random.default_rng(1)
        for _ in range(20):
            x = g.integers(0, 10, g.integers(5, 40))
            y = g.integers(0, 10, g.integers(5, 40))
            self.assertAlmostEqual(rq1.cliffs_delta(x, y), authors_cliffs_delta(x, y), places=12)

    def test_cliffs_delta_bounds(self):
        self.assertEqual(rq1.cliffs_delta([5, 6], [1, 2]), 1.0)
        self.assertEqual(rq1.cliffs_delta([1, 2], [5, 6]), -1.0)
        self.assertEqual(rq1.cliffs_delta([1, 1], [1, 1]), 0.0)

    def test_cohens_d_matches_authors(self):
        g = np.random.default_rng(2)
        for _ in range(20):
            x, y = g.normal(0, 1, 40), g.normal(0.3, 1.5, 35)
            self.assertAlmostEqual(rq1.cohens_d(x, y), authors_cohens_d(x, y), places=12)


class Bootstrap(unittest.TestCase):
    def test_same_seed_same_ci(self):
        data = np.random.default_rng(3).normal(size=40)
        a = rq1.bootstrap_ci(data, np.mean, np.random.default_rng(7), resamples=5000)
        b = rq1.bootstrap_ci(data, np.mean, np.random.default_rng(7), resamples=5000)
        self.assertEqual(a, b)

    def test_ci_brackets_centre(self):
        data = np.random.default_rng(4).normal(10, 2, 40)
        for centre in (np.mean, np.median):
            lo, hi = rq1.bootstrap_ci(data, centre, np.random.default_rng(8), resamples=5000)
            self.assertLess(lo, centre(data))
            self.assertGreater(hi, centre(data))

    def test_chunking_does_not_change_result(self):
        data = np.random.default_rng(5).normal(size=30)
        old = rq1.CHUNK
        try:
            rq1.CHUNK = 7
            small = rq1.bootstrap_ci(data, np.median, np.random.default_rng(9), resamples=700)
            rq1.CHUNK = 700
            big = rq1.bootstrap_ci(data, np.median, np.random.default_rng(9), resamples=700)
        finally:
            rq1.CHUNK = old
        # different batching draws the same stream in the same order
        self.assertEqual(small, big)


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.df = synthetic_frame()
        self.res = rq1.run(self.df, resamples=2000, seed=11)

    def test_group_sizes_follow_per_metric_dropna(self):
        self.assertEqual((self.res["codehealth"]["n_treatment"], self.res["codehealth"]["n_control"]), (40, 35))
        self.assertEqual((self.res["coverage"]["n_treatment"], self.res["coverage"]["n_control"]), (40, 35))
        self.assertEqual((self.res["completion_time"]["n_treatment"], self.res["completion_time"]["n_control"]), (39, 33))
        self.assertEqual((self.res["perceived_productivity"]["n_treatment"], self.res["perceived_productivity"]["n_control"]), (39, 33))

    def test_tests_match_scipy_directly(self):
        t = self.df[self.df.treatment == "ai"]
        c = self.df[self.df.treatment == "human"]
        r = stats.ranksums(t.coverage.dropna(), c.coverage.dropna())
        self.assertEqual(self.res["coverage"]["p"], float(r.pvalue))
        s = stats.ttest_ind(t.codehealth, c.codehealth, equal_var=True)
        w = stats.ttest_ind(t.codehealth, c.codehealth, equal_var=False)
        self.assertEqual(self.res["codehealth"]["p"], float(s.pvalue))
        self.assertEqual(self.res["codehealth"]["welch_p"], float(w.pvalue))

    def test_time_reported_in_minutes(self):
        t = self.df[self.df.treatment == "ai"].clean_time.dropna()
        self.assertAlmostEqual(self.res["completion_time"]["treatment_centre"], t.median() / 60)

    def test_whole_run_is_repeatable(self):
        self.assertEqual(self.res, rq1.run(self.df, resamples=2000, seed=11))


if __name__ == "__main__":
    unittest.main()
