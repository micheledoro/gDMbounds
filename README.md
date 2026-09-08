# gDMbounds

A curated database of published gamma-ray bounds on dark matter annihilation and
decay, with the tools to select and plot them. Limits from direct-detection and
collider searches are included so that the three can be compared on one figure.

The value of the archive is partly historical: it preserves limit curves that
would otherwise stay locked inside the figures of old papers.

**Status: rebuilding.** Schema, validation and catalogue search are in place and
the whole database satisfies the schema. Plotting and recasting are still to come.
The plotting API described in older versions of this README no longer exists —
see [Roadmap](#roadmap).

## What is in it

367 bounds, one ECSV file per published limit curve.

| Instrument | Bounds |  | Instrument | Bounds |
|---|---:|---|---|---:|
| H.E.S.S. | 121 | | LHAASO | 9 |
| MAGIC | 74 | | DAMPE | 4 |
| Fermi-LAT | 47 | | MWA | 4 |
| CTA | 45 | | Collider searches | 3 |
| VERITAS | 25 | | Direct detection | 3 |
| HAWC | 19 | | NuSTAR | 1 |
| Multi-instrument | 12 | | | |

320 constrain annihilation, 47 decay. Most are gamma-ray, but the archive also
covers radio (MWA) and X-ray (NuSTAR) searches, the latter reaching down to
keV-scale dark matter — twelve orders of magnitude below the gamma-ray range. Twenty annihilation channels are
represented — `bb`, `WW`, `tautau`, `mumu`, `gammagamma`, `ee`, `ZZ`, `tt` and
others — across dwarf spheroidals, galaxy clusters, the Galactic Centre, the
LMC, diffuse emission and dark subhalos.

## Installation

```bash
pip install git+https://github.com/micheledoro/gDMbounds.git
```

Or from a clone, for development:

```bash
git clone https://github.com/micheledoro/gDMbounds.git
cd gDMbounds
pip install -e ".[dev]"
```

With conda, `environment.yml` builds the same thing:

```bash
conda env create -f environment.yml
conda activate gdmbounds
pytest tests/ -q
```

It deliberately installs the Python dependencies through pip rather than conda,
so that what you develop against is what CI resolves. Letting conda solve them
can yield astropy 6.1 beside numpy 2.5 — a pair that fails on import, since
astropy 6.1 calls `np.in1d`, which numpy 2 removed.

> Most of this package is data. When you change a bound file and reinstall, pass
> `--no-cache-dir` and delete `build/` first — otherwise pip serves a cached wheel
> and setuptools reuses stale files, and you silently get the old database.

## Usage

```python
import gdmbounds

cat = gdmbounds.catalog()                 # <Catalog: 367 bounds — ...>

cat.select(instrument="magic", target_class="dsph", channel="bb", mode="ann")
cat.select(instrument_class="iact")       # every Cherenkov telescope
cat.select(statement="limit")             # exclude projected sensitivities
cat.select(instrument=["magic", "hess"])  # a list means any of

cat.involves("magic")                     # joint analyses included, unlike select
cat.between(2020, 2025)                   # by year of publication
```

Criteria compose, and selecting reads no curve — `select` returns another
catalogue. Only `curves()` touches the files:

```python
chosen = cat.select(instrument_class="iact", mode="ann", channel="bb")
print(chosen.summary("instrument"))       # how the selection breaks down
tables = chosen.curves()                  # now the data is read
```

The validation layer is available directly too:

```python
assert gdmbounds.check_database() == []   # empty means the database is sound
vocabulary = gdmbounds.load_vocabulary()
print(vocabulary.instruments["magic"])    # MAGIC
```

Reading one bound is plain astropy:

```python
from astropy.io import ascii

table = ascii.read("gdmbounds/bounds/magic/magic_2022_segue1_ann_bb.ecsv", format="ecsv")
print(table.meta["reference"], table.meta["doi"])
mass, sigmav = table["mass"], table["sigmav"]
```

## Data model

One bound is one ECSV file. The header carries the metadata and is the source of
truth; the filename is a human-readable convention that must agree with it.

```
<instrument>_<year>_<source>_<mode>_<channel>[_<qualifiers>].ecsv
```

`mode` is `ann` or `dec`. The channel is the fifth underscore-separated token,
not the last — qualifiers such as `_sens`, `_nfw`, `_einasto`, `_measured` follow it.

Required header keys: `reference`, `doi`, `arxiv`, `instrument`, `origin`,
`statement`, `year`, `source`, `mode`, `channel`, `confidence`, `dmfraction`,
`obs_time`, `figure`, `comment`, `status`. Optional: `authors`, `journalref`,
`profile`.

## Selecting by class

Bounds are classified along several axes so that a whole kind of result can be
included or excluded deliberately rather than by listing files.

```python
v = gdmbounds.load_vocabulary()

v.instruments_in("iact")     # every Cherenkov telescope
v.targets_in("cluster")      # every galaxy cluster
v.channels_with("line")      # channels giving a sharp spectral feature

print(v.describe())          # every class and its members
```

In the headers: `mode` is annihilation or decay; `origin` separates a
collaboration's own result from a forecast by individual authors; `statement`
separates a measured limit from a projected sensitivity — all 45 CTA entries are
projections, since CTA is not yet operating.

`profile` records the assumed halo density profile, and is **optional**: the
filename states it for 88 of 363 bounds. A missing `profile` means it was not
written down, not that none was assumed. Filtering on it excludes the other 275.

Tables carry `mass` (keV, MeV, GeV or TeV) and either `sigmav` (cm3s-1) or `tau` (s).
A sensitivity curve may give only a band, `sigmav_lo` and `sigmav_hi`.

Controlled vocabularies live in `gdmbounds/legends/`. `templates/` holds blank
headers to copy. `unconverted/` holds raw digitised material not yet transcribed.

## Contributing a bound

1. Copy the matching template from `templates/`.
2. Fill in the header. Provenance is mandatory: `doi` or `arxiv`, plus the
   `figure` the curve was taken from.
3. Name the file by the convention above.
4. Run `pytest tests/ -q`. Every bound is validated on every pull request; a
   malformed one will not merge.

## Roadmap

- [x] Schema and validation for the whole database
- [x] Continuous integration
- [x] Catalogue search and selection by criterion — instrument, channel,
      class of telescope, target class
- [ ] Plotting, with selectable styles
- [ ] Casting and recasting of limits between assumptions
- [ ] A public-facing way to generate figures without installing anything

## Licence

Code under BSD-3-Clause (`LICENSE`); the bound database under CC-BY-4.0
(`LICENSE-DATA`). Each bound is a transcription of a published result — citing
gDMbounds does not replace citing the original paper, whose DOI is in every file.

© M. Doro and G. D'Amico, 2022–2026. Earlier contributors are credited in
[contributions.md](contributions.md).
