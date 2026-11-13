"""Canonical SPHEREx Level 2 FLAGS bits and the exclusion policy of the SED demo.

Sources: SPHEREx Explanatory Supplement v2.1 Table 16, the IRSA Spectrophotometry Tool help page, live
QR2 (VERSION 6.5.7) and QR3/DR1 (VERSION 7.0.5) headers. Bit names are never read from headers: QR2 files
use ``MP_<NAME>`` keywords, R7 files use ``MSKN####``/``MSKM####`` and omit unused planes.
"""

from __future__ import annotations

import numpy as np

FLAG_BITS: dict[str, int] = {
    "TRANSIENT": 0,
    "OVERFLOW": 1,
    "SUR_ERROR": 2,
    "PHANTOM": 4,
    "REFERENCE": 5,
    "NONFUNC": 6,
    "DICHROIC": 7,
    "MISSING_DATA": 9,
    "HOT": 10,
    "COLD": 11,
    "FULLSAMPLE": 12,
    "SUR_MISMATCH": 13,
    "PHANMISS": 14,
    "NONLINEAR": 15,
    "VAR_UNDER": 16,
    "PERSIST": 17,
    "PERSIST_UNK": 18,
    "OUTLIER": 19,
    "CROSSTALK": 20,
    "SOURCE": 21,
    "GHOST": 22,
    "GHOST_FPA": 23,
    "GHOST_EXT": 24,
    "STREAK": 25,
    "BLOOM": 26,
    "SNOWBALL": 27,
    "HALO": 28,
    "SATELLITE_HALO": 29,
}

# Pixels the IRSA Spectrophotometry Tool ignores in its Tractor fit (help page, 2026-09-22).
IRSA_TOOL_EXCLUDE = (
    "SUR_ERROR",
    "NONFUNC",
    "MISSING_DATA",
    "HOT",
    "COLD",
    "NONLINEAR",
    "PERSIST",
    "BLOOM",
    "SNOWBALL",
    "HALO",
    "SATELLITE_HALO",
)

# The demo policy (docs/sed_demo_task.md section 5): the tool's set plus TRANSIENT, OVERFLOW, DICHROIC.
DEMO_EXCLUDE = IRSA_TOOL_EXCLUDE + ("TRANSIENT", "OVERFLOW", "DICHROIC")

# Everything the Mosaic Tool and the all-sky cubes drop (Supplement v2.1 sections 2.5 and 3.4.3).
MOSAIC_EXCLUDE = IRSA_TOOL_EXCLUDE + (
    "TRANSIENT",
    "DICHROIC",
    "PHANMISS",
    "CROSSTALK",
    "GHOST",
    "GHOST_FPA",
    "GHOST_EXT",
    "STREAK",
)


def bitmask_for(names: tuple[str, ...] | list[str]) -> int:
    mask = 0
    for name in names:
        mask |= 1 << FLAG_BITS[name]
    return mask


def flagged(flags: np.ndarray, names: tuple[str, ...] | list[str] = DEMO_EXCLUDE) -> np.ndarray:
    """Boolean array, True where any of the named flags is set."""
    return (np.asarray(flags).astype(np.int64) & bitmask_for(names)) != 0


def decode(value: int) -> list[str]:
    value = int(value)
    return [name for name, bit in FLAG_BITS.items() if value & (1 << bit)]
