"""
Nature guidelines on fonts:
- subplot labels: 8pt bold, not italic
- max: 7pt
- min: 5pt
"""

__ADJECTIVES__ = {
    's': 5,
    'm': 6,
    'l': 7,
    'xl': 8,
}

__PLOT_ELEMENTS__ = {
    'annotation': 's',
    'tick': 'm',
    'legend': 'm',
    'axis': 'l',
    'title': 'xl',
    'subplot-label': 'xl',
}

# S is for size
S = {}

def __setup__():
    global __ADJECTIVES__, __PLOT_ELEMENTS__, S

    S = __ADJECTIVES__.copy()
    S.update({k: S[v] for k, v in __PLOT_ELEMENTS__.items()})


if not len(S):
    __setup__()
