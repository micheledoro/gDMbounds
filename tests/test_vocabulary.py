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
