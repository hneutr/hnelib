from functools import cached_property
import matplotlib.pyplot as plt
import matplotlib.patches
import matplotlib.lines

import hnelib.color


LINEWIDTH = .5


def set(
    ax,
    handles,
    **kwargs,
):
    legend = ax.legend(
        handles=[handle.artist for handle in handles],
        **kwargs,
    )

    set_handle_text_colors(legend, handles)


def set_handle_text_colors(legend, handles):
    text_colors = {str(h.text): h.textcolor for h in handles if hasattr(h, 'textcolor')}

    for handle in legend.get_texts():
        text = str(handle.get_text())
        if text in text_colors:
            plt.setp(handle, color=text_colors[text])


class Handle(object):
    DEFAULTS = {
        'linewidth': LINEWIDTH,
    }

    ARTIST_KEYS = {}

    def __init__(
        self,
        text,
        fade_facecolor=True,
        **kwargs,
    ):
        self.text = text
        self.fade_facecolor = fade_facecolor

        for k, v in self.DEFAULTS.items():
            kwargs[k] = kwargs.get(k, v)

        for k, v in kwargs.items():
            setattr(self, k, v)

        self.kwargs = {
            'label': text
        }

        self.set_textcolor()
        self.set_facecolor()

        for k, v in kwargs.items():
            if v != None:
                artist_key = self.ARTIST_KEYS.get(k, k)
                self.kwargs[artist_key] = v

    def set_textcolor(self):
        self.textcolor = getattr(self, 'color', 'black')

    def set_facecolor(self):
        facecolor = getattr(self, 'facecolor', getattr(self, 'color', None))

        if self.fade_facecolor and facecolor:
            facecolor = hnelib.color.set_alpha(facecolor)

        self.facecolor = facecolor
        self.kwargs['facecolor'] = facecolor

    @cached_property
    def artist(self):
        return None


class Line(Handle):
    def set_facecolor(self):
        self.facecolor = None

    @cached_property
    def artist(self):
        return matplotlib.lines.Line2D([0], [0], **self.kwargs)


class Text(Handle):
    DEFAULTS = {
        **Handle.DEFAULTS,
        'color': 'w',
    }

    def set_facecolor(self):
        self.facecolor = None

    def set_textcolor(self):
        self.textcolor = 'black'

    @cached_property
    def artist(self):
        return matplotlib.lines.Line2D([], [], **self.kwargs)


class Marker(Handle):
    GET_ARTIST = lambda kwargs: matplotlib.lines.Line2D([], [], **kwargs)

    DEFAULTS = {
        **Handle.DEFAULTS,
        'marker': 'o',
        'size': 4,
    }

    ARTIST_KEYS = {
        'color': 'markeredgecolor',
        'facecolor': 'markerfacecolor',
        'linewidth': 'markerlinewidth',
        'size': 'markersize',
    }

    @cached_property
    def artist(self):
        return matplotlib.lines.Line2D([], [], **self.kwargs)


class Box(Handle):
    ARTIST_KEYS = {
        'color': 'edgecolor',
        'facecolor': 'facecolor',
    }

    @cached_property
    def artist(self):
        return matplotlib.patches.Patch(**self.kwargs)
