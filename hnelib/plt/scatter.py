import hnelib.pd.util

import hnelib.plt.color
import hnelib.plt.axes


LINEWIDTH = .65
S = 12
LINE_ZORDER = 1
SCATTER_ZORDER = 2


def categorical(
    ax,
    df,
    val_col,
    order_col=None,
    color_col=None,
    edgecolor_col=None,
    facecolor_col=None,
    error_col=None,
    errorcolor_col=None,
    label_col=None,
    label_color_col=None,
    size_col=None,
    fade_facecolor=True,
    zorder=2,
    s=200,
    set_ticks=True,
    **kwargs,
):
    df = hnelib.pd.util.rename_df(df, {
        'Val': val_col,
        'Order': order_col,
        'Color': color_col,
        'EdgeColor': edgecolor_col,
        'FaceColor': facecolor_col,
        'ErrorColor': errorcolor_col,
        'Label': label_col,
        'LabelColor': label_color_col,
        'Error': error_col,
        'Size': size_col,
    })

    cols = df.columns

    if 'Order' not in cols:
        df = df.sort_values(by=['Val'])
        df['Order'] = [i for i in range(len(df))]

    orders = sorted(df['Order'].unique())
    df['X'] = df['Order'].apply(orders.index)

    if 'Color' not in cols:
        if 'EdgeColor' in cols:
            df['Color'] = df['EdgeColor']
        elif 'FaceColor' in cols:
            df['Color'] = df['FaceColor']

    if {'Color', 'EdgeColor', 'FaceColor'} & set(cols):
        if 'FaceColor' not in cols:
            df['FaceColor'] = df['Color']

        if fade_facecolor:
            df['FaceColor'] = df['FaceColor'].apply(hnelib.plt.color.set_alpha)

        kwargs['edgecolor'] = df['EdgeColor'] if 'EdgeColor' in cols else df['Color']
        kwargs['color'] = df['FaceColor']

    kwargs['zorder'] = kwargs.get('zorder', zorder)
    kwargs['s'] = df['Size'] if 'Size' in cols else s

    ax.scatter(
        df['X'],
        df['Val'],
        **kwargs,
    )

    if 'Error' in cols:
        errorbar_kwargs = {}

        errorbar_kwargs['zorder'] = errorbar_kwargs.get('zorder', zorder)
        errorbar_kwargs['ecolor'] = df['ErrorColor'] if 'ErrorColor' in cols else kwargs['edgecolor']

        ax.errorbar(
            df['X'],
            df['Val'],
            fmt='none',
            yerr=df['Error'],
            **errorbar_kwargs,
        )

    ax.set_xlim(-.5, max(orders) + .5)

    if set_ticks:
        hnelib.plt.axes.set_x_text(
            ax,
            df,
            tick_col='X',
            label_col='Label',
            color_col='LabelColor',
        )


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
