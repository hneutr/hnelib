import hnelib.plt.color

GRID_ZORDER = -1
GRID_LINEWIDTH = .5


def on_ticks(ax, x=True, y=True, **kwargs):
    xs = ax.get_xticks() if x else []
    ys = ax.get_yticks() if y else []

    on_vals(ax, xs=xs, ys=ys, **kwargs)


def on_vals(
    ax,
    xs=[],
    ys=[],
    color=hnelib.plt.color.colors['-'],
    alpha=hnelib.plt.color.alpha,
    zorder=GRID_ZORDER,
    linewidth=GRID_LINEWIDTH,
    **kwargs
):
    """
    adds gridlines to the plot
    """
    kwargs = {
        'color': color,
        'zorder': zorder,
        'alpha': alpha,
        'linewidth': linewidth,
        **kwargs,
    }

    for x in xs:
        ax.axvline(x, **kwargs)

    for y in ys:
        ax.axhline(y, **kwargs)
