"""One-off migration bringing every bound header up to the schema.

Works on the raw text rather than parsing and rewriting through astropy: the
headers are hand-aligned, several files do not parse at all in their current
state, and a round-trip would discard both the alignment and the licence
preamble. Run with --dry-run first.

Once the database is clean this script has served its purpose; it is kept for
the record of what was changed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOUNDS = ROOT / "gdmbounds" / "bounds"

#: Column at which every metadata value is aligned in the existing headers.
VALUE_COLUMN = 23

META_RE = re.compile(r'^# - \{(?P<key>[A-Za-z_]+)(?P<sep>:?)\s*(?P<value>.*?)\s*\}\s*$')
COLUMN_RE = re.compile(r'^# - \{name:\s*(?P<name>[^\s,]+)')

#: Historical value fixes, applied by key.
VALUE_FIXES = {
    "instrument": {"LAT": "lat"},
    "source": {"Coma Berenices dSph": "comaberenices"},
}

LICENCE_LINES = [
    "# %Part of https://github.com/micheledoro/gDMbounds under the\n",
    "# %Creative Commons Attribution 4.0 International License, see LICENSE-DATA\n",
]


def meta_line(key: str, value: str) -> str:
    """Render one metadata line with the database's alignment."""
    prefix = f"# - {{{key}:"
    padding = max(1, VALUE_COLUMN - len(prefix))
    return f"{prefix}{' ' * padding}{value}}}\n"


def mode_from_columns(lines: list[str]) -> str | None:
    """Infer annihilation vs decay from the quantity the table carries.

    More trustworthy than the filename: the column is the physics.
    """
    names = {m.group("name") for m in (COLUMN_RE.match(line) for line in lines) if m}
    if "sigmav" in names:
        return "ann"
    if "tau" in names:
        return "dec"
    return None


def mode_from_filename(path: Path) -> str | None:
    parts = path.stem.split("_")
    for token in parts:
        if token in ("ann", "dec"):
            return token
    return None


def migrate(path: Path) -> tuple[list[str], list[str]]:
    """Return the new lines and a list of what changed."""
    lines = path.read_text().splitlines(keepends=True)
    changes: list[str] = []
    out: list[str] = []

    seen_keys = set()
    in_meta = False
    for line in lines:
        # Only the block after `meta: !!omap` holds metadata. The `datatype`
        # block above it uses the same `# - {...}` syntax and must be left alone.
        if line.startswith("# meta:"):
            in_meta = True
            out.append(line)
            continue
        if line.startswith(("# schema", "# ---")):
            in_meta = False
        # Licence preamble: two fixed lines following the %ECSV marker.
        if line.startswith("# %Part of"):
            if line != LICENCE_LINES[0]:
                changes.append("licence line 1")
            out.append(LICENCE_LINES[0])
            continue
        if line.startswith("# %Creative Commons"):
            if line != LICENCE_LINES[1]:
                changes.append("licence line 2")
            out.append(LICENCE_LINES[1])
            continue

        # The schema trailer uses a Unicode minus in almost every file.
        if line.startswith("# schema"):
            fixed = line.replace("−", "-")
            if fixed != line:
                changes.append("unicode minus in schema line")
            out.append(fixed)
            continue

        match = META_RE.match(line) if in_meta else None
        if not match:
            out.append(line)
            continue

        key, sep, value = match.group("key"), match.group("sep"), match.group("value")

        if key == "author":
            key = "authors"
            changes.append("author -> authors")
        if not sep:
            changes.append(f"missing colon after '{key}'")

        stripped = value.strip('"')
        replacement = VALUE_FIXES.get(key, {}).get(stripped)
        if replacement is not None:
            changes.append(f"{key}: '{stripped}' -> '{replacement}'")
            value = f'"{replacement}"'

        seen_keys.add(key)
        out.append(meta_line(key, value))

        # `mode` is new; it belongs with the other identity keys, right after
        # the source it qualifies.
        if key == "source" and "mode" not in seen_keys:
            mode = mode_from_columns(lines) or mode_from_filename(path)
            if mode is None:
                changes.append("!! could not determine mode")
            else:
                from_name = mode_from_filename(path)
                if from_name and from_name != mode:
                    changes.append(
                        f"!! mode from columns '{mode}' disagrees with filename '{from_name}'"
                    )
                out.append(meta_line("mode", f'"{mode}"'))
                seen_keys.add("mode")
                changes.append(f"added mode='{mode}'")

    return out, changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show", type=int, default=0, help="print a diff for N files")
    args = parser.parse_args()

    paths = sorted(BOUNDS.glob("*/*.ecsv"))
    changed = 0
    warnings: list[str] = []
    shown = 0

    for path in paths:
        new_lines, changes = migrate(path)
        if not changes:
            continue
        changed += 1
        warnings.extend(f"{path.name}: {c}" for c in changes if c.startswith("!!"))

        if shown < args.show:
            shown += 1
            print(f"--- {path.relative_to(ROOT)}")
            old = path.read_text().splitlines(keepends=True)
            import difflib

            sys.stdout.writelines(difflib.unified_diff(old, new_lines, n=1, lineterm="\n"))
            print()

        if not args.dry_run:
            path.write_text("".join(new_lines))

    print(f"{'would change' if args.dry_run else 'changed'} {changed} of {len(paths)} files")
    if warnings:
        print(f"\n{len(warnings)} need attention:")
        for w in warnings:
            print(" ", w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
