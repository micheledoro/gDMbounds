# gDMbounds

A database and toolkit for gamma-ray indirect Dark Matter searches: published
experimental limits on DM annihilation and decay, the means to plot them, and
(planned) methods to recast them.

Successor to `moritzhuetten/dmbounds`; the canonical repo is `micheledoro/gDMbounds`
and the package is `gdmbounds` — repo, package and PyPI name are deliberately aligned.

## People

The software is authored by **Michele Doro** (professor, Univ. Padova) and
**Giacomo D'Amico**, who together published the casting/recasting methods that
macro-function 3 will implement. Earlier contributors, including the original
framework author, are credited in `contributions.md` but are not authors of the
current software.

**Author lists inside ECSV headers are citations, not project authorship.** They
name the authors of the paper a bound was transcribed from, and must never be
edited to reflect who works on gDMbounds. The same goes for filenames that cite
a paper, such as `modelpredictions/wimp_huetten2017_*`.

**Archived work:** the `aleksandra` branch holds sandbox material that has been
deliberately removed from `main`. Do not merge it, copy from it, or use it as a
reference. It exists as a record only. ECSV header corrections under
`gdmbounds/bounds/lat/` that originated there are format fixes to project data
and intentionally remain in `main`.

## Where the project is going

Four macro-functions define the target. They are a design brief, not a
description of what exists today.

1. **Archive.** Curated collection of published gamma-ray limits on DM
   annihilation and decay, including historical ones — the value is partly in
   preserving results that would otherwise be lost in old papers.
2. **Plotting.** Let a user select bounds and plot them, either explicitly or
   semi-automatically by criterion: all bounds from one experiment, one
   annihilation channel, one class of telescope, and so on. Multiple styles.
   **Open question:** delivery mechanism — interactive web, downloadable
   scripts, pre-rendered images, or a combination. Deliberately deferred until
   the library API is stable.
3. **Recasting.** Apply the casting/recasting methods published by Doro and
   D'Amico to transform limits between assumptions. **Nothing exists yet.**
4. **Professional structure.** Real continuous integration, and a presentation
   layer that exposes data and methods to a wider public.

## Decisions taken

- **Rebuild rather than repair.** The pre-2026 modules were abandoned mid-refactor
  and did not import. They were removed; `legacy/dmbounds_old.py` is kept
  **out of the package** as a reference for behaviour worth reproducing, not as
  code to extend.
- **The ECSV header is the source of truth**, the filename a human-readable
  convention that must agree with it. `gdmbounds/schema.py` defines the contract
  and the tests enforce it.
- **Licensing is split**: code under BSD-3-Clause (`LICENSE`), the bound database
  under CC-BY-4.0 (`LICENSE-DATA`). The old combined CC-BY-NC-SA-3.0 is kept as
  `LICENSE-legacy-CC-BY-NC-SA-3.0` and still governs `legacy/`.
- **Instrument and target classes** live in the legend ECSV files as an extra
  column, not in a Python dictionary — data stays data. The canonical class sets
  and their meanings are in `schema.py` (`INSTRUMENT_CLASSES`, `TARGET_CLASSES`,
  `CHANNEL_SPECTRA`) and reach users through `Vocabulary.describe()`.
- **Every bound sits under the instrument its header declares.** There is no
  `authors/` directory: a forecast by individual authors lives under its
  instrument and is marked `origin: "author"`, so it can be included or excluded
  by query rather than by directory. The author surname is a filename qualifier.

## Layout

```
gdmbounds/          the package
  schema.py         what a bound file is, and its validation — everything builds on this
  bounds/<inst>/    363 ECSV files, one per published limit curve
  legends/          controlled vocabularies: instruments, channels, targets
  modelpredictions/ theory curves (thermal relic, GAMBIT scan)
tests/              schema validation; run with pytest
  quality.py        checks on the numbers, kept separate from the schema
  catalog.py        every header in one table, with selection over it
tools/              migration scripts and data_review.py, which regenerates DATA_REVIEW.md
unconverted/        material the schema cannot yet hold, including ALP contours
.github/workflows/  CI: schema validation, lint, and wheel contents
legacy/             pre-2026 code, not shipped, reference only
templates/          blank ECSV headers for adding a new bound
sandbox/<name>/     per-person scratch work; nothing in the package imports from it
```

## Data model

385 bound files under `gdmbounds/bounds/<instrument>/`. Instrument directories:
`collider`, `cta`, `dampe`, `directsearches`, `hawc`, `hess`, `lat`, `lhaaso`,
`magic`, `multi-inst`, `mwa`, `nustar`, `veritas`. The archive is no longer
purely gamma-ray: MWA is radio and NuSTAR is X-ray, and NuSTAR constrains dark
matter at **keV** masses, so `MASS_UNITS` admits keV and MeV. There was an `askap/` directory holding four raw
text files and no ECSV; it is now in `unconverted/`. ASKAP is not in
`legend_instruments` and never was, so — like the old `authors/` directory — it
was invisible to the loader, which globs by legend key.

**Filename convention:**

```
<instrument>_<year>_<source>_<mode>_<channel>[_<qualifiers>].ecsv
```

`mode` is `ann` or `dec`. The channel is the **fifth underscore-separated token** —
not the last: qualifiers such as `_sens`, `_einasto`, `_nfw`, `_measured`,
`_benchmark`, `_substructure-high` may follow it, and may themselves contain
hyphens. Tokens are not all lowercase: `LMC` and `WW` are correct as written.

**Composite identifiers:** a joint analysis is `multi-inst-<a>-<b>`; a stacked
target sample is `multi<class>[-<n>][-<member>...]`, e.g. `multidsph-4-booetes1-draco`.
`schema.base_instrument` and `schema.base_source` collapse these to the token used
for grouping.

**Header metadata** (`REQUIRED_META` in `schema.py`): `reference`, `doi`, `arxiv`,
`instrument`, `origin`, `statement`, `year`, `source`, `mode`, `channel`,
`confidence`, `dmfraction`, `obs_time`, `figure`, `comment`, `status`. Optional:
`authors`, `journalref`, `profile`.

`mode` (`ann`/`dec`) and `origin` (`collaboration`/`author`) were both added in
the 2026 migration. Neither existed before: annihilation-vs-decay lived only in
the filename, and provenance only in which directory a file happened to sit in.

**Table columns:** `mass` (GeV or TeV) always; `sigmav` (cm3s-1) for annihilation,
`tau` (s) for decay. A sensitivity curve may give only a band (`sigmav_lo` /
`sigmav_hi`) with no central value, and that satisfies the schema. Some stacked-dSph
files carry one column per member galaxy.

## Classification axes

These are what makes "plot every IACT bound" or "every dwarf spheroidal"
expressible. Four exist; two are proposed and not yet built.

| Axis | Where it lives | Spread |
|---|---|---|
| annihilation vs decay | `mode` key | 338 ann / 47 dec |
| collaboration vs author | `origin` key | 357 / 10 |
| measured vs projected | `statement` key | 319 limit / 48 sensitivity |
| halo profile assumed | `profile` key, optional | 88 stated / 275 not |
| detection technique | `class` in `legend_instruments` | iact, satellite, xray, swd, radio, collider, direct, combined |
| target type | `class` in `legend_targets` | dsph, cluster, globular, galaxy, gc, diffuse, subhalo, unid |
| line vs continuum | `spectrum` in `legend_channels` | continuum, line, model, benchmark |

Two things to hold on to. All 45 CTA bounds are `sensitivity`, which is right —
CTA is not operating; treat any future CTA bound claiming `limit` as suspect until
checked. And **a missing `profile` means the filename never said, not that no
profile was assumed** — every J-factor rests on one. Filtering on `profile` drops
275 bounds, and any selection doing so should say it is.

## State

All 363 bounds satisfy the schema. `pytest tests/ -q` is green — 788 passing, 23 skipped. CI runs that check, `ruff`, and a wheel build that asserts the bounds are
actually inside the package.

The 24 skips are quarantined in `tests/test_data_quality.py`: bounds whose *numbers*
are unusable even though the file is well-formed. Twenty-three have points out of
order or repeated, consistent with digitisation noise. Two are **closed contours** —
`lat_2023_sagittarius_ann_bb` and `magic_2018_perseuscluster_dec_WW` climb in mass,
turn, and return to within a few percent of where they started. A closed contour is
a region, not an upper limit, and cannot be plotted or interpolated as one. Both need
their source papers checked.

The quarantine is a ratchet: a new bad file fails the suite, and a quarantined file
that gets fixed also fails until it is removed from the list. The same pattern guards
against a bound duplicating another's curve.

`DATA_REVIEW.md` collects everything that passes the schema but still needs a human
to read a paper. It is **generated** by `tools/data_review.py` — re-run that rather
than editing it, or it will drift from the data it describes.

Built so far: `schema` (what a bound is), `quality` (whether its numbers are
usable) and `catalog` (every header in one table, with composable selection).
**Not yet written** — plotting and recasting. `legacy/dmbounds_old.py` shows what
the old API offered (`plot`, `PlottingStyle`, `interactive_selection`) and is worth
reading before designing the replacement.

`Catalog.select` matches the publishing instrument; `Catalog.involves` matches
participation, so a joint MAGIC+LAT analysis is found by the second and not the
first. That distinction is deliberate — 86 bounds involve MAGIC, 74 are MAGIC's
own.

## Conventions

- Repo language is **English** — code, comments, commit messages, docs.
- Work on branches and open a PR; `main` is the published branch.
- Bounds are transcribed from published figures/tables. Every new bound needs its
  provenance in the header — `doi` or `arxiv` plus `figure`.
- Never hand-edit a legend or bound file without running `pytest`: a single
  unquoted multi-word value once broke every import of the package for eleven
  months without anyone noticing.
- **Reinstalling after a data change needs `pip install --no-cache-dir .`**, and
  delete `build/` first. Most of this package is data, but pip caches the built
  wheel by version, and setuptools keeps renamed and deleted files in `build/lib`.
  Both will silently serve you a stale database while `pytest` on the source tree
  says everything is fine. CI is immune — it builds from a fresh checkout.
