"""
CS4928 G33 / P32 - RQ1 bounded reproduction runner ("run everything").

Re-executes the authors' four Phase 2 frequentist notebooks EXACTLY AS SHIPPED
and saves every output into a new timestamped folder. The original notebooks
are never modified.

    python repro/run_all.py            # run all four
    python repro/run_all.py codehealth # run one (pilot)
    python repro/run_all.py --repairs R1 perceived_productivity
    python repro/run_all.py --repairs R1,R2 perceived_productivity
        # re-run with repairs declared in M1_PLAN.md, applied to an in-memory copy
        # (the authors' file is untouched). Only use these AFTER the as-shipped run
        # has been recorded, and in this order, so each fault is captured in a run.

For each run it writes to repro/runs/<UTC timestamp>/:
    <name>.executed.ipynb   fresh execution, all outputs
    <name>.outputs.txt      plain-text dump of every cell's printed output
    figures/                any figures the notebooks save
    run_log.txt             start/end, status, and the error if a notebook fails
    environment.txt         python + library versions actually used
    inputs_sha256.txt       hashes of the notebooks and data files used
                            (line endings normalised so Windows/Linux agree)

A notebook that fails is recorded as FAILED with its error and the run carries
on - do not "fix" it silently. Any fix is a deviation: record it first.
"""
import hashlib
import platform
import re
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

import nbformat
from nbclient import NotebookClient

REPO = Path(__file__).resolve().parent.parent
NB_DIR = REPO / "frequentist"
NOTEBOOKS = ["codehealth", "completion_time", "coverage", "perceived_productivity"]
DATA = ["data/task1_preprocessed.csv", "data/task2_preprocessed.csv"]
# Repairs declared in M1_PLAN.md before any reported run. Each is an exact
# (old, new) text replacement in one code cell's source; nothing else changes.
# A replacement that doesn't match exactly once aborts the run.
DECLARED_REPAIRS = {
    "perceived_productivity": {
        # R1: data path - the other three notebooks use ../data/ from frequentist/
        "R1": [('pd.read_csv("data/task1_preprocessed.csv")', 'pd.read_csv("../data/task1_preprocessed.csv")'),
               ('pd.read_csv("data/task2_preprocessed.csv")', 'pd.read_csv("../data/task2_preprocessed.csv")')],
        # R2: missing import - shapiro is called but never imported
        "R2": [("from scipy.stats import ttest_ind", "from scipy.stats import ttest_ind\nfrom scipy.stats import shapiro")],
    },
}
KERNEL_VERSIONS = (
    "import sys, importlib.metadata as m\n"
    "print('kernel python', sys.version.replace(chr(10), ' '))\n"
    "print('kernel executable', sys.executable)\n"
    "for p in %r:\n"
    "    print(p + '==' + m.version(p))\n"
)
PKGS = ["numpy", "pandas", "scipy", "matplotlib", "seaborn", "nbclient", "nbformat", "ipykernel"]
KERNEL_PKGS = ["numpy", "pandas", "scipy", "matplotlib", "seaborn"]


def sha256_normalised(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def dump_outputs(nb) -> str:
    lines = []
    for i, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        lines.append(f"--- cell {i} (execution_count={cell.get('execution_count')}) ---")
        for out in cell.get("outputs", []):
            if out.get("output_type") == "stream":
                lines.append(out.get("text", "").rstrip())
            elif out.get("output_type") == "error":
                lines.append(f"ERROR {out.get('ename')}: {out.get('evalue')}")
            else:
                data = out.get("data", {})
                if "image/png" in data:
                    lines.append("[figure]")
                elif "text/plain" in data:
                    lines.append(data["text/plain"].rstrip())
    return "\n".join(lines) + "\n"


def main(selected, repairs=()):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REPO / "repro" / "runs" / stamp
    out.mkdir(parents=True)
    log = open(out / "run_log.txt", "w", encoding="utf-8")

    def say(msg):
        print(msg)
        log.write(msg + "\n")
        log.flush()

    # environment record
    with open(out / "environment.txt", "w", encoding="utf-8") as f:
        f.write(f"python {sys.version}\nplatform {platform.platform()}\n")
        for p in PKGS:
            try:
                f.write(f"{p}=={version(p)}\n")
            except PackageNotFoundError:
                f.write(f"{p} NOT INSTALLED\n")
        # versions as seen INSIDE the kernel that executes the notebooks
        probe = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(KERNEL_VERSIONS % (KERNEL_PKGS,))])
        NotebookClient(probe, timeout=120, kernel_name="python3").execute()
        f.write("\n# inside the notebook kernel\n" + "".join(o.get("text", "") for o in probe.cells[0].outputs))

    # input identity record
    with open(out / "inputs_sha256.txt", "w", encoding="utf-8") as f:
        for rel in [f"frequentist/{n}.ipynb" for n in selected] + DATA + ["repro/requirements.txt", "repro/run_all.py"]:
            f.write(f"{sha256_normalised(REPO / rel)}  {rel}\n")

    fig_dirs = [NB_DIR / "figures"]
    stale = [d for d in fig_dirs if d.exists()]
    if stale:
        log.close()
        sys.exit(f"stale figures folder(s) {stale}: move them away first so old figures can't enter this run")
    say(f"run {stamp}  repo={REPO}  mode={('DECLARED REPAIRS ' + ','.join(repairs)) if repairs else 'AS SHIPPED'}")
    for name in selected:
        src = NB_DIR / f"{name}.ipynb"
        nb = nbformat.read(src, as_version=4)
        # Wipe the authors' stored outputs so nothing in this run's files can be
        # a leftover from their machine (a failed cell must not leave old results below it).
        for cell in nb.cells:
            if cell.cell_type == "code":
                cell.outputs = []
                cell.execution_count = None
        # Execute with frequentist/ as the working directory, which is where
        # the notebooks' relative paths (../data/...) expect to run from.
        tag = ""
        if repairs:
            known = DECLARED_REPAIRS.get(name, {})
            missing = [r for r in repairs if r not in known]
            if missing:
                log.close()
                sys.exit(f"[{name}] no declared repair(s) {missing} for this notebook")
            tag = ".repaired-" + "-".join(repairs)
            for old, new in [pair for r in repairs for pair in known[r]]:
                hits = [c for c in nb.cells if c.cell_type == "code" and c.source.count(old) == 1]
                if len(hits) != 1:
                    log.close()
                    sys.exit(f"[{name}] declared repair did not match exactly once: {old!r}")
                hits[0].source = hits[0].source.replace(old, new)
                say(f"[{name}] applied declared repair: {old!r} -> {new!r}")
        client = NotebookClient(nb, timeout=None, kernel_name="python3",
                                resources={"metadata": {"path": str(NB_DIR)}})
        t0 = time.time()
        status = "OK"
        try:
            client.execute()
        except Exception as e:  # keep the failure visible, keep going
            status = "FAILED"
            last = re.sub(r"\x1b\[[0-9;]*m", "", str(e)).strip().splitlines()
            say(f"[{name}] FAILED: {last[-1] if last else type(e).__name__}")
            log.write(traceback.format_exc() + "\n")
        nbformat.write(nb, out / f"{name}{tag}.executed.ipynb")
        header = f"STATUS: {status}\n" + ("Cells after the failing cell were NOT executed.\n" if status != "OK" else "")
        (out / f"{name}{tag}.outputs.txt").write_text(header + dump_outputs(nb), encoding="utf-8")
        say(f"[{name}] {status} in {time.time() - t0:.0f}s")

    # move the figures this run wrote into the run folder
    for d in fig_dirs:
        if d.exists():
            shutil.copytree(d, out / "figures", dirs_exist_ok=True)
            shutil.rmtree(d)  # did not exist before this run (checked above)
    say(f"done -> {out}")
    log.close()


if __name__ == "__main__":
    argv = sys.argv[1:]
    repairs = ()
    if "--repairs" in argv:
        i = argv.index("--repairs")
        repairs = tuple(argv[i + 1].split(","))
        argv = argv[:i] + argv[i + 2:]
    args = argv or NOTEBOOKS
    bad = [a for a in args if a not in NOTEBOOKS]
    if bad:
        sys.exit(f"unknown notebook(s): {bad}; choose from {NOTEBOOKS}")
    main(args, repairs)
