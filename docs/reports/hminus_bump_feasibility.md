# Can the 1.6 um H-minus bump index be measured from the demo SEDs?

Date: 2026-11-14. Script: `scripts/sed_demo/hminus_bump_feasibility.py` (reads the H-bump project's
`spectral_indices.py` and its cached FSPS products at
`/Users/shuang/Dropbox/work/project/luandun/stellar_pop/fsps_agb/output`, read only). Outputs:
`results/hminus_bump/*.csv`, `docs/figures/sed_demo/fig8_hminus_bump_feasibility.png`.

## 1. What the H-bump paper asks for

- Index Hbump_opt: blue 1.494-1.539, feature 1.570-1.734, red 1.746-1.791 um (rest, vacuum); straight-line
  pseudo-continuum through the band means of F_lambda; I_mag = -2.5 log10(mean F/F_c); negative = stronger
  bump. The paper measures it at an instrumental R = 100 (Gaussian, FWHM convention) on top of
  sigma = 300 km/s.
- Useful dynamic range in the FSPS mocks: rapid-quenching class median -0.075 mag (TP-AGB on, agb=2,
  LW02 templates) versus -0.004 mag (TP-AGB off); the transient excursion along one quenching track is
  0.006-0.023 mag; the classifier gain needs 0.005-0.010 mag precision and is "small" at 0.020 mag.
- The paper's SPHEREx concern was the "spectral resolution". SPHEREx bands 1-3 have R = 41.4 (Hui et al.
  2026, table 1, arXiv:2602.09139), with R = lambda_c / Delta lambda where Delta lambda is the integral of
  the normalised per-pixel response (their eq. 4), band centre = 50 % point of the cumulative response, and
  no measurable out-of-band leakage above 1.64 um (their section 6.2). The per-pixel profile shape is not
  tabulated, so the test below uses a Gaussian and a top-hat of equal equivalent width lambda / 41.4.

## 2. Resolution is not the limitation

Index change from the paper's R = 100 to the SPHEREx kernels, over the whole cached SSP grid (ages
0.1-12.6 Gyr, four metallicities, TP-AGB on and off, 344 spectra) and along the t_q = 3 Gyr,
tau_q = 0.3 Gyr solar track:

| kernel (equivalent width = lambda / 41.4) | median change | extremes | slope of index(kernel) vs index(R100) |
|---|---|---|---|
| Gaussian | -0.0006 mag | -0.0018 / +0.0016 | 0.969 |
| top-hat | -0.0003 mag | -0.0009 / +0.0008 | 0.983 |
| Gaussian with FWHM = lambda / 41.4 (broadest case) | -0.0007 mag | -0.0020 / +0.0019 | 0.965 |

The TP-AGB-on track peaks at -0.0734 mag at SPHEREx resolution against -0.0750 at R = 100; the on/off
contrast 1 Gyr after quenching is 0.067 mag for Hbump_opt, 0.095 for Hbump_Lu26 and 0.102 for
Hbump_Verro22. The 0.045 um sidebands are 1.2 resolution elements wide, which is enough for a feature this
broad (figure 8a, b).

## 3. What limits the measurement: sampling, the D2/D3 boundary, and the estimator

Measured on the six demo galaxies (model flux, dereddened, screened exposures; errors from bootstrapping
the exposures inside each window; 1000 draws):

| galaxy | z | exposures blue/feature/red | D2 / D3 in the index range | D2/D3 boundary (rest um) | exposure scatter | I_mag (exposures) | I_mag (102 channels) | D2/D3 ratio (model flux) | index shift if the ratio is removed |
|---|---|---|---|---|---|---|---|---|---|
| g1 reference | 0.046 | 2 / 25 / 4 | 8 / 29 | 1.566 | 1.8 % | -0.057 +- 0.017 | -0.058 +- 0.019 | 1.029 +- 0.010 | +0.014 |
| g2 compact | 0.058 | 4 / 12 / 5 | 5 / 21 | 1.547 | 2.0 % | -0.028 +- 0.020 | -0.028 +- 0.011 | 1.001 +- 0.010 | +0.001 |
| g3 large | 0.033 | 4 / 18 / 3 | 8 / 21 | 1.585 | 1.4 % | -0.050 +- 0.013 | -0.050 +- 0.010 | 1.022 +- 0.010 | +0.011 |
| g4 neighbour | 0.033 | 4 / 16 / 3 | 12 / 17 | 1.585 | 6.6 % | -0.055 +- 0.033 | -0.014 +- 0.027 | 0.985 +- 0.025 | -0.005 |
| g5 no legacy | 0.052 | 7 / 13 / 3 | 11 / 18 | 1.557 | 1.8 % | -0.040 +- 0.011 | -0.054 +- 0.007 | 1.024 +- 0.008 | +0.010 |
| g6 post-starburst | 0.052 | 5 / 15 / 3 | 10 / 21 | 1.557 | 2.2 % | -0.018 +- 0.015 | -0.027 +- 0.014 | 1.006 +- 0.015 | +0.003 |

With the wider Hbump_Lu26 windows (blue 1.40-1.50, feature 1.50-1.80, red 1.80-2.00 um) the sidebands hold
6-13 and 10-17 exposures and the bootstrap errors are 0.011-0.019 mag (g4 0.019); the Verro22 windows
(0.02 um sidebands) hold 0-3 exposures and cannot be used at all with the present sampling.

Simulation with the real rest wavelengths and the measured exposure scatter of each galaxy (TP-AGB-on
spectrum 1 Gyr after quenching, degraded to R = 41.4, 1000 noise draws, Hbump_opt, same estimator):

| galaxy | statistical scatter | bias from the irregular sampling (noiseless) | bias from the galaxy's own D2/D3 ratio |
|---|---|---|---|
| g1 | 0.010 | -0.001 | -0.015 |
| g2 | 0.010 | +0.008 | -0.001 |
| g3 | 0.007 | -0.004 | -0.012 |
| g4 | 0.032 | -0.005 | +0.006 |
| g5 | 0.009 | +0.007 | -0.010 |
| g6 | 0.011 | -0.003 | -0.004 |

Readings:

1. Statistics. One galaxy with the present DR1 + QR3 coverage gives 0.011-0.020 mag (bootstrap) or
   0.007-0.011 mag (simulated, Gaussian scatter only; the bootstrap is larger because the real sidebands
   contain structure beyond white noise, see figure 8c). That is the paper's "small gain" regime. The on/off
   contrast (0.067 mag) is detectable per galaxy at 3-6 sigma; the quenching-time excursion (0.02 mag) is
   not. The error is set by the 2-7 exposures in each 0.045 um sideband, so it falls as the square root of the
   number of exposures: a stack of 10-20 galaxies, or the four-survey mission, reaches the 0.005 mag the
   classifier needs.
2. The D2/D3 boundary. For 0 < z < 0.096 the 1.6375 um detector boundary falls inside the index windows
   (rest 1.547-1.585 um for the demo sample: the gap between the blue sideband and the feature band). Any
   detector-to-detector flux step of 1 % moves Hbump_opt by 0.003-0.007 mag (0.003-0.005 for Lu26). The
   per-galaxy model-flux steps measured in the demo (0-3 %, D3 brighter) move it by up to 0.015 mag,
   the size of the signal, and the isolated stars constrain the calibration step only to +-1.3 % (report
   table, stars n029, n013, n007). Whether the galaxy steps are calibration, the Sersic-model response to
   the different ePSFs of D2 and D3, or real spectral curvature that the boundary fit's quadratic did not
   absorb, is exactly the D2/D3 question left open at checkpoint B. Until it is settled at the 0.3 % level
   the index carries a 0.005-0.015 mag systematic per galaxy that does not average down in a stack.
3. The estimator. Band means over irregularly placed exposures are biased by up to 0.008 mag when the
   exposures cluster at one end of a window (g2, g5), and the 102-channel estimator disagrees with the
   exposure estimator by 0.014 mag (g5) and 0.04 mag (g4). A forward model that fits all 40-60 exposures in
   1.4-2.0 um with a smooth continuum plus a bump template (or the FSPS spectra directly), weighting each
   exposure by its bandpass, would remove the sampling bias and use the feature-band exposures to
   constrain the continuum too. The same machinery is what the full-sample pipeline needs anyway.
4. Minor: for z < 0.01 the blue sideband reaches the 1.49 um He I leak feature of band 2 (data guide
   section 1); not an issue at z > 0.03. Emission lines (Brackett, [Fe II] 1.644 um) and hot dust are not
   modelled; neither are metallicity and dust in the comparison models (solar, no attenuation).

## 4. The six galaxies

Five of the six have I_mag between -0.03 and -0.06 mag, inside the TP-AGB-on range of the quenching track
(-0.05 to -0.075 after t_q) and below the TP-AGB-off range (0 to -0.02); the post-starburst galaxy g6 has
the weakest bump, -0.018 +- 0.015 (both estimators), which is the opposite of the TP-AGB-on expectation
for a galaxy 0.5-1 Gyr after quenching. With 0.015 mag errors and the unresolved D2/D3 term this is not a
measurement of anything yet, and the comparison models are a single solar-metallicity track. It does show
that the data have the dynamic range: figure 8c shows the reference galaxy's exposures sitting 5-8 % above
its pseudo-continuum across the whole feature band, like the TP-AGB-on model and unlike the TP-AGB-off
one.

## 5. Verdict and what to do before using the index

Feasible in principle: SPHEREx's resolving power loses nothing (< 0.002 mag), the demo photometry has the
per-exposure precision (1.4-2.2 %) for a 0.01 mag index per galaxy today and 0.005 mag with stacks or the
full mission. Not meaningful yet, because of two systematics of the same size as the signal:

1. Settle the D2/D3 step at the 0.3 % level (hundreds of field stars, or compare the galaxy step with the
   point-source control per ePSF zone), or move the sample to z > 0.1 where the whole index sits on D3.
2. Replace the band-mean estimator with a forward-model fit over 1.4-2.0 um that uses every exposure and
   its bandpass; validate it on injected FSPS spectra with the real sampling (the simulation in the script
   is the template for that test).

Then the index becomes a per-galaxy quantity at 0.01 mag and a stacked quantity at 0.005 mag, which is
where the paper's classifier gains start.

## Figure 8

`fig8_hminus_bump_feasibility.png`. (a) The TP-AGB-on FSPS spectrum 1 Gyr after quenching at the paper's
R = 100 and degraded to the SPHEREx resolving power with a Gaussian and a top-hat of equivalent width
lambda / 41.4; shaded: the Hbump_opt blue, feature and red windows. (b) Hbump_opt along the t_q = 3 Gyr,
tau_q = 0.3 Gyr solar track for the three kernels; solid TP-AGB on, dotted TP-AGB off. (c) Exposures of the
reference galaxy and of the post-starburst galaxy (offset +0.18) divided by their straight-line
pseudo-continuum, D2 and D3 in the detector colours; the two models at SPHEREx resolution are drawn
through the reference galaxy. (d) Hbump_opt of the six galaxies: filled, exposure estimator with bootstrap
errors; open, from the 102-channel SED; grey, after dividing the D3 exposures by the galaxy's measured
D2/D3 ratio; bands, the model ranges after quenching at SPHEREx resolution.
