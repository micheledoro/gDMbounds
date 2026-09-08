"""Print the vocabulary: every class a bound can be selected by, and its members.

    python -m gdmbounds
"""

from .schema import load_vocabulary


def main() -> int:
    print(load_vocabulary().describe())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
