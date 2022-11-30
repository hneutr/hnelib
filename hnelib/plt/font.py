"""
Nature guidelines on fonts:
- subplot labels: 8pt bold, not italic
- max: 7pt
- min: 5pt
"""
__size__ = {
    's': 5,
    'm': 6,
    'l': 7,
    'xl': 8,
}

size = {
    **__size__,
    # plot elements
    'annotation': __size__['s'],
    'tick': __size__['m'],
    'legend': __size__['m'],
    'axis_label': __size__['l'],
    'title': __size__['xl'],
    'subplot_label': __size__['xl'],
}

weight = {
    'subplot_label': 'bold',
}

name = {
    'subplot_label': 'Arial',
}
