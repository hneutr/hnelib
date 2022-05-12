import numpy as np
import itertools
from scipy.stats import gaussian_kde, pearsonr, spearmanr
import matplotlib.colors


COLORS = {
    'dark_gray': '#5E5E5E',
}

DIMENSIONS = {
    'widths': {
        '1column': 5.5,
        '2column': 11,
    },
    'heights': {
        'standard': 5.5,
    },
}


FONTSIZES = {
    'axis': 13,
    'tick': 11,
    'annotation': 7,
    'annotation-l': 9,
    'annotation-xl': 10,
}


BASIC_ARROW_PROPS = {
    'lw': .5,
    'color': COLORS['dark_gray'],
    'arrowstyle': '->',
}

ZERO_SHRINK_A_ARROW_PROPS = {
    **BASIC_ARROW_PROPS,
    'shrinkA': 0,
}

HEADLESS_ARROW_PROPS = {
    'lw': .5,
    'color': COLORS['dark_gray'],
    'arrowstyle': '-',
    'shrinkA': 0,
    'shrinkB': 0,
}


def set_alpha_on_colors(colors, alpha=.25):
    """
    takes colors (single or list) and applies an alpha to them.
    """
    if isinstance(colors, list):
        return [matplotlib.colors.to_rgba(c, alpha) for c in colors]
    else:
        return matplotlib.colors.to_rgba(colors, alpha)


def annotate(ax, text, xy_loc=(.1, .9), annotate_kwargs={}):
    x_fraction, y_fraction = xy_loc
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    x = x_min + x_fraction * (x_max - x_min)
    y = y_min + y_fraction * (y_max - y_min)

    ax.annotate(
        text,
        (x, y),
        va='center',
        ha='left',
        annotation_clip=False,
        **annotate_kwargs,
    )


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

def get_max_lims(axes):
    xlims = list(itertools.chain.from_iterable([ax.get_xlim() for ax in axes]))
    ylims = list(itertools.chain.from_iterable([ax.get_ylim() for ax in axes]))
    return min(xlims), max(xlims), min(ylims), max(ylims)


def set_lims_to_max(axes, x=True, y=True):
    x_min, x_max, y_min, y_max = get_max_lims(axes)
    for ax in axes:
        if x:
            ax.set_xlim(x_min, x_max)
        if y:
            ax.set_ylim(y_min, y_max)


def square_axis(ax):
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    max_max = max(x_max, y_max)
    min_min = max(x_min, y_min)

    ax.set_xlim(min_min, max_max)
    ax.set_ylim(min_min, max_max)


def add_gridlines_on_ticks(ax, x=True, y=True, **kwargs):
    xs = ax.get_xticks() if x else []
    ys = ax.get_yticks() if y else []

    add_gridlines(ax, xs=xs, ys=ys, **kwargs)


def add_gridlines(ax, xs=[], ys=[], color=COLORS['dark_gray'], zorder=1, alpha=.5, lw=1, **kwargs):
    """
    adds gridlines to the plot
    """
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    for x in xs:
        ax.axvline(
            x,
            color=color,
            zorder=zorder,
            alpha=.5,
            lw=lw,
            **kwargs,
        )

    for y in ys:
        ax.axhline(
            y,
            color=color,
            zorder=zorder,
            alpha=.5,
            lw=lw,
            **kwargs,
        )

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)


def hide_axis(ax):
    ax.set_frame_on(False)
    ax.set_xticks([])
    ax.set_yticks([])


def stringify_numbers_without_ugly_zeros(numbers):
    strings = []
    for number in numbers:
        string = str(number)

        prefix = ''
        if '-' in string:
            string = string.replace('-', '')
            prefix = '-'

        if '.' in string:
            string, decimal_part = str(string).split('.')

            string = "." if string == "0" else f"{string}"

            if decimal_part != '0':
                if '.' not in string:
                    string += '.'

                string += f'{decimal_part}'

        string = prefix + string

        strings.append(string)

    return strings


def plot_connected_scatter(ax, df, x_column, y_column, color, s=30):
    df = df.copy()
    df = df.sort_values(by=x_column)
    faded_color = set_alpha_on_colors(color)

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
        s=s,
    )

    ax.scatter(
        df[x_column],
        df[y_column],
        facecolor=faded_color,
        edgecolor=color,
        zorder=2,
        s=s,
    )

def plot_disconnected_scatter(ax, df, x_column, y_column, color, s=4, lw=1.5):
    df = df.copy()
    df = df.sort_values(by=x_column)
    faded_color = set_alpha_on_colors(color, .75)

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


def annotate_plot_letters(axes, x_pads, y_pad=1.15, fontsize=18, labels=[], horizontal_alignments=[]):
    import string

    if not horizontal_alignments:
        horizontal_alignments = ['left' for i in range(len(axes))]

    if not labels:
        labels = list(string.ascii_uppercase)[:len(axes)]

    for ax, label, x_pad, ha in zip(axes, labels, x_pads, horizontal_alignments):
        ax.text(
            x_pad,
            y_pad,
            label,
            transform=ax.transAxes,
            fontname='Arial',
            fontsize=fontsize,
            fontweight='bold',
            va='top',
            ha=ha,
        )


def set_label_fontsize(axes, fontsize):
    for ax in axes:
        ylabel = ax.get_ylabel()

        if ylabel:
            ax.set_ylabel(ylabel, size=fontsize)

        xlabel = ax.get_xlabel()

        if xlabel:
            ax.set_xlabel(xlabel, size=fontsize)


def set_ticklabel_fontsize(axes, fontsize):
    for ax in axes:
        ax.tick_params(axis='both', which='major', labelsize=fontsize)


def finalize(
    axes,
    plot_label_x_pads=[],
    plot_label_y_pad=1.15,
    axis_fontsize=FONTSIZES['axis'],
    tick_fontsize=FONTSIZES['tick'],
):
    if not isinstance(axes, list) and not isinstance(axes, np.ndarray):
        axes = [axes]

    if plot_label_x_pads:
        annotate_plot_letters(axes, plot_label_x_pads, y_pad=plot_label_y_pad)

    set_label_fontsize(axes, fontsize=axis_fontsize)
    set_ticklabel_fontsize(axes, fontsize=tick_fontsize)
