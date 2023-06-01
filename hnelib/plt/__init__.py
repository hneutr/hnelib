#------------------------------------------------------------------------------#
# TODO
# ----
# 1. fix DIMS to be (#rows, #cols) and match plt.subplots
# 2. make "subplots" function
# 3. move functions from:
#   - leagalize.plot.util:
#       - bar_plot
#       - box_plot
#       - stacked_hbar_plot
#   - usfhn.standard_plots:
#       - tadpole_plot (plot_connected_two_values_by_taxonomy_level)
#       - connected_scatter (draw_lines_for_change_plot)
#------------------------------------------------------------------------------#
import numpy as np
import pandas as pd

import hnelib.pd.util

import matplotlib.patches as patches

from hnelib.plt.constants import *
import hnelib.plt.color
import hnelib.plt.axes
import hnelib.plt.lim
import hnelib.plt.grid
import hnelib.plt.legend
import hnelib.plt.text


#------------------------------------------------------------------------------#
#                                                                              #
#                              plotting functions                              #
#                                                                              #
#------------------------------------------------------------------------------#
def plot_connected_scatter(ax, df, x_column, y_column, color, s=12, lw=.65):
    df = df.copy()
    df = df.sort_values(by=x_column)
    faded_color = hnelib.plt.color.set_alpha(color)

    ax.plot(
        df[x_column],
        df[y_column],
        color=color,
        zorder=1,
        lw=lw,
    )

    ax.scatter(
        df[x_column],
        df[y_column],
        color='white',
        zorder=2,
        s=s,
        lw=lw,
    )

    ax.scatter(
        df[x_column],
        df[y_column],
        facecolor=faded_color,
        edgecolor=color,
        zorder=2,
        s=s,
        lw=lw,
    )

def plot_disconnected_scatter(ax, df, x_column, y_column, color, s=4, lw=1.5):
    df = df.copy()
    df = df.sort_values(by=x_column)
    faded_color = hnelib.plt.color.set_alpha(color, .75)

    big_s = s * 2
    small_s = s - 3

    ax.plot(
        df[x_column],
        df[y_column],
        color=color,
        lw=1,
        zorder=1,
    )

    ax.scatter(
        df[x_column],
        df[y_column],
        color='white',
        zorder=2,
        s=big_s,
    )

    ax.scatter(
        df[x_column],
        df[y_column],
        color=color,
        zorder=2,
        s=s,
    )

    ax.scatter(
        df[x_column],
        df[y_column],
        color='w',
        zorder=2,
        marker='.',
        s=small_s,
    )


def bar(
    ax,
    df,
    # bar
    size_col,
    stretch_col=None,
    place_col=None,
    bar_col=None,
    bar_color_col=None,
    bar_edge_color_col=None,
    bar_hatch_col=None,
    bar_annotation_col=None,
    annotate_bar_col=None,
    fade_bar_facecolor=True,
    # stack
    stack_col=None,
    # group
    group_col=None,
    group_pad=.5,
    separate_groups=True,
    # tick
    tick_label_col=None,
    tick_color_col=None,
    add_tick_col=None,
    # etc
    horizontal=False,
    **kwargs,
):
    """
    - bars:
    - stacks
    - groups
    
    |  D E
    | BD EG
    |ABC EFH
     -------
      1   2

    bars: A, B, C, D, E, F, G, H

    groups:
    - 1: A, B, C, D 
    - 2: E, F, G, G
    
    stacks:
    - A
    - B
    - C, D
    - E
    - F, G
    - H
    """
    if horizontal:
        draw = ax.barh
        axline = ax.axhline
        set_lim = ax.set_ylim
        set_text = hnelib.plt.axes.set_y_text
        bar_start_key = 'left'
        stretch_key = 'height'
        annotation_x_key = 'Size'
        annotation_y_key = 'Place'
    else:
        draw = ax.bar
        axline = ax.axvline
        set_lim = ax.set_xlim
        set_text = hnelib.plt.axes.set_x_text
        bar_start_key = 'bottom'
        stretch_key = 'width'
        annotation_x_key = 'Place'
        annotation_y_key = 'Size'

    df = hnelib.pd.util.rename_df(df, {
        'Size': size_col,
        'Stretch': stretch_col,
        'Place': place_col,
        'Bar': bar_col,
        'BarColor': bar_color_col,
        'BarEdgeColor': bar_edge_color_col,
        'BarHatch': bar_hatch_col,
        'BarAnnotation': bar_annotation_col,
        'AnnotateBar': annotate_bar_col,
        # stack args
        'Stack': stack_col,
        # group args
        'Group': group_col,
        # label args
        'TickLabel': tick_label_col,
        'TickColor': tick_color_col,
        'AddTick': add_tick_col,
    })

    cols = df.columns
    group_pad = group_pad if 'Group' in cols else 0

    if 'Bar' not in cols:
        df['Bar'] = [i for i in range(len(df))]

    bars = sorted(df['Bar'].unique())
    df['Bar'] = df['Bar'].apply(bars.index)

    if 'Stack' not in cols:
        df['Stack'] = df['Bar']

    stacks = sorted(df['Stack'].unique())
    df['Stack'] = df['Stack'].apply(stacks.index)

    if 'Group' not in cols:
        df['Group'] = 0

    groups = sorted(df['Group'].unique())
    df['Group'] = df['Group'].apply(groups.index)

    group_size = group_pad + df['Stack'].nunique()

    if 'Place' not in cols:
        df['Place'] = df['Group'] * group_size + group_pad + df['Stack']

    bar_starts = []
    for (group_order, stack_order), bars in df.groupby(['Group', 'Stack']):
        bar_start = 0
        for i, row in bars.sort_values(by='Bar').iterrows():
            bar_starts.append({
                'Group': group_order,
                'Stack': stack_order,
                'Bar': row['Bar'],
                'BarStart': bar_start,
            })

            bar_start += row['Size']

    df = df.merge(
        pd.DataFrame(bar_starts),
        on=[
            'Bar',
            'Stack',
            'Group',
        ]
    )

    kwargs[bar_start_key] = df['BarStart']

    if 'BarColor' in cols:
        df['FaceColor'] = df['BarColor']

        if fade_bar_facecolor:
            df['FaceColor'] = df['FaceColor'].apply(hnelib.plt.color.set_alpha)

        kwargs['edgecolor'] = df['BarEdgeColor'] if 'BarEdgeColor' in cols else df['BarColor']
        kwargs['color'] = df['FaceColor']

    if 'BarHatch' in cols:
        kwargs['hatch'] = df['BarHatch']

    if 'Stretch' in cols:
        kwargs[stretch_key] = df['Stretch']

    draw(
        df['Place'],
        df['Size'],
        zorder=2,
        **kwargs,
    )

    if 'BarAnnotation' in cols:
        annotations = df.copy()

        if 'AnnotateBar' in cols:
            annotations = annotations[
                annotations['AnnotateBar']
            ]

        annotations['Size'] /= 2
        annotations['Size'] += annotations['BarStart']

        for i, row in annotations.iterrows():
            ax.annotate(
                row['BarAnnotation'],
                (row[annotation_x_key], row[annotation_y_key]),
                ha='center',
                va='center',
                zorder=3,
                fontsize=font.size['annotation'],
            )

    if 'TickLabel' in cols:
        tick_labels_df = df.copy()

        if 'AddTick' in tick_labels_df.columns:
            tick_labels_df = tick_labels_df[
                tick_labels_df['AddTick']
            ]

        tick_labels_df['Tick'] = tick_labels_df.groupby('TickLabel')['Place'].transform('mean')

        set_text(
            ax,
            tick_labels_df,
            tick_col='Tick',
            tick_label_col='TickLabel',
            tick_color_col='TickColor',
        )

    margin = max(.5, 1.5 * group_pad)

    if len(df):
        set_lim(min(df['Place']) - margin, max(df['Place']) + margin,)

    if separate_groups:
        for group in sorted(df['Group'].unique()):
            if not group:
                continue

            place = group * group_size - group_pad / 2

            axline(
                place,
                color=colors['-'],
                lw=.5,
                zorder=0,
            )

    return df

def rect_bar(
    ax,
    df,
    # bar
    size_col,
    stretch_col=None,
    position_col=None,
    bar_col=None,
    color_col=None,
    edge_color_col=None,
    hatch_col=None,
    annotation_col=None,
    annotate_col=None,
    fade_facecolor=True,
    # stack
    stack_col=None,
    # group
    group_col=None,
    group_pad=.5,
    separate_groups=True,
    # tick
    tick_label_col=None,
    tick_color_col=None,
    add_tick_col=None,
    # etc
    horizontal=False,
    **kwargs,
):
    """
    - bars:
    - stacks
    - groups
    
    |  D E
    | BD EG
    |ABC EFH
     -------
      1   2

    bars: A, B, C, D, E, F, G, H

    groups:
    - 1: A, B, C, D 
    - 2: E, F, G, G
    
    stacks:
    - A
    - B
    - C, D
    - E
    - F, G
    - H
    """
    if horizontal:
        draw = ax.barh
        axline = ax.axhline
        set_lim = ax.set_ylim
        set_text = hnelib.plt.axes.set_y_text
        # bar_start_key = 'left'
        annotation_x_key = 'Size'
        annotation_y_key = 'Position'
        width_col, height_col = 'Size', 'Stretch'
    else:
        draw = ax.bar
        axline = ax.axvline
        set_lim = ax.set_xlim
        set_text = hnelib.plt.axes.set_x_text
        # bar_start_key = 'bottom'
        annotation_x_key = 'Position'
        annotation_y_key = 'Size'
        width_col, height_col = 'Stretch', 'Size'

    df = hnelib.pd.util.rename_df(df, {
        'Size': size_col,
        'Stretch': stretch_col,
        'Position': position_col,
        'Bar': bar_col,
        'Color': color_col,
        'EdgeColor': edge_color_col,
        'Hatch': hatch_col,
        'Annotation': annotation_col,
        'Annotate': annotate_col,
        # stack args
        'Stack': stack_col,
        # group args
        'Group': group_col,
        # label args
        'TickLabel': tick_label_col,
        'TickColor': tick_color_col,
        'AddTick': add_tick_col,
    })

    cols = df.columns
    group_pad = group_pad if 'Group' in cols else 0

    if 'Bar' not in cols:
        df['Bar'] = [i for i in range(len(df))]

    bars = sorted(df['Bar'].unique())
    df['Bar'] = df['Bar'].apply(bars.index)

    if 'Stack' not in cols:
        df['Stack'] = df['Bar']

    stacks = sorted(df['Stack'].unique())
    df['Stack'] = df['Stack'].apply(stacks.index)

    if 'Group' not in cols:
        df['Group'] = 0

    groups = sorted(df['Group'].unique())
    df['Group'] = df['Group'].apply(groups.index)

    group_size = group_pad + df['Stack'].nunique()

    if 'Position' not in cols:
        df['Position'] = df['Group'] * group_size + group_pad + df['Stack']

    starts = []
    for (group_order, stack_order), bars in df.groupby(['Group', 'Stack']):
        start = 0
        for i, row in bars.sort_values(by='Bar').iterrows():
            starts.append({
                'Group': group_order,
                'Stack': stack_order,
                'Bar': row['Bar'],
                'Start': start,
            })

            start += row['Size']

    df = df.merge(
        pd.DataFrame(starts),
        on=[
            'Bar',
            'Stack',
            'Group',
        ]
    )

    # kwargs[bar_start_key] = df['Start']

    if 'Color' in cols:
        df['FaceColor'] = df['Color']

        if fade_facecolor:
            df['FaceColor'] = df['FaceColor'].apply(hnelib.plt.color.set_alpha)

        kwargs['edgecolor'] = df['EdgeColor'] if 'EdgeColor' in cols else df['Color']
        kwargs['color'] = df['FaceColor']

    if 'Hatch' in cols:
        kwargs['hatch'] = df['Hatch']

    if 'Stretch' not in cols:
        df['Stretch'] = 0.8

    if horizontal:
        df['X'] = df['Start']
        df['Y'] = df['Position']
        df['Y'] -= df[height_col] / 2
    else:
        df['X'] = df['Position']
        df['X'] -= df[width_col] / 2
        df['Y'] = df['Start']

    for (group, stack, bar), rows in df.groupby(['Group', 'Stack', 'Bar']):
        bar = rows.iloc[0]

        rect = patches.Rectangle(
            (bar['X'], bar['Y']),
            bar[width_col],
            bar[height_col],
            **kwargs,
            clip=False,
            # linewidth=1,
            # edgecolor='r',
            # facecolor='none'
        )
    # ax.add_patch(rect)

    # draw(
    #     df['Position'],
    #     df['Size'],
    #     zorder=2,
    #     **kwargs,
    # )

    if 'Annotation' in cols:
        annotations = df.copy()

        if 'Annotate' in cols:
            annotations = annotations[
                annotations['Annotate']
            ]

        annotations['Size'] /= 2
        annotations['Size'] += annotations['Start']

        for i, row in annotations.iterrows():
            ax.annotate(
                row['Annotation'],
                (row[annotation_x_key], row[annotation_y_key]),
                ha='center',
                va='center',
                zorder=3,
                fontsize=font.size['annotation'],
            )

    if 'TickLabel' in cols:
        tick_labels_df = df.copy()

        if 'AddTick' in tick_labels_df.columns:
            tick_labels_df = tick_labels_df[
                tick_labels_df['AddTick']
            ]

        tick_labels_df['Tick'] = tick_labels_df.groupby('TickLabel')['Position'].transform('mean')

        set_text(
            ax,
            tick_labels_df,
            tick_col='Tick',
            tick_label_col='TickLabel',
            tick_color_col='TickColor',
        )

    margin = max(.5, 1.5 * group_pad)

    if len(df):
        set_lim(min(df['Position']) - margin, max(df['Position']) + margin,)

    if separate_groups:
        for group in sorted(df['Group'].unique()):
            if not group:
                continue

            place = group * group_size - group_pad / 2

            axline(
                place,
                color=colors['-'],
                lw=.5,
                zorder=0,
            )

    return df
