"""
CS4928 G33 / P32 - RQ1a status per metric (task 7b).

Applies the M1_PLAN.md decision rule to the authors' notebooks as executed by
repro/run_all.py (task 6a), one metric at a time:

    primary    p-value, effect size, both point estimates and the significance
               call at alpha = 0.05 must all equal the paper's values after
               format(x, '.Nf'), with N = the decimals the paper prints
    secondary  bootstrap CIs vs the paper and vs the authors' stored output
               (+-0.01, +-1 min for time); reported, never changes the status
    audit      Welch's t-test (from the 6b recompute) next to the Student's
               t-test the notebooks actually run; reported, never changes the status

    python repro/rq1_status.py repro/runs/<as shipped> [repro/runs/<R1>] [repro/runs/<R1,R2>]
    python repro/rq1_status.py ... --recompute repro/recompute/<UTC>

The primary values are read from each notebook's <name>.outputs.txt as the
notebook printed them. Each one is cross-checked against the full-precision
6b recompute: if the two round differently at the paper's precision, the run
is flagged (the printed value still decides, as the plan says the status comes
from the as-shipped run).

A metric's run is the first OK step of its ladder: as shipped, then
--repairs R1, then --repairs R1,R2 (perceived_productivity only). Each step
must come from a later run than the step before and may only be used after
that step FAILED. Writes to repro/rq1_status/<UTC timestamp>/:
    status.json         every value, rounding and verdict
    status.txt          the same, human-readable
    environment.txt     python version
    inputs_sha256.txt   hashes of every file read, and this script
"""
import argparse
import json
import platform
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import nbformat

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recompute_rq1 import sha256_normalised  # noqa: E402
from run_all import NOTEBOOKS, dump_outputs, DECLARED_REPAIRS  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DEFAULT_RECOMPUTE = "repro/recompute/20261017T144852Z"
ALPHA = 0.05

# Paper values (M1_PLAN.md § RQ1a, checked against the paper text) and the decimals
# N the paper prints for each. "prose" is where the value is printed.
PAPER = {
    "completion_time": {"prose": "§4.2.1", "centre": "median",
                        "p": (0.56, 2), "effect": (-0.079, 3),
                        "treatment": (136, 0), "control": (173, 0),
                        "treatment_ci": (105.5, 180.0), "control_ci": (118.1, 210.0), "ci_noise": 1.0},
    "perceived_productivity": {"prose": "§4.2.2", "centre": "mean",
                               "p": (0.37, 2), "effect": (-0.21, 2),
                               "treatment": (3.95, 2), "control": (4.06, 2),
                               "treatment_ci": (3.77, 4.12), "control_ci": (3.88, 4.24), "ci_noise": 0.01},
    "codehealth": {"prose": "§4.3.1", "centre": "mean",
                   "p": (0.24, 2), "effect": (0.28, 2),
                   "treatment": (8.49, 2), "control": (8.44, 2),
                   "treatment_ci": (8.43, 8.54), "control_ci": (8.39, 8.49), "ci_noise": 0.01},
    "coverage": {"prose": "§4.3.2", "centre": "median",
                 "p": (0.49, 2), "effect": (0.09, 2),
                 "treatment": (0.70, 2), "control": (0.70, 2),
                 "treatment_ci": (0.695, 0.71), "control_ci": (0.69, 0.74), "ci_noise": 0.01},
}

# What each notebook prints for its Phase 2 comparison. Everything is read from the text
# before `end`, where the Task 1 sections (which reuse some of the same labels) start.
NUM = r"(-?\d+(?:\.\d+)?(?:e[-+]\d+)?)"
GROUP_CI = r"\(AI-assisted\):\s+{n}(?: min)?\s+\(95% CI: {n} - {n}(?: min)?\)"
PATTERNS = {
    "completion_time": {
        "end": "Bootstrap CI for the median difference",
        "p": r"Wilcoxon Rank-Sum Test \(Completion Time in seconds\):\n\s+Statistic = \S+\n\s+p-value\s+= " + NUM,
        "effect": r"Cliff’s Delta: δ=" + NUM,
    },
    "perceived_productivity": {
        "end": None,
        "p": r"Welch’s t-test on Perceived Productivity \(PP\):\n\s+t-statistic = \S+\n\s+p-value\s+= " + NUM,
        "effect": r"Cohen's d for Perceived Productivity \(PP Mean\): " + NUM,
    },
    "codehealth": {
        "end": "Bootstrap CI for the mean CodeHealth difference",
        "p": r"Welch’s t-test \(unequal variances assumed\):\n\s+t-statistic = \S+\n\s+p-value\s+= " + NUM,
        "effect": r"Cohen's d for CodeHealth: " + NUM,
    },
    "coverage": {
        "end": "Bootstrap CI for the median Test Coverage difference",
        "p": r"Wilcoxon Rank-Sum Test: Statistic=\S+, p-value=" + NUM,
        "effect": r"Cliff's Delta for Code Coverage: " + NUM,
    },
}
TREATMENT_LINE = r"Treatment " + GROUP_CI.format(n=NUM)
CONTROL_LINE = r"Control \(Manual\):\s+{n}(?: min)?\s+\(95% CI: {n} - {n}(?: min)?\)".format(n=NUM)


def once(pattern, text, what):
    hits = re.findall(pattern, text)
    if len(hits) != 1:
        raise ValueError(f"{what}: expected exactly one match, found {len(hits)}")
    return hits[0]


def parse_outputs(metric, text):
    """The Phase 2 values one notebook printed, as strings exactly as printed."""
    pat = PATTERNS[metric]
    if pat["end"] is not None:
        cut = text.find(pat["end"])
        if cut < 0 or text.count(pat["end"]) != 1:
            raise ValueError(f"{metric}: end marker {pat['end']!r} not found exactly once")
        text = text[:cut]
    t_centre, t_lo, t_hi = once(TREATMENT_LINE, text, f"{metric} treatment line")
    c_centre, c_lo, c_hi = once(CONTROL_LINE, text, f"{metric} control line")
    return {"p": once(pat["p"], text, f"{metric} p-value"),
            "effect": once(pat["effect"], text, f"{metric} effect size"),
            "treatment": t_centre, "control": c_centre,
            "treatment_ci": [t_lo, t_hi], "control_ci": [c_lo, c_hi]}


def rounds_to(value, n):
    """The paper's convention: format(x, '.Nf') on float64."""
    return format(float(value), f".{n}f")


def on_boundary(value, n):
    """True if the printed decimal sits exactly halfway between two N-decimal values."""
    d = Decimal(str(value)).scaleb(n)
    return d - d.to_integral_value(rounding="ROUND_FLOOR") == Decimal("0.5")


def primary_match(value, target, n):
    """Exact match after rounding, with the plan's boundary rule: a value exactly on a
    rounding boundary matches if the paper printed either neighbour."""
    paper = format(target, f".{n}f")
    ours = rounds_to(value, n)
    if ours == paper:
        return True, ours, False
    if on_boundary(value, n):
        step = Decimal(1).scaleb(-n)
        lo = Decimal(str(value)).quantize(step, rounding="ROUND_FLOOR")
        if paper in (format(lo, f".{n}f"), format(lo + step, f".{n}f")):
            return True, ours, True
    return False, ours, False


def ladder(metric):
    """Run-file tags in the order the plan allows them: as shipped, then each declared repair set."""
    steps = [("AS SHIPPED", "")]
    declared = list(DECLARED_REPAIRS.get(metric, {}))
    for i in range(1, len(declared) + 1):
        steps.append(("REPAIRS " + ",".join(declared[:i]), ".repaired-" + "-".join(declared[:i])))
    return steps


def read_status(path):
    first = path.read_text(encoding="utf-8").splitlines()[0]
    if first not in ("STATUS: OK", "STATUS: FAILED"):
        raise ValueError(f"{path}: unexpected first line {first!r}")
    return first.split(": ")[1]


def pick_run(metric, runs):
    """The run that decides this metric, and every ladder step that was looked at.

    Returns (chosen step or None, steps, complete): `complete` is True when no further
    declared step remains, i.e. a metric with no OK step is BLOCKED rather than IN PROGRESS."""
    steps = []
    previous = None
    for label, tag in ladder(metric):
        found = [r for r in runs if (r / f"{metric}{tag}.outputs.txt").exists()]
        if len(found) > 1:
            raise ValueError(f"{metric} {label}: found in more than one run {[r.name for r in found]}")
        if not found:
            return None, steps, False
        run = found[0]
        if previous is not None and run.name <= previous["run"]:
            raise ValueError(f"{metric} {label}: run {run.name} is not later than {previous['run']}")
        step = {"step": label, "run": run.name, "file": f"{metric}{tag}.outputs.txt",
                "status": read_status(run / f"{metric}{tag}.outputs.txt")}
        steps.append(step)
        if step["status"] == "OK":
            later = [r.name for _, t in ladder(metric)[len(steps):]
                     for r in runs if (r / f"{metric}{t}.outputs.txt").exists()]
            if later:
                raise ValueError(f"{metric}: {label} ran OK, so repaired runs {later} must not be used")
            return step, steps, True
        previous = step
    return None, steps, True


def stored_outputs(metric):
    """The authors' own stored output for this notebook, in the runner's text format."""
    return dump_outputs(nbformat.read(REPO / "frequentist" / f"{metric}.ipynb", as_version=4))


def ci_rows(metric, printed, stored, recomputed):
    target = PAPER[metric]
    rows = []
    for group in ("treatment", "control"):
        for i, bound in enumerate(("lower", "upper")):
            run_v = float(printed[f"{group}_ci"][i])
            paper_v = target[f"{group}_ci"][i]
            stored_v = float(stored[f"{group}_ci"][i])
            rows.append({"group": group, "bound": bound, "run": printed[f"{group}_ci"][i],
                         "paper": paper_v, "authors_stored": stored[f"{group}_ci"][i],
                         "recompute_6b": recomputed[f"{group}_ci95"][i],
                         "run_vs_paper_within_noise": abs(run_v - paper_v) <= target["ci_noise"] + 1e-9,
                         "paper_vs_stored_within_noise": abs(stored_v - paper_v) <= target["ci_noise"] + 1e-9})
    return rows


def decide(metric, printed, recomputed):
    """The primary-criteria verdict for one completed run."""
    target = PAPER[metric]
    values = {"p": (printed["p"], recomputed["p"]),
              "effect": (printed["effect"], recomputed["effect_size"]),
              "treatment": (printed["treatment"], recomputed["treatment_centre"]),
              "control": (printed["control"], recomputed["control_centre"])}
    checks = []
    for name, (shown, full) in values.items():
        paper, n = target[name]
        ok, ours, boundary = primary_match(shown, paper, n)
        checks.append({"value": name, "printed": shown, "rounded": ours, "paper": format(paper, f".{n}f"),
                       "decimals": n, "match": ok, "on_boundary": boundary,
                       "recompute_6b": full, "recompute_6b_rounded": rounds_to(full, n),
                       "cross_check_agrees": rounds_to(full, n) == ours})
    ours_sig = float(printed["p"]) < ALPHA
    paper_sig = target["p"][0] < ALPHA
    checks.append({"value": "significance", "printed": printed["p"], "rounded": "p < 0.05" if ours_sig else "p >= 0.05",
                   "paper": "p < 0.05" if paper_sig else "p >= 0.05", "decimals": None,
                   "match": ours_sig == paper_sig, "on_boundary": False,
                   "recompute_6b": recomputed["p"], "recompute_6b_rounded": None,
                   "cross_check_agrees": (recomputed["p"] < ALPHA) == ours_sig})
    return checks


def headline(statuses):
    """M1_PLAN.md: the first rule that applies."""
    for status in ("IN PROGRESS", "NOT REPRODUCED", "INCONCLUSIVE/BLOCKED"):
        if status in statuses:
            return status
    return "REPRODUCED"


def evaluate(runs, recompute):
    results = {}
    for metric in NOTEBOOKS:
        chosen, steps, complete = pick_run(metric, runs)
        res = {"steps": steps, "paper_location": PAPER[metric]["prose"]}
        if chosen is None:
            res["status"] = "INCONCLUSIVE/BLOCKED" if complete else "IN PROGRESS"
            res["reason"] = ("every declared step FAILED" if complete else
                             "no as-shipped run given" if not steps else "next declared repair not run yet")
            results[metric] = res
            continue
        run = next(r for r in runs if r.name == chosen["run"])
        printed = parse_outputs(metric, (run / chosen["file"]).read_text(encoding="utf-8"))
        rec = recompute[metric]
        checks = decide(metric, printed, rec)
        res.update(run=chosen["run"], file=chosen["file"], repaired=chosen["step"] != "AS SHIPPED",
                   primary=checks,
                   status="REPRODUCED" if all(c["match"] for c in checks) else "NOT REPRODUCED",
                   cross_check_agrees=all(c["cross_check_agrees"] for c in checks),
                   ci=ci_rows(metric, printed, parse_outputs(metric, stored_outputs(metric)), rec))
        if "welch_p" in rec:
            res["welch_audit"] = {"test_run_by_notebook": "Student's (equal_var=True)",
                                  "test_named_in_paper": "Welch's",
                                  "student_p": rec["p"], "welch_p": rec["welch_p"],
                                  "student_p_rounded": rounds_to(rec["p"], 2),
                                  "welch_p_rounded": rounds_to(rec["welch_p"], 2),
                                  "paper_p": format(PAPER[metric]["p"][0], ".2f"),
                                  "welch_significant": rec["welch_p"] < ALPHA}
        results[metric] = res
    return results


def report(meta, results, overall):
    lines = [f"run {meta['run']}  runs={meta['runs']}  recompute={meta['recompute']}",
             f"\nRQ1a overall: {overall}"]
    for metric, r in results.items():
        lines.append(f"\n[{metric}]  {r['status']}  (paper {r['paper_location']})")
        for s in r["steps"]:
            lines.append(f"  step {s['step']:<16} run {s['run']}  {s['status']}")
        if "reason" in r:
            lines.append(f"  {r['reason']}")
            continue
        if r["repaired"]:
            lines.append("  ran only with declared repairs: record as a deviation")
        for c in r["primary"]:
            mark = "match" if c["match"] else "MISMATCH"
            extra = "  (on boundary)" if c["on_boundary"] else ""
            check = "" if c["cross_check_agrees"] else "  6b CROSS-CHECK DISAGREES"
            lines.append(f"  {c['value']:<12} printed {c['printed']:<11} -> {c['rounded']:<10} "
                         f"paper {c['paper']:<10} {mark}{extra}{check}")
        for row in r["ci"]:
            lines.append(f"  CI {row['group']:<9} {row['bound']:<5} run {row['run']:<7} paper {row['paper']:<7} "
                         f"stored {row['authors_stored']:<7} 6b {row['recompute_6b']:.4f}"
                         + ("" if row["run_vs_paper_within_noise"] else "  run vs paper OUTSIDE noise")
                         + ("" if row["paper_vs_stored_within_noise"] else "  AUDIT: paper vs stored differ"))
        if "welch_audit" in r:
            w = r["welch_audit"]
            lines.append(f"  Welch (audit): p = {w['welch_p']:.4f} -> {w['welch_p_rounded']}; "
                         f"Student p -> {w['student_p_rounded']}; paper says Welch's, p = {w['paper_p']}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="repro/runs/<UTC> folders from run_all.py (task 6a)")
    ap.add_argument("--recompute", default=DEFAULT_RECOMPUTE, help="6b output folder")
    args = ap.parse_args()

    runs = sorted((Path(r).resolve() for r in args.runs), key=lambda p: p.name)
    recompute_dir = (REPO / args.recompute).resolve()
    recompute = json.loads((recompute_dir / "results.json").read_text(encoding="utf-8"))["results"]
    results = evaluate(runs, recompute)
    overall = headline([r["status"] for r in results.values()])

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REPO / "repro" / "rq1_status" / stamp
    out.mkdir(parents=True)
    meta = {"run": stamp, "runs": [r.name for r in runs], "recompute": recompute_dir.name, "alpha": ALPHA}
    (out / "status.json").write_text(json.dumps({"meta": meta, "overall": overall, "metrics": results},
                                                indent=2, ensure_ascii=False), encoding="utf-8")
    text = report(meta, results, overall)
    (out / "status.txt").write_text(text, encoding="utf-8")
    with open(out / "environment.txt", "w", encoding="utf-8") as f:
        f.write(f"python {sys.version}\nplatform {platform.platform()}\n")
    read = [r / "run_log.txt" for r in runs] + [r / s["file"] for m in results.values()
                                                 for r in runs for s in m["steps"] if s["run"] == r.name]
    with open(out / "inputs_sha256.txt", "w", encoding="utf-8") as f:
        for path in read + [recompute_dir / "results.json"] + \
                [REPO / "frequentist" / f"{n}.ipynb" for n in NOTEBOOKS] + \
                [REPO / "repro" / "rq1_status.py", REPO / "repro" / "run_all.py"]:
            rel = path.relative_to(REPO) if REPO in path.parents else path
            f.write(f"{sha256_normalised(path)}  {rel}\n")
    print(text)
    print(f"done -> {out}")


if __name__ == "__main__":
    main()
