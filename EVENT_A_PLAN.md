# Event A plan — recorded before execution (task 8a)

> Recorded 29 Oct 2026, **before** any held-out entry was opened, and frozen with the tag
> `EVENT_A_PLAN`. After the tag, the prediction and the method don't change. Any later improvement is
> reported separately from the first result.

- **Brief:** `P32_Event_A_STUDENT.docx` (course handout, not in the repo), received 29 Oct 2026. In short:
  assess code variants not inspected at M2, with condition labels hidden, using our frozen M2 criteria.
  Reveal the labels only after the assessment is recorded.
- **Pre-event state:**
  - Tag `PRE_EVENT_A` (`38920e8`). The M2 result and evidence are in our Student Tracker row (cols I–J).
  - This plan is committed on branch `enda/8a-event-a-plan`, branched from `main` at `115e819`. That is
    after PR #6 (the RQ3 baseline, tasks 8c and 8e), which used no Event A material. The branch is merged
    with a merge commit, so the tagged commit stays on `main`.

## 1. Held-out material

- **Which entries:** JSON **IDs 12–23** in `data/task2_cs_delta.json` and `data/task2_pmd.json`, selected
  by ID in numeric order, not by array position.
  - These are Phase 2 (Task 2, recipe-finder) submissions, one snapshot per entry, with no time window.
  - Artefact `codescene-research/echoes-of-ai-emse-2025` @ `472ebca6d20af5d6de4264897ba98220ce521fd0`.
  - Data sha256 (the same as at 6e): `task2_cs_delta.json`
    `019bb13aaa8614981e3f02019b82f6583941361cb5d688a40b20d1ea86d89ef1` and `task2_pmd.json`
    `9c3e07d4ba80bc593e532835ad9147772276145a479f47a84ec378d82ede0531`. The Event A run must record
    matching hashes.
- **What a "code variant" is here:** the package has no participant Java source. As at M2, each variant
  is assessed through its tool reports (CodeScene delta findings and PMD violations). This is the 6e
  boundary: "tool-report inspection, not inspection of participant Java source".
- **Why these IDs:** they are the next 12 in the same stable order as M2's IDs 0–11, following the
  pack's rule (first eligible items in stable order). They were chosen before looking at their content,
  and they are in the same files and format, so the M2 method applies unchanged.
- **No exclusions.** All 12 are kept whatever they contain; at M2, ID 6 had an empty report and was kept.
- **Disclosure:**
  - On 17 Oct, 6d wrote per-entry counts for all 75 IDs: PMD totals, and top-level findings by change
    type and by category. They are in `repro/rq2_counts/20261017T144903Z/per_entry.csv` and
    `per_entry_findings.csv`, and in the earlier run `repro/rq2_counts/20261017T143341Z/per_entry.csv`.
  - P1 and P2 could in principle be read off those rows, and P3 in part.
  - The thresholds below were set only from the 6e evidence for IDs 0–11. Rows 12–23 of those files were
    not used for this plan, and 6e read only IDs 0–11 case by case.

## 2. Frozen method (unchanged from M2 task 6e)

- **The rule:** the coding rule in `evidence/rq2_qualitative/README.md`, Method steps 1–4:
  - count each top-level CodeScene finding by its own `change-type`, with nested details as context only;
  - `fixed` = the paper's `removed`;
  - every file is counted, including tests;
  - list the 3 most frequent PMD rule names per entry, keeping ties at third place.
- **6e step 5 is applied too:** after execution, the totals for IDs 12–23 are reconciled with rows 12–23
  of the 6d `per_entry.csv`, as 6e did for IDs 0–11.
- **No change to the 6e script.** A new wrapper, `repro/run_event_a.py`, imports `inspect()` from
  `repro/inspect_rq2_sample.py` unchanged and calls it with `sample_ids = 12–23`.
  - It writes only to `evidence/event_a/generated/`, never to the M2 evidence folder.
  - It also writes a `method.json` that records `sample_ids` 12–23, the input hashes and the Python
    version.
  - `python repro/inspect_rq2_sample.py --check` must still pass byte for byte. That shows the frozen
    method and the M2 evidence didn't change.
- **If the frozen code stops on an entry:** `inspect()` raises on PMD processing, configuration or
  suppressed errors, on a PMD version other than 7.13.0, and on an unknown change type. If it stops, we
  record the error as that entry's result and don't edit the check. The entry stays in the 12, adds no
  findings to P1/P2, and counts as not meeting P3 and P4.
- **Blind by construction:** the package doesn't link JSON IDs to participants (M1_PLAN.md § Linkage), so
  the assessment can't see the labels. We will not try to infer labels (for example from entry order or
  dates).
- **Reveal:** only with an `id` → participant mapping that passes the L2 Table 8 check (M1_PLAN.md §
  Linkage). As of 29 Oct the authors haven't replied to our L1 request on the artefact repo. Unless that
  changes, the reveal is recorded as **BLOCKED (linkage)**, the same infrastructure limitation as RQ2.
- **Who and where:** Enda runs it (task 8b). The case-by-case table, in the 6e format, goes in
  `evidence/event_a/README.md`.

## 3. The M2 result being tested (6e, IDs 0–11)

- **Findings:** 22 top-level findings: 10 introduced, 6 degraded, 5 unchanged, 1 improved, **0 fixed**.
  No smell was removed at top level (ID 1 has one nested `fixed` detail).
- **Complex Method on `RecipeSearchController.java`:** degraded in 6 of 12 (IDs 2, 3, 4, 5, 10, 11) and
  improved in 1 (ID 1).
  - In IDs 2, 3, 4, 5 and 10 the detail is `search` gaining complexity.
  - In ID 11 it is a new method, `matchMaxCostPerServing`.
  - Changes kept adding complexity to the same controller.
- **PMD:** the same 3 rules are in the top 3 of all 12 entries (`CommentRequired`,
  `MethodArgumentCouldBeFinal`, `LocalVariableCouldBeFinal`; ID 9 orders them differently). Together they
  are about 51.5% of all violations (3,473 of 6,739), which limits what the raw PMD total alone says
  about structural design.

## 4. Prediction

**The M2 pattern transfers to IDs 12–23.** Each count is over the 12 entries together, scored
mechanically from the Event A run's `findings.csv` and `pmd_top_rules.csv`, which have the same format
as 6e's. Proposed by Claude, accepted by Enda, 29 Oct 2026.

| # | Prediction (holds if…) | M2 value (IDs 0–11) |
|---|---|---|
| P1 | At most 1 top-level finding has `change_type` `fixed` | 0 |
| P2 | `introduced` + `degraded` are at least half of all top-level findings. If there are no top-level findings at all, P2 fails | 16 of 22 (73%) |
| P3 | At least 4 of the 12 entries have a row in `findings.csv` where `category` is `Complex Method`, the file's basename is exactly `RecipeSearchController.java`, and `change_type` is `introduced` or `degraded`. An entry counts once | 6 of 12 (IDs 2, 3, 4, 5, 10, 11) |
| P4 | In at least 10 of the 12 entries, `CommentRequired`, `MethodArgumentCouldBeFinal` and `LocalVariableCouldBeFinal` are all among the rule names listed for that ID in `pmd_top_rules.csv` (ties at third kept; order doesn't matter). An entry with no PMD violations doesn't meet P4 | 12 of 12 |

- **What would challenge M2:** P1 or P4 failing, that is, at least 2 fixed findings, or 3 or more
  entries whose top-3 PMD rules don't include all three of those rules. Either would mean the 6e
  description doesn't hold beyond IDs 0–11. That description is that no top-level smell was removed and
  the same three documentation/`final` rules lead every entry's PMD counts. P2 or P3 failing alone
  weakens it without overturning it.
- **What Event A can't change:** the M2 RQ2 answer (INCONCLUSIVE/BLOCKED) can't be overturned by blind
  data. Event A tests the 6e description.
- **About labels:** not scored. About 6 entries per group is too few for a test. If a validated mapping
  ever arrives, we report the P1–P4 quantities per group, descriptively.

## 5. Order of work

0. **Before running anything,** enter in our Student Tracker row, col K ("Event A prediction before
   execution"): the held-out set (IDs 12–23), P1–P4, the challenge rule and a link to the tag
   `EVENT_A_PLAN`.
1. Run `repro/run_event_a.py` on IDs 12–23 and write the case-by-case table in
   `evidence/event_a/README.md`. Commit both before any reveal attempt.
2. Score P1–P4 exactly as written, and reconcile the totals with 6d (section 2). If we later change the
   method, report that separately from this first result.
3. Compare with M2: what transfers, what doesn't, and the strongest evidence for each.
4. Name one design/maintainability implication using module concepts. No pattern unless the evidence
   justifies it.
5. Fill col L ("Event A result / decision") with links to the commit, tag and evidence.
