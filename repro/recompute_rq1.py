"""
CS4928 G33 / P32 - RQ1 independent recomputation (task 6b).

Recomputes the four Phase 2 comparisons from data/task2_preprocessed.csv with
our own code instead of the authors' notebooks, using the same tests the paper
reports, plus a FIXED-SEED bootstrap so the CIs are repeatable:

    metric                   column       test                         effect size
    completion time          clean_time   Wilcoxon rank-sum            Cliff's delta
    perceived productivity   pp_mean      t-test (Student; Welch too)  Cohen's d (pooled SD)
    CodeHealth               codehealth   t-test (Student; Welch too)  Cohen's d (pooled SD)
    test coverage            coverage     Wilcoxon rank-sum            Cliff's delta

    python repro/recompute_rq1.py                 # real data -> repro/recompute/<UTC>/
    python repro/recompute_rq1.py --resamples 10000   # quick pipeline check

Each (metric, group) bootstrap draws from its own stream, seeded with
[SEED, metric stream id, group id], so one metric's CI doesn't depend on which
other metrics ran, in what order, or with what n. The same seed gives the same
CIs only with the same NumPy version (environment.txt records it).

Do not run on the real data before the M1_PLAN tag exists. Writes to
repro/recompute/<UTC timestamp>/:
    results.json        every number, full precision
    results.txt         the same, human-readable
    environment.txt     python + library versions
    inputs_sha256.txt   hashes of the data file and this script
"""
import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
DATA = "data/task2_preprocessed.csv"
SEED = 4928
RESAMPLES = 1_000_000  # as in the authors' notebooks
CHUNK = 20_000  # resamples per batch, keeps memory small

# (column, test family, centre statistic, divide by for reporting, bootstrap stream id)
METRICS = {
    "completion_time": ("clean_time", "rank", np.median, 60.0, 1),  # seconds -> minutes
    "perceived_productivity": ("pp_mean", "t", np.mean, 1.0, 2),
    "codehealth": ("codehealth", "t", np.mean, 1.0, 3),
    "coverage": ("coverage", "rank", np.median, 1.0, 4),
}
GROUP_STREAM = {"treatment": 0, "control": 1}


def stream(seed, metric_stream, group):
    """The bootstrap generator for one (metric, group); independent of every other."""
    return np.random.default_rng([seed, metric_stream, GROUP_STREAM[group]])


def cliffs_delta(x, y) -> float:
    """P(X > Y) - P(X < Y) over all pairs, vectorised."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    diff = np.sign(x[:, None] - y[None, :])
    return float(diff.sum() / diff.size)


def cohens_d(x, y) -> float:
    """Mean difference over the pooled sample SD (ddof=1), as in the paper."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    nx, ny = len(x), len(y)
    pooled = np.sqrt(((nx - 1) * x.var(ddof=1) + (ny - 1) * y.var(ddof=1)) / (nx + ny - 2))
    return float((x.mean() - y.mean()) / pooled)


def bootstrap_ci(data, centre, rng, resamples=RESAMPLES, ci=95.0):
    """Percentile bootstrap CI of `centre` (np.mean or np.median), seeded."""
    data = np.asarray(data, float)
    out = np.empty(resamples)
    done = 0
    while done < resamples:
        k = min(CHUNK, resamples - done)
        idx = rng.integers(0, len(data), size=(k, len(data)))
        out[done:done + k] = centre(data[idx], axis=1)
        done += k
    tail = (100.0 - ci) / 2
    return float(np.percentile(out, tail)), float(np.percentile(out, 100.0 - tail))


def compare(treatment, control, family, centre, scale, seed, metric_stream, resamples):
    t, c = np.asarray(treatment, float), np.asarray(control, float)
    res = {"n_treatment": len(t), "n_control": len(c),
           "centre": centre.__name__,
           "treatment_centre": float(centre(t)) / scale,
           "control_centre": float(centre(c)) / scale}
    if family == "rank":
        r = stats.ranksums(t, c)
        res.update(test="wilcoxon_rank_sum", statistic=float(r.statistic), p=float(r.pvalue),
                   effect="cliffs_delta", effect_size=cliffs_delta(t, c))
    else:
        student = stats.ttest_ind(t, c, equal_var=True)
        welch = stats.ttest_ind(t, c, equal_var=False)
        res.update(test="student_t", statistic=float(student.statistic), p=float(student.pvalue),
                   welch_statistic=float(welch.statistic), welch_p=float(welch.pvalue),
                   effect="cohens_d", effect_size=cohens_d(t, c))
    for group, values in (("treatment", t), ("control", c)):
        lo, hi = bootstrap_ci(values, centre, stream(seed, metric_stream, group), resamples)
        res[f"{group}_ci95"] = [lo / scale, hi / scale]
    return res


def run(df, resamples=RESAMPLES, seed=SEED, metrics=None):
    """The comparisons in `metrics` (default: all four). Each metric's result is the same
    whether it runs alone or with the others."""
    treat = df[df["treatment"] == "ai"]
    ctrl = df[df["treatment"] == "human"]
    results = {}
    for name in metrics or METRICS:
        col, family, centre, scale, metric_stream = METRICS[name]
        # same exclusions as the notebooks: per-metric dropna, nothing else
        results[name] = compare(treat[col].dropna(), ctrl[col].dropna(),
                                family, centre, scale, seed, metric_stream, resamples)
    return results


def sha256_normalised(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resamples", type=int, default=RESAMPLES)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REPO / "repro" / "recompute" / stamp
    out.mkdir(parents=True)

    df = pd.read_csv(REPO / DATA)
    results = run(df, args.resamples, args.seed)
    meta = {"run": stamp, "seed": args.seed, "resamples": args.resamples, "data": DATA,
            "bootstrap_streams": "numpy default_rng([seed, metric stream id, group id]); "
                                 "group 0 = treatment, 1 = control",
            "metric_stream_ids": {name: m[4] for name, m in METRICS.items()}}

    (out / "results.json").write_text(json.dumps({"meta": meta, "results": results}, indent=2), encoding="utf-8")
    lines = [f"run {stamp}  seed={args.seed}  resamples={args.resamples}  "
             f"(one bootstrap stream per metric and group)"]
    for name, r in results.items():
        lines.append(f"\n[{name}]  n = {r['n_treatment']} vs {r['n_control']}")
        lines.append(f"  {r['centre']}: {r['treatment_centre']!r} vs {r['control_centre']!r}")
        lines.append(f"  {r['test']}: statistic={r['statistic']!r}  p={r['p']!r}")
        if "welch_p" in r:
            lines.append(f"  welch (sensitivity): statistic={r['welch_statistic']!r}  p={r['welch_p']!r}")
        lines.append(f"  {r['effect']}: {r['effect_size']!r}")
        lines.append(f"  95% CI treatment {r['treatment_ci95']}  control {r['control_ci95']}")
    (out / "results.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with open(out / "environment.txt", "w", encoding="utf-8") as f:
        f.write(f"python {sys.version}\nplatform {platform.platform()}\n")
        for p in ("numpy", "pandas", "scipy"):
            f.write(f"{p}=={version(p)}\n")
    with open(out / "inputs_sha256.txt", "w", encoding="utf-8") as f:
        for rel in (DATA, "repro/recompute_rq1.py"):
            f.write(f"{sha256_normalised(REPO / rel)}  {rel}\n")
    print("\n".join(lines))
    print(f"\ndone -> {out}")


if __name__ == "__main__":
    main()
