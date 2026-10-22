# M2_REPRO — G33 / P32 bounded reproduction and audit (Week 7)

This file is the M2 record required by the brief: the bounded reproduction result, the raw evidence that
supports it, and the key deviations and threats. It follows the frozen plan in `M1_PLAN.md` (tag `M1_PLAN`)
and the corrections in `M1_ADDENDUM.md`. No Change Event material has been opened.

## Results

| RQ part | Status (M1 decision rule) | Raw evidence |
|---|---|---|
| **RQ1a**: four Phase 2 comparisons | **REPRODUCED**. Completion time, perceived productivity, CodeHealth and test coverage all meet every primary criterion (p, effect size, point estimates, significance call) | `repro/runs/` (README has the value-by-value table). Runs `20261022T150533Z` (as shipped), `…151200Z` (R1), `…151209Z` (R1,R2) |
| RQ1a cross-check | Independent fixed-seed recompute agrees on every primary value | `repro/recompute/20261017T144852Z/` (`repro/recompute_rq1.py`) |
| **RQ1b**: CodeHealth aggregation audit | **NOT AUDITABLE FROM PACKAGE**. There is no per-file SLOC and no JSON-to-participant link. The unweighted recompute is reported descriptively (mean 8.64 over all files, 8.27 over `src/main`, against a published mean of 8.47) | `repro/rq1b_codehealth/20261017T144901Z/` |
| **RQ2**: PMD and smell transfer | Group comparison **INCONCLUSIVE/BLOCKED** (fallback route). The authors' issue #1 asking for the id-to-participant mapping had no reply by the Week 7 checkpoint, the M1 deadline | Issue: codescene-research/echoes-of-ai-emse-2025#1 |
| RQ2 fallback (a) | Table 8 consistency: 18 of 18 printed rows match as counts, and 7 of 7 unprinted cells pool to 0 | `repro/rq2_counts/20261017T144903Z/table8_check.csv` |
| RQ2 fallback (b) | Group-blind qualitative inspection of JSON ids 0–11 (the first 12 in stable order) is done | `evidence/rq2_qualitative/README.md` |

The RQ1 expected result was "no significant difference on any of the four metrics", and it was met.
The RQ2 linkage prediction ("no validated mapping by M2, so INCONCLUSIVE/BLOCKED") was also met.

## Key deviations (full list in the M1 deviation log and `repro/runs/README.md`)

1. `perceived_productivity.ipynb` does not run as shipped. Declared repairs R1 (data path) and R2 (missing
   `shapiro` import) were applied in order, with each failure captured in its own run first.
2. Sample is all 75 Phase 2 participants, not the pack's "first 12", because the unit of analysis is the
   group comparison. The pack's first-12 rule is used for the qualitative inspection.
3. Library versions are our choice (Python 3.9.25, pins in `repro/requirements.txt`). The authors publish none.

## Key threats and audit findings

- **Welch vs Student.** The paper and the notebook labels say Welch's t-test, but the code runs Student's. The
  paper's p-values are Student's. Welch's would give CH p = 0.235 and PP p = 0.368, which does not change any
  significance call.
- **Coverage CI.** The paper's control upper bound is 0.74, but both the authors' stored output and our run
  give 0.71.
- **Unlinkable file-level data.** The JSON files cannot be tied to participants, so no maintainability measure
  other than the published CSV columns can be compared by group.
- **No source code in the package.** The "qualitative inspection of code solutions" is limited to the
  tool reports (CodeScene and PMD JSON), not the Java code itself.
- **Unseeded bootstraps.** The last digit of a CI can move between runs. Point estimates and tests are
  deterministic.

## How to re-run

See `repro/README.md`. Summary: create a Python 3.9 environment from `repro/requirements.txt`, then run
`python repro/run_all.py`, then `--repairs R1 perceived_productivity`, then `--repairs R1,R2
perceived_productivity`. The scripts' tests run with `python -m unittest discover -s repro -p "test_*.py"`
(46 tests pass on the merged branch).
