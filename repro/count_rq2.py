"""
CS4928 G33 / P32 - RQ2 prep: PMD and code-smell counts per JSON entry (task 6d).

Counting rules are the ones fixed in M1_PLAN.md (RQ2 section):

    M-PMD    total violations[] across EVERY file in the entry, test files included
    M-SMELL  net smell change = (fixed + improved) - (introduced + degraded)
             counted per finding, by the finding's own top-level "change-type"
             (nested change-details are ignored), over every file record in the
             entry, all smell categories. Higher is better.

The JSON ids can't be linked to participants yet (L1), so this script stops at
per-entry numbers; the group test (Wilcoxon + Cliff's delta) is task 7d, once a
validated mapping exists.

It also runs fallback (a), the group-blind Table 8 consistency check: for each
of Table 8's 18 rows, the pooled count over all 75 entries must equal
round(40*T) + round(35*C), with T/C the paper's 2 dp means ("Removed" in the
paper = "fixed" in the data). Rounding is half-up on exact hundredths.

    python repro/count_rq2.py              # real data -> repro/rq2_counts/<UTC>/

Writes to repro/rq2_counts/<UTC timestamp>/:
    per_entry.csv       one row per JSON entry
    table8_check.csv    the 18 fallback (a) rows
    summary.txt         human-readable summary
    environment.txt     python + library versions
    inputs_sha256.txt   hashes of the data files and this script
"""
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import pandas as pd

from recompute_rq1 import sha256_normalised

REPO = Path(__file__).resolve().parent.parent
PMD_JSON = "data/task2_pmd.json"
DELTA_JSON = "data/task2_cs_delta.json"
N_TREATMENT, N_CONTROL = 40, 35
CHANGE_TYPES = ("introduced", "degraded", "unchanged", "improved", "fixed")

# paper Table 8 (p. 39): (change-type in the data, category, treatment mean, control mean),
# means as printed, in hundredths
TABLE8 = [
    ("fixed", "Bumpy Road Ahead", 10, 6),
    ("fixed", "Code Duplication", 5, 3),
    ("fixed", "Complex Conditional", 3, 3),
    ("fixed", "Complex Method", 23, 9),
    ("fixed", "Primitive Obsession", 3, 0),
    ("improved", "Complex Method", 7, 9),
    ("unchanged", "Bumpy Road Ahead", 5, 9),
    ("unchanged", "Code Duplication", 10, 17),
    ("unchanged", "Complex Method", 3, 9),
    ("unchanged", "Primitive Obsession", 5, 6),
    ("degraded", "Bumpy Road Ahead", 5, 6),
    ("degraded", "Complex Conditional", 3, 0),
    ("degraded", "Complex Method", 60, 31),
    ("introduced", "Bumpy Road Ahead", 7, 0),
    ("introduced", "Code Duplication", 10, 11),
    ("introduced", "Complex Conditional", 17, 3),
    ("introduced", "Complex Method", 15, 37),
    ("introduced", "Primitive Obsession", 10, 26),
]


def pmd_total(content):
    return sum(len(f["violations"]) for f in content["files"])


def smell_findings(records):
    """(change-type, category) for every top-level finding in every file record."""
    found = []
    for rec in records:
        for f in rec["findings"]:
            if f["change-type"] not in CHANGE_TYPES:
                raise ValueError(f"unexpected change-type {f['change-type']!r}")
            found.append((f["change-type"], f["category"]))
    return found


def net_smell_change(counts):
    return (counts["fixed"] + counts["improved"]) - (counts["introduced"] + counts["degraded"])


def half_up(n, hundredths):
    """round(n * hundredths / 100), half-up, in exact integer arithmetic."""
    return (n * hundredths + 50) // 100


def run(pmd, delta):
    if [e["id"] for e in pmd] != [e["id"] for e in delta]:
        raise ValueError("PMD and cs_delta entries are not in the same id order")
    rows, pooled = [], Counter()
    for p, d in zip(pmd, delta):
        found = smell_findings(d["content"])
        pooled.update(found)
        counts = Counter(t for t, _ in found)
        rows.append({"id": p["id"], "pmd_files": len(p["content"]["files"]),
                     "pmd_total": pmd_total(p["content"]), "smell_records": len(d["content"]),
                     **{t: counts[t] for t in CHANGE_TYPES},
                     "net_smell_change": net_smell_change(counts)})
    check = []
    for change, category, t, c in TABLE8:
        expected = half_up(N_TREATMENT, t) + half_up(N_CONTROL, c)
        check.append({"change_type": change, "category": category, "paper_T": t / 100,
                      "paper_C": c / 100, "expected_count": expected,
                      "pooled_count": pooled[(change, category)],
                      "match": pooled[(change, category)] == expected})
    return pd.DataFrame(rows), pd.DataFrame(check)


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REPO / "repro" / "rq2_counts" / stamp
    out.mkdir(parents=True)

    pmd = json.loads((REPO / PMD_JSON).read_text(encoding="utf-8"))
    delta = json.loads((REPO / DELTA_JSON).read_text(encoding="utf-8"))
    rows, check = run(pmd, delta)

    rows.to_csv(out / "per_entry.csv", index=False)
    check.to_csv(out / "table8_check.csv", index=False)
    lines = [f"run {stamp}",
             f"{len(rows)} entries, {rows['smell_records'].sum()} smell file records, "
             f"{rows['pmd_files'].sum()} PMD file records",
             f"pmd_total: sum {rows['pmd_total'].sum()}  range {rows['pmd_total'].min()} - {rows['pmd_total'].max()}",
             "pooled findings: " + "  ".join(f"{t} {rows[t].sum()}" for t in CHANGE_TYPES),
             f"net_smell_change: sum {rows['net_smell_change'].sum()}  "
             f"range {rows['net_smell_change'].min()} - {rows['net_smell_change'].max()}",
             f"\nfallback (a), Table 8 counts: {int(check['match'].sum())} of {len(check)} rows match"]
    for r in check.itertuples():
        lines.append(f"  {'ok  ' if r.match else 'MISS'} {r.change_type:<10} {r.category:<20} "
                     f"expected {r.expected_count:>2}  pooled {r.pooled_count:>2}")
    (out / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with open(out / "environment.txt", "w", encoding="utf-8") as f:
        f.write(f"python {sys.version}\nplatform {platform.platform()}\n")
        f.write(f"pandas=={version('pandas')}\n")
    with open(out / "inputs_sha256.txt", "w", encoding="utf-8") as f:
        for rel in (PMD_JSON, DELTA_JSON, "repro/count_rq2.py"):
            f.write(f"{sha256_normalised(REPO / rel)}  {rel}\n")
    print("\n".join(lines))
    print(f"\ndone -> {out}")


if __name__ == "__main__":
    main()
