"""spherex_psb: SPHEREx spectrophotometry of low-redshift post-starburst galaxies.

Data root and layout are fixed by the project rules (docs/SPEC.md section 3).
"""

from pathlib import Path

DATA_ROOT = Path("/Users/shuang/data/spherex")
CUTOUT_ROOT = DATA_ROOT / "cutouts"
CALIBRATION_ROOT = DATA_ROOT / "calibration"
SAMPLE_ROOT = DATA_ROOT / "sample"
RESULTS_ROOT = DATA_ROOT / "results"
SCRATCH_ROOT = DATA_ROOT / "scratch"

PIXEL_SCALE_ARCSEC = 6.15
DETECTORS = (1, 2, 3, 4, 5, 6)
WIDE_COLLECTIONS = ("spherex_dr1", "spherex_qr3")
DEEP_COLLECTIONS = ("spherex_dr1_deep", "spherex_qr3_deep")
