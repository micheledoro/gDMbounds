"""Generate DATA_REVIEW.md — the list of bounds that need a human decision.

Written as a generator rather than a hand-kept list so that it cannot drift from
the data. Re-run it after touching the database:

    python tools/data_review.py

The findings here are deliberately *not* CI failures. CI enforces what can be
decided mechanically — a file parses, its keys are present, its filename agrees
with its header. What is collected here needs someone to read a paper or make a
judgement, and a test suite cannot do either. The quarantine in
tests/test_data_quality.py is the machine-enforced subset; this is the reasoning.

Part of this document is not derived from the data at all: `review_log.yaml`
records which papers have been read against their source, and that can only come
from a person. It is merged in here so that there is one place to look. Write
outcomes in the log — anything typed into this document is lost on the next run.
"""

from __future__ import annotations

import collections
import hashlib
import re
from pathlib import Path

import numpy as np
import paper_index
import review_log
from astropy.io import ascii

from gdmbounds import quality, schema

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "DATA_REVIEW.md"


def load():
    paths = schema.iter_bound_files()
    return {p: ascii.read(p, format="ecsv") for p in paths}


def identical_curves(tables) -> list[list[str]]:
    """Bounds whose numbers are byte-for-byte the same as another's.

    Two different measurements producing an identical curve does not happen.
    """
    seen = collections.defaultdict(list)
    for path, table in tables.items():
        cols = [c for c in ("mass", "sigmav", "tau") if c in table.colnames]
        if len(cols) < 2:
            continue
        block = np.column_stack([np.asarray(table[c], float) for c in cols])
        digest = hashlib.md5(np.ascontiguousarray(block)).hexdigest()
        seen[digest].append(path.name)
    return [names for names in seen.values() if len(names) > 1]


def non_numeric_confidence(tables):
    out = []
    for path, table in tables.items():
        value = str(table.meta.get("confidence", ""))
        try:
            float(value)
        except ValueError:
            out.append((path.name, value))
    return out


def missing_field(tables, key):
    return [p.name for p, t in tables.items() if not str(t.meta.get(key, "")).strip()]


#: Instrument classes for which an exposure in hours is not a meaningful
#: quantity, so a blank obs_time is correct rather than missing.
NO_EXPOSURE = {"collider", "direct"}


def obs_time_without_a_number(tables, vocabulary):
    out = collections.defaultdict(list)
    for path, table in tables.items():
        instrument = schema.base_instrument(str(table.meta.get("instrument", "")))
        if vocabulary.instrument_class.get(instrument) in NO_EXPOSURE:
            continue
        value = str(table.meta.get("obs_time", ""))
        if not re.search(r"\d", value):
            out[value or "(empty)"].append(path.name)
    return out


def section(title, body):
    return f"## {title}\n\n{body}\n"


def decided(names, decisions, name_each=False):
    """The `reviewed:` lines for whichever of these files the log has settled.

    `name_each` where the bullet above covers several files, so that a decision
    cannot be read against the wrong one.
    """
    return [
        f"  - `{n}` reviewed: {decisions[n]}" if name_each else f"  - reviewed: {decisions[n]}"
        for n in sorted(names)
        if n in decisions
    ]


def bullet_files(names, note="", decisions=None):
    """A list of files, each carrying whatever the review log decided about it.

    An entry that has been settled stays listed: the finding is still true of the
    data until the file changes, and hiding it would make a decision look like a
    fix.
    """
    decisions = decisions or {}
    lines = []
    for name in sorted(names):
        lines.append(f"- `{name}`")
        if name in decisions:
            lines.append(f"  - reviewed: {decisions[name]}")
    body = "\n".join(lines)
    return body + (f"\n\n{note}" if note else "")


def escape(text: str) -> str:
    """Make a value safe to drop into a table cell."""
    return str(text).replace("|", "\\|").strip()


def review_progress(papers, entries):
    """The state of the paper-by-paper review: what has been read, what is left.

    The queue is ordered by how many bounds each paper accounts for, because the
    distribution is steep — the heaviest paper settles 34 of them — and reading
    in that order clears the archive fastest.
    """
    parts = [
        "# Review progress\n",
        "*The outcome of reading each paper against its bounds. Merged from "
        "`review_log.yaml`, which is kept by hand — record a review there and it "
        "appears here.*\n",
    ]

    read = [
        (paper, entries[paper.identifier])
        for paper in paper_index.by_weight(papers)
        if paper.identifier in entries
    ]
    if read:
        rows = ["## Papers read\n"]
        for paper, entry in read:
            rows.append(
                f"### {paper.year} — `{paper.identifier}` — {entry.verdict}\n"
            )
            rows.append(
                f"{escape(paper.reference)}  \n"
                f"{len(paper.files)} bound(s), read by {escape(entry.reviewer)} "
                f"on {entry.date}.\n"
            )
            if entry.notes:
                rows.append(entry.notes + "\n")
        parts += rows
    else:
        parts.append(
            "No paper has been recorded as read yet. Nothing below has been "
            "checked against its source.\n"
        )

    queue = [p for p in paper_index.by_weight(papers) if p.identifier not in entries]
    if queue:
        table = [
            "## The queue\n",
            "Heaviest first: the number of bounds a single reading settles.\n",
            "| bounds | identifier | year | in | paper |",
            "|---:|---|---:|---|---|",
        ]
        for paper in queue:
            reference = escape(paper.reference)
            if len(reference) > 70:
                reference = reference[:69].rstrip() + "…"
            table.append(
                f"| {len(paper.files)} | `{escape(paper.identifier)}` | {paper.year} "
                f"| {', '.join(paper.instruments)} | {reference} |"
            )
        parts.append("\n".join(table) + "\n")
    else:
        parts.append("## The queue\n\nEvery paper in the database has been read.\n")

    return parts


def main() -> int:
    tables = load()
    papers = paper_index.collect()
    entries, complaints = review_log.load()
    decisions = review_log.decisions_by_file(entries)
    curve_issues = collections.defaultdict(list)
    for issue in quality.check_all_curves():
        curve_issues[issue.kind].append((issue.path.name, issue.detail))

    parts = [
        "# Data review\n",
        f"*Generated by `tools/data_review.py` from {len(tables)} bounds. Do not edit "
        "by hand — re-run the tool; `pytest` fails if this file is out of date.*\n",
        "Everything listed here passes the schema. These are questions the schema "
        "cannot answer: they need someone to read a paper or make a judgement. "
        "CI does not fail on them.\n",
    ]

    # ---------------------------------------------------------------- blocking
    blocking = []

    duplicates = identical_curves(tables)
    if duplicates:
        note = (
            "Two independent measurements do not produce the same numbers. One file "
            "in each group carries data copied from the other, and the paper decides "
            "which."
        )
        lines = []
        for group in duplicates:
            lines.append("- " + " == ".join(f"`{n}`" for n in group))
            lines += decided(group, decisions, name_each=True)
        blocking.append(section(
            "Identical curves in different files",
            "\n".join(lines) + f"\n\n{note}",
        ))

    contours = curve_issues.get("closed-contour", [])
    if contours:
        blocking.append(section(
            "Closed contours stored as limits",
            bullet_files(
                [n for n, _ in contours],
                "The curve climbs in mass, turns, and returns to near its starting "
                "point. That is a region in the plane, not an upper limit on a "
                "function of mass: it cannot be plotted or interpolated as one. "
                "Either the transcription is wrong, or the file should carry "
                "`statement: \"detection\"`.",
                decisions,
            ),
        ))

    bad_confidence = non_numeric_confidence(tables)
    if bad_confidence:
        lines = []
        for name, value in sorted(bad_confidence):
            lines.append(f"- `{name}` — `{value}`")
            lines += decided([name], decisions)
        blocking.append(section(
            "`confidence` is not a confidence level",
            "\n".join(lines)
            + "\n\nThese files describe a median expected curve, and the word landed "
              "in the confidence field. They are also marked `statement: \"limit\"`, "
              "which an expected curve is not. Both need correcting together, and "
              "the actual confidence level has to come from the paper.",
        ))

    # ------------------------------------------------------------------ sorting
    unsorted = curve_issues.get("unsorted-mass", [])
    duplicated_mass = curve_issues.get("duplicate-mass", [])
    ordering = []
    if unsorted or duplicated_mass:
        names = sorted({n for n, _ in unsorted} | {n for n, _ in duplicated_mass})
        ordering.append(section(
            "Curves whose points are out of order or repeated",
            bullet_files(
                names,
                "Consistent with noise in digitising a published figure. Sorting by "
                "mass reorders rows and changes no value, and for "
                "`magic_2022_segue1_ann_bb` that fix was confirmed independently "
                "upstream. It still edits a published curve, so each file wants a "
                "decision rather than a sweep.",
                decisions,
            ),
        ))

    # --------------------------------------------------------------- provenance
    provenance = []
    no_figure = missing_field(tables, "figure")
    if no_figure:
        provenance.append(section(
            "No `figure` recorded",
            bullet_files(
                no_figure,
                "Every bound is a transcription from a published plot or table. "
                "Without the figure, the curve cannot be checked against its source.",
                decisions,
            ),
        ))

    for key, title in (("doi", "No DOI"), ("arxiv", "No arXiv identifier")):
        missing = missing_field(tables, key)
        if missing:
            provenance.append(section(
                title,
                bullet_files(missing, "Each still carries the other identifier, so "
                                      "the source is reachable.", decisions),
            ))

    conflicts = paper_index.identifier_conflicts()
    if conflicts:
        rows = []
        for arxiv, dois in conflicts:
            rows.append(f"- arXiv `{arxiv}` is cited under {len(dois)} DOIs:")
            rows += [f"  - `{doi}`" for doi in dois]
        provenance.append(section(
            "One paper cited under more than one DOI",
            "\n".join(rows) + "\n\nNot necessarily wrong: a paper and its erratum "
            "carry different DOIs, and a curve taken from a corrected figure should "
            "cite the correction. What it does mean is that the figures of that "
            "paper are not all being read from the same version, so a review has to "
            "establish which curves the erratum superseded and check that each file "
            "cites the version it was actually transcribed from. The alternative "
            "reading — that a DOI was mistyped — leads to the same place.",
        ))

    obs = obs_time_without_a_number(tables, schema.load_vocabulary())
    if obs:
        rows = []
        for value, names in sorted(obs.items()):
            rows.append(f"- `{value}` — {len(names)} file(s)")
            if len(names) <= 12:
                rows += [f"  - `{n}`" for n in sorted(names)]
        rows = "\n".join(rows)
        provenance.append(section(
            "`obs_time` without a number",
            rows + "\n\nExposure is part of what makes a limit comparable to "
                   "another, and `h` states a unit with no quantity. Collider and "
                   "direct-detection bounds are excluded: an exposure in hours is not "
                   "a meaningful quantity for them, so a blank field is correct.",
        ))

    blocking_count = (
        sum(len(group) for group in duplicates) + len(contours) + len(bad_confidence)
    )
    misordered = {name for name, _ in unsorted} | {name for name, _ in duplicated_mass}
    reviewed = [p for p in papers.values() if p.identifier in entries]
    covered = sum(len(p.files) for p in reviewed)
    parts.append(
        "| | |\n|---|---:|\n"
        f"| bounds checked | {len(tables)} |\n"
        f"| papers behind them | {len(papers)} |\n"
        f"| papers read against their source | {len(reviewed)} of {len(papers)} |\n"
        f"| bounds those readings cover | {covered} |\n"
        f"| needing a decision before use | {blocking_count} |\n"
        f"| points out of order or repeated | {len(misordered)} |\n"
        f"| missing a figure reference | {len(no_figure)} |\n"
    )
    parts += review_progress(papers, entries)
    parts += ["# Needs a decision before the data can be trusted\n", *blocking]
    parts += ["# Needs a decision, lower stakes\n", *ordering]
    parts += ["# Provenance gaps\n", *provenance]

    OUT.write_text("\n".join(parts))
    print(f"{OUT.name}: {blocking_count} blocking, {len(misordered)} ordering, "
          f"{len(no_figure)} without a figure; "
          f"{len(reviewed)}/{len(papers)} papers read")

    # Kept out of the document itself: a malformed log is a problem with the log,
    # not a finding about the data. tests/test_review_log.py fails on these.
    for complaint in complaints + review_log.check_against(entries, papers):
        print(f"review_log.yaml: {complaint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
