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
    draw_kwargs={},
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
    df = hnelib.pd.util.rename_df(df, {
        'Size': size_col,
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
    stacked = 'Stack' in cols
    grouped = 'Group' in cols
    group_pad = group_pad if grouped else 0

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
    df['Place'] = df['Group'] * group_size + group_pad + df['Stack']

    bottoms = []
    for (group_order, stack_order), bars in df.groupby(['Group', 'Stack']):
        bottom = 0
        for i, row in bars.sort_values(by='Bar').iterrows():
            bottoms.append({
                'Group': group_order,
                'Stack': stack_order,
                'Bar': row['Bar'],
                'BarBottom': bottom,
            })

            bottom += row['Size']

    df = df.merge(
        pd.DataFrame(bottoms),
        on=[
            'Bar',
            'Stack',
            'Group',
        ]
    )

    if 'BarColor' in cols:
        df['FaceColor'] = df['BarColor']

        if fade_bar_facecolor:
            df['FaceColor'] = df['FaceColor'].apply(hnelib.plt.color.set_alpha)

        draw_kwargs['edgecolor'] = df['BarEdgeColor'] if 'BarEdgeColor' in cols else df['BarColor']
        draw_kwargs['color'] = df['FaceColor']

    if 'BarHatch' in df.columns:
        draw_kwargs['hatch'] = df['BarHatch']

    ax.bar(
        df['Place'],
        df['Size'],
        zorder=2,
        bottom=df['BarBottom'],
        **draw_kwargs,
    )

    if 'BarAnnotation' in cols:
        annotations = df.copy()

        if 'AnnotateBar' in cols:
            annotations = annotations[
                annotations['AnnotateBar']
            ]

        annotations['Size'] /= 2
        annotations['Size'] += annotations['BarBottom']

        for i, row in annotations.iterrows():
            ax.annotate(
                row['BarAnnotation'],
                (row['Place'], row['Size']),
                ha='center',
                va='center',
                zorder=3,
                fontsize=font.size['annotation'],
            )

    if 'TickLabel' in df.columns:
        tick_labels_df = df.copy()

        if 'AddTick' in tick_labels_df.columns:
            tick_labels_df = tick_labels_df[
                tick_labels_df['AddTick']
            ]

        tick_labels_df['Tick'] = tick_labels_df.groupby('TickLabel')['Place'].transform('mean')

        hnelib.plt.axes.set_x_text(
            ax,
            tick_labels_df,
            tick_col='Tick',
            tick_label_col='TickLabel',
            tick_color_col='TickColor',
        )

    margin = max(.5, 1.5 * group_pad)

    if len(df):
        ax.set_xlim(min(df['Place']) - margin, max(df['Place']) + margin)

    if separate_groups:
        for group in sorted(df['Group'].unique()):
            if not group:
                continue

            place = group * group_size - group_pad / 2

            ax.axvline(
                place,
                color=colors['-'],
                lw=.5,
                zorder=0,
            )

    return df
