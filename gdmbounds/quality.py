"""Checks on the numbers in a bound, as opposed to the shape of its file.

`schema.check_file` answers "is this a well-formed bound file?". This module
answers "do these values describe a usable limit curve?" — which is a different
question with a different failure mode. A file can satisfy the schema perfectly
and still carry a curve that no interpolator can evaluate.

The two are kept apart because they have different standards of proof. A schema
violation is always a defect. A curve that doubles back on itself may be a
digitisation error, or it may be a closed contour faithfully transcribed from a
paper that reported a signal region rather than an upper limit; only reading the
paper settles it.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import ascii

from .schema import Issue, iter_bound_files

#: Below this the "curve" is too sparse to interpolate meaningfully.
MIN_POINTS = 3

#: Generous bounds on DM mass in GeV. Anything outside is a transcription slip,
#: not a physics result: gamma-ray searches do not probe sub-100-MeV or
#: super-Planckian dark matter.
MASS_RANGE_GEV = (0.1, 1e9)

#: No published cross-section limit is anywhere near the thermal relic value
#: from above; a curve above this is in the wrong units or off by orders.
MAX_SIGMAV = 1e-15

#: A decay lifetime limit shorter than this would be younger than anything the
#: field constrains.
MIN_TAU = 1e15


def _quantity_column(table) -> str | None:
    for name in ("sigmav", "tau", "sigmav_lo"):
        if name in table.colnames:
            return name
    return None


def check_curve(path: Path) -> list[Issue]:
    """Check the numbers in one bound. Returns every problem found."""
    issues: list[Issue] = []

    def report(kind: str, detail: str) -> None:
        issues.append(Issue(path=path, kind=kind, detail=detail))

    try:
        table = ascii.read(path, format="ecsv")
    except Exception as exc:
        report("unreadable", f"{type(exc).__name__}")
        return issues

    mass = np.asarray(table["mass"], dtype=float)
    unit = str(table["mass"].unit)
    mass_gev = mass * (1000.0 if unit == "TeV" else 1.0)

    if len(mass) < MIN_POINTS:
        report("too-short", f"only {len(mass)} points")
    if not np.all(np.isfinite(mass)):
        report("bad-values", "mass contains non-finite entries")
    if np.any(mass <= 0):
        report("bad-values", "mass contains non-positive entries")

    lo, hi = MASS_RANGE_GEV
    if np.all(np.isfinite(mass_gev)) and (mass_gev.min() < lo or mass_gev.max() > hi):
        report(
            "implausible-mass",
            f"mass spans {mass_gev.min():.3g}–{mass_gev.max():.3g} GeV, "
            f"outside {lo:g}–{hi:g}",
        )

    _check_monotonic(mass, report)

    column = _quantity_column(table)
    if column is not None:
        values = np.asarray(table[column], dtype=float)
        if not np.all(np.isfinite(values)):
            report("bad-values", f"{column} contains non-finite entries")
        if np.any(values <= 0):
            report("bad-values", f"{column} contains non-positive entries")
        elif np.all(np.isfinite(values)):
            if column.startswith("sigmav") and values.max() > MAX_SIGMAV:
                report(
                    "implausible-value",
                    f"{column} reaches {values.max():.3g}, above {MAX_SIGMAV:g} cm3/s",
                )
            if column == "tau" and values.min() < MIN_TAU:
                report(
                    "implausible-value",
                    f"tau falls to {values.min():.3g}, below {MIN_TAU:g} s",
                )

    return issues


def _check_monotonic(mass: np.ndarray, report) -> None:
    """A limit curve must be a single-valued, increasing function of mass.

    Where it is not, the shape of the failure says what went wrong: a curve that
    climbs, turns once and comes back to where it started is a closed contour,
    not a limit.
    """
    if len(mass) < 2 or not np.all(np.isfinite(mass)):
        return

    if len(np.unique(mass)) != len(mass):
        repeated = len(mass) - len(np.unique(mass))
        report("duplicate-mass", f"{repeated} repeated mass value(s)")

    steps = np.diff(mass)
    if np.all(steps > 0):
        return

    turning = int(np.argmax(mass))
    returning = len(mass) - 1 - turning
    closure = abs(mass[0] - mass[-1]) / mass[0]

    if returning >= 5 and closure < 0.6:
        report(
            "closed-contour",
            f"mass rises to {mass.max():.4g} then returns over {returning} points, "
            f"closing {closure:.0%} from the start — this is a region, not a limit",
        )
    else:
        backward = int(np.sum(steps <= 0))
        report(
            "unsorted-mass",
            f"mass is not strictly increasing ({backward} backward step(s))",
        )


def check_all_curves() -> list[Issue]:
    """Check the numbers in every bound in the database."""
    issues: list[Issue] = []
    for path in iter_bound_files():
        issues.extend(check_curve(path))
    return issues
