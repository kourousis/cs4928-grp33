# CS4928 G33 / P32: Echoes of AI reproduction and analysis refactoring

Our group checks a bounded part of Borg et al.'s *Echoes of AI* study using its published data and Python analysis. We then refactor the analysis code and test how it handles a further requirement.

The study's Phase 2 developers worked without AI. Treatment means they inherited code previously developed with AI assistance; control means they inherited manually developed code.

## Questions and results

| Question | Result | Evidence |
|---|---|---|
| RQ1a: can we reproduce the four Phase 2 comparisons? | All four reproduce at the paper's reported precision, after the declared productivity-notebook repairs. None shows a statistically significant group difference at 0.05. | [M2 record](M2_REPRO.md), [run history and values](repro/runs/README.md) |
| RQ1b: can we audit the project-level CodeHealth calculation? | Not auditable from the package: per-file size weights and report-to-participant links are missing. | [CodeHealth audit](repro/rq1b_codehealth/20261017T144901Z/summary.txt) |
| RQ2: do PMD warnings and smell changes show the same group pattern? | Group comparison blocked by missing participant links. Both fallbacks are complete: all 18 printed pooled Table 8 counts match, and report IDs 0-11 were inspected without group labels. | [Table 8 counts](repro/rq2_counts/20261017T144903Z/table8_check.csv), [twelve-case inspection](evidence/rq2_qualitative/README.md) |
| RQ3: is a shared, tested analysis module justified over keeping the original structure? | Adopted: before/after printed results match with the same seed, repeated helper definitions are removed, and measured duplication falls from 24.9% to 10.8%. | [Alternatives](evidence/design/9a_alternatives.md), [implementation and verification](evidence/design/9b_9c_shared_module.md) |

The reproduced Phase 2 values are:

| Measure | Treatment | Control | p-value |
|---|---:|---:|---:|
| Median completion time | 136 minutes | 173 minutes | 0.56 |
| Mean perceived productivity | 3.95 | 4.06 | 0.37 |
| Mean CodeHealth | 8.49 | 8.44 | 0.24 |
| Median test coverage | 0.70 | 0.70 | 0.49 |

The sample is 75 participants (40 treatment, 35 control); time and productivity use 39 and 33 usable values. Non-significant results do not establish equivalence. The [plan](M1_PLAN.md), [addendum](M1_ADDENDUM.md) and deviation log explain the method, timing and limitations.

## Change Events

- **Event A:** the next twelve reports, IDs 12-23, challenge the first sample's description. There are 13 findings marked fixed against a prediction of at most one; P2-P4 hold. Group-label reveal remains blocked. See the [saved plan](EVENT_A_PLAN.md), [case report](evidence/event_a/README.md) and [scores](evidence/event_a/generated/scores.json).
- **Event B:** adding a `test_runs` analysis takes nine cell edits in both designs. The original design copies three helpers; the shared-module design copies none and gives identical printed results. P1, P2 and P5 hold, supporting the design decision under the saved rule; P3 and P4 fail. See the [plan](EVENT_B_PLAN.md), [result](evidence/event_b/README.md) and [recorded comparison](evidence/event_b/generated/20261110T174012Z/report.txt).

The package has tool reports, not the participants' Java source. We do not claim to have verified those implementations' behaviour. Code-smell labels and PMD warning totals are indicators, not proof of bugs or overall design quality. The Welch/Student test mismatch and coverage-interval discrepancy are documented in [M2_REPRO.md](M2_REPRO.md).

## Set up and check

Clone the repository with its history and tags; the scripts read frozen notebook versions from Git. Python 3.9 and `uv` are used for the pinned environment:

```bash
git clone https://github.com/kourousis/cs4928-grp33.git
cd cs4928-grp33
git fetch --tags
uv venv -p 3.9 .venv
uv pip install -p .venv -r repro/requirements.txt
```

From the repository root, on macOS/Linux:

```bash
.venv/bin/python -m unittest discover -s repro -p "test_*.py"
.venv/bin/python repro/inspect_rq2_sample.py --check
.venv/bin/python repro/run_event_a.py --check
.venv/bin/python repro/score_event_a.py --check
```

On Windows, replace `.venv/bin/python` with `.venv\Scripts\python.exe`.

For the complete original reproduction, execute the notebooks and then the two declared repair steps in order:

```bash
.venv/bin/python repro/run_all.py
.venv/bin/python repro/run_all.py --repairs R1 perceived_productivity
.venv/bin/python repro/run_all.py --repairs R1,R2 perceived_productivity
```

The original productivity notebook is expected to fail before both repairs. `run_all.py` reads the original notebooks at `PRE_EVENT_A`; today's `frequentist/` notebooks use the shared module.

For the refactoring comparison and Event B rerun:

```bash
.venv/bin/python repro/rq3_verify.py
.venv/bin/python repro/event_b.py run
```

These commands need a working local Jupyter kernel and may take several minutes. They save new timestamped evidence. A successful Event B run also refreshes the two `test_runs` notebooks; a failed run saves diagnostics, exits non-zero and leaves those notebook files unchanged. Full commands, environments and output locations are in [repro/README.md](repro/README.md).

## Evidence and checkpoints

- [M1 plan](M1_PLAN.md) and [addendum](M1_ADDENDUM.md): questions, sample, decision rules and declared deviations.
- [M2 record](M2_REPRO.md): reproduction results and limits.
- [RQ3 design problem](RQ3_DESIGN_PROBLEM.md): the measured reasons for considering a refactor.
- [AI log](AI_LOG.md): recorded material AI assistance and verification.
- Tags `M1_PLAN`, `M2_REPRO`, `PRE_EVENT_A`, `EVENT_A_PLAN`, `PRE_EVENT_B`, `EVENT_B_PLAN`, `EVENT_B` and `FINAL` identify saved checkpoints. Use the submitted tag/commit to identify the assessed version. Existing evidence folders retain the outputs and hashes from their original runs.

## Original study and credit

This project builds on the [authors' replication package](https://github.com/codescene-research/echoes-of-ai-emse-2025), pinned in our plan at commit `472ebca6d20af5d6de4264897ba98220ce521fd0`.

**Study:** Borg et al. (2026), *Echoes of AI: Investigating the Downstream Effects of AI Assistants on Software Maintainability*, Empirical Software Engineering. DOI: [10.1007/s10664-026-10889-1](https://doi.org/10.1007/s10664-026-10889-1).

The study authors are Markus Borg, Dave Hewett, Nadim Hagatulah, Noric Couderc, Emma Söderberg, Donal Graham, Uttam Kini and Dave Farley. The original data and research remain their work; the bounded reproduction, audits and analysis-design investigation documented here are the CS4928 group project. See [LICENSE](LICENSE).
