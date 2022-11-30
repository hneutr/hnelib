import hnelib.pd.util


LINEWIDTH = .65
S = 12
LINE_ZORDER = 1
SCATTER_ZORDER = 2


def connected(
    ax,
    df,
    x_col,
    y_col,
    color_col=None,
    facecolor_col=None,
    s_col=None,
    fade_facecolors=True,
    s=S,
    sort_cols=[],
    groupby_cols=[],
    linewidth=LINEWIDTH,
    line_kwargs={},
    **scatter_kwargs,
):
    col_remap = {
        'X': x_col,
        'Y': y_col,
        'Color': color_col,
        'FaceColor': facecolor_col,
        'S': s_col,
    }

    for col in sort_cols + groupby_cols:
        col_remap[col] = col

    df = hnelib.pd.util.rename_df(df, col_remap)
    df, groupby_cols = hnelib.pd.util.get_groupby_cols(df, groupby_cols)

    scatter_kwargs = {
        's': df['S'] if 'S' in df.columns else S,
        'linewidth': linewidth,
        'zorder': SCATTER_ZORDER,
    }

    line_kwargs = {
        'zorder': LINE_ZORDER,
        'linewidth': linewidth,
    }

    if 'Color' in df.columns:
        if 'FaceColor' not in df.columns:
            df['FaceColor'] = df['Color']

        if fade_facecolor:
            df['FaceColor'] = df['FaceColor'].apply(hnelib.plt.color.set_alpha)

        scatter_kwargs['edgecolor'] = df['Color']
        scatter_kwargs['facecolor'] = df['FaceColor']

    for _, rows in df.groupby(groupby_cols):
        if sort_cols:
            rows = rows.sort(by=sort_cols)

        row_line_kwargs = line_kwargs.copy()

        if 'Color' in rows.columns:
            row_line_kwargs['color'] = rows.iloc[0]['Color']

        ax.plot(
            rows['X'],
            rows['Y'],
            **row_line_kwargs,
        )

    ax.scatter(
        df['X'],
        df['Y'],
        **{
            **scatter_kwargs,
            'color': 'white',
        }
    )

    ax.scatter(
        df['X'],
        df['Y'],
        **scatter_kwargs,
    )

#
# def plot_disconnected_scatter(ax, df, x_column, y_column, color, s=4, lw=1.5):
#     df = df.copy()
#     df = df.sort_values(by=x_column)
#     faded_color = hnelib.plt.color.set_alpha(color, .75)
#
#     big_s = s * 2
#     small_s = s - 3
#
#     ax.plot(
#         df[x_column],
#         df[y_column],
#         color=color,
#         lw=1,
#         zorder=1,
#     )
#
#     ax.scatter(
#         df[x_column],
#         df[y_column],
#         color='white',
#         zorder=2,
#         s=big_s,
#     )
#
#     ax.scatter(
#         df[x_column],
#         df[y_column],
#         color=color,
#         zorder=2,
#         s=s,
#     )
#
#     ax.scatter(
#         df[x_column],
#         df[y_column],
#         color='w',
#         zorder=2,
#         marker='.',
#         s=small_s,
#     )
