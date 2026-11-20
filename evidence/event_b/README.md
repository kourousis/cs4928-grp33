 # Cross team feedback result
G32’s finding was a general one, that we should add more evidence and verification. We accepted it. We didn’t make a change because our design verification was already there: a before-and-after re-run with identical outputs, plus the tests seemed strong enough to us.
 
Where verification really is limited is RQ2. The authors’ data doesn’t say which code was AI-assisted and which was written by hand for each participant, so we couldn’t check it directly and used the fallback analyses instead

# Event B: result

We ran this on 10 Nov 2026, following `EVENT_B_PLAN.md` at the tag `EVENT_B_PLAN`. The prediction was
pushed and tagged before either variant of the feature was written or run. The pre-event state is the tag
`PRE_EVENT_B` (`6ed2782`).

**Short answer: the Week 9 decision is supported.** We added the same new feature to the old notebooks
and to the shared-module version. Writing it took the same number of edits in both. But the old version
left behind three more copied helper functions, a data path that depends on the working folder and an
unseeded bootstrap. The new version left behind none of these, needed no change to `stats.py` or its
tests, and gave exactly the same numbers.

## What we did

The Event B brief asked us to add one follow-up feature "in the style of the study" to both the frozen
pre-M4 code and the modernised code, then compare them.

- **The feature:** a fifth Phase 2 outcome, `test_runs` (how many times each participant ran the
  acceptance tests). The data already has this column, but no notebook analyses it.
- **How it was built:** Shapiro-Wilk rejected normality in both groups (p < 0.001), so the plan's rule
  picked `coverage.ipynb` as the template.
  - **Pre-M4:** we copied `coverage.ipynb` as it was at `PRE_EVENT_A`. The result is
    `pre_m4_variant/test_runs.ipynb` (kept as evidence only).
  - **Modernised:** we copied `coverage.ipynb` as it is at `PRE_EVENT_B`. The result is
    `frequentist/test_runs.ipynb`.
  - Both copies got exactly the same list of edits (`EDITS` in `repro/event_b.py`), so any difference
    comes from the starting point and not from how we edited them.
- **Response chosen: Option A** (no extra structural change). This was the choice made in the plan
  before running, and the result gave no reason to change it (see "Responses" below).

## Results

| | Pre-M4 | Modernised |
|---|---|---|
| Cells edited after copying (M1) | 9 (7 code, 2 text) | 9 (7 code, 2 text) |
| Other files changed (M1, M2) | none | none (`stats.py` and `test_stats.py` untouched) |
| Size of the new notebook (M2) | 151 SLOC | 112 SLOC |
| Helper functions copied into it (M2) | 3 (`cliffs_delta`, `bootstrap_ci_median`, `bootstrap_ci_median_difference`), 31 SLOC | 0 |
| Tests added or changed (M3) | none, all 94 still pass | none, all 94 still pass |
| Copied helper code across the analysis (M4) | 105 → 136 SLOC | 0 → 0 |
| Copies of each helper (M4) | `cliffs_delta` 3 → 4, `bootstrap_ci_median` 2 → 3, `bootstrap_ci_median_difference` 2 → 3 | one copy each, in `stats.py` |
| Share of duplicated lines (M4) | 24.9% → 30.7% | 10.8% → 12.8% |
| New duplicated lines outside functions (M4) | +39 | +23 |
| Re-run problems in the new file (M4) | data path `../data/` (R1 risk), unseeded bootstrap | none |
| Same numbers in both? (M5) | yes, all 26 printed lines are identical | |

The four existing notebooks, `stats.py` and the data are byte-for-byte the same as at `PRE_EVENT_B`. With
the seed set in each notebook, that means they print exactly what they printed before (P5).

### Prediction check (scored by the script, exactly as written in the plan)

| | Result | What happened |
|---|---|---|
| P1 | **Holds** | Only the new notebook was added. `stats.py` and its tests are unchanged |
| P2 | **Holds** | Pre-M4 copied 3 helpers (31 SLOC). Modernised copied none |
| P3 | **Fails** | Both needed 9 edits. Copying is just as quick either way. The cost of the old design is not in the effort to add the feature now, but in what it leaves behind |
| P4 | **Fails** | Pre-M4 added 39 duplicated lines outside functions and modernised added 23, so not within 20%. We underestimated Week 9: it also moved data loading, the group split and the effect-size labels into the module, so less is copied at notebook level than we expected |
| P5 | **Holds** | Same numbers in both variants, and no change to the existing results |

Under the plan's rule (P1, P2 and P5 hold), the **Week 9 decision is supported**. P3 and P4 are
trade-off evidence, not part of the verdict.

### The feature's own result

For completeness: test runs show no clear difference between the AI-assisted and manual groups in
Phase 2. The medians are 6 vs 5.5, the Wilcoxon rank-sum p = 0.74, Cliff's δ = 0.05 (negligible), and the
95% bootstrap CI of the median difference is [-3, 3]. This outcome is not in the paper and is not one of
our RQs, so we report it only as the output of the feature.

## Responses considered

- **A. No extra structural change (chosen).** We added the one notebook and nothing else. It is the
  smallest change, and it does not touch the four verified notebooks. The cost is that the plotting and
  printing cells are copied once more (23 duplicated lines for this outcome).
- **B. Pull a per-outcome pipeline and a plotting helper into `stats.py`.** This would remove those 23
  lines, but it means rewriting four notebooks we've already verified line by line and checking them all
  again. Building an abstraction for five callers also risks speculative generality. The evidence
  doesn't justify it yet.
- **C. One parametrised notebook run once per outcome.** This is the least code, but it replaces the
  notebooks the authors ship and moves away from how the study is organised.

## Trade-off we accepted

We kept the duplicated plotting and printing cells in each notebook rather than adding more
structure. This is a small copy-and-paste risk. It is a mild form of the "duplicated code" smell, and it
grows by about 20 to 25 lines with each new outcome. We would revisit Option B if a change had to touch the plots in
every notebook at once (for example, a new colour scheme) or if more outcomes were added.

The anti-pattern we avoided is the more serious one. In the old design each new outcome adds another copy
of the statistics helpers. Those copies have already drifted apart: `cliffs_delta` and
`bootstrap_ci_median_difference` each exist in two different versions, and the new copies just pick up
whichever version the template happened to have (here the coverage one).

## Evidence and re-run

| What | Where |
|---|---|
| Plan and prediction (frozen) | `EVENT_B_PLAN.md`, tag `EVENT_B_PLAN` |
| Script that builds, runs, measures and scores both variants | `repro/event_b.py` |
| Full run output (report, scores, both notebooks' printouts, four measure reports, hashes) | `generated/20261110T174012Z/` |
| The new notebook | `frequentist/test_runs.ipynb` |
| The pre-M4 copy (evidence only, not run from here) | `pre_m4_variant/test_runs.ipynb` |

```bash
python repro/event_b.py run      # rebuild check, run both variants, measure and score (about 3 min)
python -m unittest discover -s repro -p "test_*.py"   # 94 tests, OK
```

- The measures use `repro/rq3_measure.py` unchanged (same 5-line window as 8c and 9c). The script only
  points it at the files to compare and splits the duplicated lines into inside and outside functions
  for P4.
- The "before" measures match the earlier ones: 163 of 655 duplicated lines and 105 SLOC of copied helpers
  at `PRE_EVENT_A` (8c), and 62 of 574 at `PRE_EVENT_B` (9c).
- The pre-M4 copy was run from a temporary folder laid out like the repo, with the seed added in memory,
  as `rq3_verify.py` did for "before". The committed copy has no seed and no outputs, exactly as a
  developer would have left it.

## Conclusion

The Week 9 decision to move the shared statistics into `stats.py` is supported. Adding the same feature to
both versions took the same effort (9 edits each), but the old design left behind 3 more copied helpers,
a working-folder-dependent data path and an unseeded bootstrap, and the modernised design left behind none.
It needed no change to `stats.py` or its tests, and both versions printed identical numbers. The benefit of
the modernisation is therefore not that new work is faster to write. It is that new work leaves less to
maintain. The remaining cost is the plotting and printing cells that are still copied per notebook (23 new
duplicated lines, 12.8% duplication overall), which we accepted rather than refactor verified notebooks.

## Limitations

- **One feature, one template.** The result comes from a single added outcome (`test_runs`) built from a
  single template (`coverage.ipynb`). A different outcome, or a template with different copied code, could
  change the counts. The prediction was also checked once, on one run.
- **The verdict rests on three of five predictions.** P3 (effort) and P4 (duplicated lines outside
  functions) failed, so the evidence for "less effort" and "much less copying at notebook level" is
  negative or weaker than we predicted. We treated them as trade-off evidence, as the plan said.
- **Effort is counted in edits, not time.** Both variants got the same scripted list of edits, so "same
  effort" means the same edit count. It does not measure how long a developer would take, or whether they
  would notice the extra helper copies or the unseeded bootstrap.
- **We built both variants ourselves.** We wrote the feature for both and we also wrote the plan and the
  prediction, so this is not an independent check. The pre-registered tag and the script scoring the
  predictions are there to limit this, not to remove it.
- **The comparison is only as good as the measures.** Duplication uses the 5-line window of
  `repro/rq3_measure.py`. Duplication inside functions is not counted in P4. "Same numbers" covers the 26
  printed lines of the new notebook, and the pre-M4 copy was run from a temporary folder with the seed
  added in memory rather than as committed.
- **The feature's own result is not a finding.** `test_runs` is not in the paper and is not one of our RQs.
  The null difference (p = 0.74) says nothing about RQ1 or RQ2.
- **Duplication still grows.** In the modernised version each new outcome adds about 20 to 25 duplicated
  lines. Option B becomes worth doing if a plot change has to touch every notebook, or if more outcomes are
  added.
- **RQ2 verification is still limited.** As noted at the top, the authors' data doesn't say which code was
  AI-assisted, so RQ2 was checked with fallback analyses only.
