# The papers behind the bounds

Every bound in this database was transcribed from a published figure. This
directory holds those publications so that the source can sit open beside the
data while it is being checked.

**Nothing here is committed except this file.** They are other people's
publications, and the repository is not a place to redistribute them. A fresh
clone therefore finds this directory empty, which is what the fetch tool is for:

```bash
python tools/fetch_papers.py --list     # what is held, what is missing
python tools/fetch_papers.py            # fetch the arXiv preprints
```

Only arXiv is fetched — its preprints are freely downloadable, a publisher's PDF
usually is not. Two papers in the database have no arXiv identifier; the tool
prints them, with a DOI link and the filename to save them under.

## Naming

```
<year>_<instrument>_<identifier>.pdf     2012_hess_1202.5494.pdf
```

The year first so the directory sorts the way a review works through it, and the
identifier — the arXiv id, or the DOI with its slashes turned into hyphens —
because that is what ties the file to the `arxiv` and `doi` fields in the ECSV
headers. Adding to the name is fine, an author say; the tools find a paper by
looking for its identifier anywhere in the filename.

## What this is for

The review is done one paper at a time, not one file at a time: 385 bounds come
from 57 papers, and reading a paper settles every curve taken from it at once.
`DATA_REVIEW.md` carries the queue, ordered so that the heaviest paper — 34
bounds — comes first. Outcomes are written in `review_log.yaml`.
