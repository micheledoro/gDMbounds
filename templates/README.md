# Templates for a new bound

Copy the one matching the process you are transcribing, fill every field, and
name the file by the convention:

    <instrument>_<year>_<source>_<mode>_<channel>[_<qualifiers>].ecsv

Then run `pytest tests/ -q`. CI validates every bound on every pull request, so a
malformed one will not merge.

## Filling it in

- `instrument`, `source` and `channel` must be shortnames that already exist in
  `gdmbounds/legends/`. If yours is new, add it to the legend *with its class* in
  the same pull request.
- `origin` separates a collaboration's own result from an analysis published by
  individual authors using public data.
- `statement` separates a measured limit from a projected sensitivity. Getting
  this wrong puts a forecast on a plot as though it were a measurement.
- `profile` is optional — add `# - {profile: "nfw"}` and so on when the paper
  states the assumed halo profile. Omitting it means *not recorded*, never
  *none assumed*.
- Provenance is mandatory: `doi` or `arxiv`, plus the `figure` the curve came from.

## Two traps these templates once set

The old template wrote `{confidence  "0.95" }` without its colon, so the value was
never a key at all, and 351 bounds inherited the defect before anyone noticed. It
also carried a Unicode minus in the schema line. Both are fixed here, and
`tests/test_templates.py` now checks the templates against the same schema as the
database — so a template can no longer quietly seed a broken bound.
