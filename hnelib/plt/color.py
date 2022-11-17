import matplotlib.colors

import hnelib.utils

#------------------------------------------------------------------------------#
#                                                                              #
#                                  constants                                   #
#                                                                              #
#------------------------------------------------------------------------------#
ALPHA = .35

# grayscale
GS = {
    'w': ""
    '0': 

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

DEFAULT = GS['g']

C = {
    # default color
    '-': GS['g'],
    # grayscale
    'white': GS['w'],
    'light gray': GS['lg'],
    'gray': GS['g'],
    'dark gray': GS['dg'],
    'black': GS['b'],
    # colors
    '1': '#45A1F8',
    '2': '#FF6437', 
}

# low-alpha colors
FC = {}


#------------------------------------------------------------------------------#
#                                                                              #
#                                  functions                                   #
#                                                                              #
#------------------------------------------------------------------------------#
def set_alpha(colors, alpha=ALPHA):
    """
    takes colors (single or list) and applies an alpha to them.
    """
    colors = hnelib.utils.as_list(colors)

    new_colors = [matplotlib.colors.to_rgba(c, alpha) for c in colors]

    if len(new_colors) == 1:
        new_colors = new_colors[0]

    return new_colors


#------------------------------------------------------------------------------#
#                                                                              #
#                                 module setup                                 #
#                                                                              #
#------------------------------------------------------------------------------#
def __setup__():
    global C, FC

    FC = {k: set_alpha(v) for k, v in C.items()}
    

if not len(FC):
    __setup__()
