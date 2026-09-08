"""gDMbounds — gamma-ray bounds on dark matter annihilation and decay.

The package is being rebuilt. What exists today is the schema layer: the
definition of what a bound file is, and the validation that enforces it.
Catalogue loading, selection and plotting are built on top of it.
"""

from .schema import (
    MODES,
    REQUIRED_META,
    Issue,
    Vocabulary,
    check_database,
    check_file,
    iter_bound_files,
    load_vocabulary,
    parse_filename,
)

__version__ = "0.2.0"

__all__ = [
    "MODES",
    "REQUIRED_META",
    "Issue",
    "Vocabulary",
    "__version__",
    "check_database",
    "check_file",
    "iter_bound_files",
    "load_vocabulary",
    "parse_filename",
]
