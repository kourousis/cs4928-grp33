# Material AI contributions

Started 20 October 2026 for Adam's task **5h**. Record only AI contributions
that affected a method, engineering decision or interpretation. AI output is
not evidence by itself. Keep accepted/modified/rejected decisions and link the
checks that support them. No full prompt transcripts are required by the brief.

## Earlier contributions, recorded retrospectively

Earlier contributions were summarised on 20 October from M1_PLAN.md and PR #1.
Dates below identify when the documented work took place.

| Documented date | Material AI contribution | Decision/status recorded by the project | Evidence and verification record |
|---|---|---|---|
| 14 Oct 2026 | Claude drafted M1 from workbook entries and proposed RQ1b/RQ2/RQ3 expectations. | M1 records team adoption, including D1/D2/D3, and the timing of rules/expectations relative to pilot outputs. | [M1_PLAN.md](M1_PLAN.md), timing note, expected-result sections and deviation log. |
| 14 Oct 2026 | Claude wrote the notebook runner and identified path/import failures R1/R2, the Welch/Student mismatch and JSON linkage limitations. | Plan accepts the runner and only the two declared in-memory repairs, with as-shipped failures retained first. | [Runner](repro/run_all.py), [run instructions](repro/README.md), M1 method and audit findings. |
| 14 Oct 2026 | Two AI reviews found stale notebook outputs surviving a failed run, plus rounding/rule gaps. | M1 records the runner bug as fixed and rules clarified. | M1 "AI use" and timing note; runner clears stored outputs before execution. |
| 16-17 Oct 2026 | Claude assisted Enda's statistical/counting scripts; an AI review found the shared bootstrap-stream dependency and missing input/category checks. | Enda records accepting the fixes and retaining earlier runs. Work is in open PR #1 at the time of this log. | [PR #1](https://github.com/kourousis/cs4928-grp33/pull/1), commit `b5ed310745e5596eebcd2d3dc7a380150993e81e`, its M1 deviation rows and saved reruns; 34 passing tests reported in the PR. |

## Current work - 20 October 2026

| Contribution / influence | Decision / review | Verification |
|---|---|---|
| Codex extracted the predefined JSON IDs 0-11 and drafted their qualitative interpretation for task 6e. | Reviewed by Adam on 20 October: case table and explained examples. Analysis follows the existing sample and top-level finding rule. | [Inspection](evidence/rq2_qualitative/README.md), exact original JSON pointers and raw excerpts; tests reconcile totals with Enda's independent 6d output. |
| Codex selected the top three PMD rule names per entry, retaining cutoff ties, and provided one original example per rule. | Reporting convention chosen on 20 October and disclosed in the inspection. It does not change PMD totals or any locked hypothesis/decision rule. | [Extractor](repro/inspect_rq2_sample.py), [method](evidence/rq2_qualitative/generated/method.json), all-rule and top-rule CSVs; tests cover ties and exact source-pointer resolution. |
| Codex distinguished nested change descriptions from top-level smell labels and limited the interpretation of PMD totals. | Applied in the draft: e.g. IDs 1/7/9/11 are not recounted using nested labels; no code correctness or AI/manual conclusion is inferred. | Original findings in [source_extract.json](evidence/rq2_qualitative/generated/source_extract.json); regression checks for the six nested-label traps. Actual Java behaviour has not been verified. |

## Adam's review - 20 October 2026

Adam reviewed the case table and examples covering mixed changes (ID 1), an
empty delta report (ID 6), and finding-level versus nested change labels
(ID 11). The work is ready for repository submission and group review.

## M2 rerun and freeze - 22 October 2026

James and Claude reran all tests and notebooks on 22 October. From those
results, James and Enda agreed the M2 position below; Claude's output fed into
it but the conclusions are the team's.

- **RQ2, BLOCKED (contingency route).** The PMD and code-smell files cannot be
  matched to participants, so they cannot be split into AI and manual groups.
  We asked the authors for the mapping on 17 Oct (GitHub issue #1) and have had
  no reply. As planned, we ran the two fallbacks instead. First, the raw smell
  counts add up exactly to the paper's Table 8 (18 of 18 rows), which confirms
  the data behind that table. Second, we inspected the first 12 cases by hand.
- **RQ3:** design stage, Week 9.
- **Main threat:** the paper and notebooks say they use Welch's t-test, but the
  code runs Student's t-test. Switching would barely change the p-values (e.g.
  0.237 to 0.235) and no conclusion.

| Contribution / influence | Decision / review | Verification |
|---|---|---|
| Claude reran the full test suite and notebooks and summarised the results. | James and Enda reviewed the output and agreed the RQ2/RQ3/threat position above. | [M2_REPRO.md](M2_REPRO.md) and the saved rerun outputs. |
| Claude suggested freezing the repository state with git tags so the reported results point at a fixed commit. | Accepted by James and Enda. Three tags created: `M1_PLAN` (`618005b`), `M2_REPRO` and `PRE_EVENT_A` (both `38920e8`). | `git tag` / `git show <tag>`; anyone can check out a tag to reproduce the recorded state. |

## RQ3 baseline and design problem - 29 October 2026

| Contribution / influence | Decision / review | Verification |
|---|---|---|
| Claude wrote `repro/rq3_measure.py` (8c) and proposed its duplication measure: runs of 5 logical lines, function copies compared by AST. | Accepted by Enda; logged in the M1_PLAN.md deviation log (29 Oct) before any RQ3 change. | 23 tests on made-up notebooks (`repro/test_rq3_measure.py`). Input hashes match `git show PRE_EVENT_A:<file>` hashed separately. |
| A first, never-committed draft of the script labelled 3 of the 5 copied functions "drifted" because their ASTs differ. Reading the copies showed that only `cliffs_delta` behaves differently (NaN handling); the other two are equivalent rewrites. | The output now says "AST versions", and the behaviour call is made by hand in `RQ3_DESIGN_PROBLEM.md` (8e). | Call sites checked: every current caller passes NaN-free data, so no reported number is affected. |
| Claude drafted `RQ3_DESIGN_PROBLEM.md` (8e), including the case for changing nothing. A second Claude agent then reviewed 8c/8e against the notebooks and data. It found a wrong count (82 → 80 duplicated lines inside functions), wrong NaN reasoning for the `cliffs_delta` callers, causal wording about R1 that the evidence doesn't support, and blind spots in the seed and data-path checks. | All fixed before commit; Enda reviewed the result. | Each claim points to a cell, a run log or a measure output; tests added for the seed and git-ref cases. |

## Adding future entries

For subsequent work, record the date, AI tool, material suggestion, team
decision, reason and supporting source/test/commit evidence. Identify entries
recorded retrospectively and append review outcomes or corrections as needed.
