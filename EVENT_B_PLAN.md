# Event B plan (recorded before execution)

> We wrote this plan on 10 Nov 2026, **before** the follow-up feature was written or run in either
> variant. It is frozen with the tag `EVENT_B_PLAN`. After that tag, the prediction, the measures and
> the decision rule do not change. If we improve anything later, we report it separately from the
> first result.

- **Brief:** `P32_Event_B_STUDENT.docx` (course handout, not in the repo), read on 10 Nov 2026. In short:
  *"Apply one follow-up feature in the style of the study to both the frozen pre-M4 and modernised
  variants. Compare completion steps, changed files/tests and resulting maintainability/design
  quality."* We have to record the prediction first, compare at least two responses, build the
  smallest one we can justify, and say whether the Week 9 decision is supported, partly supported or
  should be revised.
- **Pre-event state:** tag `PRE_EVENT_B` on `6ed2782` (the merge of PR #8, 5 Nov 2026). Nothing was
  committed to `main` after that merge. We created the tag on 10 Nov, after reading the handout, but
  on that existing 5 Nov commit, so the frozen state did not change. The Week 9 decision is in
  `evidence/design/9a_alternatives.md` and `evidence/design/9b_9c_shared_module.md` (Option B, a shared
  and tested `frequentist/stats.py`). Its tracker cells (chosen intervention result and verification
  evidence) were filled in on 10 Nov from that 5 Nov evidence, without changes.

## 1. The two variants

| Variant | State | Where its feature goes |
|---|---|---|
| **Pre-M4** | The four notebooks at `PRE_EVENT_A` (`38920e8`), each with its own copies of the helpers | `evidence/event_b/pre_m4_variant/` (evidence only, never part of the shipped code) |
| **Modernised** | `PRE_EVENT_B` (`6ed2782`), where the notebooks import `frequentist/stats.py` | `frequentist/` (this becomes the state after our response) |

## 2. The follow-up feature

**We will analyse a fifth Phase 2 outcome, `test_runs`.** This is the number of times each
participant ran the acceptance tests (see `data/README.md`). We compare treatment and control in the
same way as the four existing notebooks: a descriptive table, a histogram, Shapiro-Wilk, a
significance test, an effect size and a bootstrap CI.

- **Why this feature:** it is the same kind of change the study itself makes (one more outcome
  through the same steps). The column is already in `task2_preprocessed.csv`, and none of the four
  frequentist notebooks looks at it. It needs no new data, so any difference between the variants
  comes from the design, not the data.
- **Fixed before we run anything:**
  - Both variants use the same data file. We record its sha256 in the run.
  - We follow the notebooks' own way of choosing a test. First we run Shapiro-Wilk on each group. If
    either group has p < 0.05, we take the non-parametric path (Wilcoxon rank-sum, Cliff's δ,
    bootstrap CI of the medians and of the median difference) and use **`coverage.ipynb` as the
    template**. Otherwise we take the parametric path (Student's t-test, Cohen's d, bootstrap CI of
    the means and of the mean difference) and use **`codehealth.ipynb` as the template**. Both
    variants use the same template.
  - **Pre-M4 build:** copy the template notebook as it was at `PRE_EVENT_A`, and change only what the
    new outcome needs (column, labels, file names). Anything the template already has stays in
    (helper copies, data path, no seed). This is how the feature would have been added before Week 9.
  - **Modernised build:** copy the template as it is at `PRE_EVENT_B` and make the same changes. This
    copy imports the helpers from `stats.py`.
  - We run both with `np.random.seed(4928)` so their numbers can be compared. For the pre-M4 copy the
    seed is set in memory, the same way `rq3_verify.py` did for "before".

## 3. Measures (both variants, same scripts)

| # | Measure | How |
|---|---|---|
| M1 | **Completion steps** | The edits needed after copying the template: each cell whose code differs from the template cell, plus each file changed outside the new notebook |
| M2 | **Changed files and lines** | Files added or changed, and their SLOC, compared with the variant's base tag |
| M3 | **Tests** | Test files added or changed. `python -m unittest discover -s repro -p "test_*.py"` must still pass |
| M4 | **Design quality** | `repro/rq3_measure.py` (unchanged, with the same settings as 8c and 9c) run on each variant after the change. It counts copied helper functions (names, copies, SLOC), duplicated logical lines across files (inside and outside functions), data paths (R1), undefined names (R2) and unseeded random calls |
| M5 | **No regression, same answer** | In the modernised variant, the four existing notebooks print exactly the same output before and after. The new notebook prints the same numbers in both variants |

## 4. Prediction

**We expect the pressure to land on the notebooks, not on `stats.py`.** The new outcome only needs
helpers the module already has. So in the modernised variant the change is one new notebook and
nothing else. In the pre-M4 variant it adds one more copy of each helper the template defines.

| # | Prediction (holds if...) | Why we expect it |
|---|---|---|
| P1 | In the modernised variant, `frequentist/stats.py` and `repro/test_stats.py` are unchanged (0 lines), and the new notebook is the only code file added or changed | The 9b module already has every helper the template uses |
| P2 | The pre-M4 variant adds **at least 3 copied helper functions (at least 25 SLOC)**. The modernised variant adds 0 | The `coverage.ipynb` template defines 3 helpers (31 SLOC). The `codehealth.ipynb` one defines 4 (45 SLOC) |
| P3 | The modernised variant needs **fewer completion steps (M1)** than the pre-M4 one | The pre-M4 copy also brings the data path, a bootstrap with no seed, and a choice of which `cliffs_delta` copy to keep |
| P4 | In **both** variants, the cells we kept out of the module in Week 9 (imports, colours, histograms, the Shapiro and effect-size printouts) get copied again. The new duplicated logical lines across files **outside function bodies** are within ±20% of each other between the variants | In Week 9 we left these in the notebooks on purpose, because they are layout, not analysis logic |
| P5 | The four existing notebooks print the same output before and after, and `test_runs` gives **identical numbers** in both variants | The module keeps the notebooks' behaviour, including the order of random draws (9c) |

- **Expected path:** non-parametric. `test_runs` is a count, so we expect Shapiro-Wilk to reject
  normality. That makes `coverage.ipynb` the template.
- **Expected verdict:** **Week 9 decision supported.** The main risk left is P4. Each new outcome
  still means copying one more notebook's worth of code at the notebook level.

## 5. Decision rule

- **Supported:** P1, P2 and P5 hold.
- **Partly supported:** P5 holds, but P1 or P2 fails (the module had to change, or it saved no helper
  code).
- **Should be revised:** P5 fails (the refactor changed a result, or the variants disagree), or P1
  and P2 both fail.
- P3 and P4 are reported as evidence for the trade-off. They are not part of the verdict.

## 6. Responses considered (for the modernised state)

| Option | What | Main trade-off |
|---|---|---|
| **A. No extra structural change** | Add `test_runs.ipynb`, which imports the existing helpers. `stats.py` stays the same | The smallest change, with no risk to the four verified notebooks. But the notebook-level copying (P4) grows by one more notebook |
| **B. Pull out a per-outcome pipeline** | Add a `compare_groups()` function and a plotting helper to `stats.py`, and make all five notebooks call them | Removes the notebook-level copying. But it rewrites four verified notebooks, means checking everything again, and builds an abstraction for only five callers, which risks speculative generality |
| **C. One parametrised notebook** | One notebook, run once per outcome (for example with papermill) | The least code. But it replaces the entry points the authors ship and moves away from the study's structure |

**Chosen before execution: A**, unless P1 fails. If P1 fails, we add only the missing helper to
`stats.py`, with a test, and record it as a deviation. We would only pick B or C if the results show
that copying at the notebook level, not helper copying, is the main cost of the change.

## 7. Order of work

0. **Before running anything,** fill in our Student Tracker row ("Event B prediction / expected
   pressure") with the feature, P1 to P5, the expected verdict and a link to the tag `EVENT_B_PLAN`.
1. Build both variants exactly as in section 2 and run them. The outputs go in
   `evidence/event_b/generated/`.
2. Take M1 to M5 and score P1 to P5 exactly as written.
3. Write `evidence/event_b/README.md` with the comparison table, the verdict under section 5, and one
   trade-off or anti-pattern risk with its evidence.
4. Fill in the tracker's "Event B response / accepted trade-off" cell with links to the commit, the
   tag and the evidence.
