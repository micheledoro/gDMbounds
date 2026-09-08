"""The database must satisfy its own schema.

This is the test that would have caught the malformed `mwa` legend entry that
silently broke every import of the package for eleven months.
"""

import collections

import pytest

from gdmbounds import schema


def test_vocabularies_load():
    """Every legend file must parse; the package cannot import otherwise."""
    vocabulary = schema.load_vocabulary()
    assert vocabulary.instruments
    assert vocabulary.channels
    assert vocabulary.targets


def test_database_is_not_empty():
    assert len(schema.iter_bound_files()) > 300


@pytest.mark.parametrize("path", schema.iter_bound_files(), ids=lambda p: p.name)
def test_bound_file_is_readable(path):
    """Each bound must at least parse as ECSV."""
    issues = schema.check_file(path)
    unreadable = [i for i in issues if i.kind == "unreadable"]
    assert not unreadable, unreadable[0].detail


def test_database_satisfies_schema():
    """The whole database, checked in one pass."""
    issues = schema.check_database()
    if issues:
        summary = collections.Counter(i.kind for i in issues)
        report = "\n".join(f"  {n:4d}  {kind}" for kind, n in summary.most_common())
        examples = "\n".join(f"  {i}" for i in issues[:10])
        pytest.fail(
            f"{len(issues)} schema violations in {len({i.path for i in issues})} files:\n"
            f"{report}\n\nfirst examples:\n{examples}"
        )
