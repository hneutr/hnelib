import functools
import matplotlib.colors

import hnelib.util

#------------------------------------------------------------------------------#
#                                                                              #
#                                  constants                                   #
#                                                                              #
#------------------------------------------------------------------------------#
alpha = .35

cycle = [
    '#45A1F8',
    '#FF6437', 
    '#4B917D',
    '#F037A5',
    '#2EBD59',
    '#FFC864',
    '#C87D55',
    '#1E3264',
]

# grayscale
grayscale = {
    # white
    "w": "#FFFFFF",
    "w+": "#D7D7D7",
    # light gray
    "lg-": "#D7D7D7",
    "lg": "#AFAFAF",
    "lg+": "#868686",
    # gray
    "g-": "#868686",
    "g": "#5E5E5E",
    "g+": "#474747",
    # dark gray
    "dg-": "#474747",
    "dg": "#2F2F2F",
    "dg+": "#181818",
    "b-": "#181818",
    "b": "#000000",
}

grayscale = [
    # white
    "#FFFFFF",
    "#D7D7D7",
    # light gray
    "#AFAFAF",
    "#868686",
    # gray
    "#5E5E5E",
    "#474747",
    # dark gray
    "#2F2F2F",
    "#181818",
    # black
    "#000000",
]

named_grayscale = {
    'white': grayscale[0],
    'light gray': grayscale[2],
    'gray': grayscale[4],
    'dark gray': grayscale[6],
    'black': grayscale[8],
}


#------------------------------------------------------------------------------#
#                                                                              #
#                                  functions                                   #
#                                                                              #
#------------------------------------------------------------------------------#
def set_alpha(colors, alpha=alpha):
    """
    takes colors (single or list) and applies an alpha to them.
    """
    colors = hnelib.util.as_list(colors)

    new_colors = [matplotlib.colors.to_rgba(c, alpha) for c in colors]

    if len(new_colors) == 1:
        new_colors = new_colors[0]

    return new_colors


#------------------------------------------------------------------------------#
#                                                                              #
#                                 module setup                                 #
#                                                                              #
#------------------------------------------------------------------------------#
@functools.lru_cache
def __get_faded_colors__():
    return {k: set_alpha(v) for k, v in colors.items()}

colors = {
    # default color
    '-': named_grayscale['gray'],
    **named_grayscale,
    **{i: c for i, c in enumerate(cycle)}
}

# low-alpha colors
faded_colors = __get_faded_colors__()
