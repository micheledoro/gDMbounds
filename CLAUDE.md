# gDMbounds

A database and toolkit for indirect Dark Matter searches: published experimental
limits on DM annihilation and decay, the means to select and plot them, and
(planned) methods to recast them.

Successor to `moritzhuetten/dmbounds`; the canonical repo is `micheledoro/gDMbounds`
and the package is `gdmbounds` — repo, package and PyPI name are deliberately aligned.

## Where we left off (9 September 2026)

The paper-by-paper data review has started. **One paper of 57 is read**, the
heaviest — MAGIC 2022, arXiv:2111.15009, 41 of the 391 bounds — and it produced
four real errors, all fixed. See *The paper-by-paper review* below and
`review_log.yaml` for what it found.

All of it is in `main` — pull request #66, merged — and `repo_dev`, `repo_fix`
and `data_fix` are level with it again. That work crossed two branches once:
`repo_fix` was merged into `data_fix` before the four MAGIC median files were
renamed, because the rename and the log entry naming them are one change and
splitting them would have left whichever branch merged first with a failing
suite. Worth repeating when it happens again: **a review that touches both the
data and the tooling belongs on one branch**, and the shortest way there is to
merge the other into it.

Keep the habit that made #66 easy — take a paper to `main` before starting the
next one, so the review does not accumulate on a long-lived branch.

Next in the queue, and both worth doing early: H.E.S.S. Fornax **1202.5494** (25
bounds, and its erratum question is open — four of its qualifiers still say "to
confirm against the paper") and VERITAS **1703.04937** (22).

## Picking up on another machine

```bash
git clone git@github.com:micheledoro/gDMbounds.git
cd gDMbounds
conda env create -f environment.yml     # or: pip install -e ".[dev]"
conda activate gdmbounds
pytest tests/ -q                        # expect 863 passed, 22 skipped
python tools/fetch_papers.py            # the papers, into a gitignored papers/
```

`environment.yml` installs the dependencies through **pip inside a conda
environment**, deliberately: pip is what CI uses, so the local resolution matches
the one the tests run against. Letting conda solve them produced astropy 6.1
beside numpy 2.5, a pair that cannot import — astropy 6.1 calls `np.in1d`, which
numpy 2 removed.

The plotting layer and figure styles are merged; `repo_dev` and `main` are level.

## People

The software is authored by **Michele Doro** (professor, Univ. Padova) and
**Giacomo D'Amico** (MSCA Fellow, Univ. Padova), who together published the
casting/recasting methods that macro-function 3 will implement. Earlier
contributors are credited in `contributions.md` but are not authors of the
current software.

**Author lists inside ECSV headers are citations, not project authorship.** They
name the authors of the paper a bound was transcribed from, and must never be
edited to reflect who works on gDMbounds. The same goes for filenames that cite a
paper, such as `modelpredictions/wimp_huetten2017_*`.

## Where the project is going

1. **Archive.** Curated collection of published limits, including historical ones
   — the value is partly in preserving results that would otherwise stay locked
   in the figures of old papers.
2. **Plotting.** *Built.* Select bounds by criterion and draw them, in four styles.
   **Still open:** the delivery mechanism — interactive web, downloadable scripts,
   pre-rendered images. Deferred until the API settles.
3. **Recasting.** Apply the Doro–D'Amico methods to transform limits between
   assumptions. **Nothing exists yet.** This is the next substantial piece.
4. **Professional structure.** *Built.* CI, packaging, generated documentation.

## Branching

| branch | for |
|---|---|
| `repo_dev` | new capability — plotting, recasting |
| `repo_fix` | the repository itself — CI, packaging, tests, tooling, docs |
| `data_fix` | corrections to bounds already in the database |

Plus one short-lived branch per new dataset (`bounds/magic-2023-lines`), closed on
its own. Commit freely; open a pull request when the work is coherent. CI runs on
every push to all three, not only on pull requests — see `CONTRIBUTING.md`.

`main` is protected: pull requests only, CI must pass.

Two things that bite with long-lived branches: **rebase on `main` regularly** (a
stale local clone once met a rewritten remote and untangling it took longer than
the work it held), and **do not split a coherent change across branches** — put it
where its centre of gravity is.

## Layout

```
gdmbounds/
  schema.py         what a bound file is, and its validation — everything builds on this
  quality.py        checks on the numbers, kept separate from the schema
  catalog.py        every header in one table, with composable selection over it
  plotting.py       draws a selection; refuses to mix modes, marks forecasts
  styles.py         palettes and rcParams, applied per call and then withdrawn
  bounds/<inst>/    391 ECSV files, one per published limit curve
  legends/          controlled vocabularies: instruments, targets, channels, qualifiers
  modelpredictions/ theory curves (thermal relic, GAMBIT scan)
tests/              run with pytest; 863 passing, 22 skipped
tools/              migration scripts, the two document generators, the figure gallery
                    paper_index.py groups the bounds by paper; fetch_papers.py fetches them
review_log.yaml     hand-kept: which papers have been read against their data
papers/             the publications themselves, gitignored — README.md is not
templates/          blank ECSV headers for adding a new bound — with a README
unconverted/        material the schema cannot hold, including ALP contours
legacy/             pre-2026 code, not shipped, reference only
sandbox/<name>/     per-person scratch; nothing in the package imports from it
figures/            generated by tools/example_figures.py, gitignored
```

## Data model

391 bounds under `gdmbounds/bounds/<instrument>/`: `collider`, `ctao`, `dampe`,
`directsearches`, `hawc`, `hess`, `lat`, `lhaaso`, `magic`, `multi-inst`, `mwa`,
`nustar`, `veritas`.

The archive is **no longer purely gamma-ray**: MWA is radio, NuSTAR is X-ray, and
NuSTAR constrains dark matter at **keV** masses, so `MASS_UNITS` admits keV and MeV
alongside GeV and TeV.

**Filename convention:**

```
<instrument>_<year>_<source>_<mode>_<channel>[_<qualifiers>].ecsv
```

`mode` is `ann` or `dec`. The channel is the **fifth underscore-separated token**,
not the last: qualifiers such as `_sens`, `_nfw`, `_noJerror`, `_substructure-high`
follow it and may contain hyphens. Tokens are not all lowercase — `LMC` and `WW`
are correct as written.

**Qualifiers are a controlled vocabulary**, in `legends/legend_qualifiers.ecsv`:
62 of them, and `pytest` rejects a filename carrying one that is not listed, or a
listed one no file uses. They were free-form until 2026, and the first pass
through them found `inital` sitting beside three files spelled `initial`.

They carry **no class**, deliberately. Nothing selects on a qualifier the way a
selection picks out every IACT or every dSph, and a taxonomy nobody queries only
grows and argues with itself at each new paper. The one mapping the legend does
carry is to a halo profile — `nfwrb02` to `nfw`, `zhaocored` to `cored`, and
`nfwburkertsr10a10` to neither, naming two — because `tests/test_classification.py`
uses it to keep a file called `_nfw` from declaring something else. That replaced
matching the first four letters of the stem, which caught `iso` inside any word.

A qualifier's job is to **distinguish** — `nfwrb02` from `nfwdw01`, the stack with
Segue 1 from the stack without. What is merely *true* of a curve belongs in the
header: the MAGIC 2022 bounds all assume NFW and none is called `_nfw`, because
naming it would separate nothing. `_sens` is the one deliberate exception, kept
because measured-against-projected must be visible at a glance and is load-bearing
in both the tests and the plotting.

**Composite identifiers:** a joint analysis is `multi-inst-<a>-<b>`; a stacked
sample is `multi<class>[-<n>][-<member>...]`. `schema.base_instrument` and
`schema.base_source` collapse these to the grouping token.

**Header metadata** (`REQUIRED_META`): `reference`, `doi`, `arxiv`, `instrument`,
`origin`, `statement`, `year`, `source`, `mode`, `channel`, `confidence`,
`dmfraction`, `obs_time`, `figure`, `comment`, `status`. Optional: `authors`,
`journalref`, `profile`, `bibcode`, `url`.

`mode`, `origin` and `statement` were all added in the 2026 migration. None existed
before: annihilation-vs-decay lived only in the filename, provenance only in which
directory a file sat in, and measured-vs-projected only in a `_sens` suffix.

**Table columns:** `mass` always; `sigmav` (cm3s-1) for annihilation, `tau` (s) for
decay. Optional columns are documented in `schema.OPTIONAL_COLUMNS` — containment
bands, and `sigmav_expected`, the limit expected under the null hypothesis, which
must never be confused with the observed one.

## Classification axes

All seven are built and populated. `VOCABULARY.md` lists every class and its
members; `python -m gdmbounds` prints the same.

| axis | where | spread |
|---|---|---|
| annihilation vs decay | `mode` | 344 / 47 |
| collaboration vs author | `origin` | 381 / 10 |
| measured vs projected | `statement` | 339 limit / 52 sensitivity |
| halo profile | `profile`, optional | 132 stated / 259 not |
| detection technique | `class` in `legend_instruments` | iact, satellite, xray, sfd, radio, collider, direct, combined |
| target type | `class` in `legend_targets` | dsph, cluster, globular, galaxy, gc, diffuse, subhalo, unid |
| line vs continuum | `spectrum` in `legend_channels` | continuum, line, model, benchmark |

Two things to hold on to. All 45 CTAO bounds are `sensitivity`, which is right —
CTAO is not operating; treat a future CTAO bound claiming `limit` as suspect until
checked. And **a missing `profile` means the filename never said, not that no
profile was assumed** — every J-factor rests on one. Filtering on it drops 259
bounds, and a selection doing so should say so. The gap is being closed paper by
paper as each is read: `tests/test_classification.py` requires only that a
filename naming a profile agree with its header, not that a stated profile be
named in the filename.

## State

All 391 bounds satisfy the schema. `pytest tests/ -q` is green — 863 passing, 22
skipped. CI runs that, `ruff`, and a wheel build asserting the shipped file set
matches the source tree exactly.

The 22 skips are quarantined in `tests/test_data_quality.py`: bounds whose *numbers*
are unusable though the file is well-formed. Twenty-one have points out of order or
repeated. One, `magic_2018_perseuscluster_dec_WW`, is a **closed contour** — it
climbs in mass, turns, and returns near its start, which is a region and not an
upper limit. Its paper needs checking.

`KNOWN_IDENTICAL` is empty: the one pair of files holding the same curve was
resolved during the MAGIC review.

Every quarantine here is a **ratchet**: a newly broken file fails the suite, and a
fixed one fails until it is delisted. The same pattern guards against a bound
duplicating another's curve.

Two documents are **generated**, never hand-edited:

- `VOCABULARY.md` — every axis and its members, from `tools/vocabulary_reference.py`
- `DATA_REVIEW.md` — everything passing the schema that still needs a human to read
  a paper, from `tools/data_review.py`

`DATA_REVIEW.md` is the one exception to *derived from the data alone*: it also
merges `review_log.yaml`, which is hand-kept. That is deliberate — a review
outcome exists only because someone read a paper, so it cannot be regenerated —
and the split holds the line: **the log is where you write, the document is where
you read.** Anything typed into the document is lost on the next run.

`tests/test_generated_docs.py` fails if either is stale. Both tools are
timestamp-free on purpose: regenerating must be a no-op when nothing changed, or
that test could not exist.

Two rules the plotting layer keeps, which a change should not quietly break: line
style means measured-against-projected and nothing else, so groups are separated by
colour and then by marker; and no two legend entries may share an appearance, which
is why the default colours by legend entry rather than by instrument.
`tests/test_styles.py` enforces both.

`Catalog.select` matches the publishing instrument; `Catalog.involves` matches
participation, so a joint MAGIC+LAT analysis is found by the second and not the
first — 110 bounds involve MAGIC, 84 are MAGIC's own.

## The paper-by-paper review

Under way, and the unit is **the paper, not the file**: 391 bounds come from **57
papers**, and reading one settles every curve taken from it. The distribution is
steep — the heaviest paper accounts for 34 bounds, the heaviest five for 113 — so
`DATA_REVIEW.md` carries the queue in that order.

- `papers/` holds the publications, gitignored: they are other people's work and
  are not redistributed from here. `python tools/fetch_papers.py` refills it on a
  new clone, arXiv only — two papers have no arXiv id and are placed by hand.
  Files are named `<year>_<instrument>_<identifier>.pdf`, and the tools find one
  by looking for the identifier anywhere in the name, so renaming is safe.
- **Papers are keyed by arXiv id**, falling back to the DOI. arXiv first because
  it is what can be fetched, and because the DOIs have already been seen to
  disagree between files citing one work.
- Record the outcome in `review_log.yaml`, keyed by that identifier: reviewer,
  date, verdict (`ok`, `corrected`, `open`), notes, and optionally a line per file
  the reading settled — those appear beside the finding they answer.
  `tests/test_paper_review.py` fails on a malformed entry, on an identifier no
  paper carries, and on a decision naming a file that paper did not produce.
- A verdict of `open` **must** carry notes: the log is then the only record of
  what is still wrong.

### What the first reading found, and how

MAGIC 2022 (arXiv:2111.15009), verdict `corrected`. The headers were the easy
part; **what found the errors was a physical consistency test between curves**,
and that is the method to repeat:

> every curve of a single target must lie **above** the combined limit, because
> the combination contains it.

Six of the seven channels did. Two did not, and both were wrong. Afterwards all
seven sit between 1.48 and 1.60 above the combination at the median — a band
tight enough that it corroborates the curves that were never in doubt. Where a
paper has no combined analysis, the same idea applies across channels: tau tau is
the strongest, tt the weakest, and a violation is a transcription error.

Fixed: the combined mumu file held the Coma Berenices curve; the Segue 1 WW curve
was stronger than the combination everywhere; the exposures were wrong on all 34
files; four median curves were marked `limit` with "Median" in `confidence`. Then
`tt` was digitised for all five subjects and `gammagamma` for the combination, and
`profile: nfw` recorded from Sec. 8.

**Two traps, both of which cost a wrong diagnosis before being noticed:**

- `numpy.interp` on an **unsorted** mass column returns nonsense and does not
  complain. Twenty-one files are still in the resorting quarantine. Sort first.
- Units differ **within one paper**: `magic_2014_segue1_ann_bb` is in TeV where
  its twelve siblings are in GeV. Convert before comparing.

Still open on this paper, and not errors: Ursa Major II holds three of the nine
channels where the others hold eight — mumu, WW, ZZ, hh and bb are in Fig. 4 and
were never transcribed. The four per-target `gammagamma` curves were deliberately
skipped, MD judging a noise-dominated line search not worth the transcription.

The other finding, unresolved: the H.E.S.S. Fornax bounds cite two DOIs, and the
second is the paper's **2014 erratum** — legitimate, and the six files taking
their curve from it say `figure: "Fig. 5 erratum"`. What it opens is which of the
other Fornax curves come from figures the erratum superseded; arXiv v2 says
figures 5 and 7 were corrected.

## Open: a "most constraining" selector

Discussed, **not implemented**, and worth resuming rather than restarting.

Michele proposed picking the bound with the lowest absolute `sigmav`, and after
seeing the objections still prefers that over a dominance test. Left for him to
revisit. What the data showed, so it need not be rediscovered:

- **A limit is a curve, not a number.** Among 31 dSph bb limits, four are the
  strongest somewhere: LHAASO 2024 over 48% of the mass range, multi-inst 2026 over
  32%, MWA 2019 over 19%, LAT 2020 over 1%. A single scalar hides that the answer
  changes with mass, and compares minima that fall in different physical regimes —
  Fermi-LAT's near 10 GeV, an IACT's near 1 TeV.
- **The direction inverts for decay.** Strongest means lowest `sigmav` but *highest*
  `tau`. A minimum-seeking implementation answers backwards on all 47 decay bounds.
- **The question is well-posed only with the target fixed.** Otherwise it compares
  J-factors rather than measurements. With instrument, channel and target fixed, 5
  of 8 real cases have a curve that beats all others everywhere; 3 do not, so the
  answer must be allowed to be "none dominates".
- **The trap.** Where a winner exists it is often the most *optimistic* variant:
  `magic_2020_triangulum2_ann_bb_noJerror` (no J-factor uncertainty),
  `hess_2012_fornaxcluster_ann_bb_nfwrb02_substructure-high_theta1deg`. They are
  stronger because they assume more, not because they measure better, and they are
  not the numbers one would quote. Any such selector should surface the qualifiers
  that distinguish the winner rather than hide them.

## What still needs a human

In `DATA_REVIEW.md`, and none of it is a CI failure:

- `magic_2014_segue1_ann_bb` and `..._dec_bb` carry mass in **TeV** where the
  paper's twelve other files use GeV. Legal, and a trap: a comparison that reads
  the column without its unit is wrong by a thousand. Worth settling when
  arXiv:1312.1535 is reviewed.
- Five H.E.S.S. 2014 bounds record no `figure`, so nothing checks the transcription.
- Six qualifiers are in the legend with their meaning marked **"to confirm against
  the paper"**: `expo`, `v1`, the H.E.S.S. Fornax suffixes (`nfwrb02`, `nfwdw01`,
  `nfwrs08`, `nfwsr10a6`) and the two MWA backgrounds (`FermiLAT`, `cosmicrays`).
  Each falls out of the review of its own paper.
- `lo` and `up` are H.E.S.S. spellings of `min` and `max`, two files, and could be
  normalised. `med` and `median` must **not** be: HAWC's `med` is the middle of a
  range of J-factor assumptions, MAGIC's `median` is the expected limit under the
  null hypothesis. Different things, one word apart.
- The 2026 joint-analysis files describe `sv_lo_95` as a 3σ bound and `sv_hi_95` as
  2σ. The numeric suffixes were used; the prose contradicts itself. **Raise with
  whoever produced them.**

## Conventions

- Repo language is **English** — code, comments, commit messages, docs.
- Bounds are transcribed from published figures. Provenance is mandatory: `doi` or
  `arxiv`, plus the `figure` the curve came from.
- Never hand-edit a legend or bound without running `pytest`: one unquoted
  multi-word value broke every import of the package for eleven months.
- Regenerate `VOCABULARY.md` and `DATA_REVIEW.md` after changing classes or data.
- **Reinstalling after a data change needs `pip install --no-cache-dir .`**, and
  delete `build/` first. Most of this package is data, but pip caches the built
  wheel by version and setuptools keeps renamed files in `build/lib`; both will
  serve a stale database while `pytest` on the source tree says all is well. CI is
  immune — it builds from a fresh checkout.
