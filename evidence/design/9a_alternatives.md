# Task 9a: compare the analysis design alternatives

**Task owner:** Adam Urban. **Decision recorded:** 29 October 2026.
**Status:** B recommended by Adam; team review and implementation verification pending.

## Problem and evidence

The four original notebooks repeat statistical helpers and have run faults.
Function definitions inspected in source snapshot
`c7c49f17cb2a7bc926d5f043ea82444685a51705` include:

| Helper | Notebooks containing a definition |
|---|---|
| `cohens_d`, `bootstrap_ci_mean` | `codehealth`, `perceived_productivity` |
| `cliffs_delta` | `codehealth`, `completion_time`, `coverage` |
| `bootstrap_ci_median`, `bootstrap_ci_median_difference` | `completion_time`, `coverage` |

These repeated names identify candidates for extraction. Implementations and call
sites must be compared before treating them as interchangeable. Source files are
in [frequentist/](../../frequentist/). The [reported runs](../../repro/runs/README.md)
show PP's R1 path and R2 import faults and the unseeded bootstrap limitation.
Enda's [8c/8e baseline and design evidence](../../RQ3_DESIGN_PROBLEM.md) are now
available: 163 of 655 logical lines (24.9%) meet the exact-copy measure, and the
repeated function copies total 105 physical code lines. These are different
measures and must not be added together. The differing `cliffs_delta` versions
handle missing values differently, but current callers remove those values
beforehand, so this has not changed a reported result. The design pressure is
therefore moderate: maintenance risk and repeatability, with an already successful
reproduction supporting the case for A.

## Alternatives

| Consideration | A: keep notebook structure, runner and declared repairs | B: extract a shared tested module |
|---|---|---|
| Work required | Retain the working reproduction route and document its constraints. | Compare helpers, extract compatible operations and update notebook imports/calls. |
| Future maintenance | A correction may need repeating across notebooks. | A shared operation has one implementation and direct tests. |
| Notebook readability | Each notebook contains its own implementation. | Notebooks focus on the analysis; readers follow imports for helper details. |
| Verification cost | Keep existing run evidence and rerun as needed. | Test helpers and compare every before/after RQ1a primary value. |
| Main risk | Duplication and repair dependence remain. | Extraction could silently change formulas, missing-data handling, units or random streams. |
| Proportionate scope | Appropriate if extraction offers insufficient benefit or fails verification. | A small module addresses the observed duplication without replacing the analysis workflow. |

## Decision and rationale

Adam selected **B: extract a shared tested module**. His reason is that fixes
and tests can be maintained centrally, making future maintenance easier and
reducing the risk of inconsistent changes across copies. Acceptance is
conditional on preserving the reproduced results.

Proceed with B only if it satisfies the existing M1 gate. Keep notebooks as the entry points
and extract only genuinely shared operations. Preserve the reproduced statistical
method, including Student's test; switching to Welch is a separate sensitivity
analysis. Resolve path/import faults through consistent loading/imports, rather
than assuming extraction alone fixes them.

Before accepting the implementation:

1. Review Enda's linked 8c/8e baseline and check any released Event A constraints.
2. Test each extracted helper and its important boundaries.
3. Compare every RQ1a primary value before/after at full printed precision.
   Use the same fixed seed in both versions for CI comparisons.
4. Confirm duplicated helpers and R1/R2 faults are removed. If either M1
   condition fails, retain A and report the evidence.

This is a recommendation, not a claim of an implemented or verified refactor.
It follows [M1's RQ3 alternatives and decision rule](../../M1_PLAN.md).
