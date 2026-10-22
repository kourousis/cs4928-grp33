# Adam - tasks 5h and 6e

Prepared and checked on **20 October 2026**. Both requested deliverables are
prepared and verified. Adam confirmed review of the case table and explained
examples on 20 October. Publishing, group review and the shared tracker update
are still pending.

| Task | Deliverable | Verification |
|---|---|---|
| **5h: start material AI decision log** | [AI_LOG.md](AI_LOG.md) | Contributions, decisions, supporting evidence and Adam's review are recorded. |
| **6e: inspect JSON IDs 0-11** | [Case-by-case inspection](evidence/rq2_qualitative/README.md) | 12 tests pass; 7 evidence files reproduce; 108 values match Enda's saved 6d run. |

## What the evidence says

- 22 CodeScene findings: 10 introduced, 6 degraded, 5 unchanged, 1 improved,
  **none fixed**. Nested detail labels are not counted as extra findings.
- 6,739 PMD violations. The top three rules in each case concern missing
  comments and variables/arguments that could be `final`.
- This is group-blind report inspection. It supports neither an AI/manual
  comparison nor a claim about Java correctness. It does not set the RQ1 status.

## Review and submit

1. Adam has reviewed the inspection's case table and the explained examples.
   That review is recorded in the AI log. Any subsequent checks or corrections
   should be appended accurately.
2. These checks have passed in the prepared checkout and a fresh clone; they
   can be rerun from the repository root:

   ```bash
   python3 repro/inspect_rq2_sample.py --check
   python3 -m unittest discover -s repro -p test_inspect_rq2_sample.py -v
   ```

3. Publish branch `adam/5h-6e-evidence` and open a PR against `main`.
   This branch adds files only and does not
   depend on Enda's PR being merged.
4. Update your two tracker tasks with links to the published evidence, then
   mark them Done after integration. The tracker has not been changed here.

Suggested tracker notes after publication and review:

- **5h:** `Material AI log added: AI_LOG.md. Historical entries attributed;
  current work and verification recorded. Evidence: <PR/commit link>.`
- **6e:** `IDs 0-11 inspected: evidence/rq2_qualitative/README.md. All 22
  findings, top PMD rules and exact JSON pointers saved. 12 tests pass; 108
  values match 6d. Group-blind only. Evidence: <PR/commit link>.`

## Repository and tracker

Repository write access for `adamurban04` was confirmed on 20 October 2026.
The next integration step is a pull request against `main`, followed by group
review and evidence links in the task tracker. The last attempt to open the
SharePoint tracker required university sign-in; it has not been edited here.

The group is currently in Week 7. M2_REPRO/PRE_EVENT_A and RQ1 notebook evidence
remain team checkpoint work; completing these two tasks alone does not certify
that the entire M2 checkpoint is finished.

Adam claimed task **7a** on 20 October: the results table and deviations summary.
This is his next task, separate from the completed 5h/6e preparation.
