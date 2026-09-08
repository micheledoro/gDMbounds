# gDMbounds

A database and toolkit for gamma-ray indirect Dark Matter searches: published
experimental limits on DM annihilation and decay, the means to plot them, and
(planned) methods to recast them.

Successor to `moritzhuetten/dmbounds`; the canonical repo is `micheledoro/gDMbounds`
and the package is `gdmbounds` — repo, package and PyPI name are deliberately aligned.

## People

- **Michele Doro** (professor, Univ. Padova) — initial idea, maintainer.
- **Giacomo D'Amico** — active collaborator; co-author of the casting/recasting
  methods that macro-function 3 will implement.
- Earlier contributors are listed in `contributions.md`.

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
- **Instrument and target classes** (IACT / satellite / shower-front; dSph /
  cluster / ...) belong in the legend ECSV files as an extra column, not in a
  Python dictionary — data stays data. *Not yet added.*
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
tools/              one-off migration scripts, kept as a record
unconverted/        raw digitised material not yet transcribed into bounds
.github/workflows/  CI: schema validation, lint, and wheel contents
legacy/             pre-2026 code, not shipped, reference only
templates/          blank ECSV headers for adding a new bound
sandbox/<name>/     per-person scratch work; nothing in the package imports from it
```

## Data model

363 bound files under `gdmbounds/bounds/<instrument>/`. Instrument directories:
`collider`, `cta`, `dampe`, `directsearches`, `hawc`, `hess`, `lat`, `lhaaso`,
`magic`, `multi-inst`, `veritas`. ASKAP appears in the legend but has no bounds:
its directory held four raw text files and no ECSV, now in `unconverted/`.

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
`instrument`, `origin`, `year`, `source`, `mode`, `channel`, `confidence`,
`dmfraction`, `obs_time`, `figure`, `comment`, `status`. Optional: `authors`,
`journalref`.

`mode` (`ann`/`dec`) and `origin` (`collaboration`/`author`) were both added in
the 2026 migration. Neither existed before: annihilation-vs-decay lived only in
the filename, and provenance only in which directory a file happened to sit in.

**Table columns:** `mass` (GeV or TeV) always; `sigmav` (cm3s-1) for annihilation,
`tau` (s) for decay. A sensitivity curve may give only a band (`sigmav_lo` /
`sigmav_hi`) with no central value, and that satisfies the schema. Some stacked-dSph
files carry one column per member galaxy.

## State

All 363 bounds satisfy the schema; `pytest tests/ -q` is green (366 tests). CI runs
that check, `ruff`, and a wheel build that asserts the bounds are actually inside
the package.

Built so far: the schema layer only. **Not yet written** — catalogue loading and
metadata search, selection by criterion, plotting, and recasting. `legacy/dmbounds_old.py`
shows what the old API offered (`plot`, `metadata`, `filter_metadata`, `get_data`,
`PlottingStyle`, `interactive_selection`) and is worth reading before designing
the replacement.

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
