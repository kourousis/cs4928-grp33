"""
CS4928 G33 / P32 - Change Event B: one follow-up feature added to both variants.

The feature (EVENT_B_PLAN.md, section 2): analyse a fifth Phase 2 outcome, `test_runs`,
in the same style as the existing notebooks. Shapiro-Wilk rejects normality in both groups,
so the plan's rule picks the non-parametric template, coverage.ipynb.

    pre-M4      coverage.ipynb as it is at PRE_EVENT_A (its own helper copies), copied
                and edited -> evidence/event_b/pre_m4_variant/test_runs.ipynb
    modernised  coverage.ipynb as it is at PRE_EVENT_B (imports frequentist/stats.py),
                copied and edited -> frequentist/test_runs.ipynb

Both copies get exactly the same edits (EDITS below), so any difference between them
comes from the template, not from how it was edited.

    python repro/event_b.py build      # write the two notebooks (no running)
    python repro/event_b.py run        # run both, measure, compare (~10 min)

`run` writes to evidence/event_b/generated/<UTC timestamp>/:
    report.txt / result.json       M1 to M5 and the P1 to P5 scores
    pre_m4.outputs.txt, modernised.outputs.txt   everything each notebook printed
    measure_<state>/measure.txt|json   repro/rq3_measure.py's own report for 4 states
    environment.txt, inputs_sha256.txt
The pre-M4 copy is run with the seed added in memory, as rq3_verify.py did for "before",
from a temporary folder laid out like the repo (it reads ../data/).
"""
import argparse
import ast
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

import nbformat
from nbclient import NotebookClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rq3_measure  # noqa: E402  (used unchanged; only its file reader is pointed at our texts)
from run_all import DATA, PKGS, dump_outputs, sha256_normalised  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
PRE_REF, MOD_REF = "PRE_EVENT_A", "PRE_EVENT_B"
TEMPLATE = "frequentist/coverage.ipynb"
NEW = "frequentist/test_runs.ipynb"
PRE_COPY = "evidence/event_b/pre_m4_variant/test_runs.ipynb"
EXISTING = ["frequentist/codehealth.ipynb", "frequentist/completion_time.ipynb",
            "frequentist/coverage.ipynb", "frequentist/perceived_productivity.ipynb"]
SEED_LINE = "np.random.seed(4928)"

# The edits a developer makes to the copied template, applied in order to every cell.
# Cell 5 of the template describes 'codehealth' (an upstream slip); the new outcome needs test_runs.
EDITS = [
    ("# Code coverage", "# Test runs"),
    ("['codehealth']", "['test_runs']"),
    ("TC ", "test runs "),
    ("Code Coverage", "Test Runs"),
    ("Test Coverage", "Test Runs"),
    ("'Coverage'", "'Test Runs'"),
    ("coverage", "test_runs"),
    ("cov_", "tr_"),
]
# Cell 14's conclusion is rewritten once the rank-sum result is known (see `conclude`).
CONCLUSION_CELL = 14
P_LINE = re.compile(r"Wilcoxon Rank-Sum Test: Statistic=(\S+), p-value=(\S+)")


def git_show(ref, rel):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{ref}:{rel}"],
                          capture_output=True, check=True).stdout.decode("utf-8")


def build_one(ref):
    template = nbformat.reads(git_show(ref, TEMPLATE), as_version=4)
    nb = nbformat.reads(git_show(ref, TEMPLATE), as_version=4)
    changed = []
    for i, cell in enumerate(nb.cells):
        src = cell.source
        for old, new in EDITS:
            src = src.replace(old, new)
        if cell.cell_type == "code":
            cell.outputs, cell.execution_count = [], None
        if src != template.cells[i].source:
            changed.append({"cell": i, "type": cell.cell_type})
        cell.source = src
    return nb, template, changed


def build():
    for ref, rel in ((PRE_REF, PRE_COPY), (MOD_REF, NEW)):
        nb, _, changed = build_one(ref)
        (REPO / rel).parent.mkdir(parents=True, exist_ok=True)
        nbformat.write(nb, REPO / rel)
        print(f"{rel}: from {TEMPLATE} at {ref}, {len(changed)} cells edited")


def conclude(nb, p_value):
    text = ("We reject the null hypothesis of no difference." if p_value < 0.05 else
            "We do not reject the null hypothesis of no difference.")
    nb.cells[CONCLUSION_CELL].source = text
    return text


def execute(nb, workdir):
    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.outputs, cell.execution_count = [], None
    t0 = time.time()
    status = "OK"
    try:
        NotebookClient(nb, timeout=None, kernel_name="python3",
                       resources={"metadata": {"path": str(workdir)}}).execute()
    except Exception as e:  # recorded, never hidden
        status = f"FAILED: {str(e).strip().splitlines()[-1] if str(e).strip() else type(e).__name__}"
    finally:
        shutil.rmtree(Path(workdir) / "figures", ignore_errors=True)
    return status, time.time() - t0


def printed(text):
    return [l for l in text.splitlines() if not l.startswith("--- cell ")]


def measure_texts(texts):
    """rq3_measure.measure() on texts we supply, plus the inside/outside-function split."""
    original = rq3_measure.read_text
    rq3_measure.read_text = lambda rel, ref: texts[rel]
    try:
        _, files, groups, totals = rq3_measure.measure(list(texts), None, rq3_measure.WINDOW)
    finally:
        rq3_measure.read_text = original
    # measure() drops the cell texts it used, so analyse the same texts again for the split
    fresh = {rel: rq3_measure.analyse_file(rel, t) for rel, t in texts.items()}
    dup = rq3_measure.clone_lines(fresh, rq3_measure.WINDOW)
    inside = 0
    for rel, info in files.items():
        if len(dup[rel]) != info["duplicated_logical_lines"]:
            sys.exit(f"{rel}: clone count mismatch")
        spans = set()
        for cell_no, src in enumerate(fresh[rel]["_cells"]):
            for node in ast.parse(src).body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    spans.update((cell_no, ln) for ln in range(node.lineno, node.end_lineno + 1))
        inside += len(dup[rel] & spans)
        info["duplicated_inside_functions"] = len(dup[rel] & spans)
    totals["duplicated_inside_functions"] = inside
    totals["duplicated_outside_functions"] = totals["duplicated_logical_lines"] - inside
    return files, groups, totals


def save_measure(out, label, ref_note, texts):
    files, groups, totals = measure_texts(texts)
    meta = {"task": "Event B", "ref": ref_note, "commit": ref_note, "window": rq3_measure.WINDOW,
            "files": list(texts), "run_utc": out.name}
    d = out / f"measure_{label}"
    d.mkdir()
    for f in files.values():
        f.pop("_cells", None)
        for fn in f["functions"]:
            fn.pop("ast", None)
    (d / "measure.json").write_text(json.dumps({"meta": meta, "totals": totals, "files": files,
                                                "function_groups": groups}, indent=2) + "\n", encoding="utf-8")
    text = rq3_measure.report(meta, files, groups, totals)
    text += (f"\nDuplicated logical lines inside function bodies: {totals['duplicated_inside_functions']}, "
             f"outside: {totals['duplicated_outside_functions']}\n")
    (d / "measure.txt").write_text(text, encoding="utf-8")
    return files, groups, totals


def run():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REPO / "evidence" / "event_b" / "generated" / stamp
    out.mkdir(parents=True)
    with open(out / "environment.txt", "w", encoding="utf-8") as f:
        f.write(f"python {sys.version}\nplatform {platform.platform()}\n")
        for p in PKGS:
            try:
                f.write(f"{p}=={version(p)}\n")
            except PackageNotFoundError:
                f.write(f"{p} NOT INSTALLED\n")

    # ---- build both again in memory, to check the files on disk are the plain builds
    built = {}
    for label, ref, rel in (("pre_m4", PRE_REF, PRE_COPY), ("modernised", MOD_REF, NEW)):
        nb, template, changed = build_one(ref)
        disk = nbformat.read(REPO / rel, as_version=4)
        extra = [i for i, (a, b) in enumerate(zip(nb.cells, disk.cells))
                 if a.source != b.source and i != CONCLUSION_CELL]
        if len(nb.cells) != len(disk.cells) or extra:
            sys.exit(f"{rel} differs from its build in cells {extra}: rebuild it first")
        built[label] = {"nb": disk, "changed": changed, "template_cells": len(template.cells)}

    # ---- M5b: run both copies
    runs = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "frequentist").mkdir()
        (tmp / "data").mkdir()
        for rel in DATA:
            (tmp / rel).write_text(git_show(PRE_REF, rel), encoding="utf-8")
        pre = built["pre_m4"]["nb"]
        run_pre = nbformat.from_dict(json.loads(json.dumps(pre)))
        first = next(c for c in run_pre.cells if c.cell_type == "code")
        first.source = first.source.rstrip("\n") + "\n\n" + SEED_LINE
        status, secs = execute(run_pre, tmp / "frequentist")
        runs["pre_m4"] = (run_pre, status, secs, "seed line added in memory to the first code cell")
    run_mod = built["modernised"]["nb"]
    status, secs = execute(run_mod, REPO / "frequentist")
    runs["modernised"] = (run_mod, status, secs, "run unchanged")

    texts_out = {}
    for label, (nb, status, secs, note) in runs.items():
        text = dump_outputs(nb)
        texts_out[label] = text
        (out / f"{label}.outputs.txt").write_text(f"STATUS: {status}\n" + text, encoding="utf-8")

    m = P_LINE.search(texts_out["modernised"])
    p_value = float(m.group(2)) if m else float("nan")
    conclusion = conclude(run_mod, p_value)
    conclude(built["pre_m4"]["nb"], p_value)
    nbformat.write(run_mod, REPO / NEW)  # the shipped notebook keeps its (seeded) outputs
    nbformat.write(built["pre_m4"]["nb"], REPO / PRE_COPY)  # evidence copy: no outputs, no seed

    # ---- M4: design quality of four states, via rq3_measure's own code
    new_text_pre = (REPO / PRE_COPY).read_text(encoding="utf-8")
    new_text_mod = (REPO / NEW).read_text(encoding="utf-8")
    pre_before = {rel: git_show(PRE_REF, rel) for rel in EXISTING}
    pre_after = dict(pre_before, **{NEW: new_text_pre})
    mod_files = ["frequentist/stats.py"] + EXISTING
    mod_before = {rel: git_show(MOD_REF, rel) for rel in mod_files}
    mod_after = {rel: (REPO / rel).read_text(encoding="utf-8") for rel in mod_files}
    mod_after[NEW] = new_text_mod
    meas = {}
    for label, note, texts in (("pre_m4_before", PRE_REF, pre_before),
                               ("pre_m4_after", f"{PRE_REF} + {PRE_COPY} as {NEW}", pre_after),
                               ("modernised_before", MOD_REF, mod_before),
                               ("modernised_after", f"working tree ({MOD_REF} + {NEW})", mod_after)):
        files, groups, totals = save_measure(out, label, note, texts)
        meas[label] = {"files": files, "groups": groups, "totals": totals}

    def new_file(label):
        return meas[f"{label}_after"]["files"][NEW]

    # ---- M1, M2, M3
    changed_existing = [rel for rel in mod_files + ["repro/test_stats.py"]
                        if (REPO / rel).read_bytes().replace(b"\r\n", b"\n")
                        != git_show(MOD_REF, rel).replace("\r\n", "\n").encode("utf-8")]
    m = {}
    for label in ("pre_m4", "modernised"):
        nf = new_file(label)
        changed = built[label]["changed"] + [{"cell": CONCLUSION_CELL, "type": "markdown"}]
        changed = sorted({c["cell"]: c for c in changed}.values(), key=lambda c: c["cell"])
        before, after = meas[f"{label}_before"]["totals"], meas[f"{label}_after"]["totals"]
        m[label] = {
            "M1_cells_edited": len(changed),
            "M1_code_cells_edited": sum(c["type"] == "code" for c in changed),
            "M1_markdown_cells_edited": sum(c["type"] == "markdown" for c in changed),
            "M1_other_files_changed": changed_existing if label == "modernised" else [],
            "M2_files_added": [NEW],
            "M2_new_file_sloc": nf["sloc"],
            "M2_new_file_logical_lines": nf["logical_lines"],
            "M2_new_file_functions": [(f["name"], f["sloc"]) for f in nf["functions"]],
            "M2_new_file_function_sloc": sum(f["sloc"] for f in nf["functions"]),
            "M3_test_files_changed": [r for r in changed_existing if "test" in r],
            "M4_copied_functions": [before["functions_copied_across_files"], after["functions_copied_across_files"]],
            "M4_copied_function_sloc": [before["copied_function_sloc"], after["copied_function_sloc"]],
            "M4_dup_logical": [before["duplicated_logical_lines"], after["duplicated_logical_lines"]],
            "M4_logical": [before["logical_lines"], after["logical_lines"]],
            "M4_dup_share": [before["duplicated_share"], after["duplicated_share"]],
            "M4_dup_inside_functions": [before["duplicated_inside_functions"], after["duplicated_inside_functions"]],
            "M4_dup_outside_functions": [before["duplicated_outside_functions"], after["duplicated_outside_functions"]],
            "M4_new_file_faults": nf["faults"],
            "M4_copied_not_identical_after": after["copied_functions_not_identical"],
            "run_status": runs[label][1], "run_seconds": round(runs[label][2]), "run_note": runs[label][3],
        }

    # ---- M5a: the four existing notebooks, stats.py and the data are byte-identical to PRE_EVENT_B,
    # so (with the seed set in each notebook) they print exactly what they printed at PRE_EVENT_B.
    same_inputs = not [r for r in changed_existing if r != "repro/test_stats.py"] and all(
        (REPO / r).read_bytes().replace(b"\r\n", b"\n") == git_show(MOD_REF, r).replace("\r\n", "\n").encode("utf-8")
        for r in DATA)
    lines_pre, lines_mod = printed(texts_out["pre_m4"]), printed(texts_out["modernised"])
    same_numbers = runs["pre_m4"][1] == "OK" and runs["modernised"][1] == "OK" and lines_pre == lines_mod

    # ---- score P1 to P5 exactly as written in EVENT_B_PLAN.md
    pre_added_fns = m["pre_m4"]["M4_copied_function_sloc"][1] - m["pre_m4"]["M4_copied_function_sloc"][0]
    pre_added_n = len(m["pre_m4"]["M2_new_file_functions"])
    mod_added_n = len(m["modernised"]["M2_new_file_functions"])
    out_pre = m["pre_m4"]["M4_dup_outside_functions"][1] - m["pre_m4"]["M4_dup_outside_functions"][0]
    out_mod = m["modernised"]["M4_dup_outside_functions"][1] - m["modernised"]["M4_dup_outside_functions"][0]
    p4_ratio = (min(out_pre, out_mod) / max(out_pre, out_mod)) if max(out_pre, out_mod) else 1.0
    scores = {
        "P1": not changed_existing,
        "P2": pre_added_n >= 3 and m["pre_m4"]["M2_new_file_function_sloc"] >= 25 and mod_added_n == 0,
        "P3": m["modernised"]["M1_cells_edited"] < m["pre_m4"]["M1_cells_edited"],
        "P4": max(out_pre, out_mod) == 0 or abs(out_pre - out_mod) <= 0.2 * max(out_pre, out_mod),
        "P5": same_inputs and same_numbers,
    }
    if scores["P1"] and scores["P2"] and scores["P5"]:
        verdict = "SUPPORTED"
    elif scores["P5"] and (scores["P1"] or scores["P2"]):
        verdict = "PARTLY SUPPORTED"
    else:
        verdict = "SHOULD BE REVISED"

    rep = [f"Event B run {stamp}",
           f"feature: {NEW} from {TEMPLATE}; pre-M4 base {PRE_REF}, modernised base {MOD_REF}",
           f"rank-sum p-value = {p_value:.4e} -> cell {CONCLUSION_CELL}: {conclusion!r}", ""]
    for label in ("pre_m4", "modernised"):
        rep.append(f"[{label}]")
        for k, v in m[label].items():
            rep.append(f"    {k:<32} {v}")
        rep.append("")
    rep += [f"P4 detail: new duplicated logical lines outside functions: pre-M4 {out_pre}, modernised {out_mod}",
            f"P5 detail: existing notebooks/stats.py/data unchanged = {same_inputs}; "
            f"test_runs printed lines identical = {same_numbers} ({len(lines_pre)} vs {len(lines_mod)} lines)", ""]
    rep += [f"{k}: {'HOLDS' if v else 'FAILS'}" for k, v in scores.items()]
    rep += ["", f"VERDICT (EVENT_B_PLAN.md section 5): Week 9 decision {verdict}"]
    (out / "report.txt").write_text("\n".join(rep) + "\n", encoding="utf-8")
    (out / "result.json").write_text(json.dumps({
        "stamp": stamp, "p_value": p_value, "conclusion": conclusion, "metrics": m,
        "p4_outside_new": {"pre_m4": out_pre, "modernised": out_mod, "ratio": round(p4_ratio, 3)},
        "p5": {"existing_unchanged": same_inputs, "test_runs_identical": same_numbers},
        "scores": scores, "verdict": verdict}, indent=2) + "\n", encoding="utf-8")
    hashes = [f"{sha256_normalised(REPO / r)}  {r}" for r in
              mod_files + [NEW, PRE_COPY, "repro/event_b.py", "repro/rq3_measure.py", "repro/run_all.py"] + DATA]
    (out / "inputs_sha256.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    print("\n".join(rep))
    print(f"done -> {out.relative_to(REPO).as_posix()}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=["build", "run"])
    {"build": build, "run": run}[ap.parse_args().step]()
