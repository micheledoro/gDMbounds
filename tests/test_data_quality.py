"""The numbers in the database, as opposed to the shape of its files.

Every bound must describe a usable limit curve. Twenty-five do not yet, and are
quarantined below with the reason. The quarantine is deliberately rigid: a new
file that develops a problem fails the suite, and a quarantined file that gets
fixed also fails until it is removed from the list. It can only shrink.
"""

import collections

import pytest

from gdmbounds import quality
from gdmbounds.schema import iter_bound_files

#: Curves that climb, turn once and return to their starting point. These are
#: closed contours — a signal region rather than an upper limit — and the source
#: papers need checking before deciding whether the file is mislabelled or the
#: transcription is wrong.
#:
#: They carry ``statement: "limit"``, assigned mechanically from the filename. If
#: the paper confirms a signal region, that key becomes ``"detection"`` and the
#: entry leaves the quarantine.
#:
#: One case is already closed. ``lat_2023_sagittarius_ann_bb`` was flagged here by
#: its geometry, and independently deleted upstream in October as "the wrong
#: data"; it is gone from the database.
NEEDS_ADJUDICATION = {
    "magic_2018_perseuscluster_dec_WW.ecsv": "closed contour; check the paper",
}

#: Curves with points out of order or repeated, consistent with noise in the
#: digitisation of a published figure. Sorting by mass reorders rows without
#: changing any value, but it still edits a published curve, so it waits for a
#: decision on each file.
#:
#: One is already settled: ``magic_2022_segue1_ann_bb`` had three rows permuted,
#: and upstream had independently sorted the same file. Reordering it changed no
#: value and it has left the quarantine.
NEEDS_RESORTING = {
    "cta_2021_gc_ann_WW_sens_mstonly.ecsv": "unsorted-mass",
    "dampe_2022_gc_ann_gammagamma_r16einasto.ecsv": "unsorted-mass",
    "hawc_2018_multidsph_dec_WW.ecsv": "unsorted-mass",
    "hawc_2018_multidsph_dec_bb.ecsv": "unsorted-mass",
    "hess_2011_carina_ann_WW_nfw_sommerfeld.ecsv": "duplicate-mass, unsorted-mass",
    "hess_2012_fornaxcluster_ann_WW_nfwrb02.ecsv": "unsorted-mass",
    "hess_2012_fornaxcluster_ann_WW_nfwrb02_ib.ecsv": "unsorted-mass",
    "hess_2018_gc_ann_gammagamma_einasto.ecsv": "duplicate-mass, unsorted-mass",
    "hess_2018_gc_ann_gammagamma_nfw.ecsv": "duplicate-mass, unsorted-mass",
    "hess_2018_multidsph_ann_triplett.ecsv": "unsorted-mass",
    "magic_2014_segue1_ann_gammagamma.ecsv": "unsorted-mass",
    "magic_2014_segue1_ann_mumu.ecsv": "unsorted-mass",
    "magic_2014_segue1_dec_mumu.ecsv": "unsorted-mass",
    "magic_2018_perseuscluster_dec_mumu.ecsv": "unsorted-mass",
    "magic_2022_comaberenices_ann_WW.ecsv": "unsorted-mass",
    "magic_2022_comaberenices_ann_hh.ecsv": "unsorted-mass",
    "magic_2022_multidsph_ann_WW.ecsv": "unsorted-mass",
    "magic_2022_segue1_ann_ZZ.ecsv": "unsorted-mass",
    "magic_2022_segue1_ann_mumu.ecsv": "unsorted-mass",
    "magic_2022_segue1_ann_tautau.ecsv": "unsorted-mass",
    "multi-inst-magic-lat_2016_multidsph_ann_mumu.ecsv": "unsorted-mass",
    "veritas_2012_comacluster_ann_WW.ecsv": "unsorted-mass",
}

QUARANTINE = {**NEEDS_ADJUDICATION, **NEEDS_RESORTING}


def _offending_files():
    return {i.path.name for i in quality.check_all_curves()}


def test_no_unquarantined_file_has_a_bad_curve():
    """Any bound not on the list must have a clean curve."""
    offenders = _offending_files() - set(QUARANTINE)
    assert not offenders, (
        "these bounds have curve problems and are not quarantined:\n  "
        + "\n  ".join(sorted(offenders))
    )


def test_quarantine_does_not_outlive_its_reason():
    """A quarantined file that now passes must be taken off the list."""
    stale = set(QUARANTINE) - _offending_files()
    assert not stale, (
        "these bounds are clean now; remove them from the quarantine:\n  "
        + "\n  ".join(sorted(stale))
    )


def test_quarantine_names_real_files():
    known = {p.name for p in iter_bound_files()}
    missing = set(QUARANTINE) - known
    assert not missing, f"quarantine names files that do not exist: {sorted(missing)}"


@pytest.mark.parametrize(
    "path", [p for p in iter_bound_files()], ids=lambda p: p.name
)
def test_curve_is_usable(path):
    """Each bound individually, so a failure names the file."""
    if path.name in QUARANTINE:
        pytest.skip(QUARANTINE[path.name])
    issues = quality.check_curve(path)
    assert not issues, "; ".join(i.detail for i in issues)


def test_quarantine_is_shrinking_not_growing():
    """A ratchet: the count is recorded so an increase has to be deliberate."""
    assert len(QUARANTINE) <= 23, (
        f"the quarantine has grown to {len(QUARANTINE)}; bounds are meant to be "
        "fixed and removed from it, not added to it"
    )


def test_summary_of_outstanding_problems(capsys):
    """Not an assertion — prints the current state so CI logs carry it."""
    kinds = collections.Counter(i.kind for i in quality.check_all_curves())
    with capsys.disabled():
        print("\n  outstanding curve problems:", dict(kinds))

