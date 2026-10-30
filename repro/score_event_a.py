"""Task 8b: score the Event A predictions P1-P4 exactly as written in EVENT_A_PLAN.md section 4,
and reconcile the Event A totals with the 6d per-entry counts (EVENT_A_PLAN.md section 2, 6e step 5).

Reads only evidence/event_a/generated/{findings,pmd_top_rules,summary,errors}.csv and
repro/rq2_counts/20261017T144903Z/per_entry.csv. Writes evidence/event_a/generated/scores.json.
Run from the repo root: python3 repro/score_event_a.py [--check]
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parent.parent
GEN = REPO / "evidence" / "event_a" / "generated"
SIX_D = REPO / "repro" / "rq2_counts" / "20261017T144903Z" / "per_entry.csv"
IDS = list(range(12, 24))
TOP3 = {"CommentRequired", "MethodArgumentCouldBeFinal", "LocalVariableCouldBeFinal"}
CHANGE_TYPES = ("introduced", "degraded", "unchanged", "improved", "fixed")


def rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def score():
    findings = rows(GEN / "findings.csv")
    top = rows(GEN / "pmd_top_rules.csv")
    errored = {int(r["id"]) for r in rows(GEN / "errors.csv")}
    changes = Counter(f["change_type"] for f in findings)
    total = sum(changes.values())

    p1_fixed = changes["fixed"]
    worse = changes["introduced"] + changes["degraded"]
    p3_ids = sorted({int(f["id"]) for f in findings
                     if f["category"] == "Complex Method"
                     and PurePosixPath(f["file"]).name == "RecipeSearchController.java"
                     and f["change_type"] in ("introduced", "degraded")} - errored)
    rules_by_id = {i: set() for i in IDS}
    for r in top:
        rules_by_id[int(r["id"])].add(r["rule"])
    p4_ids = [i for i in IDS if i not in errored and TOP3 <= rules_by_id[i]]
    fixed_by_id = Counter(int(f["id"]) for f in findings if f["change_type"] == "fixed")

    result = {
        "change_type_totals": {c: changes[c] for c in CHANGE_TYPES},
        "top_level_findings": total,
        "errored_ids": sorted(errored),
        "P1": {"rule": "fixed <= 1", "value": p1_fixed, "holds": p1_fixed <= 1,
               "fixed_by_id": {str(k): v for k, v in sorted(fixed_by_id.items())}},
        "P2": {"rule": "introduced+degraded >= half of top-level findings (fails if none)",
               "value": f"{worse} of {total}", "holds": total > 0 and 2 * worse >= total},
        "P3": {"rule": ">= 4 entries with Complex Method on RecipeSearchController.java introduced/degraded",
               "ids": p3_ids, "value": len(p3_ids), "holds": len(p3_ids) >= 4},
        "P4": {"rule": ">= 10 entries with all three rules among their top rules",
               "ids": p4_ids, "value": len(p4_ids), "holds": len(p4_ids) >= 10},
    }
    p4_fail = 12 - len(p4_ids)
    result["challenge_rule"] = {
        "rule": "M2 description challenged if P1 fails (>= 2 fixed) or P4 fails (>= 3 entries missing a rule)",
        "challenged": (not result["P1"]["holds"]) or p4_fail >= 3,
    }

    # Reconciliation with 6d (independent counting script, run 17 Oct).
    summary = {int(r["id"]): r for r in rows(GEN / "summary.csv")}
    six_d = {int(r["id"]): r for r in rows(SIX_D)}
    keys = ("pmd_total", "introduced", "degraded", "unchanged", "improved", "fixed", "net_smell_change")
    mismatches = []
    for i in IDS:
        if i in errored:
            continue
        for k in keys:
            if int(summary[i][k]) != int(six_d[i][k]):
                mismatches.append(f"id {i} {k}: event_a={summary[i][k]} 6d={six_d[i][k]}")
        if int(summary[i]["smell_file_records"]) != int(six_d[i]["smell_records"]):
            mismatches.append(f"id {i} smell_file_records")
    result["reconciliation_6d"] = {"source": str(SIX_D.relative_to(REPO)),
                                   "fields": list(keys) + ["smell_file_records"],
                                   "mismatches": mismatches, "agrees": not mismatches}
    return json.dumps(result, indent=2, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = score()
    out = GEN / "scores.json"
    if args.check:
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            raise SystemExit("scores.json differs")
        print("PASS: scores.json reproduces")
    else:
        out.write_text(text, encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
