"""The queryable view over the database."""

import pytest

from gdmbounds import schema
from gdmbounds.catalog import Catalog, catalog


@pytest.fixture(scope="module")
def cat():
    return catalog()


def test_catalog_holds_every_bound(cat):
    assert len(cat) == len(schema.iter_bound_files())


def test_every_row_is_classified(cat):
    """A blank class means a selection by class would silently miss the bound."""
    for column in ("instrument_class", "target_class", "channel_spectrum"):
        blank = cat.frame[cat.frame[column] == ""]
        assert blank.empty, (
            f"{len(blank)} bounds have no {column}: "
            f"{sorted(p.name for p in blank['path'])[:5]}"
        )


def test_select_narrows_and_composes(cat):
    iact = cat.select(instrument_class="iact")
    assert 0 < len(iact) < len(cat)
    both = iact.select(mode="ann")
    assert len(both) <= len(iact)
    assert set(both.frame["instrument_class"]) == {"iact"}
    assert set(both.frame["mode"]) == {"ann"}


def test_select_accepts_several_values(cat):
    pair = cat.select(instrument=["magic", "hess"])
    assert len(pair) == len(cat.select(instrument="magic")) + len(
        cat.select(instrument="hess")
    )


def test_select_rejects_an_unknown_column(cat):
    with pytest.raises(KeyError):
        cat.select(telescope="magic")


def test_involves_finds_joint_analyses(cat):
    """`select` matches the publishing instrument; `involves` matches participation."""
    alone = cat.select(instrument="magic")
    participating = cat.involves("magic")
    assert len(participating) > len(alone)
    extra = set(participating.paths()) - set(alone.paths())
    assert all("multi-inst" in str(p) for p in extra)


def test_between_filters_by_year(cat):
    recent = cat.between(2020, 2030)
    assert len(recent) > 0
    assert recent.frame["year"].min() >= 2020


def test_selection_is_not_a_view_onto_the_original(cat):
    """Narrowing must not mutate the catalogue it came from."""
    before = len(cat)
    cat.select(mode="dec")
    assert len(cat) == before


def test_curves_are_only_read_when_asked(cat):
    small = cat.select(instrument="nustar")
    assert len(small) == 1
    tables = small.curves()
    assert len(tables) == 1
    assert "mass" in tables[0].colnames


def test_summary_counts_add_up(cat):
    assert cat.summary("mode")["bounds"].sum() == len(cat)


def test_values_lists_what_can_be_selected(cat):
    modes = cat.values("mode")
    assert set(modes) == set(schema.MODES)


def test_catalog_is_cached_but_reloadable():
    assert catalog() is catalog()
    assert catalog(reload=True) is not None


def test_empty_selection_is_still_a_catalog(cat):
    empty = cat.select(instrument="magic", mode="dec", channel="gammagamma", year=1999)
    assert isinstance(empty, Catalog)
    assert len(empty) == 0
    assert empty.curves() == []
