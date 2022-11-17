import hnelib.plt.ax

def set_one_to_max(axes, axis='x'):
    get_fns = [hnelib.plt.ax.get_fn(ax, fn_suffix='lim', axis=axis)]

    if all(get_fns):
        lims = list(itertools.chain.from_iterable([fn() for fn in get_fns]))
        _min, _max = min(lims), max(lims)

        for ax in axes:
            hnelib.plt.ax.set_fn(ax, fn_suffix='lim', axis=axis)(_min, _max)

def set_to_max(axes, x=True, y=True, z=True):
    if x:
        set_lim_to_max(axes, 'x')

    if y:
        set_lim_to_max(axes, 'y')

    if z:
        set_lim_to_max(axes, 'z')

def set_equal(ax):
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    _max = max(x_max, y_max)
    _min = max(x_min, y_min)

    ax.set_xlim(_min, _max)
    ax.set_ylim(_min, _max)
