# repro/runs — M2 as-shipped notebook runs (RQ1a)

These are the reported runs for RQ1a, following `M1_PLAN.md` § RQ1a Method steps 1 and 2.
They were made on 22 Oct 2026 (Week 7) from a clean checkout of `main` @ `6914f92`. The notebooks, data and runner are unchanged since tag `M1_PLAN` (`618005b`); see `inputs_sha256.txt` in each run.

## Runs, in the order made

| Run folder | Command | Result |
|---|---|---|
| `20261022T150533Z` | `python repro/run_all.py` (all four, as shipped) | `codehealth` OK, `completion_time` OK, `coverage` OK, `perceived_productivity` **FAILED**: `FileNotFoundError: 'data/task1_preprocessed.csv'` (fault R1) |
| `20261022T151200Z` | `python repro/run_all.py --repairs R1 perceived_productivity` | **FAILED**: `NameError: name 'shapiro' is not defined` (fault R2) |
| `20261022T151209Z` | `python repro/run_all.py --repairs R1,R2 perceived_productivity` | OK |

So each declared fault is captured in its own failed run before the repair that fixes it, as M1 requires.
No undeclared fix was applied. The authors' notebooks were not edited (see `inputs_sha256.txt` in each run).

**Environment** (from `environment.txt`, identical in all three runs): Python 3.9.25, installed with `uv`, on
Linux x86_64. numpy 2.0.2, pandas 2.2.3, scipy 1.13.1, matplotlib 3.9.4, seaborn 0.13.2, the versions pinned in
`repro/requirements.txt`. The same versions were confirmed inside the notebook kernel.

## Primary values against the paper (decision rule from M1_PLAN.md)

Each value is formatted with `format(x, '.Nf')`, with N as fixed in M1. "Ours" is copied from the run's
`*.outputs.txt`.

| Metric | Value | Paper | Ours (raw) | Ours (rounded) | Match |
|---|---|---|---|---|---|
| Completion time | median T vs C (min) | 136 vs 173 | 136.07 vs 172.63 | 136 vs 173 | yes |
| | Cliff's δ (3 dp) | −0.079 | −0.0793 | −0.079 | yes |
| | p, rank-sum (2 dp) | 0.56 | 0.5644 | 0.56 | yes |
| | significant at 0.05? | no | no | no | yes |
| Perceived productivity (after R1,R2) | mean T vs C | 3.95 vs 4.06 | 3.9462 vs 4.0636 | 3.95 vs 4.06 | yes |
| | Cohen's d | −0.21 | −0.2128 | −0.21 | yes |
| | p, as-shipped t-test | 0.37 | 0.3713 | 0.37 | yes |
| | significant at 0.05? | no | no | no | yes |
| CodeHealth | mean T vs C | 8.49 vs 8.44 | 8.48725 vs 8.44086 | 8.49 vs 8.44 | yes |
| | Cohen's d | 0.28 | 0.2761 | 0.28 | yes |
| | p, as-shipped t-test | 0.24 | 0.2367 | 0.24 | yes |
| | significant at 0.05? | no | no | no | yes |
| Test coverage | median T vs C | 0.70 vs 0.70 | 0.70 vs 0.70 | 0.70 vs 0.70 | yes |
| | Cliff's δ | 0.09 | 0.0929 | 0.09 | yes |
| | p, rank-sum | 0.49 | 0.4900 | 0.49 | yes |
| | significant at 0.05? | no | no | no | yes |

No value sat on a rounding boundary.

**Status per metric, applying the M1 rule mechanically (for team review before M2_REPRO):**
completion time REPRODUCED, perceived productivity REPRODUCED (needed declared repairs R1 and R2, which
are recorded as a deviation), CodeHealth REPRODUCED, test coverage REPRODUCED.
**Overall RQ1a: REPRODUCED.** This matches the RQ1 expected result (no significant difference on any of
the four metrics).

## Secondary values: bootstrap 95% CIs (reported; they do not change the status)

| Metric | Paper T / C | Ours T / C | Note |
|---|---|---|---|
| Completion time (min) | 105.5–180.0 / 118.1–210.0 | 105.5–180.0 / 118.1–210.0 | same |
| Perceived productivity | 3.77–4.12 / 3.88–4.24 | 3.77–4.12 / 3.88–4.24 | same |
| CodeHealth | 8.43–8.54 / 8.39–8.49 | 8.43–8.54 / 8.39–8.49 | same |
| Test coverage | 0.695–0.71 / 0.69–0.74 | 0.69–0.71 / 0.69–0.71 | **Control upper bound differs from the paper (0.74 vs 0.71)**; ours matches the authors' stored notebook output. This is the audit finding already listed in M1. Treatment: the notebook prints 2 dp, so the paper's 0.695 can't be compared beyond that |

## Things seen in these runs that belong in the deviation / audit list

- R1 and R2 were needed for `perceived_productivity` (declared in M1).
- The CH and PP cells print "Welch's t-test (unequal variances assumed)", but the code runs Student's t-test
  (`equal_var=True`). The p-values above are the as-shipped Student's values. Welch's sensitivity values are
  in Enda's recompute (`repro/recompute/`, PR #1): CH p = 0.235, PP p = 0.368.
- `coverage.ipynb` cell 5 is titled "TC Descriptive Statistics" but prints CodeHealth values (8.32, 8.35 …).
  `perceived_productivity.ipynb` cell 6 has the same copy-paste title but prints PP values.
- Python 3.9.25 is used, not the 3.9.21 that the notebooks record. Same minor version.
- Bootstrap CIs are unseeded (1,000,000 resamples), so their last digit could move on a re-run.
