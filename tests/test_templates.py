"""The templates must satisfy the same schema as the database.

They did not, and that is how the database acquired a systematic defect: the old
template wrote `{confidence  "0.95" }` with no colon, so every bound copied from
it inherited a key that never parsed. 351 files carried it. Fixing the files
without fixing the template would only have delayed the next one.

These tests check structure, not content: a template's `instrument` is the string
"shortname from ..." and cannot be looked up in a vocabulary. What matters is that
every required key is present and correctly formed, so a bound built from it
starts valid.
"""

from pathlib import Path

import pytest
from astropy import units as u
from astropy.io import ascii

from gdmbounds import schema

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

EXPECTED_COLUMNS = {
    "bound_annihilation.ecsv": ("ann", "sigmav", "cm3s-1"),
    "bound_decay.ecsv": ("dec", "tau", "s"),
}


def template_paths():
    return sorted(TEMPLATES.glob("*.ecsv"))


def test_templates_exist():
    assert template_paths(), f"no templates found in {TEMPLATES}"


@pytest.mark.parametrize("path", template_paths(), ids=lambda p: p.name)
def test_template_parses(path):
    ascii.read(path, format="ecsv")


@pytest.mark.parametrize("path", template_paths(), ids=lambda p: p.name)
def test_template_carries_every_required_key(path):
    """A missing key here becomes a missing key in every bound copied from it."""
    meta = ascii.read(path, format="ecsv").meta
    missing = [key for key in schema.REQUIRED_META if key not in meta]
    assert not missing, f"{path.name} would produce bounds missing {missing}"


@pytest.mark.parametrize("path", template_paths(), ids=lambda p: p.name)
def test_template_declares_the_right_quantity(path):
    """Each template must carry the column its mode implies, in the right unit."""
    mode, column, unit = EXPECTED_COLUMNS[path.name]
    table = ascii.read(path, format="ecsv")
    assert str(table.meta["mode"]) == mode
    assert column in table.colnames, f"{path.name} has no '{column}' column"
    assert table[column].unit == u.Unit(unit)


@pytest.mark.parametrize("path", template_paths(), ids=lambda p: p.name)
def test_template_is_free_of_the_defects_it_once_spread(path):
    """The two specific faults the previous templates propagated."""
    text = path.read_text()
    assert "−" not in text, (
        f"{path.name} uses a Unicode minus; the schema line needs an ASCII hyphen"
    )
    for key in schema.REQUIRED_META:
        assert f"{{{key}:" in text, (
            f"{path.name} writes '{key}' without its colon, so it is not a key"
        )


@pytest.mark.parametrize("path", template_paths(), ids=lambda p: p.name)
def test_template_points_at_the_current_licence(path):
    text = path.read_text()
    assert "moritzhuetten" not in text, f"{path.name} still cites the old repository"
    assert "LICENSE.rst" not in text, f"{path.name} cites a licence file that does not exist"
