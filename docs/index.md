# SPHEREx notes for the post-starburst project

These pages record what the `spherex_psb` project has learned about SPHEREx (the Spectro-Photometer for the
History of the Universe, Epoch of Reionization and Ices Explorer) while preparing a study of nearby
post-starburst galaxies: how the instrument samples the sky, how its public data are organised and reached,
what the Level 2 images contain and how they must be handled, how we extract spectral energy distributions
(SEDs) of resolved SDSS galaxies from the individual exposures, and whether a near-infrared spectral index can
be measured from such SEDs.

The intended reader is an astronomer who knows galaxies and infrared photometry but not the particular way
SPHEREx works: an all-sky survey whose every exposure is an image in which the wavelength changes with
position on the detector. That single fact drives almost everything on these pages.

!!! note "Status (2026-11-14)"
    The notes cover SPHEREx data releases DR1 and QR3 (pipeline R7, version 7.0.5), the Explanatory
    Supplement v2.1, and the instrument, pipeline, spectral-response and map-making papers. Every number
    quoted is either cited to a source or was measured in this project; the latter are marked "measured"
    and point to the script that produced them. The SED demonstration used 2,225 exposures of six SDSS
    galaxies at 0.03 < z < 0.06.

## The pages

<div class="grid cards" markdown>

-   **[SPHEREx primer](primer.md)**

    ---

    The telescope, the linear variable filters, the six detectors, the survey plan, and the numbers that set
    what can be measured: pixel scale, resolving power, depth, cadence.

-   **[Data access](data_access.md)**

    ---

    Releases and their pipeline versions, the IRSA archive services (TAP, SIA, cutouts, S3), the Data
    Explorer tools, what we measured about request rates and outages, and the lessons learned.

-   **[Data reduction and analysis](reduction_analysis.md)**

    ---

    What is inside a Level 2 image, the flag bits, per-pixel wavelengths, the empirical PSF, the zodiacal
    light and the atmospheric emission lines, the dichroic boundary, and a checklist of pitfalls.

-   **[SED extraction for SDSS galaxies](sed_extraction.md)**

    ---

    Our forced Sersic photometry on every exposure of six galaxies, its validation (boundaries,
    injection, cross-code, repeat pairs, external photometry), the results and the open questions.

-   **[Spectral index measurement](spectral_indices.md)**

    ---

    What a spectral index means at R = 40 with irregular sampling, the 1.6 um H-minus bump index as the
    worked example, and what limits it on real SPHEREx SEDs.

</div>

## How to read the citations

Facts about SPHEREx are cited to the source they come from, as footnotes on each page. The sources are:

| Source | Short name used in the notes | Our reading notes |
|---|---|---|
| Korngut et al. 2026, "The SPHEREx Instrument" (arXiv:2603.29835) | instrument paper | [note](references/papers/paper_instrument_2603.29835.md) |
| Hui et al. 2026, "Spectral response of SPHEREx" (ApJS 284, 10; arXiv:2602.09139) | spectral-response paper | this site |
| Akeson et al. 2026, "The SPHEREx Image and Spectrophotometry Processing Pipeline" (ApJS 285, 67; arXiv:2511.15823) | pipeline paper | [note](references/papers/paper_pipeline_2511.15823.md) |
| Cukierman et al. 2026, "Spectral Map Making with SPHEREx" (ApJS 286, 22; arXiv:2603.25790) | map-making paper | [note](references/papers/paper_mapmaking_2603.25790.md) |
| Bock et al. 2026, "The SPHEREx Satellite Mission" (ApJ 999, 139; arXiv:2511.02985) | mission paper | cited through the official pages |
| SPHEREx Explanatory Supplement v2.0 (2026-08-25) and v2.1 (2026-11-10), IRSA | Explanatory Supplement | [note](references/irsa/spherex_explanatory_supplement_v2.0.md) |
| IRSA SPHEREx mission pages, Quick Release overview, tool help pages, tutorials | IRSA pages | [note](references/irsa/irsa_spherex_official_pages.md), [tutorials](references/irsa/irsa_spherex_tutorials.md) |
| Six early-science papers that extract SPHEREx spectra | by first author | [references](references/papers/paper_ref_2604.22012.md) |

Figures reproduced from papers carry a credit line naming the paper and figure number. Figures without a
credit line were made in this project from the public calibration products or from our own measurements;
the script that makes them is named in the caption.

## Repository

The notes are the `docs/` folder of the project repository; the analysis code lives in `spherex_psb/` and
`scripts/`. The project specification, task list and lessons file are under "Project" in the navigation.
The site is built with MkDocs and deployed to GitHub Pages by a workflow on every push to `main`.

```
uv run --only-group docs mkdocs serve      # local preview at http://127.0.0.1:8000
uv run --only-group docs mkdocs build --strict
```

## Acknowledgement text for publications

The IRSA release pages ask for this sentence[^ack]:

> This publication makes use of data products from the Spectro-Photometer for the History of the Universe,
> Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion
> Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space
> Administration.

together with the DOI of each release used (QR2 10.26131/IRSA652, QR3 10.26131/IRSA662, DR1
10.26131/IRSA678) and citations of the mission, pipeline, instrument and spectral-response papers.

[^ack]: IRSA Quick Release overview, `https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_qr.html`; see
    the [IRSA pages note](references/irsa/irsa_spherex_official_pages.md).
