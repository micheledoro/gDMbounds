"""Generated documents must match what their tool produces right now.

`VOCABULARY.md` and `DATA_REVIEW.md` are committed so they can be browsed on
GitHub without running anything. That convenience is also the risk: a committed
copy of derived information goes stale the moment someone changes the source and
forgets to regenerate, and then it lies with authority.

These tests remove the risk. Add a class, fix a bound, and the suite fails until
the document is regenerated. Both tools are deliberately free of timestamps so
that regenerating is a no-op when nothing has changed.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

GENERATED = {
    "VOCABULARY.md": "tools/vocabulary_reference.py",
    "DATA_REVIEW.md": "tools/data_review.py",
}


@pytest.mark.parametrize("document, tool", sorted(GENERATED.items()))
def test_generated_document_is_current(document, tool, tmp_path):
    path = ROOT / document
    assert path.exists(), f"{document} is missing; run `python {tool}`"

    before = path.read_text()
    backup = tmp_path / document
    backup.write_text(before)
    try:
        result = subprocess.run(
            [sys.executable, tool], cwd=ROOT, capture_output=True, text=True
        )
        assert result.returncode == 0, f"{tool} failed:\n{result.stderr}"
        after = path.read_text()
    finally:
        path.write_text(before)

    assert after == before, (
        f"{document} is out of date. Run `python {tool}` and commit the result."
    )


def test_every_generator_is_registered():
    """A new tool that writes a document must be covered here too."""
    writers = set()
    for tool in (ROOT / "tools").glob("*.py"):
        text = tool.read_text()
        if "OUT = ROOT /" in text and "write_text" in text:
            writers.add(f"tools/{tool.name}")
    assert writers == set(GENERATED.values()), (
        f"tools writing a document: {sorted(writers)}; "
        f"registered here: {sorted(GENERATED.values())}"
    )
