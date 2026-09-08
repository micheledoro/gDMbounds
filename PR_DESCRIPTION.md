# Rebuild: schema, validation, packaging and CI

Replaces the abandoned mid-refactor with a working package built around an
explicit schema, and brings the whole bound database into conformance with it.

Base note: this branch was developed from `17ad7c2` (25 Sept) before the
September–November work on `main` was visible. Those 25 commits are preserved on
`archive/main-pre-rebuild`, and the content they added — four MWA bounds and one
NuSTAR bound — has been ported onto this branch.

## Why

Neither entry point imported. `from dmbounds import dmbounds` raised `ImportError`
on an empty `computations.py`; the working legacy module failed at import because
it reads `legend_instruments.ecsv` at module level and that file no longer parsed.
One unquoted three-word value in the `mwa` legend row made astropy read three
columns instead of two, and **broke every import of the package for eleven months**
without anyone noticing.

That is the argument for CI, and it is why the first test is `import` plus "every
bound parses".

## What changed

**Package.** `dmbounds` → `gdmbounds`, so repo, package and PyPI name agree.
`pyproject.toml` replaces `setup.py`. The abandoned modules are deleted; the
working legacy implementation moves to `legacy/`, outside the package, as a
behavioural reference.

**Schema.** `gdmbounds/schema.py` is the single definition of what a bound is:
required metadata, controlled vocabularies, filename convention, and the checks
that filename and header agree. The header is the source of truth.

**Database migration.** All 367 bounds now parse and validate. Notably:
`mode` (annihilation vs decay) existed only in filenames and is now in the data;
`confidence` was written without its colon in 351 files and had therefore never
been a key at all; seven files did not parse; three carried a `channel`
copy-pasted from a sibling — verified the curves were genuinely distinct before
correcting the header.

**Classification.** Seven axes bounds can be selected along: `mode`, `origin`,
`statement` (measured vs projected), `profile`, plus instrument class, target
class and channel spectrum in the legends. This is what makes "every IACT" or
"every dwarf spheroidal" expressible.

**Beyond gamma rays.** NuSTAR constrains keV-scale dark matter, so masses in keV
and MeV are now valid and `xray` joins the instrument classes.

**CI.** Schema validation on three Python versions, `ruff`, and a wheel build
asserting the shipped file set matches the source tree exactly.

## What still needs a decision

- `magic_2018_perseuscluster_dec_WW` is a **closed contour** — it climbs in mass,
  turns, and returns to within 6% of its start. That is a region, not an upper
  limit. The source paper needs checking. (A second such file,
  `lat_2023_sagittarius_ann_bb`, was found the same way and removed; it had
  independently been deleted upstream in October as bad data.)
- 23 further bounds have points out of order or repeated, consistent with
  digitisation noise. Sorting by mass is very probably right but edits scientific
  data, so they are quarantined rather than silently fixed.
- The two ported papers are marked `origin: "author"` on the reading that they are
  analyses of public data by individual authors rather than collaboration results.

The quarantine is a ratchet: a newly broken bound fails CI, and a fixed one fails
until it is delisted. It can only shrink.

## State

```
367 bounds — 0 schema violations — 727 tests passing, 24 skipped — ruff clean
```
