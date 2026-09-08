"""gDMbounds — gamma-ray bounds on dark matter annihilation and decay.

Two layers exist. `schema` defines what a bound file is and validates it;
`catalog` reads every header into one table and gives selection over it. Plotting
and recasting are still to come.

    >>> import gdmbounds
    >>> gdmbounds.catalog().select(instrument_class="iact", mode="ann", channel="bb")
"""

from .catalog import Catalog, catalog
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
    "Catalog",
    "Issue",
    "Vocabulary",
    "__version__",
    "catalog",
    "check_all_curves",
    "check_curve",
    "check_database",
    "check_file",
    "check_vocabulary",
    "iter_bound_files",
    "load_vocabulary",
    "parse_filename",
]
