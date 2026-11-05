"""
CS4928 G33 / P32 - RQ3 before/after check of the shared stats module (task 9c).

Applies criterion 1 of the RQ3 decision rule in M1_PLAN.md: every RQ1a primary
value must be identical before and after the restructuring, at full printed
precision, with CIs compared under the same fixed seed in both versions.

    before  the four notebooks as they were at --ref (default PRE_EVENT_A), with
            only the repairs already declared in M1_PLAN.md (R1, R2 for
            perceived_productivity, without which it cannot run) and the seed
            line added after the imports, applied to an in-memory copy
    after   the four notebooks as they are now on disk, run unchanged (they import
            frequentist/stats.py and set the same seed themselves)

Both versions run in the same environment, from frequentist/. The check compares
every line each notebook prints, in order (cell numbers are ignored, since the
restructuring removed cells that printed nothing), and lists the RQ1a primary
values parsed with the same parser as rq1_status.py.

    python repro/rq3_verify.py                     # all four (~10 min per version)
    python repro/rq3_verify.py coverage            # one notebook

Writes to repro/rq3_verify/<UTC timestamp>/:
    report.txt              verdict, primary values before/after, any differing line
    result.json             the same, machine-readable
    before/<name>.outputs.txt, after/<name>.outputs.txt   everything each version printed
    environment.txt         python + library versions
    inputs_sha256.txt       hashes of the notebooks (both versions), stats.py, data and scripts
Exits with status 1 if any notebook fails or any printed line differs.
"""
import argparse
import difflib
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

import nbformat
from nbclient import NotebookClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_all import NOTEBOOKS, DATA, DECLARED_REPAIRS, PKGS, dump_outputs, sha256_normalised  # noqa: E402
from rq1_status import parse_outputs  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
NB_DIR = REPO / "frequentist"
SEED = 4928
SEED_LINE = f"np.random.seed({SEED})"
BEFORE_REPAIRS = {"perceived_productivity": ("R1", "R2")}


def notebook_at(ref, name):
    text = subprocess.run(["git", "show", f"{ref}:frequentist/{name}.ipynb"], cwd=REPO,
                          capture_output=True, check=True).stdout.decode("utf-8")
    return nbformat.reads(text, as_version=4), text


def prepare_before(nb, name):
    """Declared repairs + the seed, on an in-memory copy. Returns the edits made."""
    edits = []
    for r in BEFORE_REPAIRS.get(name, ()):
        for old, new in DECLARED_REPAIRS[name][r]:
            hits = [c for c in nb.cells if c.cell_type == "code" and c.source.count(old) == 1]
            if len(hits) != 1:
                sys.exit(f"[{name}] declared repair {r} did not match exactly once: {old!r}")
            hits[0].source = hits[0].source.replace(old, new)
            edits.append(f"repair {r}: {old!r} -> {new!r}")
    first = next(c for c in nb.cells if c.cell_type == "code")
    if "np.random" in first.source or "import numpy as np" not in first.source:
        sys.exit(f"[{name}] first code cell is not the plain import cell; cannot add the seed safely")
    first.source = first.source.rstrip("\n") + "\n\n" + SEED_LINE
    edits.append(f"seed: {SEED_LINE!r} appended to the first code cell")
    return edits


def execute(nb):
    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    if (NB_DIR / "figures").exists():
        sys.exit("frequentist/figures exists: move it away first so old figures can't mix in")
    t0 = time.time()
    status = "OK"
    try:
        NotebookClient(nb, timeout=None, kernel_name="python3",
                       resources={"metadata": {"path": str(NB_DIR)}}).execute()
    except Exception as e:  # recorded, never hidden
        status = f"FAILED: {str(e).strip().splitlines()[-1] if str(e).strip() else type(e).__name__}"
    finally:
        shutil.rmtree(NB_DIR / "figures", ignore_errors=True)  # created by the notebook itself
    return status, time.time() - t0


def printed_lines(text):
    return [l for l in text.splitlines() if not l.startswith("--- cell ")]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("notebooks", nargs="*", default=NOTEBOOKS)
    ap.add_argument("--ref", default="PRE_EVENT_A", help="git ref of the 'before' notebooks")
    args = ap.parse_args()
    bad = [n for n in args.notebooks if n not in NOTEBOOKS]
    if bad:
        sys.exit(f"unknown notebook(s) {bad}; choose from {NOTEBOOKS}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REPO / "repro" / "rq3_verify" / stamp
    (out / "before").mkdir(parents=True)
    (out / "after").mkdir()

    with open(out / "environment.txt", "w", encoding="utf-8") as f:
        f.write(f"python {sys.version}\nplatform {platform.platform()}\n")
        for p in PKGS:
            try:
                f.write(f"{p}=={version(p)}\n")
            except PackageNotFoundError:
                f.write(f"{p} NOT INSTALLED\n")

    hashes = []
    results = {}
    report = [f"RQ3 before/after check {stamp}",
              f"before = frequentist/*.ipynb at {args.ref} (+ declared repairs, + seed {SEED}); "
              f"after = frequentist/*.ipynb on disk (seed {SEED} in the notebook)", ""]
    all_ok = True
    for name in args.notebooks:
        nb_before, raw = notebook_at(args.ref, name)
        digest = hashlib.sha256(raw.replace("\r\n", "\n").encode("utf-8")).hexdigest()
        hashes.append(f"{digest}  {args.ref}:frequentist/{name}.ipynb")
        edits = prepare_before(nb_before, name)
        status_b, secs_b = execute(nb_before)
        text_b = dump_outputs(nb_before)
        (out / "before" / f"{name}.outputs.txt").write_text(f"STATUS: {status_b}\n" + text_b, encoding="utf-8")

        path_after = NB_DIR / f"{name}.ipynb"
        hashes.append(f"{sha256_normalised(path_after)}  frequentist/{name}.ipynb")
        nb_after = nbformat.read(path_after, as_version=4)
        status_a, secs_a = execute(nb_after)
        text_a = dump_outputs(nb_after)
        (out / "after" / f"{name}.outputs.txt").write_text(f"STATUS: {status_a}\n" + text_a, encoding="utf-8")

        lines_b, lines_a = printed_lines(text_b), printed_lines(text_a)
        identical = status_b == "OK" and status_a == "OK" and lines_b == lines_a
        diff = list(difflib.unified_diff(lines_b, lines_a, "before", "after", lineterm="", n=0))
        try:
            prim_b, prim_a = parse_outputs(name, text_b), parse_outputs(name, text_a)
        except ValueError as e:
            prim_b = prim_a = {"error": str(e)}
            identical = False
        all_ok &= identical
        results[name] = {"identical": identical, "status_before": status_b, "status_after": status_a,
                         "seconds_before": round(secs_b), "seconds_after": round(secs_a),
                         "printed_lines": [len(lines_b), len(lines_a)], "before_edits": edits,
                         "primary_before": prim_b, "primary_after": prim_a, "diff": diff}
        report.append(f"[{name}] {'IDENTICAL' if identical else 'DIFFERENT'}  "
                      f"(before {status_b}, {len(lines_b)} lines, {secs_b:.0f}s; "
                      f"after {status_a}, {len(lines_a)} lines, {secs_a:.0f}s)")
        for e in edits:
            report.append(f"    before-run edit: {e}")
        for key in ("p", "effect", "treatment", "control", "treatment_ci", "control_ci"):
            if key in prim_b:
                report.append(f"    {key:<13} before {str(prim_b[key]):<22} after {prim_a.get(key)}")
        report.extend("    " + d for d in diff)
        print(report[-1] if diff else f"[{name}] {'IDENTICAL' if identical else 'DIFFERENT'}", flush=True)

    report += ["", "VERDICT: " + ("every printed line, including every RQ1a primary value and CI, is identical "
                                  "before and after" if all_ok else "NOT identical - see above")]
    (out / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (out / "result.json").write_text(json.dumps({"stamp": stamp, "ref": args.ref, "seed": SEED,
                                                 "all_identical": all_ok, "notebooks": results},
                                                indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for rel in ["frequentist/stats.py"] + DATA + ["repro/rq3_verify.py", "repro/run_all.py",
                                                  "repro/rq1_status.py", "repro/requirements.txt"]:
        hashes.append(f"{sha256_normalised(REPO / rel)}  {rel}")
    (out / "inputs_sha256.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    print(f"done -> {out}\nVERDICT: {'IDENTICAL' if all_ok else 'NOT IDENTICAL'}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
