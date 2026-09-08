"""gDMbounds — gamma-ray bounds on dark matter annihilation and decay.

The package is being rebuilt. What exists today is the schema layer: the
definition of what a bound file is, and the validation that enforces it.
Catalogue loading, selection and plotting are built on top of it.
"""

from .quality import check_all_curves, check_curve
from .schema import (
    CHANNEL_SPECTRA,
    INSTRUMENT_CLASSES,
    MODES,
    ORIGINS,
    PROFILES,
    REQUIRED_META,
    STATEMENTS,
    TARGET_CLASSES,
    Issue,
    Vocabulary,
    check_database,
    check_file,
    check_vocabulary,
    iter_bound_files,
    load_vocabulary,
    parse_filename,
)

__version__ = "0.2.0"

__all__ = [
    "CHANNEL_SPECTRA",
    "INSTRUMENT_CLASSES",
    "MODES",
    "ORIGINS",
    "PROFILES",
    "REQUIRED_META",
    "STATEMENTS",
    "TARGET_CLASSES",
    "Issue",
    "Vocabulary",
    "__version__",
    "check_all_curves",
    "check_curve",
    "check_database",
    "check_file",
    "check_vocabulary",
    "iter_bound_files",
    "load_vocabulary",
    "parse_filename",
]
