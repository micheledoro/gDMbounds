# gDMbounds: Metadata → ECSV (YAML & JSON→ECSV guide)

This guide shows how to prepare a **YAML header** per paper/target and convert digitized curves from **WebPlotDigitizer (WPD) JSON** into clean **ECSV** files compatible with `dmbounds/bounds`. It also explains how to **plot many ECSV curves** together.

Focus on results; the cells handle housekeeping:

- **Units are unified automatically**  
  Mass → **GeV**; annihilation ⟨σv⟩ → **cm³/s**; decay τ → **s**.
- **Channels are set per curve** (unless the figure really has a single channel).

---

## Quickstart (4 steps)

1. **Create one YAML header per paper/target** using *Cell A* (short, guided).  
2. **Digitize** the curves with WebPlotDigitizer → export a **JSON** with series.  
3. **Run the JSON→ECSV converter** (*Cell B*): it reads YAML+JSON, converts units, resolves channels, writes `.ecsv`.  
4. **Plot/overlay** any number of ECSV curves with *Cell C*.

**Recommended names**

- Header YAML:  
  `{instrument}_{year}_{source}_header.yaml` → e.g. `mwa_2019_boo_header.yaml`
- ECSV per curve:  
  `{instrument}_{year}_{source}_{channel}_{tag?}{_vN?}.ecsv` → e.g. `mwa_2019_boo_bb_fl.ecsv`


---

## Cell A — YAML header (what to fill)

Use *Cell A* to write a header YAML. It holds metadata common to **all** curves from the same figure/paper.

### Minimal required (fill these)

| key            | example                                      | notes |
|----------------|----------------------------------------------|-------|
| `reference`    | *Constraints on dark matter…*                | Human-readable title of the result/paper. |
| `instrument`   | `MWA`, `Fermi-LAT`, `HAWC`, …                | Canonical short label. |
| `year`         | `2019`                                       | Publication/result year (YYYY). |
| `source`       | `Boo`, `Draco`, `M31`, `GC`, …               | Target/ROI canonical short name. |
| `confidence`   | `0.95`                                       | e.g. `0.68`, `0.90`, `0.95`, `0.99` (string). |
| `dmfraction`   | `1`                                          | Fraction of DM in this candidate (string). |
| `doi` **or** `arxiv` | `10.1103/PhysRevD.100.043002` / `1804.00628` | Provide **one** (no `arXiv:` prefix). |

### Optional (recommended)

| key            | example                         | why/when |
|----------------|---------------------------------|----------|
| `quantity`     | `annihilation` *(default)* or `decay` | Selects **Y-axis physics**. Converter writes `sigmav [cm³/s]` for annihilation or `lifetime [s]` for decay. |
| `x_unit_src`   | `GeV` *(or `TeV`, `MeV`)*       | **Original** X-axis units in the figure (converter → GeV). |
| `y_unit_src`   | `cm3 s-1` *(or `m3 s-1`; for decay: `s`)* | **Original** Y-axis units (converter → cm³/s or s). |
| `obs_time`     | `Phase I`, `1017d`, `6 years`   | Free short string. |
| `figure`       | `Fig. 2 (top-left)`             | What exactly was digitized. |
| `channel`      | `bb` *(**only if single channel** in the figure)* | **Leave empty** when the figure has multiple channels; the converter sets per-curve `channel`. Fill **only** if all curves are the **same** channel and WPD names lack channel hints. |
| `journalref`   | `Phys. Rev. D 100, 043002 (2019)` | Optional reference formatting. |
| `url`          | *(publisher or arXiv URL)*      | Optional link. |
| `collaboration`| `HAWC Collaboration`            | Optional. |
| `comment`      | `B=1 μG, D0=3e26 cm^2/s…`       | One-line assumptions. |
| `tags`         | `radio, dSph, Boo`              | Comma-separated. |
| `status`       | `done` / `wip` / `todo`         | Repo workflow. |

#### (Optional) Whitelist & mapping for robust channel detection

- `channels`: a **hint/whitelist** of canonical channels present in this figure  
  (e.g. `["bb","tautau","WW"]`). If you set `STRICT_CHANNEL_WHITELIST=True` in *Cell B*, curves outside this set are skipped.
- `series_map`: **bullet-proof mapping** from WPD series names to `{channel, tag}` when names are unusual.

```yaml
channels: ["bb","tautau","WW"]
series_map:
  "FL_bb":     {channel: "bb",     tag: "FL"}
  "CR_tau":    {channel: "tautau", tag: "CR"}
  "thin blue": {channel: "gammagamma", tag: "LAT"}
```
### Canonical channels
**bb, cc, tt, qq, uu, dd, ss, ee, mumu, tautau, WW, ZZ, hh, gg, gammagamma, Zg, nunu.**

---

## Cell B — JSON→ECSV converter (what it does)
Reads header + WPD JSON (supports `datasetColl` / `datasets`; points as `value[x,y]` or `x`,`y`).

**Converts to canonical units**
- mass → **GeV**  
- annihilation → **`sigmav [cm³/s]`**  
- decay → **`lifetime [s]`**

**Resolves channels per curve (priority)**
1) `series_map` (if provided)  
2) header `channel` (if filled)  
3) heuristics from series names (tokens like `bb`, `tautau`, `WW`, …; Greek/UTF-8 variants accepted)

**Writes ECSV with**
- Columns: `mass [GeV]` + `sigmav [cm3 s-1]` *(annih.)* **or** `lifetime [s]` *(decay)*
- `float32` dtype for both columns, units via `astropy.units`
- Per-curve meta includes `channel`, `tag`, `quantity`
- Filename: `{instrument}_{year}_{source}_{channel}_{tag?}{_vN?}.ecsv` (auto `_v2`, `_v3`, … avoids overwrite)

**Sanity checks & hints**
- Drops non-finite / non-positive points; sorts by mass; removes exact duplicate mass points
- Warns if magnitudes look off (likely unit mismatch in `x_unit_src` / `y_unit_src`)
- Clear `Skip(…)` messages for unresolved channel, empty series, unit parse issues, etc.
- Prints a summary of written files and skip reasons

### WPD series naming (best practice)

Name each WPD series with the **channel token** (and optional tag):

- **Channels** (canonical):  
  `bb, cc, tt, qq, uu, dd, ss, ee, mumu, tautau, WW, ZZ, hh, gg, gammagamma, Zg, nunu`
- **Tags** (optional, for provenance):  
  `FL` (Fermi-LAT), `CR` (cosmic-ray), instrument names like `MWA`, `MAGIC`, `HAWC`, `HESS`, `CTA`, `VERITAS`, `LHAASO`, …

**Examples:** `bb_FL`, `tautau_CR`, `gammagamma_LAT`, `WW`, `bb_MWA`.

The converter normalizes a lot of variants (e.g. `τ+τ−`, `mu+mu-`, `γγ`, `zγ`, `uu/dd/ss` → `qq`, etc.). If it **cannot** infer a channel, it prints `Skip (channel unresolved)`.

---

## Cell C — Plotting ECSV overlays

The plotting helper draws **any number** of ECSV files from **files / folders / globs** in one overlay, **grouped by quantity**:

- **Annihilation** curves (with `sigmav`) → one figure  
- **Decay** curves (with `lifetime`) → separate figure

**What it does**
- Accepts: paths, folders, and glob patterns (e.g., `outputs/*.ecsv`, `outputs/lat`, `other_run/**/*.ecsv`)
- Reads data + meta; converts units on the fly to canonical (GeV; cm³/s; s)
- Builds legend labels: `instrument year (source, channel) [tag]`
- Light style cue: `tag=FL` → dashed, `tag=CR` → dotted, else solid
- Legend placement adapts to many curves; log–log axes; saves PNG (and prints where)

**Examples**
```python
# Plot from an explicit list
result = plot_ecsv_many([
    "outputs/mwa_2019_boo_bb_fl.ecsv",
    "outputs/mwa_2019_boo_bb_cr.ecsv",
    "outputs/mwa_2019_boo_tautau_fl.ecsv",
    "outputs/mwa_2019_boo_tautau_cr.ecsv",
], out_base="outputs/mwa_2019_boo_overlay", title="MWA Boo limits")

# Plot everything in a folder (recursively)
result = plot_ecsv_many(
    ["outputs/lat"],                      # also accepts ["more/*.ecsv"]
    out_base="outputs/lat_overlay",
    title="LAT repository curves"
)
```

## Troubleshooting

**“No ECSV files written.”**  
No series had a recognizable channel and no `series_map` was provided.  
→ Add channel tokens to WPD series names (`bb`, `tautau`, `WW`, …) or supply `series_map` in the header YAML.

**“Skip (unit conversion failed …)”**  
Check `x_unit_src` / `y_unit_src`; acceptable examples: `GeV`, `TeV`, `cm3 s-1`, `m3 s-1`, `s`.

**“Sanity check failed …”**  
Units or dtypes are not canonical, or data contain non-positive values.  
→ Inspect the printed filename (the file is kept for inspection).

**Some external ECSV do not load**  
The plotter expects standard ECSV starting with `# %ECSV`. Files with a license banner **before** that line or with odd unicode dashes in YAML may fail.  
→ Easiest fix: pass those curves through your converter (YAML+JSON path) or normalize them manually to “pure” ECSV before plotting.

---

## Appendix A — Canonical channel vocabulary (normalized)

| canonical    | common synonyms recognized in names |
|--------------|-------------------------------------|
| `bb`         | bbar, b-b, b\bar{b}                 |
| `tautau`     | tau+tau-, τ+τ−, tau tau             |
| `mumu`       | mu+mu-, μμ, mu mu                   |
| `ee`         | e+e-                                |
| `WW`         | w+w-, w w                           |
| `ZZ`         | z z                                 |
| `hh`         | h h, Higgs                          |
| `gg`         | gluon, g g                          |
| `gammagamma` | γγ, gamma gamma, 2gamma, line       |
| `Zg`         | zγ, zgamma, γz, z-gamma             |
| `tt`         | top                                 |
| `cc`         | charm                               |
| `qq`         | uu/dd/ss, light quarks, q q         |
| `nunu`       | νν̄, nu nu                          |

---

## Appendix B — One-line checklist (before running Cell B)

- YAML: `reference`, `instrument`, `year`, `source`, `confidence`, `dmfraction`, and **one of** `doi`/`arxiv` are filled.  
- YAML: `quantity` is correct (`annihilation` / `decay`).  
- YAML: `x_unit_src` / `y_unit_src` match the **original** figure axes.  
- JSON: your WPD series names contain channel hints **or** you provided `series_map`.  
- (Optional) YAML: `channel` is **empty** when the figure has **multiple** channels.

**Happy bounding!** 🧪📈