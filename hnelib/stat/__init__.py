import pandas as pd
import scipy.stats
import statsmodels.stats.proportion
import statsmodels.api as sm


import hnelib.stat.test
import hnelib.stat.model


def correlation(xs, ys):
    pearson, pearson_p = scipy.stats.pearsonr(xs, ys)
    return pearson, pearson_p


def proportions_confidence_interval(events, observations, alpha=.05, method='normal', as_percent=False):
    lower_bound, upper_bound = statsmodels.stats.proportion.proportion_confint(
        count=events,
        nobs=observations,
        alpha=alpha,
        method=method,
    )

    if as_percent:
        upper_bound *= 100
        lower_bound *= 100

    return lower_bound, upper_bound

def lowess(xs, ys, frac=.2):
    lowess_xs, lowess_ys = zip(*sm.nonparametric.lowess(ys, xs, frac=frac))
    return lowess_xs, lowess_ys
