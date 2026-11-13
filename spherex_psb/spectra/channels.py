"""The 102 nominal SPHEREx spectral channels (17 per detector) from the Spectral Channels calibration product.

The product (``<release>/spectral_channels/cal-sch-v<ver>-<date>/spectral_channels_*.fits``) carries a
2040x2040 channel-index map and a ``SPECTRAL_CHANNELS`` table with per-detector, per-channel WAVELENGTH,
WL_MIN,
WL_MAX, BANDWIDTH and R (Explanatory Supplement v2.1 section 4.3.2 and Tables 29-34). Channels 0 and 18 are
the off-nominal corners and are not part of the 102-channel grid.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests
from astropy.io import fits
from astropy.table import Table

from spherex_psb import CALIBRATION_ROOT

S3_URL = "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com"


def download_spectral_channels(release: str = "dr1") -> Path:
    target_dir = CALIBRATION_ROOT / "spectral_channels"
    target_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(target_dir.glob(f"{release}_spectral_channels_*.fits"))
    if existing:
        return existing[-1]
    listing = requests.get(f"{S3_URL}/?list-type=2&prefix={release}/spectral_channels/", timeout=60).text
    keys = re.findall(r"<Key>([^<]+\.fits)</Key>", listing)
    if not keys:
        raise RuntimeError(f"no spectral_channels product under {release}/")
    key = sorted(keys)[-1]
    path = target_dir / f"{release}_{Path(key).name}"
    with requests.get(f"{S3_URL}/{key}", stream=True, timeout=600) as response:
        response.raise_for_status()
        with open(path, "wb") as handle:
            for chunk in response.iter_content(1 << 20):
                handle.write(chunk)
    return path


def channel_table(release: str = "dr1") -> pd.DataFrame:
    """One row per (detector, channel 1..17) with the nominal wavelength bounds."""
    path = download_spectral_channels(release)
    with fits.open(path) as hdulist:
        names = [h.name for h in hdulist]
        table_name = "SPECTRAL_CHANNELS" if "SPECTRAL_CHANNELS" in names else names[-1]
        table = Table(hdulist[table_name].data).to_pandas()
    table.columns = [c.lower() for c in table.columns]
    table = table.rename(columns={"subchan": "channel"})
    nominal = table[(table.channel >= 1) & (table.channel <= 17)].copy()
    nominal["global_channel"] = (nominal.detector - 1) * 17 + nominal.channel
    return nominal.sort_values("global_channel").reset_index(drop=True)
