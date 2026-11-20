# Material AI contributions

Started 20 October 2026 for Adam's task **5h**. Record only AI contributions
that affected a method, engineering decision or interpretation. AI output is
not evidence by itself. Keep accepted/modified/rejected decisions and link the
checks that support them. No full prompt transcripts are required by the brief.

## AI tools used

- **Adam:** Codex.
- **Enda, Ilias and James:** Claude, for research, analysis scripts and verification.

## Earlier contributions, recorded retrospectively

Earlier contributions were summarised on 20 October from M1_PLAN.md and PR #1.
Dates below identify when the documented work took place.

| Documented date | Material AI contribution | Decision/status recorded by the project | Evidence and verification record |
|---|---|---|---|
| 14 Oct 2026 | Claude assisted with formatting M1 from team workbook entries and documenting the team's RQ1b/RQ2/RQ3 expectations. | M1 records team adoption, including D1/D2/D3, and the timing of rules/expectations relative to pilot outputs. | [M1_PLAN.md](M1_PLAN.md), timing note, expected-result sections and deviation log. |
| 14 Oct 2026 | Claude wrote the notebook runner and identified path/import failures R1/R2, the Welch/Student t-test mismatch, and JSON linkage limitations during analysis. | Team accepted the runner and specified applying only the two declared in-memory repairs, with as-shipped failures retained first. | [Runner](repro/run_all.py), [run instructions](repro/README.md), M1 method and audit findings. |
| 14 Oct 2026 | Two AI code-review passes flagged stale notebook outputs surviving a failed run, plus rounding/rule gaps. | Team decided to update the runner to clear outputs and clarified the rules in M1. | M1 "AI use" and timing note; runner clears stored outputs before execution. |
| 16-17 Oct 2026 | Claude assisted with implementing Enda's statistical/counting scripts; an AI review pass flagged a shared bootstrap-stream dependency and missing input/category checks. | Enda accepted the fixes and retained earlier runs. The work was merged through PR #1 (merge commit `8c3b4ee`). | [PR #1](https://github.com/kourousis/cs4928-grp33/pull/1), commit `b5ed310745e5596eebcd2d3dc7a380150993e81e`, its M1 deviation rows and saved reruns; 34 passing tests reported in the PR. |

## Current work - 20 October 2026

| Contribution / influence | Decision / review | Verification |
|---|---|---|
| Codex extracted the predefined JSON IDs 0-11 and assisted with drafting qualitative descriptions for task 6e. | Reviewed by Adam on 20 October: case table and explained examples. Analysis follows the team's existing sample and top-level finding rule. | [Inspection](evidence/rq2_qualitative/README.md), exact original JSON pointers and raw excerpts; tests reconcile totals with Enda's independent 6d output. |
| Codex implemented the extraction of the top three PMD rule names per entry (retaining cutoff ties) and pulled one original example per rule per the team's reporting format. | Reporting convention chosen by the team on 20 October and disclosed in the inspection. It does not change PMD totals or any locked hypothesis/decision rule. | [Extractor](repro/inspect_rq2_sample.py), [method](evidence/rq2_qualitative/generated/method.json), all-rule and top-rule CSVs; tests cover ties and exact source-pointer resolution. |
| Codex implemented checks separating nested change descriptions from top-level smell labels according to the team's bounded interpretation rules. | Applied in the inspection: e.g. IDs 1/7/9/11 are not recounted using nested labels; no code correctness or AI/manual conclusion is inferred. | Original findings in [source_extract.json](evidence/rq2_qualitative/generated/source_extract.json); regression checks for the six nested-label traps. Actual Java behaviour has not been verified. |

## Adam's review - 20 October 2026

Adam reviewed the case table and examples covering mixed changes (ID 1), an
empty delta report (ID 6), and finding-level versus nested change labels
(ID 11), and approved the work for the repository.

## M2 rerun and freeze - 22 October 2026

James and Claude reran all tests and notebooks on 22 October. From those
results, James and Enda agreed the M2 position below; Claude assisted with running
the scripts, while all conclusions are the team's.

- **RQ2, BLOCKED (contingency route).** The PMD and code-smell files cannot be
  matched to participants, so they cannot be split into AI and manual groups.
  We asked the authors for the mapping on 17 Oct (GitHub issue #1) and received
  no reply. As planned, we ran the two fallbacks instead. First, the raw smell
  counts add up exactly to the paper's Table 8 (18 of 18 rows), which confirms
  the data behind that table. Second, we inspected the first 12 cases by hand.
- **RQ3:** addressed in Week 9 (see below).
- **Main threat:** the paper and notebooks say they use Welch's t-test, but the
  code runs Student's t-test. Switching would barely change the p-values (e.g.
  0.237 to 0.235) and no conclusion.

| Contribution / influence | Decision / review | Verification |
|---|---|---|
| Claude assisted with rerunning the full test suite and notebooks and compiling the raw outputs. | James and Enda reviewed the output and agreed the RQ2/RQ3/threat position above. | [M2_REPRO.md](M2_REPRO.md) and the saved rerun outputs. |
| Following the team's plan to freeze the repository state at fixed commits, Claude generated the git tag commands. | Executed and verified by James and Enda. Three tags created: `M1_PLAN` (`618005b`), `M2_REPRO` and `PRE_EVENT_A` (both `38920e8`). | `git tag` / `git show <tag>`; anyone can check out a tag to reproduce the recorded state. |

## RQ3 baseline and design problem - 29 October 2026

| Contribution / influence | Decision / review | Verification |
|---|---|---|
| Following Enda's specification for measuring duplication (runs of 5 logical lines and AST-based function comparison), Claude helped implement `repro/rq3_measure.py` (8c). | Reviewed and accepted by Enda; logged in the M1_PLAN.md deviation log (29 Oct) before any RQ3 change. | 23 tests on made-up notebooks (`repro/test_rq3_measure.py`). Input hashes match `git show PRE_EVENT_A:<file>` hashed separately. |
| An early draft of the script labelled 3 of the 5 copied functions "drifted" because their ASTs differed. Manual inspection showed that only `cliffs_delta` behaves differently (NaN handling); the other two are equivalent rewrites. | Team updated the label to "AST versions", and the behaviour call was made by hand in `RQ3_DESIGN_PROBLEM.md` (8e). | Call sites checked: every current caller passes NaN-free data, so no reported number is affected. |
| Claude assisted with drafting `RQ3_DESIGN_PROBLEM.md` (8e) based on the team's baseline analysis. A second Claude verification pass checked 8c/8e against the notebooks and data, catching a line count error (82 → 80 duplicated lines), imprecise NaN notes for `cliffs_delta`, overstated causal wording about R1, and edge cases in seed/data-path checks. | All fixes applied and reviewed by Enda before commit. | Each claim points to a cell, a run log or a measure output; tests added for the seed and git-ref cases. |

## Event A plan - 29 October 2026

| Contribution / influence | Decision / review | Verification |
|---|---|---|
| Following the team's design for held-out validation (IDs 12–23 and prediction thresholds P1–P4), Claude helped draft `EVENT_A_PLAN.md` (8a). | Reviewed and accepted by Enda on 29 Oct, before any held-out entry was opened. Frozen with the tag `EVENT_A_PLAN`. | The M2 values in the plan trace to `evidence/rq2_qualitative/` (README, `generated/findings.csv`, `generated/pmd_top_rules.csv`). The plan was tagged before the held-out run on 30 Oct. |
| A second Claude review pass checked the plan before tagging and caught that editing the 6e script directly would break its self-hash `--check`, along with ordering/disclosure details in the draft text (tracker prediction scheduled too late, understated 6d disclosure, and ID 11's finding mischaracterised). | Based on that catch, the team kept the 6e script unchanged and used a wrapper to call it, moving the tracker prediction to step 0 before tagging. | Verified against `repro/inspect_rq2_sample.py` and the 6e evidence (IDs 0–11 only). |

## Task 7a summary - 29 October 2026

Codex assisted with formatting the [7a summary](evidence/week7/7a_results_review.md)
and verifying its four rounded p-values and effect sizes against the saved outputs.

## Task 9a alternatives - 29 October 2026

Codex assisted with formatting the [alternatives comparison](evidence/design/9a_alternatives.md).
Adam selected Option B for central maintenance of fixes and tests, conditional on
preserving results; verification requirements follow M1's existing RQ3 rule.

## Event A run - 30 October 2026

| Contribution / influence | Decision / review | Verification |
|---|---|---|
| Claude helped implement `repro/run_event_a.py` (wrapper calling the frozen 6e `inspect()` per ID) and `repro/score_event_a.py` (P1–P4 scoring per `EVENT_A_PLAN.md`, plus 6d reconciliation), executed the run on IDs 12–23, and assisted with drafting `evidence/event_a/README.md`. | Reviewed by Ilias before commit. Two small implementation deviations from the plan disclosed in the README (Python version printed, not stored; one call per ID). | `inspect_rq2_sample.py --check` still passes; Event A evidence and scores reproduce with `--check`; totals agree with 6d `per_entry.csv` for all 12 IDs. |
| Claude helped extract and group details for the 13 `fixed` findings (relocation in ID 13, threshold swaps in IDs 18/22, concentration in ID 17) for the team's post-hoc review. | Team reported these notes separately from the mechanical P1 result, which is unchanged. | Each note points to the JSON finding; P1 fails under every reading. |

## Week 9: shared stats module (9b/9c) - 5 November 2026

| Contribution / influence | Decision / review | Verification |
|---|---|---|
| Implementing Adam's design decision to extract a shared module, Claude helped write `frequentist/stats.py` (consolidating the helpers from the four notebooks), refactored the notebooks to import it, and wrote unit tests (`repro/test_stats.py`). It also implemented the team's declared fixes for R1/R2 and added a fixed seed for reproducibility. | The architectural decision to use a shared, tested module was Adam's (task 9a, above), on the condition that results did not change. James committed the change and merged it as PR #8 on 5 Nov (`227d6df`, merge `6ed2782`, tagged `PRE_EVENT_B`). | All 94 tests pass at the change commit `227d6df` (re-run on 20 Nov). The module's behaviour is covered by hand-worked cases in `repro/test_stats.py`. |
| Claude helped implement `repro/rq3_verify.py` to run the four notebooks before (at `PRE_EVENT_A`, with only the declared repairs and the seed) and after, comparing every printed line and re-running the 8c duplication script. | The write-up records that the result meets both criteria of the team's RQ3 decision rule from M1_PLAN.md, and James merged it. The seed and the change to `run_all.py` and `rq1_status.py` (which now read the original notebooks from git) were added to the M1_PLAN.md deviation log on 5 Nov. | The saved run [`20261105T185759Z`](repro/rq3_verify/20261105T185759Z/report.txt) shows all four notebooks printing identical results (all 16 primary values and all 16 CI bounds). Copied helper functions fell from 5 (105 lines) to 0, and the share of duplicated lines from 24.9% to 10.8% in the measure from 8c. Written up in [9b_9c_shared_module.md](evidence/design/9b_9c_shared_module.md). |
| The copies of `cliffs_delta` in the notebooks had drifted apart; the team standardised the shared version to drop missing values first. | Confirmed by the team, as every current caller already removed missing values before calling it. | Checked in the 9b/9c write-up and by the before/after run: no reported number changed. |

## Change Event B - 10 November 2026

| Contribution / influence | Decision / review | Verification |
|---|---|---|
| Following the team's design for Event B (testing a fifth outcome `test_runs`, predictions P1–P5, and selecting option A, no extra structural change, prior to execution), Claude assisted with drafting `EVENT_B_PLAN.md`. | James committed the team's plan on 10 Nov before either variant was built or run (`e9caa20`, tag `EVENT_B_PLAN`). | The tag points at a commit that holds only the plan. The plan states that `PRE_EVENT_B` was created on 10 Nov on the existing 5 Nov merge commit. |
| Claude helped implement `repro/event_b.py` to generate the new notebook in both variants (original structure and shared module) with identical edits, run the measurements, score P1–P5 per the plan, and draft `evidence/event_b/README.md`. | James committed the result on 10 Nov (`c017e7f`, tag `EVENT_B`). The verdict follows the team's pre-registered rule: P1, P2 and P5 held, supporting the Week 9 design decision. | Full run saved in [`20261110T174012Z`](evidence/event_b/generated/20261110T174012Z/report.txt). Both versions print the same numbers (26 of 26 lines). The four existing notebooks, `stats.py` and its tests are unchanged since `PRE_EVENT_B`, and all 94 tests still pass. |
| Two of the team's pre-registered predictions in the plan turned out wrong: that the shared-module version would need fewer edits (P3), and that duplicated lines outside functions would be similar in both versions (P4). | Both failures are reported as they came out, not rewritten, and recorded by the team as trade-off evidence outside the main verdict. | P3 and P4 are marked FAILS in the report and the Event B README: nine edits in both versions, and 39 against 23 new duplicated lines. |

## Final README and Event B fix - 19 November 2026

| Contribution / influence | Decision / review | Verification |
|---|---|---|
| Adam rewrote the README for the final submission and changed `repro/event_b.py` so that a failed or invalid run stops with a clear error instead of carrying on with a missing p-value. He also added `repro/test_event_b.py`. Recorded here for traceability, as this change touched Event B code after the `EVENT_B` tag. | Adam committed it on 19 Nov (`b166ddf`) and James merged it as PR #9 (`fec4e6d`). | Five new tests cover the failure cases (missing or invalid p-value, a failed notebook, valid edge values, and replay of the saved good run). All 99 tests pass at `fec4e6d` (94 before this commit). Every file link in the README resolves to a file in the repository, and every tag it names exists. |

## Sign-off - 20 November 2026

- A team member signed off every AI-assisted implementation or verification check in this log before it went into the repository (including fixes from the 14 Oct, 17 Oct and 29 Oct review passes). Everything was committed by a team member. AI output was never treated as evidence by itself: each result above is backed by a test, a saved run or a tag.
- The rows for 5-19 November were compiled with Claude's assistance from the git history, tags and tests, then checked by James against the repository.
- The submitted state is the tag `FINAL`, on the commit that adds this version of the log (after PR #9).
