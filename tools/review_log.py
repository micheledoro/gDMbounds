"""Read `review_log.yaml`, the hand-kept record of which papers have been read.

Two documents in this repository are generated and must never be edited by
hand, because a committed copy of derived information goes stale silently. A
review outcome is not derived from anything — it exists only because someone
read a paper — so it needs a place to be written that no tool overwrites. That
place is `review_log.yaml`; `data_review.py` merges it into DATA_REVIEW.md, so
the log is where one writes and the generated document is where one reads.

Keeping the outcome here rather than in the ECSV headers was a deliberate
choice: a review is about a paper, and a paper's bounds are spread across many
files that would each have to carry — and agree on — the same verdict.

PyYAML is not declared as a dependency because astropy requires it: the ECSV
format this database is written in is parsed with it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "review_log.yaml"

VERDICTS = ("ok", "corrected", "open")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class Entry:
    """One paper, read by one person on one day."""

    identifier: str
    reviewer: str
    date: str
    verdict: str
    notes: str = ""
    #: Filename -> what was decided about it, for the questions a review settled.
    decisions: dict = field(default_factory=dict)


def load(path: Path | None = None) -> tuple[dict[str, Entry], list[str]]:
    """Every entry in the log, and every complaint about how it is written.

    A malformed entry is reported rather than raised: the generator still has a
    document to produce, and the test suite is where a complaint becomes a
    failure.
    """
    path = path or LOG
    if not path.exists():
        return {}, []

    document = yaml.safe_load(path.read_text()) or {}
    if not isinstance(document, dict):
        return {}, [f"{path.name}: the file must hold a mapping"]

    raw = document.get("reviewed") or {}
    if not isinstance(raw, dict):
        return {}, [f"{path.name}: `reviewed` must be a mapping of identifier to entry"]

    entries: dict[str, Entry] = {}
    problems: list[str] = []
    for identifier, body in raw.items():
        identifier = str(identifier)
        if not isinstance(body, dict):
            problems.append(f"{identifier}: the entry must be a mapping")
            continue

        reviewer = str(body.get("reviewer", "")).strip()
        date = str(body.get("date", "")).strip()
        verdict = str(body.get("verdict", "")).strip()
        notes = str(body.get("notes", "")).strip()
        decisions = body.get("decisions") or {}

        if not reviewer:
            problems.append(f"{identifier}: no reviewer")
        if not DATE.match(date):
            problems.append(f"{identifier}: date {date!r} is not YYYY-MM-DD")
        if verdict not in VERDICTS:
            problems.append(
                f"{identifier}: verdict {verdict!r} is not one of {list(VERDICTS)}"
            )
        if verdict == "open" and not notes:
            problems.append(
                f"{identifier}: verdict 'open' with no notes — the log is the only "
                "record of what is still wrong"
            )
        if not isinstance(decisions, dict):
            problems.append(f"{identifier}: `decisions` must map a filename to a reason")
            decisions = {}

        entries[identifier] = Entry(
            identifier=identifier,
            reviewer=reviewer,
            date=date,
            verdict=verdict,
            notes=notes,
            decisions={str(k): str(v).strip() for k, v in decisions.items()},
        )
    return entries, problems


def check_against(entries: dict[str, Entry], papers: dict) -> list[str]:
    """Complaints about entries that name something the database does not hold.

    An identifier that matches no paper is usually a typo, and silently reviewing
    nothing is worse than a stale entry: the progress count would say the work is
    done.
    """
    known = {paper.identifier: paper for paper in papers.values()}
    problems = []
    for identifier, entry in sorted(entries.items()):
        paper = known.get(identifier)
        if paper is None:
            problems.append(
                f"{identifier}: no paper in the database carries this identifier"
            )
            continue
        for filename in sorted(entry.decisions):
            if filename not in paper.files:
                problems.append(
                    f"{identifier}: decision names `{filename}`, which is not one of "
                    "that paper's bounds"
                )
    return problems


def decisions_by_file(entries: dict[str, Entry]) -> dict[str, str]:
    """Every per-file decision in the log, flattened for annotating a finding."""
    out: dict[str, str] = {}
    for entry in entries.values():
        for filename, reason in entry.decisions.items():
            out[filename] = reason
    return out
