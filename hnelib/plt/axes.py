import hnelib.util
import hnelib.pd.util

from hnelib.plt.constants import *


def _ax_fn(ax, fn_suffix, axis='x', fn_prefix='get'):
    return getattr(ax, f"{fn_prefix}_{axis}{fn_suffix}", None)


def get_fn(ax, fn_suffix, axis='x'):
    return _ax_fn(ax, fn_suffix=fn_suffix, axis=axis, fn_prefix='get')


def set_fn(ax, fn_suffix, axis='x'):
    return _ax_fn(ax, fn_suffix=fn_suffix, axis=axis, fn_prefix='set')


def hide(ax):
    ax.set_frame_on(False)
    ax.set_xticks([])
    ax.set_yticks([])


def label_subplots(
    axes,
    x_pads,
    y_pad=1.15,
    labels=[],
    horizontal_alignments=[],
    fontsize=font.size['subplot_label'],
    fontweight=font.weight['subplot_label'],
    fontname=font.name['subplot_label'],
):
    import string

    if not horizontal_alignments:
        horizontal_alignments = ['left' for i in range(len(axes))]

    if not labels:
        labels = list(string.ascii_uppercase)[:len(axes)]

    for ax, label, x_pad, ha in zip(axes, labels, x_pads, horizontal_alignments):
        ax.text(
            x_pad,
            y_pad,
            label.lower(),
            transform=ax.transAxes,
            fontname=fontname,
            fontsize=fontsize,
            fontweight=fontweight,
            va='top',
            ha=ha,
        )


def set_axis_text(
    ax,
    df,
    tick_col=None,,
    tick_color_col=None,
    label=None,
    label_color=None,
    which='x',
):
    df = hnelib.pd.util.rename_df(df, {
        'Tick': tick_col,
        'TickColor': tick_color_col,
        'Label': label_col,
    })

    ticks = df['Tick'] if 'Tick' in df.columns else []
    set_fn(ax, fn_suffix='ticks', axis=which)(ticks)

    if 'TickColor' in df.columns and ticks:
        ticklabels = get_fn(ax, fn_suffix='ticklabels', axis=which)()
        for color, tick in zip(df['Color'], ticklabels):
            tick.set_color(color)

    if label:
        set_fn(ax, fn_suffix='ticklabels', axis=which)(label)

        if label_color:
            ax.tick_params(axis=which, colors=label_color)


def set_x_text(*args, **kwargs):
    set_axis_text(*args, which='x', **kwargs)


def set_y_text(*args, **kwargs):
    set_axis_text(*args, which='y', **kwargs)


def set_label_size(axes, size=font.size['axis_label']):
    for ax in hnelib.util.as_list(axes):
        for axis in ['x', 'y']:
            label = get_fn(ax, 'label', axis=axis)()

            if label:
                set_fn(ax, 'label', axis=axis)(label, size=size)


def set_ticklabel_size(axes, axis='both', which='major', size=font.size['tick']):
    for ax in hnelib.util.as_list(axes):
        ax.tick_params(axis=axis, which=which, labelsize=size)


def finalize(
    axes,
    label_x_pads=[],
    label_y_pad=1.15,
):
    if label_x_pads:
        label_subplots(axes, label_x_pads, y_pad=label_y_pad)

    set_label_size(axes)
    set_ticklabel_size(axes)
