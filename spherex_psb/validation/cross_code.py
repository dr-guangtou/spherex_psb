"""Cross-code check: run tractorjax-spherex (GPL-3.0, hbahk) on the same cutouts with the same catalogue.

Differences from our measurement that are kept on purpose: tractorjax-spherex solves per 15 px tile with a
3 px halo, uses its own CWAVE + photutils background, and reports fluxes in mJy. Its mask is a module
constant; DICHROIC, TRANSIENT and OVERFLOW are added to it here so that both codes exclude the same pixels.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from astropy.table import Table

from spherex_psb.extraction.fit import Source
from spherex_psb.products.flags import FLAG_BITS

EXTRA_MASK_FLAGS = ("DICHROIC", "TRANSIENT", "OVERFLOW")


def catalogue_for_tractorjax(sources: list[Source]) -> Table:
    rows = []
    for k, source in enumerate(sources):
        shape = source.shape
        e = (1 - shape.axis_ratio) / (1 + shape.axis_ratio) if not shape.is_point else 0.0
        phi = np.radians(shape.position_angle_deg)
        flux_z = 10 ** (-0.4 * (source.mag_z - 22.5)) if np.isfinite(source.mag_z) else 1.0
        rows.append(
            {
                "id": k,
                "name": source.name,
                "ra": source.ra,
                "dec": source.dec,
                "flux_z": flux_z,
                "shape_r": 0.0 if shape.is_point else shape.effective_radius_arcsec,
                "sersic": 0.0 if shape.is_point else shape.sersic_index,
                "shape_e1": e * np.cos(2 * phi),
                "shape_e2": e * np.sin(2 * phi),
            }
        )
    return Table(rows=rows)


def _extend_maskbits() -> int:
    import tractorjax_spherex.constants as constants

    extra = sum(1 << FLAG_BITS[name] for name in EXTRA_MASK_FLAGS)
    new_mask = int(constants.MASKBITS) | extra
    import importlib
    import pkgutil

    import tractorjax_spherex

    for module_info in pkgutil.walk_packages(tractorjax_spherex.__path__, "tractorjax_spherex."):
        try:
            module = importlib.import_module(module_info.name)
        except Exception:  # noqa: BLE001
            continue
        if hasattr(module, "MASKBITS"):
            module.MASKBITS = new_mask
    constants.MASKBITS = new_mask
    return new_mask


def run_tractorjax(
    bundle_paths: list[Path],
    sources: list[Source],
    target: Source,
    solver: str = "linear",
    output: Path | None = None,
) -> pd.DataFrame:
    from tractorjax_spherex import PhotometryConfig, run_photometry

    mask = _extend_maskbits()
    catalogue = catalogue_for_tractorjax(sources)
    config = (
        PhotometryConfig(solver=solver, fit_zmag_max=30.0, device="cpu", progress=False)
        if "progress" in PhotometryConfig.__dataclass_fields__
        else PhotometryConfig(solver=solver, fit_zmag_max=30.0, device="cpu")
    )
    pairs = [(k + 1, str(path)) for k, path in enumerate(bundle_paths)]
    table = run_photometry(pairs, catalogue, config, target=(target.ra, target.dec), progress=False)
    frame = table.to_pandas()
    frame["maskbits_used"] = mask
    frame["flux_ujy"] = frame.flux * 1e3
    frame["flux_err_ujy"] = frame.flux_err * 1e3
    target_id = [s.name for s in sources].index(target.name)
    frame = frame[frame.id == target_id].copy()
    if output is not None:
        frame.to_parquet(output, index=False)
    return frame


def compare_with_records(records: pd.DataFrame, tractorjax: pd.DataFrame) -> pd.DataFrame:
    left = records[records.reject_reason == ""][
        [
            "obs_id",
            "detector",
            "cwave_um",
            "flux_model_ujy",
            "flux_model_err_ujy",
            "chi2_dof_near",
            "screen_reason",
        ]
    ]
    right = tractorjax[
        ["obs_id", "detector", "central_wavelength", "flux_ujy", "flux_err_ujy"]
        + [c for c in ("fit_chi2", "mask_frac", "quality_flag") if c in tractorjax.columns]
    ]
    merged = left.merge(right, on=["obs_id", "detector"], how="inner", suffixes=("", "_tjx"))
    merged["ratio_ours_over_tjx"] = merged.flux_model_ujy / merged.flux_ujy
    merged["difference_sigma"] = (merged.flux_model_ujy - merged.flux_ujy) / np.hypot(
        merged.flux_model_err_ujy, merged.flux_err_ujy
    )
    return merged
