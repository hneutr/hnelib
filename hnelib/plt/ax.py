import hnelib.utils
import hnelib.pd.util
import hnelib.plt.font as font

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

def add_subplot_labels(
    axes,
    x_pads,
    y_pad=1.15,
    size=font.S['subplot-label'],
    labels=[],
    horizontal_alignments=[],
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
            fontname='Arial',
            fontsize=fontsize,
            fontweight='bold',
            va='top',
            ha=ha,
        )



def set_axis_text(
    ax,
    df,
    tick_col,
    label_col=None,
    color_col=None,
    which='x',
):
    df = hnelib.pd.util.rename_df(df, {
        'Tick': tick_col,
        'Label': label_col,
        'Color': color_col,
    })

    set_fn(ax, fn_suffix='ticks', axis=which)(df['Tick'])

    if 'Label' in df.columns:
        set_fn(ax, fn_suffix='ticklabels', axis=which)(df['Label'])

    if 'Color' in df.columns:
        ticklabels = get_fn(ax, fn_suffix='ticklabels', axis=which)()
        for color, tick in zip(df['Color'], ticklabels):
            tick.set_color(color)

def set_x_text(*args, **kwargs):
    set_axis_text(*args, which='x', **kwargs)


def set_y_text(*args, **kwargs):
    set_axis_text(*args, which='y', **kwargs)


def set_label_size(axes, size=font.S['axis']):
    for ax in hnelib.utils.as_list(axes):
        for axis in ['x', 'y']:
            label = get_fn(ax, 'label', axis=axis)()

            if label:
                set_fn(ax, 'label', axis=axis)(label, size=size)


def set_ticklabel_size(axes, size=font.S['tick']):
    for ax in hnelib.utils.as_list(axes):
        ax.tick_params(axis='both', which='major', labelsize=size)


def finalize(
    axes,
    label_x_pads=[],
    label_y_pad=1.15,
    axis_size=font.S['axis'],
    tick_size=font.S['tick'],
    label_size=font.S['subplot-label'],
):
    if label_x_pads:
        add_subplot_labels(axes, label_x_pads, y_pad=label_y_pad, size=label_size)

    set_label_size(axes, size=axis_size)
    set_ticklabel_size(axes, size=tick_size)
