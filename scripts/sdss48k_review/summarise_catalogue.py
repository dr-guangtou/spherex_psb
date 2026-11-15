"""Summarise the student's SDSS 48k SPHEREx forced-photometry run: targets, images, coverage, measurement
quality.

Reads the four Parquet files in /Users/shuang/data/spherex/spherex_sdss48k_phot (read only) and prints
tables.
usage: uv run python scripts/sdss48k_review/summarise_catalogue.py
"""

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RUN_DIR = "/Users/shuang/data/spherex/spherex_sdss48k_phot"
PARENT_CATALOGUE = "/Users/shuang/data/mpa/outputs/catalogs/galaxy_summary_48111.csv"


def percentiles(values, levels=(5, 16, 50, 84, 95)):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return " / ".join(f"{np.percentile(values, level):.3g}" for level in levels) + f"  (n={len(values):,})"


targets = pd.read_parquet(f"{RUN_DIR}/targets.parquet")
images = pd.read_parquet(f"{RUN_DIR}/images.parquet")
extinction = pd.read_parquet(f"{RUN_DIR}/ebv.parquet")
parent = pd.read_csv(PARENT_CATALOGUE, dtype={"specobjid": np.int64})

print("== targets ==")
print(
    "rows",
    len(targets),
    "| same specobjid order as parent:",
    np.array_equal(targets.specobjid, parent.specobjid),
)
print(
    "redshift range",
    targets.redshift.min(),
    targets.redshift.max(),
    "| logM* min",
    targets.log_stellar_mass_msun.min(),
)
groups = targets.loc[targets.repeat_group >= 0, "repeat_group"]
print(
    "repeat groups",
    groups.nunique(),
    "| rows in groups",
    len(groups),
    "| unique galaxies",
    len(targets) - len(groups) + groups.nunique(),
)
print("in_magellanic", int(targets.in_magellanic.sum()))
print("n_images p5/16/50/84/95", percentiles(targets.n_images))
print("n_meas   p5/16/50/84/95", percentiles(targets.n_meas))
print(
    "targets with n_meas == 0:",
    int((targets.n_meas == 0).sum()),
    "| n_meas < n_images:",
    int((targets.n_meas < targets.n_images).sum()),
)
print("sum n_images", int(targets.n_images.sum()), "| sum n_meas", int(targets.n_meas.sum()))
print("ebv p5/16/50/84/95", percentiles(extinction.ebv), "| ebv > 0.1:", int((extinction.ebv > 0.1).sum()))

print("\n== images ==")
print(images.groupby(["release", "detector"]).size().unstack())
for release, block in images.groupby("release"):
    print(
        release,
        "MJD",
        round(block.mjd_beg.min(), 2),
        "-",
        round(block.mjd_end.max(), 2),
        "| images with 0 measurements",
        int((block.n_meas == 0).sum()),
    )
images["obs_week"] = images.obsid.str[:7]
print(
    "observation weeks:",
    images.obs_week.min(),
    "->",
    images.obs_week.max(),
    "| distinct",
    images.obs_week.nunique(),
)

print("\n== photometry (all rows) ==")
columns = [
    "target",
    "expid",
    "detector_id",
    "wv_um",
    "opt_flux_uJy",
    "opt_flux_uJy_err",
    "aper_flux_uJy",
    "aper_flux_uJy_err",
    "bkg_MJysr",
    "opt_chi2",
    "opt_dof",
    "n_pix_used",
    "n_pix_flagged",
    "n_pix_outlier",
    "converged",
]
phot = pq.read_table(f"{RUN_DIR}/photometry.parquet", columns=columns).to_pandas()
phot = phot.merge(images[["expid", "release"]], on="expid", how="left")
print("rows", len(phot), "| release counts", phot.release.value_counts().to_dict())
print("converged fraction", round(phot.converged.mean(), 5))
print("wavelength range", phot.wv_um.min(), phot.wv_um.max())
signal_to_noise = phot.opt_flux_uJy / phot.opt_flux_uJy_err
phot["snr"] = signal_to_noise
phot["chi2_dof"] = phot.opt_chi2 / phot.opt_dof.clip(lower=1)
phot["outlier_fraction"] = phot.n_pix_outlier / (phot.n_pix_used + phot.n_pix_outlier).clip(lower=1)
phot["aperture_over_psf"] = phot.aper_flux_uJy / phot.opt_flux_uJy
print(
    "finite flux fraction",
    round(np.isfinite(phot.opt_flux_uJy).mean(), 5),
    "| negative PSF flux",
    round((phot.opt_flux_uJy < 0).mean(), 5),
)
print(
    "\nper detector: wavelength, PSF flux, S/N, chi2/dof, outlier-pixel fraction, aperture/PSF (S/N > 10),"
    " n_pix_used"
)
for detector, block in phot.groupby("detector_id"):
    good = block[block.snr > 10]
    print(f"D{detector} rows {len(block):,}  wv {block.wv_um.min():.3f}-{block.wv_um.max():.3f}")
    print("   flux uJy  ", percentiles(block.opt_flux_uJy))
    print("   S/N       ", percentiles(block.snr))
    print("   chi2/dof  ", percentiles(block.chi2_dof))
    print(
        "   outlier fr",
        percentiles(block.outlier_fraction),
        "| rows with >=1 outlier",
        round((block.n_pix_outlier > 0).mean(), 3),
    )
    print("   aper/PSF  ", percentiles(good.aperture_over_psf))
    print(
        "   n_pix_used",
        percentiles(block.n_pix_used),
        "| n_pix_flagged>0",
        round((block.n_pix_flagged > 0).mean(), 3),
    )
print("\nby release: S/N and aperture/PSF (S/N > 10)")
for release, block in phot.groupby("release"):
    print(
        release,
        "S/N",
        percentiles(block.snr),
        "| aper/PSF",
        percentiles(block.aperture_over_psf[block.snr > 10]),
    )
phot[
    [
        "target",
        "expid",
        "detector_id",
        "wv_um",
        "snr",
        "chi2_dof",
        "outlier_fraction",
        "aperture_over_psf",
        "release",
    ]
].sample(2_000_000, random_state=0).to_parquet(
    "/Users/shuang/data/spherex/scratch/sdss48k_quality_sample.parquet"
)
