# M1_PLAN — G33 / P32 preregistration

**Group:** G33 · **Project:** P32 Downstream Maintainability of AI-Assisted Code
**Study:** Borg et al., "Echoes of AI", *Empirical Software Engineering* 31:161 (2026), doi:10.1007/s10664-026-10889-1
**Artefact:** github.com/codescene-research/echoes-of-ai-emse-2025 @ `472ebca6d20af5d6de4264897ba98220ce521fd0`
(accessed 12 Oct 2026; our copy is byte-identical apart from CRLF line endings)

> **Timing note.** The RQs (below, verbatim) and the RQ1 expected result were entered in the shared
> workbook in Week 5. This file was committed and tagged `M1_PLAN` on __ Oct 2026 (Week 6; M1 was due
> in Week 5). Before tagging, on 14 Oct, Claude (AI-assisted) ran the following on a separate copy of
> the authors' repo. These are **not** our reported runs, but their outputs were seen:
> - runner tests, all times UTC:
>   - 11:44: `codehealth`
>   - 11:47: all four notebooks (three ran; `perceived_productivity` failed)
>   - 11:57, 12:31, 12:38 and 14:01: re-tests of the runner
>   - 12:39 and 14:02: `perceived_productivity` with repairs R1 and R2 applied
> - the JSON linkage checks reported in § Linkage;
> - the group-blind Table 8 consistency check, which is RQ2 fallback (a): 18 of 18 rows matched.
>
> The RQs and the RQ1 expected result were not changed after these. The decision rules, the
> precision rules, the declared repairs and the RQ1b/RQ2/RQ3 expected results **were written after
> them**. See the deviation log.

### Mapping to the paper
Our RQ1 covers the paper's Phase 2 frequentist hypotheses H0 1–H0 4 (§3.2.1). In the paper these are
split across its own RQ1 (efficiency: completion time and perceived productivity, §4.2) and its RQ2
(maintainability: CodeHealth and test coverage, §4.3). Our RQ2 and RQ3 have no counterpart in the paper.

---

## RQ1 — bounded reproduction + aggregation audit

**RQ1 (verbatim):** "To what extent can the paper's Phase 2 comparison between treatment (developers
evolving AI-assisted code) and control (developers evolving manually written code) be reproduced from
the replication package for CodeHealth, completion time, test coverage and perceived productivity, and
can the published project-level CodeHealth aggregation be audited from the file-level data?"

### RQ1a — the four Phase 2 comparisons

**Targets (paper values):**

| Metric | Notebook | Paper location | Treatment vs control | Effect size | p (two-sided) |
|---|---|---|---|---|---|
| Completion time | `completion_time.ipynb` | §4.2.1, Fig. 13b | median 136 vs 173 min | Cliff's δ = −0.079 | 0.56 (rank-sum) |
| Perceived productivity | `perceived_productivity.ipynb` | §4.2.2, Fig. 15b | mean 3.95 vs 4.06 | Cohen's d = −0.21 | 0.37 ("Welch's") |
| CodeHealth | `codehealth.ipynb` | §4.3.1, Fig. 18b | mean 8.49 vs 8.44 | Cohen's d = 0.28 | 0.24 ("Welch's") |
| Test coverage | `coverage.ipynb` | §4.3.2, Fig. 20b | median 0.70 vs 0.70 | Cliff's δ = 0.09 | 0.49 (rank-sum) |

The secondary targets are the bootstrap 95% CIs printed in the paper:

| Metric | Treatment | Control |
|---|---|---|
| Completion time | 105.5–180.0 | 118.1–210.0 |
| Perceived productivity | 3.77–4.12 | 3.88–4.24 |
| CodeHealth | 8.43–8.54 | 8.39–8.49 |
| Test coverage | 0.695–0.71 | 0.69–0.74 |

**Bounded sample.** The Phase 2 submissions in `data/task2_preprocessed.csv` are CSV rows 0–74: 75
rows with a `treatment` value, 40 `ai` and 35 `human`.

The file has 1001 rows. Rows 75–999 are empty. Row 1000 has only `estimated_time` = `clean_time` = 33
and no `treatment` or `github` value. The notebooks select by `treatment`, so row 1000 is excluded
automatically. We record it as a data anomaly.

The 75 participant IDs, in CSV row order:
`anon136 anon106 anon037 anon005 anon050 anon143 anon098 anon027 anon003 anon052 anon123 anon149 anon141
anon097 anon022 anon109 anon049 anon130 anon100 anon046 anon071 anon088 anon035 anon093 anon137 anon033
anon132 anon112 anon127 anon051 anon115 anon129 anon024 anon119 anon039 anon023 anon089 anon079 anon030
anon016 anon086 anon065 anon042 anon048 anon135 anon144 anon108 anon055 anon145 anon091 anon069 anon044
anon092 anon077 anon146 anon020 anon095 anon014 anon131 anon053 anon104 anon101 anon010 anon040 anon102
anon084 anon067 anon068 anon059 anon120 anon096 anon025 anon140 anon038 anon138`

Rows each test uses after the notebooks' own `dropna()`:

| Metric | Treatment | Control |
|---|---|---|
| CodeHealth | 40 | 35 |
| Coverage | 40 | 35 |
| Completion time (`clean_time`) | 39 | 33 |
| Perceived productivity (`pp_mean`) | 39 | 33 |

There are no exclusions beyond the authors' own.

We depart from the pack's "first 12" rule. The unit of analysis is the treatment-vs-control comparison,
and a two-sample test on 12 rows would not test the same hypothesis.

**Method.** The workbook method, verbatim: "Two-sided tests at α = 0.05, no multiple-testing
correction, re-run from the authors' published data and notebooks, then recomputed …" ← *paste the rest of the cell*.

1. **As-shipped run.** Run all four notebooks with `python repro/run_all.py` (Python 3.9, pinned in
   `repro/requirements.txt`).
   - The runner clears the authors' stored outputs before executing.
   - It saves to `repro/runs/<UTC>/`: the executed notebooks, their text outputs and figures, the
     package versions (from the runner process and from inside the notebook kernel), and input
     hashes (notebooks, data, pins, runner).
2. **Declared repairs.** A notebook that fails is recorded as FAILED. After that, only the repairs
   declared here may be applied, cumulatively and in order, so that each fault is captured in its own
   run:
   - `--repairs R1`, then
   - `--repairs R1,R2`.

   Each repair edits an in-memory copy; the authors' file is never changed. A repair that doesn't
   match exactly once aborts the run.
   - **R1 (`perceived_productivity`):** change the data paths `"data/…"` to `"../data/…"`, as in the
     other three notebooks.
   - **R2 (`perceived_productivity`):** add the missing `from scipy.stats import shapiro`. Cell 16
     calls it, but no cell imports it.

   Both are path/dependency errors, which the Week 6 sheet allows because they don't change the
   method. Any further failure makes that metric INCONCLUSIVE/BLOCKED. We will not apply any
   undeclared fix.
3. **Audit step (reported separately from the status).** The CH and PP cells say "Welch's t-test", as
   does paper §3.4.1, but the code runs `ttest_ind(..., equal_var=True)`, which is Student's t-test.
   Our status uses the as-shipped test. We also report Welch's (`equal_var=False`) as a sensitivity
   check.

**Decision rule.** Each metric is decided on its own.

**Primary criteria.** All of the following must match the paper:
- the p-value;
- the effect size;
- the point estimates (means or medians);
- the significance call at α = 0.05.

These are exact matches after rounding; there is no tunable tolerance. Rounding works as follows:
- **Convention.** Our value is formatted with Python `format(x, '.Nf')` on float64, where N is the
  number of decimals the paper prints for that value. This is the convention the paper's own numbers
  follow (e.g. Table 8 prints 3/40 as 0.07).
- **Decimals (N) by value:**

  | Value | N |
  |---|---|
  | All p-values | 2 |
  | Cliff's δ, completion time | 3 |
  | Cliff's δ, coverage | 2 |
  | Cohen's d | 2 |
  | Means (CH, PP) | 2 |
  | Median time, in minutes | 0 |
  | Median TC | 2 |
- **Edge cases.**
  - If our value sits exactly on a rounding boundary and the paper's figure equals either neighbour,
    it counts as a match. We record this.
  - If the paper's prose and its figure/table disagree, the prose value in §4.2.1–§4.3.2 is the target.

**Secondary criteria (reported; they don't change the status).**
- We compare bootstrap CIs with both the paper and the authors' stored notebook output.
- The bootstraps are unseeded, so ±0.01 (±1 min for time) is expected noise.
- Any disagreement between the paper and the stored output is an **audit finding**.

**Status per metric** (the coordinator's vocabulary from the Week 6 sheet):

| Status | Meaning |
|---|---|
| REPRODUCED | A valid completed run meets every primary criterion. |
| NOT REPRODUCED | A valid completed run misses any primary criterion. |
| INCONCLUSIVE/BLOCKED | No valid run is possible, even after R1/R2. |
| IN PROGRESS | The pipeline is valid but this metric's run is not yet complete. Not a final outcome; must be resolved before M2. |

**Overall RQ1a status.** We always report the four per-metric statuses. The headline status is the
first rule below that applies:
1. Any metric IN PROGRESS → **IN PROGRESS**.
2. Else, any metric NOT REPRODUCED → **NOT REPRODUCED**.
3. Else, any metric INCONCLUSIVE/BLOCKED → **INCONCLUSIVE/BLOCKED**.
4. Else → **REPRODUCED**.

If a metric needed R1/R2 to run, that is recorded as a deviation; it doesn't by itself lower the
metric's status.

**Expected result (verbatim from workbook):** "RQ1: No significant difference between treatment and
control on any of the four Phase 2 metrics (Phase 2 was underpowered for …" ← *paste the rest*.

**What would count as non-reproduction:** a valid run in which any metric misses a primary criterion.
In particular, p < 0.05 on any metric would be a non-reproduction.

### RQ1b — CodeHealth aggregation audit

**Published rule.** `data/README.md` defines project CodeHealth as the SLOC-weighted mean of the
file-level CodeHealth scores.

**Known before running.** `data/task2_codeHealth.json` has 75 entries, keyed `id` 0–74. Each entry
lists per-file CodeHealth scores and smell warnings. There is **no SLOC** and **no participant ID**
(§ Linkage). So the published weighted aggregation cannot be recomputed from the package alone.

**Sample.** All 75 entries.

**Method.**
1. Parse every `Code health score` in each entry.
2. Compute the unweighted mean, once over all files and once over `src/main` files only.
3. If a validated linkage is obtained (L1/L2 below), compare each participant's recomputed value with
   their published `codehealth`. Report Spearman ρ, the mean absolute difference, and the share that
   match to 2 dp.
4. Report the group-blind distributions of the recomputed and published values (mean, SD, range).
   This is descriptive context only and does not feed the decision.

**Decision rule.**

| Outcome | When |
|---|---|
| **AUDIT PASSED** | Linkage **and** SLOC weights are obtained (from the authors), and ≥ 95% of published values recompute to 2 dp. |
| **AUDIT FAILED** | Linkage and SLOC are obtained, but fewer than 95% recompute. We report the size of the gap. |
| **NOT AUDITABLE FROM PACKAGE** | Linkage or SLOC is missing. This is a valid finding about the artefact. |

Without SLOC, any linkage-only comparison is reported descriptively and does not count as a pass or a fail.

**Expected result** (proposed by Claude, adopted by the team on 14 Oct 2026): NOT AUDITABLE FROM PACKAGE.

---

## RQ2 — transfer to other maintainability measures

**RQ2 (verbatim):** "Do two other maintainability measures in the package, PMD rule violations and
CodeScene code-smell deltas, show the same Phase 2 treatment-versus-control pattern as CodeHealth?"

**"The CodeHealth pattern" (fixed now, from the paper).** There is no significant difference between
the groups (p = 0.24), with a small difference in treatment's favour (d = +0.28). We compare against
these paper values even if RQ1a produces different ones.

**Data.**
- `data/task2_pmd.json`: PMD 7.13.0 output.
- `data/task2_cs_delta.json`: CodeScene smell changes.

Each file holds 75 entries, keyed `id` 0–74, with no participant ID.

**Counting unit (cs_delta), fixed now.**
- **Level.** Count at finding level: one finding = one `findings[]` element, typed by its own
  `change-type`.
- **Change types.** introduced / degraded / unchanged / improved / fixed, where "fixed" = the paper's
  "removed". We ignore the nested `change-details[].change-type`.
- **Files.** Every file record in the entry: 106 records in total, including 24 outside `src/main`
  and 7 with no `name`.
- **Categories.**
  - For the RQ2 measures: all 11 smell categories present.
  - For the Table 8 check (L2): Table 8's five categories only (Bumpy Road Ahead, Code Duplication,
    Complex Conditional, Complex Method, Primitive Obsession).

**Counting unit (PMD), fixed now.** Total `violations[]` across every file in the entry, including test
files, as the authors ran it.

### Linkage (a prerequisite, checked before tagging on 14 Oct)
No column links JSON `id` to `github`/`treatment`, and no notebook joins them.

We tested five candidate orders of the 75 CSV rows against JSON `id` 0–74. Date parsing:
- `entry-date` is d/m/Y H:M:S.
- `exit-date` is mostly m/d/Y. One value is valid only as d/m/Y (31/01/2025). Three are missing and
  sorted last.

| Candidate order | RefactoringMiner commits vs `gh-commits`: ρ (exact matches) | Unweighted `src/main` CH vs `codehealth`: ρ (p) |
|---|---|---|
| CSV row order | −0.03 (19/75) | 0.05 (0.69) |
| anon ID ascending | 0.01 (14/75) | −0.08 (0.48) |
| entry datetime | 0.13 (22/75) | 0.33 (0.004) |
| exit datetime | −0.07 (17/75) | −0.09 (0.45) |
| predecessor ID ascending | −0.02 (18/75) | 0.18 (0.13) |

A correct link would give near-exact commit counts. **The link is not recoverable from the package.**
Entry-date order is the weak best candidate, and we will mention it to the authors.

- **L1.** Ask the authors for the `id` → participant mapping (and, for RQ1b, per-file SLOC) through a
  GitHub issue on the artefact repo. Raised on 17 Oct 2026 by Enda
  ([codescene-research/echoes-of-ai-emse-2025#1](https://github.com/codescene-research/echoes-of-ai-emse-2025/issues/1)).
- **L2.** We accept a mapping only if it reproduces paper Table 8 from `task2_cs_delta.json`.
  - Compare **recovered integer counts**, not rounded means: for each Table 8 row and group, the count
    must equal round(n · mean), with n = 40 or 35.
  - We compare counts because Table 8's 2 dp means carry rounding error.
- **Deadline.** The Week 7 M2 checkpoint. If there is no validated mapping by then, we switch to the
  fallback.

**Primary method (if a validated link exists).**
- **Sample.** All 75 participants. We depart from "first 12" for the same reason as RQ1a.
- **Measures (one per tool, as in the RQ wording):**
  - **M-PMD:** PMD total violations per participant.
  - **M-SMELL:** net smell change per participant = (`fixed` + `improved`) − (`introduced` + `degraded`)
    findings. Higher is better.
  - The two components, "better" and "worse", are reported descriptively only; they do not enter
    the answer.
- **Test.** For each measure, treatment vs control: two-sided Wilcoxon rank-sum, α = 0.05, plus
  Cliff's δ (the paper's route for non-normal data). No multiple-testing correction.
- **Decision rule.**
  - **Pattern per measure:**
    - **matches** the CH pattern if p ≥ 0.05 and δ favours treatment (fewer PMD violations; higher net
      smell change). δ is reported to 3 dp.
    - **contradicts** it if p < 0.05, in either direction;
    - is **inconsistent in direction** if p ≥ 0.05 and δ favours control or δ = 0.000.
  - **RQ2 answer:**
    - **YES** if both measures match;
    - **NO** if either contradicts;
    - otherwise **MIXED**.

**Fallback (no validated link by M2).** The group comparison becomes **INCONCLUSIVE/BLOCKED**: an
infrastructure limitation under the brief's contingency route. We then report two group-blind
analyses:
- **(a) Consistency check.** Pooled counts over all 75 entries for each Table 8 row, compared with
  round(40·T) + round(35·C) from Table 8. *Already run before tagging: 18 of 18 rows match. At 2 dp
  only 12 of 18 would have matched, because of Table 8's rounding.*
- **(b) Qualitative inspection.** The first 12 entries in stable order (JSON `id` 0–11). For each, we
  record the smells introduced or fixed (with files) and the PMD rules with the most violations. This
  follows the pack's "inspect a small set … qualitatively"; group labels are unknown.

**Expected result** (proposed by Claude, adopted by the team on 14 Oct 2026). Written without having seen
any per-group PMD or smell value from the package. The bases are:
- paper Table 8, from which net smell change is about −0.76 for treatment vs −0.84 for control on its
  five categories;
- paper Table 12, Task 1 PMD totals: AI-dev mean 512 vs 490, but median 456 vs 465.

| Measure / case | Prediction | Confidence |
|---|---|---|
| M-SMELL | p ≥ 0.05, δ slightly favours treatment (negligible or small, \|δ\| < 0.33) → **matches** | moderate |
| M-PMD | p ≥ 0.05, \|δ\| < 0.147 (negligible), slightly favouring treatment (fewer violations), inherited from the lower Task 1 median → **matches** | low (direction is close to a coin flip) |
| RQ2 answer, if linked | **YES** | low–moderate |
| Linkage | No validated mapping from the authors by the Week 7 M2 checkpoint, so the group comparison ends **INCONCLUSIVE/BLOCKED** | moderate |
| Fallback (a) | All 18 Table 8 rows match as counts (already observed before tagging; see timing note) | — |

This prediction would be wrong if either measure shows p < 0.05 (answer NO), or if δ favours control
(answer MIXED).

---

## RQ3 — design / modernisation (carries the required Week 9 / M4 design work)

The brief requires a design/modernisation stage (M4, Week 9; rubric criterion "Software design /
refactoring / modernisation decision", 12 marks). RQ3 is where our group answers it. The brief allows
a third RQ "when it clearly adds value"; this one does, because it holds a required stage.

**RQ3 (verbatim):** "Can the duplicated, hard-to-re-run analysis code in the replication package be
restructured into a shared, tested module without changing any reproduced result, and is that change
justified compared with leaving the code as it is?"

**Unit.** The four `frequentist/` notebooks.
- **Known duplication:** data loading, Cohen's d, Cliff's δ, and the bootstrap CI functions.
- **Known re-run faults:** the inconsistent data path (R1), the missing import (R2), and the unseeded
  bootstraps.

**Alternatives.**
- **(A) No structural change:** the notebooks as they are, plus the declared repairs and a runner.
- **(B) Shared module:** extract a shared `stats` module with unit tests, and have the notebooks import it.

**Decision rule.** (B) is justified only if both of these hold:
1. Every RQ1a primary value is identical before and after, at full printed precision. CIs are compared
   with the same fixed seed in both versions.
2. It removes the duplicated functions and faults R1/R2, with tests covering each extracted function.

Otherwise we choose (A) and report why.

**Expected result** (proposed by Claude, adopted by the team on 14 Oct 2026): (B) preserves all results and is justified, mainly
because it removes the faults that broke `perceived_productivity`.

---

## Threats and audit findings (known now)
- **Library versions** are our choice (the last releases supporting Python 3.9); the authors published
  none. The runner records the versions actually used, including inside the kernel.
- **Unseeded bootstraps** with 1,000,000 resamples: the CI's last digit can vary between runs.
- **Welch vs Student.** The paper and the notebooks say Welch's, but the code runs Student's. The
  paper's p-values match Student's; Welch's would give CH p = 0.235, which rounds to 0.23.
- **TC control CI.** The paper says 0.69–0.74; the authors' stored notebook output says 0.69–0.71.
- **Stray CSV row.** Row 1000 of `task2_preprocessed.csv` has values without a participant.
- **`coverage.ipynb`:**
  - its "TC Descriptive Statistics" cell actually summarises `codehealth`;
  - its markdown says "We reject the null hypothesis of difference" at p = 0.49.
- **`data/README.md`** documents a column `pp_mran`, but the column is `pp_mean`.
- **Table 8** rounding is not half-up (3/40 → 0.07, 7/40 → 0.17). The prose on p. 38 says "18%, 7
  solutions" for the same cell.
- **Unlinkable JSON.** The JSON files cannot be linked to participants, and SLOC is absent (RQ1b, RQ2).
- **Malformed JSON.** `task2_miner.json` is not strict JSON (control characters); it parses with
  `strict=False`. It is used only for the linkage check.

## AI use (material only)
Claude (AI assistant) did the following:
- wrote `repro/` (the runner and the version pins) and ran the pre-tag checks listed in the timing note;
- identified faults R1 and R2, the Welch/Student mismatch and the linkage problem;
- drafted this plan from the team's workbook entries.

Two independent AI reviews were run on drafts.
- They found a runner bug, now fixed, that had let the authors' stored outputs show up in a failed run.
- They also found the Table 8 rounding issue and gaps in the rules.

The paper values, counts and IDs above were checked against the paper and the data. The team remains
responsible for verifying them.

## Held-out boundary
No Change Event material has been opened.

## Change / deviation log
| Date | Change | Why |
|---|---|---|
| 14 Oct 2026 | M1 committed and tagged in Week 6, not Week 5 | Late; RQs and the RQ1 expectation were already in the workbook in Week 5 |
| 14 Oct 2026 | Decision rules, precision rules and RQ1b/RQ2/RQ3 expectations written after the pre-tag outputs were seen | Disclosed. Primary criteria are exact-match after a fixed rounding convention, with no tolerance to tune |
| 14 Oct 2026 | Declared repairs R1 and R2 for `perceived_productivity`, before any reported run | The as-shipped notebook cannot run (path, missing import) |
| 14 Oct 2026 | RQ1a/RQ2 sample = all 75 participants, not "first 12" | The group comparison is the unit of analysis |
| 14 Oct 2026 | RQ2 group comparison depends on obtaining the linkage (L1/L2) | The package does not link the JSON files to participants |
| 14 Oct 2026 | RQ2 uses one measure per tool: PMD total violations and net smell change (team decision D1) | The RQ names two measures; net change uses both smell directions without double-counting |
| 14 Oct 2026 | RQ2 expected result adopted (team decision D2), proposed by Claude from paper Tables 8 and 12 | Prediction made before any per-group RQ2 value was seen |
| 14 Oct 2026 | RQ1b and RQ3 expected results adopted, as proposed by Claude | Predictions made before any RQ1b/RQ3 analysis was run |
| 14 Oct 2026 | RQ3 marked as carrying the M4 design work, not optional (team decision D3) | The brief makes the design stage mandatory |
| 16 Oct 2026 | RQ1b: files whose score is `null` (written `nu` in the JSON; 84 of 1,774 file lines, in 74 of 75 entries, 74 of them `RecipeRepository.java`, all under `src/main`) are left out of the unweighted means and counted per entry. Proposed by Claude, accepted by Enda | CodeScene gives no score for these files and the plan didn't say how to treat them. Decided before the RQ1b run: the rule is in `repro/recompute_rq1b.py` as last edited on 16 Oct, whose hash is in `repro/rq1b_codehealth/20261017T143340Z/inputs_sha256.txt`. The published SLOC-weighted rule can't be checked either way |
| 16 Oct 2026 | Enda's script runs (6b, 6c, 6d) use Python 3.9.25 (installed with `uv`) | The authors' notebooks record 3.9.21. Same minor version, so no effect on results is expected; each run's `environment.txt` records the version used |
| 17 Oct 2026 | 6b: our own fixed-seed recompute of the four RQ1a comparisons (`repro/recompute_rq1.py`, seed 4928, 1,000,000 resamples) is added as a cross-check. It does not set the RQ1a status, which still comes from the as-shipped notebook runs (Method step 1) | The workbook (G37) promises a result "recomputed independently with a fixed seed", but this plan didn't include it. Run first on 16 Oct (`repro/recompute/20261016T155931Z`) |
| 17 Oct 2026 | 6b re-run with its own bootstrap stream for each metric and group (`default_rng([seed, metric, group])`) instead of one stream shared by all four metrics. The 16 Oct run is kept as made. Found in an AI review (Claude), fix accepted by Enda | With one shared stream, a metric's CIs depended on which metrics ran before it, so no metric could be recomputed alone, and 9c needs exactly that. Point estimates, test statistics, p-values and effect sizes don't use the bootstrap and can't change; only the CIs can |
| 17 Oct 2026 | 6c and 6d re-run after adding input checks (expected ids, keys, paths, empty PMD error fields). 6d also now writes per-entry counts by change type and category, and checks that Table 8's 7 unprinted cells pool to 0. The first runs (`20261017T143340Z`, `20261017T143341Z`) are kept as made. Found in an AI review (Claude), accepted by Enda | The per-category counts are needed for the L2 per-group check. The checks only stop a run on unexpected input, so the per-entry numbers must equal the first runs' |
| 17 Oct 2026 | RQ2: PMD totals include generated code. Entries 56 and 60 have 12 PMD file records under `./target/generated-sources/` (264 violations), which are counted | The "every file" counting rule covers them, but the plan didn't mention generated code. Disclosed; the rule is unchanged |
| 22 Oct 2026 | 7b (`repro/rq1_status.py`): the RQ1a primary values are read as the notebooks print them (p-values to 5 significant figures, d and δ to 4 dp, means and medians to 1–2 dp), then rounded by the convention above. Each one is cross-checked against the full-precision 6b value, and any value where the two round differently is flagged. Proposed by Claude, accepted by Enda | The status comes from the as-shipped run, and the notebooks print only rounded values, so the value we round has already been rounded once. The cross-check shows whether that changed any result. Decided before `rq1_status.py` was run on any reported 6a run. In the first 7b run (`repro/rq1_status/20261022T153138Z`) all 20 values agree with 6b, so this choice changes no status |
| 29 Oct 2026 | RQ3: the "duplication and line counts before/after" in our frozen method (Student Tracker, G33 row, method column) is now defined in `repro/rq3_measure.py` (8c): SLOC and logical lines per file, functions defined in more than one file (compared by AST), and the share of logical lines in a run of 5 or more that also occurs in another file. The baseline is the four `frequentist/` notebooks at `PRE_EVENT_A` (`repro/rq3_measure/20261029T132012Z`). Proposed by Claude, accepted by Enda | The method named the measure but not how to count it. Fixed before any RQ3 change, so the "after" measurement in 9c can't be tuned to the result. SLOC and the duplicated-line share are descriptive only; the function-copy and fault outputs are evidence for decision-rule criterion 2 (duplicated functions and R1/R2 removed) |
