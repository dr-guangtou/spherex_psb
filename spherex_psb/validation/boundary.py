"""Detector-boundary test: flux ratio between the two detectors that both observe a boundary wavelength.

The detector overlaps (from the ePSF CWAVE ranges; docs/sed_demo_task.md section 7) are narrow and their
pixels are mostly DICHROIC-flagged at D3/D4, so instead of requiring exposures inside the overlap, the
exposures of both detectors within a window around the boundary are fitted jointly with a quadratic in
wavelength (in log flux, so that the local curvature of the SED is absorbed) plus a constant step for
detector B. The step is the logarithm of the B/A flux ratio.
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


def _step_fit(wavelength, flux, err, is_b, x0: float) -> tuple[float, float, int, int]:
    """Joint weighted fit of ln(flux) = p0 + p1 x + p2 x^2 + s [detector B], x = lambda - x0.

    Returns (s, sigma_s, n_a, n_b). The quadratic absorbs the local curvature of the SED; the step s is the
    logarithm of the detector ratio at every wavelength of the window.
    """
    good = np.isfinite(flux) & np.isfinite(err) & (err > 0) & (flux > 0)
    wavelength, flux, err, is_b = wavelength[good], flux[good], err[good], is_b[good]
    n_a, n_b = int((~is_b).sum()), int(is_b.sum())
    if n_a == 0 or n_b == 0 or len(flux) < 5:
        return np.nan, np.nan, n_a, n_b
    x = wavelength - x0
    y = np.log(flux)
    w = (flux / err) ** 2
    columns = [np.ones(len(x)), x, is_b.astype(float)]
    if len(flux) >= 6 and np.ptp(x) > 0.02:
        columns.insert(2, x**2)
    design = np.stack(columns, axis=1)
    normal = design.T @ (design * w[:, None])
    covariance = np.linalg.pinv(normal)
    coefficients = covariance @ (design.T @ (y * w))
    k = design.shape[1] - 1
    return float(coefficients[k]), float(np.sqrt(max(covariance[k, k], 0))), n_a, n_b


def boundary_ratios(records: pd.DataFrame, flux_column: str) -> pd.DataFrame:
    """One row per boundary: ratio of the detector-B to detector-A flux across the boundary."""
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
        both = pd.concat([a_rows, b_rows])
        is_b = np.concatenate([np.zeros(len(a_rows), bool), np.ones(len(b_rows), bool)])
        step, step_err, na, nb = _step_fit(
            both.cwave_um.to_numpy(),
            both[flux_column].to_numpy(),
            both[err_column].to_numpy(),
            is_b,
            wavelength,
        )
        ratio = float(np.exp(step)) if np.isfinite(step) else np.nan
        rows.append(
            {
                "boundary": name,
                "wavelength_um": wavelength,
                "flux_column": flux_column,
                "n_a": na,
                "n_b": nb,
                "ratio_b_over_a": ratio,
                "ratio_err": ratio * step_err if np.isfinite(ratio) else np.nan,
                "ratio_mag": -2.5 / np.log(10) * step if np.isfinite(step) else np.nan,
                "ratio_mag_err": 2.5 / np.log(10) * step_err if np.isfinite(step_err) else np.nan,
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
