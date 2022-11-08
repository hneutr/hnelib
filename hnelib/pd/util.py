import pandas as pd

import hnelib.utils


FAKE_COL_PREFIX = 'fake_hnelib_col'


def get_fake_col(col_name):
    return f"{FAKE_COL_PREFIX}_{col_name}"


def is_fake_col(col):
    return col.startswith(FAKE_COL_PREFIX)


def get_groupby_dict(row, groupby_cols):
    if isinstance(row, pd.Series):
        row = row.iloc[0]

    return {col: row[col] for col in groupby_cols if not is_fake_col(col)}


def get_groupby_cols(df, groupby_cols=None):
    """
    given a df and some (possibly empty) groupby_cols, returns:
    - a (possibly modified df)
    - the groupby cols (now definitely non-empty)
    """
    df = df.copy()

    if not groupby_cols:
        groupby_cols = get_fake_col('groupby')
        df[groupby_cols] = True

    groupby_cols = hnelib.utils.as_list(groupby_cols)

    return df, groupby_cols


def remove_fake_cols(df):
    cols = [col for col in df.columns if not is_fake_col(col)]
    return df[cols]


def rename_df(df, column_remap):
    """
    creates a df with the new column names, but properly handles duplicated source keys
    """
    return pd.DataFrame({new_c: df[old_c] for new_c, old_c in column_remap.items() if old_c in df.columns})
