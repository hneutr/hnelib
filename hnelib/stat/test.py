import scipy.stats

import hnelib.pd.util


def ks(dist_1, dist_2, alpha=.05, d_threshold=1.628):
    ks, p = scipy.stats.ks_2samp(dist_1, dist_2)

    n = len(dist_1) + len(dist_2)

    ks_threshold = d_threshold * (((2 * n) / (n ** 2)) **.5)

    significant = ks_threshold < abs(ks) and p < alpha

    return p, significant


def correct_for_multiple_hypotheses(
    p_vals,
    alpha=.05,
    method='fdr_bh',
):
    rejects, corrected_p_vals, _, _ = statsmodels.stats.multitest.multipletests(
        pvals=p_vals,
        alpha=alpha,
        method=method,
    )

    return corrected_p_vals

def t(a, b, alternative='two-sided', **kwargs):
    return scipy.stats.ttest_ind(a=a, b=b, alternative=alternative, **kwargs)
