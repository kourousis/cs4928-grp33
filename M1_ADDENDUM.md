# M1_ADDENDUM — corrections to the frozen M1_PLAN

`M1_PLAN.md` at tag `M1_PLAN` (commit `618005b`) is left exactly as frozen. This file only fills in
blanks and drafting markers that were left in it. **No RQ, sample, method, decision rule or expected
result is changed here.** Written 22 Oct 2026 (Week 7). That is why it only fills
in clerical blanks and changes nothing that could depend on a result.

| # | M1_PLAN.md location | As frozen | Filled in | Source |
|---|---|---|---|---|
| A1 | Timing note, line 9 | "committed and tagged `M1_PLAN` on __ Oct 2026" | 14 Oct 2026, 15:51 (Irish time, UTC+1) | Commit `618005b` date. `M1_PLAN` is a lightweight tag, so it has no separate tag time |
| A2 | RQ1a Method, line 88 | "…then recomputed …" ← *paste the rest of the cell* | Full text is in the workbook cell, which the plan truncated. The part the plan quotes is unchanged. The remainder ("…recomputed independently with a fixed seed", as Enda's 17 Oct deviation row quotes it) is carried out by `repro/recompute_rq1.py` | G33 row, "Method / metric or decision rule" cell, shared Student Tracker (entered Week 5) |
| A3 | RQ1a Expected result, line 170 | "…(Phase 2 was underpowered for …" ← *paste the rest* | Full text is in the workbook cell, which the plan truncated. The decisive part the plan quotes is unchanged: no significant difference on any of the four Phase 2 metrics | G33 row, "Expected result before execution" cell, shared Student Tracker (entered Week 5) |
| A4 | Linkage L1, line 259 | "Raised on __ Oct 2026 by __" | 17 Oct 2026, by Enda: [codescene-research/echoes-of-ai-emse-2025#1](https://github.com/codescene-research/echoes-of-ai-emse-2025/issues/1) | Also recorded on branch `enda/6b-rq1-recompute` (PR #1). As of 22 Oct 2026 the issue is open with no reply from the authors |

A2 and A3 were entered in the workbook in Week 5 and only failed to be copied into the plan in full.
The workbook cells are the authoritative frozen text and were not edited.
