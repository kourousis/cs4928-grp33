"""Task 8b: Event A run. Applies the frozen 6e method, unchanged, to JSON IDs 12-23.

Plan: EVENT_A_PLAN.md (tag EVENT_A_PLAN). This wrapper imports inspect() from
repro/inspect_rq2_sample.py without modifying it and writes only to
evidence/event_a/generated/, never to the M2 evidence folder.

If the frozen inspect() raises on an entry, the error is recorded as that entry's
result (errors.csv) and the entry stays in the sample (EVENT_A_PLAN.md section 2).

Run from the repo root:
    python3 repro/run_event_a.py           # write evidence
    python3 repro/run_event_a.py --check   # verify saved evidence byte for byte
Standard library only.
"""

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inspect_rq2_sample import REPO, SOURCES, csv_text, inspect  # noqa: E402  (frozen 6e code)

EVENT_A_IDS = tuple(range(12, 24))
DEFAULT_OUTPUT = REPO / "evidence" / "event_a" / "generated"
EXPECTED_SHA256 = {
    "data/task2_cs_delta.json": "019bb13aaa8614981e3f02019b82f6583941361cb5d688a40b20d1ea86d89ef1",
    "data/task2_pmd.json": "9c3e07d4ba80bc593e532835ad9147772276145a479f47a84ec378d82ede0531",
}


def run(repo=REPO, sample_ids=EVENT_A_IDS):
    hashes = {}
    for name in (*SOURCES, "repro/inspect_rq2_sample.py", "repro/run_event_a.py"):
        raw = (repo / name).read_bytes()
        hashes[name] = {
            "sha256_raw": hashlib.sha256(raw).hexdigest(),
            "sha256_lf": hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
        }
    for name, expected in EXPECTED_SHA256.items():
        # Compare the LF-normalised hash so a Windows (CRLF) checkout passes too.
        if hashes[name]["sha256_lf"] != expected:
            raise SystemExit(f"{name}: hash differs from the one frozen in EVENT_A_PLAN.md")

    cs, pmd = [json.loads((repo / s).read_text(encoding="utf-8")) for s in SOURCES]
    merged = {"summary": [], "findings": [], "pmd_rules": [], "pmd_top_rules": [],
              "source_extract": []}
    errors = []
    # One call per ID so that a stop on one entry is recorded without losing the rest.
    for entry_id in sample_ids:
        try:
            result = inspect(cs, pmd, sample_ids=(entry_id,))
        except ValueError as exc:
            errors.append({"id": entry_id, "error": str(exc)})
            continue
        for key in merged:
            merged[key].extend(result[key])

    outputs = {name + ".csv": csv_text(merged[name]) for name in (
        "summary", "findings", "pmd_rules", "pmd_top_rules")}
    outputs["errors.csv"] = csv_text(errors) if errors else '"id","error"\n'
    outputs["source_extract.json"] = json.dumps(merged["source_extract"], indent=2,
                                               ensure_ascii=False, sort_keys=True) + "\n"
    outputs["method.json"] = json.dumps({
        "plan": "EVENT_A_PLAN.md at tag EVENT_A_PLAN",
        "sample_ids": list(sample_ids),
        "method": "inspect() from repro/inspect_rq2_sample.py, unchanged (6e Method steps 1-4)",
        "call_pattern": "one inspect() call per ID; a ValueError is recorded in errors.csv",
        "unit": "JSON entry; treatment and participant identity unknown",
        "claim_boundary": "tool-report inspection, not inspection of participant Java source",
    }, indent=2, sort_keys=True) + "\n"
    outputs["inputs_sha256.json"] = json.dumps(hashes, indent=2, sort_keys=True) + "\n"
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = run()
    if args.check:
        bad = [n for n, t in outputs.items()
               if not (args.output / n).exists() or (args.output / n).read_bytes() != t.encode()]
        if bad:
            raise SystemExit("Evidence differs: " + ", ".join(bad))
        print(f"PASS: all {len(outputs)} saved Event A evidence files reproduce byte-for-byte")
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        for name, text in outputs.items():
            (args.output / name).write_bytes(text.encode("utf-8"))
        print(f"Wrote {len(outputs)} evidence files to {args.output}")
    # Runtime is printed, not written, so the saved files stay deterministic (as in 6e).
    print(f"Python {platform.python_version()} ({platform.python_implementation()}); stdlib only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
