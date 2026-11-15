"""Are the H-bump paper's model loci comparable with the SDSS 48k measurements? Three measured checks.

1. Optical resolution. The models give D4000 and HdeltaA on a sigma = 300 km/s product; MPA-JHU measures them
   on the SDSS spectra, whose broadening is the instrument plus the galaxy's own velocity dispersion. The
   H-bump project's native C3K SSPs (ages 1-13 Gyr, four metallicities, TP-AGB off) are broadened to total
   sigma = 70-300 km/s and the broad D4000, Dn4000 and HdeltaA are measured at each; the sample's
   velocity dispersions come from galSpecInfo `V_DISP`.
2. SPHEREx sampling. The models give the bump at R = 100 on a continuous spectrum; the data index uses
   discrete exposures at R ~ 41 placed where each galaxy's redshift and the survey put them. For every galaxy
   the model spectra are integrated over its own exposures (rest centre, rest bandwidth = `wv_width_um`, a
   Gaussian of that equivalent width) and passed through the same estimator as the data
   (`measure_hminus_bump.index_and_error`); the difference from the R = 100 index is the comparability bias.
3. Star-formation histories. The models' quenching time is uniform in 1-5.9 Gyr after the onset of star
   formation (the cosmic age at z = 1 is 5.85 Gyr, Planck 2018) and every epoch of 0.05-13 Gyr is kept.
   The populations at late epochs (what a z = 0.03-0.06 galaxy can be) are compared with the sample's broad
   D4000 and MPA-JHU specific star-formation rate.

The H-bump project is read only (its `spectral_indices.py` and `broadening.py` are imported from its folder).

usage: uv run python scripts/sdss48k_review/check_model_comparability.py [--max-galaxies N]
Output: <results>/sdss48k_hminus/model_check_{optical_resolution,sampling_bias,epochs}.parquet, summary json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from astropy.cosmology import Planck18
from astropy.io import fits

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_hminus_bump import FIT_RANGE_UM, OUT_DIR, RUN_DIR, index_and_error  # noqa: E402

HBUMP_PROJECT = Path("/Users/shuang/Dropbox/work/project/luandun/stellar_pop/fsps_agb")
sys.path.insert(0, str(HBUMP_PROJECT))
import broadening  # noqa: E402
import spectral_indices  # noqa: E402

MPA_DIR = Path("/Users/shuang/data/mpa")
TOTAL_SIGMA_KM_S = (70.0, 100.0, 150.0, 200.0, 250.0, 300.0)
DN4000_BANDS_AIR_A = {"blue": (3850.0, 3950.0), "red": (4000.0, 4100.0)}  # Balogh et al. 1999
SSP_AGES_GYR = (1.0, 2.0, 3.0, 5.0, 10.0)
LATE_EPOCH_CUTS_GYR = (8.0, 10.0, 12.0)


def dn4000(wave_a: np.ndarray, flux_nu: np.ndarray) -> np.ndarray:
    blue = spectral_indices._vacuum_band(*DN4000_BANDS_AIR_A["blue"])
    red = spectral_indices._vacuum_band(*DN4000_BANDS_AIR_A["red"])
    return spectral_indices.band_mean(wave_a, flux_nu, *red) / spectral_indices.band_mean(
        wave_a, flux_nu, *blue
    )


def optical_resolution_check() -> pd.DataFrame:
    grid = np.load(HBUMP_PROJECT / "output/ssp_grid/native.npz")
    wave, flux = grid["wave_a"], grid["flux_nu"][:, 0]  # TP-AGB off; (log_z, age, pixel)
    age_gyr = 10 ** grid["log_age_yr"] / 1e9
    ages = (age_gyr >= 1.0) & (age_gyr <= 13.0)
    optical = (wave > 3500) & (wave < 4600)
    native = float(np.median(grid["native_sigma_km_s"][optical]))
    log_wave = broadening.log_wavelength_grid(3500.0, 4600.0)
    resampled = broadening.resample_flux(wave, flux[:, ages], log_wave)
    rows = []
    for sigma in TOTAL_SIGMA_KM_S:
        smoothed = broadening.gaussian_broaden(
            log_wave, resampled, broadening.added_sigma_km_s(sigma, native)
        )
        for i_z, log_z in enumerate(grid["log_z_grid"]):
            for i_age, age in enumerate(age_gyr[ages]):
                spectrum = smoothed[i_z, i_age]
                rows.append(
                    {
                        "total_sigma_km_s": sigma,
                        "log_z": float(log_z),
                        "age_gyr": float(age),
                        "d4000": float(spectral_indices.d4000(log_wave, spectrum)),
                        "dn4000": float(dn4000(log_wave, spectrum)),
                        "hdelta_a": float(spectral_indices.hdelta_a(log_wave, spectrum)),
                    }
                )
    table = pd.DataFrame(rows)
    reference = table[table.total_sigma_km_s == 300.0].set_index(["log_z", "age_gyr"])
    for name in ("d4000", "dn4000", "hdelta_a"):
        table[f"{name}_minus_sigma300"] = (
            table[name] - table.set_index(["log_z", "age_gyr"]).index.map(reference[name]).to_numpy()
        )
    print(f"native optical sigma of the C3K grid: {native:.1f} km/s")
    return table


def model_spectra() -> dict[str, tuple[np.ndarray, np.ndarray, float]]:
    """Solar SSPs at SSP_AGES_GYR, TP-AGB off (C3K, agb 0) and on (LW02, 2 x agb1 - agb0, as the paper):
    native spectrum in 1.30-1.95 um rest, and the R = 100 index the model loci use."""
    spectra = {}
    for label, folder in (("off", "ssp_grid"), ("on", "ssp_grid_lw02")):
        native = np.load(HBUMP_PROJECT / f"output/{folder}/native.npz")
        r100 = np.load(HBUMP_PROJECT / f"output/{folder}/r100.npz")
        i_z = int(np.argmin(np.abs(native["log_z_grid"] - 0.0)))
        age_gyr = 10 ** native["log_age_yr"] / 1e9
        for age in SSP_AGES_GYR:
            i_age = int(np.argmin(np.abs(age_gyr - age)))

            def pick(grid, i_age=i_age, i_z=i_z, label=label):
                flux = grid["flux_nu"][i_z, :, i_age]
                return flux[0] if label == "off" else 2.0 * flux[1] - flux[0]

            window = (native["wave_a"] > 12500) & (native["wave_a"] < 20500)
            reference = float(spectral_indices.h_minus_bump(r100["wave_a"], pick(r100)))
            spectra[f"{label}_{age:g}gyr"] = (native["wave_a"][window], pick(native)[window], reference)
    return spectra


def kernel_table(wave_a: np.ndarray, flux_nu: np.ndarray, resolving_powers: np.ndarray):
    """F_nu averaged over a Gaussian response of equivalent width lambda / R (peak-normalised), on a
    log-wavelength grid, for each R; returns the grid and an array (n_R, n_wave)."""
    log_wave = broadening.log_wavelength_grid(wave_a[0], wave_a[-1], velocity_step_km_s=50.0)
    resampled = np.interp(log_wave, wave_a, flux_nu)
    step = np.log(log_wave[1] / log_wave[0])
    table = np.empty((len(resolving_powers), len(log_wave)))
    from scipy.ndimage import gaussian_filter1d

    for k, power in enumerate(resolving_powers):
        sigma_ln = 1.0 / (power * np.sqrt(2 * np.pi))
        table[k] = gaussian_filter1d(resampled, sigma_ln / step, mode="nearest", truncate=5.0)
    return log_wave, table


def sampling_bias_check(max_galaxies: int | None) -> pd.DataFrame:
    measured = pd.read_parquet(OUT_DIR / "hminus_bump_indices.parquet")
    measured = measured[np.isfinite(measured.hminus_bump_mag)]
    if max_galaxies:
        measured = measured.sample(max_galaxies, random_state=1)
    targets = set(measured.target)
    redshift = measured.set_index("target").redshift
    low, high = FIT_RANGE_UM[0] * (1 + redshift.min()), FIT_RANGE_UM[1] * (1 + redshift.max())
    dataset = ds.dataset(f"{RUN_DIR}/photometry.parquet")
    rows = dataset.to_table(
        columns=["target", "wv_um", "wv_width_um"],
        filter=(ds.field("wv_um") >= low)
        & (ds.field("wv_um") <= high)
        & ds.field("target").isin(list(targets)),
    ).to_pandas()
    rows["redshift"] = rows.target.map(redshift)
    rows["rest_um"] = rows.wv_um / (1 + rows.redshift)
    rows = rows[(rows.rest_um >= FIT_RANGE_UM[0]) & (rows.rest_um <= FIT_RANGE_UM[1])]
    rows = rows.sort_values(["target", "rest_um"])
    power = (rows.wv_um / rows.wv_width_um).clip(25, 60).to_numpy()
    powers = np.arange(25.0, 61.0, 1.0)
    spectra = model_spectra()
    sampled, resolution_only = {}, {}
    for name, (wave_a, flux_nu, reference) in spectra.items():
        log_wave, table = kernel_table(wave_a, flux_nu, powers)
        row_41 = int(np.argmin(np.abs(powers - 41.0)))
        resolution_only[name] = float(spectral_indices.h_minus_bump(log_wave, table[row_41])) - reference
        rest_a = rows.rest_um.to_numpy() * 1e4
        lower = np.clip(np.searchsorted(powers, power) - 1, 0, len(powers) - 2)
        fraction = (power - powers[lower]) / (powers[lower + 1] - powers[lower])
        at_lower = np.array([np.interp(rest_a[j], log_wave, table[lower[j]]) for j in range(len(rest_a))])
        at_upper = np.array([np.interp(rest_a[j], log_wave, table[lower[j] + 1]) for j in range(len(rest_a))])
        sampled[name] = (at_lower * (1 - fraction) + at_upper * fraction) / rows.rest_um.to_numpy() ** 2
    target_ids = rows.target.to_numpy()
    starts = np.flatnonzero(np.r_[True, target_ids[1:] != target_ids[:-1]])
    stops = np.r_[starts[1:], len(target_ids)]
    rest_all = rows.rest_um.to_numpy()
    results = []
    for start, stop in zip(starts, stops, strict=True):
        entry = {"target": int(target_ids[start]), "redshift": float(redshift[target_ids[start]])}
        for name, (_, _, reference) in spectra.items():
            value = index_and_error(rest_all[start:stop], sampled[name][start:stop], 0.0)["hminus_bump_mag"]
            entry[f"bias_{name}"] = value - reference
        results.append(entry)
    table = pd.DataFrame(results)
    reference_values = {name: spec[2] for name, spec in spectra.items()}
    print("R = 100 model indices:", {k: round(v, 4) for k, v in reference_values.items()})
    print(
        "continuous R = 41 minus R = 100 (resolution only):",
        {k: round(v, 4) for k, v in resolution_only.items()},
    )
    return table, {
        "r100_reference_mag": reference_values,
        "resolution_only_r41_minus_r100_mag": resolution_only,
    }


def mpa_column(file_stem: str, names: list[str]) -> pd.DataFrame:
    with fits.open(MPA_DIR / f"{file_stem}-dr8.fits", memmap=True) as hdul:
        data = hdul[1].data
        table = pd.DataFrame(
            {name: np.asarray(data[name]).astype(data[name].dtype.newbyteorder("=")) for name in names}
        )
    table["specobjid"] = pd.to_numeric(pd.Series(table.SPECOBJID).astype(str).str.strip(), errors="coerce")
    return table.dropna(subset=["specobjid"]).astype({"specobjid": np.int64}).drop(columns="SPECOBJID")


def epoch_check() -> tuple[pd.DataFrame, dict]:
    measured = pd.read_parquet(OUT_DIR / "hminus_bump_indices.parquet")
    measured = measured[np.isfinite(measured.hminus_bump_mag)]
    extra = mpa_column("galSpecExtra", ["SPECOBJID", "SPECSFR_TOT_P50"]).drop_duplicates("specobjid")
    info = mpa_column("galSpecInfo", ["SPECOBJID", "V_DISP"]).drop_duplicates("specobjid")
    measured = measured.merge(extra, on="specobjid", how="left").merge(info, on="specobjid", how="left")
    data_d4000 = measured.d4000_sub.to_numpy()
    data_ssfr = measured.SPECSFR_TOT_P50.to_numpy()  # log yr^-1
    rows = []
    for label, folder in (("off", "population"), ("on", "population_lw02")):
        model = np.load(HBUMP_PROJECT / f"output/{folder}/indices.npz")
        key = "agb0" if label == "off" else "agb2"
        ssfr = np.log10(np.clip(model["ssfr_0_100_myr"], 1e-30, None)) - 9  # per Gyr -> per yr
        for cut in (1.0,) + LATE_EPOCH_CUTS_GYR:
            keep = model["epoch_gyr"] >= cut
            d4000 = model[f"d4000_{key}"][keep]
            bump = model[f"h_minus_bump_r100_{key}"][keep]
            rows.append(
                {
                    "tp_agb": label,
                    "epoch_min_gyr": cut,
                    "n_epochs": int(keep.sum()),
                    "fraction_before_quenching": float(
                        np.mean(model["epoch_gyr"][keep] < model["t_q_gyr"][keep])
                    ),
                    "d4000_p01": float(np.percentile(d4000, 1)),
                    "d4000_p50": float(np.median(d4000)),
                    "log_ssfr_p99": float(np.percentile(ssfr[keep], 99)),
                    "bump_p50": float(np.median(bump)),
                    "bump_p16": float(np.percentile(bump, 16)),
                    "bump_p84": float(np.percentile(bump, 84)),
                    "data_fraction_below_d4000_p01": float(np.mean(data_d4000 < np.percentile(d4000, 1))),
                    "data_fraction_above_log_ssfr_p99": float(
                        np.nanmean(data_ssfr > np.percentile(ssfr[keep], 99))
                    ),
                }
            )
    summary = {
        "cosmic_age_gyr": {str(z): round(float(Planck18.age(z).value), 2) for z in (0.03, 0.06, 1.0)},
        "data_d4000_sub_percentiles_5_50_95": np.nanpercentile(data_d4000, [5, 50, 95]).round(3).tolist(),
        "data_log_ssfr_percentiles_5_50_95": np.nanpercentile(data_ssfr, [5, 50, 95]).round(2).tolist(),
        "data_v_disp_percentiles_5_50_95": np.nanpercentile(measured.V_DISP, [5, 50, 95]).round(0).tolist(),
    }
    return pd.DataFrame(rows), summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-galaxies", type=int, default=None)
    parser.add_argument("--parts", default="optical,sampling,epochs")
    args = parser.parse_args()
    parts = args.parts.split(",")
    suffix = "_test" if args.max_galaxies else ""
    summary = {}
    if "optical" in parts:
        optical = optical_resolution_check()
        optical.to_parquet(OUT_DIR / f"model_check_optical_resolution{suffix}.parquet")
        grouped = optical.groupby("total_sigma_km_s")[
            ["d4000_minus_sigma300", "dn4000_minus_sigma300", "hdelta_a_minus_sigma300"]
        ]
        with pd.option_context("display.width", 250, "display.max_columns", 30):
            print(grouped.median().round(3))
            print(grouped.agg(["min", "max"]).round(3))
        summary["optical_minus_sigma300_median"] = grouped.median().round(3).to_dict()
    if "sampling" in parts:
        sampling, references = sampling_bias_check(args.max_galaxies)
        sampling.to_parquet(OUT_DIR / f"model_check_sampling_bias{suffix}.parquet")
        bias_columns = [c for c in sampling.columns if c.startswith("bias_")]
        print(sampling[bias_columns].describe(percentiles=[0.05, 0.5, 0.95]).T.round(4))
        bins = pd.cut(sampling.redshift, [0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06])
        print(sampling.groupby(bins, observed=True)[bias_columns].median().round(4))
        summary |= references
        summary["sampling_bias_percentiles_5_50_95"] = {
            c: np.percentile(sampling[c].dropna(), [5, 50, 95]).round(4).tolist() for c in bias_columns
        }
    if "epochs" in parts:
        epochs, epoch_summary = epoch_check()
        epochs.to_parquet(OUT_DIR / f"model_check_epochs{suffix}.parquet")
        with pd.option_context("display.width", 250, "display.max_columns", 30):
            print(epochs.round(3))
        print(epoch_summary)
        summary |= epoch_summary
    (OUT_DIR / f"model_check_summary{suffix}.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
