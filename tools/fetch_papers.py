"""Download the papers the bounds were transcribed from, into `papers/`.

    python tools/fetch_papers.py --list     # what is held and what is missing
    python tools/fetch_papers.py            # fetch the missing arXiv preprints
    python tools/fetch_papers.py --limit 5  # a few at a time

The directory is gitignored: these are other people's publications, and the
repository is not a place to redistribute them. That also means a fresh clone
has an empty `papers/`, which is what this tool is for — the review needs the
paper open beside the data, on whichever machine the work is happening.

Only arXiv is fetched. Its preprints are freely downloadable; a publisher's PDF
usually is not, and those papers are listed for someone to place by hand. The
requests are spaced, because arXiv asks for that and one review is not worth
being blocked over.
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import paper_index

PAPERS = paper_index.PAPERS_DIR

#: arXiv asks automated clients to identify themselves and to leave a few
#: seconds between requests.
USER_AGENT = "gdmbounds-fetch-papers/1.0 (+https://github.com/micheledoro/gDMbounds)"
DELAY_SECONDS = 3.0
TIMEOUT_SECONDS = 60


def download(arxiv_id: str, destination: Path) -> str:
    """Fetch one preprint. Returns "" on success, or why it failed.

    Written to a temporary neighbour and renamed, so an interrupted download
    never leaves a half a PDF looking like a paper that has been fetched.
    """
    url = f"https://arxiv.org/pdf/{arxiv_id}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read()
    except urllib.error.HTTPError as error:
        return f"HTTP {error.code}"
    except (urllib.error.URLError, TimeoutError) as error:
        return str(getattr(error, "reason", error))

    # arXiv answers a rate-limited or unavailable request with an HTML page and a
    # 200, so the status code alone does not say a PDF arrived.
    if not payload.startswith(b"%PDF"):
        return f"the reply was not a PDF ({len(payload)} bytes)"

    partial = destination.with_suffix(".part")
    partial.write_bytes(payload)
    partial.replace(destination)
    return ""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--list", action="store_true",
                        help="report what is held and what is missing; fetch nothing")
    parser.add_argument("--limit", type=int, default=0,
                        help="stop after this many downloads")
    parser.add_argument("--force", action="store_true",
                        help="download again even if the paper is already held")
    parser.add_argument("--dry-run", action="store_true",
                        help="say what would be fetched, without fetching it")
    args = parser.parse_args(argv)

    collected = paper_index.collect()
    ordered = paper_index.by_weight(collected)

    held = [p for p in ordered if p.pdf(PAPERS) is not None]
    fetchable = [p for p in ordered if p.arxiv and (args.force or p.pdf(PAPERS) is None)]
    by_hand = [p for p in ordered if not p.arxiv and p.pdf(PAPERS) is None]

    print(f"{len(collected)} papers behind the database; {len(held)} held in "
          f"{PAPERS.relative_to(paper_index.ROOT)}/")

    if args.list:
        for paper in ordered:
            pdf = paper.pdf(PAPERS)
            mark = "held" if pdf else ("arxiv" if paper.arxiv else "by hand")
            print(f"  [{mark:>7}] {len(paper.files):3d} bounds  {paper.identifier:32s} "
                  f"{paper.reference[:60]}")
        return 0

    if by_hand:
        print(f"\n{len(by_hand)} paper(s) have no arXiv identifier and must be placed "
              f"by hand, named so that the identifier appears in the filename:")
        for paper in by_hand:
            print(f"  {paper.stem}.pdf   https://doi.org/{paper.doi}")

    if not fetchable:
        print("\nNothing to fetch.")
        return 0

    wanted = fetchable[: args.limit] if args.limit else fetchable
    print(f"\n{len(wanted)} to fetch from arXiv:")

    PAPERS.mkdir(exist_ok=True)
    failures = []
    for index, paper in enumerate(wanted):
        destination = PAPERS / f"{paper.stem}.pdf"
        if args.dry_run:
            print(f"  would fetch {paper.arxiv} -> {destination.name}")
            continue
        if index:
            time.sleep(DELAY_SECONDS)
        problem = download(paper.arxiv, destination)
        if problem:
            failures.append((paper, problem))
            print(f"  FAILED {paper.arxiv}: {problem}")
        else:
            size = destination.stat().st_size / 1024
            print(f"  {destination.name}  ({size:.0f} kB)")

    if failures:
        print(f"\n{len(failures)} failed; re-run to retry just those.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
