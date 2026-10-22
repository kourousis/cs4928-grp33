"""Checks for the task 6e extractor, including the observed nested-label traps."""

import copy
import json
import unittest
from collections import Counter

from inspect_rq2_sample import REPO, SOURCES, build_outputs, index_entries, inspect, top_rules


class SampleInspectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cs, cls.pmd = [json.loads((REPO / name).read_text(encoding="utf-8"))
                          for name in SOURCES]
        cls.result = inspect(cls.cs, cls.pmd)

    def test_locked_sample_and_independent_6d_totals(self):
        # Cross-checked against Enda's saved 6d run at b5ed3107, not derived
        # from this extractor. Also checked directly against the source reports.
        expected = [
            (0, 592, 1, 0, 1, 0, 0, -1), (1, 536, 2, 0, 1, 1, 0, -1),
            (2, 510, 0, 1, 1, 0, 0, -1), (3, 502, 0, 1, 0, 0, 0, -1),
            (4, 527, 0, 1, 0, 0, 0, -1), (5, 523, 0, 1, 0, 0, 0, -1),
            (6, 527, 0, 0, 0, 0, 0, 0), (7, 586, 2, 0, 1, 0, 0, -2),
            (8, 693, 4, 0, 0, 0, 0, -4), (9, 681, 0, 0, 1, 0, 0, 0),
            (10, 496, 0, 1, 0, 0, 0, -1), (11, 566, 1, 1, 0, 0, 0, -2),
        ]
        keys = ("id", "pmd_total", "introduced", "degraded", "unchanged",
                "improved", "fixed", "net_smell_change")
        self.assertEqual([tuple(row[k] for k in keys) for row in self.result["summary"]], expected)

    def test_nested_changes_do_not_become_extra_findings(self):
        rows = self.result["findings"]
        self.assertEqual(len(rows), 22)
        self.assertEqual(Counter(row["change_type"] for row in rows),
                         {"introduced": 10, "degraded": 6, "unchanged": 5, "improved": 1})
        nested_traps = {(0, "String Heavy Function Arguments"): "unchanged",
                        (1, "Bumpy Road Ahead"): "unchanged",
                        (2, "Bumpy Road Ahead"): "unchanged",
                        (7, "Excess Number of Function Arguments"): "unchanged",
                        (9, "Code Duplication"): "unchanged",
                        (11, "Complex Method"): "degraded"}
        for key, change in nested_traps.items():
            selected = [r for r in rows if (r["id"], r["category"]) == key]
            self.assertEqual(len(selected), 1)
            self.assertEqual(selected[0]["change_type"], change)

    def test_sample_selected_by_id_even_if_source_arrays_reordered(self):
        result = inspect(list(reversed(self.cs)), self.pmd[10:] + self.pmd[:10])
        self.assertEqual(result["summary"], self.result["summary"])

    def test_duplicate_and_missing_ids_fail(self):
        with self.assertRaises(ValueError):
            index_entries([self.cs[0], self.cs[0]])
        with self.assertRaises(ValueError):
            inspect(self.cs[1:], self.pmd)

    def test_top_rule_cutoff_keeps_ties(self):
        self.assertEqual(top_rules(Counter(A=8, B=5, D=3, C=3, E=1)),
                         [("A", 8), ("B", 5), ("C", 3), ("D", 3)])
        self.assertEqual(top_rules(Counter()), [])

    def test_empty_smell_entry_is_retained(self):
        row = self.result["summary"][6]
        self.assertEqual(row["id"], 6)
        self.assertEqual(row["smell_file_records"], 0)
        self.assertEqual(row["net_smell_change"], 0)
        self.assertEqual(row["pmd_total"], 527)

    def test_pmd_rules_and_scopes_reconcile_with_each_total(self):
        for row in self.result["summary"]:
            entry_id = row["id"]
            self.assertEqual(sum(r["count"] for r in self.result["pmd_rules"]
                                 if r["id"] == entry_id), row["pmd_total"])
            self.assertEqual(row["pmd_main"] + row["pmd_test"] + row["pmd_other"],
                             row["pmd_total"])
        self.assertEqual(sum(row["pmd_total"] for row in self.result["summary"]), 6739)
        self.assertGreater(sum(row["pmd_test"] for row in self.result["summary"]), 0)

    def test_errors_and_suppression_cannot_silently_disappear(self):
        for key in ("processingErrors", "configurationErrors", "suppressedViolations"):
            pmd = copy.deepcopy(self.pmd[:1])
            pmd[0]["content"][key] = [{"message": "test error"}]
            with self.assertRaises(ValueError):
                inspect(self.cs[:1], pmd, sample_ids=(0,))

    def test_source_pointers_resolve_to_original_records(self):
        def resolve(data, pointer):
            for token in pointer.lstrip("/").split("/"):
                data = data[int(token)] if isinstance(data, list) else data[token]
            return data
        for row in self.result["findings"]:
            original = resolve(self.cs, row["pointer"])
            self.assertEqual(original["category"], row["category"])
            self.assertEqual(original["change-type"], row["change_type"])
        for row in self.result["pmd_rules"]:
            original = resolve(self.pmd, row["example_pointer"])
            self.assertEqual(original["rule"], row["rule"])
            self.assertEqual(original["description"], row["example_description"])

    def test_test_files_and_all_categories_retained(self):
        rows = self.result["findings"]
        self.assertTrue(any(r["file"].startswith("src/test/") for r in rows))
        self.assertTrue(any(r["category"] == "Missing Arguments Abstractions" for r in rows))
        self.assertEqual(self.result["summary"][8]["introduced"], 4)

    def test_unknown_change_type_fails(self):
        cs = copy.deepcopy(self.cs[:1])
        cs[0]["content"][0]["findings"][0]["change-type"] = "removed"
        with self.assertRaises(ValueError):
            inspect(cs, self.pmd[:1], sample_ids=(0,))

    def test_outputs_deterministic(self):
        self.assertEqual(build_outputs(), build_outputs())


if __name__ == "__main__":
    unittest.main()
