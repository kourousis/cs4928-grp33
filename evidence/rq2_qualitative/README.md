# Task 6e - RQ2 fallback (b): inspection of JSON IDs 0-11

Prepared 20 October 2026 with Codex assistance for the report inspection and
extraction/checking code. Adam reviewed the case table and examples (IDs 1, 6
and 11) on 20 October. See [AI_LOG.md](../../AI_LOG.md).

## Result and boundary

The 12 selected entries contain **22 top-level CodeScene findings**: 10 introduced,
6 degraded, 5 unchanged, 1 improved and **0 fixed**. There are 17 smell file
records. PMD reports **6,739 violations**, including 2,907 in tests and 3,832 in
production files. No selected entry reports PMD processing/configuration errors
or suppressed violations. ID 6 has an empty CodeScene delta report and is retained.

This is the predefined **group-blind qualitative fallback**, not an AI/manual
comparison, not a new RQ1 result, and not a causal claim. JSON IDs are not participant
IDs. No treatment labels are inferred. PMD totals are final report counts, not
newly introduced violations. The selected cases are a fixed small sample, not
a representative estimate of all 75 entries.

The observed search-method complexity increases and test duplication are useful
descriptions of the reports. They do not establish incorrect behaviour, justify
a particular design pattern, or verify an improvement in maintainability. The
participant Java source and behaviour were not inspected or executed here.

## Method and evidence

The method follows the RQ2 fallback (b) in [M1_PLAN.md](../../M1_PLAN.md), at
base commit `618005be76da818910ec27d85678baea14392a25`:

1. Select JSON **IDs** 0-11 in stable numeric order from
   [task2_cs_delta.json](../../data/task2_cs_delta.json) and
   [task2_pmd.json](../../data/task2_pmd.json). Select by ID, not array position.
2. Inspect every CodeScene file/finding, including test files. Count each
   finding using its own `change-type`; read nested details as context only.
   `fixed` means the paper's `removed`. Retain all categories and unchanged findings.
3. Count PMD violations across every file. For this report, "top rules" means
   the three rule names with the highest counts per entry, retaining ties at
   third place. This reporting convention was chosen on 20 October; it is not
   a new preregistered hypothesis or decision rule. No cutoff tie occurs here.
4. Read the descriptions/locations for each case below. Store exact source
   pointers, full finding details and PMD rule examples for audit.
5. Independently reconcile totals with Enda's task 6d output at commit
   `b5ed310745e5596eebcd2d3dc7a380150993e81e`,
   `repro/rq2_counts/20261017T144903Z/per_entry.csv` (currently in
   [PR #1](https://github.com/kourousis/cs4928-grp33/pull/1)).

All pointers below are zero-based JSON Pointers into `data/task2_cs_delta.json`.
For example, `/1/content/1/findings/0` resolves to a single original finding.
The `file` column in [findings.csv](generated/findings.csv) supplies each full
Java path; the quoted Java line numbers are locations reported by the tool,
not lines in a source tree available in this repository.

## Case-by-case inspection

| ID | Introduced / fixed findings and context from the report | Exact evidence pointer(s) |
|---:|---|---|
| 0 | **Introduced:** Primitive Obsession in `RecipeSearchService.java`; primitive arguments increase from 66.7% to 70.6%. **Fixed:** none. String Heavy Function Arguments remains top-level **unchanged** even though its detail says improved (50.0% to 41.2%). File score falls 7.32 to 7.10. | `/0/content/0/findings/0`; `/0/content/0/findings/1` |
| 1 | **Introduced:** Complex Method in `RecipeAdminController.downloadRecipes` (reported complexity 4, lines 96-114), and one Complex Method finding in `InputParser.java` covering two new methods (complexities 6 and 5). **Fixed:** none at finding level. Search-controller Complex Method is **improved**: `search` drops 17 to 5, while a new helper has complexity 9. Bumpy Road Ahead is **unchanged**, with one nested fixed detail and one nested introduced detail. This is mixed local change, not removal of the whole smell. | `/1/content/0/findings/0`; `/1/content/2/findings/0`; `/1/content/1/findings/0`; `/1/content/1/findings/1` |
| 2 | **Introduced/fixed:** none. `RecipeSearchController.search` Complex Method **degrades**, complexity 14 to 16 (lines 32-82). Bumpy Road Ahead stays **unchanged** at finding level although its detail records nested blocks increasing 3 to 4. | `/2/content/0/findings/0`; `/2/content/0/findings/1` |
| 3 | **Introduced/fixed:** none. `RecipeSearchController.search` Complex Method **degrades**, complexity 15 to 17 (lines 31-88); file score 5.00 to 4.59. | `/3/content/0/findings/0` |
| 4 | **Introduced/fixed:** none. `RecipeSearchController.search` Complex Method **degrades**, complexity 14 to 15 (lines 28-72); file score 5.21 to 5.00. | `/4/content/0/findings/0` |
| 5 | **Introduced/fixed:** none. `RecipeSearchController.search` Complex Method **degrades**, complexity 8 to 10 (lines 25-46); file score 6.89 to 6.30. | `/5/content/0/findings/0` |
| 6 | `content` is an empty array. There are **no reported delta findings** to inspect, including no introduced/fixed finding. This does not prove the implementation is smell-free or unchanged. PMD still reports 527 violations. | `/6/content` |
| 7 | **Introduced:** Missing Arguments Abstractions (average argument count 3.83 to 4.25 across 8 functions) and Primitive Obsession (34.8% to 38.2%) in `RecipeSearchController.java`. **Fixed:** none. Excess Number of Function Arguments is top-level **unchanged**, despite a nested introduced detail for the six-argument `queryAndTimeAndCostPredicate` (lines 94-112). | `/7/content/0/findings/0`; `/7/content/0/findings/1`; `/7/content/0/findings/2` |
| 8 | **Introduced:** four findings: Code Duplication in test `RecipeSearchTest.java` (two similar filter tests, lines 75-114), and Complex Method in `RecipeSearch.perform` (complexity 4), `Money.equals` (4), and `RecipeSearchRequest.equals` (6). **Fixed:** none. Test duplication is included under the locked all-files rule; it is not silently treated as production code. Missing old scores do not mean old scores were zero. | `/8/content/0/findings/0`; `/8/content/1/findings/0`; `/8/content/2/findings/0`; `/8/content/3/findings/0` |
| 9 | **Introduced/fixed:** none at finding level. Code Duplication in test utility `Data.java` is top-level **unchanged**, with a nested degraded detail naming `avoOnToastIngredients` and `burntToastIngredients`. File score remains 9.38. A stable score therefore does not mean every underlying detail stayed identical. | `/9/content/0/findings/0` |
| 10 | **Introduced/fixed:** none. `RecipeSearchController.search` Complex Method **degrades**, complexity 5 to 7 (lines 24-54); file score 6.30 to 5.77. | `/10/content/0/findings/0` |
| 11 | **Introduced:** Code Duplication in `RecipeSearchControllerTest.java`, with seven similar cost-filter tests (locations span lines 145-262). **Fixed:** none. The production Complex Method finding is **degraded**, while its nested detail describes an introduced `matchMaxCostPerServing` method (complexity 6, lines 82-92). Count this as one degraded finding, not an extra introduced finding. | `/11/content/0/findings/0`; `/11/content/1/findings/0` |

## Most frequent PMD rules per entry

These are the same three most frequent rule names for every selected entry
(ID 9 ranks LocalVariableCouldBeFinal second). Their counts cover 3,473 of the
6,739 violations, about 51.5%. This concentration in documentation and `final`
suggestions limits what the raw total alone says about structural design.
It is not a severity-weighted quality measure or adjusted for project size.

| ID | All violations | CommentRequired | MethodArgumentCouldBeFinal | LocalVariableCouldBeFinal |
|---:|---:|---:|---:|---:|
| 0 | 592 | 140 | 92 | 77 |
| 1 | 536 | 130 | 78 | 69 |
| 2 | 510 | 124 | 71 | 64 |
| 3 | 502 | 123 | 71 | 62 |
| 4 | 527 | 126 | 72 | 71 |
| 5 | 523 | 130 | 71 | 67 |
| 6 | 527 | 123 | 77 | 65 |
| 7 | 586 | 132 | 103 | 72 |
| 8 | 693 | 183 | 93 | 75 |
| 9 | 681 | 153 | 87 | 123 |
| 10 | 496 | 124 | 77 | 63 |
| 11 | 566 | 140 | 81 | 64 |

Each rule has an exact original JSON pointer, file, reported line range and
example description in [pmd_top_rules.csv](generated/pmd_top_rules.csv).
For example, ID 0 points to `/0/content/files/0/violations/0` for the missing
class comment, `/0/content/files/0/violations/3` for the `args` parameter that
could be final, and `/0/content/files/1/violations/23` for the local `recipes`
variable that could be final. All rule counts, not only the top three, are in
[pmd_rules.csv](generated/pmd_rules.csv).

## Verification and reproducibility

From the repository root (macOS/Linux: `python3`; Windows: use `python`):

```bash
python3 repro/inspect_rq2_sample.py --check
python3 -m unittest discover -s repro -p test_inspect_rq2_sample.py -v
```

To regenerate the evidence, omit `--check`. No third-party dependencies are
needed. The recorded run used CPython 3.12.14, a disclosed difference from the
Python 3.9 environment for RQ1; this extractor performs only JSON parsing,
integer counting and text export, and does not run the statistical notebooks.

The 12 tests cover sample selection/reordering, duplicate/missing IDs,
finding-level counting, test files, PMD errors/suppression, cutoff ties,
source-pointer resolution, total reconciliation and deterministic exports.
Every selected PMD total, change-type count, net smell count and file-record
count agrees with the saved task 6d run identified above.

Saved evidence:

- [summary.csv](generated/summary.csv): all 12 entries and all change-type counts.
- [findings.csv](generated/findings.csv): all 22 findings, full paths and details.
- [source_extract.json](generated/source_extract.json): unchanged selected
  CodeScene objects and original PMD examples for the top rules.
- [method.json](generated/method.json): selection, counting and reporting rules.
- [inputs_sha256.json](generated/inputs_sha256.json): raw and LF-normalised
  SHA-256 hashes of the inputs and extractor.
- [VALIDATION.md](VALIDATION.md): checks actually executed and results.

This completes the prepared evidence for fallback (b). The team should retain
it even if a validated participant mapping later permits the primary RQ2 test.
The group-level RQ2 answer and the M2 freeze remain separate team tasks.
