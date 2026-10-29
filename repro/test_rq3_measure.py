"""
Tests for rq3_measure.py (task 8c). Made-up notebooks and modules only - the authors' notebooks are not read.

    python -m unittest repro/test_rq3_measure.py -v
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rq3_measure as m  # noqa: E402

SHARED = """def cliffs_delta(x, y):
    greater = 0
    lesser = 0
    for i in x:
        for j in y:
            if i > j:
                greater += 1
            elif i < j:
                lesser += 1
    return (greater - lesser) / (len(x) * len(y))
"""


def notebook(*cells, markdown=1):
    nb = {"cells": [{"cell_type": "markdown", "source": ["# title\n"]}] * markdown, "nbformat": 4}
    for c in cells:
        nb["cells"].append({"cell_type": "code", "source": c.splitlines(keepends=True)})
    return json.dumps(nb)


class Measure(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_repo = m.REPO
        m.REPO = Path(self.tmp.name)

    def tearDown(self):
        m.REPO = self.old_repo
        self.tmp.cleanup()

    def write(self, rel, text):
        path = m.REPO / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return rel

    def run_measure(self, files, window=5):
        texts, info, groups, totals = m.measure(files, None, window)
        return info, {g["name"]: g for g in groups}, totals


class Lines(unittest.TestCase):
    def test_norm_lines_drop_comments_and_blanks(self):
        src = "x = 1  # set x\n\n# only a comment\ny  =  (x +\n      2)\n"
        self.assertEqual(m.norm_lines(src), [(1, "x = 1"), (4, "y = ( x + 2 )")])

    def test_sloc_counts_continuation_lines(self):
        src = "x = 1\n\n# c\ny = (x +\n     2)\n"
        self.assertEqual(m.sloc_lines(src), {1, 4, 5})

    def test_crlf_is_normalised(self):
        with tempfile.TemporaryDirectory() as d:
            old = m.REPO
            m.REPO = Path(d)
            try:
                (Path(d) / "a.py").write_bytes(b"x = 1\r\ny = 2\r\n")
                self.assertEqual(m.read_text("a.py", None), "x = 1\ny = 2\n")
            finally:
                m.REPO = old


class Functions(Measure):
    def test_identical_copies_ignore_docstring_and_comments(self):
        other = SHARED.replace("def cliffs_delta(x, y):\n",
                               'def cliffs_delta(x, y):\n    """Effect size."""\n    # count pairs\n')
        a = self.write("a.ipynb", notebook("import numpy as np", SHARED))
        b = self.write("b.ipynb", notebook(other))
        info, groups, totals = self.run_measure([a, b])
        g = groups["cliffs_delta"]
        self.assertEqual((g["copies"], g["variants"]), (2, 1))
        self.assertEqual(g["sloc_each"], [10, 11])  # the docstring is a code line; comments are not
        self.assertEqual(totals["copied_function_sloc"], 21)
        self.assertEqual(totals["copied_functions_not_identical"], [])

    def test_changed_body_is_a_second_version(self):
        changed = SHARED.replace("    greater = 0\n", "    x, y = x.dropna(), y.dropna()\n    greater = 0\n")
        a = self.write("a.ipynb", notebook(SHARED))
        b = self.write("b.ipynb", notebook(changed))
        _, groups, totals = self.run_measure([a, b])
        self.assertEqual(groups["cliffs_delta"]["variants"], 2)
        self.assertEqual(sorted(groups["cliffs_delta"]["variant_each"]), [0, 1])
        self.assertEqual(totals["copied_functions_not_identical"], ["cliffs_delta"])

    def test_redefinition_in_one_file_is_not_a_copy(self):
        a = self.write("a.ipynb", notebook("def f():\n    return 1", "def f():\n    return 2"))
        b = self.write("b.ipynb", notebook("x = 1"))
        _, groups, totals = self.run_measure([a, b])
        self.assertEqual((groups["f"]["copies"], groups["f"]["in_files"]), (2, 1))
        self.assertEqual(totals["functions_copied_across_files"], 0)

    def test_single_file_functions_are_not_copies(self):
        a = self.write("a.ipynb", notebook("def f():\n    return 1\n"))
        b = self.write("b.ipynb", notebook("def g():\n    return 2\n"))
        _, groups, totals = self.run_measure([a, b])
        self.assertEqual(totals["functions_copied_across_files"], 0)
        self.assertEqual(totals["distinct_function_names"], 2)


class Clones(Measure):
    def test_shared_run_counts_in_both_files(self):
        a = self.write("a.ipynb", notebook(SHARED + "z = 1\n"))
        b = self.write("b.ipynb", notebook("w = 0\n" + SHARED))
        info, _, totals = self.run_measure([a, b])
        self.assertEqual(info[a]["duplicated_logical_lines"], 10)
        self.assertEqual(info[b]["duplicated_logical_lines"], 10)
        self.assertEqual(totals["duplicated_logical_lines"], 20)
        self.assertEqual(totals["logical_lines"], 22)

    def test_run_shorter_than_window_is_not_a_clone(self):
        four = "a = 1\nb = 2\nc = 3\nd = 4\n"
        a = self.write("a.ipynb", notebook(four + "e = 5\n"))
        b = self.write("b.ipynb", notebook(four + "f = 6\n"))
        info, _, _ = self.run_measure([a, b])
        self.assertEqual(info[a]["duplicated_logical_lines"], 0)
        info, _, _ = self.run_measure([a, b], window=4)
        self.assertEqual(info[a]["duplicated_logical_lines"], 4)

    def test_runs_do_not_cross_cells(self):
        a = self.write("a.ipynb", notebook("a = 1\nb = 2\nc = 3\n", "d = 4\ne = 5\n"))
        b = self.write("b.ipynb", notebook("a = 1\nb = 2\nc = 3\nd = 4\ne = 5\n"))
        info, _, _ = self.run_measure([a, b])
        self.assertEqual(info[b]["duplicated_logical_lines"], 0)

    def test_repeat_inside_one_file_is_not_cross_file(self):
        a = self.write("a.ipynb", notebook(SHARED, SHARED.replace("cliffs_delta", "again")))
        b = self.write("b.ipynb", notebook("x = 1\n"))
        info, _, _ = self.run_measure([a, b])
        self.assertEqual(info[a]["duplicated_logical_lines"], 0)

    def test_py_module_is_measured_whole(self):
        mod = self.write("stats.py", SHARED)
        nb = self.write("a.ipynb", notebook("from stats import cliffs_delta", SHARED))
        info, _, _ = self.run_measure([mod, nb])
        self.assertIsNone(info[mod]["cells"])
        self.assertEqual(info[mod]["sloc"], 10)
        self.assertEqual(info[mod]["duplicated_logical_lines"], 10)


class Faults(Measure):
    def test_missing_import_is_reported(self):
        a = self.write("a.ipynb", notebook("from scipy.stats import levene",
                                           "print(len(shapiro([1, 2, 3])), levene)\ndisplay(1)"))
        info, _, totals = self.run_measure([a])
        self.assertEqual(info[a]["faults"]["undefined_names"], ["shapiro"])
        self.assertEqual(totals["files_with_undefined_names"], [a])

    def test_parameters_loop_and_except_names_are_bound(self):
        a = self.write("a.ipynb", notebook("def f(x):\n    for i in x:\n        pass\n    return i",
                                           "try:\n    f([1])\nexcept ValueError as err:\n    print(err)"))
        info, _, _ = self.run_measure([a])
        self.assertEqual(info[a]["faults"]["undefined_names"], [])

    def test_data_paths_and_prefixes(self):
        a = self.write("a.ipynb", notebook('import pandas as pd\nd = pd.read_csv("../data/t.csv")'))
        b = self.write("b.ipynb", notebook('import pandas as pd\nd = pd.read_csv("data/t.csv")'))
        info, _, totals = self.run_measure([a, b])
        self.assertEqual(info[a]["faults"]["data_paths"], ["../data/t.csv"])
        self.assertEqual(totals["distinct_data_path_prefixes"], ["../data/", "data/"])

    def test_unseeded_and_seeded_random(self):
        draw = "import numpy as np\nv = np.random.choice([1, 2], size=2)"
        a = self.write("a.ipynb", notebook(draw))
        b = self.write("b.ipynb", notebook("np.random.seed(4928)\n" + draw))
        c = self.write("c.ipynb", notebook("import numpy as np\nrng = np.random.default_rng(4928)\n"
                                           "v = rng.choice([1, 2])"))
        d = self.write("d.ipynb", notebook("import numpy as np\nrng = np.random.default_rng()\n"
                                           "v = np.random.choice([1, 2])"))
        e = self.write("e.py", "import numpy as np\nrng = np.random.default_rng()\nv = rng.choice([1, 2])\n")
        info, _, totals = self.run_measure([a, b, c, d, e])
        self.assertEqual(info[a]["faults"]["random_calls"], {"np.random.choice": 1})
        self.assertTrue(info[a]["faults"]["unseeded_random"])
        self.assertFalse(info[b]["faults"]["unseeded_random"])
        self.assertFalse(info[c]["faults"]["unseeded_random"])
        self.assertTrue(info[d]["faults"]["unseeded_random"])
        self.assertEqual(info[e]["faults"]["random_calls"], {"np.random.default_rng": 1})
        self.assertEqual(totals["files_with_unseeded_random"], [a, d, e])

    def test_seed_without_argument_is_not_a_seed(self):
        a = self.write("a.ipynb", notebook("import numpy as np\nnp.random.seed()\nv = np.random.choice([1, 2])"))
        info, _, _ = self.run_measure([a])
        self.assertEqual(info[a]["faults"]["seed_calls"], [])
        self.assertTrue(info[a]["faults"]["unseeded_random"])

    def test_magics_are_ignored(self):
        a = self.write("a.ipynb", notebook("%load_ext autoreload\n%autoreload 2\nimport numpy as np",
                                           "!pip list\nx = np.mean([1])"))
        info, _, _ = self.run_measure([a])
        self.assertEqual((info[a]["sloc"], info[a]["code_lines"]), (2, 5))
        self.assertEqual(info[a]["faults"]["undefined_names"], [])

    def test_seed_from_a_variable_is_not_a_seed(self):
        a = self.write("a.py", "import numpy as np\ndef boot(x, seed=None):\n"
                               "    rng = np.random.default_rng(seed)\n    return np.random.choice(x)\n")
        b = self.write("b.py", "import numpy as np\nrng = np.random.default_rng(seed=4928)\n")
        c = self.write("c.py", "import random\nrandom.shuffle([1, 2])\n")
        info, _, _ = self.run_measure([a, b, c])
        self.assertEqual(info[a]["faults"]["random_calls"], {"np.random.choice": 1, "np.random.default_rng": 1})
        self.assertTrue(info[a]["faults"]["unseeded_random"])
        self.assertEqual(info[b]["faults"]["seed_calls"], ["np.random.default_rng"])
        self.assertEqual(info[c]["faults"]["random_calls"], {"random.shuffle": 1})

    def test_cell_counts(self):
        a = self.write("a.ipynb", notebook("x = 1", "y = 2", markdown=3))
        info, _, _ = self.run_measure([a])
        self.assertEqual((info[a]["code_cells"], info[a]["cells"]), (2, 5))

    def test_function_cell_is_its_position_among_all_cells(self):
        a = self.write("a.ipynb", notebook("x = 1", "def f():\n    return 1", markdown=2))
        mod = self.write("m.py", "def g():\n    return 2\n")
        info, _, _ = self.run_measure([a, mod])
        self.assertEqual(info[a]["functions"][0]["cell"], 3)
        self.assertIsNone(info[mod]["functions"][0]["cell"])


class GitRefAndReport(Measure):
    def test_reads_the_file_at_a_git_ref_not_the_worktree(self):
        git = ["git", "-C", str(m.REPO), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        subprocess.run(git[:3] + ["init", "-q"], check=True)
        self.write("a.py", "x = 1\r\n")
        subprocess.run(git + ["add", "a.py"], check=True)
        subprocess.run(git + ["commit", "-qm", "c"], check=True)
        subprocess.run(git + ["tag", "T"], check=True)
        self.write("a.py", "x = 2\n")
        self.assertEqual(m.read_text("a.py", "T"), "x = 1\n")
        self.assertEqual(m.read_text("a.py", None), "x = 2\n")
        with self.assertRaises(SystemExit):
            m.read_text("missing.py", "T")

    def test_report_shows_logical_lines_and_no_python_version(self):
        a = self.write("a.ipynb", notebook(SHARED))
        b = self.write("b.ipynb", notebook(SHARED))
        _, info, groups, totals = m.measure([a, b], None, 5)
        text = m.report({"ref": "WORKTREE", "commit": "WORKTREE", "window": 5, "run_utc": "R"},
                        info, groups, totals)
        self.assertIn("logic", text)
        self.assertNotIn("python", text)
        self.assertIn("cliffs_delta                     x2  identical", text)


if __name__ == "__main__":
    unittest.main()
