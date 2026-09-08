# gDMbounds

A database and toolkit for gamma-ray indirect Dark Matter searches: published
experimental limits on DM annihilation and decay, the means to plot them, and
(planned) methods to recast them.

Successor to `moritzhuetten/dmbounds`; the canonical repo is now
`micheledoro/gDMbounds`. Some files still carry the old URL — see *Known issues*.

## People

- **Michele Doro** (professor, Univ. Padova) — initial idea, maintainer.
- **Giacomo D'Amico** — active collaborator; co-author of the casting/recasting
  methods that macro-function 3 will implement.
- Earlier contributors are listed in `contributions.md`.

**Archived work:** the `aleksandra` branch holds sandbox material that has been
deliberately removed from `main`. Do not merge it, copy from it, or use it as a
reference. It exists as a record only. ECSV header corrections under
`dmbounds/bounds/lat/` that originated there are format fixes to project data
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
   scripts, pre-rendered images, or a combination. Not yet decided.
3. **Recasting.** Apply the casting/recasting methods published by Doro and
   D'Amico to transform limits between assumptions. **Nothing exists yet**;
   `dmbounds/computations.py` is an empty placeholder where this belongs.
4. **Professional structure.** Real continuous integration, and a presentation
   layer that exposes data and methods to a wider public. Explicitly a
   first-class goal, not polish to add later.

**Current phase: structure before content.** The near-term work is deciding the
architecture — packaging, CI, data validation, how the web layer relates to the
Python library. Resist adding features or bounds until that is settled.

## Current state — read before assuming

The repository is **mid-refactor and the refactor is incomplete**:

- `dmbounds/dmbounds_old.py` (1191 lines) is the real, working legacy
  implementation.
- `dmbounds/dmbounds.py`, `data_reader.py`, `plotter.py` are a newer modular
  skeleton that is **largely non-functional scaffolding**. `read_multiple_ecsv`
  builds an empty DataFrame and never populates it; `plotter.py` is generic
  matplotlib boilerplate with `'X-axis'` labels; `dmbounds.py:main()` references
  a nonexistent `bounds/instrument2/` path.
- `dmbounds/computations.py` is a 0-byte file.

Do not mistake the new modules for a working API. Any real behaviour currently
lives in `dmbounds_old.py`.

There is **no CI, no test suite, no `pyproject.toml`, and no pinned
requirements**. Packaging is a legacy `setup.py` still pointing at the old
upstream repo and author.

## Data model

363 ECSV files under `dmbounds/bounds/<instrument>/`, one file per published
limit curve. Instruments present: `askap`, `authors`, `collider`, `cta`,
`dampe`, `directsearches`, `hawc`, `hess`, `lat`, `lhaaso`, `magic`,
`multi-inst`, `veritas`. (`authors` holds theory/phenomenology curves rather
than one experiment.)

**Filename convention:**

```
<instrument>_<year>_<target>_<mode>_<channel>[_<qualifiers>].ecsv
```

`mode` is `ann` or `dec`. Qualifiers such as `_sens`, `_einasto`, `_nfw`,
`_expo`, `_unbinned`, `_measured`, `_benchmark` may follow the channel — so the
channel is **not** simply the last underscore-separated token. Parse against the
`channel` metadata key, not by splitting the filename.

**File format:** ECSV with an `astropy` table. Columns are typically `mass`
(GeV) and `sigmav` (cm3s-1) for annihilation or a lifetime for decay, sometimes
with `±1sigma`/`±2sigma` containment bands. The header carries a YAML `!!omap`
of metadata: `reference`, `authors`, `journalref`, `doi`, `arxiv`, `instrument`,
`year`, `source`, `channel`, `confidence`, `dmfraction`, `obs_time`, `figure`,
`comment`, `status`.

Controlled vocabularies live in `dmbounds/legends/`
(`legend_instruments.ecsv`, `legend_channels.ecsv`, `legend_targets.ecsv`);
theory curves in `dmbounds/modelpredictions/`; blank headers to copy in
`templates/`.

## Known issues in the data

Found by scanning all 363 files. These are the concrete argument for validation
in CI — they are systematic, not one-offs:

- **357/363** write the metadata key as `{confidence  "0.95" }` — missing the
  colon, so it is not valid YAML and does not parse as a key.
- **358/363** end with `schema : astropy −2.0` using a Unicode minus (U+2212)
  instead of an ASCII hyphen.
- **3** files disagree between filename and `channel` metadata:
  `cta_2023_perseuscluster_ann_bb_sens.ecsv`, `magic_2022_segue1_ann_bb.ecsv`,
  and `magic_2022_segue1_ann_WW.ecsv` all declare `channel: "tautau"`.
- **4** still reference the old `moritzhuetten` URL in their licence line.

The six already-clean files are those corrected in September 2025; the fix was
never applied to the rest.

## Conventions

- Repo language is **English** — code, comments, commit messages, docs.
- Work on branches and open a PR; `main` is the published branch.
- `sandbox/` holds per-person exploratory work (`sandbox/<name>/`). It is
  scratch space: nothing in the library should import from it.
- Bounds are transcribed from published figures/tables. Every new bound needs
  its provenance in the ECSV header — `doi` or `arxiv` plus `figure`.
