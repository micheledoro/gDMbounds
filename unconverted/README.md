# Unconverted source material

Raw digitised data that has never been turned into a bound. Nothing here is
part of the database: `gdmbounds/bounds/` contains only validated ECSV files,
and CI requires every file in it to satisfy the schema.

- `askap/` — four two-column text files of *radio* limits on the LMC. The
  `askap` directory under `bounds/` held these and no ECSV at all, so ASKAP is
  not in fact represented in the database.
- `cta_moritz_old/` — seven text files of CTA sensitivity curves predating the
  ECSV format.
- `*.json` — digitised curves, presumably the input from which the
  corresponding ECSV bounds were transcribed.

To promote any of these, transcribe it into an ECSV using `templates/` and give
it full provenance (`doi` or `arxiv`, plus `figure`). Without provenance a curve
cannot be archived.
