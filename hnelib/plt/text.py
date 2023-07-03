import matplotlib.pyplot as plt
from matplotlib import transforms

import hnelib.util

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

class Text(object):
    def __init__(self, fig, ax):
        self.fig = fig
        self.ax = ax
        self.inverse_transformer = self.ax.transData.inverted()
        self.transform = self.ax.transData

    def draw(self, x, y, string, **kwargs):
        kwargs.setdefault('bbox', {})
        kwargs['bbox'] |= {
            'pad': 0,
            'fill': False,
            'linewidth': 0,
        }

        self.text = self.ax.text(
            x,
            y,
            string,
            transform=self.transform,
            **kwargs,
        )

        self.text.draw(self.fig.canvas.get_renderer())

    def get_coord(self, axis, bbox_point):
        bbox = self.text.get_tightbbox(self.fig.canvas.get_renderer())

        axes = ['x', 'y']
        index = axes.index(axis)

        coords = [0, 0]
        coords[index] = getattr(bbox, bbox_point)

        return self.inverse_transformer.transform(coords)[index]

    def annotate(
        self,
        x,
        y,
        x_pad=0,
        y_pad=0,
        x_arrow_len=0,
        y_arrow_len=0,
        ha='center',
        va='center',
        clip_on=False,
        arrowprops=arrows['->'],
        fontsize=fontsize['annotation'],
        bbox_kwargs={},
        **kwargs,
    ):
        kwargs = {
            'ha': ha,
            'va': va,
            'clip_on': clip_on,
            'fontsize': fontsize,
        } | kwargs

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

        self.draw(
            x=x_end,
            y=y_end,
            string=self.string,
            **kwargs,
        )

        if bbox_kwargs:
            self.text.set_bbox(bbox_kwargs)

        if x_start != x_end or y_start != y_end:
            self.ax.annotate(
                "",
                (x_start, y_start),
                xytext=(x_end, y_end),
                arrowprops=arrowprops,
                **kwargs,
            )

    def get_min_coord(self, axis):
        return min([self.get_coord(axis=axis, bbox_point=f"{axis}{p}") for p in [0, 1]])

    def get_max_coord(self, axis):
        return max([self.get_coord(axis=axis, bbox_point=f"{axis}{p}") for p in [0, 1]])
    

class Substring(Text):
    DEFAULT_COLOR = 'black'

    def __init__(self, raw, **kwargs):
        super().__init__(**kwargs)
        self.string, self.color = raw if isinstance(raw, tuple) or isinstance(raw, list) else (raw, self.DEFAULT_COLOR)

    def draw(self, x, y, **kwargs):
        return super().draw(
            x,
            y,
            string=self.string,
            color=self.color,
            **kwargs,
        )

    def alter_string(self, pre="", post=""):
        self.string = f"{pre}{self.string}{post}"
    

class Line(Text):
    def __init__(self, substrings, line_number=0, n_lines=1, **kwargs):
        super().__init__(**kwargs)
        self.substrings = [Substring(substring, **kwargs) for substring in hnelib.util.as_list(substrings)]
        self.line_number = line_number
        self.n_lines = n_lines

    @property
    def string(self):
        return "".join([ss.string for ss in self.substrings])

    def alter_string(self, **kwargs):
        for ss in self.substrings:
            ss.alter_string(**kwargs)

    def draw(self, x, y, **kwargs):
        super().draw(
            x,
            y,
            string=self.string,
            alpha=0,
            **kwargs,
        )

        x = self.get_min_coord(axis='x')

        for key in ['ha', 'horizontalalignment']:
            kwargs.pop(key, None)

        kwargs['ha'] = 'left'

        for substring in self.substrings:
            substring.transform = self.transform
            substring.draw(x, y, **kwargs)
            self.transform = transforms.offset_copy(
                substring.text._transform,
                x=substring.text.get_window_extent().width * .95,
                units='points',
                fig=self.fig,
            )


class Paragraph(Text):
    def __init__(self, lines, **kwargs):
        super().__init__(**kwargs)
        lines = hnelib.util.as_list(lines)
        self.lines = [Line(l, line_number=i, n_lines=len(lines), **kwargs) for i, l in enumerate(lines)]

    @property
    def string(self):
        return "\n".join([line.string for line in self.lines])

    def draw(self, x, y, **kwargs):
        kwargs.pop('string', None)

        super().draw(
            x,
            y,
            string=self.string,
            alpha=0,
            **kwargs,
        )

        y = self.get_min_coord(axis='y')

        for key in ['va', 'verticalalignment']:
            kwargs.pop(key, None)

        kwargs['va'] = 'bottom'

        for line in reversed(self.lines):
            line.transform = self.transform
            line.draw(x, y, **kwargs)
            self.transform = transforms.offset_copy(
                line.text._transform,
                y=line.text.get_window_extent().height,
                units='points',
                fig=self.fig,
            )
            # y = line.get_max_coord(axis='y')
