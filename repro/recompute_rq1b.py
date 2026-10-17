"""
CS4928 G33 / P32 - RQ1b CodeHealth aggregation audit (task 6c).

The package defines project CodeHealth as the SLOC-weighted mean of file-level
scores (data/README.md), but task2_codeHealth.json has no SLOC and no
participant ID. So this script computes what the package does allow:

    per JSON entry (id 0-74): the UNWEIGHTED mean file score
        (a) over all files
        (b) over ./src/main/ files only

and the group-blind distributions (mean, SD, min, max) of those values and of
the published `codehealth` column in data/task2_preprocessed.csv. This is
descriptive context only; with no linkage or SLOC it cannot pass or fail the
audit (the RQ1b verdict is task 7c).

Files whose score is `null` (CodeScene gives no score; the package truncates
it to "nu") are excluded from the means and counted per entry. Any other line
that doesn't parse, a path outside ./src/main/ or ./src/test/, an entry with no
scored src/main file, or anything other than 75 entries with ids 0-74 and 75
published values stops the run.

    python repro/recompute_rq1b.py            # real data -> repro/rq1b_codehealth/<UTC>/

Writes to repro/rq1b_codehealth/<UTC timestamp>/:
    per_entry.csv       one row per JSON entry
    summary.json        the distributions, full precision
    summary.txt         the same, human-readable
    environment.txt     python + library versions
    inputs_sha256.txt   hashes of the data files and this script
"""
import json
import platform
import re
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from recompute_rq1 import sha256_normalised

REPO = Path(__file__).resolve().parent.parent
CH_JSON = "data/task2_codeHealth.json"
CSV = "data/task2_preprocessed.csv"
MAIN = "./src/main/"
KNOWN_PREFIXES = (MAIN, "./src/test/")
N_ENTRIES = 75  # Phase 2: 40 treatment + 35 control

# one string per file: "info: <path>:1: Code health score: <score> [warn: ...]"
SCORE_LINE = re.compile(r"^info: (?P<path>\S+?):\d+: Code health score: (?P<score>\S+) ")
NUMBER = re.compile(r"^\d+\.\d+$")
NULL_SCORES = {"nu", "null"}  # the package truncates "null" to "nu"


def parse_file_line(line):
    """(path, score) for one file line; score is None for a null score."""
    m = SCORE_LINE.match(line)
    if not m or line.count("Code health score:") != 1:
        raise ValueError(f"unexpected CodeHealth line: {line[:200]!r}")
    if not m["path"].startswith(KNOWN_PREFIXES):
        raise ValueError(f"path outside {KNOWN_PREFIXES}: {m['path']!r}")
    score = m["score"]
    if score in NULL_SCORES:
        return m["path"], None
    if not NUMBER.match(score):
        raise ValueError(f"unexpected score {score!r} in: {line[:200]!r}")
    return m["path"], float(score)


def entry_row(entry):
    files = [parse_file_line(s) for s in entry["content"]]
    scored = [(p, s) for p, s in files if s is not None]
    main = [s for p, s in scored if p.startswith(MAIN)]
    return {
        "id": entry["id"],
        "n_files": len(files),
        "n_null": len(files) - len(scored),
        "n_scored_all": len(scored),
        "mean_all": float(np.mean([s for _, s in scored])) if scored else float("nan"),
        "n_scored_main": len(main),
        "mean_main": float(np.mean(main)) if main else float("nan"),
    }


def describe(values):
    v = np.asarray(values, float)
    return {"n": len(v), "mean": float(v.mean()), "sd": float(v.std(ddof=1)),
            "min": float(v.min()), "max": float(v.max())}


def check_shape(entries, published, n=N_ENTRIES):
    """The package's shape, as M1_PLAN.md describes it; stop rather than guess."""
    ids = [e["id"] for e in entries]
    if ids != list(range(n)):
        raise ValueError(f"expected JSON ids 0-{n - 1} in order, got {len(ids)} entries")
    keys = sorted({k for e in entries for k in e})
    if keys != ["content", "id"]:
        raise ValueError(f"expected only id/content keys, got {keys}")
    if len(published) != n or published.isna().any():
        raise ValueError(f"expected {n} published codehealth values, got {published.notna().sum()}")


def run(entries, df):
    rows = pd.DataFrame([entry_row(e) for e in entries])
    if (rows["n_scored_main"] == 0).any():
        raise ValueError(f"entries with no scored src/main file: {list(rows.loc[rows['n_scored_main'] == 0, 'id'])}")
    published = df.loc[df["treatment"].notna(), "codehealth"]
    summary = {
        "entries": len(rows),
        "files": int(rows["n_files"].sum()),
        "null_scores": int(rows["n_null"].sum()),
        "entries_with_null": int((rows["n_null"] > 0).sum()),
        "json_entry_keys": sorted({k for e in entries for k in e}),  # no SLOC, no participant ID
        "recomputed_unweighted_all": describe(rows["mean_all"]),
        "recomputed_unweighted_src_main": describe(rows["mean_main"]),
        "published_codehealth": describe(published),
    }
    return rows, summary


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REPO / "repro" / "rq1b_codehealth" / stamp
    out.mkdir(parents=True)

    entries = json.loads((REPO / CH_JSON).read_text(encoding="utf-8"))
    df = pd.read_csv(REPO / CSV)
    check_shape(entries, df.loc[df["treatment"].notna(), "codehealth"])
    rows, summary = run(entries, df)

    rows.to_csv(out / "per_entry.csv", index=False)
    (out / "summary.json").write_text(json.dumps({"run": stamp, "summary": summary}, indent=2), encoding="utf-8")
    lines = [f"run {stamp}",
             f"{summary['entries']} entries, {summary['files']} file lines, "
             f"{summary['null_scores']} null scores (in {summary['entries_with_null']} entries, excluded)"]
    for name in ("recomputed_unweighted_all", "recomputed_unweighted_src_main", "published_codehealth"):
        d = summary[name]
        lines.append(f"\n[{name}]  n = {d['n']}")
        lines.append(f"  mean {d['mean']!r}  sd {d['sd']!r}  range {d['min']!r} - {d['max']!r}")
    (out / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with open(out / "environment.txt", "w", encoding="utf-8") as f:
        f.write(f"python {sys.version}\nplatform {platform.platform()}\n")
        for p in ("numpy", "pandas"):
            f.write(f"{p}=={version(p)}\n")
    with open(out / "inputs_sha256.txt", "w", encoding="utf-8") as f:
        for rel in (CH_JSON, CSV, "repro/recompute_rq1b.py", "repro/recompute_rq1.py"):
            f.write(f"{sha256_normalised(REPO / rel)}  {rel}\n")
    print("\n".join(lines))
    print(f"\ndone -> {out}")


if __name__ == "__main__":
    main()
