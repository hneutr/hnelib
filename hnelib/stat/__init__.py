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

def lowess(df, x_col, y_col, frac=.2):
    lowess_xs, lowess_ys = zip(*sm.nonparametric.lowess(df[y_col], df[x_col], frac=frac))
    lowess_df = pd.DataFrame({x_col: lowess_xs, y_col: lowess_ys})
    lowess_df = lowess_df.drop_duplicates()

    return lowess_df
