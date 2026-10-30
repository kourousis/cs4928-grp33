# Event A — result (task 8b)

Run on 30 Oct 2026, following `EVENT_A_PLAN.md` at tag `EVENT_A_PLAN` (prediction frozen 29 Oct, before
any held-out entry was opened). Executed with Claude (AI-assisted); see `AI_LOG.md`. Labels stay hidden:
the authors have not answered L1, so the reveal is **BLOCKED (linkage)**, as the plan anticipated.

**Headline:** P2, P3 and P4 hold; **P1 fails (13 top-level `fixed` findings, against a limit of 1)**. Under the
plan's challenge rule, the M2/6e description "no top-level smell was removed" **does not transfer** to
IDs 12–23. The other three parts of the description (changes add more smells than they remove, complexity
keeps accumulating in `RecipeSearchController`, and PMD is dominated by the same three documentation/`final`
rules) do transfer.

## Evidence and re-run

| What | Where |
|---|---|
| Wrapper (calls the frozen 6e `inspect()` unchanged, one ID at a time) | `repro/run_event_a.py` |
| Generated evidence (same format as 6e, plus `errors.csv`) | `evidence/event_a/generated/` |
| Mechanical scoring of P1–P4 and the 6d reconciliation | `repro/score_event_a.py` → `generated/scores.json` |

```bash
python3 repro/inspect_rq2_sample.py --check   # M2 evidence and the frozen method unchanged (PASS)
python3 repro/run_event_a.py --check          # Event A evidence reproduces byte for byte (PASS)
python3 repro/score_event_a.py --check        # scores reproduce (PASS)
python3 -m unittest discover -s repro -p "test_inspect*.py"   # 12 tests, OK
```

- **Inputs:** `task2_cs_delta.json` and `task2_pmd.json` hashes match the ones frozen in the plan (the
  wrapper stops if they don't); full hashes in `generated/inputs_sha256.json`.
- **Errors:** none. `inspect()` raised on no entry, so all 12 are scored (`generated/errors.csv` is empty).
- **Reconciliation with 6d (6e step 5):** every PMD total, change-type count, net smell change and file-record
  count for IDs 12–23 equals `repro/rq2_counts/20261017T144903Z/per_entry.csv` (`scores.json` →
  `reconciliation_6d.agrees = true`).

## Scoring (exactly as written in the plan)

| # | Rule | Event A (IDs 12–23) | M2 (IDs 0–11) | Holds? |
|---|---|---|---|---|
| P1 | ≤ 1 top-level `fixed` | **13** (in 6 entries: 13×2, 14, 16, 17×7, 18, 22) | 0 | **No** |
| P2 | introduced + degraded ≥ half of top-level findings | 19 of 38 (50.0%) | 16 of 22 (73%) | Yes (exactly at the line) |
| P3 | ≥ 4 entries: Complex Method on `RecipeSearchController.java`, introduced/degraded | 4 (IDs 15, 16, 20, 21) | 6 | Yes (exactly at the line) |
| P4 | ≥ 10 entries with all three rules in their top rules | 12 | 12 | Yes |

Totals: 38 top-level findings — 13 introduced, 6 degraded, 6 unchanged, 0 improved, 13 fixed. PMD:
6,297 violations (3,660 production, 2,637 test).

**Challenge rule → M2 description challenged** (P1 fails). P2 and P3 hold only at their thresholds, so the
"mostly worse" and "controller hotspot" parts transfer, but more weakly than at M2.

## Case-by-case inspection

Pointers are zero-based JSON Pointers into `data/task2_cs_delta.json`. Full details: `generated/findings.csv`.

| ID | Introduced / fixed findings and context | Pointer(s) |
|---:|---|---|
| 12 | Nothing introduced or fixed. One String Heavy Function Arguments finding, top-level **unchanged** (detail: 50% → 40%), on a file record with **no name**. | `/12/content/0/findings/0` |
| 13 | **Introduced:** Complex Method (9) and Bumpy Road Ahead (3 blocks) for `matches` in new-looking `ComparisonFilterMethods.java`. **Fixed:** the same two smells for `matches` in `RecipeSearchController.java`, with the same values (9, 3). The method was **moved**, not simplified; the controller's score goes 6.49 → 10.0. | `/13/content/0/findings/0–1`; `/13/content/1/findings/0–1` |
| 14 | **Introduced:** Complex Conditional in `Recipe.getCostPerServing`; Complex Method in `Recipe.java` **degrades**. **Fixed:** String Heavy Function Arguments in `RecipeSearchController.java`. | `/14/content/0/findings/0–1`; `/14/content/1/findings/0` |
| 15 | **Introduced:** Complex Conditional, Bumpy Road Ahead and Primitive Obsession in `RecipeSearchController.java`. Complex Method **degrades** (`matchesSearchCriteria` 9 → 12). Score 6.59 → 5.52. | `/15/content/0/findings/0–3` |
| 16 | **Introduced:** Complex Method in `RecipeSearchController.filteredRecipes` (4, exactly at threshold). **Fixed:** String Heavy Function Arguments in `RecipeFilter.java`; Primitive Obsession there stays unchanged. | `/16/content/1/findings/0`; `/16/content/0/findings/1` |
| 17 | **7 of the 13 fixed findings.** `RecipeServiceImpl.java` goes 5.36 → 10.0 with all five smells fixed (Code Duplication, Complex Method for `matchesQuery` and `searchRecipes`, Complex Conditional, Primitive Obsession, String Heavy); test file `CountTestRuns.java` loses its Complex Method; test duplication fixed. **Introduced:** Excess Number of Function Arguments (`searchRecipes`, 5 args) in `RecipeServiceImplTest.java`. A `SearchCriteria.java` file appears in this entry's PMD report; whether it is new in Phase 2 can't be told from the package. | `/17/content/2/findings/0–4`; `/17/content/1/findings/0`; `/17/content/0/findings/0–1` |
| 18 | **Introduced:** Primitive Obsession; **fixed:** String Heavy Function Arguments — both in `RecipeSearchService.java`, whose score stays 7.0. | `/18/content/0/findings/0–1` |
| 19 | Nothing introduced or fixed. `RecipeServiceImpl.searchRecipes` Complex Method (5 → 7) and Complex Conditional **degrade**; test duplication top-level unchanged with a nested introduced detail. | `/19/content/1/findings/0–1`; `/19/content/0/findings/0` |
| 20 | **Introduced:** Complex Conditional and String Heavy Function Arguments in `RecipeSearchController.java`. Complex Method **degrades** even though its detail says `search` is fixed: complexity moved into new `getActiveFilterText` (9) and `containsSearchTerm` (6). Score 6.89 → 4.93. | `/20/content/0/findings/0–2` |
| 21 | Nothing introduced or fixed. `RecipeSearchController.search` Complex Method **degrades** 4 → 5. | `/21/content/0/findings/0` |
| 22 | **Introduced:** Primitive Obsession; **fixed:** String Heavy Function Arguments — both in `RecipeSearchController.java`, score unchanged at 7.32. | `/22/content/0/findings/0–1` |
| 23 | **Introduced:** Primitive Obsession in `Recipe.java`. Complex Method top-level unchanged (detail: `matchQuery` 12 → 10). | `/23/content/0/findings/0–1` |

**Top PMD rules:** in all 12 entries the top three are `CommentRequired`, `MethodArgumentCouldBeFinal`,
`LocalVariableCouldBeFinal`, in that order (`generated/pmd_top_rules.csv`).

## What transfers and what doesn't

| M2 description (6e) | Event A | Strongest evidence |
|---|---|---|
| No top-level smell removed | **Does not transfer.** 13 fixed, in 6 of 12 entries | ID 17 (`/17/content/2`), ID 13 (`/13/content/1`) |
| Changes add more smells than they remove | Transfers, weakly (50% vs 73%) | P2 |
| Complexity accumulates in `RecipeSearchController` | Transfers (4 entries, plus ID 13's controller still held `matches` before the move) | IDs 15, 20 |
| Same three PMD rules dominate | Transfers fully (12/12) | `generated/pmd_top_rules.csv` |

## Post-hoc reading of P1 (reported separately; does not change the result above)

The plan scores P1 on raw counts, and that result stands. Reading the 13 fixed findings case by case:

- **2 are relocations** (ID 13): the same smell with the same values is fixed in one file and introduced in another.
- **2 are threshold swaps** (IDs 18, 22): String Heavy fixed and Primitive Obsession introduced in the same file,
  with the file score unchanged.
- **7 come from one entry** (ID 17).

Even after removing the relocations and swaps, 9 remain; even after also removing ID 17, 2 remain. Either way
P1 still fails (≥ 2), so the challenge to M2 does not depend on these readings. What it does show is that
**a top-level `fixed` count is not on its own evidence that a smell was removed from the design**: CodeScene's
deltas are per file, so moving a method counts as one fix plus one introduction. Our M-SMELL measure
(fixed + improved − introduced − degraded) nets relocations to 0 (ID 13 net = 0), which supports keeping net
change, not the fixed count, as the RQ2 measure.

## Design implication (module concepts)

The recurring pressure is the **controller's search/filter method**: in M2 and again here, each new filter
was added to `RecipeSearchController` (low cohesion, a growing conditional over filter types), so the class
is a change hotspot. The entries that *reduced* that pressure did it by moving filter logic out (ID 13
`ComparisonFilterMethods`, ID 16 `RecipeFilter`, ID 17 cleaning up `RecipeServiceImpl`), but ID 13 shows that
moving the method without decomposing it only relocates the complexity. We don't claim a pattern (for
example Strategy/Specification per filter) from tool reports alone: there is no participant source in the
package, and the evidence supports "extract and decompose the filtering responsibility", not a specific pattern.

**For our own RQ3 (notebooks):** Event A does not change the RQ3 decision rule or alternatives. It does
support the reuse-over-copy direction in practice: Event A needed a second sample, and reusing the frozen
`inspect()` through a wrapper (instead of copying the 6e script) is what let `--check` prove the method
was unchanged.

## Deviations from EVENT_A_PLAN.md

1. **Run by Claude with Ilias, not by Enda** (task 8b was unassigned on the task list).
2. **Python version is printed, not stored in `method.json`.** Storing it would make the evidence files
   depend on the interpreter, breaking the byte-for-byte `--check` that 6e also relies on (6e prints it
   too). Run used CPython 3.13.18; the extractor is stdlib-only JSON counting.
3. **`inspect()` is called once per ID** so that an error on one entry can be recorded without losing the
   rest, as section 2 of the plan requires. The function itself is unchanged; no entry errored, so a
   single call would have given identical rows.
4. **Order of work step 0** (prediction in Student Tracker col K before running) must be confirmed by the
   team; if col K was filled after this run, record that.
