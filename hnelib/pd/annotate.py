import pandas as pd
import numpy as np

import hnelib.util
import hnelib.pd.util

COL = 'Value'


def _add_annotations(df, annotations, join_cols):
    join_cols = hnelib.util.as_list(join_cols)

    if isinstance(annotations, list):
        if len(annotations) and isinstance(annotations[0], pd.DataFrame):
            annotations = pd.concat(annotations)
        else:
            annotations = pd.DataFrame(annotations)

    df = df.drop(columns=[c for c in annotations.columns if c not in join_cols], errors='ignore')

    df = df.merge(
        annotations,
        on=join_cols,
    )

    return hnelib.pd.util.remove_fake_cols(df)


#------------------------------------------------------------------------------#
#                              external functions                              #
#------------------------------------------------------------------------------#
def error(
    df,
    col=COL,
    to_col='Error',
    groupby_cols=None,
):
    """
    given a dataframe, adds a column with the standard error.
    """
    df, groupby_cols = hnelib.pd.util.get_groupby_cols(df, groupby_cols)

    std_col = hnelib.pd.util.get_fake_col('std')
    n_col = hnelib.pd.util.get_fake_col('n')
    sqrt_n_col = hnelib.pd.util.get_fake_col('sqrt_n')

    df[std_col] = df.groupby(groupby_cols)[col].transform('std')
    df[n_col] = df.groupby(groupby_cols)[col].transform('count')
    df[sqrt_n_col] = df[n_col] ** .5
    df[to_col] = df[std_col] / df[sqrt_n_col]

    return hnelib.pd.util.remove_fake_cols(df)


def norm(
    df,
    col=COL,
    to_col=None,
    groupby_cols=None
):
    df, groupby_cols = hnelib.pd.util.get_groupby_cols(df, groupby_cols)

    to_col = to_col or col

    df[to_col] = df[col]
    df[to_col] -= df.groupby(groupby_cols)[to_col].transform('min')
    df[to_col] /= df.groupby(groupby_cols)[to_col].transform('max')

    return df


def percentiles(
    df,
    col=COL,
    values=[25, 75],
    to_col_prefix='',
    groupby_cols=None,
):
    df, groupby_cols = hnelib.pd.util.get_groupby_cols(df, groupby_cols)

    value_to_col = {p: to_col_prefix + hnelib.util.add_ordinal_indicator(p) for p in values}

    annotations = []
    for _, rows in df.groupby(groupby_cols):
        annotations.append({
            **hnelib.pd.util.get_groupby_dict(rows),
            **{p_col: np.percentile(rows[col], p) for p, p_col in value_to_col.items()},
        })

    return _add_annotations(df, annotations, join_cols=groupby_cols)


def duplicate_quantile(
    df,
    col,
    entity_col,
    to_col=None,
    n_quantiles=100,
    groupby_cols=None,
):
    """
    adds a percentile column where {col} values can exist in more than one bin
    """
    to_col = to_col or col
    df, groupby_cols = hnelib.pd.util.get_groupby_cols(df, groupby_cols)

    annotations = []
    for _, rows in df.groupby(groupby_cols):
        entities = list(rows.sort_values(by=col)[entity_col].unique())

        bins = np.linspace(0, len(entities), min(n_quantiles, len(entities)) + 1)

        quantile = 0
        for i, entity in enumerate(entities):
            if quantile < len(bins) and bins[quantile + 1] < i:
                quantile += 1

            annotations.append({
                entity_col: entity,
                to_col: quantile,
            })

    return _add_annotations(df, annotations, join_cols=entity_col)


#------------------------------------------------------------------------------#
#                                                                              #
#                                                                              #
#                                    stats                                     #
#                                                                              #
#                                                                              #
#------------------------------------------------------------------------------#
def proportions_confidence_interval(
    df,
    events_col,
    observations_col,
    lower_bound_col='LowerBound',
    upper_bound_col='UpperBound',
    groupby_cols=None,
    **kwargs,
):
    """
    given a dataframe, adds a columns with the confidence intervals.
    """
    import hnelib.stat
    df, groupby_cols = hnelib.pd.util.get_groupby_cols(df, groupby_cols)

    annotations = []
    for _, rows in df.groupby(groupby_cols):
        row = rows.first()
        lower_bound, upper_bound = hnelib.stat.proportions_confidence_interval(
            events=row[events_col],
            observations=row[observations_col],
            **kwargs,
        )

        annotations.append({
            **hnelib.pd.util.get_groupby_dict(rows),
            upper_col: upper_conf,
            lower_col: lower_conf,
        })

    return _add_annotations(df, annotations, join_cols=groupby_cols)


def multiple_hypothesis_corrected_pvalue(
    df,
    col='P',
    to_col=None,
    hypothesis_cols=None,
    groupby_cols=None,
    **kwargs,
):
    import hnelib.stat
    to_col = to_col or col
    hypothesis_cols = hnelib.util.as_list(hypothesis_cols)

    df, groupby_cols = hnelib.pd.util.get_groupby_cols(df, groupby_cols)

    annotations = []
    for _, rows in df.groupby(groupby_cols):
        rows = rows.copy()[
            hypothesis_cols + [p_col]
        ].drop_duplicates()

        rows[to_col] = hnelib.stat.test.correct_for_multiple_hypotheses(
            pvals=rows[col],
            **kwargs,
        )

        annotations.append(rows)

    return _add_annotations(df, annotations, join_cols=groupby_cols + hypothesis_cols)


def round_to_nearest(df, col, to_col=None, nearest=1):
    to_col = to_col or col
    df[to_col] = df[col].apply(lambda v: round(v / nearest) * nearest)
    return df
