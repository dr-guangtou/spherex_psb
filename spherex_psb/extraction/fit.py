"""Per-exposure forced photometry: joint weighted linear solve for the target, its neighbours and the
background, and the two SED estimators (forced-model flux and model-corrected aperture flux).

Everything is linear in the amplitudes; positions and shapes are fixed. NaN pixels are removed from the fit
(not zero-weighted). The point-source fit of the target is computed as a negative control.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from spherex_psb.extraction.background import background_templates
from spherex_psb.extraction.render import POINT_SOURCE, SersicShape, template_on_cutout
from spherex_psb.products.bundle import UJY_PER_MJY, Bundle
from spherex_psb.products.epsf import epsf_plane, select_zone, zone_record
from spherex_psb.products.flags import DEMO_EXCLUDE, FLAG_BITS, flagged

MINIMUM_TEMPLATE_FRACTION = 1e-3  # fraction of a source's flux that must fall in the cutout to fit it


@dataclass
class Source:
    name: str
    ra: float
    dec: float
    shape: SersicShape
    mag_z: float = np.nan
    is_target: bool = False


@dataclass
class FitSettings:
    fit_radius_px: float = 5.0  # chi2 and quality statistics are computed inside this radius of the target
    aperture_radii_px: tuple[float, ...] = (1.5, 2.0, 2.5, 3.0)
    background_model: str = (
        "cwave2"  # neutral away from airglow lines, repairs He I exposures (lessons 2026-11-13)
    )
    exclude_flags: tuple[str, ...] = DEMO_EXCLUDE
    half_width_px: int = 14
    use_cwave_at_target: bool = True
    minimum_fit_fraction: float = 0.5  # reject the exposure when less of the target's model weight survives


@dataclass
class FitResult:
    record: dict
    model: np.ndarray | None = None
    target_template: np.ndarray | None = None
    neighbour_light: np.ndarray | None = None
    background: np.ndarray | None = None
    data: np.ndarray | None = None
    good: np.ndarray | None = None
    amplitudes: dict = field(default_factory=dict)


def solve_weighted(
    data: np.ndarray, templates: list[np.ndarray], inverse_variance: np.ndarray, good: np.ndarray
):
    design = np.stack([t[good] for t in templates], axis=1)
    weight = inverse_variance[good]
    normal = design.T @ (design * weight[:, None])
    try:
        covariance = np.linalg.inv(normal)
    except np.linalg.LinAlgError:
        covariance = np.linalg.pinv(normal)
    amplitudes = covariance @ (design.T @ (data[good] * weight))
    residual = data[good] - design @ amplitudes
    chi2 = float(np.sum(residual**2 * weight))
    return amplitudes, np.sqrt(np.maximum(np.diag(covariance), 0)), chi2, design


def measure_exposure(bundle: Bundle, sources: list[Source], settings: FitSettings) -> FitResult:
    target = [s for s in sources if s.is_target]
    if len(target) != 1:
        raise ValueError("exactly one source must be the target")
    target = target[0]
    wcs = bundle.wcs
    shape = bundle.shape
    x0, y0 = (float(v) for v in wcs.all_world2pix([[target.ra, target.dec]], 0)[0])
    record: dict = {
        "obs_id": bundle.obs_id,
        "detector": bundle.detector,
        "collection": bundle.collection,
        "release": bundle.release,
        "pipeline_version": bundle.pipeline_version,
        "mjd": bundle.mjd,
        "x_cutout": x0,
        "y_cutout": y0,
        "n_sources": len(sources),
        "background_model": settings.background_model,
        "reject_reason": "",
    }
    x_orig, y_orig = bundle.parent_pixel(x0, y0)
    record["x_parent"], record["y_parent"] = x_orig, y_orig
    for key in (
        "HE_AIRGLOW_CONT",
        "AURORA_CONT",
        "SHUTTLE_GLOW_CONT",
        "AURORA_CORR",
        "SHUTTLE_GLOW_CORR",
        "L2DQAFLG",
        "FINAST",
        "PSF_FWHM",
    ):
        value = bundle.header_flag(key)
        record[key.lower()] = value if value is not None else np.nan

    inside = (0 <= x0 < shape[1]) and (0 <= y0 < shape[0])
    if not inside:
        record["reject_reason"] = "target_outside_cutout"
        return FitResult(record)
    margin = settings.fit_radius_px
    if x0 < margin or y0 < margin or x0 > shape[1] - 1 - margin or y0 > shape[0] - 1 - margin:
        record["reject_reason"] = "cutout_truncated"  # the detector edge cut the cutout short
        return FitResult(record)

    plane = select_zone(bundle, x0, y0)
    epsf = epsf_plane(bundle, plane)
    record.update(zone_record(bundle, plane))
    record["epsf_plane"] = plane

    # wavelength at the target position from the Spectral WCS maps
    j, i = int(round(y0)), int(round(x0))
    record["cwave_um"] = float(bundle.cwave[j, i])
    record["cband_um"] = float(bundle.cband[j, i])
    omega_sr = bundle.solid_angle_sr(x0, y0)
    record["omega_pixel_sr"] = omega_sr
    to_ujy = omega_sr * UJY_PER_MJY

    # templates
    templates, names = [], []
    captured = {}
    for source in sources:
        template, _, _, frac = template_on_cutout(
            wcs,
            source.ra,
            source.dec,
            source.shape,
            epsf,
            bundle.psf_oversampling,
            shape,
            settings.half_width_px,
        )
        if template.sum() < MINIMUM_TEMPLATE_FRACTION and not source.is_target:
            continue  # the source puts no usable light in the cutout; its amplitude would be unconstrained
        templates.append(template)
        names.append(source.name)
        captured[source.name] = frac
    target_index = names.index(target.name)
    target_template = templates[target_index]
    point_template, _, _, _ = template_on_cutout(
        wcs, target.ra, target.dec, POINT_SOURCE, epsf, bundle.psf_oversampling, shape, settings.half_width_px
    )
    background = background_templates(settings.background_model, shape, bundle.cwave)
    for name, template in background:
        templates.append(template)
        names.append(name)
    record["model_fraction_on_grid"] = captured[target.name]

    data = bundle.image - bundle.zodi
    usable = np.isfinite(data) & np.isfinite(bundle.variance) & (bundle.variance > 0)
    good = usable & ~flagged(bundle.flags, settings.exclude_flags)
    inverse_variance = np.zeros(shape)
    inverse_variance[usable] = 1.0 / bundle.variance[usable]
    yy, xx = np.indices(shape)
    radius = np.hypot(xx - x0, yy - y0)
    near = radius <= settings.fit_radius_px
    record["n_pixels_fit"] = int(good.sum())
    record["n_pixels_near"] = int((good & near).sum())
    record["n_flagged_near"] = int((near & usable & ~good).sum())
    record["n_nan_near"] = int((near & ~usable).sum())
    weight_total = target_template[near].sum()
    weight_kept = target_template[near & good].sum()
    record["model_fraction_fit"] = float(weight_kept / weight_total) if weight_total > 0 else 0.0
    record["dichroic_fraction_near"] = float(flagged(bundle.flags, ("DICHROIC",))[near].mean())
    record["source_flag_fraction_near"] = float(((bundle.flags[near] >> FLAG_BITS["SOURCE"]) & 1).mean())
    if record["model_fraction_fit"] < settings.minimum_fit_fraction:
        record["reject_reason"] = "model_weight_masked"
        return FitResult(record)

    amplitudes, errors, chi2, _ = solve_weighted(data, templates, inverse_variance, good)
    model = sum(a * t for a, t in zip(amplitudes, templates, strict=True))
    neighbour_light = sum(
        (
            a * t
            for a, t, n in zip(amplitudes, templates, names, strict=True)
            if n != target.name and not n.startswith("bkg_")
        ),
        np.zeros(shape),
    )
    background_light = sum(
        (a * t for a, t, n in zip(amplitudes, templates, names, strict=True) if n.startswith("bkg_")),
        np.zeros(shape),
    )
    flux_amp, flux_err = amplitudes[target_index], errors[target_index]
    record["flux_model_ujy"] = float(flux_amp * to_ujy)
    record["flux_model_err_ujy"] = float(flux_err * to_ujy)
    residual_near = (data - model)[good & near]
    dof_near = max(int((good & near).sum()) - 1, 1)
    record["chi2_dof_near"] = float(np.sum(residual_near**2 * inverse_variance[good & near]) / dof_near)
    record["chi2_dof_all"] = float(chi2 / max(int(good.sum()) - len(templates), 1))
    record["background_const_mjysr"] = float(amplitudes[names.index("bkg_const")])
    record["zodi_at_target_mjysr"] = float(bundle.zodi[j, i])
    record["neighbour_light_fraction_near"] = float(
        neighbour_light[near].sum() / max(flux_amp * target_template[near].sum(), 1e-30)
    )
    for name, a in zip(names, amplitudes, strict=True):
        if name.startswith("bkg_") and name != "bkg_const":
            record[name] = float(a)

    # model-corrected aperture fluxes at fixed angular radii; flagged pixels filled with the model
    cleaned = np.where(good, data - neighbour_light - background_light, flux_amp * target_template)
    for r_ap in settings.aperture_radii_px:
        in_aperture = radius <= r_ap
        fraction = target_template[in_aperture].sum()
        aperture_sum = cleaned[in_aperture].sum()
        key = f"{r_ap:g}".replace(".", "p")
        record[f"flux_aperture_{key}px_ujy"] = (
            float(aperture_sum / fraction * to_ujy) if fraction > 0 else np.nan
        )
        variance_sum = bundle.variance[in_aperture & good].sum()
        record[f"flux_aperture_{key}px_err_ujy"] = (
            float(np.sqrt(variance_sum) / fraction * to_ujy) if fraction > 0 else np.nan
        )
        record[f"aperture_{key}px_model_fraction"] = float(fraction)
        record[f"aperture_{key}px_filled_fraction"] = float(
            (in_aperture & ~good).sum() / max(in_aperture.sum(), 1)
        )

    # point-source negative control: same pixels, same background and neighbour templates
    control_templates = [point_template] + [
        t for t, n in zip(templates, names, strict=True) if n != target.name
    ]
    amp_point, err_point, chi2_point, _ = solve_weighted(data, control_templates, inverse_variance, good)
    record["flux_point_ujy"] = float(amp_point[0] * to_ujy)
    record["flux_point_err_ujy"] = float(err_point[0] * to_ujy)
    point_model = sum(a * t for a, t in zip(amp_point, control_templates, strict=True))
    record["chi2_dof_near_point"] = float(
        np.sum((data - point_model)[good & near] ** 2 * inverse_variance[good & near]) / dof_near
    )

    return FitResult(
        record,
        model=model,
        target_template=flux_amp * target_template,
        neighbour_light=neighbour_light,
        background=background_light,
        data=data,
        good=good,
        amplitudes={n: float(a) for n, a in zip(names, amplitudes, strict=True)},
    )
