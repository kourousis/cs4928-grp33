"""
Tests for recompute_rq1b.py (task 6c). Made-up strings in the package's format only.

    python -m unittest repro/test_recompute_rq1b.py -v
"""
import math
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recompute_rq1b as rq1b  # noqa: E402

MAIN_A = "info: ./src/main/java/x/A.java:1: Code health score: 8.50 warn: ./src/main/java/x/A.java:12: Complex Method (cc = 9) "
MAIN_B = "info: ./src/main/java/x/B.java:1: Code health score: 10.00 "
TEST_C = "info: ./src/test/java/x/CTest.java:1: Code health score: 7.00 warn: ./src/test/java/x/CTest.java:3: Code Duplication (null) "
NULL_D = "info: ./src/main/java/x/Repo.java:1: Code health score: nu "


class ParseLine(unittest.TestCase):
    def test_score_and_path(self):
        self.assertEqual(rq1b.parse_file_line(MAIN_A), ("./src/main/java/x/A.java", 8.5))

    def test_warning_text_is_ignored(self):
        # "(null)" in a warning must not be read as a null score
        self.assertEqual(rq1b.parse_file_line(TEST_C), ("./src/test/java/x/CTest.java", 7.0))

    def test_null_score(self):
        self.assertEqual(rq1b.parse_file_line(NULL_D), ("./src/main/java/x/Repo.java", None))

    def test_unexpected_lines_stop_the_run(self):
        for bad in ("warn: ./src/main/A.java:3: Complex Method ",
                    "info: ./src/main/A.java:1: Code health score: 8.5x ",
                    MAIN_A + MAIN_B,
                    "info: src/main/java/x/A.java:1: Code health score: 8.50 ",     # no ./
                    "info: ./target/generated/A.java:1: Code health score: 8.50 "):
            with self.assertRaises(ValueError):
                rq1b.parse_file_line(bad)


class EntryMeans(unittest.TestCase):
    def test_unweighted_means(self):
        row = rq1b.entry_row({"id": 3, "content": [MAIN_A, MAIN_B, TEST_C, NULL_D]})
        self.assertEqual((row["n_files"], row["n_null"], row["n_scored_all"], row["n_scored_main"]), (4, 1, 3, 2))
        self.assertAlmostEqual(row["mean_all"], (8.5 + 10.0 + 7.0) / 3)
        self.assertAlmostEqual(row["mean_main"], (8.5 + 10.0) / 2)

    def test_no_main_files_gives_nan(self):
        row = rq1b.entry_row({"id": 0, "content": [TEST_C]})
        self.assertTrue(math.isnan(row["mean_main"]))


class Shape(unittest.TestCase):
    def test_expected_shape_passes(self):
        rq1b.check_shape([{"id": i, "content": []} for i in range(3)], pd.Series([8.0, 8.5, 9.0]), n=3)

    def test_wrong_shape_stops_the_run(self):
        good = [{"id": i, "content": []} for i in range(3)]
        for entries, published in ((good[:2], pd.Series([8.0, 8.5, 9.0])),              # too few entries
                                   ([good[1], good[0], good[2]], pd.Series([8.0, 8.5, 9.0])),  # out of order
                                   ([dict(good[0], sloc=1), *good[1:]], pd.Series([8.0, 8.5, 9.0])),  # extra key
                                   (good, pd.Series([8.0, 8.5])),                         # too few published
                                   (good, pd.Series([8.0, None, 9.0]))):                  # missing published
            with self.assertRaises(ValueError):
                rq1b.check_shape(entries, published, n=3)


class Run(unittest.TestCase):
    def test_entry_without_scored_main_file_stops_the_run(self):
        df = pd.DataFrame({"treatment": ["ai"], "codehealth": [8.0]})
        with self.assertRaises(ValueError):
            rq1b.run([{"id": 0, "content": [TEST_C, NULL_D]}], df)

    def test_summary_uses_only_rows_with_treatment(self):
        entries = [{"id": 0, "content": [MAIN_A]}, {"id": 1, "content": [MAIN_B, NULL_D]}]
        df = pd.DataFrame({"treatment": ["ai", "human", None], "codehealth": [8.0, 9.0, None]})
        rows, s = rq1b.run(entries, df)
        self.assertEqual(list(rows["id"]), [0, 1])
        self.assertEqual((s["files"], s["null_scores"], s["entries_with_null"]), (3, 1, 1))
        self.assertEqual(s["json_entry_keys"], ["content", "id"])
        self.assertEqual(s["published_codehealth"]["n"], 2)
        self.assertAlmostEqual(s["published_codehealth"]["mean"], 8.5)
        self.assertAlmostEqual(s["recomputed_unweighted_all"]["mean"], (8.5 + 10.0) / 2)


if __name__ == "__main__":
    unittest.main()
