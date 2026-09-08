"""Authoritative definition of what a gDMbounds bound file is.

Every bound in the database is one ECSV file whose header carries the metadata
and whose table carries the limit curve. This module defines that contract and
nothing else: no plotting, no catalogue loading, no I/O beyond reading the
controlled vocabularies. Everything else in the package validates against it.

The header is the source of truth. The filename is a human-readable convention
that must agree with the header, and `check_file` enforces that agreement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from astropy import units as u
from astropy.io import ascii
from astropy.table import Table

DATA_DIR = Path(__file__).resolve().parent
BOUNDS_DIR = DATA_DIR / "bounds"
LEGENDS_DIR = DATA_DIR / "legends"

#: Metadata keys every bound file must carry.
#:
#: ``mode`` is included even though historical files predate it: a bound that
#: does not say whether it constrains annihilation or decay is not
#: self-describing, and these files are meant to be readable on their own.
REQUIRED_META = (
    "reference",
    "doi",
    "arxiv",
    "instrument",
    "year",
    "source",
    "mode",
    "channel",
    "confidence",
    "dmfraction",
    "obs_time",
    "figure",
    "comment",
    "status",
)

#: Recognised but not mandatory.
OPTIONAL_META = ("authors", "journalref")

#: DM process a bound constrains, and the observable each one limits.
MODES = {
    "ann": "annihilation",
    "dec": "decay",
}

#: The quantity each mode limits: the central-value column, the band columns
#: that may stand in for it, and the unit all of them carry.
#:
#: A sensitivity curve often gives only a band, with no central value, so a file
#: satisfies its mode by carrying either.
MODE_COLUMNS = {
    "ann": ("sigmav", ("sigmav_lo", "sigmav_hi"), "cm3s-1"),
    "dec": ("tau", ("tau_lo", "tau_hi"), "s"),
}

#: Accepted units for the mass column.
MASS_UNITS = ("GeV", "TeV")

#: ``<instrument>_<year>_<source>_<mode>_<channel>`` plus free-form qualifiers
#: such as ``_sens``, ``_einasto``, ``_measured``. The channel is the fifth
#: token, never simply the last one.
FILENAME_RE = re.compile(
    r"^(?P<instrument>[A-Za-z0-9-]+)"
    r"_(?P<year>\d{4})"
    r"_(?P<source>[A-Za-z0-9-]+)"
    r"_(?P<mode>ann|dec)"
    r"_(?P<channel>[A-Za-z0-9]+)"
    r"(?P<qualifiers>(?:_[A-Za-z0-9-]+)*)$"
)

#: Composite identifiers. A joint analysis is written ``multi-inst-<a>-<b>``
#: and a stacked target sample ``multi<class>[-<n>][-<member>...]``.
MULTI_INSTRUMENT_PREFIX = "multi-inst"
MULTI_SOURCE_PREFIX = "multi"


@dataclass
class Issue:
    """One schema violation, tied to the file it was found in."""

    path: Path
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"{self.path.name}: {self.kind} — {self.detail}"


@dataclass
class Vocabulary:
    """The controlled vocabularies, read from ``legends/``."""

    instruments: dict[str, str] = field(default_factory=dict)
    channels: dict[str, str] = field(default_factory=dict)
    targets: dict[str, str] = field(default_factory=dict)


def _read_legend(name: str, key: str, value: str) -> dict[str, str]:
    table = ascii.read(LEGENDS_DIR / f"legend_{name}.ecsv")
    return {str(row[key]): str(row[value]) for row in table}


def load_vocabulary() -> Vocabulary:
    """Read the controlled vocabularies that bound metadata must draw from."""
    return Vocabulary(
        instruments=_read_legend("instruments", "shortname", "longname"),
        channels=_read_legend("channels", "shortname", "latex"),
        targets=_read_legend("targets", "shortname", "longname"),
    )


def _same_unit(actual, expected: str) -> bool:
    """Compare units as physical quantities, not as strings.

    A file declaring ``cm3s-1`` is read back by astropy as ``cm3 / s``; the two
    are the same unit written differently.
    """
    if actual is None:
        return False
    try:
        return u.Unit(actual) == u.Unit(expected)
    except Exception:
        return False


def base_instrument(value: str) -> str:
    """Collapse a joint-analysis instrument to the token used as its directory."""
    if value.startswith(MULTI_INSTRUMENT_PREFIX):
        return MULTI_INSTRUMENT_PREFIX
    return value


def base_source(value: str) -> str:
    """Collapse a stacked target sample to its class token.

    ``multidsph-4-booetes1-draco`` and ``multidsph-14`` both describe samples of
    dwarf spheroidals, so both reduce to ``multidsph``.
    """
    if not value.startswith(MULTI_SOURCE_PREFIX):
        return value
    return value.split("-")[0]


def parse_filename(path: Path) -> dict[str, str] | None:
    """Split a bound filename into its conventional parts, or None if it does
    not follow the convention."""
    match = FILENAME_RE.match(path.stem)
    return match.groupdict() if match else None


def check_file(path: Path, vocabulary: Vocabulary | None = None) -> list[Issue]:
    """Check one bound file against the schema.

    Returns every problem found rather than raising on the first, so that a
    validation run reports the whole picture in one pass.
    """
    issues: list[Issue] = []

    def report(kind: str, detail: str) -> None:
        issues.append(Issue(path=path, kind=kind, detail=detail))

    try:
        table: Table = ascii.read(path, format="ecsv")
    except Exception as exc:  # astropy raises a variety of parse errors
        report("unreadable", f"{type(exc).__name__}: {str(exc).splitlines()[0]}")
        return issues

    meta = {str(k): v for k, v in table.meta.items()}

    for key in REQUIRED_META:
        if key not in meta:
            report("missing-key", f"required metadata key '{key}' absent")

    mode = str(meta.get("mode", ""))
    if mode and mode not in MODES:
        report("bad-value", f"mode '{mode}' is not one of {sorted(MODES)}")

    if vocabulary is not None:
        instrument = base_instrument(str(meta.get("instrument", "")))
        if instrument and instrument not in vocabulary.instruments:
            report("unknown-instrument", f"'{instrument}' is not in legend_instruments")

        channel = str(meta.get("channel", ""))
        if channel and channel not in vocabulary.channels:
            report("unknown-channel", f"'{channel}' is not in legend_channels")

        source = base_source(str(meta.get("source", "")))
        if source and source not in vocabulary.targets:
            report("unknown-target", f"'{source}' is not in legend_targets")

    _check_columns(table, mode, report)
    _check_filename_agrees(path, meta, report)

    return issues


def _check_columns(table: Table, mode: str, report) -> None:
    """Verify the table carries the quantity its mode implies, in the right unit."""
    if "mass" not in table.colnames:
        report("bad-table", "no 'mass' column")
    elif not any(_same_unit(table["mass"].unit, m) for m in MASS_UNITS):
        report(
            "bad-unit",
            f"mass is in '{table['mass'].unit}', expected one of {MASS_UNITS}",
        )

    if mode in MODE_COLUMNS:
        central, bands, expected_unit = MODE_COLUMNS[mode]
        candidates = (central, *bands)
        present = [c for c in candidates if c in table.colnames]
        if not present:
            report(
                "bad-table",
                f"mode '{mode}' requires '{central}' or the bands {list(bands)}",
            )
        for column in present:
            if not _same_unit(table[column].unit, expected_unit):
                report(
                    "bad-unit",
                    f"{column} is in '{table[column].unit}', expected '{expected_unit}'",
                )


def _check_filename_agrees(path: Path, meta: dict, report) -> None:
    """Verify the filename convention matches the authoritative header."""
    parts = parse_filename(path)
    if parts is None:
        report(
            "bad-filename",
            "does not match <instrument>_<year>_<source>_<mode>_<channel>[_...]",
        )
        return

    comparisons = (
        ("instrument", str(meta.get("instrument", ""))),
        ("year", str(meta.get("year", ""))),
        ("source", base_source(str(meta.get("source", "")))),
        ("mode", str(meta.get("mode", ""))),
        ("channel", str(meta.get("channel", ""))),
    )
    for name, from_meta in comparisons:
        if not from_meta:
            continue
        if parts[name] != from_meta:
            report(
                "filename-mismatch",
                f"filename says {name}='{parts[name]}', header says '{from_meta}'",
            )


def iter_bound_files(root: Path | None = None):
    """Yield every bound file in the database, in a stable order."""
    root = root or BOUNDS_DIR
    return sorted(root.glob("*/*.ecsv"))


def check_database(root: Path | None = None) -> list[Issue]:
    """Check every bound file. This is what CI runs."""
    vocabulary = load_vocabulary()
    issues: list[Issue] = []
    for path in iter_bound_files(root):
        issues.extend(check_file(path, vocabulary))
    return issues
