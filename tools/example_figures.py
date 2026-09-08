"""Render the example gallery into figures/.

    python tools/example_figures.py [--outdir figures]

The figures are not committed. A PNG in the repository would go stale the moment
the data or the plotting changed, and unlike the generated Markdown there is no
cheap way to test that it has not — so the script is the artefact, and the
pictures are whatever it produces today.

Each example is chosen to show something the plotting layer decides on your
behalf, not merely to look like a plot.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

import gdmbounds  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def examples(cat):
    """(filename, title, selection, kwargs) for each figure, with why it is here."""
    return [
        (
            "dsph-annihilation-bb",
            "Annihilation to $b\\bar{b}$, dwarf spheroidals",
            cat.select(target_class="dsph", mode="ann", channel="bb", statement="limit"),
            {"label": "{instrument} {year}"},
            "The canonical figure: measured limits only, against the thermal relic.",
        ),
        (
            "fornax-profiles",
            "H.E.S.S. Fornax cluster — halo profile assumptions",
            cat.select(instrument="hess", source="fornaxcluster", channel="bb", mode="ann"),
            {},
            "Eleven bounds sharing every metadata field. Labels fall back to the "
            "filename qualifiers, because that is where the physics differs.",
        ),
        (
            "iact-measured-and-projected",
            "Cherenkov telescopes, $b\\bar{b}$ — measured and projected",
            cat.select(instrument_class="iact", mode="ann", channel="bb"),
            {"label": "{instrument} {year}"},
            "CTAO is not operating; its curves are dashed so they cannot be read "
            "as measurements.",
        ),
        (
            "decay-lifetime",
            "Decay to $b\\bar{b}$ — lifetime, not cross section",
            cat.select(mode="dec", channel="bb"),
            {"label": "{instrument} {year}", "relic": None},
            "A different y axis entirely, which is why a mixed selection raises.",
        ),
        (
            "styles",
            None,
            cat.select(instrument=["magic", "hess", "lat"], target_class="dsph",
                       mode="ann", channel="tautau").select(year=[2016, 2020, 2022, 2023]),
            {"label": "{instrument} {year}"},
            "The same selection in all four styles, print included.",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", default=ROOT / "figures", type=Path)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    cat = gdmbounds.catalog()
    for name, title, selection, kwargs, why in examples(cat):
        if name == "styles":
            figure, axes = plt.subplots(2, 2, figsize=(15, 11))
            for ax, style in zip(axes.ravel(), ["default", "paper", "talk", "print"]):
                gdmbounds.plot(selection, ax=ax, style=style, **kwargs)
                ax.set_title(f"style = {style}")
            figure.tight_layout()
        else:
            figure, ax = plt.subplots(figsize=(8.5, 5.5))
            gdmbounds.plot(selection, ax=ax, **kwargs)
            ax.set_title(title)
        path = args.outdir / f"{name}.png"
        figure.savefig(path, dpi=110, bbox_inches="tight")
        plt.close(figure)
        print(f"  {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
        print(f"      {len(selection)} bounds — {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
