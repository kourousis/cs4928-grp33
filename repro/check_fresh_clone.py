"""
CS4928 G33 / P32 - fresh-clone re-run check (task 7e).

Clones the group repo at a ref into an empty folder, builds the pinned
environment from scratch with uv, runs every test, re-runs every script and
compares the new outputs with the newest committed output folder of each:

    script              compared with              must be identical
    recompute_rq1.py    repro/recompute/<newest>   every number, CIs too (same seed, same NumPy)
    recompute_rq1b.py   repro/rq1b_codehealth/...  every file except environment.txt
    count_rq2.py        repro/rq2_counts/...       every file except environment.txt
    inspect_rq2_sample.py --check  evidence/rq2_qualitative/generated  every file (its own check)
    run_all.py          repro/runs/<newest>        the Phase 2 primary values (CIs are unseeded)
    rq1_status.py       repro/rq1_status/<newest>  every per-metric status and the headline

    python repro/check_fresh_clone.py                       # origin, main
    python repro/check_fresh_clone.py --ref enda/7b-rq1-status
    python repro/check_fresh_clone.py --skip-notebooks      # ~1 min instead of ~10-35

A script with no committed output folder is re-run and reported as "nothing
committed to compare". The run folder's own timestamp is masked before
comparing; inputs_sha256.txt is compared too, so a changed data file or script
since the committed run shows up. Writes to repro/fresh_clone/<UTC timestamp>/
in THIS checkout (not the clone); the temporary clone path is masked as <TMP>:
    report.txt          every step, its command, and every difference found
    environment.txt     the clone's python + library versions
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = [  # (script, output folder, extra args)
    ("recompute_rq1.py", "recompute", []),
    ("recompute_rq1b.py", "rq1b_codehealth", []),
    ("count_rq2.py", "rq2_counts", []),
]


def committed(clone, folder):
    root = clone / "repro" / folder
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.exists() else []


def masked(path, stamp):
    return path.read_text(encoding="utf-8").replace(stamp, "<RUN>")


def compare_folders(old, new, skip=("environment.txt",)):
    """Differences between two output folders of the same script, timestamps masked."""
    diffs = []
    old_files = {p.name for p in old.iterdir()} - set(skip)
    new_files = {p.name for p in new.iterdir()} - set(skip)
    for name in sorted(old_files ^ new_files):
        diffs.append(f"{name}: only in {'committed' if name in old_files else 'new'} run")
    for name in sorted(old_files & new_files):
        a, b = masked(old / name, old.name), masked(new / name, new.name)
        if a != b:
            al, bl = a.splitlines(), b.splitlines()
            first = next((i for i, (x, y) in enumerate(zip(al, bl)) if x != y), min(len(al), len(bl)))
            diffs.append(f"{name}: differs from line {first + 1}\n"
                         f"      committed: {al[first] if first < len(al) else '<end>'}\n"
                         f"      new:       {bl[first] if first < len(bl) else '<end>'}")
    return diffs


def compare_notebook_runs(clone, old_runs, new_runs):
    """Phase 2 primary values from the committed 6a runs vs the new ones, per notebook file."""
    sys.path.insert(0, str(clone / "repro"))
    import rq1_status as st
    diffs = []
    for metric in st.NOTEBOOKS:
        for _, tag in st.ladder(metric):
            name = f"{metric}{tag}.outputs.txt"
            old = [r / name for r in old_runs if (r / name).exists()]
            new = [r / name for r in new_runs if (r / name).exists()]
            if not old and not new:
                continue
            if len(old) != 1 or len(new) != 1:
                diffs.append(f"{name}: {len(old)} committed vs {len(new)} new")
                continue
            os_, ns = st.read_status(old[0]), st.read_status(new[0])
            if os_ != ns:
                diffs.append(f"{name}: committed {os_}, new {ns}")
            elif ns == "OK":
                a = st.parse_outputs(metric, old[0].read_text(encoding="utf-8"))
                b = st.parse_outputs(metric, new[0].read_text(encoding="utf-8"))
                for key in ("p", "effect", "treatment", "control"):
                    if a[key] != b[key]:
                        diffs.append(f"{name} {key}: committed {a[key]}, new {b[key]}")
    return diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=None, help="repo to clone (default: this checkout's origin)")
    ap.add_argument("--ref", default="main")
    ap.add_argument("--skip-notebooks", action="store_true", help="skip run_all.py and rq1_status.py")
    args = ap.parse_args()
    url = args.url or subprocess.run(["git", "-C", str(REPO), "remote", "get-url", "origin"],
                                     capture_output=True, text=True, check=True).stdout.strip()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REPO / "repro" / "fresh_clone" / stamp
    out.mkdir(parents=True)
    report = open(out / "report.txt", "w", encoding="utf-8")
    failures = 0

    masks = []  # the temp clone path, so the report has no machine-specific paths

    def say(msg=""):
        for m in masks:
            msg = msg.replace(m, "<TMP>")
        print(msg)
        report.write(msg + "\n")
        report.flush()

    def sh(cmd, cwd):
        say(f"$ {' '.join(cmd)}")
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
        for line in tail:
            say(f"    {line}")
        return r

    def verdict(step, diffs):
        nonlocal failures
        failures += bool(diffs)
        say(f"  {step}: {'IDENTICAL' if not diffs else f'{len(diffs)} DIFFERENCE(S)'}")
        for d in diffs:
            say(f"    - {d}")

    with tempfile.TemporaryDirectory(prefix="cs4928-fresh-") as tmp:
        clone = Path(tmp) / "clone"
        masks.append(str(Path(tmp).resolve()))
        masks.append(tmp)
        say(f"fresh-clone check {stamp}  url={url}  ref={args.ref}")
        if sh(["git", "clone", "--quiet", "--branch", args.ref, url, str(clone)], tmp).returncode:
            sys.exit("clone failed")
        head = subprocess.run(["git", "-C", str(clone), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        say(f"commit {head}\n")
        py = str(clone / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))
        for cmd in (["uv", "venv", "--quiet", "-p", "3.9", ".venv"],
                    ["uv", "pip", "install", "--quiet", "-p", ".venv", "-r", "repro/requirements.txt"]):
            if sh(cmd, clone).returncode:
                sys.exit("environment setup failed")
        freeze = subprocess.run(["uv", "pip", "freeze", "-p", ".venv"], cwd=clone, capture_output=True, text=True)
        version = subprocess.run([py, "--version"], capture_output=True, text=True)
        (out / "environment.txt").write_text(version.stdout + freeze.stdout, encoding="utf-8")

        say("\n[tests]")
        r = sh([py, "-m", "unittest", "discover", "-s", "repro", "-p", "test_*.py"], clone)
        verdict("unit tests", [] if r.returncode == 0 else ["unittest exited with " + str(r.returncode)])

        for script, folder, extra in SCRIPTS:
            say(f"\n[{script}]")
            before = committed(clone, folder)
            r = sh([py, f"repro/{script}", *extra], clone)
            after = [p for p in committed(clone, folder) if p not in before]
            if r.returncode or len(after) != 1:
                verdict(script, [f"run failed (exit {r.returncode}, {len(after)} new folder(s))"])
            elif not before:
                say(f"  {script}: nothing committed to compare; new run {after[0].name}")
            else:
                say(f"  committed {before[-1].name} vs new {after[0].name}")
                verdict(script, compare_folders(before[-1], after[0]))

        say("\n[inspect_rq2_sample.py --check]")
        r = sh([py, "repro/inspect_rq2_sample.py", "--check"], clone)
        verdict("inspect_rq2_sample.py (6e evidence reproduces)", [] if r.returncode == 0 else [f"exit {r.returncode}"])

        if not args.skip_notebooks:
            say("\n[run_all.py: as shipped, then the declared repairs]")
            old_runs = committed(clone, "runs")
            sh([py, "repro/run_all.py"], clone)
            sh([py, "repro/run_all.py", "--repairs", "R1", "perceived_productivity"], clone)
            sh([py, "repro/run_all.py", "--repairs", "R1,R2", "perceived_productivity"], clone)
            new_runs = [p for p in committed(clone, "runs") if p not in old_runs]
            if not old_runs:
                say(f"  run_all.py: nothing committed to compare; new runs {[p.name for p in new_runs]}")
            else:
                say(f"  committed {[p.name for p in old_runs]} vs new {[p.name for p in new_runs]}")
                verdict("run_all.py primary values", compare_notebook_runs(clone, old_runs, new_runs))

            say("\n[rq1_status.py on the new runs]")
            old_status = committed(clone, "rq1_status")
            r = sh([py, "repro/rq1_status.py", *[str(p) for p in new_runs]], clone)
            new_status = [p for p in committed(clone, "rq1_status") if p not in old_status]
            if r.returncode or len(new_status) != 1:
                verdict("rq1_status.py", [f"run failed (exit {r.returncode})"])
            elif not old_status:
                say("  rq1_status.py: nothing committed to compare")
            else:
                def statuses(p):
                    s = json.loads((p / "status.json").read_text(encoding="utf-8"))
                    return {"overall": s["overall"], **{m: v["status"] for m, v in s["metrics"].items()}}
                a, b = statuses(old_status[-1]), statuses(new_status[0])
                verdict("rq1_status.py statuses",
                        [f"{k}: committed {a[k]}, new {b.get(k)}" for k in a if a[k] != b.get(k)])

    say(f"\n{'ALL CHECKS PASSED' if not failures else f'{failures} CHECK(S) FAILED'}")
    report.close()
    print(f"done -> {out}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
