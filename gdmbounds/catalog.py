"""One queryable table over the whole database.

Answering "every MAGIC dwarf-spheroidal bb limit" by hand means opening 367 files
and filtering their headers, and every piece of code that wants to do it writes
that loop again. The catalogue reads the headers once into a table whose rows are
bounds and whose columns are the metadata, joined with the classes from the
legends, and gives selection over it.

Selecting does not read any curve. `select` returns another catalogue, so
criteria compose; the ECSV tables are only touched when `curves` is called. The
whole database reads in about a second, so this is not about speed — it is about
being able to say what you want in one expression instead of a loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd
from astropy.io import ascii
from astropy.table import Table

from . import schema


def _row(path: Path, meta: dict, vocabulary: schema.Vocabulary) -> dict[str, Any]:
    instrument = str(meta.get("instrument", ""))
    source = str(meta.get("source", ""))
    key = schema.base_instrument(instrument)
    target = schema.base_source(source)

    # A joint analysis names its members after the multi-inst prefix; a single
    # instrument is a one-element tuple, so `involves` works the same for both.
    members = (
        tuple(instrument[len(schema.MULTI_INSTRUMENT_PREFIX) + 1:].split("-"))
        if key == schema.MULTI_INSTRUMENT_PREFIX and "-" in instrument
        else (key,)
    )

    row: dict[str, Any] = {
        "path": path,
        "instrument": key,
        "instruments": members,
        "instrument_class": vocabulary.instrument_class.get(key, ""),
        "source": source,
        "target": target,
        "target_class": vocabulary.target_class.get(target, ""),
        "channel_spectrum": vocabulary.channel_spectrum.get(
            str(meta.get("channel", "")), ""
        ),
    }
    for key_name in (*schema.REQUIRED_META, *schema.OPTIONAL_META):
        if key_name not in ("instrument", "source"):
            row[key_name] = str(meta.get(key_name, ""))
    row["year"] = pd.to_numeric(row.get("year"), errors="coerce")
    return row


@dataclass(frozen=True)
class Catalog:
    """A set of bounds and their metadata."""

    frame: pd.DataFrame

    @classmethod
    def load(cls, root: Path | None = None) -> Catalog:
        """Read every bound's header into a table."""
        vocabulary = schema.load_vocabulary()
        rows = [
            _row(path, ascii.read(path, format="ecsv").meta, vocabulary)
            for path in schema.iter_bound_files(root)
        ]
        return cls(pd.DataFrame(rows))

    def __len__(self) -> int:
        return len(self.frame)

    def __iter__(self):
        return iter(self.frame.itertuples(index=False))

    def __repr__(self) -> str:
        if self.frame.empty:
            return "<Catalog: no bounds>"
        instruments = ", ".join(sorted(self.frame["instrument"].unique()))
        return f"<Catalog: {len(self)} bounds — {instruments}>"

    def select(self, **criteria: Any) -> Catalog:
        """Narrow the catalogue. Each keyword is a column; a list means any of.

        >>> catalog().select(instrument_class="iact", mode="ann", channel="bb")
        """
        frame = self.frame
        for column, wanted in criteria.items():
            if column not in frame.columns:
                raise KeyError(
                    f"no column {column!r}; available: {sorted(frame.columns)}"
                )
            if isinstance(wanted, (list, tuple, set)):
                frame = frame[frame[column].isin(list(wanted))]
            else:
                frame = frame[frame[column] == wanted]
        return Catalog(frame)

    def involves(self, instrument: str) -> Catalog:
        """Bounds this instrument contributed to, joint analyses included.

        Distinct from ``select(instrument=...)``, which matches only bounds
        published under that instrument alone.
        """
        mask = self.frame["instruments"].apply(lambda names: instrument in names)
        return Catalog(self.frame[mask])

    def between(self, first: int, last: int) -> Catalog:
        """Bounds published in the given years, inclusive."""
        years = self.frame["year"]
        return Catalog(self.frame[(years >= first) & (years <= last)])

    def where(self, predicate: Callable[[pd.Series], bool]) -> Catalog:
        """Anything the other methods do not express."""
        return Catalog(self.frame[self.frame.apply(predicate, axis=1)])

    def curves(self) -> list[Table]:
        """Read the selected bounds' data. This is the only method that does I/O."""
        return [ascii.read(path, format="ecsv") for path in self.frame["path"]]

    def paths(self) -> list[Path]:
        return list(self.frame["path"])

    def values(self, column: str) -> list:
        """The distinct values a column takes here, for building a selection."""
        if column not in self.frame.columns:
            raise KeyError(f"no column {column!r}")
        return sorted(set(self.frame[column].dropna()))

    def summary(self, *columns: str) -> pd.DataFrame:
        """How the selection breaks down along one or more axes."""
        columns = columns or ("instrument", "mode", "statement")
        return (
            self.frame.groupby(list(columns), dropna=False)
            .size()
            .reset_index(name="bounds")
            .sort_values("bounds", ascending=False)
            .reset_index(drop=True)
        )


_CACHE: Catalog | None = None


def catalog(reload: bool = False) -> Catalog:
    """The database catalogue, read once and reused."""
    global _CACHE
    if _CACHE is None or reload:
        _CACHE = Catalog.load()
    return _CACHE
