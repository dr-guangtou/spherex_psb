# SED demo report (in progress)

Branch `feature/sed-demo`; task spec `docs/sed_demo_task.md`; facts from the earlier study in
`docs/reference_notes/photometry_study_2026-11.md`. Figures in `docs/figures/sed_demo/`.

## Checkpoint A (2026-11-13): galaxy 1 end to end

Setup
- Data: DR1 + QR3 wide-survey exposures (IRSA TAP via spherex-retrieval); 341 exposures cover the
  reference galaxy (DR1 296: D1-D6 49/42/56/50/43/56; QR3 45: 9/9/5/9/9/4); 6 per detector selected,
  spread in time (30 DR1 + 6 QR3).
- Cutouts: 0.07 deg (41 x 41 px) bundles from spherex-retrieval with the R7 ePSF zones, CWAVE/CBAND and
  SAPM attached; 36 bundles = 7.4 MB on disk (0.20 MB each), 157 s at two concurrent requests
  (4.4 s per cutout); calibration cache 445 MB (ePSF, Spectral WCS, SAPM for six detectors, once).
- Catalogue: Legacy Survey DR10 Tractor sources within 1.1' down to z = 21 (119 neighbours; target shape
  from SDSS: exponential, R_e 4.38", b/a 0.77, PA 101.7). No shreds flagged. Neighbours are fitted
  jointly with the target.
- Model: PSF-convolved Sersic templates on the ePSF 5x grid (zone chosen in parent-frame pixels), point-
  sampled at native pixels; ZODI subtracted; constant background; flags = IRSA tool set + TRANSIENT,
  OVERFLOW, DICHROIC; NaN pixels removed; weighted linear solve for all amplitudes.
- Estimators: forced-model flux; model-corrected aperture flux at 1.5, 2, 2.5, 3 px; point-source fit as
  the negative control. Wavelength = CWAVE at the target pixel; MJy/sr to uJy with the SAPM.

Results (figures `g1_reference_fig2_image_qa.png`, `g1_reference_fig3_diagnostics.png`,
`g1_reference_fig4_sed.png`)
- 35 of 36 exposures measured; the 2.416 um D3 exposure is rejected (all pixels near the target flagged
  DICHROIC, reason `model_weight_masked`); the 1.097 um D2 exposure next to He I 1.083 um is screened as
  a chi2 outlier (chi2/dof 8.9 against a detector median of 1.3).
- chi2/dof near the target: median 1.1 (D1), 1.4 (D2), 1.5 (D3), 1.6 (D4), 1.0 (D5), 1.0 (D6) for the
  galaxy model; 3-15 for the point-source control in D1-D4.
- Point-source flux / model flux: 0.60-0.74 (D1-D4), 0.66-0.78 (D5-D6), as the simulations predicted.
- Model / 2 px aperture: 0.99-1.02 in D1-D4, 0.95-1.06 in D5-D6.
- Projected full demo (six galaxies, every wide-survey exposure, ~300-450 per galaxy): ~2,200 cutouts,
  ~0.45 GB on disk, ~2.7 h of IRSA requests at two workers.

Found while testing
- A background basis quadratic in CWAVE repairs the He I exposures (chi2/dof 8.9 -> 1.8) and moves their
  fluxes by 5-9 %; a plane in x, y does not. Default background model to be chosen on the full sample.
- One D4 exposure (3.32 um) has chi2/dof ~50 over the whole cutout but 3 near the target; to be inspected.

## Checkpoint B

(to come)
