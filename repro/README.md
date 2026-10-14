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
