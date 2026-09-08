"""The controlled vocabularies and the classes built on them.

The classes are what makes a selection like "every IACT" or "every dwarf
spheroidal" expressible. They live in the legend ECSV files, which are
hand-edited, so they need checking like any other data.
"""

import pytest

from gdmbounds import schema


@pytest.fixture(scope="module")
def vocabulary():
    return schema.load_vocabulary()


def test_every_term_is_classified(vocabulary):
    """No blank or misspelled class survives in a legend."""
    issues = schema.check_vocabulary(vocabulary)
    assert not issues, "\n  ".join(str(i) for i in issues)


def test_no_class_is_empty(vocabulary):
    """A declared class with no members is either a typo or dead weight."""
    empty = [
        f"instrument class '{k}'"
        for k in schema.INSTRUMENT_CLASSES
        if not vocabulary.instruments_in(k)
    ] + [
        f"target class '{k}'"
        for k in schema.TARGET_CLASSES
        if not vocabulary.targets_in(k)
    ] + [
        f"channel spectrum '{k}'"
        for k in schema.CHANNEL_SPECTRA
        if not vocabulary.channels_with(k)
    ]
    assert not empty, f"declared but unused: {empty}"


def test_every_instrument_used_by_a_bound_is_in_the_legend(vocabulary):
    """A bound whose instrument is missing from the legend is invisible to any
    selection made by class — which is how five bounds went unread for years."""
    from astropy.io import ascii

    used = set()
    for path in schema.iter_bound_files():
        table = ascii.read(path, format="ecsv")
        used.add(schema.base_instrument(str(table.meta["instrument"])))
    missing = used - set(vocabulary.instruments)
    assert not missing, f"instruments used by bounds but absent from the legend: {missing}"


def test_describe_mentions_every_class(vocabulary):
    """The user-facing summary must not silently omit a class."""
    text = vocabulary.describe()
    for key in (*schema.INSTRUMENT_CLASSES, *schema.TARGET_CLASSES, *schema.CHANNEL_SPECTRA):
        assert key in text, f"describe() omits '{key}'"


def _used(key):
    """Every value of a metadata key actually used by a bound, collapsed to the
    token the legends are indexed by."""
    from astropy.io import ascii

    collapse = {"instrument": schema.base_instrument, "source": schema.base_source}
    return {
        collapse.get(key, str)(str(ascii.read(p, format="ecsv").meta[key]))
        for p in schema.iter_bound_files()
    }


def test_every_target_used_by_a_bound_is_in_the_legend(vocabulary):
    """Adding a bound whose target has no legend entry must fail.

    Already enforced through `schema.check_file`, which reports `unknown-target`;
    stated separately here so the invariant is findable rather than implied.
    """
    missing = _used("source") - set(vocabulary.targets)
    assert not missing, f"targets used by bounds but absent from the legend: {missing}"


def test_every_channel_used_by_a_bound_is_in_the_legend(vocabulary):
    missing = _used("channel") - set(vocabulary.channels)
    assert not missing, f"channels used by bounds but absent from the legend: {missing}"


@pytest.mark.parametrize("legend", ["instruments", "targets", "channels"])
def test_legend_entries_are_distinguishable(legend):
    """Two entries sharing a display name defeat the point of a legend.

    `canesvec1` and `canesvec2` both read 'Canes Ven I - II dSph' until this
    caught them, so a plot legend could not tell the two galaxies apart.
    """
    import collections

    from astropy.io import ascii

    table = ascii.read(schema.LEGENDS_DIR / f"legend_{legend}.ecsv")
    label = "latex" if legend == "channels" else "longname"
    counts = collections.Counter(str(row[label]) for row in table)
    repeated = {name: n for name, n in counts.items() if n > 1}
    assert not repeated, f"legend_{legend} reuses these labels: {repeated}"
