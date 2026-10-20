# Task 6e validation record

Executed on 20 October 2026 by Codex in the local task branch, starting from
`618005be76da818910ec27d85678baea14392a25`. Runtime: CPython 3.12.14;
standard library only. No statistical notebook or Change Event was executed.

| Check actually run | Result |
|---|---|
| `python3 repro/inspect_rq2_sample.py` | Seven evidence files generated for exactly IDs 0-11. |
| `python3 repro/inspect_rq2_sample.py --check` | All seven saved evidence files reproduce byte-for-byte with the recorded input bytes. |
| `python3 -m unittest discover -s repro -p test_inspect_rq2_sample.py -v` | 12 tests pass, including every source pointer and the nested-label cases. |
| Comparison with Enda's saved task 6d output | 108/108 values agree: 12 entries times nine measures (PMD total/file count, smell file count, five finding types and net smell change). |
| `git diff --check` after staging | No whitespace errors. |

## Independent count comparison

Reference commit: `b5ed310745e5596eebcd2d3dc7a380150993e81e`.
Reference file: `repro/rq2_counts/20261017T144903Z/per_entry.csv`.
This commit belongs to Enda's open PR #1; it is not assumed merged into main.
The comparison reads its CSV with `git show`; it does not execute Enda's code.

The exact comparison can be rerun from a clone that contains that commit:

```bash
python3 - <<'PY'
import csv, io, subprocess
from pathlib import Path
ours = list(csv.DictReader(Path('evidence/rq2_qualitative/generated/summary.csv').open()))
saved = subprocess.check_output([
    'git', 'show',
    'b5ed310745e5596eebcd2d3dc7a380150993e81e:repro/rq2_counts/20261017T144903Z/per_entry.csv'
], text=True)
reference = {int(row['id']): row for row in csv.DictReader(io.StringIO(saved))}
keys = ('pmd_total', 'pmd_files_with_violations', 'introduced', 'degraded',
        'unchanged', 'improved', 'fixed', 'net_smell_change')
for row in ours:
    expected = reference[int(row['id'])]
    for key in keys:
        assert row[key] == expected[key], (row['id'], key)
    assert row['smell_file_records'] == expected['smell_records']
print('PASS: 108/108 values agree')
PY
```

## What these checks establish

They verify the extraction, exact source locations, counting conventions and
agreement with another computation. Validation against participant Java source
and treatment-group comparisons are outside this inspection's scope. No earlier
expectation was rewritten and no new statistical conclusion was derived from
the 12 cases.

The raw hashes in `generated/inputs_sha256.json` identify this exact run's
bytes; the LF-normalised hashes allow CRLF/LF source copies to be compared.
`--check` is deliberately an exact-byte check. If a checkout converts line
endings, compare the LF hashes and regenerate in a separate output directory
instead of silently replacing the recorded evidence.
