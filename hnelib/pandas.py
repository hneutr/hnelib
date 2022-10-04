import pandas as pd
import numpy as np

import hnelib.utils


COL = 'Value'
GROUPBY_COLS = None

#------------------------------------------------------------------------------#
#                              interal functions                               #
#------------------------------------------------------------------------------#
def _get_col(col_name):
    return f"__hnelib_{col_name}_col__"


def _get_original_and_groupby_cols(df, groupby_cols=None):
    df = df.copy()
    original_cols = list(df.columns)

    if not groupby_cols:
        groupby_cols = _get_col('groupby')
        df[groupby_cols] = True

    groupby_cols = hnelib.utils.listify(groupby_cols)

    return df, original_cols, groupby_cols


def _clean_cols(df, original_cols, added_cols):
    added_cols = hnelib.utils.listify(added_cols)

    cols = original_cols + [c for c in added_cols if c not in original_cols]

    return df[cols]


def _merge_annotations(df, annotations, original_cols, added_cols, join_cols):
    added_cols = hnelib.utils.listify(added_cols)
    join_cols = hnelib.utils.listify(join_cols)

    df = df.drop(columns=added_cols, errors='ignore')

    annotations = annotations[join_cols + added_cols].drop_duplicates()

    df = df.merge(
        annotations,
        on=join_cols,
    )

    return _clean_cols(df, original_cols, added_cols)

#------------------------------------------------------------------------------#
#                              external functions                              #
#------------------------------------------------------------------------------#
def annotate_error(df, col=COL, groupby_cols=GROUPBY_COLS, err_col='Error'):
    """
    given a dataframe, adds a column with the standard error.
    """
    df, original_cols, groupby_cols = _get_original_and_groupby_cols(df, groupby_cols)

    std_col = _get_col('std')
    n_col = _get_col('n')
    sqrt_n_col = _get_col('sqrt_n')

    df[std_col] = df.groupby(groupby_cols)[col].transform('std')
    df[n_col] = df.groupby(groupby_cols)[col].transform('count')
    df[sqrt_n_col] = df[n_col] ** .5
    df[err_col] = df[std_col] / df[sqrt_n_col]

    return _clean_cols(df, original_cols, err_col)


def normalize_col(df, col=COL, groupby_cols=GROUPBY_COLS, norm_col=None):
    norm_col = norm_col or col

    df, original_cols, groupby_cols = _get_original_and_groupby_cols(df, groupby_cols)

    min_col = _get_col('min')
    max_col = _get_col('max')
    norm_col = _get_col('norm')

    df[min_col] = df.groupby(groupby_cols)[col].transform('min')
    df[norm_col] = df[col] - df[min_col]
    df[max_col] = df.groupby(groupby_cols)[norm_col].transform('max')
    df[norm_col] /= df[max_col]
    df[col] = df[norm_col]

    return _clean_cols(df, original_cols, col)


def annotate_percentiles(
    df,
    col=COL,
    groupby_cols=GROUPBY_COLS,
    percentiles=[25, 75],
    percentile_col_prefix='',
):
    df = original_cols, groupby_cols = _get_original_and_groupby_cols(df, groupby_cols=groupby_cols)

    percentile_to_col = {p: percentile_col_prefix + hnelib.utils.add_ordinal_indicator(p) for p in percentiles}

    percentile_rows = []
    for _, rows in df.groupby(groupby_cols):
        percentile_rows.append({
            **{c: rows.iloc[0][c] for c in groupby_cols},
            **{c: np.percentile(rows[col], p) for p, c in percentile_to_col.items()},
        })

    return _merge_annotations(
        df=df, 
        annotations=pd.DataFrame(percentile_rows),
        original_cols=original_cols,
        added_cols=list(percentile_to_col.values()),
        join_cols=groupby_cols,
    )


def annotate_25th_and_75th_percentiles(*args, **kwargs):
    return annotate_percentiles(*args, **kwargs, percentiles=[25, 75])


def annotate_proportions_confidence_interval(
    df,
    count_col,
    observations_col,
    groupby_cols=GROUPBY_COLS,
    upper_col='UpperConf',
    lower_col='LowerConf',
    as_percent=False,
    alpha=.05,
    method='normal',
):
    """
    given a dataframe, adds a columns with the confidence intervals.
    """
    from statsmodels.stats.proportion import proportion_confint

    df, original_cols, groupby_cols = _get_original_and_groupby_cols(df, groupby_cols)

    conf_intervals = []
    for _, rows in df.groupby(groupby_cols):
        row = rows.iloc[0]

        lower_conf, upper_conf = proportion_confint(
            count=row[count_col],
            nobs=row[observations_col],
            alpha=alpha,
            method=method,
        )

        if as_percent:
            upper_conf *= 100
            lower_conf *= 100

        conf_intervals.append({
            **{c: row[c] for c in groupby_cols},
            upper_col: upper_conf,
            lower_col: lower_conf,
        })

    return _merge_annotations(
        df=df, 
        annotations=pd.DataFrame(conf_intervals),
        original_cols=original_cols,
        added_cols=[
            lower_col,
            upper_col,
        ],
        join_cols=groupby_cols,
    )


def aggregate_over_col(
    df,
    col=COL,
    join_cols=[],
    agg_cols=[],
    col_val_labels={},
):
    """
    This is useful for taking dfs with a column like Gender: Male/Female and a
    stat column like "GiniCoefficient" and turning it into:
    - MaleGiniCoefficient
    - FemaleGiniCoefficient

    - {col}: in the above example, `Gender`
    - {agg_cols}: in the above example, ["GiniCoefficient"]
    - {col_val_labels}: defaults to {col.val}: {col.val}

    for each key ({agg_val}) and value ({agg_val_label}) in {col_val_labels}:
        for each {val_col} in {agg_cols}:
            add a new col to df: `{agg_val_label}{val_col}`
    """
    df = df.copy()

    col_val_labels = col_val_labels or {v: v for v in df[col].unique()}

    df[col] = df[col].apply(col_val_labels.get)

    dfs = []
    for val, rows in df.groupby(col):
        _df = rows.copy()[
            join_cols + agg_cols
        ].rename(columns={c: f"{val}{c}" for c in agg_cols})

        dfs.append(_df)
    
    df = dfs.pop()
    for _df in dfs:
        df = df.merge(
            _df,
            on=join_cols,
        )

    return df


def correct_significance_for_multiple_tests(
    df,
    p_col='P',
    groupby_cols=GROUPBY_COLS,
    significance_col='Significant',
    alpha=.05,
    method='bonferroni',
):
    from statsmodels.stats.multitest import multipletests
    df, original_cols, groupby_cols = _get_original_and_groupby_cols(df, groupby_cols)

    dfs = []
    for _, rows in df.groupby(groupby_cols):
        rejects = multipletests(rows[p_col], alpha=alpha, method=method)

        rows = rows.copy()
        rows[significance_col] = [not reject for reject in rejects]
        dfs.append(rows)

    return _clean_cols(df, original_cols, significance_col)


def annotate_duplicate_percentile(
    df,
    col,
    sort_by,
    groupby_cols=GROUPBY_COLS,
    percentile_col='Percentile',
    n_bins=100,
):
    """
    this function makes a percentile column that allows a given value to exist in multiple bins.
    """
    df, original_cols, groupby_cols = _get_original_and_groupby_cols(df, groupby_cols)

    percentile_dfs = []
    for _, rows in df.groupby(groupby_cols):
        vals = list(rows.sort_values(by=sort_by)[[col]].drop_duplicates()[col])

        bins = np.linspace(0, len(vals), min(n_bins, len(vals)) + 1)

        percentile = 0
        percentiles = []
        for i, val in enumerate(val):
            if percentile < len(bins) and bins[percentile + 1] < i:
                percentile += 1

            percentiles.append({
                **{c: rows.iloc[0][c] for c in groupby_cols},
                val_col: val,
                percentile_col: percentile,
            })

        percentile_dfs.append(pd.DataFrame(percentiles)) 

    return _merge_annotations(
        df=df, 
        annotations=pd.concat(percentile_dfs),
        original_cols=original_cols,
        added_cols=percentile_col,
        join_cols=[col] + groupby_cols,
    )
