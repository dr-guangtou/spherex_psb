"""Sample-wide checks of the SDSS 48k photometry: clipping failures and the repeatability of each flux.

1. Clipping: the fraction of measurements whose PSF flux exceeds the 12.3" aperture flux by a given factor
   (an unclipped point-source fit of a galaxy cannot exceed its aperture flux by much), per detector and
   versus the number of clipped pixels.
2. Repeatability: within one galaxy, pairs of exposures on the same detector whose wavelengths differ by
   less than 0.2 of the local bandwidth see nearly the same spectrum, so (f1 - f2) / sqrt(e1^2 + e2^2)
   measures how well the formal errors describe the real scatter. Robust sigma = 1.4826 x median absolute
   deviation.
Uses a random 5,000-galaxy subset for step 2.
usage: uv run python scripts/sdss48k_review/measure_failures_and_errors.py
"""

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

RUN_DIR = "/Users/shuang/data/spherex/spherex_sdss48k_phot"
OUTPUT_DIR = "/Users/shuang/data/spherex/scratch"
N_SUBSET = 5_000
columns = [
    "target",
    "detector_id",
    "wv_um",
    "wv_width_um",
    "opt_flux_uJy",
    "opt_flux_uJy_err",
    "aper_flux_uJy",
    "aper_flux_uJy_err",
    "n_pix_outlier",
    "n_pix_used",
    "opt_chi2",
    "opt_dof",
]
photometry = ds.dataset(f"{RUN_DIR}/photometry.parquet").to_table(columns=columns).to_pandas()
photometry["psf_over_aperture"] = photometry.opt_flux_uJy / photometry.aper_flux_uJy
bright = photometry[photometry.aper_flux_uJy / photometry.aper_flux_uJy_err > 10]

print("== 1. PSF flux above the aperture flux (aperture S/N > 10) ==")
summary = bright.groupby("detector_id").psf_over_aperture.agg(
    n="size",
    above_1p0=lambda r: (r > 1.0).mean(),
    above_1p2=lambda r: (r > 1.2).mean(),
    above_1p5=lambda r: (r > 1.5).mean(),
    above_2=lambda r: (r > 2).mean(),
)
print(summary.round(4).to_string())
print(
    "all detectors: >1.2",
    round((bright.psf_over_aperture > 1.2).mean(), 4),
    "| >1.5",
    round((bright.psf_over_aperture > 1.5).mean(), 4),
    "| >2",
    round((bright.psf_over_aperture > 2).mean(), 4),
)
bins = [-1, 0, 2, 5, 10, 20, 60]
bright = bright.assign(outlier_bin=pd.cut(bright.n_pix_outlier, bins))
print("\nPSF / aperture versus clipped pixels (all detectors): median, p95, fraction > 1.5")
print(
    bright.groupby("outlier_bin", observed=True)
    .psf_over_aperture.agg(
        n="size", median="median", p95=lambda r: r.quantile(0.95), above_1p5=lambda r: (r > 1.5).mean()
    )
    .round(3)
    .to_string()
)
per_galaxy = bright.groupby("target").psf_over_aperture.apply(lambda r: (r > 1.5).mean())
print(
    "\ngalaxies by fraction of their exposures with PSF/aperture > 1.5: p50 / p90 / p99 / max",
    np.round(np.percentile(per_galaxy, [50, 90, 99, 100]), 3),
    "| galaxies with > 10 %:",
    int((per_galaxy > 0.1).sum()),
)
per_galaxy.rename("fraction_psf_over_aperture_above_1p5").to_frame().to_parquet(
    f"{OUTPUT_DIR}/sdss48k_clipping_per_galaxy.parquet"
)

print("\n== 2. Repeatability of close-wavelength pairs (random subset) ==")
rng = np.random.default_rng(0)
subset_targets = rng.choice(photometry.target.unique(), N_SUBSET, replace=False)
subset = photometry[photometry.target.isin(subset_targets)].sort_values(["target", "detector_id", "wv_um"])
pairs = []
for (_, _), block in subset.groupby(["target", "detector_id"], sort=False):
    block = block.reset_index(drop=True)
    first, second = block.iloc[:-1].reset_index(drop=True), block.iloc[1:].reset_index(drop=True)
    close = (second.wv_um - first.wv_um) < 0.2 * first.wv_width_um
    if close.any():
        pairs.append(
            pd.DataFrame(
                {
                    "detector_id": first.detector_id[close],
                    "flux_level": 0.5 * (first.aper_flux_uJy[close] + second.aper_flux_uJy[close]),
                    "psf_pull": (first.opt_flux_uJy - second.opt_flux_uJy)[close]
                    / np.hypot(first.opt_flux_uJy_err, second.opt_flux_uJy_err)[close],
                    "aperture_pull": (first.aper_flux_uJy - second.aper_flux_uJy)[close]
                    / np.hypot(first.aper_flux_uJy_err, second.aper_flux_uJy_err)[close],
                    "psf_fractional_difference": (
                        (first.opt_flux_uJy - second.opt_flux_uJy)
                        / (0.5 * (first.opt_flux_uJy + second.opt_flux_uJy))
                    )[close],
                    "aperture_fractional_difference": (
                        (first.aper_flux_uJy - second.aper_flux_uJy)
                        / (0.5 * (first.aper_flux_uJy + second.aper_flux_uJy))
                    )[close],
                    "psf_snr": (0.5 * (first.opt_flux_uJy + second.opt_flux_uJy) / first.opt_flux_uJy_err)[
                        close
                    ],
                }
            )
        )
pairs = pd.concat(pairs, ignore_index=True)
pairs.to_parquet(f"{OUTPUT_DIR}/sdss48k_close_pairs.parquet")


def robust_sigma(values):
    values = values[np.isfinite(values)]
    return 1.4826 * np.median(np.abs(values - np.median(values)))


print("pairs", len(pairs))
table = pairs.groupby("detector_id").agg(
    n=("psf_pull", "size"),
    psf_pull_sigma=("psf_pull", robust_sigma),
    aperture_pull_sigma=("aperture_pull", robust_sigma),
    psf_fractional_sigma=("psf_fractional_difference", lambda v: robust_sigma(v) / np.sqrt(2)),
    aperture_fractional_sigma=("aperture_fractional_difference", lambda v: robust_sigma(v) / np.sqrt(2)),
    psf_beyond_5sigma=("psf_pull", lambda v: (np.abs(v) > 5 * robust_sigma(v)).mean()),
    aperture_beyond_5sigma=("aperture_pull", lambda v: (np.abs(v) > 5 * robust_sigma(v)).mean()),
)
print(
    "pull sigma = robust sigma of (f1 - f2)/sqrt(e1^2+e2^2) (1 if errors are right);"
    " fractional sigma = per-exposure fractional scatter"
)
print(table.round(3).to_string())
pairs["snr_bin"] = pd.cut(pairs.psf_snr, [0, 10, 20, 40, 80, 1e9])
print("\npull sigma versus PSF S/N (all detectors)")
print(
    pairs.groupby("snr_bin", observed=True)
    .agg(n=("psf_pull", "size"), psf=("psf_pull", robust_sigma), aperture=("aperture_pull", robust_sigma))
    .round(3)
    .to_string()
)
