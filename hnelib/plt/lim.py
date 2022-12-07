import itertools

import hnelib.plt.axes

def set_one_to_max(axes, axis='x'):
    get_fns = [hnelib.plt.axes.get_fn(ax, fn_suffix='lim', axis=axis) for ax in axes]

    if all(get_fns):
        lims = list(itertools.chain.from_iterable([fn() for fn in get_fns]))
        _min, _max = min(lims), max(lims)

        for ax in axes:
            hnelib.plt.axes.set_fn(ax, fn_suffix='lim', axis=axis)(_min, _max)

def set_x_to_max(axes):
    set_one_to_max(axes, 'x')

def set_y_to_max(axes):
    set_one_to_max(axes, 'y')

def set_z_to_max(axes):
    set_one_to_max(axes, 'z')

def set_to_max(axes, x=True, y=True, z=True):
    if x:
        set_x_to_max(axes)

    if y:
        set_y_to_max(axes)

    if z:
        set_z_to_max(axes)

def set_equal(ax):
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    _max = max(x_max, y_max)
    _min = max(x_min, y_min)

    ax.set_xlim(_min, _max)
    ax.set_ylim(_min, _max)
