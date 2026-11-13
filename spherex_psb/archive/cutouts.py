"""Retrieve per-exposure cutout bundles with spherex-retrieval (MIT) into the project data tree.

Each bundle carries IMAGE/FLAGS/VARIANCE/ZODI cropped to the request, the ePSF planes of the overlapping
zones, CWAVE/CBAND from the Spectral WCS product and the SAPM. Retrieval is incremental: frames whose bundle
already exists are skipped. Concurrency stays low because the IRSA cutout service answers 503 under load.
"""

from __future__ import annotations

import time
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.table import Table

from spherex_psb import CALIBRATION_ROOT, CUTOUT_ROOT

RETRIEVAL_CACHE = CALIBRATION_ROOT / "spherex_retrieval_cache"


def bundle_filename(obs_id: str, detector: int) -> str:
    return f"cutout_{obs_id}_D{detector}.fits"


def retrieve_frames(
    frames: Table,
    ra: float,
    dec: float,
    size_deg: float,
    galaxy_name: str,
    max_workers: int = 2,
    attempts: int = 3,
) -> tuple[Path, dict]:
    """Download the bundles of ``frames`` into CUTOUT_ROOT/<galaxy_name>.

    Returns the output directory and a report dictionary.
    """
    from spherex_retrieval.core import retrieve

    out_dir = CUTOUT_ROOT / galaxy_name
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = {p.name for p in out_dir.glob("cutout_*.fits")}
    wanted = [bundle_filename(o, int(d)) for o, d in zip(frames["obs_id"], frames["detector"], strict=True)]
    todo = frames[[name not in existing for name in wanted]]
    report = {
        "requested": len(frames),
        "already_present": len(frames) - len(todo),
        "retrieved": 0,
        "failed": 0,
        "seconds": 0.0,
        "bytes": 0,
    }
    if len(todo) == 0:
        return out_dir, report
    coord = SkyCoord(ra, dec, unit="deg")
    start = time.time()
    remaining = todo
    for attempt in range(attempts):
        bundles, _ = retrieve(
            coord,
            size_deg * u.deg,
            query_backend=lambda c, s, bandpass=None, table=remaining: table,
            collections=tuple(sorted(set(np.asarray(frames["collection"]).astype(str)))),
            include_sapm=True,
            output_dir=out_dir,
            cache_dir=RETRIEVAL_CACHE,
            max_workers=max_workers,
        )
        _rename_bundles(out_dir)
        present = {p.name for p in out_dir.glob("cutout_*.fits")}
        still = [
            bundle_filename(o, int(d)) not in present
            for o, d in zip(remaining["obs_id"], remaining["detector"], strict=True)
        ]
        remaining = remaining[still]
        if len(remaining) == 0:
            break
        time.sleep(20 * (attempt + 1))
    report["retrieved"] = len(todo) - len(remaining)
    report["failed"] = len(remaining)
    report["seconds"] = round(time.time() - start, 1)
    report["bytes"] = int(sum(p.stat().st_size for p in out_dir.glob("cutout_*.fits")))
    return out_dir, report


def _rename_bundles(out_dir: Path) -> None:
    """spherex-retrieval names files cutout_<index>_<obsid>_D<n>.fits; use a stable name without the index."""
    for path in out_dir.glob("cutout_*.fits"):
        parts = path.stem.split("_")
        if len(parts) >= 6 and parts[1].isdigit() and len(parts[1]) == 4:
            target = out_dir / ("cutout_" + "_".join(parts[2:]) + ".fits")
            if not target.exists():
                path.rename(target)
            else:
                path.unlink()
