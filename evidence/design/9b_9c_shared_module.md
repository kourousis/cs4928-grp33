# Tasks 9b and 9c: the shared stats module and its verification

**Decision:** Option B (shared, tested module) is adopted. It passes both criteria of the RQ3 decision
rule in [M1_PLAN.md](../../M1_PLAN.md), so the condition set in [9a](9a_alternatives.md) is met.
**Recorded:** 5 November 2026. **Before state:** tag `PRE_EVENT_A`. **After state:** the commit that adds this file.

## What changed (9b)

- **New [`frequentist/stats.py`](../../frequentist/stats.py)** holds one copy of each shared helper:
  `cohens_d`, `cliffs_delta`, `bootstrap_ci_mean`, `bootstrap_ci_median`, `bootstrap_ci_mean_difference`,
  `bootstrap_ci_median_difference`, the two effect-size labels (`cohens_magnitude`, `cliffs_magnitude`),
  and the data loading (`load_data`, `split_groups`).
- **The four notebooks import from it.** Their own copies, the copied magnitude thresholds and the
  `read_csv` lines are gone. Each notebook is still the entry point and still prints the same tables
  and figures. The authors' stored outputs are kept.
- **R1 fixed:** `load_data()` builds the data path from the module's location, so it no longer depends on
  the working directory.
- **R2 fixed:** `perceived_productivity` imports `shapiro`.
- **Unseeded bootstrap fixed:** each notebook sets `np.random.seed(4928)` after its imports (logged in the
  M1_PLAN.md deviation log).
- **The drifted `cliffs_delta` copies are now one function** that always drops NaNs first, like the
  coverage copy. Every existing caller already dropped them, so no number changes.
- **Kept out on purpose:** `cronbach_alpha` (one copy only), Student's t-test (the reproduced method; the
  Welch question stays a separate audit finding), and the copied plotting and colour cells (layout, not
  analysis logic).
- **Unchanged RQ1 evidence:** `repro/run_all.py` and `repro/rq1_status.py` now read the as-shipped notebooks
  from git at `PRE_EVENT_A`. Re-running `rq1_status.py` on the committed M2 runs gives the same statuses.

## Verification (9c)

| Decision-rule check | Result | Evidence |
|---|---|---|
| 1. Every RQ1a primary value identical, CIs under the same seed | **Pass.** All 4 notebooks print exactly the same lines before and after (167 lines in all), including all 16 primary values (p-value, effect size and both point estimates for each metric) and all 16 CI bounds | [`repro/rq3_verify/20261105T185759Z/report.txt`](../../repro/rq3_verify/20261105T185759Z/report.txt) |
| 2a. Duplicated functions removed | **Pass.** Copied functions: 5 names and 105 SLOC before, 0 after | [`measure_after/measure.txt`](../../repro/rq3_verify/20261105T185759Z/measure_after/measure.txt) vs the baseline [`repro/rq3_measure/20261029T132012Z`](../../repro/rq3_measure/20261029T132012Z/measure.txt) |
| 2b. R1 and R2 removed | **Pass.** One data location instead of two (`../data/` and `data/`), no undefined names in the notebooks, and `perceived_productivity` runs with no repairs (status OK in the "after" run) | same two files; `repro/rq3_verify/20261105T185759Z/after/perceived_productivity.outputs.txt` |
| 2c. Tests for each extracted function | **Pass.** [`repro/test_stats.py`](../../repro/test_stats.py) tests each function on small hand-worked cases. The full suite (94 tests) passes. The before/after run above is the main check that nothing changed | `python -m unittest discover -s repro -p "test_*.py"` |

**Descriptive numbers** (not part of the rule): cross-file duplicated logical lines fell from 163 of 655
(24.9%) to 62 of 574 (10.8%). What's left is mostly imports, the copied plotting and colour cells and the
Shapiro-Wilk printout. Total SLOC went from 762 to 705, including the new module (111 SLOC).

**How "before" was run:** the notebooks at `PRE_EVENT_A`, with only the repairs already declared in
M1_PLAN.md (R1 and R2, without which `perceived_productivity` cannot run) and the same seed line, applied
in memory. Both versions ran in the same pinned environment (`environment.txt` in the run folder).

## Limits

- Identical output was shown for this data and this seed. The unit tests cover the general case
  (other data, NaNs, ties, boundaries), but on synthetic data.
- `rq3_measure.py` reports `__file__` as undefined in `stats.py` and its random calls as unseeded. Both are
  limits of that measure: `__file__` exists in every module, and the seed is set by the notebook that
  calls the function.
- The duplicated-line share is a lower bound (exact copies only), as for the baseline.
