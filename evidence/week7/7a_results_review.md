# Task 7a: RQ1 results and deviations

**Task owner:** Adam Urban. **Prepared:** 29 October 2026.

This consolidates the team's saved results for the task tracker and lab discussion.
The notebook runs and primary comparison were already produced by teammates.
Source snapshot: `c7c49f17cb2a7bc926d5f043ea82444685a51705`.

## Results

T means developers evolving code originally written with AI assistance; C means
developers evolving manually written code. Phase 2 developers worked without AI.
Numbers below use the precision fixed in M1; each paper/reproduced pair matches.

| Phase 2 metric | Paper T / C | Reproduced T / C | Paper / reproduced effect | Paper / reproduced p | Recorded status |
|---|---|---|---|---|---|
| Completion time, median minutes | 136 / 173 | 136 / 173 | Cliff's delta: -0.079 / -0.079 | 0.56 / 0.56 | REPRODUCED |
| Perceived productivity, mean | 3.95 / 4.06 | 3.95 / 4.06 | Cohen's d: -0.21 / -0.21 | 0.37 / 0.37 | REPRODUCED after R1/R2 |
| CodeHealth, mean | 8.49 / 8.44 | 8.49 / 8.44 | Cohen's d: 0.28 / 0.28 | 0.24 / 0.24 | REPRODUCED |
| Test coverage, median | 0.70 / 0.70 | 0.70 / 0.70 | Cliff's delta: 0.09 / 0.09 | 0.49 / 0.49 | REPRODUCED |

All four p-values exceed 0.05, matching the paper's significance calls. This
reproduces the bounded analysis; it does not establish equivalence between groups
or a general benefit from AI. These statuses are the team's recorded M2 outcomes.

## Deviations and audit findings

| Item | What happened | Treatment in this reproduction |
|---|---|---|
| R1: data path | Perceived productivity looked in `data/` rather than `../data/`. | Declared repair applied to a temporary copy; original failure retained. |
| R2: missing import | The same notebook called `shapiro` without importing it. | Declared import repair applied after recording the R1-only failure. |
| Sample | All 75 Phase 2 participants were used for group comparisons, rather than a first-12 subset. | M1's bounded sample; each metric retains the notebook's missing-value exclusions. IDs 0-11 are used separately for qualitative inspection. |
| Environment | Runs used Python 3.9.25 rather than the recorded 3.9.21; the authors did not provide dependency pins. | Team-chosen versions and actual kernel environment are saved with each run. |
| Test mismatch | CH/PP labels say Welch, but `equal_var=True` runs Student's t-test. | Reproduction keeps the shipped test. Enda's separate Welch sensitivity check leaves both significance calls unchanged. |
| Misleading headings | Coverage prints CodeHealth descriptive values under a TC heading; PP also has a copied TC heading. | Recorded as original reporting faults; no silent data relabelling or substitution. |
| Bootstrap randomness | Original confidence intervals use an unseeded bootstrap. | CI comparison is secondary under M1. The fixed-seed recompute is a separate cross-check. |
| Coverage CI discrepancy | Paper control interval ends at 0.74; stored notebook output and the reported rerun end at 0.71. | Explicit audit finding; does not change the preregistered primary reproduction status. |

## Evidence and review

- [Reported runs, full comparison and commands](../../repro/runs/README.md).
- Raw outputs: [CH](../../repro/runs/20261022T150533Z/codehealth.outputs.txt),
  [time](../../repro/runs/20261022T150533Z/completion_time.outputs.txt),
  [coverage](../../repro/runs/20261022T150533Z/coverage.outputs.txt),
  [PP after R1/R2](../../repro/runs/20261022T151209Z/perceived_productivity.repaired-R1-R2.outputs.txt).
- [Frozen M2 outcome](https://github.com/kourousis/cs4928-grp33/blob/M2_REPRO/M2_REPRO.md),
  [M1 rules](../../M1_PLAN.md) and [addendum](../../M1_ADDENDUM.md).

Reviewed on 29 October: CodeHealth comparison, R1/R2 repairs and documented
deviations. Results are summarised from the team's saved notebook runs.
