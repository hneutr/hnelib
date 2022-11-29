#------------------------------------------------------------------------------#
# TODO
# ----
# 1. fix DIMS to be (#rows, #cols) and match plt.subplots
# 2. make "subplots" function
# 3. move functions from:
#   - leagalize.plot.utils:
#       - bar_plot
#       - box_plot
#       - stacked_hbar_plot
#   - usfhn.standard_plots:
#       - tadpole_plot (plot_connected_two_values_by_taxonomy_level)
#       - connected_scatter (draw_lines_for_change_plot)
#------------------------------------------------------------------------------#
import numpy as np
import pandas as pd
import itertools
from scipy.stats import pearsonr

import hnelib.pd.util

import hnelib.plt.dims as dims
import hnelib.plt.font
import hnelib.plt.ax


def annotate_pearson(ax, xs, ys, xy_loc=(.1, .9), annotate_kwargs={}):
    x_fraction, y_fraction = xy_loc
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    x = x_min + x_fraction * (x_max - x_min)
    y = y_min + y_fraction * (y_max - y_min)

    pearson, pearson_p = pearsonr(xs, ys)
    ax.annotate(
        f"\tpearson: {round(pearson, 2)}",
        (x, y),
        va='center',
        ha='left',
        annotation_clip=False,
        **annotate_kwargs,
    )


def text_fraction_label(numerator, denominator, convert_hyphens=True):
    text = r"$\frac{\mathrm{" + numerator + "}}{\mathrm{" + denominator + "}}$"

    text = text.replace(' ', '\ ')

    if convert_hyphens:
        text = text.replace("-", u"\u2010")

    return text


#------------------------------------------------------------------------------#
#                                                                              #
#                              plotting functions                              #
#                                                                              #
#------------------------------------------------------------------------------#
def plot_connected_scatter(ax, df, x_column, y_column, color, s=12, lw=.65):
    df = df.copy()
    df = df.sort_values(by=x_column)
    faded_color = hnelib.color.set_alpha(color)

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
    faded_color = hnelib.color.set_alpha(color, .75)

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


#------------------------------------------------------------------------------#
#                                     bar                                      #
#------------------------------------------------------------------------------#
def bar_plot(
    ax,
    df,
    val_col,
    x_col=None,
    color_col=None,
    hatch_col=None,
    label_col=None,
    label_color_col=None,
    annotation_col=None,
    annotate_col=None,
    bottom_col=None,
    fade_facecolor=True,
    draw_kwargs={},
):
    df = hnelib.pd.util.rename_df(df, {
        'Y': val_col,
        'X': x_col,
        'Color': color_col,
        'Hatch': hatch_col,
        'Label': label_col,
        'LabelColor': label_color_col,
        'Annotation': annotation_col,
        'Annotate': annotate_col,
        'Bottom': bottom_col,
    })

    if 'X' not in df.columns:
        df['X'] = [i for i in range(len(df))]

    if 'Color' in df.columns:
        df['FaceColor'] = df['Color']

        if fade_facecolor:
            df['FaceColor'] = df['FaceColor'].apply(hnelib.color.set_alpha)

        draw_kwargs['edgecolor'] = df['Color']
        draw_kwargs['color'] = df['FaceColor']

    if 'Hatch' in df.columns:
        draw_kwargs['color'] = 'none'
        draw_kwargs['hatch'] = df['Hatch']

    if 'Bottom' in df.columns:
        draw_kwargs['bottom'] = df['Bottom']

    ax.bar(
        df['X'],
        df['Y'],
        zorder=2,
        **draw_kwargs,
    )

    if 'Annotation' in df.columns:
        annotations = df.copy()

        if 'Annotate' in annotations.columns:
            annotations = annotations[
                annotations['Annotate']
            ]

        annotations['Y'] /= 2

        if 'Bottom' in annotations.columns:
            annotations['Y'] += annotations['Bottom']

        for i, row in annotations.iterrows():
            ax.annotate(
                row['Annotation'],
                (row['X'], row['Y']),
                ha='center',
                va='center',
                zorder=3,
            )

    if 'Label' in df.columns:
        ax.set_xticks(df['X'])
        ax.set_xticklabels(df['Label'])

        if 'LabelColor' in df.columns:
            for color, tick in zip(list(df['LabelColor']), ax.get_xticklabels()):
                tick.set_color(color)

    if len(df):
        ax.set_xlim(-.5, len(df) -.5)


def stacked_bar_plot(
    ax,
    df,
    val_col,
    bar_col,
    stack_col,
    bar_order_col=None,
    bar_color_col=None,
    bar_hatch_col=None,
    bar_annotation_col=None,
    annotate_bar_col=None,
    stack_x_col=None,
    stack_label_col=None,
    stack_label_color_col=None,
    fade_bar_facecolor=True,
    draw_kwargs={},
):
    df = hnelib.pd.util.rename_df(df, {
        'Value': val_col,
        'Bar': bar_col,
        'BarOrder': bar_order_col,
        'BarColor': bar_color_col,
        'BarHatch': bar_hatch_col,
        'BarAnnotation': bar_annotation_col,
        'AnnotateBar': annotate_bar_col,
        'Stack': stack_col,
        'StackX': stack_x_col,
        'StackLabel': stack_label_col,
        'StackLabelColor': stack_label_color_col,
    })

    if 'StackX' not in df.columns:
        stacks = sorted(list(df['Stack'].unique()))
        df['StackX'] = df['Stack'].apply(stacks.index)

    if 'BarOrder' not in df.columns:
        bars = sorted(list(df['Bar'].unique()))
        df['BarOrder'] = df['Bar'].apply(bars.index)

    bottoms = []
    for stack, bars in df.groupby('Stack'):
        bottom = 0
        for i, row in bars.sort_values(by='BarOrder').iterrows():
            bottoms.append({
                'Stack': stack,
                'Bar': row['Bar'],
                'Bottom': bottom,
            })

            bottom += row['Value']

    df = df.merge(
        pd.DataFrame(bottoms),
        on=[
            'Bar',
            'Stack',
        ]
    )

    for bar_index, bars in df.groupby('BarOrder'):
        bar_plot(
            ax,
            bars,
            val_col='Value',
            x_col='StackX',
            color_col='BarColor',
            hatch_col='BarHatch',
            label_col='StackLabel',
            label_color_col='StackLabelColor',
            annotation_col='BarAnnotation',
            annotate_col='AnnotateBar',
            bottom_col='Bottom',
            fade_facecolor=fade_bar_facecolor,
            draw_kwargs=draw_kwargs,
        )

def grouped_bar_plot(
    ax,
    df,
    val_col,
    bar_col,
    group_col,
    bar_order_col=None,
    bar_color_col=None,
    bar_hatch_col=None,
    bar_annotation_col=None,
    annotate_bar_col=None,
    group_order_col=None,
    group_label_col=None,
    group_label_color_col=None,
    fade_bar_facecolor=True,
    group_pad=.5,
    draw_kwargs={},
):
    df = hnelib.pd.util.rename_df(df, {
        'Value': val_col,
        'Bar': bar_col,
        'BarOrder': bar_order_col,
        'BarColor': bar_color_col,
        'BarHatch': bar_hatch_col,
        'BarAnnotation': bar_annotation_col,
        'AnnotateBar': annotate_bar_col,
        'Group': group_col,
        'GroupOrder': group_order_col,
        'GroupLabel': group_label_col,
        'GroupLabelColor': group_label_color_col,
    })

    if 'BarOrder' not in df.columns:
        bars = sorted(list(df['Bar'].unique()))
        df['BarOrder'] = df['Bar'].apply(bars.index)


    if 'GroupOrder' not in df.columns:
        groups = sorted(list(df['Group'].unique()))
        df['GroupOrder'] = df['Group'].apply(groups.index)

    group_size = group_pad + df['Bar'].nunique()

    df['GroupXStart'] = df['GroupOrder'] * group_size

    df['X'] = df['GroupXStart'] + group_pad + df['BarOrder']

    bar_plot(
        ax,
        df,
        val_col='Value',
        x_col='X',
        color_col='BarColor',
        hatch_col='BarHatch',
        annotation_col='BarAnnotation',
        annotate_col='AnnotateBar',
        fade_facecolor=fade_bar_facecolor,
        draw_kwargs=draw_kwargs,
    )

    if 'GroupLabel' in df.columns:
        df['GroupTick'] = df.groupby('Group')['X'].transform('mean')

        set_x_text(
            ax,
            df,
            tick_col='GroupTick',
            label_col='GroupLabel',
            color_col='GroupLabelColor',
        )

    ax.set_xlim(min(df['X']) - 1.5 * group_pad, max(df['X']) + 1.5 * group_pad)

    for group in sorted(list(df['Group'].unique())):
        if not group:
            continue

        x = group * group_size - group_pad / 2

        ax.axvline(
            x,
            color=hnelib.color.C['dark_gray'],
            lw=.5,
            zorder=0,
        )


#-------------------------------------------------------------------------------
# TESTING: combo bar plot. supports:
# - bars
# - stacks
# - groups
#-------------------------------------------------------------------------------
# a bar is a rectangle. has:
# - height
# ~ id
# ~ x
# ~ color
# ~ hatch
# ~ bottom
# ~ order
# ~ annotation
# ~ should_annotate

# ~ label
# ~ label color
#-------------------------------------------------------------------------------
# a stack is a vertical grouping of bars. has:
# - id
# ~ x
# ~ order
# 
# ~ label
# ~ label color
#-------------------------------------------------------------------------------
# a group is a horizontal grouping of bars/stacks. has:
# - id
# ~ x
# ~ order
#
# ~ label
# ~ label color

# groups also have:
# ~ group pad
#-------------------------------------------------------------------------------
# labeling logic:
# - if there are groups, label the groups
# - elif there are stacks, label the stacks
# - elif label the bars
#
# additional labels:
# - if groups:
#   - if stacks:
#       - support labelling stacks
#   - support labelling bars
def ultibar_plot(
    ax,
    df,
    # bar args
    bar_height_col,
    bar_col=None,
    bar_order_col=None,
    bar_color_col=None,
    bar_hatch_col=None,
    bar_annotation_col=None,
    annotate_bar_col=None,
    fade_bar_facecolor=True,
    # stack args
    stack_col=None,
    stack_order_col=None,
    # group args
    group_col=None,
    group_order_col=None,
    group_pad=.5,
    # label args
    label_col=None,
    label_color_col=None,
    # etc
    draw_kwargs={},
):
    df = hnelib.pd.util.rename_df(df, {
        'Y': bar_height_col,
        'Bar': bar_col,
        'BarOrder': bar_order_col,
        'BarColor': bar_color_col,
        'BarHatch': bar_hatch_col,
        'BarAnnotation': bar_annotation_col,
        'AnnotateBar': annotate_bar_col,
        # stack args
        'Stack': stack_col,
        'StackOrder': stack_order_col,
        # group args
        'Group': group_col,
        'GroupOrder': group_order_col,
        # label args
        'Label': label_col,
        'LabelColor': label_color_col,
    })

    cols = df.columns
    stacked = 'Stack' in cols
    grouped = 'Group' in cols
    group_pad = group_pad if grouped else 0

    if 'Bar' not in cols:
        df['Bar'] = [i for i in range(len(df))]

    if 'BarOrder' not in cols:
        bars = sorted(df['Bar'].unique())
        df['BarOrder'] = df['Bar'].apply(bars.index)

    if 'Stack' not in cols:
        df['Stack'] = df['Bar']

    bottoms = []
    for stack, bars in df.groupby('Stack'):
        bottom = 0
        for i, row in bars.sort_values(by='BarOrder').iterrows():
            bottoms.append({
                'Stack': stack,
                'Bar': row['Bar'],
                'BarBottom': bottom,
            })

            bottom += row['Y']

    df = df.merge(
        pd.DataFrame(bottoms),
        on=[
            'Bar',
            'Stack',
        ]
    )

    if 'StackOrder' not in cols:
        stacks = sorted(df['Stack'].unique())
        df['StackOrder'] = df['Stack'].apply(stacks.index)

    if 'Group' not in cols:
        df['Group'] = df['Stack']

    if 'GroupOrder' not in cols:
        groups = sorted(df['Group'].unique())
        df['GroupOrder'] = df['Group'].apply(groups.index)

    group_size = group_pad + df['Stack'].nunique()
    df['X'] = df['GroupOrder'] * group_size + group_pad + df['StackOrder']

    if 'Color' in cols:
        df['FaceColor'] = df['Color']

        if fade_facecolor:
            df['FaceColor'] = df['FaceColor'].apply(hnelib.color.set_alpha)

        draw_kwargs['edgecolor'] = df['Color']
        draw_kwargs['color'] = df['FaceColor']

    if 'Hatch' in df.columns:
        draw_kwargs['color'] = 'none'
        draw_kwargs['hatch'] = df['Hatch']

    ax.bar(
        df['X'],
        df['Y'],
        zorder=2,
        bottom=df['BarBottom'],
        **draw_kwargs,
    )

    if 'Annotation' in cols:
        annotations = df.copy()

        if 'Annotate' in cols:
            annotations = annotations[
                annotations['Annotate']
            ]

        annotations['Y'] /= 2
        annotations['Y'] += annotations['BarBottom']

        for i, row in annotations.iterrows():
            ax.annotate(
                row['Annotation'],
                (row['X'], row['Y']),
                ha='center',
                va='center',
                zorder=3,
            )

    if 'Label' in df.columns:
        df['LabelX'] = df.groupby('Group')['X'].transform('mean')

        hnelib.plt.ax.set_x_text(
            ax,
            df,
            tick_col='LabelX',
            label_col='Label',
            color_col='LabelColor',
        )


    margin = max(.5, 1.5 * group_pad)

    if len(df):
        ax.set_xlim(min(df['X']) - margin, max(df['X']) + margin)

    for group in sorted(df['GroupOrder'].unique()):
        if not group:
            continue

        x = group * group_size - group_pad / 2

        ax.axvline(
            x,
            color=hnelib.color.C['dark_gray'],
            lw=.5,
            zorder=0,
        )
