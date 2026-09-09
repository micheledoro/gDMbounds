# Working on gDMbounds

## Branches

Three long-lived branches, by what the work is:

| branch | for |
|---|---|
| `repo_dev` | new capability — plotting, recasting, anything the package could not do before |
| `repo_fix` | the repository itself — CI, packaging, tests, tooling, documentation |
| `data_fix` | corrections to bounds already in the database |

Plus one short-lived branch per new dataset, named for what it adds
(`bounds/magic-2023-lines`), opened and closed on its own.

Commit to the long-lived branches freely; open a pull request when the work has
accumulated into something coherent. CI runs on every push to them, not only on
the pull request, so a branch cannot drift for weeks without anyone noticing.

Two things to hold to:

- **Rebase on `main` regularly.** A branch that lives for months diverges, and
  reconciling it costs more than the branching saved. This repository has already
  paid that bill once: a local clone two months stale met a remote whose history
  had been rewritten, and untangling it took longer than the work it contained.
- **Do not split a coherent change across branches.** Adding a plot may reveal a
  bad bound and want a new test; that is one change, and it belongs wherever its
  centre of gravity is. Three branches for one idea is worse than one branch for
  three.

`main` is protected: it takes pull requests only, and CI must pass.

## Before you push

```bash
conda activate gdmbounds        # or pip install -e ".[dev]"
pytest tests/ -q
ruff check gdmbounds tools tests
```

If you changed the classes or the data, regenerate the documents that describe
them — the suite fails if you forget:

```bash
python tools/vocabulary_reference.py
python tools/data_review.py
```

## Adding a bound

See `templates/README.md`. Provenance is mandatory: a DOI or an arXiv identifier,
plus the figure the curve was taken from. A bound whose instrument, target or
channel is missing from `gdmbounds/legends/` will not pass CI — add it to the
legend, **with its class**, in the same pull request.

## What the tests will not tell you

CI enforces what can be decided mechanically. It cannot tell you that a curve was
transcribed from the wrong figure, or that two files hold the same data because
one was copied from the other. `DATA_REVIEW.md` collects what is currently known
to need a human; it is generated, so it is never out of date.

Closing those questions means reading the paper, and that is done one paper at a
time — 385 bounds come from 57 papers, and one reading settles every curve taken
from that paper.

```bash
python tools/fetch_papers.py --list     # the papers, into a gitignored papers/
python tools/fetch_papers.py
```

`DATA_REVIEW.md` carries the queue, heaviest paper first. Record what you find in
`review_log.yaml`, keyed by the paper's arXiv identifier — reviewer, date, verdict
(`ok`, `corrected`, `open`) and notes — and regenerate. **Write in the log, read in
the document:** `DATA_REVIEW.md` is rewritten from scratch every time the tool
runs, so an outcome typed into it is lost.
