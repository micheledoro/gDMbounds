"""Figure styles.

A style is a palette plus a set of matplotlib settings, applied for the duration
of a plot and then withdrawn. The old implementation assigned to `mpl.rcParams`
at import time, so importing the package changed how every unrelated figure in
the session looked; nothing here leaks.

The default palette is Okabe–Ito, designed to stay distinguishable under the
common forms of colour vision deficiency. Roughly one man in twelve has one, and
a figure whose curves are told apart by red against green is unreadable to them.

No style requires LaTeX. `paper` uses it only if `latex=True` is asked for, and
raises a clear error rather than a TeX traceback when it is missing.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field

#: Okabe–Ito, minus its yellow, which is illegible as a thin line on white.
#: https://jfly.uni-koeln.de/color/
COLOURBLIND_SAFE = [
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # bluish green
    "#CC79A7",  # reddish purple
    "#56B4E9",  # sky blue
    "#D55E00",  # vermillion
    "#000000",  # black
]

#: Greys for print. Lightness alone separates only a handful of curves before the
#: palest is lost against the page, so print also carries markers.
GREYSCALE = ["#000000", "#404040", "#737373", "#a6a6a6"]

#: Marker shapes for greyscale, where line style cannot be borrowed to separate
#: groups: it already distinguishes a measurement from a projection, and one
#: visual channel cannot carry two meanings.
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]


@dataclass(frozen=True)
class Style:
    """A palette and a set of matplotlib settings."""

    name: str
    palette: list[str]
    figsize: tuple[float, float]
    rc: dict = field(default_factory=dict)
    #: Marker shapes, cycled once the palette runs out. Line style cannot be
    #: borrowed for this: it already separates a measurement from a projection.
    markers: list[str] = field(default_factory=lambda: list(MARKERS))

    def separable_groups(self) -> int:
        """How many groups this style can tell apart before repeating."""
        return len(self.palette) * (len(self.markers) or 1)

    def rcparams(self) -> dict:
        import matplotlib as mpl

        return {"axes.prop_cycle": mpl.cycler(color=self.palette), **self.rc}


_BASE = {
    "axes.grid": False,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "legend.frameon": False,
    "figure.autolayout": False,
}

STYLES = {
    "default": Style(
        name="default",
        palette=COLOURBLIND_SAFE,
        figsize=(8.0, 5.5),
        rc={**_BASE, "font.size": 11, "axes.labelsize": 12, "lines.linewidth": 1.6},
    ),
    "paper": Style(
        name="paper",
        palette=COLOURBLIND_SAFE,
        figsize=(6.5, 4.8),
        rc={
            **_BASE,
            "font.family": "serif",
            "font.size": 9,
            "axes.labelsize": 10,
            "legend.fontsize": 7.5,
            "lines.linewidth": 1.2,
            "savefig.dpi": 300,
        },
    ),
    "talk": Style(
        name="talk",
        palette=COLOURBLIND_SAFE,
        figsize=(10.0, 6.5),
        rc={
            **_BASE,
            "font.size": 15,
            "axes.labelsize": 17,
            "legend.fontsize": 12,
            "lines.linewidth": 2.6,
            "axes.linewidth": 1.4,
        },
    ),
    "print": Style(
        name="print",
        palette=GREYSCALE,
        figsize=(6.5, 4.8),
        rc={**_BASE, "font.size": 10, "lines.linewidth": 1.4, "savefig.dpi": 300},
    ),
}


def get(style: str | Style) -> Style:
    if isinstance(style, Style):
        return style
    if style not in STYLES:
        raise ValueError(f"unknown style {style!r}; choose from {sorted(STYLES)}")
    return STYLES[style]


@contextlib.contextmanager
def use(style: str | Style = "default", latex: bool = False):
    """Apply a style for the duration of the block, then withdraw it.

    Nothing is left changed afterwards, so importing this package never alters
    how an unrelated figure looks.
    """
    import matplotlib as mpl

    chosen = get(style)
    settings = chosen.rcparams()
    if latex:
        settings.update(_latex_settings())
    with mpl.rc_context(settings):
        yield chosen


def _latex_settings() -> dict:
    """LaTeX rendering, if a distribution is actually installed.

    Checked up front: without it matplotlib fails deep inside a subprocess with
    an error that says nothing about the real cause.
    """
    import shutil

    if shutil.which("latex") is None:
        raise RuntimeError(
            "latex=True needs a LaTeX distribution on PATH, and none was found. "
            "Every style renders without it; pass latex=False (the default)."
        )
    return {"text.usetex": True, "font.family": "serif"}
