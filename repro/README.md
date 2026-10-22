# repro/ — G33 RQ1 bounded reproduction

Re-runs the authors' four Phase 2 frequentist notebooks (`frequentist/*.ipynb`)
**as shipped** and stores each run, with its environment and input hashes, under
`repro/runs/<UTC timestamp>/`. The authors' notebooks are never edited.

Artefact: codescene-research/echoes-of-ai-emse-2025 @ `472ebca6d20af5d6de4264897ba98220ce521fd0`
(our copy is byte-identical apart from Windows line endings).

## One-time setup (Windows, from the repo root)

Python 3.9 is required (the notebooks record 3.9.21). With `uv`:

```
uv venv -p 3.9 .venv
uv pip install -p .venv -r repro/requirements.txt
```

or, if Python 3.9 is installed: `py -3.9 -m venv .venv` then
`.venv\Scripts\pip install -r repro\requirements.txt`.

## Run

```
.venv\Scripts\python repro\run_all.py codehealth   # pilot: one notebook (~2 min)
.venv\Scripts\python repro\run_all.py              # all four (~10 min)
.venv\Scripts\python repro\run_all.py --repairs R1 perceived_productivity
.venv\Scripts\python repro\run_all.py --repairs R1,R2 perceived_productivity
                                                    # only after the as-shipped failure is recorded, in this order
```

Before running, move away any existing `frequentist/figures/` folder (the runner refuses to mix old figures in).
Commit the `repro/runs/<timestamp>/` folder of the run you report — it is the raw evidence.

## Known as-shipped behaviour (record in the deviation log)

1. `perceived_productivity.ipynb` fails as shipped, for two reasons: it reads `data/...` where the other
   three use `../data/...`, and it calls `shapiro` without importing it. Record the as-shipped failure
   first. Then `--repairs R1` (path) and `--repairs R1,R2` (path + import) apply exactly the repairs
   declared in M1_PLAN.md to an in-memory copy, so each fault is captured in its own run. The authors'
   file is never edited.
2. Bootstrap CIs are unseeded (1,000,000 resamples), so the last digit of a CI can move
   between runs. The point estimates, test statistics and p-values are deterministic.
3. The CH and PP cells are labelled "Welch's t-test" (and the paper says Welch's), but the
   code calls `ttest_ind(..., equal_var=True)`, which is Student's t-test. Audit finding.
4. Library versions are our choice (last releases supporting Python 3.9); the authors
   published no versions.

## Our own scripts (tasks 6b, 6c, 6d)

These read the package's data directly instead of running the notebooks. Each run writes a new
timestamped folder with its results, `environment.txt` and `inputs_sha256.txt`. Commit that folder as
raw evidence and never edit it; to change a result, fix the script, log the deviation in `M1_PLAN.md`
first, and re-run.

| Script | Task | Writes to | What it does |
|---|---|---|---|
| `recompute_rq1.py` | 6b | `repro/recompute/<UTC>/` | The four RQ1a comparisons recomputed with our code, plus fixed-seed bootstrap CIs (seed 4928, 1,000,000 resamples, one stream per metric and group). A cross-check, not the source of the RQ1a status |
| `recompute_rq1b.py` | 6c | `repro/rq1b_codehealth/<UTC>/` | Unweighted CodeHealth per JSON entry (all files, and `src/main` only) and the group-blind distributions next to the published `codehealth` |
| `count_rq2.py` | 6d | `repro/rq2_counts/<UTC>/` | PMD total violations and net smell change per JSON entry, counts by change type and category, and fallback (a): the Table 8 check |

```
.venv/bin/python -m unittest discover -s repro -p "test_*.py"   # all tests, made-up data only
.venv/bin/python repro/recompute_rq1.py
.venv/bin/python repro/recompute_rq1b.py
.venv/bin/python repro/count_rq2.py
```

`recompute_rq1b.py` and `count_rq2.py` import the hash function from `recompute_rq1.py`. The same seed
gives the same CIs only with the same NumPy version (see `environment.txt`).

## Results and checks (tasks 7b, 7e)

| Script | Task | Writes to | What it does |
|---|---|---|---|
| `rq1_status.py` | 7b | `repro/rq1_status/<UTC>/` | The RQ1a status per metric and the headline status, from the 6a notebook runs, by the M1_PLAN.md decision rule. Also compares CIs with the paper and the authors' stored output, cross-checks every primary value against the 6b recompute, and reports Welch's next to Student's |
| `check_fresh_clone.py` | 7e | `repro/fresh_clone/<UTC>/` | Clones the repo at a ref, builds the pinned environment with `uv`, runs every test and script (6b, 6c, 6d, the 6e `--check`, 6a and 7b), and compares each new output with the newest committed one. Temporary paths in its report are masked |

```
.venv/bin/python repro/rq1_status.py repro/runs/<as shipped> repro/runs/<R1> repro/runs/<R1,R2>
.venv/bin/python repro/check_fresh_clone.py                    # origin main; ~10-35 min
.venv/bin/python repro/check_fresh_clone.py --skip-notebooks   # scripts only, ~1 min
```

`rq1_status.py` takes each metric from the first OK step of its ladder (as shipped, then R1, then
R1,R2). It refuses a repaired run that is not later than the step before it, or one used after an OK step. A metric with no as-shipped run is IN PROGRESS.
