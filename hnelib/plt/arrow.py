import hnelib.plt.color

__color__ = hnelib.plt.color.C['-']
__linewidth__ = .35

A = {
    '->': {
        'lw': __linewidth__,
        'color': __color__,
        'arrowstyle': '->, head_width=.15, head_length=.21',
    },
    '-': {
        'lw': __linewidth__,
        'color': __color__,
        'arrowstyle': '-',
        'shrinkA': 0,
        'shrinkB': 0,
    },
}

A['-> (full -)'] = {
    **A['->'],
    'shrinkA': 0,
}

A['-> (full >)'] = {
    **A['->'],
    'shrinkB': 0,
}
