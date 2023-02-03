import pandas as pd

import hnelib.pd.util

import hnelib.plt.color
import hnelib.plt.axes

#------------------------------------------------------------------------------#
#                                     bar                                      #
#------------------------------------------------------------------------------#
def do(
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
            df['FaceColor'] = df['FaceColor'].apply(hnelib.plt.color.set_alpha)

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


def stacked(
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

def grouped(
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

        hnelib.plt.axes.set_x_text(
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
            color=colors['-'],
            lw=.5,
            zorder=0,
        )
