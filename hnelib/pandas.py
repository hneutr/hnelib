def add_error(df, groupby_col='Bin', value_col='Value', error_col='Error'):
    """
    given a dataframe, adds a column with the standard error.
    """
    df = df.copy()

    df['STD'] = df.groupby(groupby_col)[value_col].transform('std')
    df['N'] = df.groupby(groupby_col)[groupby_col].transform('count')
    df['N^.5'] = df['N'] ** .5
    df[error_col] = df['STD'] / df['N^.5']

    df = df.drop(columns=['STD', 'N', 'N^.5'])
    return df
