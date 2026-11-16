"""The 1.6 um H-minus bump index (Hbump_opt of the H-bump paper) for every galaxy of the SDSS 48k run.

Input: the run's 12.3 arcsec aperture fluxes (`aper_flux_uJy`), which repeat to 3-5 % per exposure in D1-D4
(review section 6); the PSF-fit flux is not used. Only the SED shape enters the index. The run converted
surface brightness to flux with a constant 6.15 x 6.15 arcsec pixel; each flux is rescaled here by the
Solid Angle Pixel Map at the galaxy's detector position (SAPM / 37.8225 arcsec^2; full-detector maps from the
spherex-retrieval cache, checked against the per-exposure solid angles of the SED demo). The index is also
kept without this correction (`hminus_bump_uncorrected_mag`).

Per galaxy (one row per repeat group):
1. Exposures with rest wavelength 1.44-1.84 um (rest = observed / (1 + z)); F_lambda = F_nu / lambda^2.
2. Outlier screen: quadratic in rest wavelength fitted to F_lambda / median; exposures more than 5 robust
   sigma off (sigma floor 1 %) rejected, three iterations. This removes the bad-pixel aperture outliers
   without touching a 5-8 % bump.
3. Index as in the demo feasibility study (`scripts/sed_demo/hminus_bump_feasibility.py`): band means of
   F_lambda in the blue (1.494-1.539 um) and red (1.746-1.791 um) windows, straight-line pseudo-continuum
   through the window midpoints, I = -2.5 log10 mean(F_lambda / F_c) over the feature exposures (1.570-1.734
   um). Requires >= 2 exposures in each side window and >= 5 in the feature window.
4. Error: per-exposure fractional scatter s = robust sigma of the step-2 residuals, propagated to the index
   analytically (feature mean plus the two continuum means with their interpolation weights); checked
   against a bootstrap over exposures for a random subset.
5. D2/D3 diagnostic: both detectors cover observed 1.616-1.668 um; the median step-2 residual of D3 minus
   that of D2 there measures the detector-to-detector step of this galaxy's aperture flux.

The MPA-JHU optical indices are joined by specobjid from `galSpecIndx-dr8.fits`: Dn4000 and HdeltaA
(emission-subtracted, as in the input catalogue) and the broad Bruzual D4000 (`D4000_SUB`) that the H-bump
paper's models use, with their errors. No Galactic extinction correction: across 1.49-1.79 um it is close to
linear in wavelength, which the pseudo-continuum absorbs.

usage: uv run python scripts/sdss48k_review/measure_hminus_bump.py [--bootstrap-galaxies 500]
Output: <results>/sdss48k_hminus/hminus_bump_indices.parquet, bootstrap_check.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from astropy.io import fits

from spherex_psb import RESULTS_ROOT

RUN_DIR = "/Users/shuang/data/spherex/spherex_sdss48k_phot"
MPA_INDEX_FILE = "/Users/shuang/data/mpa/galSpecIndx-dr8.fits"
SAPM_CACHE = Path("/Users/shuang/data/spherex/calibration/spherex_retrieval_cache")
CONSTANT_PIXEL_ARCSEC2 = 6.15**2
OUT_DIR = RESULTS_ROOT / "sdss48k_hminus"
WINDOWS_UM = {"blue": (1.494, 1.539), "feature": (1.570, 1.734), "red": (1.746, 1.791)}  # rest, vacuum
FIT_RANGE_UM = (1.44, 1.84)
OVERLAP_OBSERVED_UM = (1.616, 1.668)
REJECT_SIGMA = 5.0
SIGMA_FLOOR = 0.01
MIN_SIDE, MIN_FEATURE = 2, 5
MAGNITUDE = 2.5 / np.log(10)
BLUE_MID, RED_MID = (0.5 * sum(WINDOWS_UM[key]) for key in ("blue", "red"))


def robust_sigma(values: np.ndarray) -> float:
    return float(1.4826 * np.median(np.abs(values - np.median(values))))


def screen(rest_um: np.ndarray, flux_lambda: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Iterative quadratic fit; returns the kept mask, the fractional residuals and their robust sigma."""
    keep = np.isfinite(flux_lambda) & (flux_lambda > 0)
    normalised = flux_lambda / np.median(flux_lambda[keep])
    x = rest_um - 1.64
    residual = np.zeros_like(normalised)
    sigma = np.nan
    for _ in range(3):
        if keep.sum() < 6:
            return keep, residual, np.nan
        coefficients = np.polyfit(x[keep], normalised[keep], 2)
        model = np.polyval(coefficients, x)
        residual = normalised / model - 1
        sigma = max(robust_sigma(residual[keep]), SIGMA_FLOOR)
        new_keep = keep & (np.abs(residual) < REJECT_SIGMA * sigma)
        if np.array_equal(new_keep, keep):
            break
        keep = new_keep
    return keep, residual, robust_sigma(residual[keep])


def index_and_error(
    rest_um: np.ndarray,
    flux_lambda: np.ndarray,
    scatter: float,
    min_side: int = MIN_SIDE,
    min_feature: int = MIN_FEATURE,
) -> dict:
    members = {key: (rest_um >= lo) & (rest_um <= hi) for key, (lo, hi) in WINDOWS_UM.items()}
    counts = {f"n_{key}": int(mask.sum()) for key, mask in members.items()}
    if counts["n_blue"] < min_side or counts["n_red"] < min_side or counts["n_feature"] < min_feature:
        return counts | {"hminus_bump_mag": np.nan, "hminus_bump_err_mag": np.nan}
    blue = flux_lambda[members["blue"]].mean()
    red = flux_lambda[members["red"]].mean()
    fraction = (rest_um[members["feature"]] - BLUE_MID) / (RED_MID - BLUE_MID)
    continuum = blue * (1 - fraction) + red * fraction
    index = -MAGNITUDE * np.log(np.mean(flux_lambda[members["feature"]] / continuum))
    weight_blue = np.mean(
        blue * (1 - fraction) / continuum
    )  # d ln F_c / d ln blue, averaged over the feature
    weight_red = np.mean(red * fraction / continuum)
    variance = scatter**2 * (
        1 / counts["n_feature"] + weight_blue**2 / counts["n_blue"] + weight_red**2 / counts["n_red"]
    )
    return counts | {
        "hminus_bump_mag": float(index),
        "hminus_bump_err_mag": float(MAGNITUDE * np.sqrt(variance)),
    }


def bootstrap_error(rest_um: np.ndarray, flux_lambda: np.ndarray, rng, n_draws: int = 300) -> float:
    members = {key: np.flatnonzero((rest_um >= lo) & (rest_um <= hi)) for key, (lo, hi) in WINDOWS_UM.items()}
    values = np.empty(n_draws)
    for k in range(n_draws):
        picks = np.concatenate([rng.choice(idx, size=len(idx), replace=True) for idx in members.values()])
        values[k] = index_and_error(rest_um[picks], flux_lambda[picks], 0.0)["hminus_bump_mag"]
    return float(np.std(values, ddof=1))


def load_solid_angle_maps() -> dict[int, np.ndarray]:
    """The six full-detector Solid Angle Pixel Maps (arcsec^2) in the spherex-retrieval cache."""
    maps = {}
    for path in SAPM_CACHE.glob("*.fits"):
        with fits.open(path) as hdul:
            if (
                len(hdul) == 2
                and hdul[1].header.get("BUNIT") == "arcsec2"
                and hdul[1].data.shape == (2040, 2040)
            ):
                maps[int(hdul[1].header["DETECTOR"])] = hdul[1].data.astype(np.float64)
    assert sorted(maps) == [1, 2, 3, 4, 5, 6], sorted(maps)
    return maps


def load_mpa_indices(specobjids: pd.Series) -> pd.DataFrame:
    columns = [
        "SPECOBJID",
        "D4000_N_SUB",
        "D4000_N_SUB_ERR",
        "D4000_SUB",
        "D4000_SUB_ERR",
        "LICK_HD_A_SUB",
        "LICK_HD_A_SUB_ERR",
    ]
    with fits.open(MPA_INDEX_FILE, memmap=True) as hdul:
        data = hdul[1].data
        table = pd.DataFrame(
            {name: np.asarray(data[name]).astype(data[name].dtype.newbyteorder("=")) for name in columns}
        )
    table["specobjid"] = pd.to_numeric(pd.Series(table.SPECOBJID).astype(str).str.strip(), errors="coerce")
    table = table.dropna(subset=["specobjid"]).astype({"specobjid": np.int64})
    table = table[table.specobjid.isin(set(specobjids))].drop_duplicates("specobjid")
    return table.drop(columns="SPECOBJID").rename(columns=str.lower)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap-galaxies", type=int, default=500)
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    targets = pd.read_parquet(f"{RUN_DIR}/targets.parquet")
    first_of_group = ~targets.duplicated("repeat_group") | (targets.repeat_group < 0)
    targets = targets[first_of_group]
    print(f"galaxies after removing repeat spectra: {len(targets):,}")

    low = FIT_RANGE_UM[0] * (1 + targets.redshift.min())
    high = FIT_RANGE_UM[1] * (1 + targets.redshift.max())
    columns = ["target", "detector_id", "wv_um", "aper_flux_uJy", "xpix_fulldet", "ypix_fulldet"]
    dataset = ds.dataset(f"{RUN_DIR}/photometry.parquet")
    rows = dataset.to_table(columns=columns, filter=(ds.field("wv_um") >= low) & (ds.field("wv_um") <= high))
    rows = rows.to_pandas().merge(targets[["target", "redshift"]], on="target", how="inner")
    rows["rest_um"] = rows.wv_um / (1 + rows.redshift)
    rows = rows[(rows.rest_um >= FIT_RANGE_UM[0]) & (rows.rest_um <= FIT_RANGE_UM[1])]
    maps = load_solid_angle_maps()
    column = np.clip(np.round(rows.xpix_fulldet.to_numpy()).astype(int), 0, 2039)
    row = np.clip(np.round(rows.ypix_fulldet.to_numpy()).astype(int), 0, 2039)
    solid_angle = np.empty(len(rows))
    for detector, sapm in maps.items():
        on = rows.detector_id.to_numpy() == detector
        solid_angle[on] = sapm[row[on], column[on]]
    rows["solid_angle_factor"] = solid_angle / CONSTANT_PIXEL_ARCSEC2
    rows["flux_lambda_uncorrected"] = rows.aper_flux_uJy / rows.rest_um**2
    rows["flux_lambda"] = rows.flux_lambda_uncorrected * rows.solid_angle_factor
    factors = rows.groupby("detector_id").solid_angle_factor.median().round(4).to_dict()
    print("solid-angle factor by detector (median):", factors)
    rows = rows.sort_values(["target", "rest_um"])
    print(f"exposures in {FIT_RANGE_UM} um rest: {len(rows):,}")

    rng = np.random.default_rng(0)
    bootstrap_targets = set(rng.choice(targets.target.to_numpy(), args.bootstrap_galaxies, replace=False))
    results, checks = [], []
    target_ids = rows.target.to_numpy()
    starts = np.flatnonzero(np.r_[True, target_ids[1:] != target_ids[:-1]])
    stops = np.r_[starts[1:], len(target_ids)]
    rest_all, flux_all = rows.rest_um.to_numpy(), rows.flux_lambda.to_numpy()
    flux_uncorrected_all = rows.flux_lambda_uncorrected.to_numpy()
    wave_all, detector_all = rows.wv_um.to_numpy(), rows.detector_id.to_numpy()
    for start, stop in zip(starts, stops, strict=True):
        target = int(target_ids[start])
        rest, flux = rest_all[start:stop], flux_all[start:stop]
        keep, residual, scatter = screen(rest, flux)
        record = {
            "target": target,
            "n_fit": int(stop - start),
            "n_rejected": int((~keep).sum()),
            "exposure_scatter": scatter,
        }
        record |= index_and_error(rest[keep], flux[keep], scatter)
        uncorrected = flux_uncorrected_all[start:stop]
        record["hminus_bump_uncorrected_mag"] = index_and_error(rest[keep], uncorrected[keep], scatter)[
            "hminus_bump_mag"
        ]
        _, residual_uncorrected, _ = screen(rest, uncorrected)
        overlap = (
            keep
            & (wave_all[start:stop] >= OVERLAP_OBSERVED_UM[0])
            & (wave_all[start:stop] <= OVERLAP_OBSERVED_UM[1])
        )
        in_d2, in_d3 = overlap & (detector_all[start:stop] == 2), overlap & (detector_all[start:stop] == 3)
        record["n_overlap_d2"], record["n_overlap_d3"] = int(in_d2.sum()), int(in_d3.sum())
        both = in_d2.any() and in_d3.any()
        record["d3_minus_d2_step"] = (
            float(np.median(residual[in_d3]) - np.median(residual[in_d2])) if both else np.nan
        )
        record["d3_minus_d2_step_uncorrected"] = (
            float(np.median(residual_uncorrected[in_d3]) - np.median(residual_uncorrected[in_d2]))
            if both
            else np.nan
        )
        results.append(record)
        if target in bootstrap_targets and np.isfinite(record["hminus_bump_mag"]):
            checks.append(
                {
                    "target": target,
                    "analytic_err_mag": record["hminus_bump_err_mag"],
                    "bootstrap_err_mag": bootstrap_error(rest[keep], flux[keep], rng),
                }
            )

    results = pd.DataFrame(results)
    results = targets.merge(results, on="target", how="left")
    mpa = load_mpa_indices(results.specobjid)
    results = results.merge(mpa, on="specobjid", how="left")
    print(
        "MPA-JHU rows joined:",
        int(results.d4000_n_sub.notna().sum()),
        "| Dn4000 equal to the input catalogue:",
        bool(np.allclose(results.d4000_n_sub, results.dn4000_emission_subtracted, equal_nan=True)),
        "| HdeltaA equal:",
        bool(
            np.allclose(results.lick_hd_a_sub, results.h_delta_a_emission_subtracted_angstrom, equal_nan=True)
        ),
    )
    results.to_parquet(OUT_DIR / "hminus_bump_indices.parquet")
    checks = pd.DataFrame(checks)
    checks.to_parquet(OUT_DIR / "bootstrap_check.parquet")

    measured = results[np.isfinite(results.hminus_bump_mag)]
    print(f"\nmeasured: {len(measured):,} of {len(results):,}")
    for key in [
        "n_blue",
        "n_feature",
        "n_red",
        "n_rejected",
        "exposure_scatter",
        "hminus_bump_mag",
        "hminus_bump_err_mag",
        "hminus_bump_uncorrected_mag",
        "d3_minus_d2_step",
        "d3_minus_d2_step_uncorrected",
    ]:
        values = measured[key].dropna()
        print(
            f"{key:22s} p5/16/50/84/95",
            np.round(np.percentile(values, [5, 16, 50, 84, 95]), 4),
            f"(n={len(values):,})",
        )
    shift = measured.hminus_bump_mag - measured.hminus_bump_uncorrected_mag
    print(
        "index change from the solid-angle correction p5/16/50/84/95",
        np.round(np.percentile(shift, [5, 16, 50, 84, 95]), 4),
    )
    unmeasured = results[~np.isfinite(results.hminus_bump_mag)]
    print(
        "not measured, by the window that fell short: blue",
        int((unmeasured.n_blue < MIN_SIDE).sum()),
        "| red",
        int((unmeasured.n_red < MIN_SIDE).sum()),
        "| feature",
        int((unmeasured.n_feature < MIN_FEATURE).sum()),
    )
    ratio = checks.bootstrap_err_mag / checks.analytic_err_mag
    print(
        f"\nbootstrap / analytic error ({len(checks)} galaxies): p16/50/84",
        np.round(np.percentile(ratio, [16, 50, 84]), 3),
    )


if __name__ == "__main__":
    main()
