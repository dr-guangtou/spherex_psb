"""Assemble per-exposure measurements into an SED: exposure screening, Galactic extinction, binning onto the
102 nominal channels, rest-frame wavelengths.

Combination within a channel: inverse-variance weighted mean with two error estimates, the propagated formal
error and the scatter between exposures (standard error of the mean from the unbiased weighted variance), plus
a median with its MAD-based error. No pixel-level clipping anywhere; exposures are only excluded by explicit
reason codes recorded in the records.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
import requests

from spherex_psb.spectra.channels import channel_table

IRSA_DUST = "https://irsa.ipac.caltech.edu/cgi-bin/DUST/nph-dust"
CHI2_OUTLIER_FACTOR = 5.0
CHI2_ALL_OUTLIER_FACTOR = (
    10.0  # exposures whose chi2/dof exceeds this times the per-detector median are rejected
)
NEIGHBOUR_OUTLIER_SIGMA = 5.0  # exposures off the local running median by this many sigma are rejected


def galactic_ebv(ra: float, dec: float) -> dict:
    """E(B-V) from the IRSA dust service: Schlafly & Finkbeiner (2011) and SFD (1998) mean values (mag)."""
    response = requests.get(IRSA_DUST, params={"locstr": f"{ra} {dec} equ j2000"}, timeout=120)
    response.raise_for_status()
    values = {}
    for tag, key in (("meanValueSandF", "ebv_sandf"), ("meanValueSFD", "ebv_sfd")):
        match = re.search(rf"<{tag}>\s*([0-9.]+)\s*\(mag\)", response.text)
        if match:
            values[key] = float(match.group(1))
    if "ebv_sandf" not in values:
        raise RuntimeError("could not parse E(B-V) from the IRSA dust service response")
    return values


def extinction_correction(wavelength_um: np.ndarray, ebv: float, r_v: float = 3.1) -> np.ndarray:
    """Multiplicative flux correction 10^(0.4 A_lambda), Gordon et al. (2023) Milky Way curve (0.09-32 um)."""
    import astropy.units as u
    from dust_extinction.parameter_averages import G23

    curve = G23(Rv=r_v)
    a_lambda = curve(np.asarray(wavelength_um) * u.micron) * r_v * ebv
    return 10 ** (0.4 * a_lambda)


def screen_exposures(records: pd.DataFrame, flux_column: str = "flux_model_ujy") -> pd.DataFrame:
    """Add reason codes for exposures the fit accepted but the SED should not use."""
    table = records.copy()
    reason = table.reject_reason.fillna("").astype(str)
    measured = reason == ""
    for _detector, group in table[measured].groupby("detector"):
        median_chi2 = np.nanmedian(group.chi2_dof_near)
        bad = group.index[group.chi2_dof_near > CHI2_OUTLIER_FACTOR * median_chi2]
        reason.loc[bad] = "chi2_outlier"
    measured = reason == ""
    for _detector, group in table[measured].groupby("detector"):
        median_chi2_all = np.nanmedian(group.chi2_dof_all)
        bad = group.index[group.chi2_dof_all > CHI2_ALL_OUTLIER_FACTOR * median_chi2_all]
        reason.loc[bad] = "cutout_chi2_outlier"  # an artefact elsewhere in the cutout corrupts the joint fit
    measured = reason == ""
    # outlier against nearby wavelengths: running median over the 7 nearest exposures in wavelength
    sub = table[measured].sort_values("cwave_um")
    flux = sub[flux_column].to_numpy()
    err = sub[flux_column.replace("_ujy", "_err_ujy")].to_numpy()
    for k, index in enumerate(sub.index):
        lo, hi = max(0, k - 3), min(len(sub), k + 4)
        window = np.delete(flux[lo:hi], k - lo)
        if len(window) < 3:
            continue
        local_median = np.median(window)
        local_scatter = 1.4826 * np.median(np.abs(window - local_median))
        sigma = max(local_scatter, err[k])
        if (
            abs(flux[k] - local_median) > NEIGHBOUR_OUTLIER_SIGMA * sigma
            and abs(flux[k] / local_median - 1) > 0.3
        ):
            reason.loc[index] = "wavelength_outlier"
    table["screen_reason"] = reason
    return table


def bin_to_channels(records: pd.DataFrame, flux_column: str, release: str = "dr1") -> pd.DataFrame:
    channels = channel_table(release)
    usable = records[records.screen_reason == ""]
    err_column = flux_column.replace("_ujy", "_err_ujy")
    rows = []
    # adjacent nominal channels overlap by up to 0.018 um: assign each exposure to the nearest channel centre
    # of its detector, so that no exposure enters two channels
    assigned = {}
    for detector, group in usable.groupby("detector"):
        centres = channels[channels.detector == detector]
        nearest = np.abs(group.cwave_um.to_numpy()[:, None] - centres.wavelength.to_numpy()[None, :]).argmin(
            axis=1
        )
        for index, k in zip(group.index, nearest, strict=True):
            assigned[index] = int(centres.global_channel.iloc[k])
    usable = usable.assign(global_channel=pd.Series(assigned))
    for channel in channels.itertuples():
        in_channel = usable[usable.global_channel == channel.global_channel]
        row = {
            "global_channel": int(channel.global_channel),
            "detector": int(channel.detector),
            "channel": int(channel.channel),
            "wavelength_um": float(channel.wavelength),
            "wl_min_um": float(channel.wl_min),
            "wl_max_um": float(channel.wl_max),
            "bandwidth_um": float(channel.bandwidth),
            "n_exposures": len(in_channel),
        }
        if len(in_channel):
            flux = in_channel[flux_column].to_numpy(dtype=float)
            err = in_channel[err_column].to_numpy(dtype=float)
            weight = 1.0 / np.maximum(err, 1e-30) ** 2
            mean = np.sum(weight * flux) / np.sum(weight)
            row["flux_ujy"] = mean
            row["flux_err_formal_ujy"] = 1.0 / np.sqrt(np.sum(weight))
            if len(in_channel) > 1:
                scatter = np.sqrt(
                    np.sum(weight * (flux - mean) ** 2) / np.sum(weight) * len(flux) / (len(flux) - 1)
                )
                row["flux_err_scatter_ujy"] = scatter / np.sqrt(len(flux))
                row["exposure_scatter_ujy"] = scatter
            else:
                row["flux_err_scatter_ujy"] = np.nan
                row["exposure_scatter_ujy"] = np.nan
            row["flux_median_ujy"] = float(np.median(flux))
            row["flux_err_mad_ujy"] = (
                float(1.4826 * np.median(np.abs(flux - np.median(flux))) / np.sqrt(len(flux)))
                if len(flux) > 1
                else np.nan
            )
            row["mean_cwave_um"] = float(np.mean(in_channel.cwave_um))
        rows.append(row)
    return pd.DataFrame(rows)


def add_rest_frame(
    table: pd.DataFrame, redshift: float, wavelength_column: str = "wavelength_um"
) -> pd.DataFrame:
    table = table.copy()
    table["rest_wavelength_um"] = table[wavelength_column] / (1 + redshift)
    return table
