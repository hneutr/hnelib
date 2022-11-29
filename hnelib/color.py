import matplotlib.colors

import hnelib.utils

#------------------------------------------------------------------------------#
#                                                                              #
#                                  constants                                   #
#                                                                              #
#------------------------------------------------------------------------------#
ALPHA = .35

C = {
    'dark-gray': '#5E5E5E',
    '1': '#45A1F8',
    '2': '#FF6437', 
    '3': '#4B917D',
    '4': '#F037A5', 
    '5': '#2EBD59',
    '6': '#FFC864',
    '7': '#C87D55', 
    '8': '#1E3264',
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
def __set_colors__():
    global __COLORS_SET__, C, FC

    if __COLORS_SET__:
        return

    for c in list(C):
        C[c.replace('-', '_')] = C[c]

    for k, v in C.items():
        FC[k] = set_alpha(v)

    __COLORS_SET__ = True
    

__COLORS_SET__ = False
__set_colors__()
