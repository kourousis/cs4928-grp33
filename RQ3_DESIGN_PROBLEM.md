# RQ3 — the design problem (task 8e)

The concrete design pressure behind RQ3, with the evidence for each part. The options and the decision
(9a), the change itself (9b) and its verification (9c) build on this.

- **State measured:** tag `PRE_EVENT_A` (`38920e8`), before any RQ3 change. The four `frequentist/`
  notebooks there are the authors' as shipped (artefact `472ebca`, see `repro/README.md`).
- **Measurements:** `repro/rq3_measure/20261029T132012Z/` (task 8c, `repro/rq3_measure.py`). Cell numbers below are
  0-based positions among all cells of the notebook.
- **Two units:**
  - **SLOC** = physical lines with code (762 in all);
  - **logical lines** = statements, where a statement split over several lines counts once (655 in all).
  - Duplication is measured in logical lines.
- **RQ3 (verbatim, M1_PLAN.md):** "Can the duplicated, hard-to-re-run analysis code in the replication
  package be restructured into a shared, tested module without changing any reproduced result, and is
  that change justified compared with leaving the code as it is?"

## 1. The statistics code is copied between notebooks, and the copies have started to differ

13 functions are defined across the four notebooks, under 7 names. 5 names are defined in more than one
notebook, and their copies add up to 105 SLOC. No notebook imports from another, and the package has no
tests for any of them (its only tests are for the Julia code under `bayesian/test/`).

| Function | Where (notebook, cell) | SLOC per copy | Copies the same? |
|---|---|---|---|
| `cliffs_delta` | codehealth 28, completion_time 14, coverage 15 | 13, 13, 8 | codehealth = completion_time. coverage is rewritten: it **drops NaNs inside the function**, which the other two don't, and so needs pandas input |
| `cohens_d` | codehealth 20, perceived_productivity 22 | 9, 9 | Same behaviour, written differently (returns directly; comments differ) |
| `bootstrap_ci_mean` | codehealth 21, perceived_productivity 23 | 6, 5 | Identical apart from codehealth's docstring |
| `bootstrap_ci_median` | completion_time 16, coverage 16 | 6, 6 | Identical |
| `bootstrap_ci_median_difference` | completion_time 17, coverage 17 | 13, 17 | Same behaviour (coverage adds `np.asarray` and spacing) |
| `bootstrap_ci_mean_difference` | codehealth 22 | 17 | One copy |
| `cronbach_alpha` | perceived_productivity 8 | 6 | One copy |

"Same behaviour" is our reading of the two copies side by side. `rq3_measure.py` only reports whether
their ASTs are identical (ignoring the docstring).

**Copying goes beyond the functions.** 163 of the 655 logical lines (24.9%) lie in a run of at least 5
logical lines that also appears in another notebook. 80 of those are inside functions. The other 83 are:
- imports (25);
- the block that names Cliff's δ magnitude from the 0.147 / 0.33 / 0.474 thresholds, copied three
  times: codehealth 29, completion_time 15 and 23 (30);
- the Shapiro-Wilk normality test and its printout: codehealth 14 = coverage 11 (10);
- the error-bar plotting in the bootstrap cells: completion_time 16 = coverage 16 (18).

The copied thresholds are analysis logic, not just layout.

**24.9% is a lower bound.** The measure only finds exact copies, so it misses:
- **near-copies with renamed variables,** such as the histogram and descriptive-statistics cells;
- **cells shorter than the 5-line window,** of which three are identical:
  - cell 1, loading the data: the same in codehealth, completion_time and coverage;
  - cell 2, splitting the groups: the same in all four;
  - cell 3 (perceived_productivity: cell 4), the colour scheme: the same in all four;
- **the two `bootstrap_ci_mean` copies,** which count 0 duplicated lines because one has a docstring.

**Why this is a problem, with evidence:**
- **The faulty data path is in a copied cell.** Fault R1 (§2) sits in the fourth copy of the
  data-loading cell, the one copy that differs from the other three.
- **A copied function has already drifted.** coverage's `cliffs_delta` drops NaNs itself. The callers of
  the other copy drop them first:
  - codehealth cell 29 (Phase 1 data, dropped in cell 26);
  - completion_time cell 15 (Phase 2, dropped in cell 10);
  - completion_time cell 23 (Phase 1, dropped in cell 19).

  So no reported number is affected. Those dropna calls matter, though. Phase 1 `clean_time` has 8 NaNs
  (3 AI, 5 manual), and among the 75 Phase 2 treatment/control rows `clean_time` has 3 (1 treatment,
  2 control). Called without them, the codehealth/completion_time copy would count every pair involving
  a NaN as a tie, pulling δ towards 0 with no error.
- **Every fix has to be made more than once.** A fix to Cliff's δ, or to its magnitude thresholds,
  means three edits, each checked by hand, since there are no tests.

## 2. Two faults stop `perceived_productivity` from running as shipped (R1, R2)

| Fault | Location | Evidence |
|---|---|---|
| R1: data path | cell 1 reads `data/task*_preprocessed.csv` (both `read_csv` calls); the other three notebooks read `../data/` | `repro/runs/20261022T150533Z/run_log.txt`: `FileNotFoundError: ... 'data/task1_preprocessed.csv'` |
| R2: missing import | cell 16 calls `shapiro`, but cell 0 imports only `levene` and `ttest_ind` from `scipy.stats` | `repro/runs/20261022T151200Z/run_log.txt` (R1 applied): `NameError: name 'shapiro' is not defined` |

**With both repairs it runs.** The repairs (`run_all.py --repairs R1,R2`) were declared in M1_PLAN.md
before any reported run; the successful run is `repro/runs/20261022T151209Z`. The other three notebooks
run as shipped.

**`rq3_measure.py` finds both faults from the code alone:** `data path prefixes in use: ['../data/',
'data/']` and `undefined names: ['shapiro']`. In 9c it can confirm that R2 is gone. It can confirm R1 is
gone only while paths stay literal `read_csv` arguments; a path built from variables isn't reported
(see the script's docstring). So 9c must also show a successful run without repairs.

## 3. The bootstrap is unseeded

- **No seed anywhere.** All four notebooks draw with `np.random.choice`, 10 call sites in all, and none
  sets a seed. Every CI uses 1,000,000 resamples.
- **The compared CIs still match at printed precision.** In our run, all 16 group-CI bounds (4 metrics ×
  2 groups × lower/upper) equal the authors' stored output when rounded as printed
  (`repro/rq1_status/20261022T153138Z/status.txt`; the difference CIs were not compared).
  - The one mismatch with the *paper*, the coverage control upper bound (0.74 in the paper, 0.71 in both
    our run and the stored output), is a paper-vs-stored discrepancy already listed in M1_PLAN.md
    threats. It is not run-to-run noise.
- **What it costs is exact re-running.** No run can be repeated bit for bit, and no CI can be compared
  exactly before and after a change. That is why the RQ3 decision rule compares CIs "with the same fixed
  seed in both versions", which these notebooks can't do as they stand. It is also why our 6b cross-check
  (`repro/recompute_rq1.py`) uses its own seed, 4928.

## 4. What the evidence does not show (the case for changing nothing)

Option (A), "no structural change", has real support, and 9a should weigh it fairly:
- **The reproduction succeeded as things stand.** Three notebooks run as shipped, and the fourth needs
  two small repairs (two path strings and one import), already declared and automated in
  `repro/run_all.py`. All four RQ1a metrics were REPRODUCED from these notebooks (7b).
- **The duplication is small.** The copied functions total 105 SLOC, about 14% of the 762 SLOC.
- **None of the drift has changed a result.** The differing `cliffs_delta` copies are only a hazard for
  future use.
- **The pressure is on whoever re-runs or extends the analysis** (us now, and the later Change Event B in
  Week 10), not on the original authors. The package is a finished replication artefact.
- **Runtime is not part of this problem.** The run logs record it (52–159 s per notebook), but we didn't
  analyse it.

**Verdict: the pressure is real but moderate.** It comes down to three things:
- copies that have already diverged once;
- the faulty data path sitting in the one differing copy of a copied cell;
- results that can't be re-run exactly.

Duplication on its own is not the argument.
