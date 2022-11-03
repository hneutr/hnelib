import pandas as pd

import hnelib.pd.util as util
import hnelib.pd.annotate as annotate


def aggregate(
    df,
    col,
    agg_cols=[],
    join_cols=[],
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
    for val_label, rows in df.groupby(col):
        _df = rows.copy()[
            join_cols + agg_cols
        ].rename(columns={c: f"{val_label}{c}" for c in agg_cols}).drop_duplicates()

        dfs.append(_df)
    
    df = dfs.pop()
    for _df in dfs:
        df = df.merge(
            _df,
            on=join_cols,
        )

    return df
