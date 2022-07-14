import pandas as pd
import numpy as np


FAKE_GROUPBY_COL = '__fake_hnelib_groupby_column__'


def add_error(df, groupby_col='Bin', value_col='Value', error_col='Error'):
    """
    given a dataframe, adds a column with the standard error.
    """
    df = df.copy()

    df['STD'] = df.groupby(groupby_col)[value_col].transform('std')
    df['N'] = df.groupby(groupby_col)[value_col].transform('count')
    df['N^.5'] = df['N'] ** .5
    df[error_col] = df['STD'] / df['N^.5']

    df = df.drop(columns=['STD', 'N', 'N^.5'])
    return df


def annotate_25th_and_75th_percentiles(
    df,
    value_col,
    groupby_cols=[],
    twenty_fifth_col='25th',
    seventy_fifth_col='75th',
):
    df, groupby_cols = pad_groupby_cols(df, groupby_cols)

    percentile_rows = []
    for _, rows in df.groupby(groupby_cols):
        percentile_rows.append({
            **get_groupby_info(rows, groupby_cols),
            twenty_fifth_col: np.percentile(rows[value_col], 25),
            seventy_fifth_col: np.percentile(rows[value_col], 75),
        })

    df = df.merge(
        pd.DataFrame(percentile_rows),
        on=groupby_cols,
    )

    return df


def add_proportions_confidence_interval(
    df,
    count_col,
    observations_col,
    alpha=.05,
    method='normal',
    groupby_cols=[],
    upper_col='UpperConf',
    lower_col='LowerConf',
    as_percent=False,
):
    """
    given a dataframe, adds a columns with the confidence intervals.
    """
    from statsmodels.stats.proportion import proportion_confint
    df = df.copy()

    cols = list(df.columns)

    if not groupby_cols:
        df['__dummy__'] = True
        groupby_cols.append('__dummy__')

    annotated_rows = []
    for _, rows in df.groupby(groupby_cols):
        row = rows.iloc[0]

        groupby_info = {c: row[c] for c in groupby_cols}

        lower_conf, upper_conf = proportion_confint(
            count=row[count_col],
            nobs=row[observations_col],
            alpha=alpha,
            method=method,
        )

        annotated_rows.append({
            **groupby_info,
            upper_col: upper_conf,
            lower_col: lower_conf,
        })

    df = df.merge(
        pd.DataFrame(annotated_rows),
        on=groupby_cols
    )

    df = df[
        cols + [upper_col, lower_col]
    ].drop_duplicates()

    if as_percent:
        df[upper_col] *= 100
        df[lower_col] *= 100

    return df


def aggregate_df_over_column(df, agg_col, join_cols=[], value_cols=[], agg_value_to_label={}):
    """
    This is useful for taking dfs with a column like Gender: Male/Female and a
    stat column like "GiniCoefficient" and turning it into:
    - MaleGiniCoefficient
    - FemaleGiniCoefficient
    etc

    agg_col is something like "NewHire"

    If agg_value_to_label isn't empty, we'll use each key in
    that dict as a value to map over, and, for each col in value_cols, produce a
    column like: `{value}original` (where `value` is the value under `key`)
    """
    df = df.copy()
    df = df[join_cols + value_cols + [agg_col]]

    if not agg_value_to_label:
        agg_value_to_label = {v: v for v in df[agg_col].unique()}

    df = df[
        df[agg_col].isin(list(agg_value_to_label.keys()))
    ]

    new_df = pd.DataFrame()
    for agg_value, rows in df.groupby(agg_col):
        agg_label = agg_value_to_label[agg_value]
        rows = rows.copy().drop(columns=[agg_col])
        rows = rows.rename(columns={c: f"{agg_label}{c}" for c in value_cols})

        if new_df.empty:
            new_df = rows
        else:
            new_df = new_df.merge(
                rows,
                on=join_cols,
            )

    return new_df


def pad_groupby_cols(df, groupby_cols=[]):
    """
    It's nice to be able to run things as either a groupby or not, so sometimes
    we want to add a fake column to groupby over.

    We'll delete this column after groupbying.
    """
    if not groupby_cols:
        groupby_cols.append(FAKE_GROUPBY_COL)
        df[FAKE_GROUPBY_COL] = True

    return df, groupby_cols


def get_groupby_info(df, groupby_cols):
    """
    This returns a dict of info for the groupby_cols, but excludes the
    FAKE_GROUPBY_COL, in case it was added
    """
    return {c: df.iloc[0][c] for c in groupby_cols if c != FAKE_GROUPBY_COL}


def adjust_significance_for_multiple_tests(
    df,
    p_col='P',
    groupby_cols=[],
    alpha=.05,
    method='bonferroni',
    significance_col='Significant',
):
    from statsmodels.stats.multitest import multipletests
    df = df.copy()
    df, groupby_cols = pad_groupby_cols(df, groupby_cols)

    cols = list(df.columns)

    new_dfs = []
    for _, rows in df.groupby(groupby_cols):
        rows = rows.copy()
        p_values = rows[p_col]
        
        rejects = multipletests(p_values, alpha=alpha, method=method)
        rows[significance_col] = [not reject for reject in rejects]

        new_dfs.append(rows)

    df = pd.concat(new_dfs)

    df = df[
        cols + [significance_col]
    ].drop_duplicates()

    return df


def annotate_duplicate_percentile(df, val_col, id_col, n_bins=100, out_col='Percentile'):
    """
    this function makes a percentile column that allows a given value to exist in multiple bins.
    """
    new_df = df.copy()[
        [
            val_col,
            id_col,
        ]
    ].drop_duplicates()

    n_bins = min(n_bins, new_df[id_col].nunique())

    new_df = new_df.sort_values(by=val_col)
    bin_edges = np.linspace(0, len(new_df), n_bins + 1)

    current_bin = 0
    bin_annotations = []
    for i in range(len(new_df)):
        if current_bin < len(bin_edges):
            if i > bin_edges[current_bin + 1]:
                current_bin += 1

        bin_annotations.append(current_bin)

    new_df[out_col] = bin_annotations
    
    new_df = new_df[
        [
            id_col,
            out_col,
        ]
    ].drop_duplicates()

    df = df.copy().merge(
        new_df,
        on=id_col
    )

    return df
