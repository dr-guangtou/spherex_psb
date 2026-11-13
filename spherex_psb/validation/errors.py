"""Error calibration from repeat measurements: pairs of exposures of the same galaxy taken at nearly the same
wavelength (different visits of the same detector rows) should differ by their quoted errors. The pull
(f1 - f2) / sqrt(e1^2 + e2^2) has unit scatter when the errors are right; its robust standard deviation per
detector is the error scale factor. A fractional floor is estimated from the pulls of the brightest pairs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MAX_PAIR_SEPARATION_UM = 0.012  # about a quarter of a channel at 0.75 um, a tenth at 5 um


def repeat_pairs(records: pd.DataFrame, flux_column: str = "flux_model_ujy") -> pd.DataFrame:
    err_column = flux_column.replace("_ujy", "_err_ujy")
    usable = records[records.screen_reason == ""].sort_values("cwave_um")
    rows = []
    for detector, group in usable.groupby("detector"):
        wavelength = group.cwave_um.to_numpy()
        flux = group[flux_column].to_numpy()
        err = group[err_column].to_numpy()
        obs = group.obs_id.to_numpy()
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                if wavelength[j] - wavelength[i] > MAX_PAIR_SEPARATION_UM:
                    break
                if obs[i] == obs[j]:
                    continue
                sigma = np.hypot(err[i], err[j])
                mean = 0.5 * (flux[i] + flux[j])
                rows.append(
                    {
                        "detector": int(detector),
                        "wavelength_um": 0.5 * (wavelength[i] + wavelength[j]),
                        "delta_um": wavelength[j] - wavelength[i],
                        "flux_mean_ujy": mean,
                        "difference_ujy": flux[i] - flux[j],
                        "sigma_ujy": sigma,
                        "pull": (flux[i] - flux[j]) / sigma,
                        "fractional_difference": (flux[i] - flux[j]) / mean,
                        "snr": mean / (sigma / np.sqrt(2)),
                    }
                )
    return pd.DataFrame(rows)


def pull_statistics(pairs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for detector, group in pairs.groupby("detector"):
        pull = group.pull.to_numpy()
        pull = pull[np.isfinite(pull)]
        if len(pull) == 0:
            continue
        mad = 1.4826 * np.median(np.abs(pull - np.median(pull)))
        # fractional floor: the fractional scatter of pairs beyond what the formal errors explain
        frac = group.fractional_difference.to_numpy() / np.sqrt(2)
        formal_frac = (group.sigma_ujy / group.flux_mean_ujy).to_numpy() / np.sqrt(2)
        excess = np.nanmedian(frac**2) - np.nanmedian(formal_frac**2)
        rows.append(
            {
                "detector": int(detector),
                "n_pairs": len(pull),
                "pull_median": float(np.median(pull)),
                "pull_std_robust": float(mad),
                "pull_std": float(np.std(pull)),
                "error_scale_factor": float(mad),
                "fractional_floor": float(np.sqrt(excess)) if excess > 0 else 0.0,
                "median_snr": float(np.median(group.snr)),
            }
        )
    return pd.DataFrame(rows)
