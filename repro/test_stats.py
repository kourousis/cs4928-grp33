# Tests for frequentist/stats.py (RQ3, task 9b)
# python -m unittest repro/test_stats.py

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "frequentist"))
import stats  # noqa: E402


class TestStats(unittest.TestCase):

    def test_cohens_d(self):
        # means 2 and 4, both variances 1, so d = -2
        self.assertAlmostEqual(stats.cohens_d([1, 2, 3], [3, 4, 5]), -2.0)
        self.assertAlmostEqual(stats.cohens_d([1, 2, 3, np.nan], [3, 4, 5]), -2.0)

    def test_cliffs_delta(self):
        self.assertEqual(stats.cliffs_delta([3, 4], [1, 2]), 1.0)
        self.assertEqual(stats.cliffs_delta([1, 2], [3, 4]), -1.0)
        self.assertEqual(stats.cliffs_delta([1, 2], [1, 2]), 0.0)
        # NaNs are dropped (the old codehealth/completion_time copy counted them as ties)
        self.assertEqual(stats.cliffs_delta([3, 4, np.nan], [1, 2]), 1.0)

    def test_magnitudes(self):
        self.assertEqual(stats.cliffs_magnitude(0.1), "negligible")
        self.assertEqual(stats.cliffs_magnitude(-0.147), "small")
        self.assertEqual(stats.cliffs_magnitude(0.474), "large")
        self.assertEqual(stats.cohens_magnitude(-0.21), "Small")
        self.assertEqual(stats.cohens_magnitude(0.8), "Large")

    def test_bootstrap_constant_data(self):
        self.assertEqual(stats.bootstrap_ci_mean([5.0] * 10, n_bootstraps=100), (5.0, 5.0, 5.0))
        self.assertEqual(stats.bootstrap_ci_median([5.0] * 10, n_bootstraps=100), (5.0, 5.0, 5.0))
        self.assertEqual(stats.bootstrap_ci_mean_difference([2.0] * 5, [1.0] * 4, n_bootstraps=100), (1.0, 1.0, 1.0))
        self.assertEqual(stats.bootstrap_ci_median_difference([2.0] * 5, [1.0] * 4, n_bootstraps=100), (1.0, 1.0, 1.0))

    def test_bootstrap_same_seed_same_result(self):
        data = [1, 4, 2, 8, 5, 7, 3]
        np.random.seed(4928)
        first = stats.bootstrap_ci_mean(data, n_bootstraps=1000)
        np.random.seed(4928)
        self.assertEqual(stats.bootstrap_ci_mean(data, n_bootstraps=1000), first)
        self.assertTrue(first[1] <= first[0] <= first[2])

    def test_load_data(self):
        task1_df, task2_df = stats.load_data()
        ai, manual, treatment, control = stats.split_groups(task1_df, task2_df)
        self.assertEqual((len(treatment), len(control)), (40, 35))


if __name__ == "__main__":
    unittest.main()
