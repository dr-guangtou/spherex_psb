"""Detector-boundary test: flux ratio between the two detectors that both observe a boundary wavelength.

The detector overlaps (from the ePSF CWAVE ranges; docs/sed_demo_task.md section 7) are narrow, so instead
of requiring exposures inside the overlap, the exposures of each detector within a window around the
boundary are fitted with a straight line in wavelength (weighted by their errors) and the two lines are
evaluated at the boundary wavelength. The ratio B/A and its error come from the line intercepts.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BOUNDARIES_UM = {
    "D1/D2": (1, 2, 1.1055),
    "D2/D3": (2, 3, 1.6375),
    "D3/D4": (3, 4, 2.4215),
    "D4/D5": (4, 5, 3.814),
    "D5/D6": (5, 6, 4.414),
}
WINDOW_UM = {"D1/D2": 0.12, "D2/D3": 0.15, "D3/D4": 0.20, "D4/D5": 0.12, "D5/D6": 0.10}


def _line_at(
    wavelength: np.ndarray, flux: np.ndarray, err: np.ndarray, x0: float
) -> tuple[float, float, int]:
    """Weighted straight-line fit flux = a + b (lambda - x0); returns (a, sigma_a, n)."""
    good = np.isfinite(flux) & np.isfinite(err) & (err > 0)
    wavelength, flux, err = wavelength[good], flux[good], err[good]
    n = len(flux)
    if n == 0:
        return np.nan, np.nan, 0
    if n == 1:
        return float(flux[0]), float(err[0]), 1
    x = wavelength - x0
    w = 1.0 / err**2
    if n == 2 or np.ptp(x) < 1e-4:
        a = np.sum(w * flux) / np.sum(w)
        return float(a), float(1 / np.sqrt(np.sum(w))), n
    design = np.stack([np.ones(n), x], axis=1)
    normal = design.T @ (design * w[:, None])
    covariance = np.linalg.inv(normal)
    coefficients = covariance @ (design.T @ (flux * w))
    return float(coefficients[0]), float(np.sqrt(covariance[0, 0])), n


def boundary_ratios(records: pd.DataFrame, flux_column: str) -> pd.DataFrame:
    """One row per boundary: ratio of the detector-B to detector-A flux at the boundary wavelength."""
    err_column = flux_column.replace("_ujy", "_err_ujy")
    usable = records[records.screen_reason == ""]
    rows = []
    for name, (det_a, det_b, wavelength) in BOUNDARIES_UM.items():
        window = WINDOW_UM[name]
        a_rows = usable[
            (usable.detector == det_a)
            & (usable.cwave_um >= wavelength - window)
            & (usable.cwave_um <= wavelength + 0.03)
        ]
        b_rows = usable[
            (usable.detector == det_b)
            & (usable.cwave_um >= wavelength - 0.03)
            & (usable.cwave_um <= wavelength + window)
        ]
        fa, ea, na = _line_at(
            a_rows.cwave_um.to_numpy(),
            a_rows[flux_column].to_numpy(),
            a_rows[err_column].to_numpy(),
            wavelength,
        )
        fb, eb, nb = _line_at(
            b_rows.cwave_um.to_numpy(),
            b_rows[flux_column].to_numpy(),
            b_rows[err_column].to_numpy(),
            wavelength,
        )
        ratio = fb / fa if (na and nb and fa > 0) else np.nan
        ratio_err = ratio * np.hypot(ea / fa, eb / fb) if np.isfinite(ratio) else np.nan
        rows.append(
            {
                "boundary": name,
                "wavelength_um": wavelength,
                "flux_column": flux_column,
                "n_a": na,
                "n_b": nb,
                "flux_a_ujy": fa,
                "flux_b_ujy": fb,
                "ratio_b_over_a": ratio,
                "ratio_err": ratio_err,
                "ratio_mag": -2.5 * np.log10(ratio) if np.isfinite(ratio) and ratio > 0 else np.nan,
            }
        )
    return pd.DataFrame(rows)


def estimator_consistency(records: pd.DataFrame, aperture_key: str = "2px") -> dict:
    """Slope and scatter of model / aperture flux against wavelength (per galaxy)."""
    usable = records[records.screen_reason == ""]
    ratio = (usable.flux_model_ujy / usable[f"flux_aperture_{aperture_key}_ujy"]).to_numpy()
    wavelength = usable.cwave_um.to_numpy()
    good = np.isfinite(ratio)
    if good.sum() < 3:
        return {"n": int(good.sum())}
    slope, intercept = np.polyfit(wavelength[good], ratio[good], 1)
    residual = ratio[good] - (intercept + slope * wavelength[good])
    return {
        "n": int(good.sum()),
        "median_ratio": float(np.median(ratio[good])),
        "slope_per_um": float(slope),
        "change_over_band_mag": float(
            -2.5 * np.log10((intercept + slope * 5.0) / (intercept + slope * 0.75))
        ),
        "scatter_mad": float(1.4826 * np.median(np.abs(residual - np.median(residual)))),
    }
