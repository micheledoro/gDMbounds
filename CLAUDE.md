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
  Python dictionary — data stays data.

## Layout

```
gdmbounds/          the package
  schema.py         what a bound file is, and its validation — everything builds on this
  bounds/<inst>/    363 ECSV files, one per published limit curve
  legends/          controlled vocabularies: instruments, channels, targets
  modelpredictions/ theory curves (thermal relic, GAMBIT scan)
tests/              schema validation; run with pytest
legacy/             pre-2026 code, not shipped, reference only
templates/          blank ECSV headers for adding a new bound
sandbox/<name>/     per-person scratch work; nothing in the package imports from it
```

## Data model

363 bound files under `gdmbounds/bounds/<instrument>/`. Instrument directories:
`askap`, `authors`, `collider`, `cta`, `dampe`, `directsearches`, `hawc`, `hess`,
`lat`, `lhaaso`, `magic`, `multi-inst`, `veritas`. (`authors` holds
theory/phenomenology curves rather than one experiment.)

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
`instrument`, `year`, `source`, `mode`, `channel`, `confidence`, `dmfraction`,
`obs_time`, `figure`, `comment`, `status`. Optional: `authors`, `journalref`.

`mode` is **new**: no historical file carries it, so annihilation-vs-decay lived
only in the filename. Adding it is part of the pending migration.

**Table columns:** `mass` (GeV or TeV) always; `sigmav` (cm3s-1) for annihilation,
`tau` (s) for decay. Some files add containment bands; some stacked-dSph files
carry one column per member galaxy.

## Pending data migration

`pytest` currently fails on 8 tests — deliberately. The failures are the real
defect list, not noise, and each needs fixing before the catalogue layer is built:

- **356** files missing `mode`; **351** missing `confidence` (written as
  `{confidence  "0.95" }`, no colon, so it never parsed as a key).
- **7** unreadable: band columns present in the data but not declared in the
  `datatype` block.
- **19** filename/header mismatches, and **3** filenames in `authors/` that do not
  follow the convention at all.
- **10** values outside the controlled vocabularies.

Run `pytest tests/ -q` for the current list.

## Conventions

- Repo language is **English** — code, comments, commit messages, docs.
- Work on branches and open a PR; `main` is the published branch.
- Bounds are transcribed from published figures/tables. Every new bound needs its
  provenance in the header — `doi` or `arxiv` plus `figure`.
- Never hand-edit a legend or bound file without running `pytest`: a single
  unquoted multi-word value once broke every import of the package for eleven
  months without anyone noticing.
