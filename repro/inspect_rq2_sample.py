"""Task 6e: reproducible evidence for the group-blind inspection of JSON IDs 0-11.

Run from any directory: python3 repro/inspect_rq2_sample.py
Only the standard library is required. This extracts evidence; the case-by-case
interpretation and AI disclosure are in evidence/rq2_qualitative/README.md.
"""

import argparse
import csv
import hashlib
import io
import json
import platform
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SAMPLE_IDS = tuple(range(12))
CHANGE_TYPES = ("introduced", "degraded", "unchanged", "improved", "fixed")
SOURCES = ("data/task2_cs_delta.json", "data/task2_pmd.json")
DEFAULT_OUTPUT = REPO / "evidence" / "rq2_qualitative" / "generated"


def index_entries(entries):
    """Retain JSON array positions as evidence, but select cases by their ID."""
    indexed = {}
    for position, entry in enumerate(entries):
        entry_id = entry["id"]
        if not isinstance(entry_id, int) or isinstance(entry_id, bool):
            raise ValueError("JSON entry ID must be an integer")
        if entry_id in indexed:
            raise ValueError(f"Duplicate JSON entry ID: {entry_id}")
        indexed[entry_id] = (position, entry)
    return indexed


def top_rules(counts, rank_limit=3):
    """Top three rule names by count, retaining every tie at the cutoff."""
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    if not ranked:
        return []
    cutoff = ranked[min(rank_limit, len(ranked)) - 1][1]
    return [(name, count) for name, count in ranked if count >= cutoff]


def inspect(cs_entries, pmd_entries, sample_ids=SAMPLE_IDS):
    cs_index, pmd_index = index_entries(cs_entries), index_entries(pmd_entries)
    if len(set(sample_ids)) != len(sample_ids):
        raise ValueError("Sample IDs must be unique")
    summaries, findings, rules, top, cases = [], [], [], [], []
    for entry_id in sample_ids:
        if entry_id not in cs_index or entry_id not in pmd_index:
            raise ValueError(f"Missing sample ID {entry_id}")
        cs_pos, cs = cs_index[entry_id]
        pmd_pos, pmd = pmd_index[entry_id]
        content = pmd["content"]
        for key in ("processingErrors", "configurationErrors", "suppressedViolations"):
            if content.get(key):
                raise ValueError(f"ID {entry_id}: non-empty PMD {key}")
        if content.get("pmdVersion") != "7.13.0":
            raise ValueError(f"ID {entry_id}: unexpected PMD version")

        changes = Counter()
        for file_index, file_record in enumerate(cs["content"]):
            for finding_index, finding in enumerate(file_record["findings"]):
                change = finding["change-type"]
                if change not in CHANGE_TYPES:
                    raise ValueError(f"Unexpected change type {change!r}")
                changes[change] += 1
                findings.append({
                    "id": entry_id,
                    "pointer": f"/{cs_pos}/content/{file_index}/findings/{finding_index}",
                    "file": file_record.get("name", "<missing name>"),
                    "category": finding["category"],
                    "change_type": change,
                    "old_file_score": file_record.get("old-score", ""),
                    "new_file_score": file_record.get("new-score", ""),
                    "detail_change_types": json.dumps(
                        [d["change-type"] for d in finding.get("change-details", [])]),
                    "details_json": json.dumps(finding.get("change-details", []),
                                               ensure_ascii=False, sort_keys=True),
                })

        rule_counts, first_examples = Counter(), {}
        scopes = Counter()
        for file_index, file_record in enumerate(content["files"]):
            filename = file_record["filename"]
            scope = ("main" if filename.startswith("./src/main/") else
                     "test" if filename.startswith("./src/test/") else "other")
            for violation_index, violation in enumerate(file_record["violations"]):
                rule = violation["rule"]
                rule_counts[rule] += 1
                scopes[scope] += 1
                if rule not in first_examples:
                    first_examples[rule] = {
                        "pointer": f"/{pmd_pos}/content/files/{file_index}/violations/{violation_index}",
                        "file": filename,
                        "violation": violation,
                    }
        ranked_top = top_rules(rule_counts)
        selected = dict(ranked_top)
        for rule, count in sorted(rule_counts.items(), key=lambda item: (-item[1], item[0])):
            example = first_examples[rule]
            row = {
                "id": entry_id, "rule": rule, "count": count,
                "example_pointer": example["pointer"], "example_file": example["file"],
                "example_beginline": example["violation"]["beginline"],
                "example_endline": example["violation"]["endline"],
                "example_description": example["violation"]["description"],
            }
            rules.append(row)
            if rule in selected:
                top.append(dict(row))

        summary = {
            "id": entry_id, "smell_file_records": len(cs["content"]),
            **{change: changes[change] for change in CHANGE_TYPES},
            "net_smell_change": (changes["fixed"] + changes["improved"]
                                 - changes["introduced"] - changes["degraded"]),
            "pmd_total": sum(rule_counts.values()),
            "pmd_main": scopes["main"], "pmd_test": scopes["test"],
            "pmd_other": scopes["other"],
            "pmd_files_with_violations": len(content["files"]),
            "top_rules": "; ".join(f"{rule}={count}" for rule, count in ranked_top),
        }
        summaries.append(summary)
        cases.append({
            "id": entry_id, "cs_entry_pointer": f"/{cs_pos}",
            "cs_entry": cs, "pmd_entry_pointer": f"/{pmd_pos}",
            "pmd_version": content["pmdVersion"],
            "pmd_errors": {key: content.get(key, []) for key in (
                "processingErrors", "configurationErrors", "suppressedViolations")},
            "top_rule_examples": {rule: first_examples[rule] for rule in selected},
        })
    return {"summary": summaries, "findings": findings, "pmd_rules": rules,
            "pmd_top_rules": top, "source_extract": cases}


def csv_text(rows):
    if not rows:
        return ""
    buffer = io.StringIO(newline="")
    # Quote every field so original trailing spaces in PMD descriptions remain
    # inside a quoted value rather than looking like whitespace added by us.
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n",
                            quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def build_outputs(repo=REPO):
    cs, pmd = [json.loads((repo / source).read_text(encoding="utf-8")) for source in SOURCES]
    evidence = inspect(cs, pmd)
    outputs = {name + ".csv": csv_text(evidence[name]) for name in (
        "summary", "findings", "pmd_rules", "pmd_top_rules")}
    outputs["source_extract.json"] = json.dumps(evidence["source_extract"], indent=2,
                                               ensure_ascii=False, sort_keys=True) + "\n"
    outputs["method.json"] = json.dumps({
        "sample_ids": list(SAMPLE_IDS),
        "unit": "JSON entry; treatment and participant identity unknown",
        "smell_counting": "one top-level finding; nested change-details not counted",
        "files": "all file records, including tests and missing names",
        "pmd_counting": "all violations in all files; totals, not changes or severity weights",
        "top_rules": "top three rule names by count; all cutoff ties retained; alphabetical tie order",
        "pmd_example": "first occurrence in source file order for each rule",
        "source_pointer": "RFC 6901 JSON Pointer into the named original source; zero-based arrays",
        "claim_boundary": "tool-report inspection, not inspection of participant Java source",
        "generated_files": "deterministic; runtime details printed separately",
    }, indent=2, sort_keys=True) + "\n"
    hashes = {}
    for name in (*SOURCES, "repro/inspect_rq2_sample.py"):
        raw = (repo / name).read_bytes()
        hashes[name] = {
            "sha256_raw": hashlib.sha256(raw).hexdigest(),
            "sha256_lf": hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
        }
    outputs["inputs_sha256.json"] = json.dumps(hashes, indent=2, sort_keys=True) + "\n"
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="verify saved evidence without writing")
    args = parser.parse_args()
    outputs = build_outputs()
    if args.check:
        mismatches = [name for name, text in outputs.items()
                      if not (args.output / name).exists()
                      or (args.output / name).read_bytes() != text.encode("utf-8")]
        if mismatches:
            raise SystemExit("Evidence differs: " + ", ".join(mismatches))
        print(f"PASS: all {len(outputs)} saved evidence files reproduce byte-for-byte")
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        for name, text in outputs.items():
            (args.output / name).write_bytes(text.encode("utf-8"))
        print(f"Wrote {len(outputs)} evidence files to {args.output}")
    print(f"Python {platform.python_version()} ({platform.python_implementation()}); stdlib only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
