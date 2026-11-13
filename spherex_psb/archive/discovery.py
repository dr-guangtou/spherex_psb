"""Find the Level 2 exposures covering a position (DR1 + QR3 wide survey) with per-collection counts.

Uses spherex-retrieval's TAP backend (``spherex.plane``/``spherex.artifact``/``spherex.observation``), which
lists each L2 file once. Counts per collection are printed and stored so that silent archive changes (QR2
vanished from TAP on 2026-11-13) are visible in every run.
"""

from __future__ import annotations

import time
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.table import Table

from spherex_psb import WIDE_COLLECTIONS


def find_exposures(
    ra: float,
    dec: float,
    size_deg: float,
    collections: tuple[str, ...] = WIDE_COLLECTIONS,
    bandpass: str | None = None,
) -> Table:
    from spherex_retrieval.query import find_overlapping

    coord = SkyCoord(ra, dec, unit="deg")
    start = time.time()
    frames = find_overlapping(
        coord, size_deg * u.deg, backend="pyvo", collections=collections, bandpass=bandpass
    )
    frames.meta["query_seconds"] = round(time.time() - start, 1)
    counts = {}
    for collection in collections:
        for detector in range(1, 7):
            n = int(
                np.sum(
                    (np.asarray(frames["collection"]).astype(str) == collection)
                    & (np.asarray(frames["detector"]) == detector)
                )
            )
            counts[f"{collection}_D{detector}"] = n
    frames.meta["counts"] = counts
    key = [f"{o}_{d}" for o, d in zip(frames["obs_id"], frames["detector"], strict=True)]
    if len(set(key)) != len(key):
        raise RuntimeError("duplicate (obs_id, detector) in the discovery result")
    return frames


def describe_counts(frames: Table) -> str:
    counts = frames.meta["counts"]
    parts = []
    for collection in sorted({k.rsplit("_D", 1)[0] for k in counts}):
        per_detector = [counts[f"{collection}_D{d}"] for d in range(1, 7)]
        parts.append(f"{collection}: {sum(per_detector)} (D1-D6 {per_detector})")
    return f"{len(frames)} exposures; " + "; ".join(parts) + f"; TAP {frames.meta.get('query_seconds')} s"


def select_per_detector(frames: Table, per_detector: int | None, seed: int = 0) -> Table:
    """Keep ``per_detector`` exposures per detector spread in time (all when None)."""
    if per_detector is None:
        return frames
    keep = []
    for detector in range(1, 7):
        rows = np.where(np.asarray(frames["detector"]) == detector)[0]
        if len(rows) == 0:
            continue
        rows = rows[np.argsort(np.asarray(frames["time_bounds_lower"])[rows])]
        picks = np.unique(np.linspace(0, len(rows) - 1, min(per_detector, len(rows))).astype(int))
        keep.extend(rows[picks].tolist())
    subset = frames[sorted(keep)]
    subset.meta = dict(frames.meta)
    return subset


def save_frames(frames: Table, path: str | Path) -> None:
    frames.write(path, format="ascii.ecsv", overwrite=True)
