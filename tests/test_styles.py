"""Figure styles.

The property worth testing is not that a style sets a font size, but that a
reader can decode the figure: every legend entry must look different from every
other, or the legend cannot be matched to the curves it describes.
"""

import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from gdmbounds import catalog, plot, styles  # noqa: E402


@pytest.fixture(scope="module")
def selection():
    return catalog().select(
        instrument=["magic", "hess", "lat"], target_class="dsph",
        mode="ann", channel="tautau",
    ).select(year=[2016, 2020, 2022, 2023])


@pytest.fixture
def ax():
    figure, axes = plt.subplots()
    yield axes
    plt.close(figure)


def appearances(axes):
    handles, labels = axes.get_legend_handles_labels()
    return {
        (h.get_color(), h.get_linestyle(), str(h.get_marker())) for h in handles
    }, labels


@pytest.mark.parametrize("name", sorted(styles.STYLES))
def test_every_legend_entry_looks_different(selection, ax, name):
    """Two entries that look alike cannot be told apart on the page.

    This is why the default colours by legend entry rather than by instrument:
    grouping by instrument gave five entries and three appearances.
    """
    plot(selection, ax=ax, style=name, label="{instrument} {year}")
    looks, labels = appearances(ax)
    assert len(looks) == len(labels), (
        f"{name}: {len(labels)} legend entries share {len(looks)} appearances"
    )


@pytest.mark.parametrize("name", sorted(styles.STYLES))
def test_a_style_leaves_no_trace(selection, ax, name):
    """Importing or using this package must not change unrelated figures."""
    before = dict(mpl.rcParams)
    plot(selection, ax=ax, style=name)
    changed = {k for k in before if mpl.rcParams[k] != before[k]}
    assert not changed, f"{name} leaked these settings: {sorted(changed)}"


def test_print_style_does_not_rely_on_colour(selection, ax):
    """Greyscale must still separate curves, so print carries markers."""
    plot(selection, ax=ax, style="print", label="{instrument} {year}")
    handles = ax.get_legend_handles_labels()[0]
    curves = [h for h in handles if h.get_linestyle() != "-."]  # exclude the relic
    assert len({str(h.get_marker()) for h in curves}) > 1


def test_line_style_still_means_the_statement(selection, ax):
    """Markers separate groups so that line style stays free for its own meaning."""
    plot(selection, ax=ax, style="print")
    from gdmbounds.plotting import STATEMENT_STYLE

    drawn = {line.get_linestyle() for line in ax.lines}
    assert drawn <= set(STATEMENT_STYLE.values()) | {"-."}


def test_unknown_style_is_refused(selection, ax):
    with pytest.raises(ValueError, match="unknown style"):
        plot(selection, ax=ax, style="antique")


def test_warns_when_a_style_runs_out_of_appearances(ax):
    """Silently drawing two curves alike would mislead; say so instead.

    Colour and marker together separate dozens of curves, so this only bites on a
    selection far too crowded to read anyway — which is exactly when the reader
    most needs telling.
    """
    crowded = catalog().select(mode="ann")
    assert len(crowded) > styles.get("paper").separable_groups()
    with pytest.warns(UserWarning, match="exceed"):
        plot(crowded, ax=ax, style="paper", relic=None)


def test_latex_is_never_required(selection, ax):
    """Every style must render without a TeX installation."""
    for name in styles.STYLES:
        settings = styles.get(name).rcparams()
        assert not settings.get("text.usetex", False), f"{name} demands LaTeX"
