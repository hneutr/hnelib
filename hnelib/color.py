import matplotlib.colors

import hnelib.utils

ALPHA = .35

C = {
    'dark-gray': '#5E5E5E',
    '1': '#45A1F8',
    '2': '#FF6437', 
}

COLORS_SET = False

def set_alpha(colors, alpha=ALPHA):
    """
    takes colors (single or list) and applies an alpha to them.
    """
    colors = hnelib.utils.as_list(colors)

    new_colors = [matplotlib.colors.to_rgba(c, alpha) for c in colors]

    if len(new_colors) == 1:
        new_colors = new_colors[0]

    return new_colors


def _set_colors():
    global COLORS_SET, C

    if COLORS_SET:
        return

    for c in list(C):
        C[c.replace('-', '_')] = C[c]

    alpha_colors = {}
    for k, v in C.items():
        alpha_colors[k] = set_alpha(v)

    C['a'] = alpha_colors

    COLORS_SET = True
    
_set_colors()
