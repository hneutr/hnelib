import numpy as np
import pandas as pd
import itertools
from scipy.stats import gaussian_kde, pearsonr, spearmanr
import matplotlib.colors


WIDTHS = {
    '1-col': 3.54331,
    '2-col': 7.08661,
}


COLORS = {
    'dark_gray': '#5E5E5E',
    'color_1': '#45A1F8',
    'color_2': '#FF6437', 
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
    'small': 5,
    'medium': 6,
    'large': 7,
    'huge': 8,
}


FONTSIZES['axis'] = FONTSIZES['large']
FONTSIZES['tick'] = FONTSIZES['medium']
FONTSIZES['annotation'] = FONTSIZES['small']
FONTSIZES['title'] = FONTSIZES['huge']
FONTSIZES['legend'] = FONTSIZES['medium']
FONTSIZES['subplot-label'] = FONTSIZES['huge']

BASIC_ARROW_PROPS = {
    'lw': .35,
    'color': COLORS['dark_gray'],
    'arrowstyle': '->, head_width=.15, head_length=.21',
}

ZERO_SHRINK_A_ARROW_PROPS = {
    **BASIC_ARROW_PROPS,
    'shrinkA': 0,
}

HEADLESS_ARROW_PROPS = {
    'lw': .35,
    'color': COLORS['dark_gray'],
    'arrowstyle': '-',
    'shrinkA': 0,
    'shrinkB': 0,
}


def set_alpha_on_colors(colors, alpha=.35):
    """
    takes colors (single or list) and applies an alpha to them.
    """
    if isinstance(colors, list):
        return [matplotlib.colors.to_rgba(c, alpha) for c in colors]
    elif isinstance(colors, pd.Series):
        return [matplotlib.colors.to_rgba(c, alpha) for c in list(colors)]
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

def set_lim_to_max(axes, axis='x'):
    get_fns = [getattr(ax, f'get_{axis}lim', None) for ax in axes]

    if all(get_fns):
        lims = list(itertools.chain.from_iterable([get_fn() for get_fn in get_fns]))
        _min, _max = min(lims), max(lims)

        for ax in axes:
            getattr(ax, f'set_{axis}lim')(_min, _max)

def set_lims_to_max(axes, x=True, y=True, z=True):
    if x:
        set_lim_to_max(axes, 'x')

    if y:
        set_lim_to_max(axes, 'y')

    if z:
        set_lim_to_max(axes, 'z')

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


def add_gridlines(ax, xs=[], ys=[], color=COLORS['dark_gray'], zorder=1, alpha=.5, lw=.5, **kwargs):
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

            if decimal_part == "0" and string == "0":
                string = "0"
            else:
                string = "." if string == "0" else f"{string}"

            if decimal_part != '0':
                if '.' not in string:
                    string += '.'

                string += f'{decimal_part}'

        string = prefix + string

        strings.append(string)

    return strings


def plot_connected_scatter(ax, df, x_column, y_column, color, s=12, lw=.65):
    df = df.copy()
    df = df.sort_values(by=x_column)
    faded_color = set_alpha_on_colors(color)

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


def annotate_plot_letters(
    axes,
    x_pads,
    y_pad=1.15,
    fontsize=FONTSIZES['subplot-label'],
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
    plot_letters_fontsize=FONTSIZES['subplot-label'],
):
    if not isinstance(axes, list) and not isinstance(axes, np.ndarray):
        axes = [axes]

    if plot_label_x_pads:
        annotate_plot_letters(axes, plot_label_x_pads, y_pad=plot_label_y_pad, fontsize=plot_letters_fontsize)

    set_label_fontsize(axes, fontsize=axis_fontsize)
    set_ticklabel_fontsize(axes, fontsize=tick_fontsize)


def text_fraction_label(numerator, denominator, convert_hyphens=True):
    text = r"$\frac{\mathrm{" + numerator + "}}{\mathrm{" + denominator + "}}$"

    text = text.replace(' ', '\ ')

    if convert_hyphens:
        text = text.replace("-", u"\u2010")

    return text
