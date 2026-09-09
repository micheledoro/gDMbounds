"""The paper-by-paper review: its grouping, and the log that records it.

A review is done once per paper and settles every bound transcribed from it, so
the grouping has to be exact — a bound that falls outside every paper is a bound
nobody will ever be asked to check. And the log is hand-written, which is the
whole point of it and also its risk: a typo in an identifier would sit there
recording a review of nothing while the progress count says the work is done.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import paper_index  # noqa: E402
import review_log  # noqa: E402

from gdmbounds import schema  # noqa: E402


@pytest.fixture(scope="module")
def papers():
    return paper_index.collect()


def test_every_bound_belongs_to_exactly_one_paper(papers):
    grouped = [name for paper in papers.values() for name in paper.files]
    expected = [p.name for p in schema.iter_bound_files()]
    assert sorted(grouped) == sorted(expected)
    assert len(grouped) == len(set(grouped)), "a bound counted under two papers"


def test_no_bound_is_unidentified(papers):
    """Every bound cites a DOI or an arXiv id; provenance is mandatory."""
    assert "unidentified" not in papers


def test_paper_filenames_are_distinct(papers):
    """Two papers sharing a PDF filename would overwrite each other in `papers/`."""
    stems = [paper.stem for paper in papers.values()]
    assert len(stems) == len(set(stems))


def test_no_identifier_contains_another(papers):
    """`Paper.pdf` finds a file by looking for the identifier inside its name.

    That tolerates renaming a PDF by hand, and it only stays unambiguous while no
    identifier is a substring of another.
    """
    identifiers = sorted(paper.identifier for paper in papers.values())
    for one in identifiers:
        for other in identifiers:
            if one != other:
                assert one not in other, f"{one!r} is contained in {other!r}"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("1202.5494", "1202.5494"),
        (" arXiv:1202.5494 ", "1202.5494"),
        ("https://arxiv.org/abs/2111.15009", "2111.15009"),
        ("astro-ph/0611502", "astro-ph/0611502"),
        ("2111.15009v2", "2111.15009v2"),
        # Not an arXiv identifier, whatever field it was written in.
        ("https://pos.sissa.it/358/538/", ""),
        ("", ""),
        (None, ""),
    ],
)
def test_arxiv_identifiers_are_recognised(raw, expected):
    assert paper_index.normalise_arxiv(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("10.1088/0004-637X/750/2/123", "10.1088/0004-637X/750/2/123"),
        ("https://doi.org/10.48550/arXiv.2406.08698", "10.48550/arXiv.2406.08698"),
        ("  doi:10.1016/j.dark.2021.100912  ", "10.1016/j.dark.2021.100912"),
    ],
)
def test_dois_are_recognised(raw, expected):
    assert paper_index.normalise_doi(raw) == expected


def test_the_queue_is_ordered_by_how_much_it_settles(papers):
    counts = [len(p.files) for p in paper_index.by_weight(papers)]
    assert counts == sorted(counts, reverse=True)


# --------------------------------------------------------------------- the log

def test_the_committed_log_is_well_formed():
    entries, problems = review_log.load()
    assert problems == []


def test_the_committed_log_names_papers_that_exist(papers):
    entries, _ = review_log.load()
    assert review_log.check_against(entries, papers) == []


def write_log(tmp_path, body):
    path = tmp_path / "review_log.yaml"
    path.write_text(body)
    return path


def test_a_complete_entry_is_read(tmp_path):
    entries, problems = review_log.load(write_log(tmp_path, """
reviewed:
  1202.5494:
    reviewer: MD
    date: 2026-09-09
    verdict: corrected
    notes: The DOI disagreed between files; fixed against the published version.
    decisions:
      hess_2012_fornaxcluster_ann_bb_nfwrs08.ecsv: Matches figure 4, left panel.
"""))
    assert problems == []
    entry = entries["1202.5494"]
    assert entry.reviewer == "MD"
    assert entry.verdict == "corrected"
    assert entry.decisions["hess_2012_fornaxcluster_ann_bb_nfwrs08.ecsv"].startswith(
        "Matches figure 4"
    )


def test_a_missing_log_is_not_an_error(tmp_path):
    assert review_log.load(tmp_path / "absent.yaml") == ({}, [])


@pytest.mark.parametrize(
    "body, complaint",
    [
        ("reviewed:\n  1202.5494:\n    date: 2026-09-09\n    verdict: ok\n", "reviewer"),
        ("reviewed:\n  1202.5494:\n    reviewer: MD\n    date: sept\n    verdict: ok\n",
         "YYYY-MM-DD"),
        ("reviewed:\n  1202.5494:\n    reviewer: MD\n    date: 2026-09-09\n"
         "    verdict: probably fine\n", "verdict"),
        # An unresolved problem with no note leaves no record of what it was.
        ("reviewed:\n  1202.5494:\n    reviewer: MD\n    date: 2026-09-09\n"
         "    verdict: open\n", "no notes"),
    ],
)
def test_a_malformed_entry_is_reported(tmp_path, body, complaint):
    _, problems = review_log.load(write_log(tmp_path, body))
    assert any(complaint in problem for problem in problems), problems


def test_an_unknown_identifier_is_reported(tmp_path, papers):
    entries, _ = review_log.load(write_log(tmp_path, """
reviewed:
  0000.00000:
    reviewer: MD
    date: 2026-09-09
    verdict: ok
"""))
    assert any("no paper" in p for p in review_log.check_against(entries, papers))


def test_a_decision_naming_another_paper_bound_is_reported(tmp_path, papers):
    entries, _ = review_log.load(write_log(tmp_path, """
reviewed:
  1202.5494:
    reviewer: MD
    date: 2026-09-09
    verdict: ok
    decisions:
      magic_2022_segue1_ann_bb.ecsv: not a bound of this paper
"""))
    assert any("not one of" in p for p in review_log.check_against(entries, papers))


def test_a_decision_is_shown_beside_the_finding_it_settles():
    """The log is written once; the generated document is where it is read."""
    import data_review

    body = data_review.bullet_files(
        ["a.ecsv", "b.ecsv"], decisions={"b.ecsv": "kept: matches figure 7."}
    )
    assert "- `a.ecsv`" in body
    assert "  - reviewed: kept: matches figure 7." in body
