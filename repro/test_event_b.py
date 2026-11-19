"""Event B failure handling and replay of the saved successful output.

Notebook execution is replaced with controlled output, so these tests need no
Jupyter kernel. The real build checks, measurements and scoring still run.
"""
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import nbformat

sys.path.insert(0, str(Path(__file__).resolve().parent))
import event_b


class TestEventB(unittest.TestCase):
    def setUp(self):
        self.source = event_b.REPO
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        files = set(event_b.EXISTING + event_b.DATA + [
            event_b.NEW, event_b.PRE_COPY, "frequentist/stats.py",
            "repro/test_stats.py", "repro/event_b.py", "repro/rq3_measure.py", "repro/run_all.py",
        ])
        for rel in files:
            dest = self.repo / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.source / rel, dest)
        self.originals = {rel: (self.repo / rel).read_bytes()
                          for rel in (event_b.NEW, event_b.PRE_COPY)}
        nb = nbformat.read(self.source / event_b.NEW, as_version=4)
        self.saved_stdout = "\n".join(event_b.printed(event_b.dump_outputs(nb))) + "\n"
        self.expected = json.loads((self.source / "evidence/event_b/generated/"
                                   "20261110T174012Z/result.json").read_text())
        self.counter = 0
        self.patch_repo = mock.patch.object(event_b, "REPO", self.repo)
        self.patch_repo.start()
        self.addCleanup(self.patch_repo.stop)
        self.patch_git = mock.patch.object(event_b, "git_show", side_effect=self.git_show)
        self.patch_git.start()
        self.addCleanup(self.patch_git.stop)

    def git_show(self, ref, rel):
        return subprocess.check_output(["git", "-C", str(self.source), "show", f"{ref}:{rel}"]
                                       ).decode("utf-8")

    def invoke(self, statuses=("OK", "OK"), text=None):
        self.counter += 1
        stamp = f"20990101T0000{self.counter:02d}Z"
        out = self.repo / "evidence/event_b/generated" / stamp
        output = self.saved_stdout if text is None else text
        calls = iter(statuses)

        def execute(nb, workdir):
            for cell in nb.cells:
                if cell.cell_type == "code":
                    cell.outputs, cell.execution_count = [], None
            first = next(c for c in nb.cells if c.cell_type == "code")
            first.outputs = [nbformat.v4.new_output("stream", name="stdout", text=output)]
            return next(calls), 0.0

        with mock.patch.object(event_b, "execute", side_effect=execute), \
                mock.patch.object(event_b, "datetime") as clock, \
                mock.patch("sys.stdout", new_callable=io.StringIO), \
                mock.patch("sys.stderr", new_callable=io.StringIO):
            clock.now.return_value.strftime.return_value = stamp
            try:
                event_b.run()
                exit_code = 0
            except SystemExit as exc:
                exit_code = exc.code
        return exit_code, out, json.loads((out / "result.json").read_text())

    def assert_failed(self, code, out, result):
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "FAILED")
        for key in ("p_value", "conclusion", "scores", "verdict"):
            self.assertNotIn(key, result)
        self.assertIn("No predictions were scored", (out / "report.txt").read_text())
        for rel, original in self.originals.items():
            self.assertEqual((self.repo / rel).read_bytes(), original, rel)
        self.assertFalse(any(out.glob("measure_*")))

    def test_either_failed_notebook_blocks_scoring_even_with_valid_output(self):
        for statuses in (("FAILED: kernel died", "OK"), ("OK", "FAILED: kernel died"),
                         ("FAILED: kernel died", "FAILED: kernel died")):
            with self.subTest(statuses=statuses):
                code, out, result = self.invoke(statuses=statuses)
                self.assert_failed(code, out, result)
                self.assertIn("kernel died", result["reason"])
                for label, status in zip(("pre_m4", "modernised"), statuses):
                    self.assertTrue((out / f"{label}.outputs.txt").read_text()
                                    .startswith(f"STATUS: {status}\n"))
                self.assertTrue((out / "environment.txt").exists())

    def test_missing_p_value_does_not_become_a_conclusion(self):
        code, out, result = self.invoke(text="some partial output\n")
        self.assert_failed(code, out, result)
        self.assertIn("no rank-sum p-value", result["reason"])

    def test_invalid_p_values_preserve_notebooks(self):
        for value in ("nan", "inf", "-inf", "-0.1", "1.1", "invalid"):
            with self.subTest(value=value):
                text = f"Wilcoxon Rank-Sum Test: Statistic=0.1, p-value={value}\n"
                self.assert_failed(*self.invoke(text=text))

    def test_valid_p_values_include_zero_and_one(self):
        for value in ("0", "1", "7.3770e-01"):
            with self.subTest(value=value):
                text = f"Wilcoxon Rank-Sum Test: Statistic=0.1, p-value={value}\n"
                self.assertEqual(event_b.parse_p_value(text), float(value))

    def test_successful_replay_keeps_recorded_metrics_and_verdict(self):
        code, out, result = self.invoke()
        self.assertEqual(code, 0)
        for key in ("p_value", "conclusion", "scores", "verdict", "p4_outside_new", "p5"):
            self.assertEqual(result[key], self.expected[key], key)
        for label, metrics in result["metrics"].items():
            for key, value in metrics.items():
                if key != "run_seconds":
                    self.assertEqual(value, self.expected["metrics"][label][key], (label, key))
        self.assertEqual(len(list(out.glob("measure_*"))), 4)
        modernised = nbformat.read(self.repo / event_b.NEW, as_version=4)
        self.assertEqual(modernised.cells[event_b.CONCLUSION_CELL].source, result["conclusion"])
        self.assertTrue(any(c.get("outputs") for c in modernised.cells))
        baseline = nbformat.read(self.repo / event_b.PRE_COPY, as_version=4)
        self.assertFalse(any(c.get("outputs") for c in baseline.cells))


if __name__ == "__main__":
    unittest.main()
