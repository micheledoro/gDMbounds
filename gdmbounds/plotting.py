"""Draw a selection of bounds.

`plot` takes whatever a catalogue selection produced and draws it. It does not
know how the selection was made, which is the point: "every IACT limit on bb" and
"these three files" arrive here the same way.

Two distinctions are drawn automatically rather than left to the caller, because
getting them wrong misreads the physics:

- **Annihilation and decay cannot share an axis.** One limits a cross section
  from above, the other a lifetime from below. Asking for both raises.
- **A projected sensitivity is not a measurement.** CTAO is not yet operating,
  and 48 bounds here are forecasts. They are drawn dashed, and the legend says
  so, unless the caller deliberately overrides the styling.
"""

from __future__ import annotations

import collections
import warnings
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.io import ascii

from . import schema, styles
from .catalog import Catalog

#: Axis label for the quantity each mode constrains.
Y_LABEL = {
    "ann": r"$\langle \sigma v \rangle$  [cm$^3$ s$^{-1}$]",
    "dec": r"$\tau$  [s]",
}

#: Line style per kind of statement. A reader should be able to tell a forecast
#: from a measurement without consulting the legend text.
STATEMENT_STYLE = {
    "limit": "-",
    "sensitivity": "--",
    "detection": ":",
}

#: Thermal relic curves worth drawing under an annihilation plot.
RELIC_CURVES = {
    "steigman": ("wimp_steigman2012_numerical.ecsv", "Thermal relic (Steigman+ 2012)"),
    "huetten": ("wimp_huetten2017_analytical_omega012.ecsv",
                "Thermal relic (Hütten+ 2017)"),
}


def _quantity_column(table) -> str:
    for name in ("sigmav", "tau", "sigmav_lo"):
        if name in table.colnames:
            return name
    raise ValueError("no quantity column")


#: Fields a legend entry may name, in the order they read best.
LABEL_FIELDS = ("instrument", "year", "target", "channel", "profile")


def _fields(row, vocabulary) -> dict[str, str]:
    """The long names, not the shortnames. `magic` is a key; MAGIC goes on a figure."""
    return {
        "instrument": vocabulary.instruments.get(row.instrument, row.instrument),
        "year": str(row.year if row.year == row.year else ""),  # NaN-safe
        "target": vocabulary.targets.get(row.target, row.target),
        "channel": f"${vocabulary.channels.get(row.channel, row.channel)}$",
        "profile": row.profile,
        "statement": row.statement,
    }


def _labeller(selection, vocabulary, template: str | None):
    """Build a labelling function that names only what actually varies.

    A legend repeating "H.E.S.S. 2012" eleven times says nothing: the curves
    differ by profile or by target, and that is what the reader needs. So the
    label is assembled from the fields that take more than one value across this
    particular selection, and from nothing else.
    """
    if template:
        return lambda row: template.format(**_fields(row, vocabulary))

    varying = [
        field for field in LABEL_FIELDS
        if len(set(selection.frame[_COLUMN[field]].fillna(""))) > 1
    ]
    if not varying:
        varying = ["instrument", "year"]

    def base(row):
        fields = _fields(row, vocabulary)
        text = " ".join(fields[f] for f in varying if fields[f])
        if fields["statement"] == "sensitivity" and "statement" not in varying:
            text += " (projected)"
        return text

    # Metadata does not always separate curves that differ. Eleven H.E.S.S.
    # bounds on Fornax share every key and are told apart only by their filename
    # qualifiers — Sommerfeld enhancement, substructure, angular cut. Collapsing
    # them to two legend entries would show two curves where there are eleven, so
    # where a label would cover more than one file, the qualifiers are added.
    counts = collections.Counter(base(row) for row in selection.frame.itertuples())

    def label(row):
        text = base(row)
        # An empty label is silently dropped from a matplotlib legend, so a bound
        # whose varying fields happen to be blank — an unstated halo profile, say —
        # would be drawn and never named.
        if counts[text] > 1 or not text:
            parts = schema.parse_filename(Path(row.path))
            extra = parts["qualifiers"].strip("_").replace("_", ", ") if parts else ""
            # A bound with no qualifiers is the unadorned case, and the bare label
            # already tells it apart from its qualified siblings. Falling back to
            # the whole filename would put a path next to a name.
            if extra:
                text = f"{text} ({extra})" if text else extra
            elif not text:
                text = Path(row.path).stem
        return text

    return label


#: Which catalogue column backs each label field.
_COLUMN = {
    "instrument": "instrument", "year": "year", "target": "target",
    "channel": "channel", "profile": "profile",
}


def plot(
    selection: Catalog,
    ax=None,
    *,
    mass_unit: str = "TeV",
    color_by: str | None = "auto",
    label: str | None = None,
    bands: bool = True,
    relic: str | None = "steigman",
    legend: str | None = None,
    style: str | styles.Style = "default",
    latex: bool = False,
    **line_kwargs,
):
    """Draw every bound in `selection` on one pair of log axes.

    Returns the axes, so the caller composes rather than being handed a figure.
    Nothing is shown or saved here.

    `style` names one of `styles.STYLES`. It applies for this call only: the
    session's matplotlib settings are the same afterwards as before.
    """

    if len(selection) == 0:
        raise ValueError("nothing to plot: the selection is empty")

    modes = set(selection.frame["mode"])
    if len(modes) > 1:
        raise ValueError(
            f"cannot draw {sorted(modes)} on the same axes: annihilation limits a "
            "cross section from above and decay a lifetime from below, so the y "
            "axis would mean two things. Select one mode."
        )
    mode = modes.pop()

    chosen = styles.get(style)
    with styles.use(chosen, latex=latex):
        return _draw(selection, ax, mode, chosen, mass_unit, color_by, label,
                     bands, relic, legend, line_kwargs)


def _draw(selection, ax, mode, chosen, mass_unit, color_by, label, bands, relic,
          legend, line_kwargs):
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=chosen.figsize)
    vocabulary = schema.load_vocabulary()
    unit = u.Unit(mass_unit)

    make_label = _labeller(selection, vocabulary, label)
    drawn: set[str] = set()
    # "auto" colours by the legend entry, so no two entries look alike. Grouping
    # by instrument instead is a deliberate choice — it reads well, but several
    # entries then share a colour and the reader cannot tell which curve is which.
    if color_by == "auto":
        group_of = {row.path: make_label(row) for row in selection.frame.itertuples()}
    elif color_by:
        group_of = {row.path: getattr(row, color_by) for row in selection.frame.itertuples()}
    else:
        group_of = {}
    groups = sorted(set(group_of.values()))
    palette = chosen.palette
    colour_of = {g: palette[i % len(palette)] for i, g in enumerate(groups)}
    # Markers only once colour alone stops separating the curves: on a figure of
    # five they would be clutter, on one of fifteen they are what makes it
    # readable at all.
    marker_of = (
        {
            g: chosen.markers[(i // len(palette)) % len(chosen.markers)]
            for i, g in enumerate(groups)
        }
        if chosen.markers and len(groups) > len(palette)
        else {}
    )
    if groups and len(groups) > chosen.separable_groups():
        warnings.warn(
            f"{len(groups)} distinct curves exceed the "
            f"{chosen.separable_groups()} the {chosen.name!r} style can tell apart, "
            "so some curves are drawn alike. Narrow the selection, or pass "
            "color_by=None and distinguish them another way.",
            stacklevel=4,
        )

    for row in selection.frame.itertuples(index=False):
        table = ascii.read(row.path, format="ecsv")
        column = _quantity_column(table)
        mass = (np.asarray(table["mass"], float) * table["mass"].unit).to(unit)
        order = np.argsort(mass.value)
        value = np.asarray(table[column], float)[order]

        # One legend entry per distinct label: repeating it once per file turns
        # the legend into a wall and hides the plot behind it.
        text = make_label(row)
        group = group_of.get(row.path)
        kwargs = {
            "color": colour_of.get(group) if group is not None else None,
            "linestyle": STATEMENT_STYLE.get(row.statement, "-"),
            "label": text if text not in drawn else "_nolegend_",
            **line_kwargs,
        }
        if marker_of:
            # Sparse, so the marker identifies the curve without drowning it.
            kwargs.setdefault("marker", marker_of.get(group))
            kwargs.setdefault("markevery", max(1, len(value) // 6))
            kwargs.setdefault("markersize", 4)
        drawn.add(text)
        ax.plot(mass.value[order], value, **kwargs)

        if bands and {"sigmav_1sigma_lo", "sigmav_1sigma_hi"} <= set(table.colnames):
            ax.fill_between(
                mass.value[order],
                np.asarray(table["sigmav_1sigma_lo"], float)[order],
                np.asarray(table["sigmav_1sigma_hi"], float)[order],
                color=kwargs["color"], alpha=0.15, linewidth=0,
            )

    if relic and mode == "ann":
        _draw_relic(ax, relic, unit)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(f"$m_{{\\mathrm{{DM}}}}$  [{unit:latex_inline}]".replace("$$", ""))
    ax.set_ylabel(Y_LABEL[mode])
    _legend(ax, legend)
    return ax


def _legend(ax, placement: str | None) -> None:
    """Place the legend, or leave it off when it would obscure the data.

    Beyond about a dozen entries a legend inside the axes covers the curves it
    describes, so it moves outside by default and the figure grows to fit.
    """
    if placement == "none":
        return
    entries = len([h for h in ax.get_legend_handles_labels()[1]])
    if placement == "side" or (placement is None and entries > 12):
        ax.legend(frameon=False, fontsize="small", loc="upper left",
                  bbox_to_anchor=(1.02, 1.0), borderaxespad=0)
        ax.figure.subplots_adjust(right=0.62)
    else:
        ax.legend(frameon=False, fontsize="small")


def _draw_relic(ax, which: str, unit) -> None:
    """Underlay a thermal relic cross section, the scale a limit is measured against."""
    if which not in RELIC_CURVES:
        raise ValueError(f"unknown relic curve {which!r}; choose from {sorted(RELIC_CURVES)}")
    filename, label = RELIC_CURVES[which]
    path = Path(schema.DATA_DIR) / "modelpredictions" / filename
    table = ascii.read(path, format="ecsv")
    mass = (np.asarray(table["mass"], float) * table["mass"].unit).to(unit)
    ax.plot(
        mass.value, np.asarray(table["sigmav"], float),
        color="0.4", linestyle="-.", linewidth=1.2, label=label, zorder=0,
    )
