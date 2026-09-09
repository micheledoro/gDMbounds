"""Group the database by the paper each bound was transcribed from.

The unit of a data review is the paper, not the file. 385 bounds come from 57
papers, and the question a review answers — does this curve match the figure it
cites — is asked once per paper and then settled for every curve that paper
produced. The distribution is steep: the largest paper accounts for 34 bounds,
the largest five for 113.

A paper is identified by its arXiv id where it has one, and by its DOI
otherwise. arXiv comes first deliberately: it is the identifier that can be
fetched (see `fetch_papers.py`), and a DOI transcribed by hand is the one that
has already been seen to disagree between files citing the same work.

Nothing here writes a document; `data_review.py` and `fetch_papers.py` both
read from it. It is not called `papers.py`: the directory holding the PDFs is
`papers/`, and an import of that name could reach the directory instead of this
module depending on how the path is ordered.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from astropy.io import ascii

from gdmbounds import schema

ROOT = Path(__file__).resolve().parent.parent
PAPERS_DIR = ROOT / "papers"

#: 2401.12345, with an optional version suffix.
ARXIV_MODERN = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
#: astro-ph/0611502 and its siblings, used before April 2007.
ARXIV_LEGACY = re.compile(r"^[a-z-]+(\.[A-Z]{2})?/\d{7}(v\d+)?$")


def normalise_arxiv(value: object) -> str:
    """The bare arXiv id in a header field, or "" if the field holds something else.

    Headers have been seen carrying a full URL, an `arXiv:` prefix, and — in one
    case — a conference-proceedings link in the arXiv field. The last is not an
    arXiv id and must not be treated as one.
    """
    text = str(value or "").strip()
    for prefix in ("arxiv:", "arXiv:", "https://arxiv.org/abs/", "http://arxiv.org/abs/"):
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):]
    text = text.strip().rstrip("/")
    if ARXIV_MODERN.match(text) or ARXIV_LEGACY.match(text):
        return text
    return ""


def normalise_doi(value: object) -> str:
    """The bare DOI in a header field, or "" if the field is empty."""
    text = str(value or "").strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:", "DOI:"):
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):]
    return text.strip().rstrip("/")


@dataclass(frozen=True)
class Paper:
    """One published work, and every bound transcribed from it."""

    key: str
    reference: str
    year: str
    doi: str
    arxiv: str
    files: tuple[str, ...]
    instruments: tuple[str, ...]

    @property
    def identifier(self) -> str:
        """The identifier the key was built from, without its kind prefix."""
        return self.key.split(":", 1)[1]

    @property
    def stem(self) -> str:
        """Filename stem for this paper's PDF, readable and stable.

        `2012_hess_1202.5494`. Sorting the directory sorts by year, which is the
        order a reviewer works in; the identifier keeps it unambiguous. Slashes
        in a legacy arXiv id or a DOI cannot appear in a filename.
        """
        instrument = self.instruments[0] if self.instruments else "unknown"
        return f"{self.year}_{instrument}_{self.identifier}".replace("/", "-")

    def pdf(self, directory: Path | None = None) -> Path | None:
        """The PDF held for this paper, or None if it has not been downloaded.

        Matched on the identifier rather than the whole stem, so that renaming a
        file by hand — to add a first author, say — does not lose it.
        """
        directory = directory or PAPERS_DIR
        if not directory.is_dir():
            return None
        wanted = self.identifier.replace("/", "-")
        for path in sorted(directory.glob("*.pdf")):
            if wanted in path.stem:
                return path
        return None


def collect(root: Path | None = None) -> dict[str, Paper]:
    """Every paper in the database, keyed by `arxiv:<id>` or `doi:<id>`."""
    grouped: dict[str, dict] = {}
    for path in schema.iter_bound_files(root):
        meta = ascii.read(path, format="ecsv").meta
        arxiv = normalise_arxiv(meta.get("arxiv"))
        doi = normalise_doi(meta.get("doi"))
        key = f"arxiv:{arxiv}" if arxiv else f"doi:{doi}" if doi else "unidentified"
        entry = grouped.setdefault(
            key,
            {
                "reference": str(meta.get("reference", "")).strip(),
                "year": str(meta.get("year", "")).strip(),
                "doi": doi,
                "arxiv": arxiv,
                "files": [],
                "instruments": set(),
            },
        )
        entry["files"].append(path.name)
        entry["instruments"].add(path.parent.name)

    return {
        key: Paper(
            key=key,
            reference=entry["reference"],
            year=entry["year"],
            doi=entry["doi"],
            arxiv=entry["arxiv"],
            files=tuple(sorted(entry["files"])),
            instruments=tuple(sorted(entry["instruments"])),
        )
        for key, entry in sorted(grouped.items())
    }


def by_weight(papers: dict[str, Paper]) -> list[Paper]:
    """Papers ordered by how much of the archive they account for, heaviest first."""
    return sorted(papers.values(), key=lambda p: (-len(p.files), p.year, p.key))


def identifier_conflicts(root: Path | None = None) -> list[tuple[str, list[str]]]:
    """Papers whose files disagree about an identifier.

    One arXiv id belongs to one work. Files citing the same arXiv id under two
    DOIs mean a DOI was mistyped in some of them, and until it is fixed the
    archive holds one paper twice under different names.
    """
    seen: dict[str, dict[str, list[str]]] = {}
    for path in schema.iter_bound_files(root):
        meta = ascii.read(path, format="ecsv").meta
        arxiv = normalise_arxiv(meta.get("arxiv"))
        doi = normalise_doi(meta.get("doi"))
        if arxiv and doi:
            seen.setdefault(arxiv, {}).setdefault(doi, []).append(path.name)
    return [
        (arxiv, sorted(dois))
        for arxiv, dois in sorted(seen.items())
        if len(dois) > 1
    ]
