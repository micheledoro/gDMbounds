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
    "origin",
    "statement",
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
#:
#: ``profile`` is optional because the filename records it for only about a
#: quarter of the database. Its absence means the assumed halo profile was not
#: written down, **not** that none was assumed — every J-factor rests on one. Any
#: selection filtering on ``profile`` silently drops the rest, and should say so.
OPTIONAL_META = ("authors", "journalref", "profile", "bibcode", "url")

#: Who produced a bound. A forecast or reinterpretation published by individual
#: authors is not the same kind of result as a collaboration measurement, and
#: users need to be able to include or exclude them deliberately.
ORIGINS = {
    "collaboration": "published by the experiment collaboration",
    "author": "forecast or reinterpretation by individual authors",
}

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

#: Optional data columns a bound may carry beyond its central curve, and what
#: each means. A combined analysis often publishes the limit it observed
#: alongside the limit it expected under the null hypothesis, and the two must
#: not be confused: the observed one is the result, the expected one says how
#: lucky or unlucky the observation was.
OPTIONAL_COLUMNS = {
    "sigmav_expected": "median limit expected under the null hypothesis",
    "sigmav_1sigma_lo": "lower edge of the 68% containment band",
    "sigmav_1sigma_hi": "upper edge of the 68% containment band",
    "sigmav_2sigma_lo": "lower edge of the 95% containment band",
    "sigmav_2sigma_hi": "upper edge of the 95% containment band",
    "sigmav_lo": "lower edge of a band whose level is not stated",
    "sigmav_hi": "upper edge of a band whose level is not stated",
}

#: Accepted units for the mass column.
#:
#: keV and MeV admit X-ray searches for light dark matter, which constrain the
#: same annihilation cross-section over a mass range twelve orders of magnitude
#: below the gamma-ray one.
MASS_UNITS = ("keV", "MeV", "GeV", "TeV")

#: What kind of statement a bound makes. Mixing these on one figure without
#: distinguishing them is the most misleading thing this database could do: a
#: projected sensitivity for an instrument that is not yet operating is not
#: evidence about the universe in the way a measured limit is.
STATEMENTS = {
    "limit": "upper limit derived from observed data",
    "sensitivity": "projected reach of an instrument or exposure",
    "detection": "claimed signal region rather than an exclusion",
}

#: Assumed dark matter halo density profile. Two limits computed under different
#: profiles are not directly comparable, because the J-factor differs.
PROFILES = {
    "nfw": "Navarro-Frenk-White, including contracted and rescaled variants",
    "einasto": "Einasto",
    "burkert": "Burkert",
    "isothermal": "isothermal / cored isothermal",
    "cored": "cored, family unspecified",
    "cusped": "cusped, family unspecified",
}

#: How an instrument detects gamma rays. Bounds from different techniques cover
#: different energy ranges and carry different systematics, so this is the axis
#: along which "all the Cherenkov telescopes" is a meaningful selection.
INSTRUMENT_CLASSES = {
    "iact": "Imaging Atmospheric Cherenkov Telescope",
    "satellite": "satellite-borne pair-conversion detector",
    "xray": "satellite-borne X-ray telescope",
    "sfd": "shower-front detector array",
    "radio": "radio interferometer",
    "collider": "collider search",
    "direct": "direct-detection experiment",
    "combined": "joint analysis across instruments",
}

#: What kind of object the bound looks at. Targets in one class share a dark
#: matter density profile family and a set of astrophysical uncertainties.
TARGET_CLASSES = {
    "dsph": "dwarf spheroidal galaxy",
    "cluster": "galaxy cluster",
    "globular": "globular cluster",
    "galaxy": "galaxy",
    "gc": "Galactic Centre and Milky Way halo",
    "diffuse": "diffuse or extragalactic emission",
    "subhalo": "dark matter subhalo",
    "unid": "unidentified source",
    "collider": "collider search",
    "direct": "direct-detection experiment",
}

#: The spectral shape a channel produces. A line and a continuum bound are not
#: directly comparable, and plotting them on one axis without saying so misleads.
CHANNEL_SPECTRA = {
    "continuum": "broad spectrum from hadronisation or cascade",
    "line": "monochromatic feature at the dark matter mass",
    "model": "specific model with both line and continuum features",
    "benchmark": "individual benchmark points rather than a curve",
}

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
    """The controlled vocabularies, read from ``legends/``.

    Each term maps to its display name, and separately to the class it belongs
    to. The classes are what makes a selection like "every IACT bound" or "every
    dwarf spheroidal" expressible without listing members by hand.
    """

    instruments: dict[str, str] = field(default_factory=dict)
    channels: dict[str, str] = field(default_factory=dict)
    targets: dict[str, str] = field(default_factory=dict)
    instrument_class: dict[str, str] = field(default_factory=dict)
    target_class: dict[str, str] = field(default_factory=dict)
    channel_spectrum: dict[str, str] = field(default_factory=dict)

    def instruments_in(self, klass: str) -> list[str]:
        """Every instrument using a given detection technique."""
        return sorted(k for k, v in self.instrument_class.items() if v == klass)

    def targets_in(self, klass: str) -> list[str]:
        """Every target of a given type."""
        return sorted(k for k, v in self.target_class.items() if v == klass)

    def channels_with(self, spectrum: str) -> list[str]:
        """Every channel producing a given spectral shape."""
        return sorted(k for k, v in self.channel_spectrum.items() if v == spectrum)

    def describe(self) -> str:
        """A readable summary of every class and its members."""
        blocks = []
        for title, classes, membership in (
            ("Instrument classes", INSTRUMENT_CLASSES, self.instrument_class),
            ("Target classes", TARGET_CLASSES, self.target_class),
            ("Channel spectra", CHANNEL_SPECTRA, self.channel_spectrum),
        ):
            lines = [title, "-" * len(title)]
            for key, description in classes.items():
                members = sorted(k for k, v in membership.items() if v == key)
                lines.append(f"  {key:<10} {description}")
                lines.append(f"             {', '.join(members) or '(none)'}")
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)


def _read_legend(name: str, key: str, *values: str) -> tuple[dict[str, str], ...]:
    table = ascii.read(LEGENDS_DIR / f"legend_{name}.ecsv")
    return tuple(
        {str(row[key]): str(row[value]) for row in table} for value in values
    )


def load_vocabulary() -> Vocabulary:
    """Read the controlled vocabularies that bound metadata must draw from."""
    instruments, instrument_class = _read_legend(
        "instruments", "shortname", "longname", "class"
    )
    channels, channel_spectrum = _read_legend(
        "channels", "shortname", "latex", "spectrum"
    )
    targets, target_class = _read_legend("targets", "shortname", "longname", "class")
    return Vocabulary(
        instruments=instruments,
        channels=channels,
        targets=targets,
        instrument_class=instrument_class,
        target_class=target_class,
        channel_spectrum=channel_spectrum,
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

    origin = str(meta.get("origin", ""))
    if origin and origin not in ORIGINS:
        report("bad-value", f"origin '{origin}' is not one of {sorted(ORIGINS)}")

    statement = str(meta.get("statement", ""))
    if statement and statement not in STATEMENTS:
        report(
            "bad-value", f"statement '{statement}' is not one of {sorted(STATEMENTS)}"
        )

    profile = str(meta.get("profile", ""))
    if profile and profile not in PROFILES:
        report("bad-value", f"profile '{profile}' is not one of {sorted(PROFILES)}")

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


def check_vocabulary(vocabulary: Vocabulary | None = None) -> list[Issue]:
    """Check that the legends classify every term into a known class.

    The legends are hand-edited, and a class column is exactly the kind of thing
    that acquires a typo or gets left blank on a new row.
    """
    vocabulary = vocabulary or load_vocabulary()
    issues: list[Issue] = []
    for legend, membership, allowed, label in (
        ("instruments", vocabulary.instrument_class, INSTRUMENT_CLASSES, "class"),
        ("targets", vocabulary.target_class, TARGET_CLASSES, "class"),
        ("channels", vocabulary.channel_spectrum, CHANNEL_SPECTRA, "spectrum"),
    ):
        path = LEGENDS_DIR / f"legend_{legend}.ecsv"
        for term, value in sorted(membership.items()):
            if not value or value == "--":
                issues.append(Issue(path, "unclassified", f"'{term}' has no {label}"))
            elif value not in allowed:
                issues.append(
                    Issue(
                        path,
                        "unknown-class",
                        f"'{term}' has {label} '{value}', not one of {sorted(allowed)}",
                    )
                )
    return issues


def check_database(root: Path | None = None) -> list[Issue]:
    """Check every bound file. This is what CI runs."""
    vocabulary = load_vocabulary()
    issues: list[Issue] = []
    for path in iter_bound_files(root):
        issues.extend(check_file(path, vocabulary))
    return issues
