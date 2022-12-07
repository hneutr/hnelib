from hnelib.plt.arrow import arrows
import hnelib.plt.font


def fraction(numerator, denominator, convert_hyphens=True):
    string = r"$\frac{\mathrm{" + numerator + "}}{\mathrm{" + denominator + "}}$"

    string = string.replace(' ', '\ ')

    if convert_hyphens:
        string = string.replace("-", u"\u2010")

    return string

def annotate(
    ax,
    text,
    x,
    y,
    x_pad=0,
    y_pad=0,
    x_arrow_len=0,
    y_arrow_len=0,
    ha='center',
    va='center',
    annotation_clip=False,
    arrowstyle=arrows['->'],
    fontsize=hnelib.plt.font.size['annotation'],
):
    kwargs = {
        'ha': ha,
        'va': va,
        'fontsize': fontsize,
        'annotation_clip': annotation_clip,
    }

    if ha == 'center':
        x_mult = 0
    elif ha == 'left':
        x_mult = 1
    elif ha == 'right':
        x_mult = -1
        
    if va == 'center':
        y_mult = 0
    elif va == 'bottom':
        y_mult = 1
    elif va == 'top':
        y_mult = -1

    x_start = x + (x_mult * x_pad)
    y_start = y + (y_mult * y_pad)

    x_end = x_start + (x_mult * x_arrow_len) 
    y_end = y_start + (y_mult * y_arrow_len) 

    if x_start != x_end or y_start != y_end:
        kwargs['xytext'] = (x_end, y_end)
        kwargs['arrowstyle'] = arrowstyle

    ax.annotate(
        text,
        (x_start, y_end),
        **kwargs,
    )
