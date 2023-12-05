import numpy as np


STRS_TO_ESCAPE = ['%', '&', '#']
STRS_TO_REPLACE = {
    '<': '$<$',
    '>': '$>$',
    '=': '$\eq$',
}


def sanitize_string(string, to_escape=STRS_TO_ESCAPE, to_replace=STRS_TO_REPLACE):
    to_replace = to_replace | {s: f"\{s}" for s in to_escape}

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


def format_df(
    df,
    column_alignments=[],
    sanitize=True,
    column_format=None,
    table_styles=None,
    rules={
        '\\toprule': '\\toprule\n\\hline',
        '\\midrule': '\\midrule\n\\hline',
        '\\bottomrule': '\\bottomrule\n\\hline',
    },
):
    """
    adds some lines that I like to tables

    also does some nice little alignment magic on columns
    """
    if not column_alignments:
        column_alignments = ['l' if dtype == np.object else 'r' for c, dtype in df.dtypes.items()]

    if sanitize:
        df = sanitize_df(df)

    if table_styles:
        df = df.style.set_table_styles(table_styles)

    # if hide_columns:
    #     df.style.hide_

    content = df.style.hide(axis='index').to_latex(
        column_format=column_format or "|" + "|".join(column_alignments) + "|",
        hrules=True,
    )

    for pattern, replacement in rules.items():
        content = content.replace(pattern, replacement)

    return content

def fancy_table(df, column_alignments=None, sanitize=True, table_styles=None):
    content = format_df(
        df,
        sanitize=sanitize,
        column_format="@{}" + "".join(column_alignments or []) + "@{}",
        table_styles=table_styles,
        rules={
            '\\midrule': '\\hline',
            '\\bottomrule': '\\bottomrule\n\\hline',
        },
    )

    content = "\\renewcommand{\\arraystretch}{1.1}\n" + content
    return content
