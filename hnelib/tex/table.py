import numpy as np


STRS_TO_ESCAPE = ['%', '&', '#']
STRS_TO_REPLACE = {
    '<': '$\lt$',
    '>': '$\gt$',
    '=': '$\eq$',
}


def sanitize_string(string, to_escape=STRS_TO_ESCAPE, to_replace=STRS_TO_REPLACE):
    to_replace = to_replace or {s: f"\{s}" for s in to_escape}

    for find, replace in to_replace.items():
        string = string.replace(find, replace)

    return string

def sanitize_df(df):
    df = df.copy()

    for col, dtype in df.dtypes.items():
        if dtype == 'object':
            df[col] = df[col].astype(str).apply(sanitize_string)

    df = df.rename(columns={c: sanitize_string(c) for c in df.columns})

    return df


def format_df(df, column_alignments=[], sanitize=True):
    """
    adds some lines that I like to tables

    also does some nice little alignment magic on columns
    """
    if not column_alignments:
        column_alignments = ['l' if dtype == np.object else 'r' for c, dtype in df.dtypes.items()]

    if sanitize:
        df = sanitize_df(df)

    header = "|" + "|".join(column_alignments) + "|"

    content = df.style.hide(axis='index').to_latex(
        column_format=header,
        hrules=True,
    )

    for rule in ['\\toprule', '\midrule', '\\bottomrule']:
        content = content.replace(rule, f"{rule}\n\\hline")

    return content