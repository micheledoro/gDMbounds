"""The classification axes bounds are selected and plotted by.

Each axis exists so that a user can include or exclude a whole kind of result
deliberately. A wrong value is worse than a missing one: it puts a bound in a
selection where it does not belong, silently.
"""

import collections

import pytest
from astropy.io import ascii

from gdmbounds import schema


@pytest.fixture(scope="module")
def metadata():
    return [
        (path, ascii.read(path, format="ecsv").meta)
        for path in schema.iter_bound_files()
    ]


def test_statement_agrees_with_the_filename(metadata):
    """`_sens` in the name and `statement` in the header must not disagree."""
    wrong = []
    for path, meta in metadata:
        parts = schema.parse_filename(path)
        marked = "sens" in (parts["qualifiers"].split("_") if parts else [])
        declared = str(meta.get("statement", ""))
        if marked != (declared == "sensitivity"):
            wrong.append(f"{path.name}: filename sens={marked}, statement={declared!r}")
    assert not wrong, "\n  ".join(wrong)


def test_profile_agrees_with_the_filename(metadata):
    """A declared profile must appear in the filename it was taken from."""
    wrong = []
    for path, meta in metadata:
        profile = str(meta.get("profile", ""))
        if not profile:
            continue
        stem = path.stem.lower()
        token = "iso" if profile == "isothermal" else profile[:4]
        if token not in stem:
            wrong.append(f"{path.name}: declares profile {profile!r}")
    assert not wrong, "\n  ".join(wrong)


def test_every_bound_states_what_kind_of_result_it_is(metadata):
    missing = [p.name for p, meta in metadata if not str(meta.get("statement", ""))]
    assert not missing, f"{len(missing)} bounds without a statement: {missing[:5]}"


def test_axes_are_actually_discriminating(metadata):
    """An axis on which every bound has the same value sorts nothing.

    This is not pedantry: `origin` was invented to separate author forecasts from
    collaboration results, and would be useless if every file said the same thing.
    """
    for key in ("mode", "origin", "statement"):
        values = collections.Counter(str(meta.get(key, "")) for _, meta in metadata)
        assert len(values) > 1, f"every bound has {key}={list(values)[0]!r}"


def test_profile_absence_is_not_mistaken_for_absence_of_a_profile(metadata):
    """Guards the documented meaning of a missing `profile`.

    Most bounds do not record one, and a future change that made the key required
    would force someone to invent values. If this ratio ever approaches 1, the key
    has quietly become mandatory in practice and the docs need revisiting.
    """
    declared = sum(1 for _, meta in metadata if str(meta.get("profile", "")))
    assert declared < len(metadata), (
        "every bound now declares a profile; move it to REQUIRED_META and "
        "update the note in schema.OPTIONAL_META"
    )
