from matplotlib import transforms

from hnelib.plt.arrow import arrows
from hnelib.plt.font import size as fontsize


def fraction(numerator, denominator, convert_hyphens=True):
    string = r"$\frac{\mathrm{" + numerator + "}}{\mathrm{" + denominator + "}}$"

    string = string.replace(' ', '\ ')

    if convert_hyphens:
        string = subtract(string)

    return string


def subtract(string):
    return string.replace("-", u"\u2010")


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
    arrowprops=arrows['->'],
    fontsize=fontsize['annotation'],
    background_kwargs={},
):
    kwargs = {
        'ha': ha or 'center',
        'va': va or 'center',
        'fontsize': fontsize,
        'annotation_clip': annotation_clip,
    }

    if ha == 'left':
        x_mult = 1
    elif ha == 'right':
        x_mult = -1
    else:
        x_mult = 0
        
    if va == 'bottom':
        y_mult = 1
    elif va == 'top':
        y_mult = -1
    else:
        y_mult = 0

    x_start = x + (x_mult * x_pad)
    y_start = y + (y_mult * y_pad)

    x_end = x_start + (x_mult * x_arrow_len) 
    y_end = y_start + (y_mult * y_arrow_len) 

    annotation = ax.annotate(
        text,
        (x_end, y_end),
        **kwargs,
    )

    if background_kwargs:
        annotation.set_bbox(background_kwargs)

    if x_start != x_end or y_start != y_end:
        ax.annotate(
            "",
            (x_start, y_start),
            xytext=(x_end, y_end),
            arrowprops=arrowprops,
            **kwargs,
        )

def multiline(
    ax,
    lines,
    x,
    y,
    va='bottom',
    ha='left',
):

def multicolor(
    ax,
    elements,
    x,
    y,
    va='bottom',
    ha='left',
    **kwargs,
):
    for i, element in enumerate(elements):
        text, color = element if isinstance(element, tuple) else (element, 'black')

        if i != len(elements):
            text += " "

        text = ax.text(
            x,
            y,
            text,
            color=color,
            transform=ax.transAxes,
            va=va,
            ha=ha,
            **kwargs,
        )

        transforms.offset_copy(
            text._transform,
            x=text.get_window_extent().width,
            units='dots',
        )

    for s,c in zip(ls,lc):
        text = plt.text(x,y,s+" ",color=c, transform=t, **kw)
        text.draw(fig.canvas.get_renderer())
        ex = text.get_window_extent()
        t = transforms.offset_copy(text._transform, x=ex.width, units='dots')
