"""
Tests for count_rq2.py (task 6d). Small made-up JSON in the package's shape only.

    python -m unittest repro/test_count_rq2.py -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import count_rq2 as rq2  # noqa: E402


def finding(change, category="Complex Method", nested="improved"):
    # nested change-details deliberately disagree with the top-level type
    return {"category": category, "change-type": change,
            "change-details": [{"change-type": nested, "description": "..."}]}


def pmd_entry(i, per_file):
    return {"id": i, "content": {"pmdVersion": "7.13.0", "files": [
        {"filename": f"./src/{'test' if k else 'main'}/F{k}.java", "violations": [{"rule": "R"}] * n}
        for k, n in enumerate(per_file)]}}


class Pmd(unittest.TestCase):
    def test_counts_every_file_including_tests(self):
        self.assertEqual(rq2.pmd_total(pmd_entry(0, [3, 2, 0])["content"]), 5)

    def test_generated_code_is_counted_and_reported(self):
        e = pmd_entry(0, [3, 2])
        e["content"]["files"].append({"filename": "./target/generated-sources/annotations/G.java",
                                      "violations": [{"rule": "R"}] * 4})
        self.assertEqual(rq2.pmd_total(e["content"]), 9)
        self.assertEqual(rq2.pmd_outside_src(e["content"]), (1, 4))

    def test_pmd_errors_stop_the_run(self):
        rq2.check_pmd(pmd_entry(0, [1]))
        for key in rq2.PMD_MUST_BE_EMPTY:
            e = pmd_entry(0, [1])
            e["content"][key] = [{"filename": "x", "message": "boom"}]
            with self.assertRaises(ValueError):
                rq2.check_pmd(e)


class Smells(unittest.TestCase):
    def test_top_level_change_type_only(self):
        recs = [{"name": "src/main/A.java", "findings": [finding("introduced"), finding("fixed")]},
                {"hashed-file-name": "abc", "findings": [finding("degraded", "Bumpy Road Ahead")]}]
        self.assertEqual(rq2.smell_findings(recs), [("introduced", "Complex Method"),
                                                    ("fixed", "Complex Method"),
                                                    ("degraded", "Bumpy Road Ahead")])

    def test_net_change(self):
        counts = {"fixed": 3, "improved": 1, "introduced": 2, "degraded": 4, "unchanged": 9}
        self.assertEqual(rq2.net_smell_change(counts), -2)

    def test_unknown_change_type_stops_the_run(self):
        with self.assertRaises(ValueError):
            rq2.smell_findings([{"findings": [finding("removed")]}])


class HalfUp(unittest.TestCase):
    def test_half_up_on_hundredths(self):
        self.assertEqual(rq2.half_up(40, 7), 3)    # 2.8
        self.assertEqual(rq2.half_up(35, 10), 4)   # 3.5 -> 4 (Python's round() would give 4 too)
        self.assertEqual(rq2.half_up(35, 30), 11)  # 10.5 -> 11 (round() gives 10)
        self.assertEqual(rq2.half_up(40, 0), 0)


class Run(unittest.TestCase):
    def test_per_entry_and_pooled(self):
        pmd = [pmd_entry(0, [1, 1]), pmd_entry(1, [4])]
        delta = [{"id": 0, "content": [{"name": "A", "findings": [finding("fixed", "Bumpy Road Ahead")]}]},
                 {"id": 1, "content": []}]
        rows, findings, check = rq2.run(pmd, delta)
        self.assertEqual(list(rows["pmd_total"]), [2, 4])
        self.assertEqual(list(rows["net_smell_change"]), [1, 0])
        self.assertEqual(findings.to_dict("records"),
                         [{"id": 0, "change_type": "fixed", "category": "Bumpy Road Ahead", "count": 1}])
        self.assertEqual(len(check), 25)
        self.assertEqual(int(check["printed_in_paper"].sum()), 18)
        bra = check[(check.change_type == "fixed") & (check.category == "Bumpy Road Ahead")].iloc[0]
        self.assertEqual(bra.pooled_count, 1)
        self.assertEqual(bra.expected_count, 4 + 2)  # round(40 * 0.10) + round(35 * 0.06)

    def test_unprinted_table8_cell_must_be_zero(self):
        # improved / Code Duplication isn't printed in Table 8, so one finding there is a miss
        delta = [{"id": 0, "content": [{"name": "A", "findings": [finding("improved", "Code Duplication")]}]}]
        _, _, check = rq2.run([pmd_entry(0, [1])], delta)
        cell = check[(check.change_type == "improved") & (check.category == "Code Duplication")].iloc[0]
        self.assertFalse(cell.printed_in_paper)
        self.assertEqual((cell.expected_count, cell.pooled_count, cell.match), (0, 1, False))

    def test_findings_table_sums_to_per_entry_totals(self):
        delta = [{"id": 0, "content": [{"name": "A", "findings": [finding("fixed"), finding("fixed"),
                                                                  finding("introduced", "Bumpy Road Ahead")]},
                                       {"name": "B", "findings": [finding("fixed")]}]}]
        rows, findings, _ = rq2.run([pmd_entry(0, [1])], delta)
        self.assertEqual(findings.to_dict("records"),
                         [{"id": 0, "change_type": "fixed", "category": "Complex Method", "count": 3},
                          {"id": 0, "change_type": "introduced", "category": "Bumpy Road Ahead", "count": 1}])
        self.assertEqual(int(rows.loc[0, "fixed"]), 3)

    def test_id_order_must_agree(self):
        with self.assertRaises(ValueError):
            rq2.run([pmd_entry(0, [1]), pmd_entry(1, [1])], [{"id": 1, "content": []}, {"id": 0, "content": []}])


if __name__ == "__main__":
    unittest.main()
