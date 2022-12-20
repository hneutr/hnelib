import functools

from matplotlib.patches import ArrowStyle

from hnelib.plt.color import colors

DEFAULT_ARROW = {
    'linewidth': .45,
    'color': colors['-'],
    'arrowstyle': '->, head_width=.15, head_length=.25',
}

DEFAULT_LINE = {
    **DEFAULT_ARROW,
    'arrowstyle': '-',
    'shrinkA': 0,
    'shrinkB': 0,
}


@functools.lru_cache
def __get_arrows__():
    arrows = {
        '->': DEFAULT_ARROW,
        '-': DEFAULT_LINE,
    }

    for shrinkA, shrinkB in [(0, 0), (0, 1), (1, 0)]:
        shrink_kwargs = {
            'shrinkA': shrinkA,
            'shrinkB': shrinkB,
        }

        label = f"a{' ' * shrinkA}->{' ' * shrinkB}b" 
        arrows[label] = {
            **DEFAULT_ARROW,
            **{k: v for k, v in shrink_kwargs.items() if v == 0}
        }

    return arrows

arrows = __get_arrows__()
