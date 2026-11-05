"""Shared statistics helpers for the four frequentist notebooks (RQ3, task 9b).

Before this module, each notebook kept its own copy of these functions, and the
copies had started to differ (see RQ3_DESIGN_PROBLEM.md). Every function below
keeps the behaviour of the notebook copies it replaces, including the order of
the random draws, so a run with the same seed prints the same numbers as the
original notebooks (checked by repro/rq3_verify.py, tested in repro/test_stats.py).

The notebooks import it with `from stats import ...`; they run with frequentist/
as the working directory, so this file is found without any path setup.
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Cliff's delta magnitude thresholds used by the notebooks (Romano et al.)
CLIFFS_THRESHOLDS = ((0.147, "negligible"), (0.33, "small"), (0.474, "medium"))
# Cohen's d magnitude thresholds used by the notebooks
COHENS_THRESHOLDS = ((0.2, "Negligible"), (0.5, "Small"), (0.8, "Medium"))


# --- data ----------------------------------------------------------------------

def load_data(data_dir=DATA_DIR):
    """Task 1 and Task 2 data frames.

    The path is built from this file's location, so it no longer depends on the
    working directory (fault R1: perceived_productivity read data/ while the
    other notebooks read ../data/).
    """
    data_dir = Path(data_dir)
    task1_df = pd.read_csv(data_dir / "task1_preprocessed.csv")
    task2_df = pd.read_csv(data_dir / "task2_preprocessed.csv")
    return task1_df, task2_df


def split_groups(task1_df, task2_df):
    """(task1_ai_group, task1_manual_group, task2_treatment, task2_control)."""
    return (task1_df[task1_df['ai'] == True],  # noqa: E712 (same comparison as the notebooks)
            task1_df[task1_df['ai'] == False],  # noqa: E712
            task2_df[task2_df['treatment'] == 'ai'],
            task2_df[task2_df['treatment'] == 'human'])


def _drop_na(values):
    """Missing values removed. A pandas Series stays a Series (the notebooks pass
    Series, and numpy's mean/std then use the same pandas code as before)."""
    if hasattr(values, "dropna"):
        return values.dropna()
    values = np.asarray(values, dtype=float)
    return values[~np.isnan(values)]


# --- effect sizes ---------------------------------------------------------------

def cohens_d(group1, group2):
    """Cohen's d with the pooled sample standard deviation (ddof=1). NaNs are dropped."""
    group1 = _drop_na(group1)
    group2 = _drop_na(group2)

    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)

    pooled_std = np.sqrt(((len(group1) - 1) * std1**2 + (len(group2) - 1) * std2**2) /
                         (len(group1) + len(group2) - 2))
    return (mean1 - mean2) / pooled_std


def cohens_magnitude(d):
    """'Negligible', 'Small', 'Medium' or 'Large' for |d|."""
    for limit, label in COHENS_THRESHOLDS:
        if abs(d) < limit:
            return label
    return "Large"


def cliffs_delta(x, y):
    """Cliff's delta: (#pairs x > y - #pairs x < y) / (n_x * n_y).

    NaNs are always dropped first. One of the old copies (coverage) did this and
    two (codehealth, completion_time) did not, where a NaN counted as a tie and
    pulled delta towards 0. Every existing caller dropped NaNs before calling,
    so no reported number changes.
    """
    x = _drop_na(x)
    y = _drop_na(y)
    greater = 0
    lesser = 0
    for i in x:
        for j in y:
            if i > j:
                greater += 1
            elif i < j:
                lesser += 1
    return (greater - lesser) / (len(x) * len(y))


def cliffs_magnitude(delta):
    """'negligible', 'small', 'medium' or 'large' for |delta|."""
    for limit, label in CLIFFS_THRESHOLDS:
        if abs(delta) < limit:
            return label
    return "large"


# --- bootstrap confidence intervals ----------------------------------------------
# All use np.random's global generator, drawing in the same order as the old copies,
# so a seeded run reproduces the old copies' numbers exactly.

def _percentile_ci(samples, ci):
    return np.percentile(samples, (100 - ci) / 2), np.percentile(samples, 100 - (100 - ci) / 2)


def _bootstrap_ci(data, statistic, n_bootstraps, ci):
    boot = [statistic(np.random.choice(data, size=len(data), replace=True)) for _ in range(n_bootstraps)]
    lower, upper = _percentile_ci(boot, ci)
    return statistic(data), lower, upper


def _bootstrap_ci_difference(treatment, control, statistic, n_bootstraps, ci):
    treatment = np.asarray(treatment)
    control = np.asarray(control)
    n_t = len(treatment)
    n_c = len(control)
    diffs = np.empty(n_bootstraps)
    for i in range(n_bootstraps):
        t_samp = np.random.choice(treatment, size=n_t, replace=True)
        c_samp = np.random.choice(control, size=n_c, replace=True)
        diffs[i] = statistic(t_samp) - statistic(c_samp)
    lower, upper = _percentile_ci(diffs, ci)
    return statistic(treatment) - statistic(control), lower, upper


def bootstrap_ci_mean(data, n_bootstraps=1000000, ci=95):
    """(mean, lower, upper): percentile bootstrap CI for the mean."""
    return _bootstrap_ci(data, np.mean, n_bootstraps, ci)


def bootstrap_ci_median(data, n_bootstraps=1000000, ci=95):
    """(median, lower, upper): percentile bootstrap CI for the median."""
    return _bootstrap_ci(data, np.median, n_bootstraps, ci)


def bootstrap_ci_mean_difference(treatment, control, n_bootstraps=1000000, ci=95):
    """(difference, lower, upper) for mean(treatment) - mean(control)."""
    return _bootstrap_ci_difference(treatment, control, np.mean, n_bootstraps, ci)


def bootstrap_ci_median_difference(treatment, control, n_bootstraps=1000000, ci=95):
    """(difference, lower, upper) for median(treatment) - median(control)."""
    return _bootstrap_ci_difference(treatment, control, np.median, n_bootstraps, ci)
