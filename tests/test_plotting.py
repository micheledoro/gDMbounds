"""Drawing a selection.

The tests check what a reader of the figure would be misled by, not that
matplotlib works: that no curve is drawn without being named, that a forecast is
visually distinct from a measurement, and that two quantities which cannot share
an axis are refused rather than silently overlaid.
"""

import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from gdmbounds import catalog  # noqa: E402
from gdmbounds.plotting import STATEMENT_STYLE, plot  # noqa: E402


@pytest.fixture(scope="module")
def cat():
    return catalog()


@pytest.fixture
def ax():
    figure, axes = plt.subplots()
    yield axes
    plt.close(figure)


def test_draws_one_line_per_bound(cat, ax):
    selection = cat.select(instrument="hess", source="fornaxcluster", channel="bb")
    plot(selection, ax=ax, relic=None)
    assert len(ax.lines) == len(selection)


def test_every_curve_is_named(cat, ax):
    """A curve with no legend entry is a curve the reader cannot identify.

    Eleven H.E.S.S. Fornax bounds share every metadata field and differ only in
    their filename qualifiers, and one of them has no halo profile recorded — an
    empty label, which matplotlib drops without a word.
    """
    selection = cat.select(instrument="hess", source="fornaxcluster", channel="bb")
    plot(selection, ax=ax, relic=None)
    labels = [text for text in ax.get_legend_handles_labels()[1]]
    assert len(labels) == len(selection)
    assert all(labels), "a curve was drawn with an empty label"
    assert len(set(labels)) == len(labels), "two curves share a legend entry"


def test_labels_name_only_what_varies(cat, ax):
    """Repeating the instrument and year on every entry says nothing."""
    selection = cat.select(instrument="hess", source="fornaxcluster", channel="bb")
    plot(selection, ax=ax, relic=None)
    labels = ax.get_legend_handles_labels()[1]
    assert not any("H.E.S.S." in text for text in labels), (
        "instrument is constant here and should not be repeated: " + str(labels[:3])
    )


def test_repeated_bounds_share_one_legend_entry(cat, ax):
    """Many files, one label: the legend describes curves, not files."""
    selection = cat.select(instrument="hess", mode="ann", channel="bb")
    plot(selection, ax=ax, relic=None, label="{instrument}")
    labels = ax.get_legend_handles_labels()[1]
    assert len(labels) == 1
    assert len(ax.lines) == len(selection)


def test_a_forecast_looks_different_from_a_measurement(cat, ax):
    """CTAO is not operating; its curves must not read as measurements."""
    selection = cat.select(instrument="ctao", mode="ann", channel="bb")
    plot(selection, ax=ax, relic=None)
    assert {line.get_linestyle() for line in ax.lines} == {
        STATEMENT_STYLE["sensitivity"]
    }


def test_refuses_to_mix_annihilation_and_decay(cat, ax):
    """One limits a cross section from above, the other a lifetime from below."""
    with pytest.raises(ValueError, match="same axes"):
        plot(cat.select(instrument=["hess", "lat"]), ax=ax)


def test_refuses_an_empty_selection(cat, ax):
    with pytest.raises(ValueError, match="empty"):
        plot(cat.select(instrument="magic", year=1899), ax=ax)


@pytest.mark.parametrize("unit, factor", [("GeV", 1000.0), ("TeV", 1.0)])
def test_mass_axis_honours_its_unit(cat, ax, unit, factor):
    selection = cat.select(instrument="magic", source="segue1", channel="bb", year=2011)
    plot(selection, ax=ax, mass_unit=unit, relic=None)
    assert unit in ax.get_xlabel()
    first = ax.lines[0].get_xdata()[0]
    plt.close(ax.figure)
    other, other_ax = plt.subplots()
    plot(selection, ax=other_ax, mass_unit="TeV", relic=None)
    assert first == pytest.approx(other_ax.lines[0].get_xdata()[0] * factor, rel=1e-6)
    plt.close(other)


def test_relic_curve_is_optional_and_only_for_annihilation(cat, ax):
    selection = cat.select(instrument="magic", source="segue1", channel="bb", year=2011)
    plot(selection, ax=ax, relic=None)
    without = len(ax.lines)
    plot(selection, ax=ax, relic="steigman")
    assert len(ax.lines) == 2 * without + 1


def test_decay_axis_is_a_lifetime(cat, ax):
    plot(cat.select(mode="dec", channel="bb", instrument="lat"), ax=ax)
    assert r"\tau" in ax.get_ylabel()
    assert "sigma" not in ax.get_ylabel()
